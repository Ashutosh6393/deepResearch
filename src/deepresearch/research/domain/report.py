import math
from dataclasses import dataclass, field
from uuid import UUID

from deepresearch.research.domain.evidence import Evidence
from deepresearch.research.domain.source import Source


@dataclass(slots=True)
class ResearchClaim:
    statement: str
    evidence_ids: list[UUID]
    confidence: float
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.statement = self._normalize_text(self.statement, "Claim statement")
        self.evidence_ids = list(self.evidence_ids)
        self.limitations = [
            self._normalize_text(item, "Claim limitation") for item in self.limitations
        ]

        self._validate_evidence_ids()
        self._validate_confidence()

    @staticmethod
    def _normalize_text(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string.")

        normalized = value.strip()

        if not normalized:
            raise ValueError(f"{field_name} cannot be empty.")

        return normalized

    def _validate_evidence_ids(self) -> None:
        if not self.evidence_ids:
            raise ValueError(
                "A research claim must reference at least one evidence item."
            )

        if any(not isinstance(item, UUID) for item in self.evidence_ids):
            raise TypeError("All evidence IDs must be UUIDs.")

        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("Evidence IDs in a research claim must be unique.")

    def _validate_confidence(self) -> None:
        if isinstance(self.confidence, bool) or not isinstance(
            self.confidence, (int, float)
        ):
            raise TypeError("Claim confidence must be numeric.")

        if not math.isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Claim confidence must be between 0.0 and 1.0.")


@dataclass(slots=True)
class ComparisonTable:
    title: str
    columns: list[str]
    rows: list[list[str]]

    def __post_init__(self) -> None:
        self.title = self._normalize_text(self.title, "Table title")

        if not isinstance(self.columns, list):
            raise TypeError("Table columns must be a list.")

        if not isinstance(self.rows, list):
            raise TypeError("Table rows must be a list.")

        self.columns = [
            self._normalize_text(column, "Column name") for column in self.columns
        ]

        self.rows = [
            [self._normalize_text(cell, "Table cell") for cell in row]
            for row in self.rows
        ]

        self._validate_columns()
        self._validate_rows()

    @staticmethod
    def _normalize_text(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string.")

        normalized = value.strip()

        if not normalized:
            raise ValueError(f"{field_name} cannot be empty.")

        return normalized

    def _validate_columns(self) -> None:
        if not self.columns:
            raise ValueError("A comparison table must have at least one column.")

        if len(self.columns) != len(set(self.columns)):
            raise ValueError("Comparison table column names must be unique.")

    def _validate_rows(self) -> None:
        for index, row in enumerate(self.rows):
            if len(row) != len(self.columns):
                raise ValueError(
                    f"Row {index} has {len(row)} cells, "
                    f"but the table has {len(self.columns)} columns."
                )


@dataclass(slots=True)
class ResearchReport:
    title: str
    executive_summary: str
    methodology: str
    key_findings: list[ResearchClaim]
    sources: list[Source]
    evidence: list[Evidence]
    conclusion: str
    comparison_tables: list[ComparisonTable] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.title = self._normalize_text(self.title, "Report title")
        self.executive_summary = self._normalize_text(
            self.executive_summary, "Executive summary"
        )
        self.methodology = self._normalize_text(self.methodology, "Methodology")
        self.conclusion = self._normalize_text(self.conclusion, "Conclusion")

        self.key_findings = list(self.key_findings)
        self.sources = list(self.sources)
        self.evidence = list(self.evidence)
        self.comparison_tables = list(self.comparison_tables)
        self.limitations = [
            self._normalize_text(item, "Report limitation") for item in self.limitations
        ]

        self._validate_required_collections()
        self._validate_collection_types()
        self._validate_unique_identifiers()
        self._validate_evidence_sources()
        self._validate_claim_evidence()

    @staticmethod
    def _normalize_text(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string.")

        normalized = value.strip()

        if not normalized:
            raise ValueError(f"{field_name} cannot be empty.")

        return normalized

    def _validate_required_collections(self) -> None:
        if not self.key_findings:
            raise ValueError("A research report must contain at least one finding.")

        if not self.sources:
            raise ValueError("A research report must contain at least one source.")

        if not self.evidence:
            raise ValueError(
                "A research report must contain at least one evidence item."
            )

    def _validate_collection_types(self) -> None:
        if any(not isinstance(item, ResearchClaim) for item in self.key_findings):
            raise TypeError("All key findings must be ResearchClaim instances.")

        if any(not isinstance(item, Source) for item in self.sources):
            raise TypeError("All sources must be Source instances.")

        if any(not isinstance(item, Evidence) for item in self.evidence):
            raise TypeError("All evidence items must be Evidence instances.")

        if any(
            not isinstance(item, ComparisonTable)
            for item in self.comparison_tables
        ):
            raise TypeError(
                "All comparison tables must be ComparisonTable instances."
            )
    def _validate_unique_identifiers(self) -> None:
        source_ids = [source.source_id for source in self.sources]
        evidence_ids = [item.evidence_id for item in self.evidence]

        if len(source_ids) != len(set(source_ids)):
            raise ValueError("A research report cannot contain duplicate sources.")

        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("A research report cannot contain duplicate evidence.")

    def _validate_evidence_sources(self) -> None:
        source_ids = {source.source_id for source in self.sources}

        for item in self.evidence:
            if item.source_id not in source_ids:
                raise ValueError(
                    f"Evidence {item.evidence_id} references a source "
                    "that is not included in the report."
                )

    def _validate_claim_evidence(self) -> None:
        evidence_ids = {item.evidence_id for item in self.evidence}

        for claim in self.key_findings:
            missing_ids = set(claim.evidence_ids) - evidence_ids

            if missing_ids:
                raise ValueError(
                    "A research claim references evidence "
                    "that is not included in the report."
                )
