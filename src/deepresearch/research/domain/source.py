import hashlib
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from urllib.parse import urlsplit
from uuid import UUID, uuid4

MAX_EXTRACTED_CONTENT_LENGTH = 2_000_000
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


class ExtractionStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass(slots=True)
class Source:
    """Domain entity representing a source collected during research."""

    canonical_url: str
    title: str
    domain: str
    source_id: UUID = field(default_factory=uuid4)
    extracted_content: str | None = None
    content_hash: str | None = None
    publication_date: datetime | None = None
    retrieval_timestamp: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    extraction_status: ExtractionStatus = ExtractionStatus.PENDING

    def __post_init__(self) -> None:
        self.canonical_url = self.canonical_url.strip()
        self.title = self.title.strip()
        self.domain = self.domain.strip().lower().rstrip(".")

        self._validate_required_fields()
        self._validate_url()
        self._validate_timestamps()
        self._validate_extracted_content()
        self._validate_extraction_state()

    def _validate_required_fields(self) -> None:
        if not self.canonical_url:
            raise ValueError("Canonical URL cannot be empty.")

        if not self.title:
            raise ValueError("Source title cannot be empty.")

        if len(self.title) > 1_000:
            raise ValueError("Source title cannot exceed 1000 characters.")

        if not self.domain:
            raise ValueError("Source domain cannot be empty.")

    def _validate_url(self) -> None:
        try:
            parsed_url = urlsplit(self.canonical_url)
            hostname = parsed_url.hostname
        except ValueError as exc:
            raise ValueError("Source URL is malformed.") from exc

        if parsed_url.scheme not in {"http", "https"}:
            raise ValueError("Source URL must use HTTP or HTTPS.")

        if not hostname:
            raise ValueError("Source URL must contain a hostname.")

        if parsed_url.username is not None or parsed_url.password is not None:
            raise ValueError("Source URL cannot contain credentials.")

        normalized_hostname = hostname.lower().rstrip(".")

        if self.domain != normalized_hostname:
            raise ValueError("Source domain must match the hostname in canonical_url.")

    def _validate_timestamps(self) -> None:
        timestamps = {
            "retrieval_timestamp": self.retrieval_timestamp,
            "publication_date": self.publication_date,
        }

        for name, value in timestamps.items():
            if value is not None and (
                value.tzinfo is None or value.utcoffset() is None
            ):
                raise ValueError(f"{name} must be timezone-aware.")

        if (
            self.publication_date is not None
            and self.publication_date > self.retrieval_timestamp
        ):
            raise ValueError(
                "Publication date cannot be later than retrieval timestamp."
            )

    def _validate_extracted_content(self) -> None:
        if self.extracted_content is None:
            if self.content_hash is not None:
                raise ValueError("Content hash cannot exist without extracted content.")
            return

        if not self.extracted_content.strip():
            raise ValueError("Extracted content cannot be empty.")

        if len(self.extracted_content) > MAX_EXTRACTED_CONTENT_LENGTH:
            raise ValueError("Extracted content exceeds the maximum allowed length.")

        if self.content_hash is None:
            raise ValueError("Extracted content must have a SHA-256 content hash.")

        if not SHA256_PATTERN.fullmatch(self.content_hash):
            raise ValueError("Content hash must be a valid lowercase SHA-256 hash.")

        expected_hash = self.calculate_content_hash(self.extracted_content)

        if self.content_hash != expected_hash:
            raise ValueError("Content hash does not match the extracted content.")

    def _validate_extraction_state(self) -> None:
        if self.extraction_status in {
            ExtractionStatus.SUCCEEDED,
            ExtractionStatus.PARTIAL,
        }:
            if self.extracted_content is None:
                raise ValueError(
                    f"{self.extraction_status.value.capitalize()} extraction "
                    "must contain extracted content."
                )

        elif self.extracted_content is not None:
            raise ValueError(
                "Pending or failed extraction cannot contain extracted content."
            )

    @staticmethod
    def calculate_content_hash(content: str) -> str:
        """Calculate the SHA-256 hash of UTF-8 encoded content."""

        return hashlib.sha256(content.encode("utf-8")).hexdigest()
