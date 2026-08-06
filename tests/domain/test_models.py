from datetime import date
from decimal import Decimal

from projektguard.domain.models import (
    AuditContext,
    BudgetLine,
    BudgetVersion,
    Contract,
    Cost,
    EligibilityPeriod,
    FundingStream,
    Payment,
    Procurement,
    ProjectFinancials,
    SourceRef,
)


def test_decimal_fields_preserve_exact_money():
    cost = Cost(
        cost_id="C1",
        invoice_number="INV-1",
        invoice_date=date(2026, 3, 12),
        amount=Decimal("100.10"),
        currency="EUR",
        budget_line_id="BL1",
        contract_id="CON1",
        document_hash="hash-1",
        sources=[SourceRef(document_id="invoice.pdf", page=1)],
    )
    assert cost.amount == Decimal("100.10")


def test_project_financials_preserve_raw_values_for_audit_rules():
    financials = ProjectFinancials(
        total_project_cost=Decimal("100"),
        eligible_cost=Decimal("120"),
        grant_amount=Decimal("80"),
        currency="EUR",
    )
    assert financials.eligible_cost == Decimal("120")


def test_audit_context_selects_current_budget_by_as_of_date():
    context = AuditContext(
        project_id="P1",
        as_of=date(2026, 5, 1),
        eligibility=EligibilityPeriod(start=date(2026, 1, 1), end=date(2026, 12, 31)),
        financials=ProjectFinancials(
            total_project_cost=Decimal("1000"),
            eligible_cost=Decimal("900"),
            grant_amount=Decimal("500"),
            currency="EUR",
        ),
        budget_versions=[
            BudgetVersion(
                budget_id="B1",
                version=1,
                valid_from=date(2026, 1, 1),
                valid_to=date(2026, 3, 31),
                approved=True,
                approval_source=SourceRef(document_id="budget-v1.pdf", page=1),
                lines=[BudgetLine(budget_line_id="BL1", approved_amount=Decimal("100"), currency="EUR")],
            ),
            BudgetVersion(
                budget_id="B2",
                version=2,
                valid_from=date(2026, 4, 1),
                approved=True,
                approval_source=SourceRef(document_id="addendum.pdf", page=2),
                lines=[BudgetLine(budget_line_id="BL1", approved_amount=Decimal("150"), currency="EUR")],
            ),
        ],
    )
    assert context.current_budget().budget_id == "B2"
