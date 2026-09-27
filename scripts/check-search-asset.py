#!/usr/bin/env python3
"""Pin the reviewed search asset only; do not advance the whole shared version.

Source: itdojp/book-formatter@ea6f970e23b93e27260cf55f408c7b4ff19faf66
        shared/assets/js/search.js (PR161, DOM text/mark construction).
An intentional update needs an audited source, behavioral review, and a new
checksum. This byte gate complements that review; it is not a DOM simulator.
"""
import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "856d6f1540af2dda82d193af041ab243a8fa3a03bf6b81a22a7cd6a790a234ab"
SOURCE = ROOT / "docs/assets/js/search.js"
LAYOUT = ROOT / "docs/_layouts/book.html"
SCRIPT_REFERENCE = "<script defer src=\"{{ '/assets/js/search.js' | relative_url }}\"></script>"


def check_asset(data: bytes) -> None:
    if hashlib.sha256(data).hexdigest() != EXPECTED_SHA256:
        raise ValueError("search.js differs from the reviewed DOM-safe source; re-audit before updating the pin")


def check_layout(text: str) -> None:
    if text.count(SCRIPT_REFERENCE) != 1:
        raise ValueError("book layout must load the reviewed search asset exactly once")
    for marker in ('id="search-input"', 'id="search-results"', 'class="page-content"'):
        if marker not in text:
            raise ValueError(f"book layout lacks search integration: {marker}")


def self_test(data: bytes, layout: str) -> None:
    cases = [(check_asset, b""), (check_asset, data[:-1]),
             (check_asset, data + b"\n"),
             (check_layout, layout.replace(SCRIPT_REFERENCE, "")),
             (check_layout, layout + SCRIPT_REFERENCE),
             (check_layout, layout.replace('id="search-input"', 'id="unused-input"'))]
    for check, value in cases:
        try:
            check(value)
        except ValueError:
            continue
        raise AssertionError("invalid asset/layout mutation was accepted")
    print(f"Search asset self-test passed ({len(cases)} negative mutations).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    data, layout = SOURCE.read_bytes(), LAYOUT.read_text(encoding="utf-8")
    check_asset(data)
    check_layout(layout)
    if args.self_test:
        self_test(data, layout)
    print("Reviewed search asset and layout integration passed.")


if __name__ == "__main__":
    main()
