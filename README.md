# portfolio

The personal site at **[lktec.org](https://lktec.org)** — a single hand-written page plus a legal
notice. No framework, no build step, no backend, no dependencies.

[![CI](https://github.com/lukislp/portfolio/actions/workflows/ci.yml/badge.svg)](https://github.com/lukislp/portfolio/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/lukislp/portfolio/badge)](https://securityscorecards.dev/viewer/?uri=github.com/lukislp/portfolio)

## Layout

```
public/            everything that is served — this is the Cloudflare Pages output directory
  index.html       the German page and the single source of truth (inline CSS + JS)
  en/index.html    the English page — GENERATED, do not edit
  sitemap.xml      GENERATED
  impressum.html   legal notice, noindex
  404.html         not-found page
  _headers         response headers Cloudflare Pages applies (see below)
  favicon.svg  og-image.png  robots.txt
tools/
  build.py         renders public/en/ and sitemap.xml from public/index.html
  check-site.py    link/asset resolution, sitemap drift, meta tags, hreflang, unclosed tags
```

Nothing outside `public/` is published.

## Languages

`public/index.html` holds the German copy in its markup and both languages in its `i18n` object.
`tools/build.py` renders the English variant into `public/en/` with the English text baked into
the HTML, so search engines get a real indexable URL per language instead of a switch that only
exists in JavaScript. The two pages reference each other with `hreflang`, and the language toggle
navigates between them.

**Edit `public/index.html`, never `public/en/index.html`.** After editing:

```bash
python3 tools/build.py      # regenerate the English page and the sitemap
```

CI runs `tools/build.py --check` and fails if the generated files are out of date.

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
