
from uuid import uuid4

import pytest

from deepresearch.research.domain.plan import (
    ExpectedSourceType,
    ResearchPlan,
    ResearchPriority,
    ResearchSearchQuery,
    ResearchSubQuestion,
)


def make_valid_plan() -> ResearchPlan:
    question = ResearchSubQuestion(
        question="What are current AI research trends?"
    )

    return ResearchPlan(
        objective="Understand the current state of AI research.",
        sub_questions=[question],
        search_queries=[
            ResearchSearchQuery(
                query="current AI research trends",
                sub_question_ids=[question.id],
            )
        ],
        expected_source_types=[ExpectedSourceType.ACADEMIC],
    )


def test_create_valid_research_plan() -> None:
    plan = make_valid_plan()

    assert plan.objective == "Understand the current state of AI research."
    assert len(plan.sub_questions) == 1
    assert len(plan.search_queries) == 1
    assert plan.priority == ResearchPriority.MEDIUM


def test_normalize_objective() -> None:
    plan = make_valid_plan()
    plan.objective = "  Understand AI research trends.  "

    # Assignment does not trigger __post_init__.
    # Construct a new plan to test normalization.
    normalized = ResearchPlan(
        objective=plan.objective,
        sub_questions=plan.sub_questions,
        search_queries=plan.search_queries,
        expected_source_types=plan.expected_source_types,
    )

    assert normalized.objective == "Understand AI research trends."


@pytest.mark.parametrize("objective", ["", "   ", "Too short"])
def test_reject_invalid_objective(objective: str) -> None:
    plan = make_valid_plan()

    with pytest.raises(ValueError, match="at least 10 characters"):
        ResearchPlan(
            objective=objective,
            sub_questions=plan.sub_questions,
            search_queries=plan.search_queries,
            expected_source_types=plan.expected_source_types,
        )


def test_reject_objective_exceeding_maximum_length() -> None:
    plan = make_valid_plan()

    with pytest.raises(ValueError, match="2000 characters"):
        ResearchPlan(
            objective="A" * 2_001,
            sub_questions=plan.sub_questions,
            search_queries=plan.search_queries,
            expected_source_types=plan.expected_source_types,
        )


def test_reject_empty_subquestions() -> None:
    plan = make_valid_plan()

    with pytest.raises(ValueError, match="between 1 and 12 subquestions"):
        ResearchPlan(
            objective=plan.objective,
            sub_questions=[],
            search_queries=plan.search_queries,
            expected_source_types=plan.expected_source_types,
        )


def test_reject_more_than_twelve_subquestions() -> None:
    questions = [
        ResearchSubQuestion(
            question=f"What is AI research topic number {index}?"
        )
        for index in range(13)
    ]

    query = ResearchSearchQuery(
        query="AI research topics",
        sub_question_ids=[questions[0].id],
    )

    with pytest.raises(ValueError, match="between 1 and 12 subquestions"):
        ResearchPlan(
            objective="Understand current AI research.",
            sub_questions=questions,
            search_queries=[query],
            expected_source_types=[ExpectedSourceType.ACADEMIC],
        )


def test_reject_empty_search_queries() -> None:
    plan = make_valid_plan()

    with pytest.raises(ValueError, match="between 1 and 20 search queries"):
        ResearchPlan(
            objective=plan.objective,
            sub_questions=plan.sub_questions,
            search_queries=[],
            expected_source_types=plan.expected_source_types,
        )


def test_reject_missing_expected_source_types() -> None:
    plan = make_valid_plan()

    with pytest.raises(ValueError, match="at least one expected source type"):
        ResearchPlan(
            objective=plan.objective,
            sub_questions=plan.sub_questions,
            search_queries=plan.search_queries,
            expected_source_types=[],
        )


def test_reject_duplicate_subquestion_ids() -> None:
    question_id = uuid4()

    questions = [
        ResearchSubQuestion(
            question="What are current AI research trends?",
            id=question_id,
        ),
        ResearchSubQuestion(
            question="What are the challenges in AI research?",
            id=question_id,
        ),
    ]

    query = ResearchSearchQuery(
        query="AI research trends",
        sub_question_ids=[question_id],
    )

    with pytest.raises(ValueError, match="Subquestion IDs must be unique"):
        ResearchPlan(
            objective="Understand current AI research.",
            sub_questions=questions,
            search_queries=[query],
            expected_source_types=[ExpectedSourceType.ACADEMIC],
        )


def test_reject_duplicate_search_query_ids() -> None:
    question = ResearchSubQuestion(
        question="What are current AI research trends?"
    )
    query_id = uuid4()

    queries = [
        ResearchSearchQuery(
            query="AI research trends",
            sub_question_ids=[question.id],
            id=query_id,
        ),
        ResearchSearchQuery(
            query="AI research developments",
            sub_question_ids=[question.id],
            id=query_id,
        ),
    ]

    with pytest.raises(ValueError, match="Search query IDs must be unique"):
        ResearchPlan(
            objective="Understand current AI research.",
            sub_questions=[question],
            search_queries=queries,
            expected_source_types=[ExpectedSourceType.ACADEMIC],
        )


def test_reject_unknown_subquestion_reference() -> None:
    question = ResearchSubQuestion(
        question="What are current AI research trends?"
    )

    query = ResearchSearchQuery(
        query="AI research trends",
        sub_question_ids=[uuid4()],
    )

    with pytest.raises(
        ValueError,
        match="Search query references unknown subquestion IDs",
    ):
        ResearchPlan(
            objective="Understand current AI research.",
            sub_questions=[question],
            search_queries=[query],
            expected_source_types=[ExpectedSourceType.ACADEMIC],
        )


def test_reject_short_subquestion() -> None:
    with pytest.raises(ValueError, match="at least 5 characters"):
        ResearchSubQuestion(question="AI")


def test_reject_short_search_query() -> None:
    with pytest.raises(ValueError, match="at least 3 characters"):
        ResearchSearchQuery(
            query="AI",
            sub_question_ids=[uuid4()],
        )


def test_reject_search_query_without_subquestion_references() -> None:
    with pytest.raises(
        ValueError,
        match="must reference at least one subquestion",
    ):
        ResearchSearchQuery(
            query="current AI research",
            sub_question_ids=[],
        )


def test_reject_duplicate_references_in_search_query() -> None:
    question_id = uuid4()

    with pytest.raises(
        ValueError,
        match="subquestion IDs must be unique",
    ):
        ResearchSearchQuery(
            query="current AI research",
            sub_question_ids=[question_id, question_id],
        )


def test_support_custom_priority() -> None:
    plan = make_valid_plan()

    plan = ResearchPlan(
        objective=plan.objective,
        sub_questions=plan.sub_questions,
        search_queries=plan.search_queries,
        expected_source_types=plan.expected_source_types,
        priority=ResearchPriority.HIGH,
    )

    assert plan.priority == ResearchPriority.HIGH
