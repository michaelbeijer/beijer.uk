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
 *   GET /search?q=<query>&limit=<n>
 *     FTS5 prefix search over (a, b, def). Returns matching entries in the
 *     same compact shape the old static snapshot used, so the front-end's
 *     direction-grouping logic is unchanged. `limit` is capped server-side.
 *
 * D1 schema is produced by the private repo's `wordbook build-d1` command and
 * loaded with `wrangler d1 execute`. See worker/README.md for the runbook.
 */

const ALLOWED_ORIGINS = new Set([
	'https://beijerterm.com',      // canonical Beijerterm site (Cloudflare Pages)
	'https://www.beijerterm.com',
	'https://beijer.uk',           // hand-off search box on the main site
	'https://www.beijer.uk',
	'http://localhost:4321',       // Astro dev
	'http://127.0.0.1:4321',
	'http://localhost:8788',       // wrangler pages dev
]);

const MAX_LIMIT = 100;
const DEFAULT_LIMIT = 50;

// Also trust this account's own *.workers.dev / *.pages.dev preview subdomains
// (e.g. beijerterm.michaelbeijer-co-uk.workers.dev) so previews work before the
// custom domain is attached. The custom domains above are the real surfaces.
function isAllowedOrigin(origin) {
	if (ALLOWED_ORIGINS.has(origin)) return true;
	return /^https:\/\/[a-z0-9-]+\.michaelbeijer-co-uk\.(workers|pages)\.dev$/.test(origin || '');
}

function corsHeaders(origin) {
	const allow = isAllowedOrigin(origin) ? origin : 'https://beijerterm.com';
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
 * punctuation, then AND the tokens together with prefix matching so "octrooi"
 * also matches "octrooien". Mirrors the local search.py logic.
 */
function toFtsQuery(q) {
	const cleaned = (q || '').replace(/["'()*:.,;?!\[\]{}^$~-]/g, ' ').trim();
	if (!cleaned) return '';
	const tokens = cleaned.split(/\s+/).filter(Boolean);
	if (!tokens.length) return '';
	return tokens.map((t) => `"${t}"*`).join(' AND ');
}

async function handleSearch(url, env, origin) {
	const q = url.searchParams.get('q') || '';
	let limit = parseInt(url.searchParams.get('limit') || '', 10);
	if (!Number.isFinite(limit) || limit <= 0) limit = DEFAULT_LIMIT;
	limit = Math.min(limit, MAX_LIMIT);

	const fts = toFtsQuery(q);
	if (!fts) return json({ query: q, entries: [] }, origin);

	const stmt = env.DB.prepare(
		`SELECT e.id, e.la, e.a, e.qa, e.lb, e.b, e.qb,
		        e.reg, e.pos, e.dom, e.def, e.srcs,
		        bm25(entries_fts) AS rank
		 FROM entries_fts
		 JOIN entries e ON e.id = entries_fts.rowid
		 WHERE entries_fts MATCH ?
		 ORDER BY rank
		 LIMIT ?`
	).bind(fts, limit);

	const { results } = await stmt.all();
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
		if (r.srcs) o.src = r.srcs;
		return o;
	});
	return json({ query: q, entries }, origin);
}

async function handleMeta(env, origin) {
	const sourcesP = env.DB.prepare(
		`SELECT slug, title, author, publisher, year, url,
		        source_lang, target_lang, primary_domain, subject_tags,
		        licence, description, entry_count
		 FROM sources ORDER BY slug`
	).all();
	const pairsP = env.DB.prepare(
		`SELECT DISTINCT la, lb FROM entries WHERE la IS NOT NULL AND lb IS NOT NULL`
	).all();
	const countP = env.DB.prepare(`SELECT COUNT(*) AS n FROM entries`).first();

	const [{ results: sources }, { results: rawPairs }, count] = await Promise.all([
		sourcesP,
		pairsP,
		countP,
	]);

	// Collapse (la, lb) into unordered pairs, matching the old lang_pairs shape.
	const seen = new Set();
	const lang_pairs = [];
	for (const p of rawPairs || []) {
		const key = [p.la, p.lb].sort().join('>');
		if (seen.has(key)) continue;
		seen.add(key);
		const [a, b] = [p.la, p.lb].sort();
		lang_pairs.push({ a, b });
	}

	return json(
		{
			sources: sources || [],
			lang_pairs,
			counts: { sources: (sources || []).length, entries: count ? count.n : 0 },
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
