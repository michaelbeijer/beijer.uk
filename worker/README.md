# Wordbook search API (Cloudflare Worker + D1)

The public `/wordbook` search box calls this Worker. The Worker queries a **D1**
database (SQLite at Cloudflare's edge) and returns **only per-query result
snippets** — the terminology dataset is never shipped to the browser. That is
the copyright safeguard: visitors can look terms up, but cannot download the
curated corpus.

```
browser (beijer.uk/wordbook)
      │  GET /search?q=…   /meta
      ▼
  Worker (wordbook-search)        ← this folder
      │  SQL over FTS5
      ▼
  D1 "wordbook"  (loaded from the PRIVATE wordbook repo's master store)
```

The data lives only in the private `wordbook` repo and in D1. Nothing here
contains terminology data (`data/*.sql` is gitignored).

## Endpoints

| Route | Returns |
|---|---|
| `GET /meta` | Source inventory, language pairs (including those of multilingual sources), total counts (page-load payload). The entry count and the entries' language pairs come from `entry_stats`, which every publish (full or quick) fills on D1; without it, /meta counts all entries live (~0.6 s, ~3.5M rows read) and logs a warning. |
| `GET /search?q=<q>&limit=<n>` | FTS5 prefix search over term A / term B / definition. `limit` capped at 300. Also returns up to 20 multilingual `concepts` (a row of a multilingual source, whole, with all its languages), or `concepts_error` if that lookup failed. |
| `GET /concordance?q=<q>&from=<lang>&to=<lang>&offset=<n>` | EU legislation in context: up to 20 sentence pairs from DGT-TM in any two of `en`, `nl`, `fr`, `de`, `it`, `es`, containing `q` as an exact phrase on the `from` side, shortest first, each with its document's CELEX number. Without `to`, `en` pairs with `nl` and any other language with `en`. `total` is capped at 1,000 (`capped: true` beyond), `more` says whether another page exists (offset up to 400). From the separate `eu-legislation` D1 (binding `DGT`); without it the answer is `available: false`. |
| `GET /health` | Liveness check. |

CORS is locked to the site origins in `src/index.js` (`ALLOWED_ORIGINS`).

### Why the concordance query is never ranked

`eu-legislation` holds ~4.5 million rows, each one sentence in up to six
languages, numbered shortest first when it is built. `/concordance` returns
matches in that order (`ORDER BY rowid`), which FTS5 serves without looking at
every match, and stops at the LIMIT. A common word therefore costs the same as
a rare one. Ranking with `bm25()` would score every match first: millions of
rows for "the". Keep it that way.

Each pair of languages has a column, `n_<a>_<b>` (codes in alphabetical
order, e.g. `n_fr_nl`), set only on the first row holding each distinct
sentence pair, to how often that pair occurs. `/concordance` keeps the rows
where it is set, so every pair is listed once; the filter is checked row by
row as FTS5 hands rows over, so the LIMIT still ends the scan.

## One-time setup

```bash
cd worker
npm install
npx wrangler login

# 1. Create the D1 database (prints a database_id)
npx wrangler d1 create wordbook
#    → paste the printed database_id into wrangler.toml (database_id = "…")
```

## Loading / refreshing the data

Whenever the master store changes, regenerate the dump in the **private**
`wordbook` repo and load it into D1:

```bash
# In the private wordbook repo:
wordbook build-d1 --out data/d1_dump.sql

# Copy the dump here (gitignored), then load the REMOTE D1:
cp ../../Wordbook/data/d1_dump.sql ./data/d1_dump.sql
npx wrangler d1 execute wordbook --remote --file=./data/d1_dump.sql
```

The dump drops + recreates all its tables (sources, entries, sense groups,
concepts and their search indexes), so a reload fully refreshes D1.

### EU legislation in context (`eu-legislation`)

A second D1 database, loaded once and refreshed only when a new DGT-TM release
appears. It is about 7 GB (D1's limit is 10 GB per database), so it is kept
out of the `wordbook` dump. Built in the private repo (`beijerterm-database`,
see its README) from the OPUS files in `D:\Corpora\dgt-tm\original\`:

```bash
# In beijerterm-database:
wordbook dgt-build --original D:/Corpora/dgt-tm/original --out D:/Corpora/dgt-tm/dgt.db
wordbook dgt-d1 --db D:/Corpora/dgt-tm/dgt.db --out-dir D:/Corpora/dgt-tm/d1

# Once: create the database and paste its id into wrangler.toml (binding DGT).
npx wrangler d1 create eu-legislation --location weur

# Load the files IN NAME ORDER. 000-schema.sql drops and recreates every
# table, so if a file fails, start again from 000.
for f in D:/Corpora/dgt-tm/d1/*.sql; do
  npx wrangler d1 execute eu-legislation --remote --yes --file="$f" || break
done
```

To refresh it without a gap on the site, load a NEW database, then point the
`DGT` binding at it and deploy: the switch is the deploy. The Worker code and
the database go together (the query names the `n_<a>_<b>` columns), so never
deploy this code against a database built before them. Until 2026-11 the
binding pointed at `dgt-tm`, an English–Dutch-only database with a different
layout.

## Deploy

```bash
npx wrangler deploy        # prints the https://wordbook-search.<sub>.workers.dev URL
```

## Wire the front-end to the deployed Worker

Set the Worker URL as a build-time variable so the static site calls it:

1. GitHub → repo **beijer.uk** → Settings → Secrets and variables → Actions →
   **Variables** → New variable: `PUBLIC_WORDBOOK_API` =
   `https://wordbook-search.<sub>.workers.dev`
2. Re-run the Pages deploy (push any commit, or "Run workflow").

The build passes `PUBLIC_WORDBOOK_API` to Astro (see `.github/workflows/deploy.yml`).
If the variable is unset, the page shows "Search API not configured" rather than
shipping any data — safe by default.

## Local development

```bash
# Load a local D1 (Miniflare) from a dump, then run the Worker:
npx wrangler d1 execute wordbook --local --file=./data/d1_dump.sql
npm run dev        # serves on http://127.0.0.1:8787
```

In `astro dev`, the front-end auto-targets `http://127.0.0.1:8787`, so running
the Worker locally is all that's needed to exercise the full search on
`localhost:4321/wordbook/`.
