from decimal import Decimal
from typing import Annotated

from pydantic import PlainSerializer


MoneyAmount = Annotated[
    Decimal,
    PlainSerializer(float, return_type=float, when_used="json"),
]
