from __future__ import annotations

import json
import math
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class Chunk:
    chunk_id: str
    source_url: str
    doc_type: str
    version_tag: str
    section_title: str
    content: str
    api_names: list[str]
    change_type: str
    has_deprecation: bool = False
    replacement_api: str | None = None
    freshness_score: float = 1.0


@dataclass
class ParsedQuery:
    raw_query: str
    intent: str
    api_names: list[str]
    version_mentions: list[str]


@dataclass
class VersionContext:
    mode: str
    explicit_versions: list[str]
    from_version: str | None = None
    to_version: str | None = None


@dataclass
class RetrievalTrace:
    chunk_id: str
    bm25_score: float
    vector_score: float
    rrf_score: float
    rank: int
    selected: bool
    version_tag: str
    doc_type: str


@dataclass
class ConflictAlert:
    conflict_type: str
    severity: str
    chunk_ids: list[str]
    description: str


@dataclass
class MigrationDecisionReport:
    query_id: str
    verdict: str
    from_version: str | None
    to_version: str | None
    conflict_count: dict[str, int]
    version_coverage: dict[str, str]
    source_freshness_min: float
    grounding_rate: float
    citations: list[dict[str, Any]]
    synthesis_text: str | None
    caveats: list[str]
    generated_at: str


@dataclass
class QueryModeResult:
    query_id: str
    parsed_query: ParsedQuery
    version_context: VersionContext
    route_taken: str
    retrieved_chunks: list[dict[str, Any]]
    retrieval_traces: list[RetrievalTrace]
    conflict_alerts: list[ConflictAlert]
    conflict_flag: bool
    migration_report: MigrationDecisionReport
    fallback_events: list[dict[str, Any]] = field(default_factory=list)


def demo_corpus() -> list[Chunk]:
    return [
        Chunk(
            chunk_id="chunk_v2_auth_ref",
            source_url="docs/reference/v2/authenticate",
            doc_type="reference",
            version_tag="v2",
            section_title="authenticate() reference v2",
            content="In v2, authenticate(api_key) accepts an API key string and returns a session token.",
            api_names=["authenticate"],
            change_type="current",
        ),
        Chunk(
            chunk_id="chunk_v3_auth_ref",
            source_url="docs/reference/v3/authenticate",
            doc_type="reference",
            version_tag="v3",
            section_title="authenticate() reference v3",
            content="In v3, authenticate(client_id, client_secret) replaces api_key authentication and returns an OAuth session.",
            api_names=["authenticate"],
            change_type="modified",
        ),
        Chunk(
            chunk_id="chunk_v3_migration_auth",
            source_url="docs/migration/v2-to-v3/authenticate",
            doc_type="migration_guide",
            version_tag="v3",
            section_title="Migrating authenticate() from v2 to v3",
            content="When migrating from v2 to v3, replace authenticate(api_key) with authenticate(client_id, client_secret).",
            api_names=["authenticate"],
            change_type="breaking",
            replacement_api="authenticate(client_id, client_secret)",
        ),
        Chunk(
            chunk_id="chunk_v2_fetch_ref",
            source_url="docs/reference/v2/fetchUser",
            doc_type="reference",
            version_tag="v2",
            section_title="fetchUser() reference v2",
            content="In v2, fetchUser(user_id) returns a user profile object.",
            api_names=["fetchUser"],
            change_type="current",
        ),
        Chunk(
            chunk_id="chunk_v3_fetch_changelog",
            source_url="docs/changelog/v3/fetchUser",
            doc_type="changelog",
            version_tag="v3",
            section_title="fetchUser renamed in v3",
            content="In v3, fetchUser is deprecated. Use getUserProfile(user_id) instead.",
            api_names=["fetchUser", "getUserProfile"],
            change_type="deprecated",
            has_deprecation=True,
            replacement_api="getUserProfile",
        ),
        Chunk(
            chunk_id="chunk_v3_fetch_ref_stale",
            source_url="docs/reference/v3/fetchUser",
            doc_type="reference",
            version_tag="v3",
            section_title="fetchUser() reference v3 stale page",
            content="In v3, fetchUser(user_id) returns a user profile object.",
            api_names=["fetchUser"],
            change_type="current",
            freshness_score=0.25,
        ),
        Chunk(
            chunk_id="chunk_v3_rate_ref",
            source_url="docs/reference/v3/rateLimit",
            doc_type="reference",
            version_tag="v3",
            section_title="rateLimit v3",
            content="In v3, rateLimit is 1000 requests per minute for paid plans.",
            api_names=["rateLimit"],
            change_type="current",
        ),
        Chunk(
            chunk_id="chunk_v2_rate_ref",
            source_url="docs/reference/v2/rateLimit",
            doc_type="reference",
            version_tag="v2",
            section_title="rateLimit v2",
            content="In v2, rateLimit is 500 requests per minute for paid plans.",
            api_names=["rateLimit"],
            change_type="current",
        ),
        Chunk(
            chunk_id="chunk_v3_logging_ref_stale",
            source_url="docs/reference/v3/logging",
            doc_type="reference",
            version_tag="v3",
            section_title="logging reference v3 stale page",
            content="In v3, logging supports structured event payloads, but this page is marked stale and needs reviewer confirmation.",
            api_names=["logging"],
            change_type="current",
            freshness_score=0.25,
        ),
    ]


