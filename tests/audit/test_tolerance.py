from decimal import Decimal

from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.money import compare_amounts


def test_four_kuna_difference_is_immaterial_under_absolute_tolerance():
    result = compare_amounts(
        actual=Decimal("55004"),
        expected=Decimal("55000"),
        policy=TolerancePolicy(absolute=Decimal("10"), relative_percent=Decimal("0.1")),
    )
    assert result.within_tolerance is True
    assert result.absolute == Decimal("4")


def test_material_relative_difference_is_detected():
    result = compare_amounts(
        actual=Decimal("82350"),
        expected=Decimal("79500"),
        policy=TolerancePolicy(absolute=Decimal("10"), relative_percent=Decimal("0.1")),
    )
    assert result.within_tolerance is False
    assert result.relative_percent.quantize(Decimal("0.01")) == Decimal("3.58")
