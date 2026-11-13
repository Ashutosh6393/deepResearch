from uuid import uuid4

import pytest
from pydantic import ValidationError

from deepresearch.research.schemas.plan import (
    ExpectedSourceType,
    ResearchPlan,
    ResearchPriority,
    ResearchSearchQuery,
    ResearchSubQuestion,
)


def test_research_plan_accepts_valid_data() -> None:
    sub_question = ResearchSubQuestion(
        question="How does PostgreSQL handle concurrent transactions?"
    )

    plan = ResearchPlan(
        objective="Compare database transaction handling.",
        sub_questions=[sub_question],
        search_queries=[
            ResearchSearchQuery(
                query="PostgreSQL concurrency control",
                sub_question_ids=[sub_question.id],
            )
        ],
        priority=ResearchPriority.HIGH,
        expected_source_types=[ExpectedSourceType.TECHNICAL],
    )

    assert plan.priority == ResearchPriority.HIGH
    assert len(plan.sub_questions) == 1
    assert plan.search_queries[0].sub_question_ids == [sub_question.id]


def test_research_plan_uses_default_priority() -> None:
    sub_question = ResearchSubQuestion(
        question="How does PostgreSQL handle transactions?"
    )

    plan = ResearchPlan(
        objective="Understand PostgreSQL transaction handling.",
        sub_questions=[sub_question],
        search_queries=[
            ResearchSearchQuery(
                query="PostgreSQL transaction handling",
                sub_question_ids=[sub_question.id],
            )
        ],
        expected_source_types=[ExpectedSourceType.OFFICIAL],
    )

    assert plan.priority == ResearchPriority.MEDIUM


def test_research_plan_rejects_unknown_subquestion_reference() -> None:
    with pytest.raises(ValidationError, match="unknown subquestion IDs"):
        ResearchPlan(
            objective="Compare database transaction handling.",
            sub_questions=[
                ResearchSubQuestion(question="How does PostgreSQL handle transactions?")
            ],
            search_queries=[
                ResearchSearchQuery(
                    query="PostgreSQL transaction handling",
                    sub_question_ids=[uuid4()],
                )
            ],
            expected_source_types=[ExpectedSourceType.TECHNICAL],
        )


def test_research_plan_rejects_duplicate_subquestion_ids() -> None:
    sub_question_id = uuid4()

    with pytest.raises(ValidationError, match="Subquestion IDs must be unique"):
        ResearchPlan(
            objective="Compare database transaction handling.",
            sub_questions=[
                ResearchSubQuestion(
                    id=sub_question_id,
                    question="How does PostgreSQL handle transactions?",
                ),
                ResearchSubQuestion(
                    id=sub_question_id,
                    question="How does PostgreSQL handle concurrency?",
                ),
            ],
            search_queries=[
                ResearchSearchQuery(
                    query="PostgreSQL transactions",
                    sub_question_ids=[sub_question_id],
                )
            ],
            expected_source_types=[ExpectedSourceType.TECHNICAL],
        )


def test_research_plan_rejects_empty_subquestions() -> None:
    with pytest.raises(ValidationError):
        ResearchPlan(
            objective="Compare database transaction handling.",
            sub_questions=[],
            search_queries=[
                ResearchSearchQuery(
                    query="PostgreSQL transactions",
                    sub_question_ids=[uuid4()],
                )
            ],
            expected_source_types=[ExpectedSourceType.TECHNICAL],
        )


def test_research_search_query_requires_subquestion_reference() -> None:
    with pytest.raises(ValidationError):
        ResearchSearchQuery(
            query="PostgreSQL transactions",
            sub_question_ids=[],
        )
