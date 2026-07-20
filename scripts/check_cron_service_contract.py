#!/usr/bin/env python3
"""Validate the WSL cron service-management contract (Issue #135)."""

from __future__ import annotations

import argparse
import html
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "chapter3": Path("docs/chapter3/index.md"),
    "chapter5": Path("docs/chapter5/index.md"),
}


class ContractError(RuntimeError):
    """Raised when required guidance is absent or unsafe guidance returns."""


@dataclass(frozen=True)
class Snapshot:
    files: Dict[str, str]


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        raise ContractError(f"{label}: missing {token!r}")


def reject(text: str, pattern: str, label: str) -> None:
    if re.search(pattern, text, flags=re.IGNORECASE):
        raise ContractError(f"{label}: forbidden pattern {pattern!r}")


def read_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContractError(f"{label} unreadable: {path}: {exc}") from exc


def load_source(root: Path = ROOT) -> Snapshot:
    return Snapshot({name: read_text(root / path, name) for name, path in TARGETS.items()})


def check_order(text: str, tokens: list[str], label: str) -> None:
    positions = []
    for token in tokens:
        require(text, token, label)
        positions.append(text.index(token))
    if positions != sorted(positions) or len(set(positions)) != len(positions):
        raise ContractError(f"{label}: expected order is broken")


def check_source(snapshot: Snapshot, root: Path = ROOT, check_workflow: bool = True) -> None:
    chapter3 = snapshot.files["chapter3"]
    chapter5 = snapshot.files["chapter5"]
    combined = "\n".join(snapshot.files.values())

    for token in [
        "### 有効化手順\n{: #wsl-systemd-service-management}",
        "`.bashrc` に `sudo service ... start` を追加すると",
        "systemd service だけを起動しても、WSL instance は常時稼働になりません",
        "../chapter5/#wsl-cron-service-management",
    ]:
        require(chapter3, token, "chapter 3 service boundary")

    check_order(
        chapter5,
        [
            "### WSL2 でのcron設定\n{: #wsl-cron-service-management}",
            "ps -p 1 -o comm=",
            "#### systemd有効時",
            "sudo systemctl enable --now cron",
            "systemctl is-enabled cron",
            "systemctl is-active cron",
            "systemctl status cron --no-pager",
            "journalctl -u cron -b -n 50 --no-pager",
            "#### systemd無効時",
            "sudo service cron start",
            "service cron status",
            "#### WSL instanceのライフサイクル",
            "#### Cron / WSL Source Notes（確認日: 2026-07-20）",
        ],
        "chapter 5 cron decision flow",
    )
    for token in [
        "`is-enabled` の期待値は `enabled`、`is-active` の期待値は `active`",
        "現在の WSL instance に対する明示的な手動起動",
        "このコマンドを `.bashrc`、`.profile` などの対話shell初期化ファイルへ追加してはいけません",
        "エラー出力も破棄しません",
        "systemd service だけを起動しても、WSL instance は常時稼働になりません",
        "systemd serviceはWSL instanceを存続させず",
        "../chapter3/#wsl-systemd-service-management",
        "https://learn.microsoft.com/en-us/windows/wsl/systemd",
        "https://www.freedesktop.org/software/systemd/man/latest/systemctl.html",
        "https://www.freedesktop.org/software/systemd/man/latest/journalctl.html",
    ]:
        require(chapter5, token, "chapter 5 cron boundary")

    for pattern in [
        r"echo\s+['\"]sudo\s+service\s+cron\s+start.*(?:\.bashrc|\.profile)",
        r"sudo\s+service\s+cron\s+start\s+2>/dev/null",
    ]:
        reject(combined, pattern, "interactive-shell privileged startup")

    if check_workflow:
        workflow = read_text(root / ".github/workflows/book-qa.yml", "Book QA workflow")
        package = read_text(root / "package.json", "package.json")
        for token in [
            "python3 scripts/check_cron_service_contract.py --self-test",
            "python3 scripts/check_cron_service_contract.py",
            "python3 scripts/check_cron_service_contract.py --built-site _site",
        ]:
            require(workflow, token, "Book QA workflow")
        require(package, '"check:cron-service"', "npm test contract")
        require(package, "npm run check:cron-service", "npm test contract")


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def visible_text(document: str) -> str:
    parser = TextExtractor()
    parser.feed(document)
    text = html.unescape("".join(parser.parts))
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def load_built(site: Path) -> Snapshot:
    paths = {
        "chapter3": site / "chapter3/index.html",
        "chapter5": site / "chapter5/index.html",
    }
    return Snapshot({name: read_text(path, f"built {name}") for name, path in paths.items()})


