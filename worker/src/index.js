/**
 * Wordbook search API — Cloudflare Worker over a D1 (edge SQLite) database.
 *
 * The terminology data is private. This Worker is the ONLY way the public
 * website touches it, and it returns only isolated, per-query result snippets —
 * never the bulk database. That's the copyright safeguard: a visitor can look
 * a term up, but cannot download the curated corpus.
 *
 * Endpoints (all GET, JSON, CORS-locked to the site origins below):
 *
 *   GET /meta
 *     One-time payload for page load: the source inventory ("Inside the
 *     Wordbook" table), the available language pairs, and total counts.
 *
 *   GET /search?q=<query>&limit=<n>&from=<lang>&to=<lang>
 *     FTS5 prefix search over (a, b, def, abbr). Returns matching entries in the
 *     same compact shape the old static snapshot used, so the front-end's
 *     direction-grouping logic is unchanged. `limit` is capped server-side.
 *     `from`/`to` are the UI's search direction (ISO 639-1, or "any"); they
 *     don't filter, they only steer ranking — see buildRankSql().
 *     Also returns `concepts`: the multilingual concepts a term matches, each
 *     whole with all its languages (see searchConcepts()). If that lookup
 *     fails, `concepts_error` says why and the entries still come back.
 *
 * D1 schema is produced by the private repo's `wordbook build-d1` command and
 * loaded with `wrangler d1 execute`. See worker/README.md for the runbook.
 */

const ALLOWED_ORIGINS = new Set([
	'https://beijerdictionary.com', // canonical Beijerdictionary site (Cloudflare)
	'https://www.beijerdictionary.com',
	'https://beijerterm.com',      // the old name; redirects to beijerdictionary.com
	'https://www.beijerterm.com',
	'https://superterm.io',        // former domain — kept during the 301 grace window
	'https://www.superterm.io',
	'https://beijer.uk',           // hand-off search box on the main site
	'https://www.beijer.uk',
	'http://localhost:4321',       // Astro dev
	'http://127.0.0.1:4321',
	'http://localhost:8788',       // wrangler pages dev
]);

// A common word ("terminal") has hundreds of prefix matches, and its genuine
// equivalents have to fit inside the result budget alongside them, so the cap
// is generous. Still a per-query snippet, not the corpus: the front-end shows
// at most a few dozen headword cards from it.
const MAX_LIMIT = 300;
const DEFAULT_LIMIT = 50;

// Also trust this account's own *.workers.dev / *.pages.dev preview subdomains
// (e.g. beijerterm.michaelbeijer-co-uk.workers.dev) so previews work before the
// custom domain is attached. The custom domains above are the real surfaces.
function isAllowedOrigin(origin) {
	if (ALLOWED_ORIGINS.has(origin)) return true;
	return /^https:\/\/[a-z0-9-]+\.michaelbeijer-co-uk\.(workers|pages)\.dev$/.test(origin || '');
}

function corsHeaders(origin) {
	const allow = isAllowedOrigin(origin) ? origin : 'https://beijerdictionary.com';
	return {
		'Access-Control-Allow-Origin': allow,
		'Access-Control-Allow-Methods': 'GET, OPTIONS',
		'Access-Control-Allow-Headers': 'Content-Type',
		'Vary': 'Origin',
	};
}

function json(data, origin, status = 200, extra = {}) {
	return new Response(JSON.stringify(data), {
		status,
		headers: {
			'Content-Type': 'application/json; charset=utf-8',
			'Cache-Control': 'public, max-age=60',
			...corsHeaders(origin),
			...extra,
		},
	});
}

/**
 * Turn a user string into a safe FTS5 MATCH expression: strip FTS operator
 * punctuation, then AND the tokens together. By default each token is a prefix
 * ("octrooi" also matches "octrooien"); with wholeWord the tokens match whole
 * words only. Mirrors the local search.py logic.
 */
