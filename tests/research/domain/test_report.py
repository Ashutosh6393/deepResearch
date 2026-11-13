from uuid import uuid4

import pytest

from deepresearch.research.domain.evidence import Evidence
from deepresearch.research.domain.report import (
    ComparisonTable,
    ResearchClaim,
    ResearchReport,
)
from deepresearch.research.domain.source import ExtractionStatus, Source


@pytest.fixture
def valid_source() -> Source:
    content = "This is extracted research content from a reliable source."

    return Source(
        canonical_url="https://example.com/research",
        title="Research Source",
        domain="example.com",
        extracted_content=content,
        content_hash=Source.calculate_content_hash(content),
        extraction_status=ExtractionStatus.SUCCEEDED,
    )

@pytest.fixture
def valid_evidence(valid_source: Source) -> Evidence:
    return Evidence(
        source_id=valid_source.source_id,
        content="The research source supports this particular finding.",
        relevance_score=0.9,
        credibility_score=0.85,
        associated_subquestion_ids=[uuid4()],
    )


@pytest.fixture
def valid_claim(valid_evidence: Evidence) -> ResearchClaim:
    return ResearchClaim(
        statement="The research supports this finding.",
        evidence_ids=[valid_evidence.evidence_id],
        confidence=0.9,
    )


@pytest.fixture
def valid_report(
    valid_source: Source,
    valid_evidence: Evidence,
    valid_claim: ResearchClaim,
) -> ResearchReport:
    return ResearchReport(
        title="Research Report",
        executive_summary="A summary of the research and its main findings.",
        methodology="We reviewed sources and evaluated supporting evidence.",
        key_findings=[valid_claim],
        sources=[valid_source],
        evidence=[valid_evidence],
        conclusion="The available evidence supports the stated conclusion.",
    )


def test_create_valid_research_claim(valid_evidence: Evidence) -> None:
    claim = ResearchClaim(
        statement="  A supported research finding.  ",
        evidence_ids=[valid_evidence.evidence_id],
        confidence=0.9,
        limitations=["  Limited available data.  "],
    )

    assert claim.statement == "A supported research finding."
    assert claim.limitations == ["Limited available data."]


def test_research_claim_rejects_empty_statement(
    valid_evidence: Evidence,
) -> None:
    with pytest.raises(ValueError, match="Claim statement cannot be empty"):
        ResearchClaim(
            statement=" ",
            evidence_ids=[valid_evidence.evidence_id],
            confidence=0.9,
        )


def test_research_claim_requires_evidence() -> None:
    with pytest.raises(ValueError, match="at least one evidence"):
        ResearchClaim(
            statement="A research finding.",
            evidence_ids=[],
            confidence=0.9,
        )


