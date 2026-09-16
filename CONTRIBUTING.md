# Contributing to portfolio

Thanks for taking the time. This is the source of a single personal site
([lktec.org](https://lktec.org)) and a single-maintainer project, so the process is deliberately
small - but it is the same for every change, including the maintainer's own.

The content of the page is a personal CV, so corrections (a broken link, a typo, a wrong date, a
rendering bug in some browser) are far more useful here than rewrites of what the page says about
its author.

## How changes get in

1. Open an issue first for anything bigger than a typo or an obvious bug fix, so the direction can
   be agreed before you spend time on it. Use the templates under `.github/ISSUE_TEMPLATE/`.
2. Fork the repository (or branch, if you have write access) and make your change on a branch.
3. Open a pull request against `main`. The pull-request template asks for what changed and why.
4. `main` is protected: a PR merges only after the required checks are green and the branch is up
   to date with `main` (enable auto-merge and it lands on its own once that is the case). Nobody
   pushes to `main` directly, not even the maintainer.
5. Merging to `main` publishes. Cloudflare Pages deploys `public/` straight from `main`, so there
   is no release step, no tag and no changelog between a merge and the live site.

## What a pull request needs

- **Conventional Commits.** `fix:`, `feat:`, `ci:`, `docs:`, `style:`, `refactor:` and so on.
  Squash-merge keeps the PR title as the commit message, so give the PR a Conventional Commit
  title - the history is the only record of what changed on the site.
- **Green required checks.** `check` (the job in [`.github/workflows/ci.yml`](.github/workflows/ci.yml))
  and `review / dependency-review` are required; a red one blocks the merge. CodeQL runs on the
  workflows and on `tools/` through GitHub's default setup and blocks on errors and high-severity
  alerts.
- **The site check passes.** `python3 tools/check-site.py public` is exactly what CI runs. It
  resolves every link and asset, compares `public/sitemap.xml` against the files that actually
  exist, requires the social-preview meta tags, and looks for unclosed elements. Run it before
  pushing.
- **No build step and no dependencies.** `public/` is served as it is, and `tools/check-site.py`
  is stdlib-only on purpose. A change that introduces a package manager, a bundler, a framework
  or a runtime dependency needs a very good reason - the absence of a supply chain is a feature of
  this repository, not an omission.
- **Both languages.** The page switches between German and English from the `i18n` object in
  `public/index.html`, keyed by the `data-i18n` attributes in the markup. New user-facing text
  needs a `de` and an `en` entry; a key that exists in only one language shows up as a gap for
  half the visitors.
- **New pages are wired up.** A new file under `public/` that should be indexed belongs in
  `public/sitemap.xml` as well, or the check fails on the drift.
- **Response headers.** `public/_headers` is a Cloudflare Pages feature and carries the security
  headers including the Content-Security-Policy. If a change needs a new origin (a font, an image
  host), the CSP has to be widened in the same pull request - and the narrower option is usually
  to inline or self-host the asset instead.
- **No personal data beyond what is already public.** The page intentionally carries a legal
  notice; nothing else belongs in the repository.

## Running things locally

```bash
# Serve the site
python3 -m http.server 8000 --directory public
# http://localhost:8000

# The check CI runs
python3 tools/check-site.py public
```

Two things only exist on a deployed Pages URL, not in that local server: `_headers` is ignored,
and Pages serves pages without the `.html` extension, so the `/impressum` link 404s locally while
working in production. Every pull request gets its own Cloudflare Pages preview URL - check
anything that depends on either of those there.

## Security issues

Please do not open a public issue for a vulnerability - use the private reporting path described
in [SECURITY.md](SECURITY.md). The [Code of Conduct](CODE_OF_CONDUCT.md) applies to every
interaction in this repository.
