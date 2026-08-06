from datetime import date
from decimal import Decimal

from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import Severity, Verdict
from projektguard.domain.models import AuditContext, Contract, EligibilityPeriod, Procurement, ProjectFinancials, SourceRef
import projektguard.rules.procurement


def _context(award="79500", contract="82350", invoiced="82350", paid="82350"):
    return AuditContext(
        project_id="P1",
        as_of=date(2026, 5, 1),
        eligibility=EligibilityPeriod(start=date(2026, 1, 1), end=date(2026, 12, 31)),
        financials=ProjectFinancials(
            total_project_cost=Decimal("100000"), eligible_cost=Decimal("90000"), grant_amount=Decimal("50000"), currency="EUR"
        ),
        procurements=[Procurement(
            procurement_id="PR1", award_amount=Decimal(award), currency="EUR",
            sources=[SourceRef(document_id="award.pdf", page=4)],
        )],
        contracts=[Contract(
            contract_id="CON1", procurement_id="PR1", amount=Decimal(contract), currency="EUR",
            actual_invoiced=Decimal(invoiced), actual_paid=Decimal(paid),
            sources=[SourceRef(document_id="contract.pdf", page=2)],
        )],
    )


def test_r18_warns_on_material_award_contract_difference():
    finding = run_rule("R18", _context(), TolerancePolicy(absolute=Decimal("10"), relative_percent=Decimal("0.1")))[0]
    assert finding.verdict == Verdict.WARNING
    assert finding.severity == Severity.HIGH
    assert finding.facts["difference"] == Decimal("2850")


def test_r61_suppresses_immaterial_four_unit_difference():
    ctx = _context(award="55000", contract="55004", invoiced="55004", paid="55004")
    finding = run_rule("R61", ctx, TolerancePolicy(absolute=Decimal("10"), relative_percent=Decimal("0.1")))[0]
    assert finding.verdict == Verdict.VERIFIED
    assert finding.severity == Severity.INFO


def test_r51_warns_when_actual_paid_exceeds_contract():
    ctx = _context(award="100", contract="100", invoiced="102", paid="102")
    finding = run_rule("R51", ctx, TolerancePolicy())[0]
    assert finding.verdict == Verdict.WARNING
    assert finding.reason_code == "ACTUAL_PAID_EXCEEDS_CONTRACT"


def test_r18_unknown_when_contract_is_missing():
    ctx = _context()
    ctx.contracts = []
    finding = run_rule("R18", ctx, TolerancePolicy())[0]
    assert finding.verdict == Verdict.UNKNOWN
    assert finding.reason_code == "PROCUREMENT_OR_CONTRACT_MISSING"


def test_r22_unknown_when_actual_invoicing_is_missing():
    ctx = _context()
    ctx.contracts[0].actual_invoiced = None
    finding = run_rule("R22", ctx, TolerancePolicy())[0]
    assert finding.verdict == Verdict.UNKNOWN
    assert finding.reason_code == "INVOICING_DATA_UNKNOWN"


def test_r51_unknown_when_actual_payment_total_is_missing():
    ctx = _context()
    ctx.contracts[0].actual_paid = None
    finding = run_rule("R51", ctx, TolerancePolicy())[0]
    assert finding.verdict == Verdict.UNKNOWN
    assert finding.reason_code == "ACTUAL_PAYMENT_TOTAL_UNKNOWN"


def test_r61_unknown_when_materiality_comparison_is_unavailable():
    ctx = _context()
    ctx.contracts[0].actual_paid = None
    finding = run_rule("R61", ctx, TolerancePolicy())[0]
    assert finding.verdict == Verdict.UNKNOWN
    assert finding.reason_code == "COMPARISON_NOT_AVAILABLE"
