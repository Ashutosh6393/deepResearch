
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class SchemaBase(BaseModel):
    """Base class for application-level Pydantic schemas."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class ResearchDepth(StrEnum):
    """Controls the breadth and depth of a research execution."""

    QUICK = "quick"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


class OutputFormat(StrEnum):
    """Supported research report formats."""

    MARKDOWN = "markdown"
    JSON = "json"
