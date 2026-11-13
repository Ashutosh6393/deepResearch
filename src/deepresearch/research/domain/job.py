from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class ResearchJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InvalidResearchJobTransition(Exception):
    """Raised when a research job undergoes an invalid state transition."""


@dataclass(slots=True)
class ResearchJob:
    """Domain entity representing a research job and its lifecycle."""

    query: str
    job_id: UUID = field(default_factory=uuid4)
    status: ResearchJobStatus = ResearchJobStatus.QUEUED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        self.query = self.query.strip()

        if not self.query:
            raise ValueError("Research query cannot be empty.")

        if len(self.query) > 2_000:
            raise ValueError("Research query cannot exceed 2000 characters.")

        for name, value in (
            ("created_at", self.created_at),
            ("started_at", self.started_at),
            ("completed_at", self.completed_at),
        ):
            if value is not None and (
                value.tzinfo is None or value.utcoffset() is None
            ):
                raise ValueError(f"{name} must be timezone-aware.")

        if self.created_at > (self.started_at or self.created_at):
            raise ValueError("started_at cannot be earlier than created_at.")
        
        if self.completed_at is not None and self.completed_at < self.created_at:
            raise ValueError("completed_at cannot be earlier than created_at.")

        if self.status == ResearchJobStatus.QUEUED:
            if self.started_at is not None or self.completed_at is not None:
                raise ValueError("Queued jobs cannot have execution timestamps.")

        elif self.status == ResearchJobStatus.RUNNING:
            if self.started_at is None or self.completed_at is not None:
                raise ValueError(
                    "Running jobs require started_at and cannot have completed_at."
                )

        elif self.status == ResearchJobStatus.CANCELLED:
            if self.completed_at is None:
                raise ValueError("Cancelled jobs require completed_at.")

            if self.started_at is not None and self.completed_at < self.started_at:
                raise ValueError("completed_at cannot be earlier than started_at.")

        else:
            if self.started_at is None or self.completed_at is None:
                raise ValueError(
                    "Completed and failed jobs require execution timestamps."
                )

            if self.completed_at < self.started_at:
                raise ValueError("completed_at cannot be earlier than started_at.")

        if self.status == ResearchJobStatus.FAILED:
            if not self.failure_reason or not self.failure_reason.strip():
                raise ValueError("Failed jobs require a failure reason.")

        elif self.failure_reason is not None:
            raise ValueError("Only failed jobs can have a failure reason.")

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            ResearchJobStatus.COMPLETED,
            ResearchJobStatus.FAILED,
            ResearchJobStatus.CANCELLED,
        }

    def start(self) -> None:
        self._ensure_status(ResearchJobStatus.QUEUED)

        now = datetime.now(UTC)

        self.status = ResearchJobStatus.RUNNING
        self.started_at = now

    def complete(self) -> None:
        self._ensure_status(ResearchJobStatus.RUNNING)

        self.status = ResearchJobStatus.COMPLETED
        self.completed_at = datetime.now(UTC)

    def fail(self, reason: str) -> None:
        self._ensure_status(ResearchJobStatus.RUNNING)

        normalized_reason = reason.strip()

        if not normalized_reason:
            raise ValueError("Failure reason cannot be empty.")

        self.status = ResearchJobStatus.FAILED
        self.failure_reason = normalized_reason
        self.completed_at = datetime.now(UTC)

    def cancel(self) -> None:
        if self.status not in {
            ResearchJobStatus.QUEUED,
            ResearchJobStatus.RUNNING,
        }:
            raise InvalidResearchJobTransition(
                f"Cannot cancel a job with status '{self.status.value}'."
            )

        self.status = ResearchJobStatus.CANCELLED
        self.completed_at = datetime.now(UTC)

    def _ensure_status(self, expected: ResearchJobStatus) -> None:
        if self.status != expected:
            raise InvalidResearchJobTransition(
                f"Expected job status '{expected.value}', "
                f"but current status is '{self.status.value}'."
            )
