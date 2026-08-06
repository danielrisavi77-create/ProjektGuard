from decimal import Decimal

from pydantic import BaseModel

from projektguard.audit.tolerance import TolerancePolicy


class Difference(BaseModel):
    absolute: Decimal
    relative_percent: Decimal
    within_tolerance: bool


def compare_amounts(actual: Decimal, expected: Decimal, policy: TolerancePolicy) -> Difference:
    absolute = abs(actual - expected)
    relative_percent = Decimal("0") if expected == 0 else (absolute / abs(expected)) * Decimal("100")
    within = absolute <= policy.absolute or relative_percent <= policy.relative_percent
    return Difference(
        absolute=absolute,
        relative_percent=relative_percent,
        within_tolerance=within,
    )
