from uuid import uuid4

import pytest
from pydantic import ValidationError

from deepresearch.research.schemas.evidence import (
    Evidence,
    ResearchClaim,
)


def test_evidence_accepts_valid_data() -> None:
    source_id = uuid4()
    sub_question_id = uuid4()

    evidence = Evidence(
        source_id=source_id,
        content="PostgreSQL uses MVCC to handle concurrent transactions.",
        relevance_score=0.95,
        credibility_score=0.98,
        associated_subquestion_ids=[sub_question_id],
    )

    assert evidence.source_id == source_id
    assert evidence.relevance_score == 0.95
    assert evidence.credibility_score == 0.98
    assert evidence.associated_subquestion_ids == [sub_question_id]


def test_evidence_generates_identifier() -> None:
    evidence = Evidence(
        source_id=uuid4(),
        content="PostgreSQL uses MVCC for transaction management.",
        relevance_score=0.9,
        credibility_score=0.95,
        associated_subquestion_ids=[uuid4()],
    )

    assert evidence.evidence_id is not None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("relevance_score", -0.1),
        ("relevance_score", 1.1),
        ("credibility_score", -0.1),
        ("credibility_score", 1.1),
    ],
)
def test_evidence_rejects_invalid_scores(
    field: str,
    value: float,
) -> None:
    payload: dict[str, object] = {
        "source_id": uuid4(),
        "content": "PostgreSQL uses MVCC for transaction management.",
        "relevance_score": 0.9,
        "credibility_score": 0.9,
        "associated_subquestion_ids": [uuid4()],
    }

    payload[field] = value

    with pytest.raises(ValidationError):
        Evidence.model_validate(payload)


def test_evidence_rejects_empty_content() -> None:
    with pytest.raises(ValidationError):
        Evidence(
            source_id=uuid4(),
            content="",
            relevance_score=0.9,
            credibility_score=0.9,
            associated_subquestion_ids=[uuid4()],
        )


def test_evidence_requires_associated_subquestions() -> None:
    with pytest.raises(ValidationError):
        Evidence(
            source_id=uuid4(),
            content="PostgreSQL uses MVCC for transaction management.",
            relevance_score=0.9,
            credibility_score=0.9,
            associated_subquestion_ids=[],
        )


def test_evidence_rejects_duplicate_subquestion_ids() -> None:
    sub_question_id = uuid4()

    with pytest.raises(
        ValidationError,
        match="Associated subquestion IDs must be unique",
    ):
        Evidence(
            source_id=uuid4(),
            content="PostgreSQL uses MVCC for transaction management.",
            relevance_score=0.9,
            credibility_score=0.9,
            associated_subquestion_ids=[
                sub_question_id,
                sub_question_id,
            ],
        )


def test_research_claim_accepts_valid_data() -> None:
    evidence_id = uuid4()

    claim = ResearchClaim(
        statement="PostgreSQL uses MVCC to support concurrent transactions.",
        evidence_ids=[evidence_id],
        confidence=0.95,
        limitations=["Performance depends on workload characteristics."],
    )

    assert claim.evidence_ids == [evidence_id]
    assert claim.confidence == 0.95
    assert len(claim.limitations) == 1


def test_research_claim_defaults_to_empty_limitations() -> None:
    claim = ResearchClaim(
        statement="PostgreSQL supports concurrent transactions.",
        evidence_ids=[uuid4()],
        confidence=0.9,
    )

    assert claim.limitations == []


def test_research_claim_rejects_missing_evidence() -> None:
    with pytest.raises(ValidationError):
        ResearchClaim(
            statement="PostgreSQL supports concurrent transactions.",
            evidence_ids=[],
            confidence=0.9,
        )


def test_research_claim_rejects_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        ResearchClaim(
            statement="PostgreSQL supports concurrent transactions.",
            evidence_ids=[uuid4()],
            confidence=1.5,
        )


def test_research_claim_rejects_duplicate_evidence_ids() -> None:
    evidence_id = uuid4()

    with pytest.raises(
        ValidationError,
        match="Evidence IDs must be unique",
    ):
        ResearchClaim(
            statement="PostgreSQL supports concurrent transactions.",
            evidence_ids=[evidence_id, evidence_id],
            confidence=0.9,
        )
