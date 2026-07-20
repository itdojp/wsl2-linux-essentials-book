#!/usr/bin/env python3
"""Validate the fixed WordPress download and checksum verification contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "docs/chapter6/index.md"
SNAPSHOT = ROOT / "docs/assets/data/wordpress-release.json"
PACKAGE = ROOT / "package.json"
WORKFLOW = ROOT / ".github/workflows/book-qa.yml"

VERSION = "7.0.2"
LOCALE = "en_US"
CONFIRMED_DATE = "2026-07-21"
CONFIRMED_TIME_ZONE = "Asia/Tokyo"
ARCHIVE_URL = f"https://downloads.wordpress.org/release/wordpress-{VERSION}.tar.gz"
CHECKSUM_URL = (
    "https://api.wordpress.org/core/checksums/1.0/"
    f"?version={VERSION}&locale={LOCALE}"
)
EXPECTED_FILES = 3945


class ContractError(RuntimeError):
    """Raised when the documented supply-chain contract drifts."""


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag in {"script", "style"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            self.parts.append(data)

    def text(self) -> str:
        return " ".join(" ".join(self.parts).split())


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContractError(f"cannot read {path.relative_to(ROOT)}: {exc}") from exc


def read_json(path: Path) -> dict:
    try:
        value = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise ContractError(f"{label}: missing required marker: {needle}")


def forbid(text: str, pattern: str, label: str) -> None:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    if match:
        excerpt = " ".join(match.group(0).split())
        raise ContractError(f"{label}: forbidden pattern found: {excerpt}")


def require_order(text: str, markers: list[str], label: str) -> None:
    positions: list[int] = []
    for marker in markers:
        position = text.find(marker)
        if position < 0:
            raise ContractError(f"{label}: missing order marker: {marker}")
        positions.append(position)
    if positions != sorted(positions):
        raise ContractError(f"{label}: unsafe order for markers: {' -> '.join(markers)}")


def validate_snapshot(snapshot: dict) -> None:
    expected = {
        "schemaVersion": 1,
        "confirmedDate": CONFIRMED_DATE,
        "confirmedTimeZone": CONFIRMED_TIME_ZONE,
    }
    for key, value in expected.items():
        if snapshot.get(key) != value:
            raise ContractError(f"snapshot {key} must be {value!r}")

    wordpress = snapshot.get("wordpress")
    if not isinstance(wordpress, dict):
        raise ContractError("snapshot wordpress must be an object")
    expected_wordpress = {
        "version": VERSION,
        "checksumLocale": LOCALE,
        "archiveUrl": ARCHIVE_URL,
        "checksumApiUrl": CHECKSUM_URL,
        "checksumAlgorithm": "md5",
        "expectedCoreFiles": EXPECTED_FILES,
    }
    for key, value in expected_wordpress.items():
        if wordpress.get(key) != value:
            raise ContractError(f"snapshot wordpress.{key} must be {value!r}")

    requirements = snapshot.get("requirements")
    if requirements != {
        "versionApiMinimum": {"php": "7.4", "mysql": "5.5.5"},
        "wordpressOrgRecommended": {
            "php": "8.3",
            "mysql": "8.0",
            "mariadb": "10.11",
            "https": True,
        },
    }:
        raise ContractError("snapshot requirements drifted")

    maintenance = snapshot.get("maintenance")
    if not isinstance(maintenance, dict):
        raise ContractError("snapshot maintenance must be an object")
    validation = maintenance.get("requiredValidation")
    if validation != [
        "archive-download-over-verified-tls",
        "official-core-checksums-positive-case",
        "modified-core-file-negative-case",
        "missing-or-unexpected-core-file-negative-case",
        "php-and-database-requirements-review",
    ]:
        raise ContractError("snapshot maintenance.requiredValidation drifted")


def validate_chapter(chapter: str) -> None:
    label = "docs/chapter6/index.md"
    required = [
        f"WordPress coreは`{VERSION}`",
        f"checksum localeは`{LOCALE}`",
        f"WP_VERSION='{VERSION}'",
        f"WP_LOCALE='{LOCALE}'",
        "WP_DOWNLOAD_URL=\"https://downloads.wordpress.org/release/${WP_ARCHIVE}\"",
        "WP_CHECKSUM_URL=\"https://api.wordpress.org/core/checksums/1.0/?version=${WP_VERSION}&locale=${WP_LOCALE}\"",
        "set -euo pipefail",
        "trap cleanup_wordpress_download EXIT",
        "trap 'exit 130' INT",
        "trap 'exit 143' TERM",
        "sudo apt install -y php",
        "php-zip curl jq",
        "--proto '=https' --tlsv1.2",
        "from pathlib import PurePosixPath",
        "or \"..\" in path.parts",
        "or path.parts[0] != \"wordpress\"",
        "or any(ord(character) < 32 or ord(character) == 127",
        "unsafe_type = not (member.isdir() or member.isfile())",
        "jq -e '.checksums | (type == \"object\" and length > 0)'",
        "if ! diff --unified=0 checksum-files.txt archive-files.txt; then",
        "if ! md5sum --check --strict --quiet wordpress-core.md5; then",
        "web rootへ配置しません",
        "if sudo test -e /var/www/html/wordpress; then",
        "sudo cp --archive wordpress /var/www/html/wordpress",
        "PHP 8.3以上",
        "MySQL 8.0以上またはMariaDB 10.11以上",
        "WordPress Version Check API",
        "WordPress Core Checksums API",
        "WP-CLI: `wp core verify-checksums`",
        f"**{CONFIRMED_DATE} JST確認**",
        "assets/data/wordpress-release.json",
    ]
    for marker in required:
        require(chapter, marker, label)

    forbid(chapter, r"latest\.tar\.gz", label)
    forbid(chapter, r"wordpress\.org/latest", label)
    forbid(
        chapter,
        r"^[ \t]*(?:sudo[ \t]+)?(?:curl|wget)\b[^\n]*(?:[ \t]-k(?:[ \t]|$)|--insecure)",
        label,
    )
    forbid(
        chapter,
        r"^[ \t]*(?:sudo[ \t]+)?wp[ \t]+core[ \t]+verify-checksums[^\n]*--insecure",
        label,
    )
    forbid(chapter, r"^[ \t]*(?:-k|--insecure)(?:[ \t\\]|$)", label)
    forbid(chapter, r"sudo\s+cp[^\n]+wordpress[^\n]+/var/www/html/(?!wordpress)", label)

    require_order(
        chapter,
        [
            "--output \"$WP_ARCHIVE\" \"$WP_DOWNLOAD_URL\"",
            "--output core-checksums.json \"$WP_CHECKSUM_URL\"",
            "if ! diff --unified=0 checksum-files.txt archive-files.txt; then",
            "if ! md5sum --check --strict --quiet wordpress-core.md5; then",
            "if sudo test -e /var/www/html/wordpress; then",
            "sudo cp --archive wordpress /var/www/html/wordpress",
        ],
        label,
    )

    # The extraction guard must fail before tar extraction.
    require_order(
        chapter,
        [
            "python3 - \"$WP_ARCHIVE\" <<'PY'",
            "or \"..\" in path.parts",
            "unsafe_type = not (member.isdir() or member.isfile())",
            "tar --extract --gzip --file \"$WP_ARCHIVE\"",
        ],
        label,
    )


def validate_wiring(package: dict, workflow: str) -> None:
    scripts = package.get("scripts")
    if not isinstance(scripts, dict):
        raise ContractError("package.json scripts must be an object")
    command = scripts.get("check:wordpress-supply-chain")
    expected = (
        "python3 scripts/check_wordpress_supply_chain_contract.py --self-test && "
        "python3 scripts/check_wordpress_supply_chain_contract.py"
    )
    if command != expected:
        raise ContractError("package check:wordpress-supply-chain command drifted")
    test = scripts.get("test", "")
    if "npm run check:wordpress-supply-chain" not in test:
        raise ContractError("package test does not run WordPress supply-chain check")

    for marker in [
        "WordPress supply-chain contract (source + self-test)",
        "python3 scripts/check_wordpress_supply_chain_contract.py --self-test",
        "WordPress supply-chain contract (built site)",
        "python3 scripts/check_wordpress_supply_chain_contract.py --built-site _site",
    ]:
        require(workflow, marker, ".github/workflows/book-qa.yml")


def verify_fixture(root: Path, checksums: dict[str, str]) -> subprocess.CompletedProcess[str]:
    expected_names = sorted(checksums)
    actual_names = sorted(
        str(path.relative_to(root / "wordpress"))
        for path in (root / "wordpress").rglob("*")
        if path.is_file()
    )
    if actual_names != expected_names:
        return subprocess.CompletedProcess(
            args=["file-set-check"],
            returncode=1,
            stdout=(
                f"file set differs: expected={expected_names!r}, actual={actual_names!r}"
            ),
        )
    manifest = root / "wordpress-core.md5"
    lines = [f"{digest}  wordpress/{name}" for name, digest in checksums.items()]
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return subprocess.run(
        ["md5sum", "--check", "--strict", "--quiet", manifest.name],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def md5(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    digest.update(path.read_bytes())
    return digest.hexdigest()


def run_self_test() -> None:
    negative_cases = 0
    scratch_root = ROOT / ".codex-local/tmp"
    scratch_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="wordpress-contract-", dir=scratch_root) as raw:
        root = Path(raw)
        core = root / "wordpress/wp-includes"
        core.mkdir(parents=True)
        version_file = core / "version.php"
        load_file = core / "load.php"
        version_file.write_text("<?php $wp_version = '7.0.2';\n", encoding="utf-8")
        load_file.write_text("<?php // fixture\n", encoding="utf-8")
        checksums = {
            "wp-includes/version.php": md5(version_file),
            "wp-includes/load.php": md5(load_file),
        }

        result = verify_fixture(root, checksums)
        if result.returncode != 0:
            raise ContractError(f"self-test positive fixture failed: {result.stdout}")

        version_file.write_text("<?php $wp_version = 'tampered';\n", encoding="utf-8")
        result = verify_fixture(root, checksums)
        if result.returncode == 0:
            raise ContractError("self-test did not reject a modified core file")
        negative_cases += 1
        version_file.write_text("<?php $wp_version = '7.0.2';\n", encoding="utf-8")

        load_file.unlink()
        result = verify_fixture(root, checksums)
        if result.returncode == 0:
            raise ContractError("self-test did not reject a missing core file")
        negative_cases += 1

        load_file.write_text("<?php // fixture\n", encoding="utf-8")
        extra_file = core / "unexpected.php"
        extra_file.write_text("<?php // unexpected\n", encoding="utf-8")
        result = verify_fixture(root, checksums)
        if result.returncode == 0:
            raise ContractError("self-test did not reject an unexpected core file")
        negative_cases += 1

    try:
        scratch_root.rmdir()
        scratch_root.parent.rmdir()
    except OSError:
        # Preserve a pre-existing non-empty local agent directory.
        pass

    chapter = read_text(CHAPTER)
    snapshot = read_json(SNAPSHOT)
    mutations = [
        (chapter.replace("wordpress-${WP_VERSION}.tar.gz", "latest.tar.gz", 1), snapshot),
        (chapter.replace("--proto '=https' --tlsv1.2", "--insecure", 1), snapshot),
        (chapter.replace("WP_VERSION='7.0.2'", "WP_VERSION='7.0.1'", 1), snapshot),
    ]
    for mutated_chapter, mutated_snapshot in mutations:
        try:
            validate_snapshot(mutated_snapshot)
            validate_chapter(mutated_chapter)
        except ContractError:
            negative_cases += 1
        else:
            raise ContractError("self-test accepted a source contract mutation")

    mutated_snapshot = json.loads(json.dumps(snapshot))
    mutated_snapshot["wordpress"]["checksumLocale"] = "ja"
    try:
        validate_snapshot(mutated_snapshot)
    except ContractError:
        negative_cases += 1
    else:
        raise ContractError("self-test accepted a snapshot locale mismatch")

    mutated_snapshot = json.loads(json.dumps(snapshot))
    mutated_snapshot["maintenance"] = []
    try:
        validate_snapshot(mutated_snapshot)
    except ContractError:
        negative_cases += 1
    else:
        raise ContractError("self-test accepted a non-object maintenance contract")

    if negative_cases != 8:
        raise ContractError(f"self-test expected 8 negative cases, got {negative_cases}")
    print("WordPress supply-chain self-test: PASS (1 positive, 8 negative cases)")


def validate_source() -> None:
    snapshot = read_json(SNAPSHOT)
    validate_snapshot(snapshot)
    validate_chapter(read_text(CHAPTER))
    validate_wiring(read_json(PACKAGE), read_text(WORKFLOW))
    print(
        "WordPress supply-chain source contract: PASS "
        f"(WordPress {VERSION}, locale {LOCALE}, {EXPECTED_FILES} expected files)"
    )


def validate_built_site(site: Path) -> None:
    chapter_path = site / "chapter6/index.html"
    snapshot_path = site / "assets/data/wordpress-release.json"
    html = read_text(chapter_path)
    parser = VisibleTextParser()
    parser.feed(html)
    visible = parser.text()
    for marker in [
        f"WordPress coreは {VERSION}",
        f"checksum localeは {LOCALE}",
        "checksum成功後にだけドキュメントルートへ配置",
        "Source Notes（2026-07-21 JST確認）",
        "PHP 8.3以上",
        "MySQL 8.0以上またはMariaDB 10.11以上",
    ]:
        require(visible, marker, str(chapter_path))
    forbid(visible, r"latest\.tar\.gz", str(chapter_path))
    forbid(visible, r"wordpress\.org/latest", str(chapter_path))
    validate_snapshot(read_json(snapshot_path))
    if read_json(snapshot_path) != read_json(SNAPSHOT):
        raise ContractError("built WordPress release snapshot differs from source")
    print(
        "WordPress supply-chain built contract: PASS "
        f"({chapter_path.relative_to(site)}, public snapshot present)"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--built-site", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.self_test:
            run_self_test()
        elif args.built_site:
            validate_built_site(args.built_site.resolve())
        else:
            validate_source()
    except ContractError as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
