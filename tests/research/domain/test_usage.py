from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from deepresearch.research.domain.usage import LLMUsage


@pytest.fixture
def valid_usage() -> LLMUsage:
    return LLMUsage(
        execution_id=uuid4(),
        provider="openai",
        model="gpt-4.1",
        input_tokens=1_000,
        output_tokens=500,
        estimated_cost_usd=Decimal("0.025"),
    )


def test_create_usage(valid_usage: LLMUsage) -> None:
    assert valid_usage.provider == "openai"
    assert valid_usage.model == "gpt-4.1"
    assert valid_usage.input_tokens == 1_000
    assert valid_usage.output_tokens == 500
    assert valid_usage.estimated_cost_usd == Decimal("0.025")


def test_generates_usage_id(valid_usage: LLMUsage) -> None:
    assert valid_usage.usage_id is not None


def test_generates_timezone_aware_timestamp(
    valid_usage: LLMUsage,
) -> None:
    assert valid_usage.recorded_at.tzinfo is not None
    assert valid_usage.recorded_at.utcoffset() is not None


def test_calculates_total_tokens(valid_usage: LLMUsage) -> None:
    assert valid_usage.total_tokens == 1_500


def test_normalizes_provider_and_model() -> None:
    usage = LLMUsage(
        execution_id=uuid4(),
        provider="  openai  ",
        model="  gpt-4.1  ",
        input_tokens=100,
        output_tokens=50,
    )

    assert usage.provider == "openai"
    assert usage.model == "gpt-4.1"


@pytest.mark.parametrize("provider", ["", "   "])
def test_rejects_empty_provider(provider: str) -> None:
    with pytest.raises(ValueError, match="provider cannot be empty"):
        LLMUsage(
            execution_id=uuid4(),
            provider=provider,
            model="gpt-4.1",
            input_tokens=100,
            output_tokens=50,
        )


@pytest.mark.parametrize("model", ["", "   "])
def test_rejects_empty_model(model: str) -> None:
    with pytest.raises(ValueError, match="model cannot be empty"):
        LLMUsage(
            execution_id=uuid4(),
            provider="openai",
            model=model,
            input_tokens=100,
            output_tokens=50,
        )


@pytest.mark.parametrize(
    ("input_tokens", "output_tokens"),
    [
        (-1, 50),
        (100, -1),
    ],
)
def test_rejects_negative_token_counts(
    input_tokens: int,
    output_tokens: int,
) -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        LLMUsage(
            execution_id=uuid4(),
            provider="openai",
            model="gpt-4.1",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("input_tokens", 10.5),
        ("output_tokens", "100"),
        ("input_tokens", True),
    ],
)
def test_rejects_invalid_token_types(
    field_name: str,
    value: object,
) -> None:
    token_counts: dict[str, object] = {
        "input_tokens": 100,
        "output_tokens": 50,
    }
    token_counts[field_name] = value

    with pytest.raises(TypeError, match="must be an integer"):
        LLMUsage(
            execution_id=uuid4(),
            provider="openai",
            model="gpt-4.1",
            **token_counts,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "cost",
    [
        Decimal("-0.01"),
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ],
)
def test_rejects_invalid_cost(cost: Decimal) -> None:
    with pytest.raises(ValueError):
        LLMUsage(
            execution_id=uuid4(),
            provider="openai",
            model="gpt-4.1",
            input_tokens=100,
            output_tokens=50,
            estimated_cost_usd=cost,
        )


def test_rejects_float_cost() -> None:
    with pytest.raises(TypeError, match="must be a Decimal"):
        LLMUsage(
            execution_id=uuid4(),
            provider="openai",
            model="gpt-4.1",
            input_tokens=100,
            output_tokens=50,
            estimated_cost_usd=0.025,  # type: ignore[arg-type]
        )


def test_allows_unknown_cost() -> None:
    usage = LLMUsage(
        execution_id=uuid4(),
        provider="openai",
        model="gpt-4.1",
        input_tokens=100,
        output_tokens=50,
    )

    assert usage.estimated_cost_usd is None
    assert usage.has_known_cost is False


def test_identifies_known_cost(valid_usage: LLMUsage) -> None:
    assert valid_usage.has_known_cost is True


def test_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        LLMUsage(
            execution_id=uuid4(),
            provider="openai",
            model="gpt-4.1",
            input_tokens=100,
            output_tokens=50,
            recorded_at=datetime(2026, 1, 1),
        )


def test_accepts_timezone_aware_timestamp() -> None:
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    usage = LLMUsage(
        execution_id=uuid4(),
        provider="openai",
        model="gpt-4.1",
        input_tokens=100,
        output_tokens=50,
        recorded_at=timestamp,
    )

    assert usage.recorded_at == timestamp


def test_rejects_invalid_execution_id() -> None:
    with pytest.raises(TypeError, match="execution_id must be a UUID"):
        LLMUsage(
            execution_id="invalid",  # type: ignore[arg-type]
            provider="openai",
            model="gpt-4.1",
            input_tokens=100,
            output_tokens=50,
        )
