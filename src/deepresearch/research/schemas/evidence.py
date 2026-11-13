from uuid import UUID, uuid4

from pydantic import Field, field_validator

from deepresearch.research.schemas.common import SchemaBase


class Evidence(SchemaBase):
    """A relevant piece of information extracted from a source."""

    evidence_id: UUID = Field(default_factory=uuid4)

    source_id: UUID = Field(
        description="Identifier of the source this evidence originated from."
    )

    content: str = Field(
        min_length=10,
        max_length=10_000,
        description="The extracted passage or information supporting research.",
    )

    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
        description="How relevant this evidence is to its research question.",
    )

    credibility_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Estimated credibility of the evidence's originating source.",
    )

    associated_subquestion_ids: list[UUID] = Field(
        min_length=1,
        max_length=12,
        description="Research subquestions this evidence helps answer.",
    )

    @field_validator("associated_subquestion_ids")
    @classmethod
    def validate_unique_subquestion_ids(
        cls,
        value: list[UUID],
    ) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("Associated subquestion IDs must be unique.")

        return value


class ResearchClaim(SchemaBase):
    """A research finding supported by one or more evidence records."""

    statement: str = Field(
        min_length=10,
        max_length=2_000,
        description="A factual statement derived from collected evidence.",
    )

    evidence_ids: list[UUID] = Field(
        min_length=1,
        max_length=30,
        description="Evidence records supporting this claim.",
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in the claim based on available evidence.",
    )

    limitations: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="Caveats, uncertainties, and limitations of this claim.",
    )

    @field_validator("evidence_ids")
    @classmethod
    def validate_unique_evidence_ids(
        cls,
        value: list[UUID],
    ) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("Evidence IDs must be unique.")

        return value
