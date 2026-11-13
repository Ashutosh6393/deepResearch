from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from deepresearch.research.schemas.source import (
    ExtractionStatus,
    SearchResult,
    Source,
)


def test_search_result_accepts_valid_data() -> None:
    result = SearchResult.model_validate(
        {
            "title": "PostgreSQL Documentation",
            "url": "https://www.postgresql.org/docs/",
            "snippet": "Official PostgreSQL documentation.",
            "provider": "tavily",
        }
    )

    assert result.title == "PostgreSQL Documentation"
    assert result.provider == "tavily"
    assert result.url.host == "www.postgresql.org"
    assert result.id is not None
    assert result.retrieved_at.tzinfo is not None


def test_search_result_allows_missing_publication_date() -> None:
    result = SearchResult.model_validate(
        {
            "title": "Example article",
            "url": "https://example.com/article",
            "provider": "tavily",
        }
    )

    assert result.published_at is None


def test_search_result_rejects_invalid_url() -> None:
    with pytest.raises(ValidationError):
        SearchResult.model_validate(
            {
                "title": "Invalid result",
                "url": "not-a-valid-url",
                "provider": "tavily",
            }
        )


def test_search_result_rejects_naive_retrieval_timestamp() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        SearchResult.model_validate(
            {
                "title": "Example article",
                "url": "https://example.com/article",
                "provider": "tavily",
                "retrieved_at": datetime(2026, 1, 1),
            }
        )


def test_source_accepts_successful_extraction() -> None:
    content = "PostgreSQL is an open-source relational database."
    content_hash = "a" * 64

    source = Source.model_validate(
        {
            "canonical_url": "https://www.postgresql.org/docs/",
            "title": "PostgreSQL Documentation",
            "domain": "www.postgresql.org",
            "extracted_content": content,
            "content_hash": content_hash,
            "extraction_status": ExtractionStatus.SUCCEEDED,
        }
    )

    assert source.extracted_content == content
    assert source.content_hash == content_hash
    assert source.extraction_status == ExtractionStatus.SUCCEEDED


def test_source_accepts_pending_extraction() -> None:
    source = Source.model_validate(
        {
            "canonical_url": "https://example.com/article",
            "title": "Example article",
            "domain": "example.com",
        }
    )

    assert source.extraction_status == ExtractionStatus.PENDING
    assert source.extracted_content is None
    assert source.content_hash is None


def test_source_accepts_failed_extraction() -> None:
    source = Source.model_validate(
        {
            "canonical_url": "https://example.com/article",
            "title": "Example article",
            "domain": "example.com",
            "extraction_status": ExtractionStatus.FAILED,
        }
    )

    assert source.extraction_status == ExtractionStatus.FAILED


def test_source_rejects_domain_mismatch() -> None:
    with pytest.raises(ValidationError, match="Domain must match"):
        Source.model_validate(
            {
                "canonical_url": "https://example.com/article",
                "title": "Example article",
                "domain": "another.com",
            }
        )


def test_source_rejects_success_without_content() -> None:
    with pytest.raises(ValidationError, match="must contain content"):
        Source.model_validate(
            {
                "canonical_url": "https://example.com/article",
                "title": "Example article",
                "domain": "example.com",
                "extraction_status": ExtractionStatus.SUCCEEDED,
                "extracted_content": "   ",
                "content_hash": "a" * 64,
            }
        )


def test_source_rejects_success_without_hash() -> None:
    with pytest.raises(ValidationError, match="must have a content hash"):
        Source.model_validate(
            {
                "canonical_url": "https://example.com/article",
                "title": "Example article",
                "domain": "example.com",
                "extraction_status": ExtractionStatus.SUCCEEDED,
                "extracted_content": "Some extracted content.",
            }
        )


def test_source_rejects_invalid_hash_format() -> None:
    with pytest.raises(ValidationError):
        Source.model_validate(
            {
                "canonical_url": "https://example.com/article",
                "title": "Example article",
                "domain": "example.com",
                "content_hash": "invalid-hash",
            }
        )


def test_source_rejects_hash_without_content() -> None:
    with pytest.raises(ValidationError, match="without extracted content"):
        Source.model_validate(
            {
                "canonical_url": "https://example.com/article",
                "title": "Example article",
                "domain": "example.com",
                "content_hash": "a" * 64,
            }
        )


def test_source_rejects_naive_retrieval_timestamp() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        Source.model_validate(
            {
                "canonical_url": "https://example.com/article",
                "title": "Example article",
                "domain": "example.com",
                "retrieval_timestamp": datetime(2026, 1, 1),
            }
        )


def test_source_accepts_aware_publication_date() -> None:
    publication_date = datetime(2026, 1, 1, tzinfo=UTC)

    source = Source.model_validate(
        {
            "canonical_url": "https://example.com/article",
            "title": "Example article",
            "domain": "example.com",
            "publication_date": publication_date,
        }
    )

    assert source.publication_date == publication_date
