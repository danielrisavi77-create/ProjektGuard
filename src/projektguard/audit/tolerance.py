from decimal import Decimal

from pydantic import BaseModel


class TolerancePolicy(BaseModel):
    absolute: Decimal = Decimal("0")
    relative_percent: Decimal = Decimal("0")