def parse_query(raw_query: str) -> ParsedQuery:
    q = raw_query.strip()
    lowered = q.lower()

    api_names = []
    for api in ["authenticate", "fetchUser", "getUserProfile", "rateLimit", "logging"]:
        if api.lower() in lowered:
            api_names.append(api)

    versions = re.findall(r"\bv\d+(?:\.\d+)?\b", lowered)

    if "migrate" in lowered or "migration" in lowered or "from v" in lowered or "to v" in lowered:
        intent = "migration"
    elif "changed" in lowered or "between" in lowered or "compare" in lowered:
        intent = "comparison"
    else:
        intent = "lookup"

    return ParsedQuery(
        raw_query=q,
        intent=intent,
        api_names=api_names,
        version_mentions=versions,
    )


def extract_version(parsed: ParsedQuery) -> VersionContext:
    versions = parsed.version_mentions

    if len(versions) >= 2:
        return VersionContext(
            mode="range",
            explicit_versions=versions,
            from_version=versions[0],
            to_version=versions[-1],
        )

    if len(versions) == 1:
        return VersionContext(
            mode="explicit",
            explicit_versions=versions,
            from_version=None,
            to_version=versions[0],
        )

    if "latest" in parsed.raw_query.lower() or "current" in parsed.raw_query.lower():
        return VersionContext(mode="inferred_latest", explicit_versions=[])

    return VersionContext(mode="none", explicit_versions=[])


def route_query(parsed: ParsedQuery, version_context: VersionContext) -> str:
    if parsed.intent in {"migration", "comparison"} or version_context.mode == "range":
        return "MIGRATION"
    if parsed.intent == "lookup" and version_context.mode == "explicit":
        return "SIMPLE"
    return "HYBRID"


def token_score(query: str, text: str) -> float:
    query_tokens = set(re.findall(r"[a-zA-Z0-9_]+", query.lower()))
    text_tokens = set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))
    if not query_tokens:
        return 0.0
    return len(query_tokens & text_tokens) / math.sqrt(len(query_tokens))


def version_allowed(chunk: Chunk, vc: VersionContext) -> bool:
    if vc.mode == "explicit" and vc.to_version:
        return chunk.version_tag == vc.to_version
    if vc.mode == "range":
        return chunk.version_tag in set(vc.explicit_versions)
    return True


