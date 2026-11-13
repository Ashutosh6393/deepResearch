from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from deepresearch.research.schemas.execution import (
    ExecutionMetadata,
    ExecutionStatus,
)


def test_execution_metadata_uses_defaults() -> None:
    metadata = ExecutionMetadata()

    assert metadata.execution_status == ExecutionStatus.RUNNING
    assert metadata.iteration_count == 0
    assert metadata.total_tokens == 0
    assert metadata.estimated_cost_usd == Decimal("0.00")
    assert metadata.model_versions == {}
    assert metadata.completed_at is None
    assert metadata.started_at.tzinfo is not None


def test_execution_metadata_accepts_running_execution() -> None:
    metadata = ExecutionMetadata(
        iteration_count=2,
        total_tokens=5_000,
        estimated_cost_usd=Decimal("0.125"),
        search_count=4,
        extraction_count=3,
        retry_count=1,
        fallback_count=0,
        model_versions={
            "planner": "model-a",
            "synthesis": "model-b",
        },
    )

    assert metadata.execution_status == ExecutionStatus.RUNNING
    assert metadata.total_tokens == 5_000
    assert metadata.model_versions["planner"] == "model-a"


@pytest.mark.parametrize(
    "status",
    [
        ExecutionStatus.COMPLETED,
        ExecutionStatus.FAILED,
        ExecutionStatus.CANCELLED,
    ],
)
def test_execution_metadata_accepts_terminal_status(
    status: ExecutionStatus,
) -> None:
    started_at = datetime.now(UTC)

    metadata = ExecutionMetadata(
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=30),
        execution_status=status,
    )

    assert metadata.execution_status == status
    assert metadata.completed_at is not None


@pytest.mark.parametrize(
    "field",
    [
        "iteration_count",
        "total_tokens",
        "search_count",
        "extraction_count",
        "retry_count",
        "fallback_count",
    ],
)
def test_execution_metadata_rejects_negative_counters(
    field: str,
) -> None:
    with pytest.raises(ValidationError):
        ExecutionMetadata.model_validate({field: -1})


def test_execution_metadata_rejects_negative_cost() -> None:
    with pytest.raises(ValidationError):
        ExecutionMetadata(estimated_cost_usd=Decimal("-0.01"))


def test_execution_metadata_rejects_naive_started_at() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        ExecutionMetadata(started_at=datetime(2026, 1, 1))


def test_execution_metadata_rejects_naive_completed_at() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        ExecutionMetadata(
            execution_status=ExecutionStatus.COMPLETED,
            completed_at=datetime(2026, 1, 1),
        )


def test_execution_metadata_rejects_completion_before_start() -> None:
    started_at = datetime(2026, 1, 2, tzinfo=UTC)
    completed_at = datetime(2026, 1, 1, tzinfo=UTC)

    with pytest.raises(ValidationError, match="earlier than started_at"):
        ExecutionMetadata(
            started_at=started_at,
            completed_at=completed_at,
            execution_status=ExecutionStatus.COMPLETED,
        )


def test_running_execution_rejects_completion_timestamp() -> None:
    with pytest.raises(ValidationError, match="cannot have a completed_at"):
        ExecutionMetadata(
            completed_at=datetime.now(UTC),
            execution_status=ExecutionStatus.RUNNING,
        )


def test_terminal_execution_requires_completion_timestamp() -> None:
    with pytest.raises(
        ValidationError,
        match="must have a completed_at",
    ):
        ExecutionMetadata(
            execution_status=ExecutionStatus.COMPLETED,
        )


def test_model_versions_are_normalized() -> None:
    metadata = ExecutionMetadata(
        model_versions={
            " planner ": " model-a ",
        },
    )

    assert metadata.model_versions == {"planner": "model-a"}


def test_model_versions_reject_empty_identifiers() -> None:
    with pytest.raises(ValidationError, match="cannot be empty"):
        ExecutionMetadata(
            model_versions={
                "planner": " ",
            },
        )


def test_execution_metadata_rejects_excessive_decimal_precision() -> None:
    with pytest.raises(ValidationError):
        ExecutionMetadata(
            estimated_cost_usd=Decimal("0.1234567"),
        )
