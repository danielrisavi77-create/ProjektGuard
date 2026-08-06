from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class SourceRef(BaseModel):
    document_id: str
    page: int | None = Field(default=None, ge=1)
    url: str | None = None


class EligibilityPeriod(BaseModel):
    start: date
    end: date

    @model_validator(mode="after")
    def validate_order(self):
        if self.end < self.start:
            raise ValueError("eligibility end must be on or after start")
        return self


class BudgetLine(BaseModel):
    budget_line_id: str
    approved_amount: Decimal
    currency: str


class BudgetVersion(BaseModel):
    budget_id: str
    version: int = Field(ge=1)
    valid_from: date
    valid_to: date | None = None
    approved: bool
    approval_source: SourceRef | None = None
    lines: list[BudgetLine] = Field(default_factory=list)

    def line(self, budget_line_id: str) -> BudgetLine | None:
        return next((line for line in self.lines if line.budget_line_id == budget_line_id), None)


class Procurement(BaseModel):
    procurement_id: str
    award_amount: Decimal
    currency: str
    selected_supplier_id: str | None = None
    sources: list[SourceRef] = Field(default_factory=list)


class Contract(BaseModel):
    contract_id: str
    procurement_id: str | None = None
    amount: Decimal
    currency: str
    actual_invoiced: Decimal | None = None
    actual_paid: Decimal | None = None
    sources: list[SourceRef] = Field(default_factory=list)


class Cost(BaseModel):
    cost_id: str
    invoice_number: str
    invoice_date: date
    amount: Decimal
    currency: str
    budget_line_id: str
    contract_id: str | None = None
    document_hash: str | None = None
    sources: list[SourceRef] = Field(default_factory=list)


class Payment(BaseModel):
    payment_id: str
    payment_date: date
    amount: Decimal
    currency: str
    related_cost_ids: list[str]
    evidence_sources: list[SourceRef] = Field(default_factory=list)


class FundingStream(BaseModel):
    funding_stream_id: str
    approved_amount: Decimal
    currency: str
    reimbursement_lifecycle: str


class ProjectFinancials(BaseModel):
    total_project_cost: Decimal | None = None
    eligible_cost: Decimal | None = None
    grant_amount: Decimal | None = None
    currency: str
    current_approved_project_cost: Decimal | None = None


class AuditContext(BaseModel):
    project_id: str
    as_of: date
    eligibility: EligibilityPeriod
    financials: ProjectFinancials
    budget_versions: list[BudgetVersion] = Field(default_factory=list)
    procurements: list[Procurement] = Field(default_factory=list)
    contracts: list[Contract] = Field(default_factory=list)
    costs: list[Cost] = Field(default_factory=list)
    payments: list[Payment] = Field(default_factory=list)
    funding_streams: list[FundingStream] = Field(default_factory=list)
    claimed_cost_ids: list[str] = Field(default_factory=list)
    baseline_changed: bool = False
    baseline_approval_source: SourceRef | None = None

    def current_budget(self) -> BudgetVersion | None:
        eligible = [
            budget
            for budget in self.budget_versions
            if budget.valid_from <= self.as_of
            and (budget.valid_to is None or self.as_of <= budget.valid_to)
        ]
        if not eligible:
            return None
        return max(eligible, key=lambda budget: budget.version)
