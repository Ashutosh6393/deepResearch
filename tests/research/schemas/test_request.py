
from decimal import Decimal

import pytest
from pydantic import ValidationError

from deepresearch.research.schemas.common import (
    OutputFormat,
    ResearchDepth,
)
from deepresearch.research.schemas.request import ResearchRequest


def test_research_request_uses_default_values() -> None:
    request = ResearchRequest(query="Research LangGraph")

    assert request.depth == ResearchDepth.STANDARD
    assert request.output_format == OutputFormat.MARKDOWN
    assert request.max_budget_usd == Decimal("5.00")
    assert request.max_iterations == 3


def test_research_request_strips_query_whitespace() -> None:
    request = ResearchRequest(query="  Research LangGraph  ")

    assert request.query == "Research LangGraph"


def test_research_request_accepts_custom_values() -> None:
    request = ResearchRequest.model_validate(
        {
            "query": "Compare LangGraph and CrewAI",
            "depth": "comprehensive",
            "output_format": "json",
            "max_budget_usd": "12.50",
            "max_iterations": 5,
        }
    )

    assert request.depth == ResearchDepth.COMPREHENSIVE
    assert request.output_format == OutputFormat.JSON
    assert request.max_budget_usd == Decimal("12.50")
    assert request.max_iterations == 5


@pytest.mark.parametrize(
    "payload",
    [
        {"query": ""},
        {"query": "   "},
        {"query": "Research", "max_iterations": 0},
        {"query": "Research", "max_iterations": 6},
        {"query": "Research", "max_budget_usd": 0},
        {"query": "Research", "max_budget_usd": 1001},
        {"query": "Research", "max_budget_usd": "1.234"},
        {"query": "Research", "depth": "invalid"},
        {"query": "Research", "output_format": "xml"},
        {"query": "Research", "unexpected_field": "value"},
    ],
)
def test_research_request_rejects_invalid_values(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        ResearchRequest.model_validate(payload)


def test_research_request_rejects_query_longer_than_limit() -> None:
    with pytest.raises(ValidationError):
        ResearchRequest(query="a" * 2001)
