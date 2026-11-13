import math
from dataclasses import dataclass, field
from uuid import UUID, uuid4

MAX_EVIDENCE_CONTENT_LENGTH = 10_000
MAX_ASSOCIATED_SUBQUESTIONS = 12


@dataclass(slots=True)
class Evidence:
    """A piece of extracted information supporting research subquestions."""

    source_id: UUID
    content: str
    relevance_score: float
    credibility_score: float
    associated_subquestion_ids: list[UUID]

    evidence_id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.content = self.content.strip()
        self.associated_subquestion_ids = list(self.associated_subquestion_ids)

        self._validate_identifiers()
        self._validate_content()
        self._validate_scores()
        self._validate_subquestion_references()

    def _validate_identifiers(self) -> None:
        if not isinstance(self.evidence_id, UUID):
            raise TypeError("Evidence ID must be a UUID.")

        if not isinstance(self.source_id, UUID):
            raise TypeError("Source ID must be a UUID.")

    def _validate_content(self) -> None:
        if len(self.content) < 10:
            raise ValueError("Evidence content must contain at least 10 characters.")

        if len(self.content) > MAX_EVIDENCE_CONTENT_LENGTH:
            raise ValueError("Evidence content cannot exceed 10000 characters.")

    def _validate_scores(self) -> None:
        scores = {
            "relevance_score": self.relevance_score,
            "credibility_score": self.credibility_score,
        }

        for name, score in scores.items():
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                raise TypeError(f"{name} must be a numeric value.")

            if not math.isfinite(score) or not 0.0 <= score <= 1.0:
                raise ValueError(f"{name} must be between 0.0 and 1.0.")

    def _validate_subquestion_references(self) -> None:
        if (
            not 1
            <= len(self.associated_subquestion_ids)
            <= (MAX_ASSOCIATED_SUBQUESTIONS)
        ):
            raise ValueError("Evidence must reference between 1 and 12 subquestions.")

        if any(not isinstance(item, UUID) for item in self.associated_subquestion_ids):
            raise ValueError("All associated subquestion IDs must be valid UUIDs.")

        if len(self.associated_subquestion_ids) != len(
            set(self.associated_subquestion_ids)
        ):
            raise ValueError("Associated subquestion IDs must be unique.")
