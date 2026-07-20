#!/usr/bin/env python3
"""Validate learning paths, time estimates, and the Chapter 5 split (Issue #137)."""

from __future__ import annotations

import argparse
import copy
import html
import json
import math
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOP = Path("docs/index.md")
CHAPTER5 = Path("docs/chapter5/index.md")
DATA = Path("docs/assets/data/learning-time.json")


class ContractError(RuntimeError):
    """Raised when the documented learning contract has drifted."""


@dataclass(frozen=True)
class Snapshot:
    top: str
    chapter5: str
    data: dict[str, Any]


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        raise ContractError(f"{label}: missing {token!r}")


def reject(text: str, pattern: str, label: str) -> None:
    if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
        raise ContractError(f"{label}: forbidden pattern {pattern!r}")


def check_order(text: str, tokens: list[str], label: str) -> None:
    positions: list[int] = []
    for token in tokens:
        require(text, token, label)
        positions.append(text.index(token))
    if positions != sorted(positions) or len(set(positions)) != len(positions):
        raise ContractError(f"{label}: expected order is broken")


def read_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContractError(f"{label} unreadable: {path}: {exc}") from exc


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(read_text(path, label))
    except json.JSONDecodeError as exc:
        raise ContractError(f"{label} invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{label}: root must be an object")
    return value


def load_source(root: Path = ROOT) -> Snapshot:
    return Snapshot(
        top=read_text(root / TOP, "book top"),
        chapter5=read_text(root / CHAPTER5, "chapter 5"),
        data=load_json(root / DATA, "learning-time snapshot"),
    )