def retrieve(raw_query: str, parsed: ParsedQuery, vc: VersionContext, route: str, corpus: list[Chunk]) -> tuple[list[Chunk], list[RetrievalTrace]]:
    eligible = [c for c in corpus if version_allowed(c, vc)]

    api_filter = set(parsed.api_names)
    if api_filter:
        api_matched = [c for c in eligible if api_filter & set(c.api_names)]
        if api_matched:
            eligible = api_matched

    traces = []
    scored = []
    for chunk in eligible:
        bm25 = token_score(raw_query, chunk.content) + (0.25 if set(parsed.api_names) & set(chunk.api_names) else 0.0)
        vector = token_score(raw_query, chunk.section_title + " " + chunk.content) * 0.85
        if vc.mode == "inferred_latest" and chunk.version_tag == "v3":
            vector += 0.2
        if parsed.intent == "migration" and chunk.doc_type == "migration_guide":
            bm25 += 0.4

        rrf = bm25 + vector + (chunk.freshness_score * 0.05)
        scored.append((rrf, bm25, vector, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:5]

    for rank, (rrf, bm25, vector, chunk) in enumerate(scored, start=1):
        traces.append(
            RetrievalTrace(
                chunk_id=chunk.chunk_id,
                bm25_score=round(bm25, 4),
                vector_score=round(vector, 4),
                rrf_score=round(rrf, 4),
                rank=rank,
                selected=rank <= 5,
                version_tag=chunk.version_tag,
                doc_type=chunk.doc_type,
            )
        )

    return [row[3] for row in top], traces


def detect_conflicts(chunks: list[Chunk], parsed: ParsedQuery, vc: VersionContext) -> list[ConflictAlert]:
    alerts: list[ConflictAlert] = []
    version_graph = build_api_version_graph(chunks)

    by_api: dict[str, list[Chunk]] = {}
    for chunk in chunks:
        for api in chunk.api_names:
            by_api.setdefault(api, []).append(chunk)

    for api, api_chunks in by_api.items():
        versions = {c.version_tag for c in api_chunks}
        change_types = {c.change_type for c in api_chunks}

        if len(versions) > 1 and len(change_types) > 1:
            # Calibrate severity by semver distance: large jumps (v1→v3) are more dangerous
            sorted_versions = version_graph.get(api, sorted(versions, key=parse_semver))
            max_dist = max(
                (semver_distance(sorted_versions[i], sorted_versions[j])
                 for i in range(len(sorted_versions))
                 for j in range(i + 1, len(sorted_versions))),
                default=0,
            )
            severity = "CRITICAL" if max_dist >= 2 else "HIGH"
            alerts.append(
                ConflictAlert(
                    conflict_type="same_api_different_behavior",
                    severity=severity,
                    chunk_ids=[c.chunk_id for c in api_chunks],
                    description=(
                        f"{api} has different behavior/change semantics across "
                        f"{sorted_versions} (semver distance: {max_dist})."
                    ),
                )
            )

        deprecated_chunks = [c for c in api_chunks if c.has_deprecation or c.change_type == "deprecated"]
        current_chunks = [c for c in api_chunks if c.change_type == "current"]
        if deprecated_chunks and current_chunks:
            # Version ordering violation: if "deprecated" appears in a NEWER version than
            # "current" that is backwards and signals a retrieval or corpus anomaly.
            dep_versions = [c.version_tag for c in deprecated_chunks]
            cur_versions = [c.version_tag for c in current_chunks]
            ordering_violation = any(
                semver_lt(cur_v, dep_v)
                for dep_v in dep_versions
                for cur_v in cur_versions
            )
            if ordering_violation:
                alerts.append(
                    ConflictAlert(
                        conflict_type="version_ordering_violation",
                        severity="CRITICAL",
                        chunk_ids=[c.chunk_id for c in deprecated_chunks + current_chunks],
                        description=(
                            f"{api} is marked 'deprecated' in a NEWER version than where it "
                            "appears as 'current'. This version-ordering anomaly likely indicates "
                            "a corpus ingestion bug or mislabelled chunk."
                        ),
                    )
                )
            else:
                alerts.append(
                    ConflictAlert(
                        conflict_type="version_deprecation_conflict",
                        severity="HIGH",
                        chunk_ids=[c.chunk_id for c in deprecated_chunks + current_chunks],
                        description=f"{api} is marked deprecated in one source but current in another.",
                    )
                )

        stale_chunks = [c for c in api_chunks if c.freshness_score < 0.4]
        if stale_chunks:
            alerts.append(
                ConflictAlert(
                    conflict_type="stale_doc_detected",
                    severity="MEDIUM",
                    chunk_ids=[c.chunk_id for c in stale_chunks],
                    description=f"{api} has stale documentation below freshness threshold.",
                )
            )

    if vc.mode == "range" and vc.to_version:
        to_version_chunks = [c for c in chunks if c.version_tag == vc.to_version]
        if not to_version_chunks:
            alerts.append(
                ConflictAlert(
                    conflict_type="missing_to_version_coverage",
                    severity="HIGH",
                    chunk_ids=[],
                    description=f"No retrieved evidence covers target version {vc.to_version}.",
                )
            )

    return dedupe_alerts(alerts)


# ── semver utilities ─────────────────────────────────────────────────────────

def parse_semver(tag: str) -> tuple[int, ...]:
    """Parse 'v2', 'v3.1', 'v2.1.0' → (2,), (3, 1), (2, 1, 0).

    Strips leading 'v'/'V'. Non-numeric segments fall back to (0,).
    """
    cleaned = tag.strip().lstrip("vV")
    if not cleaned:
        return (0,)
    try:
        return tuple(int(p) for p in cleaned.split("."))
    except ValueError:
        return (0,)


def semver_lt(a: str, b: str) -> bool:
    """Return True if version tag a is strictly older than b."""
    return parse_semver(a) < parse_semver(b)


def semver_distance(a: str, b: str) -> int:
    """Major-version distance between two tags (e.g. v1 → v4 = 3)."""
    sv_a, sv_b = parse_semver(a), parse_semver(b)
    return abs((sv_b[0] if sv_b else 0) - (sv_a[0] if sv_a else 0))


def build_api_version_graph(chunks: list[Chunk]) -> dict[str, list[str]]:
    """For each API name, return its observed version tags sorted by semver ascending."""
    api_versions: dict[str, set[str]] = {}
    for chunk in chunks:
        for api in chunk.api_names:
            api_versions.setdefault(api, set()).add(chunk.version_tag)
    return {
        api: sorted(versions, key=parse_semver)
        for api, versions in api_versions.items()
    }


def dedupe_alerts(alerts: list[ConflictAlert]) -> list[ConflictAlert]:
    seen = set()
    unique = []
    for alert in alerts:
        key = (alert.conflict_type, tuple(sorted(alert.chunk_ids)), alert.severity)
        if key not in seen:
            seen.add(key)
            unique.append(alert)
    return unique


def assemble_citations(chunks: list[Chunk], traces: list[RetrievalTrace]) -> list[dict[str, Any]]:
    trace_by_id = {t.chunk_id: t for t in traces}
    citations = []
    for chunk in chunks:
        trace = trace_by_id.get(chunk.chunk_id)
        citations.append(
            {
                "chunk_id": chunk.chunk_id,
                "source_url": chunk.source_url,
                "version_tag": chunk.version_tag,
                "doc_type": chunk.doc_type,
                "section_title": chunk.section_title,
                "retrieval_score": trace.rrf_score if trace else None,
            }
        )
    return citations


def create_migration_report(
    query_id: str,
    parsed: ParsedQuery,
    vc: VersionContext,
    chunks: list[Chunk],
    traces: list[RetrievalTrace],
    alerts: list[ConflictAlert],
) -> MigrationDecisionReport:
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for alert in alerts:
        severity_counts[alert.severity.lower()] += 1

    has_critical_or_high = severity_counts["critical"] > 0 or severity_counts["high"] > 0

    retrieved_versions = {c.version_tag for c in chunks}
    version_coverage = {
        "from_version": "complete" if vc.from_version and vc.from_version in retrieved_versions else ("not_requested" if not vc.from_version else "missing"),
        "to_version": "complete" if vc.to_version and vc.to_version in retrieved_versions else ("not_requested" if not vc.to_version else "missing"),
    }

    source_freshness_min = min([c.freshness_score for c in chunks], default=0.0)

    if has_critical_or_high or version_coverage["to_version"] == "missing":
        verdict = "BLOCKED"
        synthesis_text = None
        grounding_rate = 1.0
        caveats = [
            "Synthesis suppressed because unresolved high/critical conflict or missing target-version coverage exists."
        ] + [a.description for a in alerts]
    elif severity_counts["medium"] > 0 or source_freshness_min < 0.4:
        verdict = "RISKY"
        synthesis_text = "Evidence is mostly usable, but migration should proceed only with caveats and reviewer validation."
        grounding_rate = 0.95
        caveats = [a.description for a in alerts] or ["Minor coverage or freshness caveat."]
    else:
        verdict = "SAFE"
        synthesis_text = "Retrieved evidence supports this migration guidance with version-aligned citations."
        grounding_rate = 1.0
        caveats = []

    return MigrationDecisionReport(
        query_id=query_id,
        verdict=verdict,
        from_version=vc.from_version,
        to_version=vc.to_version,
        conflict_count=severity_counts,
        version_coverage=version_coverage,
        source_freshness_min=round(source_freshness_min, 3),
        grounding_rate=grounding_rate,
        citations=assemble_citations(chunks, traces),
        synthesis_text=synthesis_text,
        caveats=caveats,
        generated_at=now_iso(),
    )


def run_query(raw_query: str, corpus: list[Chunk] | None = None) -> QueryModeResult:
    query_id = stable_id("query")
    corpus = corpus or demo_corpus()

    parsed = parse_query(raw_query)
    vc = extract_version(parsed)
    route = route_query(parsed, vc)
    chunks, traces = retrieve(raw_query, parsed, vc, route, corpus)
    alerts = detect_conflicts(chunks, parsed, vc)
    report = create_migration_report(query_id, parsed, vc, chunks, traces, alerts)

    fallback_events = []
    if report.verdict == "BLOCKED":
        fallback_events.append(
            {
                "event_id": stable_id("fallback"),
                "query_id": query_id,
                "reason": "blocked_verdict_or_unresolved_conflict",
                "fallback_path": "evidence_only_response",
                "outcome": "synthesis_suppressed",
                "created_at": now_iso(),
            }
        )

    return QueryModeResult(
        query_id=query_id,
        parsed_query=parsed,
        version_context=vc,
        route_taken=route,
        retrieved_chunks=[asdict(c) for c in chunks],
        retrieval_traces=traces,
        conflict_alerts=alerts,
        conflict_flag=len(alerts) > 0,
        migration_report=report,
        fallback_events=fallback_events,
    )


def result_to_dict(result: QueryModeResult) -> dict[str, Any]:
    return {
        "query_id": result.query_id,
        "parsed_query": asdict(result.parsed_query),
        "version_context": asdict(result.version_context),
        "route_taken": result.route_taken,
        "retrieved_chunks": result.retrieved_chunks,
        "retrieval_traces": [asdict(t) for t in result.retrieval_traces],
        "conflict_alerts": [asdict(a) for a in result.conflict_alerts],
        "conflict_flag": result.conflict_flag,
        "migration_report": asdict(result.migration_report),
        "fallback_events": result.fallback_events,
    }


def write_json(path: str | Path, payload: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
