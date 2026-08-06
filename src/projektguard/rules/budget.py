from collections import defaultdict
from decimal import Decimal

from projektguard.audit.finding import Finding
from projektguard.audit.registry import Rule, register_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import ExecutionClass, Severity, Verdict
from projektguard.domain.models import AuditContext


def _no_observable_cost_finding(rule_id: str, reason_code: str, message: str) -> Finding:
    return Finding(rule_id=rule_id, verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                   reason_code=reason_code, message=message)


def evaluate_r04(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    costs = context.observable_costs()
    if not costs:
        reason = "COST_DATE_NOT_YET_OBSERVABLE" if context.costs else "COST_DATE_UNKNOWN"
        message = "Cost data exists only after the audit cutoff." if context.costs else "No cost date is available for eligibility testing."
        return [_no_observable_cost_finding("R04", reason, message)]
    findings = []
    for cost in costs:
        valid = context.eligibility.start <= cost.invoice_date <= context.eligibility.end
        findings.append(Finding(
            rule_id="R04", verdict=Verdict.VERIFIED if valid else Verdict.WARNING, severity=Severity.HIGH,
            reason_code="COST_DATE_VALID" if valid else "COST_OUTSIDE_ELIGIBILITY_PERIOD",
            message="Cost date is inside the eligibility period." if valid else "Cost date is outside the eligibility period.",
            subject_type="cost", subject_id=cost.cost_id,
            facts={"invoice_date": cost.invoice_date.isoformat(), "eligibility_start": context.eligibility.start.isoformat(),
                   "eligibility_end": context.eligibility.end.isoformat()},
            sources=cost.sources,
        ))
    return findings


def evaluate_r07(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    budget = context.current_approved_budget()
    if budget is None:
        return [Finding(rule_id="R07", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="CURRENT_BUDGET_NOT_AVAILABLE", message="Current approved budget is not available.")]
    costs = context.observable_costs()
    if not costs:
        return [Finding(rule_id="R07", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="COST_BUDGET_MAPPING_UNKNOWN", message="No observable cost is available for budget-line mapping.")]
    findings = []
    for cost in costs:
        line = budget.line(cost.budget_line_id)
        findings.append(Finding(
            rule_id="R07", verdict=Verdict.VERIFIED if line else Verdict.UNKNOWN, severity=Severity.HIGH,
            reason_code="BUDGET_LINE_FOUND" if line else "BUDGET_LINE_NOT_FOUND",
            message="Budget line exists in the current approved budget." if line else "Mapped budget line is not present in the current approved budget.",
            subject_type="cost", subject_id=cost.cost_id,
            facts={"budget_id": budget.budget_id, "budget_line_id": cost.budget_line_id},
            sources=[budget.approval_source] if budget.approval_source else [],
        ))
    return findings


def evaluate_r09(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    budget = context.current_approved_budget()
    if budget is None:
        return [Finding(rule_id="R09", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="CURRENT_APPROVED_BUDGET_NOT_AVAILABLE",
                        message="No approved budget version is valid for the audit date.")]
    costs = context.observable_costs()
    if not costs:
        return [Finding(rule_id="R09", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="BUDGET_LINE_LIMIT_UNKNOWN", message="Budget-line limit cannot be evaluated.")]

    grouped: dict[str, list] = defaultdict(list)
    for cost in costs:
        grouped[cost.budget_line_id].append(cost)

    findings: list[Finding] = []
    for line_id, line_costs in grouped.items():
        line = budget.line(line_id)
        if line is None:
            findings.append(Finding(
                rule_id="R09", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                reason_code="BUDGET_LINE_LIMIT_UNKNOWN", message="Budget-line limit cannot be evaluated.",
                subject_type="budget_line", subject_id=line_id,
                facts={"budget_line_id": line_id},
            ))
            continue
        currencies = {cost.currency for cost in line_costs}
        if currencies != {line.currency}:
            findings.append(Finding(
                rule_id="R09", verdict=Verdict.WARNING, severity=Severity.HIGH,
                reason_code="BUDGET_LINE_CURRENCY_MISMATCH",
                message="Cost currency does not match the approved budget-line currency.",
                subject_type="budget_line", subject_id=line_id,
                facts={"budget_currency": line.currency, "cost_currencies": sorted(currencies)},
                sources=[budget.approval_source] if budget.approval_source else [],
            ))
            continue
        total = sum((cost.amount for cost in line_costs), Decimal("0"))
        within = total <= line.approved_amount
        findings.append(Finding(
            rule_id="R09", verdict=Verdict.VERIFIED if within else Verdict.WARNING, severity=Severity.HIGH,
            reason_code="WITHIN_BUDGET_LINE" if within else "BUDGET_LINE_EXCEEDED",
            message="Cumulative cost is within the current budget-line ceiling." if within else "Cumulative cost exceeds the current budget-line ceiling.",
            subject_type="budget_line", subject_id=line_id,
            facts={"cost_amount": total, "approved_amount": line.approved_amount},
            sources=[budget.approval_source] if budget.approval_source else [],
        ))
    return findings


def evaluate_r11(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    budget = context.active_budget()
    if budget is None:
        return [Finding(rule_id="R11", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="CURRENT_BUDGET_VERSION_UNKNOWN", message="No budget version is valid for the audit date.")]
    if not budget.approved:
        return [Finding(rule_id="R11", verdict=Verdict.WARNING, severity=Severity.HIGH,
                        reason_code="CURRENT_BUDGET_NOT_APPROVED", message="The active budget version is not marked approved.",
                        subject_type="budget", subject_id=budget.budget_id,
                        facts={"budget_id": budget.budget_id, "version": budget.version},
                        sources=[budget.approval_source] if budget.approval_source else [])]
    return [Finding(rule_id="R11", verdict=Verdict.VERIFIED, severity=Severity.HIGH,
                    reason_code="CURRENT_BUDGET_VERSION_CONFIRMED", message="Current approved budget version is available.",
                    subject_type="budget", subject_id=budget.budget_id,
                    facts={"budget_id": budget.budget_id, "version": budget.version},
                    sources=[budget.approval_source] if budget.approval_source else [])]


register_rule(Rule("R04", "Cost date falls inside eligibility period", ExecutionClass.DETERMINISTIC, Severity.HIGH, evaluate_r04))
register_rule(Rule("R07", "Budget line exists", ExecutionClass.DETERMINISTIC, Severity.HIGH, evaluate_r07))
register_rule(Rule("R09", "Cost does not exceed current approved budget line", ExecutionClass.DETERMINISTIC, Severity.HIGH, evaluate_r09))
register_rule(Rule("R11", "Current approved budget version is used", ExecutionClass.DETERMINISTIC, Severity.HIGH, evaluate_r11))
