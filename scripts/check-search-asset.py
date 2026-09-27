#!/usr/bin/env python3
"""Pin the reviewed search asset only; do not advance the whole shared version.

Source: itdojp/book-formatter@ea6f970e23b93e27260cf55f408c7b4ff19faf66
        shared/assets/js/search.js (PR161, DOM text/mark construction).
An intentional update needs an audited source, behavioral review, and a new
checksum. This byte gate complements that review; it is not a DOM simulator.
"""
import argparse
import hashlib
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "856d6f1540af2dda82d193af041ab243a8fa3a03bf6b81a22a7cd6a790a234ab"
SOURCE = ROOT / "docs/assets/js/search.js"
LAYOUT = ROOT / "docs/_layouts/book.html"
SCRIPT_REFERENCE = "<script defer src=\"{{ '/assets/js/search.js' | relative_url }}\"></script>"


def check_asset(data: bytes) -> None:
    if hashlib.sha256(data).hexdigest() != EXPECTED_SHA256:
        raise ValueError("search.js differs from the reviewed DOM-safe source; re-audit before updating the pin")


class SearchScriptParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references = 0

    def handle_starttag(self, tag, attrs) -> None:
        if tag != "script":
            return
        expected = "{{ '/assets/js/search.js' | relative_url }}"
        if not any(key == "src" and value == expected for key, value in attrs):
            return
        names = [key for key, _ in attrs]
        if len(names) != len(set(names)) or "defer" not in names:
            raise ValueError("reviewed search script needs defer and unique attributes")
        self.references += 1


def check_layout(text: str) -> None:
    parser = SearchScriptParser()
    parser.feed(text)
    parser.close()
    if parser.references != 1:
        raise ValueError("book layout must load the reviewed search asset exactly once")
    for marker in ('id="search-input"', 'id="search-results"', 'class="page-content"'):
        if marker not in text:
            raise ValueError(f"book layout lacks search integration: {marker}")


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
        check_layout(layout.replace(SCRIPT_REFERENCE, equivalent))
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
    main()
