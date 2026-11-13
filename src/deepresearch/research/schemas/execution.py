from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from deepresearch.research.schemas.common import SchemaBase


class ExecutionStatus(StrEnum):
    """Lifecycle states of a research execution."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionMetadata(SchemaBase):
    """Operational metadata collected during a research execution."""

    execution_id: UUID = Field(default_factory=uuid4)

    started_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    completed_at: datetime | None = None

    iteration_count: int = Field(default=0, ge=0)

    total_tokens: int = Field(default=0, ge=0)

    estimated_cost_usd: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal(0),
        max_digits=12,
        decimal_places=6,
    )

    search_count: int = Field(default=0, ge=0)

    extraction_count: int = Field(default=0, ge=0)

    retry_count: int = Field(default=0, ge=0)

    fallback_count: int = Field(default=0, ge=0)

    model_versions: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of model roles or providers to model identifiers.",
    )

    execution_status: ExecutionStatus = ExecutionStatus.RUNNING

    @field_validator("started_at", "completed_at")
    @classmethod
    def validate_timezone_aware_datetime(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Datetime must be timezone-aware.")

        return value

    @field_validator("model_versions")
    @classmethod
    def validate_model_versions(
        cls,
        value: dict[str, str],
    ) -> dict[str, str]:
        normalized: dict[str, str] = {}

        for role, model_name in value.items():
            normalized_role = role.strip()
            normalized_model = model_name.strip()

            if not normalized_role or not normalized_model:
                raise ValueError("Model roles and model identifiers cannot be empty.")

            normalized[normalized_role] = normalized_model

        return normalized

    @model_validator(mode="after")
    def validate_execution_timestamps(self) -> "ExecutionMetadata":
        """Ensure timestamps are consistent with execution status."""

        if self.execution_status == ExecutionStatus.RUNNING:
            if self.completed_at is not None:
                raise ValueError(
                    "Running executions cannot have a completed_at timestamp."
                )

        else:
            if self.completed_at is None:
                raise ValueError(
                    "Terminal executions must have a completed_at timestamp."
                )

            if self.completed_at < self.started_at:
                raise ValueError("completed_at cannot be earlier than started_at.")

        return self
