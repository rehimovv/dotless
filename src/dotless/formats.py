"""Output formats: text, JSON, SARIF 2.1.0 and GitLab Code Quality."""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter

from . import __version__
from .rules import RULES
from .scanner import Finding

INFO_URI = "https://gitlab.com/rehimovv/dotless"


def _rel(path: str) -> str:
    try:
        rel = os.path.relpath(path)
    except ValueError:  # different drive on Windows
        return path.replace(os.sep, "/")
    return path.replace(os.sep, "/") if rel.startswith("..") else rel.replace(os.sep, "/")


def _fingerprints(findings: list[Finding]) -> list[str]:
    """Stable per-finding ids that survive unrelated line shifts."""
    seen: Counter = Counter()
    out = []
    for f in findings:
        base = f"{f.rule}\0{_rel(f.path)}\0{f.snippet}"
        seen[base] += 1
        out.append(hashlib.sha256(f"{base}\0{seen[base]}".encode()).hexdigest()[:32])
    return out


def summary(findings: list[Finding], files: int) -> str:
    sev = Counter(f.severity for f in findings)
    return (
        f"{len(findings)} finding{'s' if len(findings) != 1 else ''} "
        f"({sev['high']} high, {sev['low']} low) in {files} file{'s' if files != 1 else ''} scanned"
    )


def text(findings: list[Finding], files: int, color: bool = False) -> str:
    def c(code: str, s: str) -> str:
        return f"\033[{code}m{s}\033[0m" if color else s

    lines = []
    for f in findings:
        sev = c("1;31", "high") if f.severity == "high" else c("33", "low")
        lines.append(f"{c('1', f'{_rel(f.path)}:{f.line}:{f.column}')}: [{sev}] {f.rule} {f.message}")
        lines.append(f"    {f.snippet}")
        lines.append(f"    why: {f.reason}")
        lines.append(f"    fix: {f.fix}")
    lines.append(summary(findings, files))
    return "\n".join(lines) + "\n"


def as_json(findings: list[Finding], files: int) -> str:
    items = []
    for f, fp in zip(findings, _fingerprints(findings)):
        d = f.to_dict()
        d["path"] = _rel(f.path)
        d["fingerprint"] = fp
        items.append(d)
    return json.dumps({"tool": "dotless", "version": __version__, "files_scanned": files, "findings": items}, indent=2) + "\n"


def sarif(findings: list[Finding], files: int) -> str:
    rule_ids = sorted(RULES)
    rules = [
        {
            "id": r.id,
            "name": r.name,
            "shortDescription": {"text": r.summary.split(":")[0]},
            "fullDescription": {"text": r.summary},
            "help": {"text": f"{r.summary}\n\nFix: {r.fix}", "markdown": f"{r.summary}\n\n**Fix:** {r.fix}"},
            "helpUri": r.help_uri,
            "defaultConfiguration": {"level": "warning"},
            "properties": {"tags": ["i18n", "locale", "turkish", "azerbaijani"]},
        }
        for r in (RULES[i] for i in rule_ids)
    ]
    results = []
    for f, fp in zip(findings, _fingerprints(findings)):
        results.append(
            {
                "ruleId": f.rule,
                "ruleIndex": rule_ids.index(f.rule),
                "level": "error" if f.severity == "high" else "warning",
                "message": {"text": f"{f.message} ({f.reason}). Fix: {f.fix}"},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": _rel(f.path), "uriBaseId": "%SRCROOT%"},
                            "region": {
                                "startLine": f.line,
                                "startColumn": f.column,
                                "endColumn": max(f.end_column, f.column + 1),
                            },
                        }
                    }
                ],
                "partialFingerprints": {"dotless/v1": fp},
                "properties": {"severity": f.severity, "reason": f.reason},
            }
        )
    doc = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "dotless",
                        "version": __version__,
                        "semanticVersion": __version__,
                        "informationUri": INFO_URI,
                        "rules": rules,
                    }
                },
                "results": results,
                "properties": {"filesScanned": files},
            }
        ],
    }
    return json.dumps(doc, indent=2) + "\n"


def gitlab(findings: list[Finding], files: int) -> str:
    """GitLab Code Quality report (CodeClimate subset)."""
    items = [
        {
            "type": "issue",
            "check_name": f"{f.rule} {RULES[f.rule].name}",
            "description": f"{f.message} ({f.reason})",
            "categories": ["Bug Risk"],
            "severity": "major" if f.severity == "high" else "minor",
            "fingerprint": fp,
            "location": {"path": _rel(f.path), "lines": {"begin": f.line}},
        }
        for f, fp in zip(findings, _fingerprints(findings))
    ]
    return json.dumps(items, indent=2) + "\n"


FORMATS = {"text": text, "json": as_json, "sarif": sarif, "gitlab": gitlab}
