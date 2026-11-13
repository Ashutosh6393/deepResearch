from uuid import uuid4

import pytest

from deepresearch.research.domain.evidence import Evidence


@pytest.fixture
def valid_evidence() -> Evidence:
    return Evidence(
        source_id=uuid4(),
        content="Retrieval quality directly impacts the accuracy of RAG systems.",
        relevance_score=0.95,
        credibility_score=0.90,
        associated_subquestion_ids=[uuid4(), uuid4()],
    )


def test_create_valid_evidence(valid_evidence: Evidence) -> None:
    assert valid_evidence.source_id is not None
    assert valid_evidence.evidence_id is not None
    assert len(valid_evidence.associated_subquestion_ids) == 2
    assert valid_evidence.relevance_score == 0.95
    assert valid_evidence.credibility_score == 0.90


def test_generate_evidence_id_automatically() -> None:
    evidence = Evidence(
        source_id=uuid4(),
        content="This is a valid piece of research evidence.",
        relevance_score=0.8,
        credibility_score=0.9,
        associated_subquestion_ids=[uuid4()],
    )

    assert evidence.evidence_id is not None


def test_accept_explicit_evidence_id() -> None:
    evidence_id = uuid4()

    evidence = Evidence(
        evidence_id=evidence_id,
        source_id=uuid4(),
        content="This is a valid piece of research evidence.",
        relevance_score=0.8,
        credibility_score=0.9,
        associated_subquestion_ids=[uuid4()],
    )

    assert evidence.evidence_id == evidence_id


def test_normalize_content(valid_evidence: Evidence) -> None:
    evidence = Evidence(
        source_id=valid_evidence.source_id,
        content="  This is valid research evidence.  ",
        relevance_score=0.8,
        credibility_score=0.9,
        associated_subquestion_ids=[uuid4()],
    )

    assert evidence.content == "This is valid research evidence."


@pytest.mark.parametrize("content", ["", "   ", "Short"])
def test_reject_invalid_content(content: str) -> None:
    with pytest.raises(ValueError, match="at least 10 characters"):
        Evidence(
            source_id=uuid4(),
            content=content,
            relevance_score=0.8,
            credibility_score=0.9,
            associated_subquestion_ids=[uuid4()],
        )


def test_reject_content_exceeding_maximum_length() -> None:
    with pytest.raises(ValueError, match="10000 characters"):
        Evidence(
            source_id=uuid4(),
            content="A" * 10_001,
            relevance_score=0.8,
            credibility_score=0.9,
            associated_subquestion_ids=[uuid4()],
        )


@pytest.mark.parametrize(
    "score",
    [-0.1, 1.1, float("nan"), float("inf"), float("-inf")],
)
def test_reject_invalid_relevance_score(score: float) -> None:
    with pytest.raises(ValueError, match="relevance_score"):
        Evidence(
            source_id=uuid4(),
            content="This is valid research evidence.",
            relevance_score=score,
            credibility_score=0.9,
            associated_subquestion_ids=[uuid4()],
        )


@pytest.mark.parametrize(
    "score",
    [-0.1, 1.1, float("nan"), float("inf"), float("-inf")],
)
def test_reject_invalid_credibility_score(score: float) -> None:
    with pytest.raises(ValueError, match="credibility_score"):
        Evidence(
            source_id=uuid4(),
            content="This is valid research evidence.",
            relevance_score=0.9,
            credibility_score=score,
            associated_subquestion_ids=[uuid4()],
        )


@pytest.mark.parametrize("score", [0.0, 0.5, 1.0])
def test_accept_valid_scores(score: float) -> None:
    evidence = Evidence(
        source_id=uuid4(),
        content="This is valid research evidence.",
        relevance_score=score,
        credibility_score=score,
        associated_subquestion_ids=[uuid4()],
    )

    assert evidence.relevance_score == score
    assert evidence.credibility_score == score


@pytest.mark.parametrize("score", [True, False])
def test_reject_boolean_scores(score: bool) -> None:
    with pytest.raises(TypeError, match="numeric value"):
        Evidence(
            source_id=uuid4(),
            content="This is valid research evidence.",
            relevance_score=score,
            credibility_score=0.9,
            associated_subquestion_ids=[uuid4()],
        )


def test_reject_missing_subquestion_references() -> None:
    with pytest.raises(ValueError, match="between 1 and 12"):
        Evidence(
            source_id=uuid4(),
            content="This is valid research evidence.",
            relevance_score=0.8,
            credibility_score=0.9,
            associated_subquestion_ids=[],
        )


def test_reject_more_than_twelve_subquestion_references() -> None:
    with pytest.raises(ValueError, match="between 1 and 12"):
        Evidence(
            source_id=uuid4(),
            content="This is valid research evidence.",
            relevance_score=0.8,
            credibility_score=0.9,
            associated_subquestion_ids=[uuid4() for _ in range(13)],
        )


def test_reject_duplicate_subquestion_references() -> None:
    question_id = uuid4()

    with pytest.raises(ValueError, match="must be unique"):
        Evidence(
            source_id=uuid4(),
            content="This is valid research evidence.",
            relevance_score=0.8,
            credibility_score=0.9,
            associated_subquestion_ids=[
                question_id,
                question_id,
            ],
        )


def test_reject_invalid_subquestion_identifier() -> None:
    with pytest.raises(ValueError, match="valid UUIDs"):
        Evidence(
            source_id=uuid4(),
            content="This is valid research evidence.",
            relevance_score=0.8,
            credibility_score=0.9,
            associated_subquestion_ids=["not-a-uuid"],  # type: ignore[list-item]
        )


def test_reject_invalid_source_identifier() -> None:
    with pytest.raises(TypeError, match="Source ID must be a UUID"):
        Evidence(
            source_id="not-a-uuid",  # type: ignore[arg-type]
            content="This is valid research evidence.",
            relevance_score=0.8,
            credibility_score=0.9,
            associated_subquestion_ids=[uuid4()],
        )


def test_reject_invalid_evidence_identifier() -> None:
    with pytest.raises(TypeError, match="Evidence ID must be a UUID"):
        Evidence(
            evidence_id="not-a-uuid",  # type: ignore[arg-type]
            source_id=uuid4(),
            content="This is valid research evidence.",
            relevance_score=0.8,
            credibility_score=0.9,
            associated_subquestion_ids=[uuid4()],
        )


def test_copy_associated_subquestion_list() -> None:
    question_ids = [uuid4()]

    evidence = Evidence(
        source_id=uuid4(),
        content="This is valid research evidence.",
        relevance_score=0.8,
        credibility_score=0.9,
        associated_subquestion_ids=question_ids,
    )

    question_ids.append(uuid4())

    assert len(evidence.associated_subquestion_ids) == 1
