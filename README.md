# docs.viaduct.dev

Builds and deploys [docs.viaduct.dev](https://docs.viaduct.dev) from [airbnb/viaduct](https://github.com/airbnb/viaduct). **No content lives here** -- this repo only controls build, deployment, and the thin config layer on top of the upstream source.

## Repo structure

```
overlays/
  patch-mkdocs.py             # generates nav from upstream, writes to override config
  docs/
    mkdocs-override.yml       # INHERIT-based config (site_url, plugins, homepage)
test/
  Dockerfile                  # full build pipeline (MkDocs + Dokka)
  docker-compose.yml          # local dev server + link checker
  server.go                   # minimal static file server for the container
  lychee.toml                 # link checker exclusions
.github/workflows/
  deploy-docs.yml             # build + deploy to GitHub Pages
  lint.yml                    # ruff on patch-mkdocs.py
```

## How it works

1. Clone `airbnb/viaduct` at a given ref
2. Copy `overlays/` on top of the clone
3. `patch-mkdocs.py` reads the upstream `docs/mkdocs.yml` nav, keeps sections in `KEEP`, rejects anything not in `KEEP` or `STRIP` (build fails on unknown sections), fixes paths for the flatten step, and appends the nav to `mkdocs-override.yml`
4. Flatten `docs/docs/docs/` up one level so content serves at `/developers/` not `/docs/developers/`; copy the upstream docs landing page to `index.md`
5. Strip non-docs content (about, blog, community, roadmap)
6. `mkdocs build -f mkdocs-override.yml`
7. Dokka generates API references at `/apis/tenant-api/` and `/apis/service/`

## Config: mkdocs-override.yml

Uses MkDocs [`INHERIT`](https://www.mkdocs.org/user-guide/configuration/#configuration-inheritance) to extend the upstream `mkdocs.yml`. We only override what differs:

- `site_url` -- `https://docs.viaduct.dev` instead of the upstream domain
- `plugins` -- drops the `blog` plugin (we strip blog content)
- `extra.homepage` -- logo links to `https://viaduct.airbnb.tech/`

Everything else (theme, hooks, extensions, CSS, analytics) flows through from upstream automatically.

## Nav parity check

`patch-mkdocs.py` has two sets: `KEEP` (sections we publish) and `STRIP` (sections we intentionally exclude). If upstream adds a new top-level nav section that isn't in either set, the build fails:

```
patch-mkdocs.py: ERROR -- unknown upstream nav section 'Changelog'; add it to KEEP or STRIP
```

Edit the sets in `patch-mkdocs.py` to resolve.

## Local testing

See [test/README.md](test/README.md) for details. Quick start:

```bash
cd test
docker compose build
docker compose up                                            # http://localhost:8080
docker compose --profile linkcheck run --rm linkcheck        # check links
```

## CI / deployment

**`deploy-docs.yml`** runs on pushes to `main` (when `overlays/`, `test/`, or the workflow itself changes), weekly (skips if upstream hasn't changed), and manual dispatch. Pipeline: build, link check, deploy to GitHub Pages.

**`lint.yml`** runs on pushes that touch `*.py` files or the workflow itself.

## Switching domains

Update `SITE_URL` in both `deploy-docs.yml` and `test/Dockerfile`, then update DNS and the GitHub Pages custom domain setting.