@pytest.mark.parametrize("confidence", [True, "0.9"])
def test_research_claim_rejects_non_numeric_confidence(
    confidence: object,
    valid_evidence: Evidence,
) -> None:
    with pytest.raises(TypeError, match="confidence must be numeric"):
        ResearchClaim(
            statement="A research finding.",
            evidence_ids=[valid_evidence.evidence_id],
            confidence=confidence,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("confidence", [-0.1, 1.1, float("nan"), float("inf")])
def test_research_claim_rejects_invalid_confidence(
    confidence: float,
    valid_evidence: Evidence,
) -> None:
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        ResearchClaim(
            statement="A research finding.",
            evidence_ids=[valid_evidence.evidence_id],
            confidence=confidence,
        )


def test_research_claim_rejects_duplicate_evidence_ids(
    valid_evidence: Evidence,
) -> None:
    with pytest.raises(ValueError, match="must be unique"):
        ResearchClaim(
            statement="A research finding.",
            evidence_ids=[
                valid_evidence.evidence_id,
                valid_evidence.evidence_id,
            ],
            confidence=0.9,
        )


def test_create_valid_comparison_table() -> None:
    table = ComparisonTable(
        title="Technology comparison",
        columns=["Technology", "Performance"],
        rows=[
            ["Python", "Good"],
            ["Go", "Excellent"],
        ],
    )

    assert table.title == "Technology comparison"
    assert len(table.rows) == 2


def test_comparison_table_rejects_empty_columns() -> None:
    with pytest.raises(ValueError, match="at least one column"):
        ComparisonTable(
            title="Comparison",
            columns=[],
            rows=[],
        )


def test_comparison_table_rejects_mismatched_row_width() -> None:
    with pytest.raises(ValueError, match="but the table has 2 columns"):
        ComparisonTable(
            title="Comparison",
            columns=["Name", "Performance"],
            rows=[["Python"]],
        )


def test_comparison_table_rejects_duplicate_columns() -> None:
    with pytest.raises(ValueError, match="column names must be unique"):
        ComparisonTable(
            title="Comparison",
            columns=["Name", "Name"],
            rows=[],
        )


def test_create_valid_research_report(valid_report: ResearchReport) -> None:
    assert valid_report.title == "Research Report"
    assert len(valid_report.sources) == 1
    assert len(valid_report.evidence) == 1
    assert len(valid_report.key_findings) == 1


def test_research_report_rejects_empty_title(
    valid_report: ResearchReport,
) -> None:
    with pytest.raises(ValueError, match="Report title cannot be empty"):
        ResearchReport(
            title=" ",
            executive_summary=valid_report.executive_summary,
            methodology=valid_report.methodology,
            key_findings=valid_report.key_findings,
            sources=valid_report.sources,
            evidence=valid_report.evidence,
            conclusion=valid_report.conclusion,
        )


def test_research_report_requires_findings(
    valid_report: ResearchReport,
) -> None:
    with pytest.raises(ValueError, match="at least one finding"):
        ResearchReport(
            title=valid_report.title,
            executive_summary=valid_report.executive_summary,
            methodology=valid_report.methodology,
            key_findings=[],
            sources=valid_report.sources,
            evidence=valid_report.evidence,
            conclusion=valid_report.conclusion,
        )


def test_research_report_requires_sources(
    valid_report: ResearchReport,
) -> None:
    with pytest.raises(ValueError, match="at least one source"):
        ResearchReport(
            title=valid_report.title,
            executive_summary=valid_report.executive_summary,
            methodology=valid_report.methodology,
            key_findings=valid_report.key_findings,
            sources=[],
            evidence=valid_report.evidence,
            conclusion=valid_report.conclusion,
        )


def test_research_report_requires_evidence(
    valid_report: ResearchReport,
) -> None:
    with pytest.raises(ValueError, match="at least one evidence"):
        ResearchReport(
            title=valid_report.title,
            executive_summary=valid_report.executive_summary,
            methodology=valid_report.methodology,
            key_findings=valid_report.key_findings,
            sources=valid_report.sources,
            evidence=[],
            conclusion=valid_report.conclusion,
        )


def test_research_report_rejects_evidence_without_source(
    valid_source: Source,
    valid_claim: ResearchClaim,
    valid_evidence: Evidence,
) -> None:
    unrelated_source = Source(
        canonical_url="https://another-example.com/article",
        title="Unrelated source",
        domain="another-example.com",
    )

    with pytest.raises(ValueError, match="not included in the report"):
        ResearchReport(
            title="Research Report",
            executive_summary="A summary of the research findings.",
            methodology="Sources were reviewed and analyzed.",
            key_findings=[valid_claim],
            sources=[unrelated_source],
            evidence=[valid_evidence],
            conclusion="The evidence supports the conclusion.",
        )


def test_research_report_rejects_claim_with_missing_evidence(
    valid_source: Source,
    valid_evidence: Evidence,
) -> None:
    claim = ResearchClaim(
        statement="A research finding.",
        evidence_ids=[uuid4()],
        confidence=0.9,
    )

    with pytest.raises(ValueError, match="not included in the report"):
        ResearchReport(
            title="Research Report",
            executive_summary="A summary of the research findings.",
            methodology="Sources were reviewed and analyzed.",
            key_findings=[claim],
            sources=[valid_source],
            evidence=[valid_evidence],
            conclusion="The evidence supports the conclusion.",
        )


def test_research_report_rejects_duplicate_source_ids(
    valid_report: ResearchReport,
) -> None:
    duplicate_source = valid_report.sources[0]

    with pytest.raises(ValueError, match="duplicate sources"):
        ResearchReport(
            title=valid_report.title,
            executive_summary=valid_report.executive_summary,
            methodology=valid_report.methodology,
            key_findings=valid_report.key_findings,
            sources=[duplicate_source, duplicate_source],
            evidence=valid_report.evidence,
            conclusion=valid_report.conclusion,
        )


def test_research_report_rejects_duplicate_evidence_ids(
    valid_report: ResearchReport,
) -> None:
    duplicate_evidence = valid_report.evidence[0]

    with pytest.raises(ValueError, match="duplicate evidence"):
        ResearchReport(
            title=valid_report.title,
            executive_summary=valid_report.executive_summary,
            methodology=valid_report.methodology,
            key_findings=valid_report.key_findings,
            sources=valid_report.sources,
            evidence=[duplicate_evidence, duplicate_evidence],
            conclusion=valid_report.conclusion,
        )


def test_research_report_rejects_invalid_collection_items(
    valid_report: ResearchReport,
) -> None:
    with pytest.raises(TypeError, match="All sources"):
        ResearchReport(
            title=valid_report.title,
            executive_summary=valid_report.executive_summary,
            methodology=valid_report.methodology,
            key_findings=valid_report.key_findings,
            sources=["not-a-source"],  # type: ignore[list-item]
            evidence=valid_report.evidence,
            conclusion=valid_report.conclusion,
        )


def test_research_report_preserves_optional_fields(
    valid_source: Source,
    valid_evidence: Evidence,
    valid_claim: ResearchClaim,
) -> None:
    report = ResearchReport(
        title="Research Report",
        executive_summary="A summary of the research findings.",
        methodology="Sources were reviewed and analyzed.",
        key_findings=[valid_claim],
        sources=[valid_source],
        evidence=[valid_evidence],
        conclusion="The evidence supports the conclusion.",
        comparison_tables=[
            ComparisonTable(
                title="Comparison",
                columns=["Metric", "Value"],
                rows=[["Accuracy", "95%"]],
            )
        ],
        limitations=["The research has a limited sample size."],
    )

    assert len(report.comparison_tables) == 1
    assert len(report.limitations) == 1