function toFtsQuery(q, wholeWord, cols) {
	const cleaned = (q || '').replace(/["'()*:.,;?!\[\]{}^$~-]/g, ' ').trim();
	if (!cleaned) return '';
	const tokens = cleaned.split(/\s+/).filter(Boolean);
	if (!tokens.length) return '';
	const suffix = wholeWord ? '' : '*';
	// Restrict matching to the chosen FTS columns ("{a b abbr} : tok").
	const colFilter = (cols && cols.length) ? `{${cols.join(' ')}} : ` : '';
	return tokens.map((t) => `${colFilter}"${t}"${suffix}`).join(' AND ');
}

// "Search in" scopes → FTS columns. Default is terms only (headword sides +
// abbreviation), so long definitions/notes don't add noise unless asked for.
const SCOPE_COLS = { terms: ['a', 'b', 'abbr'], def: ['def'], notes: ['notes'] };

/**
 * Unicode-aware fold for case/accent-sensitive refinement. Diacritics are
 * stripped unless accentSensitive; text is lower-cased unless caseSensitive.
 */
function normFold(s, caseSensitive, accentSensitive) {
	let x = s || '';
	if (!accentSensitive) x = x.normalize('NFD').replace(/\p{Diacritic}/gu, '');
	if (!caseSensitive) x = x.toLowerCase();
	return x;
}

// Field-presence filters: column must be non-empty.
const HAS_COLS = { abbr: 'e.abbr', def: 'e.def', notes: 'e.notes' };

// D1 rejects a query with more than 100 bound parameters. The sense lookups
// below are `... WHERE id IN (?,?,…)` over the result set, so once the
// front-end's fetch limit passed 100 the query threw and the catch degraded
// EVERY result to no senses at all — silently, because losing senses looks the
// same as not having any. Chunk instead, with headroom.
const ID_CHUNK = 90;

// Multilingual concepts: a row of a multilingual source, kept whole (see
// CONCEPTS-DESIGN.md in the private repo). One search returns at most this
// many, each with every term in every language.
const CONCEPT_LIMIT = 20;
// Matching term rows ranked before they are grouped into concepts. One concept
// can match many times (EuroVoc's "executive agency" lists 19 agencies), so
// this is well above CONCEPT_LIMIT.
const CONCEPT_TERM_FETCH = 400;

/** Run an `id IN (...)` SELECT over `ids` in chunks, concatenating the rows. */
async function selectByIds(env, buildSql, ids) {
	const out = [];
	for (let i = 0; i < ids.length; i += ID_CHUNK) {
		const part = ids.slice(i, i + ID_CHUNK);
		const ph = part.map(() => '?').join(',');
		const { results } = await env.DB.prepare(buildSql(ph)).bind(...part).all();
		if (results) out.push(...results);
	}
	return out;
}

/**
 * Build the tiered ORDER BY expression that ranks results ahead of bm25.
 *
 * FTS matching is prefix-based ("terminal*" also hits "terminalluchtruim"), and
 * bm25 alone ranks those compounds ABOVE a row whose term IS the query — a
 * compound matches the token on both sides of the pair, an exact hit only on
 * one. Left to itself the result budget for a common word is spent entirely on
 * near-misses: searching "terminal" returned 100 rows without a single one of
 * `station`, `poot`, `pool`, `kopstation`, `aansluitklem` …
 *
 * The old boost tested only `UPPER(e.a) = UPPER(q)`. Column `a` holds Dutch for
 * essentially the whole corpus, so an English query got no boost at all and the
 * rows whose *Dutch* happened to equal the query were pinned to the top
 * instead. Rank in explicit tiers instead:
 *
 *   0  exact hit on the side carrying the SEARCH language — direction-aware, so
 *      EN "terminal" (en→nl) puts "station | terminal" first whichever column
 *      holds the English
 *   1  exact hit on either side, or on the abbreviation
 *   2  the query as a whole WORD inside a multi-word term ("user terminal")
 *   3  everything else: prefix-only hits, definition / notes matches
 *
 * bm25 still orders within a tier. `from` only steers tier 0 — nothing is
 * filtered out, so a mis-set direction can never hide a result.
 */
function buildRankSql(exact, srcLang) {
	const tiers = [];
	const binds = [];

	if (srcLang && srcLang !== 'any') {
		tiers.push(
			'WHEN (e.la = ? AND UPPER(e.a) = UPPER(?))' +
			' OR (e.lb = ? AND UPPER(e.b) = UPPER(?)) THEN 0'
		);
		binds.push(srcLang, exact, srcLang, exact);
	}

	tiers.push(
		"WHEN UPPER(e.a) = UPPER(?) OR UPPER(COALESCE(e.b, '')) = UPPER(?)" +
		" OR UPPER(COALESCE(e.abbr, '')) = UPPER(?) THEN 1"
	);
	binds.push(exact, exact, exact);

	// Whole-word-inside match, padded so the boundaries are real spaces. The
	// query is user input, so escape LIKE's own metacharacters.
	const likeWord = '% ' + exact.replace(/[\\%_]/g, (c) => '\\' + c) + ' %';
	tiers.push(
		"WHEN ' ' || COALESCE(e.a, '') || ' ' LIKE ? ESCAPE '\\'" +
		" OR ' ' || COALESCE(e.b, '') || ' ' LIKE ? ESCAPE '\\' THEN 2"
	);
	binds.push(likeWord, likeWord);

	return { sql: `CASE ${tiers.join(' ')} ELSE 3 END`, binds };
}

/**
 * Find the concepts a query matches and return each one whole.
 *
 * A concept is matched by any of its terms (ranked in the same tiers as
 * entries: exact in the search language, exact in any language, whole word,
 * anything else) or, when "Search in" asks for it, by its definition or notes.
 * The best CONCEPT_LIMIT concepts are then fetched with ALL their terms. Their
 * ids go to D1 as ONE JSON parameter (json_each), so the 100-parameter limit
 * can never be reached however many concepts come back.
 */
async function searchConcepts(env, o) {
	const { q, exact, srcLang, scopeCols, ftsWhole, refine, nq, caseSens, accentSens, has } = o;
	// Concepts carry no abbreviations, so "has an abbreviation" rules them out.
	if (has.includes('abbr')) return [];
	const hasSql = has.map((h) => ` AND c.${h} IS NOT NULL AND TRIM(c.${h}) <> ''`).join('');
	const fold = (s) => normFold(s, caseSens, accentSens);
	const hits = [];   // { cid, lang, t, tier }, best first

	if (scopeCols.includes('a')) {
		const fts = toFtsQuery(q, ftsWhole, null);
		const tiers = [];
		const binds = [];
		if (srcLang && srcLang !== 'any') {
			tiers.push('WHEN ct.lang = ? AND UPPER(ct.t) = UPPER(?) THEN 0');
			binds.push(srcLang, exact);
		}
		tiers.push('WHEN UPPER(ct.t) = UPPER(?) THEN 1');
		binds.push(exact);
		tiers.push("WHEN ' ' || ct.t || ' ' LIKE ? ESCAPE '\\' THEN 2");
		binds.push('% ' + exact.replace(/[\\%_]/g, (c) => '\\' + c) + ' %');
		const { results } = await env.DB.prepare(
			`SELECT ct.cid, ct.lang, ct.t, CASE ${tiers.join(' ')} ELSE 3 END AS tier
			 FROM concept_terms_fts
			 JOIN concept_terms ct ON ct.id = concept_terms_fts.rowid
			 ${hasSql ? 'JOIN concepts c ON c.id = ct.cid' : ''}
			 WHERE concept_terms_fts MATCH ?${hasSql}
			 ORDER BY tier, ct.ord > 0, bm25(concept_terms_fts)
			 LIMIT ?`
		).bind(...binds, fts, refine ? 2000 : CONCEPT_TERM_FETCH).all();
		for (const r of results || []) {
			if (refine && !(o.exactMode ? fold(r.t) === nq : fold(r.t).includes(nq))) continue;
			hits.push(r);
		}
	}

	const textCols = scopeCols.filter((c) => c === 'def' || c === 'notes');
	if (textCols.length) {
		const fts = toFtsQuery(q, ftsWhole, textCols);
		const { results } = await env.DB.prepare(
			`SELECT c.id AS cid, c.def, c.notes
			 FROM concepts_fts JOIN concepts c ON c.id = concepts_fts.rowid
			 WHERE concepts_fts MATCH ?${hasSql}
			 ORDER BY bm25(concepts_fts)
			 LIMIT ?`
		).bind(fts, refine ? 2000 : CONCEPT_TERM_FETCH).all();
		for (const r of results || []) {
			if (refine && !textCols.some((c) => r[c] && fold(r[c]).includes(nq))) continue;
			hits.push({ cid: r.cid, field: textCols.find((c) => r[c]) || textCols[0], tier: 3 });
		}
	}

	// One concept per id. `hits` is best first (term hits by tier then bm25,
	// then definition hits), so a concept's first hit is its best one.
	const best = new Map();
	for (const h of hits) if (!best.has(h.cid)) best.set(h.cid, h);
	const picked = [...best.values()].slice(0, CONCEPT_LIMIT);
	if (!picked.length) return [];

	const ids = JSON.stringify(picked.map((h) => h.cid));
	const [{ results: rows }, { results: terms }] = await Promise.all([
		env.DB.prepare(
			'SELECT id, src, dom, def, notes, links, langs FROM concepts ' +
			'WHERE id IN (SELECT value FROM json_each(?))').bind(ids).all(),
		env.DB.prepare(
			'SELECT cid, lang, t, q FROM concept_terms ' +
			'WHERE cid IN (SELECT value FROM json_each(?)) ORDER BY cid, id').bind(ids).all(),
	]);
	const byId = new Map((rows || []).map((r) => [r.id, r]));
	const termsById = new Map();
	for (const t of terms || []) {
		let per = termsById.get(t.cid);
		if (!per) termsById.set(t.cid, (per = {}));
		(per[t.lang] = per[t.lang] || []).push(t.q ? { t: t.t, q: t.q } : { t: t.t });
	}

	const out = [];
	for (const h of picked) {
		const c = byId.get(h.cid);
		if (!c) continue;
		const o2 = {
			id: c.id, src: c.src,
			langs: String(c.langs || '').split(',').filter(Boolean),
			hit: h.field ? { field: h.field, tier: h.tier } : { lang: h.lang, t: h.t, tier: h.tier },
			terms: termsById.get(c.id) || {},
		};
		if (c.dom) o2.dom = c.dom;
		if (c.def) o2.def = c.def;
		if (c.notes) o2.notes = c.notes;
		if (c.links) o2.links = c.links;
		out.push(o2);
	}
	return out;
}

async function handleSearch(url, env, origin) {
	const q = url.searchParams.get('q') || '';
	let limit = parseInt(url.searchParams.get('limit') || '', 10);
	if (!Number.isFinite(limit) || limit <= 0) limit = DEFAULT_LIMIT;
	limit = Math.min(limit, MAX_LIMIT);

	const exactMode  = url.searchParams.get('exact')  === '1';
	const wholeWord  = url.searchParams.get('whole')  === '1';
	const caseSens   = url.searchParams.get('case')   === '1';
	const accentSens = url.searchParams.get('accent') === '1';
	const has = (url.searchParams.get('has') || '')
		.split(',').map((s) => s.trim()).filter((h) => HAS_COLS[h]);
	// The UI's search direction. Ranking hint only (see buildRankSql) — never a
	// filter, so an unknown or absent code just drops tier 0.
	const srcLang = (url.searchParams.get('from') || '').trim().toLowerCase();

	// "Search in" scope. Default (none/invalid) is terms only.
	let cols = [];
	for (const f of (url.searchParams.get('fields') || '').split(',').map((s) => s.trim())) {
		if (SCOPE_COLS[f]) cols.push(...SCOPE_COLS[f]);
	}
	cols = [...new Set(cols.length ? cols : SCOPE_COLS.terms)];

	// Exact mode matches whole strings, so its FTS prefilter uses whole-word tokens.
	const fts = toFtsQuery(q, wholeWord || exactMode, cols);
	if (!fts) return json({ query: q, entries: [], concepts: [] }, origin);

	// SQL field-presence filters.
	const whereExtra = has.length
		? ' AND ' + has.map((h) => `${HAS_COLS[h]} IS NOT NULL AND TRIM(${HAS_COLS[h]}) <> ''`).join(' AND ')
		: '';

	// Exact whole-string matches on either headword side or the abbreviation must
	// win over mere prefix matches: a query of "AFF" should surface the
	// abbreviation "AFF" ahead of "afferent"/"affidavit"/… which only share the
	// "aff" prefix, and "terminal" must surface "station | terminal" ahead of
	// "terminalluchtruim | terminal airspace".
	const exact = (q || '').trim();
	const tier = buildRankSql(exact, srcLang);

	// Case/accent/exact need a Unicode-aware refinement the FTS tokenizer can't
	// do (it folds case + diacritics), so pull a larger candidate set ordered by
	// boost+bm25 and slice after filtering. Otherwise the SQL LIMIT is the cut.
	const refine = exactMode || caseSens || accentSens;
	const fetchN = refine ? 1200 : limit;

	// Concepts are looked up alongside the entries. A failure there must not
	// cost the entries, and must not pass for "no concepts matched" either (a
	// caught-and-ignored error is how every search once lost its senses), so
	// it is logged and reported in the payload.
	const conceptsP = searchConcepts(env, {
		q, exact, srcLang, scopeCols: cols, ftsWhole: wholeWord || exactMode, refine,
		nq: normFold(exact, caseSens, accentSens), exactMode, caseSens, accentSens, has,
	}).then(
		(concepts) => ({ concepts }),
		(err) => {
			const msg = String((err && err.message) || err);
			console.error('concept search failed:', msg);
			return { concepts: [], error: msg };
		});

	const stmt = env.DB.prepare(
		`SELECT e.id, e.la, e.a, e.qa, e.lb, e.b, e.qb,
		        e.reg, e.pos, e.dom, e.def, e.notes, e.abbr, e.links, e.srcs,
		        bm25(entries_fts) AS rank
		 FROM entries_fts
		 JOIN entries e ON e.id = entries_fts.rowid
		 WHERE entries_fts MATCH ?${whereExtra}
		 ORDER BY ${tier.sql}, rank
		 LIMIT ?`
	).bind(fts, ...tier.binds, fetchN);

	let { results } = await stmt.all();
	results = results || [];

	if (refine) {
		const nq = normFold(exact, caseSens, accentSens);
		results = results.filter((r) => {
			if (exactMode) {
				return [r.a, r.b, r.abbr].some((f) => f && normFold(f, caseSens, accentSens) === nq);
			}
			// Refine only over the searched columns (result keys match column names).
			return cols.some((c) => r[c] && normFold(r[c], caseSens, accentSens).includes(nq));
		}).slice(0, limit);
	}

	// Drop the rank field from the wire payload; strip null/empty keys to keep
	// it compact, matching the old snapshot shape.
	const entries = (results || []).map((r) => {
		const o = { id: r.id, la: r.la, a: r.a, lb: r.lb, b: r.b };
		if (r.qa) o.qa = r.qa;
		if (r.qb) o.qb = r.qb;
		if (r.reg) o.reg = r.reg;
		if (r.pos) o.pos = r.pos;
		if (r.dom) o.dom = r.dom;
		if (r.def) o.def = r.def;
		if (r.notes) o.notes = r.notes;
		if (r.abbr) o.abbr = r.abbr;
		if (r.links) o.links = r.links;
		if (r.srcs) o.src = r.srcs;
		return o;
	});

	// Consolidated senses (Phase 2). An entry can carry a sense group on EACH
	// side — "plaat | plate" belongs to a sense of Dutch *plaat* (sga) and to a
	// sense of English *plate* (sgb) — and which one applies depends on the
	// direction being searched, so both are returned and the front-end picks.
	// Wrapped in a try/catch and kept OUT of the main FTS query so an older D1
	// dump degrades gracefully to no senses; a dump with the pre-sides single
	// `sg` column is read as the a-side, which is what it was.
	let senses = [];
	try {
		const ids = entries.map((e) => e.id).filter((x) => x != null);
		if (ids.length) {
			let sgMap, sided = true;
			try {
				sgMap = await selectByIds(env,
					(ph) => `SELECT id, sga, sgb FROM entries WHERE id IN (${ph})`, ids);
			} catch (_) {
				// Pre-sides dump: one `sg`, always the a-side.
				sided = false;
				sgMap = await selectByIds(env,
					(ph) => `SELECT id, sg FROM entries WHERE id IN (${ph})`, ids);
			}
			const used = new Set();
			const bySide = {};
			for (const r of sgMap || []) {
				const a = sided ? r.sga : r.sg;
				const b = sided ? r.sgb : null;
				if (a != null || b != null) bySide[r.id] = { a, b };
				if (a != null) used.add(a);
				if (b != null) used.add(b);
			}
			for (const e of entries) {
				const m = bySide[e.id];
				if (!m) continue;
				if (m.a != null) e.sga = m.a;
				if (m.b != null) e.sgb = m.b;
			}
			const sgIds = [...used];
			if (sgIds.length) {
				const sgRows = await selectByIds(env,
					(ph) => `SELECT * FROM sense_groups WHERE id IN (${ph}) ORDER BY "key", no`,
					sgIds);
				senses = (sgRows || []).map((s) => {
					const o = { id: s.id, a: s.a, k: s.key, no: s.no, label: s.label };
					if (s.side) o.side = s.side;
					if (s.tr) o.tr = s.tr;
					if (s.dom) o.dom = s.dom; if (s.def) o.def = s.def; if (s.notes) o.notes = s.notes;
					return o;
				});
			}
		}
	} catch (_) {
		senses = []; // dump predates senses — degrade to flat results
	}

	const c = await conceptsP;
	const payload = { query: q, entries, senses, concepts: c.concepts };
	if (c.error) payload.concepts_error = c.error;
	return json(payload, origin);
}

async function handleMeta(env, origin) {
	const SRC_BASE =
		`slug, title, author, publisher, year, url, source_lang, target_lang,
		 primary_domain, subject_tags, licence, description, entry_count`;
	// `languages` and the concept counts are newer columns; tolerate an older
	// dump that lacks them so a Worker deploy that lands before the D1 reload
	// doesn't break /meta.
	let sources;
	for (const extra of [', languages, concept_count, term_count', ', languages', '']) {
		try {
			sources = (await env.DB.prepare(
				`SELECT ${SRC_BASE}${extra} FROM sources ORDER BY slug`
			).all()).results;
			break;
		} catch (err) {
			if (!extra) throw err;
		}
	}
	const [{ results: rawPairs }, count] = await Promise.all([
		env.DB.prepare(
			// Include monolingual entries (lb IS NULL): same-language glossaries
			// (e.g. English-only abbreviation lists) must be advertised too, as an
			// X→X pair, or the UI never offers a direction that can reach them.
			`SELECT DISTINCT la, lb FROM entries WHERE la IS NOT NULL`
		).all(),
		env.DB.prepare(`SELECT COUNT(*) AS n FROM entries`).first(),
	]);

	// Collapse (la, lb) into unordered pairs, matching the old lang_pairs shape.
	// A monolingual entry (no target language) collapses to an X→X pair so the
	// UI can offer a same-language direction for it.
	const seen = new Set();
	const lang_pairs = [];
	for (const p of rawPairs || []) {
		const a0 = p.la;
		const b0 = p.lb == null ? p.la : p.lb;
		const key = [a0, b0].sort().join('>');
		if (seen.has(key)) continue;
		seen.add(key);
		const [a, b] = [a0, b0].sort();
		lang_pairs.push({ a, b });
	}

	// Expose each source's full language set as an array (the dump stores it
	// comma-joined; fall back to source/target for older dumps).
	const sourcesOut = (sources || []).map((s) => ({
		...s,
		languages: s.languages
			? String(s.languages).split(',').map((c) => c.trim()).filter(Boolean)
			: [s.source_lang, s.target_lang].filter(Boolean),
	}));

	// A source shown as concepts has no entries of its own, so its language
	// pairs (German–French, Spanish–Italian, …) come from its language list.
	// Without this the From/To menus would lose every pair that only a
	// multilingual source covers.
	let concepts = 0, terms = 0;
	for (const s of sourcesOut) {
		if (!s.concept_count) continue;
		concepts += s.concept_count;
		terms += s.term_count || 0;
		const langs = s.languages;
		for (let i = 0; i < langs.length; i++) {
			for (let j = i + 1; j < langs.length; j++) {
				const [a, b] = [langs[i], langs[j]].sort();
				const key = a + '>' + b;
				if (seen.has(key)) continue;
				seen.add(key);
				lang_pairs.push({ a, b });
			}
		}
	}

	return json(
		{
			sources: sourcesOut,
			lang_pairs,
			counts: { sources: sourcesOut.length, entries: count ? count.n : 0, concepts, terms },
		},
		origin
	);
}

export default {
	async fetch(request, env) {
		const url = new URL(request.url);
		const origin = request.headers.get('Origin') || '';

		if (request.method === 'OPTIONS') {
			return new Response(null, { status: 204, headers: corsHeaders(origin) });
		}
		if (request.method !== 'GET') {
			return json({ error: 'method_not_allowed' }, origin, 405);
		}

		try {
			if (url.pathname === '/search') return await handleSearch(url, env, origin);
			if (url.pathname === '/meta') return await handleMeta(env, origin);
			if (url.pathname === '/' || url.pathname === '/health') {
				return json({ ok: true, service: 'wordbook-search' }, origin);
			}
			return json({ error: 'not_found' }, origin, 404);
		} catch (err) {
			return json({ error: 'internal', detail: String(err && err.message || err) }, origin, 500);
		}
	},
};