def integer(mapping: dict[str, Any], key: str, label: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ContractError(f"{label}.{key} must be a non-negative integer")
    return value


def reading_range(characters: int, fast: int, slow: int) -> dict[str, int]:
    return {"min": math.ceil(characters / fast), "max": math.ceil(characters / slow)}


def validate_data(data: dict[str, Any], root: Path = ROOT, check_sources: bool = True) -> None:
    if data.get("schemaVersion") != 1:
        raise ContractError("learning-time snapshot: schemaVersion must be 1")
    if data.get("confirmedDate") != "2026-07-21":
        raise ContractError("learning-time snapshot: confirmedDate must be 2026-07-21")

    measurement = data.get("measurement")
    if not isinstance(measurement, dict):
        raise ContractError("learning-time snapshot: measurement must be an object")
    if measurement.get("selector") != "article.page-content":
        raise ContractError("learning-time snapshot: selector must be article.page-content")
    if measurement.get("whitespaceExcluded") is not True or measurement.get("codeTextIncluded") is not True:
        raise ContractError("learning-time snapshot: text scope must exclude whitespace and include code")
    rates = measurement.get("readingCharactersPerMinute")
    if not isinstance(rates, dict) or rates.get("slow") != 400 or rates.get("fast") != 600:
        raise ContractError("learning-time snapshot: reading rates must be slow=400 and fast=600")
    if "planning range, not a measured guarantee" not in str(measurement.get("handsOnBasis", "")):
        raise ContractError("learning-time snapshot: hands-on limitation is missing")
    slow, fast = 400, 600

    pages = data.get("pages")
    if not isinstance(pages, list) or len(pages) != 9:
        raise ContractError("learning-time snapshot: exactly 9 public pages are required")
    expected_ids = ["top", *[f"chapter{i}" for i in range(7)], "glossary"]
    if [page.get("id") for page in pages if isinstance(page, dict)] != expected_ids:
        raise ContractError("learning-time snapshot: page order or IDs drifted")

    total_characters = 0
    total_blocks = 0
    for page in pages:
        if not isinstance(page, dict):
            raise ContractError("learning-time snapshot: every page must be an object")
        label = f"learning-time page {page.get('id', '?')}"
        characters = integer(page, "visibleCharacters", label)
        blocks = integer(page, "codeBlocks", label)
        expected_range = reading_range(characters, fast, slow)
        if page.get("readingMinutes") != expected_range:
            raise ContractError(f"{label}: readingMinutes must be {expected_range}")
        source_path = page.get("sourcePath")
        built_path = page.get("builtPath")
        if not isinstance(source_path, str) or not isinstance(built_path, str):
            raise ContractError(f"{label}: sourcePath and builtPath are required")
        if check_sources:
            source = read_text(root / source_path, label)
            source_blocks = len(re.findall(r"^```", source, flags=re.MULTILINE)) // 2
            if source_blocks != blocks:
                raise ContractError(f"{label}: codeBlocks snapshot={blocks}, source={source_blocks}")
        total_characters += characters
        total_blocks += blocks

    totals = data.get("totals")
    if not isinstance(totals, dict):
        raise ContractError("learning-time snapshot: totals must be an object")
    if integer(totals, "visibleCharacters", "learning-time totals") != total_characters:
        raise ContractError("learning-time snapshot: visibleCharacters total mismatch")
    if integer(totals, "codeBlocks", "learning-time totals") != total_blocks:
        raise ContractError("learning-time snapshot: codeBlocks total mismatch")
    expected_total_range = reading_range(total_characters, fast, slow)
    if totals.get("readingMinutes") != expected_total_range:
        raise ContractError(f"learning-time snapshot: total readingMinutes must be {expected_total_range}")

    sections = data.get("chapter5Sections")
    if not isinstance(sections, list) or [s.get("id") for s in sections if isinstance(s, dict)] != ["foundation", "advanced"]:
        raise ContractError("learning-time snapshot: Chapter 5 foundation/advanced sections are required")
    for section in sections:
        label = f"learning-time Chapter 5 {section.get('id', '?')}"
        characters = integer(section, "visibleCharacters", label)
        if section.get("readingMinutes") != reading_range(characters, fast, slow):
            raise ContractError(f"{label}: readingMinutes does not match the formula")
        hands_on = section.get("handsOnMinutes")
        if not isinstance(hands_on, dict) or integer(hands_on, "min", label) >= integer(hands_on, "max", label):
            raise ContractError(f"{label}: handsOnMinutes must be an increasing range")
    if sections[0].get("required") is not True or sections[1].get("required") is not False:
        raise ContractError("learning-time snapshot: Chapter 5 required/optional boundary drifted")

    chapter_hands_on = data.get("chapterHandsOnMinutes")
    expected_hands_on_ids = [
        "chapter0",
        "chapter1",
        "chapter2",
        "chapter3",
        "chapter4",
        "chapter5-foundation",
        "chapter5-advanced",
        "chapter6",
    ]
    if not isinstance(chapter_hands_on, list) or [
        item.get("id") for item in chapter_hands_on if isinstance(item, dict)
    ] != expected_hands_on_ids:
        raise ContractError("learning-time snapshot: ordered Chapter 0-6 hands-on inventory is required")
    hands_on_by_id: dict[str, dict[str, Any]] = {}
    for item in chapter_hands_on:
        label = f"hands-on inventory {item.get('id', '?')}"
        if integer(item, "min", label) >= integer(item, "max", label):
            raise ContractError(f"{label}: min/max must be an increasing range")
        hands_on_by_id[str(item["id"])] = item
    for section in sections:
        inventory = hands_on_by_id[f"chapter5-{section['id']}"]
        if section["handsOnMinutes"] != {"min": inventory["min"], "max": inventory["max"]}:
            raise ContractError(f"Chapter 5 {section['id']}: hands-on inventory mismatch")

    paths = data.get("learningPaths")
    if not isinstance(paths, list) or [p.get("id") for p in paths if isinstance(p, dict)] != [
        "core-with-review",
        "core-with-skip",
        "full",
    ]:
        raise ContractError("learning-time snapshot: three ordered learning paths are required")
    for path in paths:
        hours = path.get("handsOnHours")
        if not isinstance(hours, dict) or integer(hours, "min", f"path {path.get('id')}") >= integer(
            hours, "max", f"path {path.get('id')}"
        ):
            raise ContractError(f"path {path.get('id')}: handsOnHours must be an increasing range")
        required = path.get("required")
        if not isinstance(required, list) or any(item not in hands_on_by_id for item in required):
            raise ContractError(f"path {path.get('id')}: required items must reference the hands-on inventory")
        calculated = {
            "min": math.ceil(sum(hands_on_by_id[item]["min"] for item in required) / 60),
            "max": math.ceil(sum(hands_on_by_id[item]["max"] for item in required) / 60),
        }
        if hours != calculated:
            raise ContractError(f"path {path.get('id')}: handsOnHours must be {calculated}")


def check_source(snapshot: Snapshot, root: Path = ROOT, check_workflow: bool = True) -> None:
    top = snapshot.top
    chapter5 = snapshot.chapter5
    validate_data(snapshot.data, root=root)

    check_order(
        top,
        [
            "## 読み方ガイドと学習経路",
            "| 復習込みの必須経路 |",
            "| 基礎既習者の必須経路 |",
            "| 全演習経路 |",
            "### 第1〜2章のskip判定",
            "### 章別の計画値",
            "| 第0章 |",
            "| 第5章 基礎編（5.1〜5.7） |",
            "| 第5章 発展編（5.8〜5.10） |",
            "| 第6章 |",
            "## 所要時間の定義と算定方法",
            "算定snapshotと章別task inventoryの確認日: **2026-07-21**",
            "## 目次",
        ],
        "book top learning path",
    )
    for token in [
        "hands-on 7〜11時間",
        "hands-on 5〜8時間",
        "hands-on 10〜17時間",
        "資料なしで安全に実施・説明できる場合",
        "1項目でも不確かな場合",
        "読むだけ",
        "実測保証値ではありません",
        "article.page-content",
        "75,219文字・170 code blocks",
        "126〜189分（約2〜3時間）",
        "LAN公開runbookは別clientが必要なため任意",
        "download速度、machine性能、既存環境、入力速度、troubleshooting",
        "assets/data/learning-time.json",
        "**必須経路**を終えると",
        "**発展経路**まで終えると",
        "**WordPress経路**まで終えると",
        "**選択式プロジェクト**",
    ]:
        require(top, token, "book top learning contract")
    reject(top, r"0\.5\s*[〜~-]\s*1\s*時間", "stale book time")
    reject(top, r"すべてのコマンドが実行可能", "overbroad learning outcome")

    check_order(
        chapter5,
        [
            "## 第5章の学習契約",
            "| 基礎編 | 5.1〜5.7 | 必須 |",
            "| 発展編 | 5.8〜5.10 | 任意 |",
            "## 基礎編（必須: 5.1〜5.7）",
            "{: #chapter5-foundation }",
            "### 5.1 シェルスクリプトとは",
            "### 5.7 エラーハンドリング",
            "## 発展編（任意: 5.8〜5.10）",
            "{: #chapter5-advanced }",
            "### 5.8 実践スクリプト例",
            "### 5.9 cron による定期実行",
            "### 5.10 演習問題",
            "#### 演習2: ユーザー管理スクリプト",
            "#### 演習3: デプロイスクリプト",
            "## まとめ",
        ],
        "Chapter 5 foundation/advanced structure",
    )
    for token in [
        "基礎編の到達条件を満たせば必須経路は完了",
        "発展編のscriptは教育用の構造例",
        "固定password、user作成、service停止、repositoryの強制同期",
        "値と対象を置換し、差分・権限・rollbackをreviewできない段階では実行しません",
        "必須経路の修了条件には含めません",
    ]:
        require(chapter5, token, "Chapter 5 learning boundary")
    for number in range(1, 8):
        require(chapter5, f"### 5.{number}", "Chapter 5 foundation heading level")
    for number in range(8, 11):
        require(chapter5, f"### 5.{number}", "Chapter 5 advanced heading level")
    reject(chapter5, r"^## 5\.(?:[1-9]|10)\b", "flat Chapter 5 structure")

    if check_workflow:
        package = load_json(root / "package.json", "package.json")
        scripts = package.get("scripts")
        if not isinstance(scripts, dict):
            raise ContractError("package.json: scripts must be an object")
        require(str(scripts.get("check:learning-path", "")), "check_learning_path_contract.py", "npm learning path script")
        require(str(scripts.get("test", "")), "npm run check:learning-path", "npm test learning path gate")
        workflow = read_text(root / ".github/workflows/book-qa.yml", "Book QA workflow")
        for token in [
            "python3 scripts/check_learning_path_contract.py --self-test",
            "python3 scripts/check_learning_path_contract.py",
            "python3 scripts/check_learning_path_contract.py --built-site _site",
        ]:
            require(workflow, token, "Book QA learning path gate")


class ArticleExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.article_depth = 0
        self.ignored_depth = 0
        self.parts: list[str] = []
        self.code_blocks = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag.lower() == "article" and "page-content" in (attributes.get("class") or "").split():
            self.article_depth += 1
        elif self.article_depth and tag.lower() in {"script", "style"}:
            self.ignored_depth += 1
        if self.article_depth and not self.ignored_depth and tag.lower() == "pre":
            self.code_blocks += 1

    def handle_endtag(self, tag: str) -> None:
        if self.article_depth and tag.lower() in {"script", "style"} and self.ignored_depth:
            self.ignored_depth -= 1
        elif tag.lower() == "article" and self.article_depth:
            self.article_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.article_depth and not self.ignored_depth:
            self.parts.append(data)

    def text(self) -> str:
        return html.unescape("".join(self.parts))


def extract_article(path: Path, label: str) -> ArticleExtractor:
    parser = ArticleExtractor()
    parser.feed(read_text(path, label))
    parser.close()
    if not parser.parts:
        raise ContractError(f"{label}: article.page-content was not found")
    return parser


def character_count(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def check_built(site: Path, data: dict[str, Any]) -> None:
    validate_data(data, check_sources=False)
    rates = data["measurement"]["readingCharactersPerMinute"]
    slow, fast = rates["slow"], rates["fast"]
    extracted: dict[str, ArticleExtractor] = {}
    for page in data["pages"]:
        parser = extract_article(site / page["builtPath"], f"built {page['id']}")
        extracted[page["id"]] = parser
        characters = character_count(parser.text())
        if characters != page["visibleCharacters"]:
            raise ContractError(
                f"built {page['id']}: visibleCharacters snapshot={page['visibleCharacters']}, actual={characters}"
            )
        if parser.code_blocks != page["codeBlocks"]:
            raise ContractError(f"built {page['id']}: codeBlocks snapshot={page['codeBlocks']}, actual={parser.code_blocks}")
        if page["readingMinutes"] != reading_range(characters, fast, slow):
            raise ContractError(f"built {page['id']}: reading range drifted")

    chapter5_text = extracted["chapter5"].text()
    for section in data["chapter5Sections"]:
        start = str(section["startMarker"])
        end = str(section["endMarker"])
        require(chapter5_text, start, f"built Chapter 5 {section['id']}")
        require(chapter5_text, end, f"built Chapter 5 {section['id']}")
        segment = chapter5_text[chapter5_text.index(start) : chapter5_text.index(end, chapter5_text.index(start) + len(start))]
        characters = character_count(segment)
        if characters != section["visibleCharacters"]:
            raise ContractError(
                f"built Chapter 5 {section['id']}: visibleCharacters snapshot={section['visibleCharacters']}, actual={characters}"
            )

    top_text = extracted["top"].text()
    for token in [
        "復習込みの必須経路",
        "基礎既習者の必須経路",
        "第1〜2章のskip判定",
        "126〜189分（約2〜3時間）",
        "2026-07-21",
    ]:
        require(top_text, token, "built top learning contract")
    for token in ["基礎編（必須: 5.1〜5.7）", "発展編（任意: 5.8〜5.10）", "必須経路の修了条件には含めません"]:
        require(chapter5_text, token, "built Chapter 5 learning contract")
    reject(top_text, r"0\.5\s*[〜~-]\s*1\s*時間", "built stale book time")

    built_data = load_json(site / "assets/data/learning-time.json", "built learning-time snapshot")
    if built_data != data:
        raise ContractError("built learning-time snapshot differs from source")
    print(
        "Built learning path contract passed "
        f"({len(data['pages'])} pages, {data['totals']['visibleCharacters']} characters, "
        f"{data['totals']['codeBlocks']} code blocks)."
    )


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

    def replace_text(field: str, old: str, new: str) -> Snapshot:
        value = getattr(baseline, field)
        if old not in value:
            raise ContractError(f"self-test fixture missing: {field}: {old!r}")
        return Snapshot(
            top=value.replace(old, new, 1) if field == "top" else baseline.top,
            chapter5=value.replace(old, new, 1) if field == "chapter5" else baseline.chapter5,
            data=copy.deepcopy(baseline.data),
        )

    cases = [
        (
            "stale top time",
            lambda: check_source(
                replace_text("top", "126〜189分（約2〜3時間）", "0.5〜1時間"), check_workflow=False
            ),
            "learning contract",
        ),
        (
            "missing skip gate",
            lambda: check_source(
                replace_text("top", "1項目でも不確かな場合", "判定にかかわらずskip"), check_workflow=False
            ),
            "learning contract",
        ),
        (
            "flat Chapter 5 advanced heading",
            lambda: check_source(
                replace_text("chapter5", "### 5.8 実践スクリプト例", "## 5.8 実践スクリプト例"),
                check_workflow=False,
            ),
            "structure",
        ),
        (
            "missing advanced execution boundary",
            lambda: check_source(
                replace_text(
                    "chapter5",
                    "値と対象を置換し、差分・権限・rollbackをreviewできない段階では実行しません",
                    "そのまま実行します",
                ),
                check_workflow=False,
            ),
            "learning boundary",
        ),
    ]
    for label, action, expected in cases:
        expect_failure(label, action, expected)

    changed_blocks = copy.deepcopy(baseline.data)
    changed_blocks["pages"][1]["codeBlocks"] += 1
    expect_failure(
        "code block snapshot drift",
        lambda: check_source(Snapshot(baseline.top, baseline.chapter5, changed_blocks), check_workflow=False),
        "codeBlocks snapshot",
    )
    changed_date = copy.deepcopy(baseline.data)
    changed_date["confirmedDate"] = ""
    expect_failure(
        "missing confirmation date",
        lambda: check_source(Snapshot(baseline.top, baseline.chapter5, changed_date), check_workflow=False),
        "confirmedDate",
    )
    changed_hours = copy.deepcopy(baseline.data)
    changed_hours["learningPaths"][1]["handsOnHours"]["max"] += 1
    expect_failure(
        "learning path sum drift",
        lambda: check_source(Snapshot(baseline.top, baseline.chapter5, changed_hours), check_workflow=False),
        "handsOnHours must be",
    )
    print("Learning path contract self-test passed (7 negative mutations).")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--built-site", type=Path)
    args = parser.parse_args()
    if args.self_test and args.built_site is not None:
        raise ContractError("choose one of --self-test or --built-site")
    if args.self_test:
        self_test()
    elif args.built_site is not None:
        snapshot = load_source()
        check_built(args.built_site.resolve(), snapshot.data)
    else:
        snapshot = load_source()
        check_source(snapshot)
        print(
            "Learning path source contract passed "
            f"({len(snapshot.data['pages'])} pages, {snapshot.data['totals']['codeBlocks']} code blocks)."
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(f"Learning path contract failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
