from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path("sample_repos/checkout_app")
OUTPUT_DIR = Path("outputs/repo_aware")
EVIDENCE_DIR = Path("outputs/evidence")

DEPENDENCY_API_PATTERNS = {
    "auth-sdk": ["authenticate"],
    "profile-sdk": ["fetchUser", "getUserProfile"],
    "logging-lib": ["createLogger", "logger.info"],
    "analytics-sdk": ["trackEvent", "rateLimit"],
    "unknown-dep": ["unknownDep"]
}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_package_json() -> dict[str, Any]:
    return load_json(REPO_ROOT / "package.json")


def source_files() -> list[Path]:
    return sorted([
        p for p in (REPO_ROOT / "src").rglob("*")
        if p.is_file() and p.suffix in {".ts", ".tsx", ".js", ".jsx", ".py"}
    ])


def load_existing_goal_context() -> dict[str, Any]:
    delta_path = EVIDENCE_DIR / "dependency_delta_report.json"
    plan_path = EVIDENCE_DIR / "plan_summary_report.json"

    deltas = {}
    plan = {}

    if delta_path.exists():
        raw = load_json(delta_path)
        for row in raw.get("deltas", []):
            deltas[row["dependency_name"]] = row

    if plan_path.exists():
        plan = load_json(plan_path)

    return {
        "deltas": deltas,
        "plan": plan
    }


def classify_dependency_risk(dep: str, delta: dict[str, Any] | None, usage_count: int) -> dict[str, Any]:
    reasons = []
    risk = "LOW"

    if delta:
        if delta.get("version_delta_type") == "major":
            risk = "HIGH"
            reasons.append("major version jump")
        if delta.get("breaking_change_risk") == "high":
            risk = "HIGH"
            reasons.append("high breaking-change risk")
        if delta.get("version_status") == "unresolvable":
            risk = "HIGH"
            reasons.append("target version unresolved")
        if delta.get("breaking_change_risk") == "unknown":
            risk = "MEDIUM" if risk != "HIGH" else risk
            reasons.append("unknown breaking-change risk")
        if delta.get("version_delta_type") == "minor" and risk != "HIGH":
            risk = "MEDIUM"
            reasons.append("minor version movement")
        if delta.get("version_delta_type") == "patch" and risk == "LOW":
            reasons.append("patch update")
    else:
        risk = "MEDIUM"
        reasons.append("dependency not found in delta report")

    if usage_count >= 2 and risk == "LOW":
        risk = "MEDIUM"
        reasons.append("multiple callsites")

    if not reasons:
        reasons.append("low observed migration risk")

    return {
        "risk_level": risk,
        "risk_reasons": reasons
    }


