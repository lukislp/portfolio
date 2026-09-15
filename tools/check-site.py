#!/usr/bin/env python3
"""Static checks for the portfolio site in public/.

Deliberately stdlib-only: the site has no build step and no runtime dependencies, and the
repository should not acquire a supply chain just to lint six files. Catches the mistakes that
actually happen when hand-editing HTML - a link or asset that no longer resolves, a sitemap that
drifted away from the pages that exist, a missing social-preview tag, malformed markup.

Usage: python3 tools/check-site.py [root]   (default root: public)
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

SITE_ORIGIN = "https://lktec.org"
REQUIRED_META = [
    ("name", "description"),
    ("property", "og:title"),
    ("property", "og:description"),
    ("property", "og:image"),
    ("property", "og:url"),
    ("name", "twitter:card"),
]
# Attributes that carry a URL we want to resolve.
URL_ATTRS = {"href", "src", "content"}
VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
# Elements whose end tag the HTML spec allows to be omitted - leaving these open is legal and
# must not be reported, otherwise the check cries wolf on perfectly valid markup.
OPTIONAL_END_TAGS = {
    "body", "dd", "dt", "head", "html", "li", "optgroup", "option", "p", "rp", "rt",
    "tbody", "td", "tfoot", "th", "thead", "tr",
}

errors: list[str] = []


def fail(path: Path, message: str) -> None:
    errors.append(f"{path}: {message}")


class PageParser(HTMLParser):
    """Collects referenced URLs, meta tags and an element stack to spot unclosed tags."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.refs: list[tuple[str, int]] = []
        self.metas: list[dict[str, str]] = []
        self.stack: list[tuple[str, int]] = []
        self.unclosed: list[tuple[str, int]] = []
        self.title: str | None = None
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {k: (v or "") for k, v in attrs}
        if tag == "meta":
            self.metas.append(attr)
        if tag == "title":
            self._in_title = True
        # <meta content="..."> is only a URL for the og:/twitter: image and url tags.
        for name in URL_ATTRS:
            if name not in attr:
                continue
            if name == "content" and attr.get("property", attr.get("name", "")) not in {
                "og:image", "og:url", "twitter:image",
            }:
                continue
            self.refs.append((attr[name], self.getpos()[0]))
        if tag not in VOID_ELEMENTS:
            self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] != tag:
                continue
            # Everything still open above the matched tag is implicitly closed by this end tag,
            # which means it was never closed properly.
            for orphan, line in self.stack[index + 1:]:
                if orphan not in OPTIONAL_END_TAGS:
                    self.unclosed.append((orphan, line))
            del self.stack[index:]
            return

    def handle_data(self, data: str) -> None:
        if self._in_title and data.strip():
            self.title = data.strip()


def resolve(root: Path, page: Path, raw: str) -> Path | None:
    """Map a reference to a file inside root, or None when it is not ours to check."""
    ref = raw.strip()
    if not ref or ref.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
        return None
    parsed = urlparse(ref)
    if parsed.scheme in {"http", "https"}:
        # Only our own origin is resolvable locally; external links are not fetched on purpose,
        # so a CI run never depends on somebody else's uptime.
        if f"{parsed.scheme}://{parsed.netloc}" != SITE_ORIGIN:
            return None
        path = parsed.path or "/"
    elif parsed.scheme:
        return None
    else:
        path = parsed.path
    if not path:
        return None
    target = root / path.lstrip("/") if path.startswith("/") else page.parent / path
    target = Path(unquote(str(target)))
    if str(target).endswith(("/", "\\")):
        return target / "index.html"
    # Cloudflare Pages serves HTML without the extension and 308-redirects "/x.html" to "/x",
    # so the canonical internal link "/impressum" has to resolve to public/impressum.html.
    if not target.suffix and not target.exists():
        with_html = target.with_name(target.name + ".html")
        if with_html.exists():
            return with_html
    return target


def check_page(root: Path, page: Path) -> None:
    parser = PageParser()
    try:
        parser.feed(page.read_text(encoding="utf-8"))
        parser.close()
    except Exception as exc:  # noqa: BLE001 - any parse failure is a finding
        fail(page, f"could not be parsed: {exc}")
        return

    leftover = [(tag, line) for tag, line in parser.stack if tag not in OPTIONAL_END_TAGS]
    for tag, line in parser.unclosed + leftover:
        fail(page, f"<{tag}> opened on line {line} is never closed")
    if not parser.title:
        fail(page, "has no non-empty <title>")

    for raw, line in parser.refs:
        target = resolve(root, page, raw)
        if target is not None and not target.exists():
            fail(page, f"line {line}: '{raw}' does not resolve to a file in {root}/")

    # Social-preview and SEO tags only matter on the indexable landing page.
    if page.name == "index.html":
        present = {
            (key, attrs[key])
            for attrs in parser.metas
            for key in ("name", "property")
            if key in attrs
        }
        for key, value in REQUIRED_META:
            if (key, value) not in present:
                fail(page, f"missing <meta {key}=\"{value}\">")


def check_sitemap(root: Path) -> None:
    sitemap = root / "sitemap.xml"
    if not sitemap.exists():
        fail(sitemap, "is missing")
        return
    try:
        tree = ET.fromstring(sitemap.read_text(encoding="utf-8"))
    except ET.ParseError as exc:
        fail(sitemap, f"is not valid XML: {exc}")
        return
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [element.text or "" for element in tree.findall(".//sm:loc", ns)]
    if not locs:
        fail(sitemap, "contains no <loc> entries")
    for loc in locs:
        if not loc.startswith(SITE_ORIGIN):
            fail(sitemap, f"'{loc}' does not point at {SITE_ORIGIN}")
            continue
        target = resolve(root, root / "sitemap.xml", loc)
        if target is not None and not target.exists():
            fail(sitemap, f"'{loc}' has no corresponding file in {root}/")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "public")
    if not root.is_dir():
        print(f"::error::site root '{root}' does not exist")
        return 1

    pages = sorted(root.rglob("*.html"))
    if not pages:
        print(f"::error::no HTML pages found in '{root}'")
        return 1

    for page in pages:
        check_page(root, page)
    check_sitemap(root)

    for required in ("_headers", "404.html", "robots.txt", "favicon.svg"):
        if not (root / required).exists():
            fail(root / required, "is missing")

    for message in errors:
        print(f"::error::{message}")
    checked = ", ".join(page.name for page in pages)
    print(f"checked {len(pages)} page(s): {checked}")
    print("FAILED" if errors else "ok")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
