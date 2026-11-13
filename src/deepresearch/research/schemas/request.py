
from decimal import Decimal
from typing import Annotated

from pydantic import Field

from deepresearch.research.schemas.common import (
    OutputFormat,
    ResearchDepth,
    SchemaBase,
)

ResearchQuery = Annotated[
    str,
    Field(
        min_length=1,
        max_length=2_000,
        description="The research question or topic.",
    ),
]


class ResearchRequest(SchemaBase):
    """Validated input contract for a research execution."""

    query: ResearchQuery

    depth: ResearchDepth = ResearchDepth.STANDARD

    output_format: OutputFormat = OutputFormat.MARKDOWN

    max_budget_usd: Annotated[
        Decimal,
        Field(
            gt=Decimal(0),
            le=Decimal(1000),
            max_digits=8,
            decimal_places=2,
            description="Maximum permitted research budget in USD.",
        ),
    ] = Decimal("5.00")

    max_iterations: Annotated[
        int,
        Field(
            ge=1,
            le=5,
            description="Maximum number of research iterations.",
        ),
    ] = 3
