#!/usr/bin/env python3
"""Pin the reviewed search asset only; do not advance the whole shared version.

Source: itdojp/book-formatter@ea6f970e23b93e27260cf55f408c7b4ff19faf66
        shared/assets/js/search.js (PR161, DOM text/mark construction).
An intentional update needs an audited source, behavioral review, and a new
checksum. This byte gate complements that review; it is not a DOM simulator.
"""
import argparse
import hashlib
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "856d6f1540af2dda82d193af041ab243a8fa3a03bf6b81a22a7cd6a790a234ab"
SOURCE = ROOT / "docs/assets/js/search.js"
LAYOUT = ROOT / "docs/_layouts/book.html"
SCRIPT_REFERENCE = "<script defer src=\"{{ '/assets/js/search.js' | relative_url }}\"></script>"


def check_asset(data: bytes) -> None:
    if hashlib.sha256(data).hexdigest() != EXPECTED_SHA256:
        raise ValueError("search.js differs from the reviewed DOM-safe source; re-audit before updating the pin")


class SearchScriptParser(HTMLParser):
    # A bounded source-layout guard, not a Liquid/JavaScript/browser evaluator.
    # Integration inside raw-text, inert, or non-HTML containers is unsupported.
    INERT = {"template", "noscript", "textarea", "title", "style", "script",
             "xmp", "iframe", "noembed", "noframes", "plaintext", "svg", "math"}

    def __init__(self) -> None:
        super().__init__()
        self.references = 0
        self.inert = []
        self.ids = {"search-input": 0, "search-results": 0}
        self.content = 0

    def handle_starttag(self, tag, attrs) -> None:
        active = not self.inert
        if tag in self.INERT:
            self.inert.append(tag)
        if not active:
            return
        values = dict(attrs)
        if tag == "script":
            # Reject alternative literal/Liquid spellings, rather than guessing
            # their runtime equivalence; they must not hide a second load.
            sources = [value or "" for key, value in attrs if key == "src"]
            if not any("search.js" in unquote(value) for value in sources):
                return
            expected = "{{ '/assets/js/search.js' | relative_url }}"
            names = [key for key, _ in attrs]
            if sources != [expected] or len(names) != len(set(names)) or "defer" not in names:
                raise ValueError("search script requires canonical src, defer, and unique attributes")
            self.references += 1
            return
        if tag in self.INERT:
            return
        ident = values.get("id")
        if ident in self.ids:
            if ident == "search-input" and tag != "input":
                raise ValueError("search-input must be a live input element")
            self.ids[ident] += 1
        if "page-content" in (values.get("class") or "").split():
            self.content += 1

    def handle_endtag(self, tag) -> None:
        if tag in self.inert:
            # Only the bounded unsupported-container stack is tracked.
            index = len(self.inert) - 1 - self.inert[::-1].index(tag)
            del self.inert[index:]

    def handle_startendtag(self, tag, attrs) -> None:
        if tag == "script":
            raise ValueError("self-closing script tags are unsupported")
        super().handle_startendtag(tag, attrs)


def check_layout(text: str) -> None:
    parser = SearchScriptParser()
    parser.feed(text)
    parser.close()
    if parser.references != 1:
        raise ValueError("book layout must load the reviewed search asset exactly once")
    if any(count != 1 for count in parser.ids.values()) or parser.content != 1:
        raise ValueError("book layout needs one live search-input, search-results, and page-content")


def self_test(data: bytes) -> None:
    # Exercise the parser independently of the canonical layout's formatting.
    layout = ('<input id="search-input"><div id="search-results"></div>'
              '<main class="page-content"></main>' + SCRIPT_REFERENCE)
    cases = [(check_asset, b""), (check_asset, data[:-1]),
             (check_asset, data + b"\n"),
             (check_layout, layout.replace(SCRIPT_REFERENCE, "")),
             (check_layout, layout + SCRIPT_REFERENCE),
             (check_layout, layout.replace('id="search-input"', 'id="unused-input"')),
             (check_layout, layout.replace(SCRIPT_REFERENCE, '<!-- ' + SCRIPT_REFERENCE + ' -->')),
             (check_layout, layout.replace(SCRIPT_REFERENCE, SCRIPT_REFERENCE.replace('defer ', ''))),
             (check_layout, layout.replace(SCRIPT_REFERENCE, SCRIPT_REFERENCE.replace('<script ', '<script src="other.js" ')))]
    for container in ("template", "noscript", "textarea", "svg"):
        cases.append((check_layout, layout.replace(SCRIPT_REFERENCE,
                      f"<{container}>" + SCRIPT_REFERENCE + f"</{container}>")))
    for alternate in ("{{ site.baseurl }}/assets/js/search.js", "/assets/js/search.js", "/assets/js/search%2ejs"):
        cases.append((check_layout, layout + f'<script defer src="{alternate}"></script>'))
    for marker in ('<input id="search-input">', '<div id="search-results"></div>',
                   '<main class="page-content"></main>'):
        cases.append((check_layout, layout.replace(marker, '<!-- ' + marker + ' -->')))
    cases.append((check_layout, layout + '<input id="search-input">'))
    cases.append((check_layout, layout.replace('<input id="search-input">', '<div id="search-input"></div>')))
    for check, value in cases:
        try:
            check(value)
        except ValueError:
            continue
        raise AssertionError("invalid asset/layout mutation was accepted")
    # HTML-equivalent formatting/attribute order must not invalidate the gate.
    for equivalent in [
        SCRIPT_REFERENCE.replace('<script defer src=', '<script src=').replace('></script>', ' defer></script>'),
        SCRIPT_REFERENCE.replace('defer src=', 'defer\n  data-purpose="search"\n  src='),
    ]:
        check_layout(layout.replace(SCRIPT_REFERENCE, equivalent)
                     .replace('id="search-input"', "id='search-input'")
                     .replace('class="page-content"', 'class="reader page-content"'))
    print(f"Search asset self-test passed ({len(cases)} negative mutations; 2 equivalent-layout positives).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    data, layout = SOURCE.read_bytes(), LAYOUT.read_text(encoding="utf-8")
    check_asset(data)
    check_layout(layout)
    if args.self_test:
        self_test(data)
    print("Reviewed search asset and layout integration passed.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"Search asset contract failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
