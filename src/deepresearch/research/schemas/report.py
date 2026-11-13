from pydantic import Field, model_validator

from deepresearch.research.schemas.common import SchemaBase
from deepresearch.research.schemas.evidence import Evidence, ResearchClaim
from deepresearch.research.schemas.source import Source


class ComparisonTable(SchemaBase):
    """Structured comparison of multiple subjects or entities."""

    title: str = Field(
        min_length=3,
        max_length=300,
    )

    columns: list[str] = Field(
        min_length=2,
        max_length=12,
    )

    rows: list[list[str]] = Field(
        min_length=1,
        max_length=100,
    )

    @model_validator(mode="after")
    def validate_row_dimensions(self) -> "ComparisonTable":
        """Ensure every row matches the number of columns."""

        expected_width = len(self.columns)

        for index, row in enumerate(self.rows):
            if len(row) != expected_width:
                raise ValueError(
                    f"Row {index} has {len(row)} cells; expected {expected_width}."
                )

        return self


class ResearchReport(SchemaBase):
    """Complete research report with traceable supporting evidence."""

    title: str = Field(
        min_length=5,
        max_length=500,
    )

    executive_summary: str = Field(
        min_length=20,
        max_length=10_000,
    )

    methodology: str = Field(
        min_length=10,
        max_length=10_000,
    )

    key_findings: list[ResearchClaim] = Field(
        min_length=1,
        max_length=50,
    )

    comparison_tables: list[ComparisonTable] = Field(
        default_factory=list,
        max_length=20,
    )

    limitations: list[str] = Field(
        default_factory=list,
        max_length=30,
    )

    sources: list[Source] = Field(
        min_length=1,
        max_length=100,
    )

    evidence: list[Evidence] = Field(
        min_length=1,
        max_length=500,
    )

    conclusion: str = Field(
        min_length=10,
        max_length=10_000,
    )

    @model_validator(mode="after")
    def validate_report_integrity(self) -> "ResearchReport":
        """Validate all source and evidence references in the report."""

        source_ids = [source.source_id for source in self.sources]
        evidence_ids = [item.evidence_id for item in self.evidence]

        if len(source_ids) != len(set(source_ids)):
            raise ValueError("Source IDs must be unique within the report.")

        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("Evidence IDs must be unique within the report.")

        known_source_ids = set(source_ids)
        known_evidence_ids = set(evidence_ids)

        for item in self.evidence:
            if item.source_id not in known_source_ids:
                raise ValueError(
                    f"Evidence {item.evidence_id} references a source "
                    f"that is not included in the report."
                )

        for claim in self.key_findings:
            unknown_evidence_ids = set(claim.evidence_ids) - known_evidence_ids

            if unknown_evidence_ids:
                raise ValueError(
                    "Research claim references evidence that is not "
                    "included in the report: "
                    f"{sorted(str(item) for item in unknown_evidence_ids)}"
                )

        return self
