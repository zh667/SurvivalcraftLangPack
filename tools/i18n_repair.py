#!/usr/bin/env python3
"""Apply conservative, deterministic repairs to exported language files.

This does not attempt to improve translation prose.  It only restores values
that are required for the game to load safely: language menu names,
placeholders, formatting tags, literal separators, and leaked MT markers.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:  # Package import in tests.
    from .i18n_audit import (
        EXPECTED_LANGUAGE_NAMES,
        MARKUP_RE,
        PLACEHOLDER_RE,
        POLLUTION_RE,
        token_counter,
    )
except ImportError:  # Direct execution: python tools/i18n_repair.py
    from i18n_audit import (
        EXPECTED_LANGUAGE_NAMES,
        MARKUP_RE,
        PLACEHOLDER_RE,
        POLLUTION_RE,
        token_counter,
    )


def remove_last(value: str, token: str) -> str:
    index = value.rfind(token)
    return value if index < 0 else value[:index] + value[index + len(token) :]


def restore_markup(source: str, target: str) -> Tuple[str, bool]:
    """Restore the exact source tag sequence while keeping translated prose."""
    original_target = target
    source_tags = MARKUP_RE.findall(source)
    target_tags = MARKUP_RE.findall(target)
    if source_tags == target_tags:
        return target, False

    # Remove duplicated target-only closing tags first. This repairs common MT
    # output such as </em></em> without changing surrounding translated text.
    if len(target_tags) > len(source_tags):
        extras = Counter(target_tags) - Counter(source_tags)
        for tag, count in extras.items():
            for _ in range(count):
                target = remove_last(target, tag)

    target_tags = MARKUP_RE.findall(target)
    if len(target_tags) != len(source_tags):
        return source, True

    iterator = iter(source_tags)
    restored = MARKUP_RE.sub(lambda _match: next(iterator), target)
    if MARKUP_RE.findall(restored) != source_tags:
        return source, True
    return restored, restored != original_target


def repair_string(source: str, target: str) -> Tuple[str, List[str]]:
    reasons: List[str] = []

    if not target.strip() and source.strip():
        target = source
        reasons.append("empty_fallback")

    if POLLUTION_RE.search(target):
        target = source
        reasons.append("mt_marker_fallback")

    # Some MT engines turn the literal vertical separator into <unk>.
    missing_pipes = max(0, source.count("|") - target.count("|"))
    for _ in range(missing_pipes):
        if "<unk>" not in target:
            break
        target = target.replace("<unk>", "|", 1)
        reasons.append("separator_restored")

    restored, changed = restore_markup(source, target)
    if changed:
        target = restored
        reasons.append("markup_restored")

    if token_counter(PLACEHOLDER_RE, source) != token_counter(PLACEHOLDER_RE, target):
        target = source
        reasons.append("placeholder_fallback")

    return target, reasons


def repair_tree(source: Any, target: Any, changes: Counter[str]) -> Any:
    if isinstance(source, dict) and isinstance(target, dict):
        for key, source_value in source.items():
            if key in target:
                target[key] = repair_tree(source_value, target[key], changes)
        return target
    if isinstance(source, list) and isinstance(target, list):
        for index, source_value in enumerate(source):
            if index < len(target):
                target[index] = repair_tree(source_value, target[index], changes)
        return target
    if isinstance(source, str) and isinstance(target, str):
        repaired, reasons = repair_string(source, target)
        changes.update(reasons)
        return repaired
    return target


def repair_file(source: Any, target_path: Path, write: bool) -> Counter[str]:
    with target_path.open("r", encoding="utf-8") as handle:
        target = json.load(handle)
    changes: Counter[str] = Counter()
    repaired = repair_tree(source, target, changes)

    expected_name = EXPECTED_LANGUAGE_NAMES.get(target_path.stem)
    if expected_name and isinstance(repaired.get("Language"), dict):
        if repaired["Language"].get("Name") != expected_name:
            repaired["Language"]["Name"] = expected_name
            changes["language_name_restored"] += 1

    if write and changes:
        target_path.write_text(json.dumps(repaired, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changes


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=root, help="repository root")
    parser.add_argument("--write", action="store_true", help="write changes (default is dry-run)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    with (root / "source" / "en-US.json").open("r", encoding="utf-8") as handle:
        source = json.load(handle)

    total: Counter[str] = Counter()
    for target_path in sorted((root / "Assets" / "Lang").glob("*.json")):
        changes = repair_file(source, target_path, args.write)
        total.update(changes)
        detail = ", ".join(f"{key}={value}" for key, value in sorted(changes.items())) or "clean"
        print(f"{target_path.stem:8} {detail}")
    print("mode:", "write" if args.write else "dry-run")
    print("total:", dict(sorted(total.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
