from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4


class ResearchPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ExpectedSourceType(StrEnum):
    PRIMARY = "primary"
    ACADEMIC = "academic"
    OFFICIAL = "official"
    NEWS = "news"
    TECHNICAL = "technical"
    GENERAL = "general"


@dataclass(slots=True)
class ResearchSubQuestion:
    """A focused question that contributes to the research objective."""

    question: str
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.question = self.question.strip()

        if len(self.question) < 5:
            raise ValueError("Subquestion must contain at least 5 characters.")

        if len(self.question) > 1_000:
            raise ValueError("Subquestion cannot exceed 1000 characters.")


@dataclass(slots=True)
class ResearchSearchQuery:
    """A search query associated with one or more research subquestions."""

    query: str
    sub_question_ids: list[UUID]
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.query = self.query.strip()

        if len(self.query) < 3:
            raise ValueError("Search query must contain at least 3 characters.")

        if len(self.query) > 500:
            raise ValueError("Search query cannot exceed 500 characters.")

        if not self.sub_question_ids:
            raise ValueError("A search query must reference at least one subquestion.")

        if len(self.sub_question_ids) != len(set(self.sub_question_ids)):
            raise ValueError("Search query subquestion IDs must be unique.")


@dataclass(slots=True)
class ResearchPlan:
    """Domain entity representing the execution plan for a research job."""

    objective: str
    sub_questions: list[ResearchSubQuestion]
    search_queries: list[ResearchSearchQuery]
    expected_source_types: list[ExpectedSourceType]
    priority: ResearchPriority = ResearchPriority.MEDIUM

    def __post_init__(self) -> None:
        self.objective = self.objective.strip()

        if len(self.objective) < 10:
            raise ValueError("Research objective must contain at least 10 characters.")

        if len(self.objective) > 2_000:
            raise ValueError("Research objective cannot exceed 2000 characters.")

        if not 1 <= len(self.sub_questions) <= 12:
            raise ValueError(
                "A research plan must contain between 1 and 12 subquestions."
            )

        if not 1 <= len(self.search_queries) <= 20:
            raise ValueError(
                "A research plan must contain between 1 and 20 search queries."
            )

        if not self.expected_source_types:
            raise ValueError(
                "A research plan must specify at least one expected source type."
            )

        self._validate_unique_identifiers()
        self._validate_search_query_references()

    def _validate_unique_identifiers(self) -> None:
        sub_question_ids = [item.id for item in self.sub_questions]
        search_query_ids = [item.id for item in self.search_queries]

        if len(sub_question_ids) != len(set(sub_question_ids)):
            raise ValueError("Subquestion IDs must be unique within a research plan.")

        if len(search_query_ids) != len(set(search_query_ids)):
            raise ValueError("Search query IDs must be unique within a research plan.")

    def _validate_search_query_references(self) -> None:
        known_sub_question_ids = {item.id for item in self.sub_questions}

        for search_query in self.search_queries:
            unknown_ids = set(search_query.sub_question_ids) - known_sub_question_ids

            if unknown_ids:
                raise ValueError(
                    "Search query references unknown subquestion IDs: "
                    f"{sorted(str(item) for item in unknown_ids)}"
                )
