from projektguard.audit.finding import Finding
from projektguard.audit.registry import Rule, register_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import ExecutionClass, Severity, Verdict
from projektguard.domain.models import AuditContext


def evaluate_r04(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    if not context.costs:
        return [Finding(rule_id="R04", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="COST_DATE_UNKNOWN", message="No cost date is available for eligibility testing.")]
    cost = context.costs[0]
    valid = context.eligibility.start <= cost.invoice_date <= context.eligibility.end
    return [Finding(
        rule_id="R04", verdict=Verdict.VERIFIED if valid else Verdict.WARNING, severity=Severity.HIGH,
        reason_code="COST_DATE_VALID" if valid else "COST_OUTSIDE_ELIGIBILITY_PERIOD",
        message="Cost date is inside the eligibility period." if valid else "Cost date is outside the eligibility period.",
        facts={"invoice_date": cost.invoice_date.isoformat(), "eligibility_start": context.eligibility.start.isoformat(),
               "eligibility_end": context.eligibility.end.isoformat()},
        sources=cost.sources,
    )]


def evaluate_r07(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    budget = context.current_budget()
    if budget is None:
        return [Finding(rule_id="R07", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="CURRENT_BUDGET_NOT_AVAILABLE", message="Current approved budget is not available.")]
    if not context.costs:
        return [Finding(rule_id="R07", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="COST_BUDGET_MAPPING_UNKNOWN", message="No cost is available for budget-line mapping.")]
    cost = context.costs[0]
    line = budget.line(cost.budget_line_id)
    return [Finding(
        rule_id="R07", verdict=Verdict.VERIFIED if line else Verdict.UNKNOWN, severity=Severity.HIGH,
        reason_code="BUDGET_LINE_FOUND" if line else "BUDGET_LINE_NOT_FOUND",
        message="Budget line exists in the current approved budget." if line else "Mapped budget line is not present in the current budget fixture.",
        facts={"budget_id": budget.budget_id, "budget_line_id": cost.budget_line_id},
        sources=[budget.approval_source] if budget.approval_source else [],
    )]


def evaluate_r09(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    budget = context.current_budget()
    if budget is None or not context.costs:
        return [Finding(rule_id="R09", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="BUDGET_LINE_LIMIT_UNKNOWN", message="Budget-line limit cannot be evaluated.")]
    cost = context.costs[0]
    line = budget.line(cost.budget_line_id)
    if line is None:
        return [Finding(rule_id="R09", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="BUDGET_LINE_LIMIT_UNKNOWN", message="Budget-line limit cannot be evaluated.")]
    within = cost.amount <= line.approved_amount
    return [Finding(
        rule_id="R09", verdict=Verdict.VERIFIED if within else Verdict.WARNING, severity=Severity.HIGH,
        reason_code="WITHIN_BUDGET_LINE" if within else "BUDGET_LINE_EXCEEDED",
        message="Cost is within the current budget-line ceiling." if within else "Cost exceeds the current budget-line ceiling.",
        facts={"cost_amount": cost.amount, "approved_amount": line.approved_amount},
        sources=[budget.approval_source] if budget.approval_source else [],
    )]


def evaluate_r11(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    budget = context.current_budget()
    if budget is None:
        return [Finding(rule_id="R11", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="CURRENT_BUDGET_VERSION_UNKNOWN", message="No budget version is valid for the audit date.")]
    if not budget.approved:
        return [Finding(rule_id="R11", verdict=Verdict.WARNING, severity=Severity.HIGH,
                        reason_code="CURRENT_BUDGET_NOT_APPROVED", message="The active budget version is not marked approved.",
                        facts={"budget_id": budget.budget_id, "version": budget.version},
                        sources=[budget.approval_source] if budget.approval_source else [])]
    return [Finding(rule_id="R11", verdict=Verdict.VERIFIED, severity=Severity.HIGH,
                    reason_code="CURRENT_BUDGET_VERSION_CONFIRMED", message="Current approved budget version is available.",
                    facts={"budget_id": budget.budget_id, "version": budget.version},
                    sources=[budget.approval_source] if budget.approval_source else [])]


register_rule(Rule("R04", "Cost date falls inside eligibility period", ExecutionClass.DETERMINISTIC, Severity.HIGH, evaluate_r04))
register_rule(Rule("R07", "Budget line exists", ExecutionClass.DETERMINISTIC, Severity.HIGH, evaluate_r07))
register_rule(Rule("R09", "Cost does not exceed current approved budget line", ExecutionClass.DETERMINISTIC, Severity.HIGH, evaluate_r09))
register_rule(Rule("R11", "Current approved budget version is used", ExecutionClass.DETERMINISTIC, Severity.HIGH, evaluate_r11))
