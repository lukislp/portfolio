# portfolio

The personal site at **[lktec.org](https://lktec.org)** — a single hand-written page plus a legal
notice. No framework, no build step, no backend, no dependencies.

[![CI](https://github.com/lukislp/portfolio/actions/workflows/ci.yml/badge.svg)](https://github.com/lukislp/portfolio/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/lukislp/portfolio/badge)](https://securityscorecards.dev/viewer/?uri=github.com/lukislp/portfolio)

## Layout

```
public/            everything that is served — this is the Cloudflare Pages output directory
  index.html       the page itself (inline CSS + JS, DE/EN switch driven by data-i18n)
  impressum.html   legal notice, noindex
  404.html         not-found page
  _headers         response headers Cloudflare Pages applies (see below)
  favicon.svg  og-image.png  robots.txt  sitemap.xml
tools/
  check-site.py    the CI check: link/asset resolution, sitemap drift, meta tags, unclosed tags
```

Nothing outside `public/` is published.

## Local preview

```bash
python3 -m http.server 8000 --directory public
# http://localhost:8000
```

Two things only exist on a deployed Pages URL, not in the local server: `_headers` is a Pages
feature and is ignored here, and Pages serves pages without the `.html` extension, so the
`/impressum` link 404s locally while working in production. Both are verified on the preview
deployment a pull request produces.

## Checks

```bash
python3 tools/check-site.py public
```

Stdlib-only by design: a static site should not acquire a supply chain in order to be linted.
The same command runs in CI as the required `check` status.

## Deployment

Cloudflare Pages builds from `main`; every pull request gets its own preview URL.

| Setting | Value |
|---|---|
| Build command | *(none)* |
| Build output directory | `public` |
| Root directory | `/` |

`public/_headers` carries the response headers — the security set that the Caddy reverse proxy
applied while the site was hosted on the VPS (`X-Content-Type-Options`, `X-Frame-Options`,
`Referrer-Policy`), plus `Permissions-Policy`, `Cross-Origin-Opener-Policy` and a
Content-Security-Policy.

The CSP keeps `'unsafe-inline'` for scripts and styles because `index.html` uses an inline
`<style>` block, an inline `<script>` block and several inline `onclick=` attributes; nonces and
hashes do not cover inline event handlers. Moving those handlers to `addEventListener` is the
prerequisite for tightening it, and is the one worthwhile follow-up on this page.

## Scope

Only the site lives here. The demo applications that used to share a repository and a server with
it are containers behind a reverse proxy, stay on their own VPS, and are maintained separately.