def scan_callsites(package_deps: dict[str, str], deltas: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    callsites = []
    usage_by_dependency: dict[str, list[dict[str, Any]]] = {dep: [] for dep in package_deps}

    for file_path in source_files():
        text = file_path.read_text(encoding="utf-8")
        lines = text.splitlines()

        for dep, symbols in DEPENDENCY_API_PATTERNS.items():
            if dep not in package_deps:
                continue

            imported = dep in text
            for line_no, line in enumerate(lines, start=1):
                matched_symbols = []
                for symbol in symbols:
                    pattern = re.escape(symbol)
                    if re.search(pattern, line):
                        matched_symbols.append(symbol)

                if imported and matched_symbols:
                    delta = deltas.get(dep, {})
                    callsite = {
                        "dependency_name": dep,
                        "current_version": package_deps[dep],
                        "target_version": delta.get("target_version"),
                        "version_delta_type": delta.get("version_delta_type", "unknown"),
                        "breaking_change_risk": delta.get("breaking_change_risk", "unknown"),
                        "file_path": str(file_path),
                        "line_number": line_no,
                        "line": line.strip(),
                        "symbols": matched_symbols,
                        "usage_type": "direct_import_callsite"
                    }
                    callsites.append(callsite)
                    usage_by_dependency.setdefault(dep, []).append(callsite)

    return callsites, usage_by_dependency


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    package = read_package_json()
    dependencies = package.get("dependencies", {})
    context = load_existing_goal_context()
    deltas = context["deltas"]
    plan = context["plan"]

    callsites, usage_by_dependency = scan_callsites(dependencies, deltas)

    dependency_usage_rows = []
    risky_callsites = []

    for dep, version in dependencies.items():
        dep_callsites = usage_by_dependency.get(dep, [])
        risk = classify_dependency_risk(dep, deltas.get(dep), len(dep_callsites))

        row = {
            "dependency_name": dep,
            "current_version": version,
            "target_version": deltas.get(dep, {}).get("target_version"),
            "version_delta_type": deltas.get(dep, {}).get("version_delta_type", "unknown"),
            "breaking_change_risk": deltas.get(dep, {}).get("breaking_change_risk", "unknown"),
            "usage_count": len(dep_callsites),
            "files_touched": sorted(set(c["file_path"] for c in dep_callsites)),
            "risk_level": risk["risk_level"],
            "risk_reasons": risk["risk_reasons"]
        }
        dependency_usage_rows.append(row)

        for callsite in dep_callsites:
            enriched = {
                **callsite,
                "risk_level": risk["risk_level"],
                "risk_reasons": risk["risk_reasons"],
                "recommended_review_action": (
                    "manual reviewer required before migration"
                    if risk["risk_level"] == "HIGH"
                    else "review caveats before migration"
                    if risk["risk_level"] == "MEDIUM"
                    else "safe to include in staged migration candidate"
                )
            }
            if enriched["risk_level"] in {"HIGH", "MEDIUM"}:
                risky_callsites.append(enriched)

    high_risk_dependencies = [r["dependency_name"] for r in dependency_usage_rows if r["risk_level"] == "HIGH"]
    medium_risk_dependencies = [r["dependency_name"] for r in dependency_usage_rows if r["risk_level"] == "MEDIUM"]
    low_risk_dependencies = [r["dependency_name"] for r in dependency_usage_rows if r["risk_level"] == "LOW"]

    repo_inspection_report = {
        "artifact": "repo_inspection_report_v35",
        "extension": "DevPulse v3.5 repo-aware migration simulation",
        "repo_path": str(REPO_ROOT),
        "project_name": package.get("name"),
        "dependency_count": len(dependencies),
        "source_files_scanned": [str(p) for p in source_files()],
        "source_file_count": len(source_files()),
        "callsites_found": len(callsites),
        "high_risk_dependencies": high_risk_dependencies,
        "medium_risk_dependencies": medium_risk_dependencies,
        "low_risk_dependencies": low_risk_dependencies,
        "aggregate_repo_migration_readiness": (
            "BLOCKED" if high_risk_dependencies else "RISKY" if medium_risk_dependencies else "SAFE"
        ),
        "truth_boundary": {
            "claim": "local sample repo inspection and repo-aware migration simulation",
            "not_claimed": [
                "real customer repository analysis",
                "live GitHub integration",
                "real production PR generation",
                "full static type analysis",
                "full AST-based refactoring"
            ]
        },
        "evidence_statement": "DevPulse inspected a local sample repository, mapped dependency usage to source callsites, and connected usage risk to existing migration-plan evidence."
    }

    dependency_usage_map = {
        "artifact": "dependency_usage_map_v35",
        "dependency_usage_count": len(dependency_usage_rows),
        "dependencies": dependency_usage_rows,
        "callsites": callsites,
        "evidence_statement": "Maps dependency manifest entries to concrete source-file callsites in the sample repo."
    }

    risky_callsite_report = {
        "artifact": "risky_callsite_report_v35",
        "risky_callsite_count": len(risky_callsites),
        "risky_callsites": risky_callsites,
        "blocked_or_high_risk_dependencies": high_risk_dependencies,
        "reviewer_required": len(high_risk_dependencies) > 0,
        "evidence_statement": "Identifies source callsites that require reviewer attention before migration because dependency-level migration risk is HIGH or MEDIUM."
    }

    extension_summary = {
        "artifact": "repo_aware_extension_summary_v35",
        "status": "pass",
        "new_capabilities": [
            "sample repo inspection",
            "dependency usage mapping",
            "source callsite extraction",
            "risk propagation from migration plan to code usage",
            "repo-level migration readiness verdict"
        ],
        "new_artifacts": [
            "outputs/repo_aware/repo_inspection_report.json",
            "outputs/repo_aware/dependency_usage_map.json",
            "outputs/repo_aware/risky_callsite_report.json"
        ],
        "repo_migration_readiness": repo_inspection_report["aggregate_repo_migration_readiness"],
        "callsites_found": len(callsites),
        "risky_callsite_count": len(risky_callsites),
        "high_risk_dependency_count": len(high_risk_dependencies),
        "evidence_statement": "DevPulse v3.5 repo-aware extension adds codebase-aware migration intelligence without claiming live GitHub integration or autonomous code mutation."
    }

    write_json(OUTPUT_DIR / "repo_inspection_report.json", repo_inspection_report)
    write_json(OUTPUT_DIR / "dependency_usage_map.json", dependency_usage_map)
    write_json(OUTPUT_DIR / "risky_callsite_report.json", risky_callsite_report)
    write_json(OUTPUT_DIR / "repo_aware_extension_summary.json", extension_summary)

    print("repo_aware_scan_v35 complete")
    print(f"status: {extension_summary['status']}")
    print(f"repo_migration_readiness: {extension_summary['repo_migration_readiness']}")
    print(f"callsites_found: {extension_summary['callsites_found']}")
    print(f"risky_callsite_count: {extension_summary['risky_callsite_count']}")
    print("wrote outputs/repo_aware/repo_inspection_report.json")
    print("wrote outputs/repo_aware/dependency_usage_map.json")
    print("wrote outputs/repo_aware/risky_callsite_report.json")


if __name__ == "__main__":
    main()
