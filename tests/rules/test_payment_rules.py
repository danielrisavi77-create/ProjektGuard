from datetime import date
from decimal import Decimal

from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import Verdict
from projektguard.domain.models import AuditContext, Cost, EligibilityPeriod, Payment, ProjectFinancials, SourceRef
import projektguard.rules.payment


def _context(payments):
    return AuditContext(
        project_id="P1",
        as_of=date(2026, 4, 1),
        eligibility=EligibilityPeriod(start=date(2026, 1, 1), end=date(2026, 12, 31)),
        financials=ProjectFinancials(
            total_project_cost=Decimal("1000"), eligible_cost=Decimal("900"), grant_amount=Decimal("500"), currency="EUR"
        ),
        costs=[Cost(
            cost_id="C1", invoice_number="INV-1", invoice_date=date(2026, 3, 1), amount=Decimal("100"),
            currency="EUR", budget_line_id="BL1", document_hash="h1"
        )],
        payments=payments,
    )


def test_r30_unknown_when_payment_evidence_is_not_available():
    finding = run_rule("R30", _context([]), TolerancePolicy())[0]
    assert finding.verdict == Verdict.UNKNOWN
    assert finding.reason_code == "PAYMENT_EVIDENCE_NOT_AVAILABLE"


def test_r32_verifies_exact_invoice_payment_reconciliation():
    payment = Payment(
        payment_id="P1", payment_date=date(2026, 3, 10), amount=Decimal("100"), currency="EUR",
        related_cost_ids=["C1"], evidence_sources=[SourceRef(document_id="bank.pdf", page=1)]
    )
    finding = run_rule("R32", _context([payment]), TolerancePolicy())[0]
    assert finding.verdict == Verdict.VERIFIED


def test_r32_warns_on_material_underpayment():
    payment = Payment(
        payment_id="P1", payment_date=date(2026, 3, 10), amount=Decimal("90"), currency="EUR",
        related_cost_ids=["C1"], evidence_sources=[SourceRef(document_id="bank.pdf", page=1)]
    )
    finding = run_rule("R32", _context([payment]), TolerancePolicy())[0]
    assert finding.verdict == Verdict.WARNING
