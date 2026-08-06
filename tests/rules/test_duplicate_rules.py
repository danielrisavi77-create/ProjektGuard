from datetime import date
from decimal import Decimal

from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import Severity, Verdict
from projektguard.domain.models import AuditContext, Cost, EligibilityPeriod, ProjectFinancials
import projektguard.rules.duplicate


def _base(costs, claimed=None):
    return AuditContext(
        project_id="P1",
        as_of=date(2026, 4, 1),
        eligibility=EligibilityPeriod(start=date(2026, 1, 1), end=date(2026, 12, 31)),
        financials=ProjectFinancials(
            total_project_cost=Decimal("1000"), eligible_cost=Decimal("900"), grant_amount=Decimal("500"), currency="EUR"
        ),
        costs=costs,
        claimed_cost_ids=claimed or [],
    )


def _cost(cost_id, invoice_number, document_hash):
    return Cost(
        cost_id=cost_id, invoice_number=invoice_number, invoice_date=date(2026, 3, 1),
        amount=Decimal("100"), currency="EUR", budget_line_id="BL1", supplier_id="SUP-1", document_hash=document_hash
    )


def test_r26_critical_warning_for_duplicate_invoice_number():
    ctx = _base([_cost("C1", "INV-1", "h1"), _cost("C2", "INV-1", "h2")])
    finding = run_rule("R26", ctx, TolerancePolicy())[0]
    assert finding.verdict == Verdict.WARNING
    assert finding.severity == Severity.CRITICAL


def test_r44_critical_warning_when_same_cost_is_claimed_twice():
    ctx = _base([_cost("C1", "INV-1", "h1")], claimed=["C1", "C1"])
    finding = run_rule("R44", ctx, TolerancePolicy())[0]
    assert finding.verdict == Verdict.WARNING
    assert finding.reason_code == "DUPLICATE_CLAIM_DETECTED"
