from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import Field, HttpUrl, field_validator, model_validator

from deepresearch.research.schemas.common import SchemaBase


class ExtractionStatus(StrEnum):
    """Status of source content extraction."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PARTIAL = "partial"


class SearchResult(SchemaBase):
    """A result returned by an external search provider."""

    id: UUID = Field(default_factory=uuid4)

    title: str = Field(
        min_length=1,
        max_length=1_000,
    )

    url: HttpUrl

    snippet: str = Field(
        default="",
        max_length=5_000,
    )

    provider: str = Field(
        min_length=1,
        max_length=100,
    )

    published_at: datetime | None = None

    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    @field_validator("published_at", "retrieved_at")
    @classmethod
    def validate_timezone_aware_datetime(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Datetime must be timezone-aware.")

        return value


class Source(SchemaBase):
    """A discovered source and its extracted content."""

    source_id: UUID = Field(default_factory=uuid4)

    canonical_url: HttpUrl

    title: str = Field(
        min_length=1,
        max_length=1_000,
    )

    domain: str = Field(
        min_length=1,
        max_length=253,
    )

    extracted_content: str | None = Field(
        default=None,
        max_length=2_000_000,
    )

    content_hash: str | None = Field(
        default=None,
        pattern=r"^[a-f0-9]{64}$",
        description="SHA-256 hash of the extracted content.",
    )

    publication_date: datetime | None = None

    retrieval_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    extraction_status: ExtractionStatus = ExtractionStatus.PENDING

    @field_validator("domain")
    @classmethod
    def normalize_domain(cls, value: str) -> str:
        return value.strip().lower().rstrip(".")

    @field_validator("publication_date", "retrieval_timestamp")
    @classmethod
    def validate_timezone_aware_datetime(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Datetime must be timezone-aware.")

        return value

    @model_validator(mode="after")
    def validate_source_integrity(self) -> "Source":
        """Validate relationships between URL, domain and extraction data."""

        host = self.canonical_url.host
        if host is None:
            raise ValueError("Canonical URL must include a hostname.")

        hostname = host.lower().rstrip(".")

        if self.domain != hostname:
            raise ValueError("Domain must match the hostname in canonical_url.")

        if self.extraction_status == ExtractionStatus.SUCCEEDED:
            if not self.extracted_content or not self.extracted_content.strip():
                raise ValueError("Successfully extracted sources must contain content.")

            if self.content_hash is None:
                raise ValueError(
                    "Successfully extracted sources must have a content hash."
                )

        if self.content_hash is not None and self.extracted_content is None:
            raise ValueError("Content hash cannot exist without extracted content.")

        return self
