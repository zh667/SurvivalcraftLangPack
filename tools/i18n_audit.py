#!/usr/bin/env python3
"""Audit Survivalcraft language JSON files against the English source.

The game has no English fallback, so every target file must retain the complete
source structure.  This tool also detects common machine-translation damage,
including changed placeholders and Crowdin's ``format@@0`` marker leakage.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Mapping, Sequence


PLACEHOLDER_RE = re.compile(r"\{[^{}]+\}")
MARKUP_RE = re.compile(r"</?[A-Za-z][^>]*>")
# Numeric tokens are often attached to units (0.8V, 25%, 2Hz), so only the
# left boundary excludes identifiers.  A right word boundary would truncate
# or completely miss those values.
NUMBER_RE = re.compile(r"(?<![A-Za-z0-9_.])\d+(?:[.,]\d+)?(?:/\d+(?:[.,]\d+)?)?")
POLLUTION_RE = re.compile(r"(?i)(?:format|a?unnamed)@@\d+|@@\d+")
ASCII_LETTER_RE = re.compile(r"[A-Za-z]")

EXPECTED_LANGUAGE_NAMES = {
    "ar-SA": "العربية",
    "de-DE": "Deutsch",
    "fr-FR": "Français",
    "hi-IN": "हिन्दी",
    "id-ID": "Bahasa Indonesia",
    "it-IT": "Italiano",
    "ja-JP": "日本語",
    "ko-KR": "한국어",
    "pl-PL": "Polski",
    "th-TH": "ไทย",
    "tr-TR": "Türkçe",
    "uk-UA": "Українська",
    "vi-VN": "Tiếng Việt",
}


@dataclass(frozen=True)
class Issue:
    severity: str
    category: str
    path: str
    message: str
    source: str | None = None
    translation: str | None = None


@dataclass
class LanguageAudit:
    file: str
    locale: str
    source_leaves: int
    target_leaves: int
    errors: List[Issue]
    warnings: List[Issue]

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    def category_counts(self) -> Counter[str]:
        return Counter(issue.category for issue in self.errors + self.warnings)


def flatten(value: Any, path: str = "") -> Dict[str, Any]:
    """Flatten JSON dictionaries/lists into stable leaf paths."""
    result: Dict[str, Any] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            result.update(flatten(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            result.update(flatten(child, f"{path}[{index}]"))
    else:
        result[path] = value
    return result


def token_counter(pattern: re.Pattern[str], value: str) -> Counter[str]:
    return Counter(pattern.findall(value))


def short(value: str, limit: int = 180) -> str:
    value = value.replace("\r", "\\r").replace("\n", "\\n")
    return value if len(value) <= limit else value[: limit - 1] + "…"


def compare_string(path: str, source: str, target: str) -> List[Issue]:
    issues: List[Issue] = []

    if not target.strip() and source.strip():
        issues.append(Issue("error", "empty_translation", path, "translation is empty", source, target))

    source_placeholders = token_counter(PLACEHOLDER_RE, source)
    target_placeholders = token_counter(PLACEHOLDER_RE, target)
    if source_placeholders != target_placeholders:
        issues.append(
            Issue(
                "error",
                "placeholder_mismatch",
                path,
                f"placeholders differ: source={dict(source_placeholders)}, target={dict(target_placeholders)}",
                source,
                target,
            )
        )

    source_markup = token_counter(MARKUP_RE, source)
    target_markup = token_counter(MARKUP_RE, target)
    if source_markup != target_markup:
        issues.append(
            Issue(
                "error",
                "markup_mismatch",
                path,
                f"markup differs: source={dict(source_markup)}, target={dict(target_markup)}",
                source,
                target,
            )
        )

    pollution = POLLUTION_RE.findall(target)
    if pollution:
        issues.append(
            Issue(
                "error",
                "mt_marker_pollution",
                path,
                f"machine-translation markers leaked into output: {pollution}",
                source,
                target,
            )
        )

    source_numbers = token_counter(NUMBER_RE, source)
    target_numbers = token_counter(NUMBER_RE, target)
    missing_numbers = source_numbers - target_numbers
    extra_numbers = target_numbers - source_numbers
    if missing_numbers:
        issues.append(
            Issue(
                "warning",
                "missing_numbers",
                path,
                f"numeric tokens missing from translation: {dict(missing_numbers)}",
                source,
                target,
            )
        )
    if extra_numbers:
        issues.append(
            Issue(
                "warning",
                "extra_numbers",
                path,
                f"translation contains additional numeric tokens: {dict(extra_numbers)}",
                source,
                target,
            )
        )

    if source.count("\n") != target.count("\n"):
        issues.append(
            Issue(
                "warning",
                "newline_mismatch",
                path,
                f"newline count differs: source={source.count(chr(10))}, target={target.count(chr(10))}",
                source,
                target,
            )
        )

    if source == target and source.strip() and ASCII_LETTER_RE.search(source):
        issues.append(
            Issue(
                "warning",
                "source_identical",
                path,
                "translation is identical to the English source",
                source,
                target,
            )
        )

    return issues


def audit_values(source: Mapping[str, Any], target: Mapping[str, Any], file_name: str) -> LanguageAudit:
    source_flat = flatten(source)
    target_flat = flatten(target)
    errors: List[Issue] = []
    warnings: List[Issue] = []

    for path in sorted(set(source_flat) - set(target_flat)):
        errors.append(Issue("error", "missing_key", path, "key is missing from translation"))
    for path in sorted(set(target_flat) - set(source_flat)):
        errors.append(Issue("error", "extra_key", path, "translation contains a key absent from the source"))

    for path in sorted(set(source_flat) & set(target_flat)):
        source_value = source_flat[path]
        target_value = target_flat[path]
        if type(source_value) is not type(target_value):
            errors.append(
                Issue(
                    "error",
                    "type_mismatch",
                    path,
                    f"leaf type differs: source={type(source_value).__name__}, target={type(target_value).__name__}",
                )
            )
            continue
        if isinstance(source_value, str):
            for issue in compare_string(path, source_value, target_value):
                (errors if issue.severity == "error" else warnings).append(issue)

    locale = Path(file_name).stem
    expected_name = EXPECTED_LANGUAGE_NAMES.get(locale)
    actual_name = target_flat.get("Language.Name")
    if expected_name is not None and actual_name != expected_name:
        errors.append(
            Issue(
                "error",
                "language_name_mismatch",
                "Language.Name",
                f"language menu name must be {expected_name!r}, found {actual_name!r}",
                translation=actual_name if isinstance(actual_name, str) else None,
            )
        )
    return LanguageAudit(file_name, locale, len(source_flat), len(target_flat), errors, warnings)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def audit_repository(root: Path) -> List[LanguageAudit]:
    source_path = root / "source" / "en-US.json"
    language_dir = root / "Assets" / "Lang"
    source = load_json(source_path)
    audits: List[LanguageAudit] = []

    for target_path in sorted(language_dir.glob("*.json")):
        try:
            target = load_json(target_path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            issue = Issue("error", "invalid_json", "$", str(exc))
            audits.append(LanguageAudit(target_path.name, target_path.stem, len(flatten(source)), 0, [issue], []))
            continue
        audits.append(audit_values(source, target, target_path.name))
    return audits


def render_markdown(audits: Sequence[LanguageAudit]) -> str:
    lines = [
        "# Translation QA audit",
        "",
        "Generated by `python tools/i18n_audit.py`. The English source is `source/en-US.json`.",
        "",
        "## Summary",
        "",
        "| Locale | Leaves | Errors | Warnings | Identical to English | Missing numbers | Extra numbers |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for audit in audits:
        counts = audit.category_counts()
        lines.append(
            f"| {audit.locale} | {audit.target_leaves}/{audit.source_leaves} | {audit.error_count} | "
            f"{audit.warning_count} | {counts['source_identical']} | {counts['missing_numbers']} | "
            f"{counts['extra_numbers']} |"
        )

    lines.extend(
        [
            "",
            "Errors must be fixed before release. Warnings require review because proper names and some",
            "number wording can legitimately match the source or differ between languages.",
            "",
            "## Error details",
            "",
        ]
    )

    any_errors = False
    for audit in audits:
        if not audit.errors:
            continue
        any_errors = True
        lines.extend([f"### {audit.locale}", ""])
        for issue in audit.errors:
            lines.append(f"- `{issue.category}` at `{issue.path}`: {issue.message}")
            if issue.source is not None:
                lines.append(f"  - Source: `{short(issue.source)}`")
            if issue.translation is not None:
                lines.append(f"  - Translation: `{short(issue.translation)}`")
        lines.append("")
    if not any_errors:
        lines.extend(["No release-blocking errors found.", ""])

    lines.extend(["## Warning samples", ""])
    for audit in audits:
        if not audit.warnings:
            continue
        lines.extend([f"### {audit.locale}", ""])
        for issue in audit.warnings[:10]:
            lines.append(f"- `{issue.category}` at `{issue.path}`: {issue.message}")
            if issue.source is not None:
                lines.append(f"  - Source: `{short(issue.source)}`")
            if issue.translation is not None and issue.translation != issue.source:
                lines.append(f"  - Translation: `{short(issue.translation)}`")
        if len(audit.warnings) > 10:
            lines.append(f"- … {len(audit.warnings) - 10} additional warnings omitted from this Markdown report.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def serialise(audits: Iterable[LanguageAudit]) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for audit in audits:
        item = {
            "file": audit.file,
            "locale": audit.locale,
            "source_leaves": audit.source_leaves,
            "target_leaves": audit.target_leaves,
            "error_count": audit.error_count,
            "warning_count": audit.warning_count,
            "category_counts": dict(sorted(audit.category_counts().items())),
            "errors": [asdict(issue) for issue in audit.errors],
            "warnings": [asdict(issue) for issue in audit.warnings],
        }
        result.append(item)
    return result


def parse_args() -> argparse.Namespace:
    default_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=default_root, help="repository root")
    parser.add_argument("--report", type=Path, help="write a Markdown report")
    parser.add_argument("--json-report", type=Path, help="write a machine-readable JSON report")
    parser.add_argument("--strict", action="store_true", help="exit non-zero when errors are found")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    audits = audit_repository(root)
    for audit in audits:
        print(f"{audit.locale:8} errors={audit.error_count:4} warnings={audit.warning_count:4}")

    if args.report:
        report_path = args.report if args.report.is_absolute() else root / args.report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_markdown(audits), encoding="utf-8")
        print(f"Markdown report: {report_path}")
    if args.json_report:
        json_path = args.json_report if args.json_report.is_absolute() else root / args.json_report
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(serialise(audits), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"JSON report: {json_path}")

    has_errors = any(audit.errors for audit in audits)
    return 1 if args.strict and has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
