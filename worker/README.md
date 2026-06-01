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
| `GET /meta` | Source inventory, language pairs, total counts (page-load payload). |
| `GET /search?q=<q>&limit=<n>` | FTS5 prefix search over term A / term B / definition. `limit` capped at 100. |
| `GET /health` | Liveness check. |

CORS is locked to the site origins in `src/index.js` (`ALLOWED_ORIGINS`).

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

The dump drops + recreates its three tables, so a reload fully refreshes D1.

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
