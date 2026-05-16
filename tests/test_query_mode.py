"""Unit tests for devpulse query_mode core logic.

All functions under test are pure Python with no external I/O or LLM calls.
Tests cover: query parsing, version extraction, route selection, conflict
detection, retrieval filtering, and migration report verdict logic.
"""

import pytest

from src.devpulse.core.query_mode import (
    Chunk,
    ConflictAlert,
    ParsedQuery,
    VersionContext,
    create_migration_report,
    dedupe_alerts,
    demo_corpus,
    detect_conflicts,
    extract_version,
    parse_query,
    retrieve,
    route_query,
    run_query,
    token_score,
    version_allowed,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def corpus():
    return demo_corpus()


@pytest.fixture
def auth_chunk_v2():
    return Chunk(
        chunk_id="c_v2_auth",
        source_url="docs/ref/v2/auth",
        doc_type="reference",
        version_tag="v2",
        section_title="authenticate v2",
        content="In v2, authenticate(api_key) returns a session token.",
        api_names=["authenticate"],
        change_type="current",
    )


@pytest.fixture
def auth_chunk_v3():
    return Chunk(
        chunk_id="c_v3_auth",
        source_url="docs/ref/v3/auth",
        doc_type="reference",
        version_tag="v3",
        section_title="authenticate v3",
        content="In v3, authenticate(client_id, client_secret) replaces api_key.",
        api_names=["authenticate"],
        change_type="modified",
    )


@pytest.fixture
def stale_chunk():
    return Chunk(
        chunk_id="c_stale",
        source_url="docs/ref/v3/stale",
        doc_type="reference",
        version_tag="v3",
        section_title="stale reference",
        content="This page is outdated.",
        api_names=["logging"],
        change_type="current",
        freshness_score=0.20,
    )


@pytest.fixture
def deprecated_chunk():
    return Chunk(
        chunk_id="c_deprecated",
        source_url="docs/changelog/v3/fetchUser",
        doc_type="changelog",
        version_tag="v3",
        section_title="fetchUser deprecated",
        content="fetchUser is deprecated. Use getUserProfile instead.",
        api_names=["fetchUser"],
        change_type="deprecated",
        has_deprecation=True,
        replacement_api="getUserProfile",
    )


# ---------------------------------------------------------------------------
# parse_query
# ---------------------------------------------------------------------------

class TestParseQuery:
    def test_detects_migration_intent(self):
        result = parse_query("How do I migrate authenticate from v2 to v3?")
        assert result.intent == "migration"

    def test_detects_lookup_intent(self):
        result = parse_query("How does authenticate work in v3?")
        assert result.intent == "lookup"

    def test_detects_comparison_intent(self):
        result = parse_query("What changed between v2 and v3 for rateLimit?")
        assert result.intent in ("comparison", "migration")

    def test_extracts_api_names(self):
        result = parse_query("How does fetchUser work in v3?")
        assert "fetchUser" in result.api_names

    def test_extracts_multiple_api_names(self):
        result = parse_query("Comparing authenticate and rateLimit between v2 and v3")
        assert "authenticate" in result.api_names
        assert "rateLimit" in result.api_names

    def test_extracts_version_mentions(self):
        result = parse_query("How does authenticate work in v3?")
        assert "v3" in result.version_mentions

    def test_extracts_version_range(self):
        result = parse_query("Migrating from v2 to v3")
        assert "v2" in result.version_mentions
        assert "v3" in result.version_mentions

    def test_no_api_names_on_generic_query(self):
        result = parse_query("How do I get started with the SDK?")
        assert result.api_names == []

    def test_raw_query_preserved(self):
        q = "How does authenticate work in v3?"
        result = parse_query(q)
        assert result.raw_query == q


# ---------------------------------------------------------------------------
# extract_version
# ---------------------------------------------------------------------------

class TestExtractVersion:
    def test_range_mode_for_two_versions(self):
        parsed = ParsedQuery("migrate from v2 to v3", "migration", ["authenticate"], ["v2", "v3"])
        vc = extract_version(parsed)
        assert vc.mode == "range"
        assert vc.from_version == "v2"
        assert vc.to_version == "v3"

    def test_explicit_mode_for_single_version(self):
        parsed = ParsedQuery("auth in v3", "lookup", ["authenticate"], ["v3"])
        vc = extract_version(parsed)
        assert vc.mode == "explicit"
        assert vc.to_version == "v3"

    def test_inferred_latest_for_current_keyword(self):
        parsed = ParsedQuery("latest authenticate docs", "lookup", ["authenticate"], [])
        vc = extract_version(parsed)
        assert vc.mode == "inferred_latest"

    def test_none_mode_when_no_version_info(self):
        parsed = ParsedQuery("authenticate docs", "lookup", ["authenticate"], [])
        vc = extract_version(parsed)
        assert vc.mode == "none"


# ---------------------------------------------------------------------------
# route_query
# ---------------------------------------------------------------------------

class TestRouteQuery:
    def test_migration_intent_routes_to_migration(self):
        parsed = ParsedQuery("migrate v2 to v3", "migration", [], ["v2", "v3"])
        vc = VersionContext(mode="range", explicit_versions=["v2", "v3"], from_version="v2", to_version="v3")
        assert route_query(parsed, vc) == "MIGRATION"

    def test_lookup_with_explicit_version_routes_to_simple(self):
        parsed = ParsedQuery("auth in v3", "lookup", ["authenticate"], ["v3"])
        vc = VersionContext(mode="explicit", explicit_versions=["v3"], to_version="v3")
        assert route_query(parsed, vc) == "SIMPLE"

    def test_lookup_without_version_routes_to_hybrid(self):
        parsed = ParsedQuery("how to authenticate", "lookup", ["authenticate"], [])
        vc = VersionContext(mode="none", explicit_versions=[])
        assert route_query(parsed, vc) == "HYBRID"


# ---------------------------------------------------------------------------
# version_allowed
# ---------------------------------------------------------------------------

class TestVersionAllowed:
    def test_explicit_mode_filters_to_target_version(self, auth_chunk_v2, auth_chunk_v3):
        vc = VersionContext(mode="explicit", explicit_versions=["v3"], to_version="v3")
        assert not version_allowed(auth_chunk_v2, vc)
        assert version_allowed(auth_chunk_v3, vc)

    def test_range_mode_allows_both_versions(self, auth_chunk_v2, auth_chunk_v3):
        vc = VersionContext(mode="range", explicit_versions=["v2", "v3"], from_version="v2", to_version="v3")
        assert version_allowed(auth_chunk_v2, vc)
        assert version_allowed(auth_chunk_v3, vc)

    def test_none_mode_allows_all(self, auth_chunk_v2, auth_chunk_v3):
        vc = VersionContext(mode="none", explicit_versions=[])
        assert version_allowed(auth_chunk_v2, vc)
        assert version_allowed(auth_chunk_v3, vc)


# ---------------------------------------------------------------------------
# token_score
# ---------------------------------------------------------------------------

class TestTokenScore:
    def test_exact_match_scores_higher_than_no_match(self):
        high = token_score("authenticate api key", "authenticate(api_key) returns session")
        low = token_score("authenticate api key", "unrelated content about database")
        assert high > low

    def test_empty_query_returns_zero(self):
        assert token_score("", "some content") == 0.0


# ---------------------------------------------------------------------------
# detect_conflicts
# ---------------------------------------------------------------------------

class TestDetectConflicts:
    def test_same_api_different_behavior_triggers_critical(self, auth_chunk_v2, auth_chunk_v3):
        parsed = ParsedQuery("authenticate v2 to v3", "migration", ["authenticate"], ["v2", "v3"])
        vc = VersionContext(mode="range", explicit_versions=["v2", "v3"], from_version="v2", to_version="v3")
        alerts = detect_conflicts([auth_chunk_v2, auth_chunk_v3], parsed, vc)
        critical = [a for a in alerts if a.conflict_type == "same_api_different_behavior"]
        assert len(critical) > 0
        assert critical[0].severity == "CRITICAL"

    def test_deprecation_conflict_detected(self, auth_chunk_v2, deprecated_chunk):
        # auth_chunk_v2 is "current", deprecated_chunk references fetchUser as deprecated
        # Add a "current" fetchUser chunk
        current_fetch = Chunk(
            chunk_id="c_v2_fetch",
            source_url="docs/ref/v2/fetch",
            doc_type="reference",
            version_tag="v2",
            section_title="fetchUser v2",
            content="fetchUser returns user profile.",
            api_names=["fetchUser"],
            change_type="current",
        )
        parsed = ParsedQuery("fetchUser", "lookup", ["fetchUser"], ["v3"])
        vc = VersionContext(mode="explicit", explicit_versions=["v3"], to_version="v3")
        alerts = detect_conflicts([deprecated_chunk, current_fetch], parsed, vc)
        deprecation = [a for a in alerts if a.conflict_type == "version_deprecation_conflict"]
        assert len(deprecation) > 0

    def test_stale_doc_conflict_detected(self, stale_chunk):
        parsed = ParsedQuery("logging v3", "lookup", ["logging"], ["v3"])
        vc = VersionContext(mode="explicit", explicit_versions=["v3"], to_version="v3")
        alerts = detect_conflicts([stale_chunk], parsed, vc)
        stale = [a for a in alerts if a.conflict_type == "stale_doc_detected"]
        assert len(stale) > 0

    def test_no_conflicts_on_clean_single_chunk(self, auth_chunk_v3):
        parsed = ParsedQuery("authenticate v3", "lookup", ["authenticate"], ["v3"])
        vc = VersionContext(mode="explicit", explicit_versions=["v3"], to_version="v3")
        alerts = detect_conflicts([auth_chunk_v3], parsed, vc)
        blocking = [a for a in alerts if a.severity in ("CRITICAL", "HIGH")]
        assert len(blocking) == 0


# ---------------------------------------------------------------------------
# dedupe_alerts
# ---------------------------------------------------------------------------

class TestDedupeAlerts:
    def test_identical_alerts_deduplicated(self):
        alert = ConflictAlert(
            conflict_type="stale_doc_detected",
            severity="MEDIUM",
            chunk_ids=["c1"],
            description="stale",
        )
        result = dedupe_alerts([alert, alert])
        assert len(result) == 1

    def test_distinct_alerts_kept(self):
        a1 = ConflictAlert("stale_doc_detected", "MEDIUM", ["c1"], "stale")
        a2 = ConflictAlert("version_deprecation_conflict", "HIGH", ["c2"], "deprecated")
        result = dedupe_alerts([a1, a2])
        assert len(result) == 2


# ---------------------------------------------------------------------------
# create_migration_report (verdict logic)
# ---------------------------------------------------------------------------

class TestMigrationReportVerdict:
    def _make_trace(self, chunk):
        from src.devpulse.core.query_mode import RetrievalTrace
        return RetrievalTrace(
            chunk_id=chunk.chunk_id,
            bm25_score=0.5,
            vector_score=0.5,
            rrf_score=1.0,
            rank=1,
            selected=True,
            version_tag=chunk.version_tag,
            doc_type=chunk.doc_type,
        )

    def test_blocked_verdict_when_critical_conflict(self, auth_chunk_v2, auth_chunk_v3):
        parsed = ParsedQuery("migrate authenticate v2 to v3", "migration", ["authenticate"], ["v2", "v3"])
        vc = VersionContext(mode="range", explicit_versions=["v2", "v3"], from_version="v2", to_version="v3")
        chunks = [auth_chunk_v2, auth_chunk_v3]
        traces = [self._make_trace(c) for c in chunks]
        alerts = detect_conflicts(chunks, parsed, vc)
        report = create_migration_report("q1", parsed, vc, chunks, traces, alerts)
        assert report.verdict == "BLOCKED"
        assert report.synthesis_text is None

    def test_safe_verdict_on_fresh_single_version(self, auth_chunk_v3):
        parsed = ParsedQuery("authenticate v3", "lookup", ["authenticate"], ["v3"])
        vc = VersionContext(mode="explicit", explicit_versions=["v3"], to_version="v3")
        chunks = [auth_chunk_v3]
        traces = [self._make_trace(auth_chunk_v3)]
        alerts = detect_conflicts(chunks, parsed, vc)
        report = create_migration_report("q2", parsed, vc, chunks, traces, alerts)
        assert report.verdict == "SAFE"
        assert report.synthesis_text is not None
        assert report.grounding_rate == 1.0

    def test_risky_verdict_on_stale_source(self, stale_chunk):
        parsed = ParsedQuery("logging v3", "lookup", ["logging"], ["v3"])
        vc = VersionContext(mode="explicit", explicit_versions=["v3"], to_version="v3")
        chunks = [stale_chunk]
        traces = [self._make_trace(stale_chunk)]
        alerts = detect_conflicts(chunks, parsed, vc)
        report = create_migration_report("q3", parsed, vc, chunks, traces, alerts)
        assert report.verdict in ("RISKY", "BLOCKED")


# ---------------------------------------------------------------------------
# run_query (end-to-end smoke tests)
# ---------------------------------------------------------------------------

class TestRunQuery:
    def test_end_to_end_migration_query_returns_result(self):
        result = run_query("How do I migrate authenticate from v2 to v3?")
        assert result.query_id.startswith("query_")
        assert result.route_taken == "MIGRATION"
        assert len(result.retrieved_chunks) > 0

    def test_end_to_end_lookup_query_no_crash(self):
        result = run_query("How does rateLimit work in v3?")
        assert result.query_id.startswith("query_")
        assert result.migration_report is not None

    def test_blocked_query_has_fallback_event(self):
        # Migration with critical conflict should generate a fallback event
        result = run_query("How do I migrate authenticate from v2 to v3?")
        if result.migration_report.verdict == "BLOCKED":
            assert len(result.fallback_events) > 0
            assert result.fallback_events[0]["outcome"] == "synthesis_suppressed"

    def test_conflict_flag_set_when_alerts_exist(self):
        result = run_query("How do I migrate authenticate from v2 to v3?")
        assert result.conflict_flag == (len(result.conflict_alerts) > 0)

    def test_custom_corpus_used_when_provided(self, corpus):
        result = run_query("authenticate", corpus=corpus)
        assert len(result.retrieved_chunks) > 0


# ---------------------------------------------------------------------------
# semver utilities
# ---------------------------------------------------------------------------

class TestParseSemver:
    def test_v2_returns_two(self):
        from src.devpulse.core.query_mode import parse_semver
        assert parse_semver("v2") == (2,)

    def test_v3_1_returns_tuple(self):
        from src.devpulse.core.query_mode import parse_semver
        assert parse_semver("v3.1") == (3, 1)

    def test_v2_1_0_returns_three_parts(self):
        from src.devpulse.core.query_mode import parse_semver
        assert parse_semver("v2.1.0") == (2, 1, 0)

    def test_uppercase_V_stripped(self):
        from src.devpulse.core.query_mode import parse_semver
        assert parse_semver("V4") == (4,)

    def test_empty_string_returns_zero(self):
        from src.devpulse.core.query_mode import parse_semver
        assert parse_semver("") == (0,)


class TestSemverLt:
    def test_v2_lt_v3(self):
        from src.devpulse.core.query_mode import semver_lt
        assert semver_lt("v2", "v3") is True

    def test_v3_not_lt_v2(self):
        from src.devpulse.core.query_mode import semver_lt
        assert semver_lt("v3", "v2") is False

    def test_equal_versions_not_lt(self):
        from src.devpulse.core.query_mode import semver_lt
        assert semver_lt("v3", "v3") is False

    def test_minor_version_ordering(self):
        from src.devpulse.core.query_mode import semver_lt
        assert semver_lt("v3.0", "v3.1") is True


class TestBuildApiVersionGraph:
    def test_returns_sorted_versions_per_api(self, corpus):
        from src.devpulse.core.query_mode import build_api_version_graph
        graph = build_api_version_graph(corpus)
        assert "authenticate" in graph
        versions = graph["authenticate"]
        # v2 should come before v3 in sorted order
        assert versions.index("v2") < versions.index("v3")

    def test_single_version_api_returns_one_entry(self, corpus):
        from src.devpulse.core.query_mode import build_api_version_graph
        graph = build_api_version_graph(corpus)
        # rateLimit has both v2 and v3 in demo corpus
        assert "rateLimit" in graph


class TestVersionOrderingViolation:
    def test_normal_deprecation_does_not_trigger_ordering_violation(self, auth_chunk_v2, deprecated_chunk):
        """fetchUser deprecated in v3 (newer), current in v2 (older) — expected ordering."""
        from src.devpulse.core.query_mode import detect_conflicts
        current_fetch_v2 = Chunk(
            chunk_id="c_v2_fetch_cur", source_url="docs/ref/v2/fetchUser",
            doc_type="reference", version_tag="v2", section_title="fetchUser v2",
            content="fetchUser returns profile.", api_names=["fetchUser"], change_type="current",
        )
        parsed = ParsedQuery("fetchUser v2 to v3", "migration", ["fetchUser"], ["v2", "v3"])
        vc = VersionContext(mode="range", explicit_versions=["v2", "v3"])
        alerts = detect_conflicts([current_fetch_v2, deprecated_chunk], parsed, vc)
        ordering_violations = [a for a in alerts if a.conflict_type == "version_ordering_violation"]
        # Deprecated in v3 (newer) + current in v2 (older) = correct ordering, no violation
        assert len(ordering_violations) == 0

    def test_backwards_deprecation_triggers_ordering_violation(self):
        """Deprecated in v2 (older) while current in v3 (newer) = anomaly."""
        from src.devpulse.core.query_mode import detect_conflicts
        backwards_deprecated = Chunk(
            chunk_id="c_v2_dep", source_url="docs/ref/v2/foo",
            doc_type="changelog", version_tag="v2", section_title="foo deprecated in v2",
            content="foo is deprecated.", api_names=["foo"], change_type="deprecated",
            has_deprecation=True,
        )
        current_v3 = Chunk(
            chunk_id="c_v3_cur", source_url="docs/ref/v3/foo",
            doc_type="reference", version_tag="v3", section_title="foo v3 current",
            content="foo is the current API.", api_names=["foo"], change_type="current",
        )
        parsed = ParsedQuery("foo", "lookup", ["foo"], [])
        vc = VersionContext(mode="none", explicit_versions=[])
        alerts = detect_conflicts([backwards_deprecated, current_v3], parsed, vc)
        ordering_violations = [a for a in alerts if a.conflict_type == "version_ordering_violation"]
        assert len(ordering_violations) > 0
        assert ordering_violations[0].severity == "CRITICAL"

    def test_semver_distance_calibrates_severity(self):
        """Large version jump (v1→v3) → CRITICAL; same-major → HIGH."""
        from src.devpulse.core.query_mode import detect_conflicts
        v1_chunk = Chunk(
            chunk_id="c_v1", source_url="docs/v1/bar",
            doc_type="reference", version_tag="v1", section_title="bar v1",
            content="bar works like this in v1.", api_names=["bar"], change_type="current",
        )
        v3_chunk = Chunk(
            chunk_id="c_v3", source_url="docs/v3/bar",
            doc_type="migration_guide", version_tag="v3", section_title="bar v3",
            content="bar was rewritten in v3.", api_names=["bar"], change_type="breaking",
        )
        parsed = ParsedQuery("bar v1 to v3", "migration", ["bar"], ["v1", "v3"])
        vc = VersionContext(mode="range", explicit_versions=["v1", "v3"])
        alerts = detect_conflicts([v1_chunk, v3_chunk], parsed, vc)
        same_api = [a for a in alerts if a.conflict_type == "same_api_different_behavior"]
        assert len(same_api) > 0
        assert same_api[0].severity == "CRITICAL"
