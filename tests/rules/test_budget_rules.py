from datetime import date
from decimal import Decimal

from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import Verdict
from projektguard.domain.models import (
    AuditContext, BudgetLine, BudgetVersion, Cost, EligibilityPeriod, ProjectFinancials, SourceRef
)
import projektguard.rules.budget  # registers rules


def _context(cost_date=date(2026, 5, 1), cost_amount=Decimal("90"), line_id="BL1"):
    return AuditContext(
        project_id="P1",
        as_of=date(2026, 5, 1),
        eligibility=EligibilityPeriod(start=date(2026, 1, 1), end=date(2026, 12, 31)),
        financials=ProjectFinancials(
            total_project_cost=Decimal("1000"), eligible_cost=Decimal("900"), grant_amount=Decimal("500"), currency="EUR"
        ),
        budget_versions=[BudgetVersion(
            budget_id="B2", version=2, valid_from=date(2026, 4, 1), approved=True,
            approval_source=SourceRef(document_id="addendum.pdf", page=2),
            lines=[BudgetLine(budget_line_id="BL1", approved_amount=Decimal("100"), currency="EUR")],
        )],
        costs=[Cost(
            cost_id="C1", invoice_number="INV-1", invoice_date=cost_date, amount=cost_amount,
            currency="EUR", budget_line_id=line_id, document_hash="hash-1"
        )],
    )


def test_r04_warns_when_cost_date_is_outside_eligibility():
    findings = run_rule("R04", _context(cost_date=date(2027, 1, 1)), TolerancePolicy())
    assert findings[0].verdict == Verdict.WARNING
    assert findings[0].reason_code == "COST_OUTSIDE_ELIGIBILITY_PERIOD"


def test_r07_is_unknown_when_budget_line_does_not_exist():
    findings = run_rule("R07", _context(line_id="MISSING"), TolerancePolicy())
    assert findings[0].verdict == Verdict.UNKNOWN
    assert findings[0].reason_code == "BUDGET_LINE_NOT_FOUND"


def test_r09_warns_when_cost_exceeds_current_budget_line():
    findings = run_rule("R09", _context(cost_amount=Decimal("120")), TolerancePolicy())
    assert findings[0].verdict == Verdict.WARNING


def test_r11_verifies_current_budget_version_is_available_and_approved():
    findings = run_rule("R11", _context(), TolerancePolicy())
    assert findings[0].verdict == Verdict.VERIFIED
