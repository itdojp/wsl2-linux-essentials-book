#!/usr/bin/env python3
"""Validate WSL2 book metadata, navigation, and published route coverage.

The repository primarily publishes the `docs/` tree.  This check is intentionally
stdlib-only so it can run in local `npm test`, CI, and Book QA without adding a
runtime dependency.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

EXPECTED = {
    "title": "WSL2 Linux実践ガイド",
    "description": "illustrated-linux-basics-book の次のステップとして、WSL2 上で実践的な Linux スキルを習得するための技術書",
    "author": "株式会社アイティードゥ",
    "version": "2.0.1",
    "repository": "https://github.com/itdojp/wsl2-linux-essentials-book",
    "repository_full": "itdojp/wsl2-linux-essentials-book",
    "repository_git": "git+https://github.com/itdojp/wsl2-linux-essentials-book.git",
    "homepage": "https://itdojp.github.io/wsl2-linux-essentials-book/",
    "baseurl": "/wsl2-linux-essentials-book",
    "url": "https://itdojp.github.io",
    "license": "CC BY-NC-SA 4.0",
    "license_npm": "CC-BY-NC-SA-4.0",
}

REQUIRED_ASSETS = [
    "assets/css/main.css",
    "assets/css/syntax-highlighting.css",
    "assets/js/theme.js",
    "assets/js/search.js",
    "assets/js/code-copy-lightweight.js",
]

STRUCTURE_SECTIONS = ("chapters", "resources")
NAV_SECTIONS = ("introduction", "chapters", "additional", "resources", "appendices", "afterword")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"required file is missing: {path.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def read_simple_yaml_scalars(path: Path) -> dict[str, str]:
    """Read top-level scalar `key: value` pairs from the Jekyll config.

    This deliberately handles only the metadata fields validated below. Complex
    nested Jekyll config remains owned by Jekyll and is not parsed here.
    """
    if not path.exists():
        fail(f"required file is missing: {path.relative_to(ROOT)}")
    result: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line or raw_line.startswith((" ", "\t", "#")):
            continue
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value or value in {"|", ">"}:
            continue
        result[key] = strip_quotes(value)
    return result


def parse_front_matter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        fail(f"{path.relative_to(ROOT)} is missing YAML front matter")
    # splitlines() accepts LF and CRLF, which keeps the check portable for
    # contributors editing Markdown on Windows.
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        fail(f"{path.relative_to(ROOT)} has malformed front matter start")
    end = None
    for index, line in enumerate(lines[1:], start=1):
        if line == "---":
            end = index
            break
    if end is None:
        fail(f"{path.relative_to(ROOT)} has no closing front matter delimiter")
    result: dict[str, str] = {}
    for raw_line in lines[1:end]:
        if not raw_line or raw_line.startswith((" ", "\t", "#")):
            continue
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        result[key.strip()] = strip_quotes(value)
    return result


def normalize_path(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    path = value.strip()
    if not path:
        return None
    if path.startswith(("http://", "https://", "mailto:")):
        return None
    if not path.startswith("/"):
        path = "/" + path
    lower = path.lower()
    if lower.endswith((".md", ".html", ".htm", ".pdf", ".txt")):
        return path
    return path if path.endswith("/") else path + "/"


def assert_safe_path(path: str, label: str) -> None:
    if "\\" in path:
        fail(f"{label} contains a backslash: {path}")
    if not path.startswith("/"):
        fail(f"{label} must start with '/': {path}")
    if "//" in path:
        fail(f"{label} contains duplicate slashes: {path}")
    parts = [p for p in path.split("/") if p]
    if any(part in {".", ".."} for part in parts):
        fail(f"{label} contains unsafe path segment: {path}")


def route_for_markdown(path: Path) -> str:
    rel = path.relative_to(DOCS)
    front = parse_front_matter(path)
    permalink = normalize_path(front.get("permalink"))
    if permalink:
        return permalink
    if rel.name == "index.md":
        parent = rel.parent.as_posix()
        return "/" if parent == "." else f"/{parent}/"
    return f"/{rel.with_suffix('').as_posix()}/"


def route_to_markdown_candidates(route: str) -> list[Path]:
    if route == "/":
        return [DOCS / "index.md"]
    rel = route.strip("/")
    candidates = [DOCS / rel / "index.md"]
    if rel:
        candidates.append(DOCS / f"{rel}.md")
    return candidates


def published_routes() -> dict[str, Path]:
    routes: dict[str, Path] = {}
    for path in sorted(DOCS.rglob("*.md")):
        if any(part.startswith("_") for part in path.relative_to(DOCS).parts):
            continue
        route = route_for_markdown(path)
        assert_safe_path(route, f"published route for {path.relative_to(ROOT)}")
        if route in routes:
            fail(
                f"duplicate published route {route}: "
                f"{routes[route].relative_to(ROOT)} and {path.relative_to(ROOT)}"
            )
        routes[route] = path
    return routes


def navigation_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if "path" in value:
                items.append(value)
            for key in ("items", "children"):
                nested = value.get(key)
                if isinstance(nested, list):
                    for child in nested:
                        walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    for section in NAV_SECTIONS:
        section_value = data.get(section)
        if isinstance(section_value, list):
            walk(section_value)
    return items


def check_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        fail(f"{label} mismatch: expected {expected!r}, got {actual!r}")


def check_metadata(book: dict[str, Any], package: dict[str, Any]) -> None:
    for key in ("title", "description", "author", "version", "repository"):
        check_equal(book.get(key), EXPECTED[key], f"book-config.json.{key}")
    check_equal(book.get("homepage"), EXPECTED["homepage"], "book-config.json.homepage")
    check_equal(book.get("license"), EXPECTED["license"], "book-config.json.license")

    check_equal(package.get("name"), "wsl2-linux-essentials-book", "package.json.name")
    for key in ("description", "author", "version"):
        check_equal(package.get(key), EXPECTED[key], f"package.json.{key}")
    check_equal(package.get("license"), EXPECTED["license_npm"], "package.json.license")
    check_equal(package.get("homepage"), EXPECTED["homepage"], "package.json.homepage")
    repo = package.get("repository") or {}
    check_equal(repo.get("type"), "git", "package.json.repository.type")
    check_equal(repo.get("url"), EXPECTED["repository_git"], "package.json.repository.url")
    bugs = package.get("bugs") or {}
    check_equal(bugs.get("url"), EXPECTED["repository"] + "/issues", "package.json.bugs.url")
    scripts = package.get("scripts")
    if not isinstance(scripts, dict):
        fail("package.json.scripts must be an object")
    check_equal(scripts.get("check:security"), "npm audit --omit=optional", "package.json.scripts.check:security")
    test_script = scripts.get("test")
    if not isinstance(test_script, str):
        fail("package.json.scripts.test must be a string")
    for command in ("npm run check:metadata", "npm run check:security"):
        if command not in test_script:
            fail(f"package.json.scripts.test must include {command!r}")
    if not (ROOT / "package-lock.json").is_file():
        fail("package-lock.json is required for reproducible npm ci and security audit")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for command in ("npm ci", "npm test", "npm run check:metadata", "npm run check:security"):
        if command not in readme:
            fail(f"README.md must document {command!r}")

    for config_path in (ROOT / "_config.yml", DOCS / "_config.yml"):
        cfg = read_simple_yaml_scalars(config_path)
        for key in ("title", "description", "author", "version"):
            check_equal(cfg.get(key), EXPECTED[key], f"{config_path.relative_to(ROOT)}.{key}")
        check_equal(cfg.get("baseurl"), EXPECTED["baseurl"], f"{config_path.relative_to(ROOT)}.baseurl")
        check_equal(cfg.get("url"), EXPECTED["url"], f"{config_path.relative_to(ROOT)}.url")
        check_equal(cfg.get("repository"), EXPECTED["repository_full"], f"{config_path.relative_to(ROOT)}.repository")
        check_equal(cfg.get("repository_url"), EXPECTED["repository"], f"{config_path.relative_to(ROOT)}.repository_url")
        check_equal(cfg.get("homepage"), EXPECTED["homepage"], f"{config_path.relative_to(ROOT)}.homepage")
        check_equal(cfg.get("license"), EXPECTED["license"], f"{config_path.relative_to(ROOT)}.license")

    index_fm = parse_front_matter(DOCS / "index.md")
    for key in ("title", "description", "author", "version"):
        check_equal(index_fm.get(key), EXPECTED[key], f"docs/index.md front matter {key}")


def check_structure_and_navigation(book: dict[str, Any], navigation: dict[str, Any]) -> None:
    routes = published_routes()
    nav_items = navigation_items(navigation)
    nav_paths: list[str] = []
    seen_paths: dict[str, str] = {}
    for item in nav_items:
        path = normalize_path(item.get("path"))
        title = item.get("title")
        if not path:
            fail(f"navigation item is missing an internal path: {item!r}")
        assert_safe_path(path, f"navigation path for {title or item!r}")
        if path in seen_paths:
            fail(f"duplicate navigation path {path}: {seen_paths[path]!r} and {title!r}")
        seen_paths[path] = str(title)
        nav_paths.append(path)
        if path not in routes:
            candidates = ", ".join(str(p.relative_to(ROOT)) for p in route_to_markdown_candidates(path))
            fail(f"navigation path {path} has no published Markdown page (checked {candidates})")

    expected_nav = sorted(route for route in routes if route != "/")
    if sorted(nav_paths) != expected_nav:
        missing = sorted(set(expected_nav) - set(nav_paths))
        extra = sorted(set(nav_paths) - set(expected_nav))
        fail(f"navigation/docs route mismatch: missing={missing}, extra={extra}")

    structure = book.get("structure") or {}
    for section in STRUCTURE_SECTIONS:
        config_items = structure.get(section) or []
        nav_section = navigation.get(section) or []
        if len(config_items) != len(nav_section):
            fail(f"book-config.json structure.{section} length does not match navigation.{section}")
        for index, (cfg_item, nav_item) in enumerate(zip(config_items, nav_section), start=1):
            for key in ("title", "path"):
                cfg_value = cfg_item.get(key)
                nav_value = nav_item.get(key)
                if key == "path":
                    cfg_value = normalize_path(cfg_value)
                    nav_value = normalize_path(nav_value)
                if cfg_value != nav_value:
                    fail(
                        f"structure.{section}[{index}].{key} does not match navigation.{section}[{index}].{key}: "
                        f"{cfg_value!r} != {nav_value!r}"
                    )
            if not cfg_item.get("description"):
                fail(f"structure.{section}[{index}] is missing description")

    chapter_paths = [normalize_path(item.get("path")) for item in navigation.get("chapters", [])]
    chapter_titles = [item.get("title") for item in navigation.get("chapters", [])]
    for index, path in enumerate(chapter_paths):
        if not path:
            continue
        key = path.strip("/") + "/"
        nav_state = navigation.get(key) or {}
        if index > 0:
            previous = nav_state.get("previous") or {}
            check_equal(normalize_path(previous.get("path")), chapter_paths[index - 1], f"navigation.{key}.previous.path")
            check_equal(previous.get("title"), chapter_titles[index - 1], f"navigation.{key}.previous.title")
        if index < len(chapter_paths) - 1:
            next_item = nav_state.get("next") or {}
            check_equal(normalize_path(next_item.get("path")), chapter_paths[index + 1], f"navigation.{key}.next.path")
            check_equal(next_item.get("title"), chapter_titles[index + 1], f"navigation.{key}.next.title")


def check_assets() -> None:
    missing = []
    for asset in REQUIRED_ASSETS:
        path = DOCS / asset
        if not path.is_file() or path.stat().st_size <= 0:
            missing.append(asset)
    if missing:
        fail(f"required public assets are missing or empty: {missing}")


def main() -> int:
    book = read_json(ROOT / "book-config.json")
    package = read_json(ROOT / "package.json")
    navigation = read_json(DOCS / "_data" / "navigation.json")

    check_metadata(book, package)
    check_structure_and_navigation(book, navigation)
    check_assets()

    print(
        "OK: metadata, navigation, published routes, and required assets are consistent "
        f"({len(published_routes())} docs pages)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
