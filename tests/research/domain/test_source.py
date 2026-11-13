
from datetime import UTC, datetime, timedelta

import pytest

from deepresearch.research.domain.source import (
    ExtractionStatus,
    Source,
)

CONTENT = "This is extracted content from a research source."
CONTENT_HASH = Source.calculate_content_hash(CONTENT)


def make_source(**overrides: object) -> Source:
    data: dict[str, object] = {
        "canonical_url": "https://example.com/article",
        "title": "Example Research Article",
        "domain": "example.com",
    }
    data.update(overrides)
    return Source(**data)  # type: ignore[arg-type]


def test_create_pending_source() -> None:
    source = make_source()

    assert source.title == "Example Research Article"
    assert source.domain == "example.com"
    assert source.extraction_status == ExtractionStatus.PENDING
    assert source.extracted_content is None
    assert source.content_hash is None
    assert source.source_id is not None
    assert source.retrieval_timestamp.tzinfo == UTC


def test_normalize_source_fields() -> None:
    source = make_source(
        title="  Example Article  ",
        domain="  EXAMPLE.COM. ",
    )

    assert source.title == "Example Article"
    assert source.domain == "example.com"


def test_create_successful_source() -> None:
    source = make_source(
        extracted_content=CONTENT,
        content_hash=CONTENT_HASH,
        extraction_status=ExtractionStatus.SUCCEEDED,
    )

    assert source.extracted_content == CONTENT
    assert source.content_hash == CONTENT_HASH
    assert source.extraction_status == ExtractionStatus.SUCCEEDED


def test_create_partially_extracted_source() -> None:
    source = make_source(
        extracted_content=CONTENT,
        content_hash=CONTENT_HASH,
        extraction_status=ExtractionStatus.PARTIAL,
    )

    assert source.extraction_status == ExtractionStatus.PARTIAL
    assert source.extracted_content == CONTENT


def test_create_failed_source() -> None:
    source = make_source(
        extraction_status=ExtractionStatus.FAILED,
    )

    assert source.extraction_status == ExtractionStatus.FAILED
    assert source.extracted_content is None


@pytest.mark.parametrize(
    "url",
    [
        "",
        "example.com/article",
        "ftp://example.com/article",
        "https:///article",
    ],
)
def test_reject_invalid_source_url(url: str) -> None:
    with pytest.raises(ValueError):
        make_source(canonical_url=url)


def test_reject_url_with_credentials() -> None:
    with pytest.raises(ValueError, match="cannot contain credentials"):
        make_source(
            canonical_url="https://user:password@example.com/article",
        )


def test_reject_domain_mismatch() -> None:
    with pytest.raises(ValueError, match="must match the hostname"):
        make_source(domain="another-example.com")


def test_accept_subdomain() -> None:
    source = make_source(
        canonical_url="https://blog.example.com/article",
        domain="blog.example.com",
    )

    assert source.domain == "blog.example.com"


def test_reject_empty_title() -> None:
    with pytest.raises(ValueError, match="title cannot be empty"):
        make_source(title="   ")


def test_reject_title_exceeding_maximum_length() -> None:
    with pytest.raises(ValueError, match="1000 characters"):
        make_source(title="A" * 1_001)


def test_reject_content_without_hash() -> None:
    with pytest.raises(ValueError, match="must have a SHA-256"):
        make_source(
            extracted_content=CONTENT,
            extraction_status=ExtractionStatus.SUCCEEDED,
        )


def test_reject_hash_without_content() -> None:
    with pytest.raises(ValueError, match="cannot exist without extracted content"):
        make_source(content_hash=CONTENT_HASH)


def test_reject_invalid_hash_format() -> None:
    with pytest.raises(ValueError, match="valid lowercase SHA-256"):
        make_source(
            extracted_content=CONTENT,
            content_hash="invalid-hash",
            extraction_status=ExtractionStatus.SUCCEEDED,
        )


def test_reject_hash_with_uppercase_characters() -> None:
    with pytest.raises(ValueError, match="valid lowercase SHA-256"):
        make_source(
            extracted_content=CONTENT,
            content_hash=CONTENT_HASH.upper(),
            extraction_status=ExtractionStatus.SUCCEEDED,
        )


def test_reject_hash_that_does_not_match_content() -> None:
    different_hash = Source.calculate_content_hash("Different content.")

    with pytest.raises(ValueError, match="does not match"):
        make_source(
            extracted_content=CONTENT,
            content_hash=different_hash,
            extraction_status=ExtractionStatus.SUCCEEDED,
        )


def test_reject_empty_extracted_content() -> None:
    empty_content_hash = Source.calculate_content_hash("   ")

    with pytest.raises(ValueError, match="cannot be empty"):
        make_source(
            extracted_content="   ",
            content_hash=empty_content_hash,
            extraction_status=ExtractionStatus.SUCCEEDED,
        )


def test_reject_successful_extraction_without_content() -> None:
    with pytest.raises(ValueError, match="must contain extracted content"):
        make_source(
            extraction_status=ExtractionStatus.SUCCEEDED,
        )


def test_reject_partial_extraction_without_content() -> None:
    with pytest.raises(ValueError, match="must contain extracted content"):
        make_source(
            extraction_status=ExtractionStatus.PARTIAL,
        )


def test_reject_pending_extraction_with_content() -> None:
    with pytest.raises(ValueError, match="cannot contain extracted content"):
        make_source(
            extracted_content=CONTENT,
            content_hash=CONTENT_HASH,
            extraction_status=ExtractionStatus.PENDING,
        )


def test_reject_failed_extraction_with_content() -> None:
    with pytest.raises(ValueError, match="cannot contain extracted content"):
        make_source(
            extracted_content=CONTENT,
            content_hash=CONTENT_HASH,
            extraction_status=ExtractionStatus.FAILED,
        )


@pytest.mark.parametrize(
    "field",
    ["retrieval_timestamp", "publication_date"],
)
def test_reject_naive_datetime(field: str) -> None:
    with pytest.raises(ValueError, match="must be timezone-aware"):
        make_source(**{field: datetime(2026, 1, 1)})


def test_accept_timezone_aware_publication_date() -> None:
    publication_date = datetime(
        2026, 1, 1, tzinfo=UTC
    )

    source = make_source(publication_date=publication_date)

    assert source.publication_date == publication_date


def test_reject_publication_date_after_retrieval() -> None:
    retrieval_timestamp = datetime.now(UTC)
    publication_date = retrieval_timestamp + timedelta(days=1)

    with pytest.raises(
        ValueError,
        match="later than retrieval timestamp",
    ):
        make_source(
            retrieval_timestamp=retrieval_timestamp,
            publication_date=publication_date,
        )


def test_calculate_content_hash() -> None:
    assert Source.calculate_content_hash(CONTENT) == CONTENT_HASH
    assert len(CONTENT_HASH) == 64


def test_reject_content_exceeding_maximum_length() -> None:
    content = "A" * 2_000_001

    with pytest.raises(ValueError, match="maximum allowed length"):
        make_source(
            extracted_content=content,
            content_hash=Source.calculate_content_hash(content),
            extraction_status=ExtractionStatus.SUCCEEDED,
        )
