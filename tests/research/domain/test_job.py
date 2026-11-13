from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from deepresearch.research.domain.job import (
    InvalidResearchJobTransition,
    ResearchJob,
    ResearchJobStatus,
)


def test_create_research_job_with_defaults() -> None:
    job = ResearchJob(query="Research LangGraph")

    assert isinstance(job.job_id, UUID)
    assert job.query == "Research LangGraph"
    assert job.status == ResearchJobStatus.QUEUED
    assert job.started_at is None
    assert job.completed_at is None
    assert job.failure_reason is None
    assert job.is_terminal is False
    assert job.created_at.tzinfo is not None


def test_normalize_query_whitespace() -> None:
    job = ResearchJob(query="  Research LangGraph  ")

    assert job.query == "Research LangGraph"


@pytest.mark.parametrize(
    "query",
    [
        "",
        "   ",
    ],
)
def test_reject_empty_query(query: str) -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        ResearchJob(query=query)


def test_reject_query_exceeding_maximum_length() -> None:
    with pytest.raises(ValueError, match="2000 characters"):
        ResearchJob(query="a" * 2_001)


def test_start_queued_job() -> None:
    job = ResearchJob(query="Research LangGraph")

    job.start()

    assert job.status == ResearchJobStatus.RUNNING
    assert job.started_at is not None
    assert job.started_at.tzinfo is not None
    assert job.completed_at is None
    assert job.is_terminal is False


def test_complete_running_job() -> None:
    job = ResearchJob(query="Research LangGraph")
    job.start()

    job.complete()

    assert job.status == ResearchJobStatus.COMPLETED
    assert job.started_at is not None
    assert job.completed_at is not None
    assert job.completed_at >= job.started_at
    assert job.is_terminal is True


def test_fail_running_job() -> None:
    job = ResearchJob(query="Research LangGraph")
    job.start()

    job.fail("LLM provider unavailable")

    assert job.status == ResearchJobStatus.FAILED
    assert job.failure_reason == "LLM provider unavailable"
    assert job.completed_at is not None
    assert job.is_terminal is True


def test_normalize_failure_reason() -> None:
    job = ResearchJob(query="Research LangGraph")
    job.start()

    job.fail("  Provider timeout  ")

    assert job.failure_reason == "Provider timeout"


def test_reject_empty_failure_reason() -> None:
    job = ResearchJob(query="Research LangGraph")
    job.start()

    with pytest.raises(ValueError, match="Failure reason cannot be empty"):
        job.fail("   ")


def test_cancel_queued_job() -> None:
    job = ResearchJob(query="Research LangGraph")

    job.cancel()

    assert job.status == ResearchJobStatus.CANCELLED
    assert job.started_at is None
    assert job.completed_at is not None
    assert job.is_terminal is True


def test_cancel_running_job() -> None:
    job = ResearchJob(query="Research LangGraph")
    job.start()

    job.cancel()

    assert job.status == ResearchJobStatus.CANCELLED
    assert job.started_at is not None
    assert job.completed_at is not None
    assert job.completed_at >= job.started_at
    assert job.is_terminal is True


@pytest.mark.parametrize(
    ("operation", "expected_status"),
    [
        ("start", ResearchJobStatus.RUNNING),
        ("complete", ResearchJobStatus.COMPLETED),
        ("fail", ResearchJobStatus.FAILED),
        ("cancel", ResearchJobStatus.CANCELLED),
    ],
)
def test_reject_invalid_transitions_from_queued_job(
    operation: str,
    expected_status: ResearchJobStatus,
) -> None:
    job = ResearchJob(query="Research LangGraph")

    if operation == "start":
        job.start()
        assert job.status == expected_status
        return

    if operation == "fail":
        with pytest.raises(InvalidResearchJobTransition):
            job.fail("Provider error")
        return

    if operation == "complete":
        with pytest.raises(InvalidResearchJobTransition):
            job.complete()
        return

    job.cancel()
    assert job.status == expected_status


def test_reject_starting_running_job() -> None:
    job = ResearchJob(query="Research LangGraph")
    job.start()

    with pytest.raises(InvalidResearchJobTransition):
        job.start()


def test_reject_completing_job_twice() -> None:
    job = ResearchJob(query="Research LangGraph")
    job.start()
    job.complete()

    with pytest.raises(InvalidResearchJobTransition):
        job.complete()


def test_reject_cancelling_terminal_job() -> None:
    job = ResearchJob(query="Research LangGraph")
    job.start()
    job.complete()

    with pytest.raises(InvalidResearchJobTransition):
        job.cancel()


def test_reject_naive_created_at() -> None:
    with pytest.raises(ValueError, match="created_at must be timezone-aware"):
        ResearchJob(
            query="Research LangGraph",
            created_at=datetime.now(),
        )


def test_reject_naive_started_at() -> None:
    with pytest.raises(ValueError, match="started_at must be timezone-aware"):
        ResearchJob(
            query="Research LangGraph",
            status=ResearchJobStatus.RUNNING,
            started_at=datetime.now(),
        )


def test_reject_naive_completed_at() -> None:
    started_at = datetime.now(UTC)

    with pytest.raises(ValueError, match="completed_at must be timezone-aware"):
        ResearchJob(
            query="Research LangGraph",
            status=ResearchJobStatus.COMPLETED,
            started_at=started_at,
            completed_at=datetime.now(),
        )


def test_reject_completed_job_without_started_at() -> None:
    with pytest.raises(ValueError, match="require execution timestamps"):
        ResearchJob(
            query="Research LangGraph",
            status=ResearchJobStatus.COMPLETED,
            completed_at=datetime.now(UTC),
        )


def test_reject_failed_job_without_failure_reason() -> None:
    now = datetime.now(UTC)

    with pytest.raises(ValueError, match="require a failure reason"):
        ResearchJob(
            query="Research LangGraph",
            status=ResearchJobStatus.FAILED,
            created_at=now,
            started_at=now,
            completed_at=now + timedelta(seconds=1),
        )


def test_reject_completed_at_before_started_at() -> None:
    started_at = datetime.now(UTC)

    with pytest.raises(ValueError, match="earlier than started_at"):
        ResearchJob(
            query="Research LangGraph",
            status=ResearchJobStatus.COMPLETED,
            created_at=started_at - timedelta(seconds=2),
            started_at=started_at,
            completed_at=started_at - timedelta(seconds=1),
        )


def test_reject_completed_at_before_created_at_for_cancelled_job() -> None:
    now = datetime.now(UTC)

    with pytest.raises(ValueError, match="earlier than created_at"):
        ResearchJob(
            query="Research LangGraph",
            status=ResearchJobStatus.CANCELLED,
            created_at=now,
            completed_at=now - timedelta(seconds=1),
        )
