from decimal import Decimal

from projektguard.audit.finding import Finding
from projektguard.audit.registry import Rule, register_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import ExecutionClass, Severity, Verdict
from projektguard.domain.models import AuditContext
from projektguard.domain.money import compare_amounts


def evaluate_r53(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    baseline = context.financials.current_approved_project_cost
    paid_values = [contract.actual_paid for contract in context.contracts if contract.actual_paid is not None]
    if baseline is None or not paid_values:
        return [Finding(rule_id="R53", verdict=Verdict.UNKNOWN, severity=Severity.CRITICAL,
                        reason_code="PROJECT_BASELINE_RECONCILIATION_UNKNOWN",
                        message="Current approved project baseline or execution total is unavailable.")]
    executed = sum(paid_values, Decimal("0"))
    diff = compare_amounts(executed, baseline, tolerance)
    over = executed > baseline and not diff.within_tolerance
    return [Finding(
        rule_id="R53", verdict=Verdict.WARNING if over else Verdict.VERIFIED, severity=Severity.CRITICAL,
        reason_code="EXECUTION_EXCEEDS_PROJECT_BASELINE" if over else "EXECUTION_WITHIN_PROJECT_BASELINE",
        message="Known execution exceeds current approved project baseline." if over else "Known execution is within current project baseline.",
        facts={"executed": executed, "current_approved_project_cost": baseline, "difference": diff.absolute},
        sources=[source for contract in context.contracts for source in contract.sources],
    )]


def evaluate_r54(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    if not context.baseline_changed:
        return [Finding(rule_id="R54", verdict=Verdict.VERIFIED, severity=Severity.HIGH,
                        reason_code="BASELINE_UNCHANGED", message="No project financial baseline change is recorded.")]
    if context.baseline_approval_source is None:
        return [Finding(rule_id="R54", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="BASELINE_APPROVAL_EVIDENCE_NOT_LINKED",
                        message="A baseline change exists but approval evidence is not linked.")]
    return [Finding(rule_id="R54", verdict=Verdict.VERIFIED, severity=Severity.HIGH,
                    reason_code="BASELINE_CHANGE_APPROVED", message="Baseline change has linked approval evidence.",
                    sources=[context.baseline_approval_source])]


def evaluate_r62(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    total = context.financials.total_project_cost
    eligible = context.financials.eligible_cost
    grant = context.financials.grant_amount
    facts = {"total_project_cost": total, "eligible_cost": eligible, "grant_amount": grant}
    if total is None or eligible is None or grant is None:
        return [Finding(rule_id="R62", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="FINANCIAL_AMOUNT_LAYER_INCOMPLETE",
                        message="Total, eligible, and grant amounts are not all available.", facts=facts)]
    valid = grant <= eligible <= total
    return [Finding(
        rule_id="R62", verdict=Verdict.VERIFIED if valid else Verdict.WARNING, severity=Severity.HIGH,
        reason_code="FINANCIAL_AMOUNT_ORDER_VALID" if valid else "FINANCIAL_AMOUNT_ORDER_INVALID",
        message="Financial layers are logically ordered." if valid else "Financial layers violate grant <= eligible <= total.",
        facts=facts,
    )]


register_rule(Rule("R53", "Execution exceeding project funding baseline triggers reconciliation", ExecutionClass.DETERMINISTIC, Severity.CRITICAL, evaluate_r53))
register_rule(Rule("R54", "Project baseline change has linked approval", ExecutionClass.EVIDENCE, Severity.HIGH, evaluate_r54))
register_rule(Rule("R62", "Total project cost, eligible cost and grant amount remain distinct", ExecutionClass.DETERMINISTIC, Severity.HIGH, evaluate_r62))
