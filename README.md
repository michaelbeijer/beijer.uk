# beijer.uk

Professional website of Michael Beijer (Dutch↔English patent & technical translator).

## Development

```bash
npm install
npm run dev
```

## Admin Panel

See [AGENTS.md](AGENTS.md) for admin panel documentation.

```bash
cd admin
pip install -r requirements.txt
python start_dev.py
```

## Deployment

The GitHub Actions workflow deploys the built site to GitHub Pages.

- Build output: `dist/`
- Custom domain: `public/CNAME`

If you ever need to deploy under a subpath (e.g. `/<repo>/`), set `ASTRO_BASE` in the workflow.
