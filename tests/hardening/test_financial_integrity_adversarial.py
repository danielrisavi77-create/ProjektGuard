from datetime import date
from decimal import Decimal

from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import Severity, Verdict
from projektguard.domain.models import (
    AuditContext,
    BudgetLine,
    BudgetVersion,
    Contract,
    Cost,
    EligibilityPeriod,
    Payment,
    Procurement,
    ProjectFinancials,
    SourceRef,
)
from projektguard.domain.money import compare_amounts
import projektguard.rules.baseline
import projektguard.rules.budget
import projektguard.rules.duplicate
import projektguard.rules.payment
import projektguard.rules.procurement


def policy() -> TolerancePolicy:
    return TolerancePolicy(absolute=Decimal("10"), relative_percent=Decimal("0.1"))


def base_context(**overrides) -> AuditContext:
    values = dict(
        project_id="ADV",
        as_of=date(2026, 5, 1),
        eligibility=EligibilityPeriod(start=date(2026, 1, 1), end=date(2026, 12, 31)),
        financials=ProjectFinancials(
            total_project_cost=Decimal("1000"),
            eligible_cost=Decimal("900"),
            grant_amount=Decimal("500"),
            current_approved_project_cost=Decimal("1000"),
            currency="EUR",
        ),
    )
    values.update(overrides)
    return AuditContext(**values)


def cost(cost_id: str, amount: str = "60", *, invoice_date=date(2026, 3, 1), currency="EUR", line="BL1", supplier_id=None, invoice_number=None, document_hash=None) -> Cost:
    return Cost(
        cost_id=cost_id,
        invoice_number=invoice_number or f"INV-{cost_id}",
        invoice_date=invoice_date,
        amount=Decimal(amount),
        currency=currency,
        budget_line_id=line,
        supplier_id=supplier_id,
        document_hash=document_hash,
    )


def approved_budget(amount: str = "100", *, approved=True, currency="EUR") -> BudgetVersion:
    return BudgetVersion(
        budget_id="B1",
        version=1,
        valid_from=date(2026, 1, 1),
        approved=approved,
        approval_source=SourceRef(document_id="budget.pdf", page=1),
        lines=[BudgetLine(budget_line_id="BL1", approved_amount=Decimal(amount), currency=currency)],
    )


def test_zero_expected_amount_never_passes_relative_tolerance_for_nonzero_actual():
    diff = compare_amounts(Decimal("1000"), Decimal("0"), policy())
    assert diff.within_tolerance is False


def test_r04_evaluates_every_observable_cost_not_only_first():
    ctx = base_context(costs=[
        cost("C1", invoice_date=date(2026, 3, 1)),
        cost("C2", invoice_date=date(2025, 12, 31)),
    ])
    findings = run_rule("R04", ctx, policy())
    assert len(findings) == 2
    assert any(f.verdict == Verdict.WARNING and f.subject_id == "C2" for f in findings)


def test_future_dated_cost_is_not_used_before_as_of_cutoff():
    ctx = base_context(costs=[cost("FUTURE", invoice_date=date(2026, 12, 1))])
    finding = run_rule("R04", ctx, policy())[0]
    assert finding.verdict == Verdict.UNKNOWN
    assert finding.reason_code == "COST_DATE_NOT_YET_OBSERVABLE"


def test_r09_uses_cumulative_budget_line_spend():
    ctx = base_context(budget_versions=[approved_budget("100")], costs=[cost("C1", "60"), cost("C2", "60")])
    finding = run_rule("R09", ctx, policy())[0]
    assert finding.verdict == Verdict.WARNING
    assert finding.reason_code == "BUDGET_LINE_EXCEEDED"
    assert finding.facts["cost_amount"] == Decimal("120")


def test_r09_does_not_verify_against_unapproved_budget_version():
    ctx = base_context(budget_versions=[approved_budget("100", approved=False)], costs=[cost("C1", "60")])
    finding = run_rule("R09", ctx, policy())[0]
    assert finding.verdict == Verdict.UNKNOWN
    assert finding.reason_code == "CURRENT_APPROVED_BUDGET_NOT_AVAILABLE"


def test_r09_rejects_cross_currency_budget_comparison():
    ctx = base_context(budget_versions=[approved_budget("100", currency="HRK")], costs=[cost("C1", "60", currency="EUR")])
    finding = run_rule("R09", ctx, policy())[0]
    assert finding.verdict == Verdict.WARNING
    assert finding.reason_code == "BUDGET_LINE_CURRENCY_MISMATCH"