def check_built(snapshot: Snapshot) -> None:
    chapter3_html = snapshot.files["chapter3"]
    chapter5_html = snapshot.files["chapter5"]
    chapter3 = visible_text(chapter3_html)
    chapter5 = visible_text(chapter5_html)

    for token in [
        'id="wsl-systemd-service-management"',
        'href="../chapter5/#wsl-cron-service-management"',
    ]:
        require(chapter3_html, token, "built chapter 3 navigation")
    for token in [
        'id="wsl-cron-service-management"',
        'href="../chapter3/#wsl-systemd-service-management"',
    ]:
        require(chapter5_html, token, "built chapter 5 navigation")
    for token in [
        "systemd service だけを起動しても、WSL instance は常時稼働になりません",
        ".bashrc に sudo service ... start を追加すると",
    ]:
        require(chapter3, token, "built chapter 3 service boundary")
    for token in [
        "ps -p 1 -o comm=",
        "sudo systemctl enable --now cron",
        "systemctl is-enabled cron",
        "systemctl is-active cron",
        "systemctl status cron --no-pager",
        "journalctl -u cron -b -n 50 --no-pager",
        "sudo service cron start",
        "service cron status",
        "対話shell初期化ファイルへ追加してはいけません",
        "systemd service だけを起動しても、WSL instance は常時稼働になりません",
        "Cron / WSL Source Notes（確認日: 2026-07-20）",
    ]:
        require(chapter5, token, "built chapter 5 cron boundary")
    combined = chapter3 + "\n" + chapter5
    for pattern in [
        r"echo\s+['\"]sudo\s+service\s+cron\s+start.*(?:\.bashrc|\.profile)",
        r"sudo\s+service\s+cron\s+start\s+2>/dev/null",
    ]:
        reject(combined, pattern, "built interactive-shell privileged startup")
    print("Built WSL cron service contract passed (2 pages).")


def expect_failure(label: str, action, expected: str) -> None:
    try:
        action()
    except ContractError as exc:
        if expected in str(exc):
            return
        raise ContractError(f"self-test {label}: wrong error: {exc}") from exc
    raise ContractError(f"self-test {label}: mutation was accepted")


def self_test() -> None:
    baseline = load_source()
    check_source(baseline)

    def replaced(name: str, old: str, new: str) -> Snapshot:
        files = dict(baseline.files)
        if old not in files[name]:
            raise ContractError(f"self-test fixture missing: {name}: {old!r}")
        files[name] = files[name].replace(old, new, 1)
        return Snapshot(files)

    def appended(name: str, content: str) -> Snapshot:
        files = dict(baseline.files)
        files[name] += content
        return Snapshot(files)

    expect_failure(
        "bashrc privileged startup",
        lambda: check_source(
            appended("chapter5", "\necho 'sudo service cron start' >> ~/.bashrc\n"),
            check_workflow=False,
        ),
        "forbidden pattern",
    )
    for label, name, old, new, expected in [
        ("missing PID 1 branch", "chapter5", "ps -p 1 -o comm=", "ps aux", "comm="),
        ("missing active state", "chapter5", "systemctl is-active cron", "systemctl show cron", "is-active"),
        ("missing manual status", "chapter5", "service cron status", "pgrep cron", "service cron status"),
        (
            "missing lifecycle boundary",
            "chapter5",
            "systemd serviceはWSL instanceを存続させず",
            "systemd serviceなら常時稼働します",
            "存続させず",
        ),
        (
            "stale source note",
            "chapter5",
            "Cron / WSL Source Notes（確認日: 2026-07-20）",
            "Cron / WSL Source Notes（確認日なし）",
            "確認日",
        ),
        (
            "missing chapter alignment",
            "chapter3",
            "../chapter5/#wsl-cron-service-management",
            "../chapter5/",
            "wsl-cron-service-management",
        ),
    ]:
        expect_failure(
            label,
            lambda n=name, o=old, v=new: check_source(replaced(n, o, v), check_workflow=False),
            expected,
        )
    print("WSL cron service contract self-test passed (7 negative mutations).")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--built-site", type=Path)
    args = parser.parse_args()
    if args.self_test and args.built_site is not None:
        raise ContractError("choose either --self-test or --built-site")
    if args.self_test:
        self_test()
    elif args.built_site is not None:
        check_built(load_built(args.built_site.resolve()))
    else:
        check_source(load_source())
        print("WSL cron service source contract passed (2 pages).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(f"WSL cron service contract failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
