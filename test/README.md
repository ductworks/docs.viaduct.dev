# Local testing

Everything runs in Docker. The build produces the same output as CI.

## Services

**`docs`** -- Multi-stage build that clones upstream, applies overlays, runs MkDocs + Dokka, and serves the result on port 8080 via a minimal Go static file server. Has a health check so dependent services can wait for it.

**`linkcheck`** (profile: `linkcheck`) -- Runs [lychee](https://github.com/lycheeverse/lychee) against the docs container. Waits for the health check before starting. Exclusions are in `lychee.toml`.

## Usage

```bash
# Build and serve
docker compose build
docker compose up                    # http://localhost:8080

# Build from a specific upstream ref
SOURCE_REF=v0.28.0 docker compose build

# Run link checker
docker compose --profile linkcheck run --rm linkcheck

# Full rebuild (no Docker layer cache)
docker compose build --no-cache
```

## Build args

| Arg | Default | Purpose |
|-----|---------|---------|
| `SOURCE_REF` | `main` | Upstream branch, tag, or commit SHA to build from |
| `SITE_URL` | `http://localhost:8080` | Base URL baked into the site (canonical links, sitemap) |

## Java toolchains

The Dockerfile bundles both Java 17 and 21. Upstream modules require Java 17 for compilation; Dokka runs on 21. Both are baked into the image so Gradle never needs to download a JDK at build time.