def test_r18_evaluates_all_linked_contracts():
    ctx = base_context(
        procurements=[
            Procurement(procurement_id="P1", award_amount=Decimal("100"), currency="EUR"),
            Procurement(procurement_id="P2", award_amount=Decimal("100"), currency="EUR"),
        ],
        contracts=[
            Contract(contract_id="C1", procurement_id="P1", amount=Decimal("100"), currency="EUR"),
            Contract(contract_id="C2", procurement_id="P2", amount=Decimal("150"), currency="EUR"),
        ],
    )
    findings = run_rule("R18", ctx, policy())
    assert len(findings) == 2
    assert any(f.verdict == Verdict.WARNING and f.subject_id == "C2" for f in findings)


def test_r18_currency_mismatch_cannot_be_verified():
    ctx = base_context(
        procurements=[Procurement(procurement_id="P1", award_amount=Decimal("100"), currency="EUR")],
        contracts=[Contract(contract_id="C1", procurement_id="P1", amount=Decimal("100"), currency="HRK")],
    )
    finding = run_rule("R18", ctx, policy())[0]
    assert finding.verdict == Verdict.WARNING
    assert finding.reason_code == "AWARD_CONTRACT_CURRENCY_MISMATCH"


def test_r30_requires_payment_evidence_for_each_claimed_cost():
    ctx = base_context(
        costs=[cost("C1", "100"), cost("C2", "100")],
        claimed_cost_ids=["C1", "C2"],
        payments=[Payment(
            payment_id="P1", payment_date=date(2026, 3, 10), amount=Decimal("100"), currency="EUR",
            related_cost_ids=["C1"], evidence_sources=[SourceRef(document_id="bank.pdf", page=1)],
        )],
    )
    findings = run_rule("R30", ctx, policy())
    assert len(findings) == 2
    assert any(f.verdict == Verdict.UNKNOWN and f.subject_id == "C2" for f in findings)


def test_r32_currency_mismatch_cannot_be_reconciled():
    ctx = base_context(
        costs=[cost("C1", "100", currency="EUR")],
        payments=[Payment(
            payment_id="P1", payment_date=date(2026, 3, 10), amount=Decimal("100"), currency="HRK",
            related_cost_ids=["C1"], evidence_sources=[SourceRef(document_id="bank.pdf", page=1)],
        )],
    )
    finding = run_rule("R32", ctx, policy())[0]
    assert finding.verdict == Verdict.WARNING
    assert finding.reason_code == "PAYMENT_CURRENCY_MISMATCH"


def test_r32_ignores_future_payments_after_cutoff():
    ctx = base_context(
        costs=[cost("C1", "100")],
        payments=[Payment(
            payment_id="P1", payment_date=date(2026, 12, 10), amount=Decimal("100"), currency="EUR",
            related_cost_ids=["C1"], evidence_sources=[SourceRef(document_id="future-bank.pdf", page=1)],
        )],
    )
    finding = run_rule("R32", ctx, policy())[0]
    assert finding.verdict == Verdict.UNKNOWN
    assert finding.reason_code == "PAYMENT_RECONCILIATION_UNKNOWN"


def test_baseline_change_status_defaults_to_unknown_not_false():
    ctx = base_context()
    finding = run_rule("R54", ctx, policy())[0]
    assert finding.verdict == Verdict.UNKNOWN
    assert finding.reason_code == "BASELINE_CHANGE_STATUS_UNKNOWN"


def test_cost_retains_supplier_identity_for_duplicate_detection():
    item = cost("C1", supplier_id="OIB-123")
    assert item.supplier_id == "OIB-123"


def test_r26_same_invoice_number_from_different_suppliers_is_not_duplicate():
    ctx = base_context(costs=[
        cost("C1", supplier_id="A", invoice_number="2026-001", document_hash="h1"),
        cost("C2", supplier_id="B", invoice_number="2026-001", document_hash="h2"),
    ])
    finding = run_rule("R26", ctx, policy())[0]
    assert finding.verdict == Verdict.VERIFIED


def test_r44_detects_same_invoice_claimed_under_different_cost_ids():
    ctx = base_context(
        costs=[
            cost("C1", supplier_id="A", invoice_number="2026-001", document_hash="same-hash"),
            cost("C2", supplier_id="A", invoice_number="2026-001", document_hash="same-hash"),
        ],
        claimed_cost_ids=["C1", "C2"],
    )
    finding = run_rule("R44", ctx, policy())[0]
    assert finding.verdict == Verdict.WARNING
    assert finding.reason_code == "DUPLICATE_CLAIM_DETECTED"


