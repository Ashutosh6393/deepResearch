from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass
class LLMUsage:
    """Token and cost usage for a single LLM invocation."""

    execution_id: UUID
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: Decimal | None = None
    usage_id: UUID = field(default_factory=uuid4)
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self._validate_ids()
        self._normalize_identifiers()
        self._validate_token_counts()
        self._validate_cost()
        self._validate_timestamp()

    def _validate_ids(self) -> None:
        if not isinstance(self.execution_id, UUID):
            raise TypeError("execution_id must be a UUID.")

        if not isinstance(self.usage_id, UUID):
            raise TypeError("usage_id must be a UUID.")

    def _normalize_identifiers(self) -> None:
        if not isinstance(self.provider, str):
            raise TypeError("provider must be a string.")

        if not isinstance(self.model, str):
            raise TypeError("model must be a string.")

        self.provider = self.provider.strip()
        self.model = self.model.strip()

        if not self.provider:
            raise ValueError("provider cannot be empty.")

        if len(self.provider) > 100:
            raise ValueError("provider cannot exceed 100 characters.")

        if not self.model:
            raise ValueError("model cannot be empty.")

        if len(self.model) > 200:
            raise ValueError("model cannot exceed 200 characters.")

    def _validate_token_counts(self) -> None:
        for field_name, value in (
            ("input_tokens", self.input_tokens),
            ("output_tokens", self.output_tokens),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field_name} must be an integer.")

            if value < 0:
                raise ValueError(f"{field_name} cannot be negative.")

    def _validate_cost(self) -> None:
        cost = self.estimated_cost_usd

        if cost is None:
            return

        if not isinstance(cost, Decimal):
            raise TypeError("estimated_cost_usd must be a Decimal or None.")

        if not cost.is_finite():
            raise ValueError("estimated_cost_usd must be finite.")

        if cost < Decimal(0):
            raise ValueError("estimated_cost_usd cannot be negative.")

    def _validate_timestamp(self) -> None:
        if not isinstance(self.recorded_at, datetime):
            raise TypeError("recorded_at must be a datetime.")

        if self.recorded_at.tzinfo is None or self.recorded_at.utcoffset() is None:
            raise ValueError("recorded_at must be timezone-aware.")

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def has_known_cost(self) -> bool:
        return self.estimated_cost_usd is not None
