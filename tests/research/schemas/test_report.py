from uuid import uuid4

import pytest
from pydantic import ValidationError

from deepresearch.research.schemas.evidence import Evidence, ResearchClaim
from deepresearch.research.schemas.report import (
    ComparisonTable,
    ResearchReport,
)
from deepresearch.research.schemas.source import (
    ExtractionStatus,
    Source,
)


def create_source() -> Source:
    return Source.model_validate(
        {
            "canonical_url": "https://example.com/article",
            "title": "Example research article",
            "domain": "example.com",
            "extracted_content": "Example extracted research content.",
            "content_hash": "a" * 64,
            "extraction_status": ExtractionStatus.SUCCEEDED,
        }
    )


def create_evidence(source_id) -> Evidence:
    return Evidence(
        source_id=source_id,
        content="Example evidence supporting a research finding.",
        relevance_score=0.95,
        credibility_score=0.90,
        associated_subquestion_ids=[uuid4()],
    )


def create_valid_report() -> ResearchReport:
    source = create_source()
    evidence = create_evidence(source.source_id)

    claim = ResearchClaim(
        statement="The research source supports this finding.",
        evidence_ids=[evidence.evidence_id],
        confidence=0.95,
    )

    return ResearchReport(
        title="Example Research Report",
        executive_summary=(
            "This report presents findings based on collected evidence."
        ),
        methodology="We searched, extracted, and evaluated relevant sources.",
        key_findings=[claim],
        sources=[source],
        evidence=[evidence],
        conclusion="The available evidence supports the research finding.",
    )


def test_research_report_accepts_valid_data() -> None:
    report = create_valid_report()

    assert report.title == "Example Research Report"
    assert len(report.sources) == 1
    assert len(report.evidence) == 1
    assert len(report.key_findings) == 1


def test_research_report_defaults_optional_collections() -> None:
    report = create_valid_report()

    assert report.comparison_tables == []
    assert report.limitations == []


def test_research_report_rejects_evidence_with_unknown_source() -> None:
    report = create_valid_report()

    report.evidence[0].source_id = uuid4()

    with pytest.raises(
        ValidationError,
        match="references a source",
    ):
        report.model_validate(report.model_dump())


def test_research_report_rejects_claim_with_unknown_evidence() -> None:
    report = create_valid_report()

    report.key_findings[0].evidence_ids = [uuid4()]

    with pytest.raises(
        ValidationError,
        match="references evidence",
    ):
        report.model_validate(report.model_dump())


def test_research_report_rejects_duplicate_source_ids() -> None:
    report = create_valid_report()

    report.sources.append(report.sources[0].model_copy())

    with pytest.raises(
        ValidationError,
        match="Source IDs must be unique",
    ):
        ResearchReport.model_validate(report.model_dump())


def test_research_report_rejects_duplicate_evidence_ids() -> None:
    report = create_valid_report()

    report.evidence.append(report.evidence[0].model_copy())

    with pytest.raises(
        ValidationError,
        match="Evidence IDs must be unique",
    ):
        ResearchReport.model_validate(report.model_dump())


def test_comparison_table_accepts_valid_rows() -> None:
    table = ComparisonTable(
        title="Database Comparison",
        columns=["Feature", "PostgreSQL", "MongoDB"],
        rows=[
            ["Database type", "Relational", "Document"],
            ["Schema", "Structured", "Flexible"],
        ],
    )

    assert len(table.columns) == 3
    assert len(table.rows) == 2


def test_comparison_table_rejects_inconsistent_rows() -> None:
    with pytest.raises(
        ValidationError,
        match="expected 3",
    ):
        ComparisonTable(
            title="Database Comparison",
            columns=["Feature", "PostgreSQL", "MongoDB"],
            rows=[
                ["Database type", "Relational"],
            ],
        )


def test_comparison_table_requires_at_least_two_columns() -> None:
    with pytest.raises(ValidationError):
        ComparisonTable(
            title="Database Comparison",
            columns=["Feature"],
            rows=[["Database type"]],
        )


def test_research_report_requires_at_least_one_source() -> None:
    payload = create_valid_report().model_dump()
    payload["sources"] = []

    with pytest.raises(ValidationError):
        ResearchReport.model_validate(payload)