def test_r07_evaluates_budget_mapping_for_every_observable_cost():
    ctx = base_context(budget_versions=[approved_budget("100")], costs=[cost("C1", line="BL1"), cost("C2", line="MISSING")])
    findings = run_rule("R07", ctx, policy())
    assert len(findings) == 2
    assert any(f.verdict == Verdict.UNKNOWN and f.subject_id == "C2" for f in findings)


def test_r22_evaluates_every_contract_not_only_first():
    ctx = base_context(contracts=[
        Contract(contract_id="C1", amount=Decimal("100"), currency="EUR", actual_invoiced=Decimal("100")),
        Contract(contract_id="C2", amount=Decimal("100"), currency="EUR", actual_invoiced=Decimal("150")),
    ])
    findings = run_rule("R22", ctx, policy())
    assert len(findings) == 2
    assert any(f.verdict == Verdict.WARNING and f.subject_id == "C2" for f in findings)


def test_r51_evaluates_every_contract_not_only_first():
    ctx = base_context(contracts=[
        Contract(contract_id="C1", amount=Decimal("100"), currency="EUR", actual_paid=Decimal("100")),
        Contract(contract_id="C2", amount=Decimal("100"), currency="EUR", actual_paid=Decimal("150")),
    ])
    findings = run_rule("R51", ctx, policy())
    assert len(findings) == 2
    assert any(f.verdict == Verdict.WARNING and f.subject_id == "C2" for f in findings)


def test_r61_evaluates_materiality_for_every_contract():
    ctx = base_context(contracts=[
        Contract(contract_id="C1", amount=Decimal("100"), currency="EUR", actual_paid=Decimal("104")),
        Contract(contract_id="C2", amount=Decimal("100"), currency="EUR", actual_paid=Decimal("150")),
    ])
    findings = run_rule("R61", ctx, policy())
    assert len(findings) == 2
    assert any(f.verdict == Verdict.WARNING and f.subject_id == "C2" for f in findings)


def test_r32_evaluates_every_cost_not_only_first():
    ctx = base_context(
        costs=[cost("C1", "100"), cost("C2", "100")],
        payments=[
            Payment(payment_id="P1", payment_date=date(2026, 3, 10), amount=Decimal("100"), currency="EUR", related_cost_ids=["C1"]),
            Payment(payment_id="P2", payment_date=date(2026, 3, 10), amount=Decimal("50"), currency="EUR", related_cost_ids=["C2"]),
        ],
    )
    findings = run_rule("R32", ctx, policy())
    assert len(findings) == 2
    assert any(f.verdict == Verdict.WARNING and f.subject_id == "C2" for f in findings)


def test_r53_requires_expert_review_for_cross_currency_execution_aggregation():
    ctx = base_context(contracts=[Contract(contract_id="C1", amount=Decimal("100"), currency="HRK", actual_paid=Decimal("100"))])
    finding = run_rule("R53", ctx, policy())[0]
    assert finding.verdict == Verdict.EXPERT_REVIEW
    assert finding.reason_code == "PROJECT_BASELINE_CURRENCY_CONVERSION_REQUIRED"
    assert finding.requires_expert_review is True


def test_contract_execution_observed_after_cutoff_is_not_used():
    ctx = base_context(contracts=[Contract(
        contract_id="C1", amount=Decimal("100"), currency="EUR", actual_paid=Decimal("150"),
        actual_paid_observed_at=date(2026, 6, 1),
    )])
    finding = run_rule("R51", ctx, policy())[0]
    assert finding.verdict == Verdict.UNKNOWN
    assert finding.reason_code == "ACTUAL_PAYMENT_TOTAL_UNKNOWN"


def test_r26_repeated_invoice_number_without_supplier_identity_stays_unknown():
    ctx = base_context(costs=[
        cost("C1", supplier_id=None, invoice_number="2026-001", document_hash="h1"),
        cost("C2", supplier_id=None, invoice_number="2026-001", document_hash="h2"),
    ])
    finding = run_rule("R26", ctx, policy())[0]
    assert finding.verdict == Verdict.UNKNOWN
    assert finding.reason_code == "DUPLICATE_INVOICE_IDENTITY_INCOMPLETE"
