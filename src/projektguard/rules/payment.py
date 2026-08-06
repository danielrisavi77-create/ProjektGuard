from decimal import Decimal

from projektguard.audit.finding import Finding
from projektguard.audit.registry import Rule, register_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import ExecutionClass, Severity, Verdict
from projektguard.domain.models import AuditContext
from projektguard.domain.money import compare_amounts


def evaluate_r30(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    evidence = [source for payment in context.payments for source in payment.evidence_sources]
    if not evidence:
        return [Finding(rule_id="R30", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="PAYMENT_EVIDENCE_NOT_AVAILABLE",
                        message="Payment evidence is not available in the normalized context.")]
    return [Finding(rule_id="R30", verdict=Verdict.VERIFIED, severity=Severity.HIGH,
                    reason_code="PAYMENT_EVIDENCE_PRESENT", message="Payment evidence is available.", sources=evidence)]


def evaluate_r32(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    if not context.costs:
        return [Finding(rule_id="R32", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="PAYMENT_RECONCILIATION_UNKNOWN", message="No cost is available for reconciliation.")]
    cost = context.costs[0]
    linked = [payment for payment in context.payments if cost.cost_id in payment.related_cost_ids]
    if not linked:
        return [Finding(rule_id="R32", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="PAYMENT_RECONCILIATION_UNKNOWN", message="No linked payment is available.",
                        sources=cost.sources)]
    paid = sum((payment.amount for payment in linked), Decimal("0"))
    diff = compare_amounts(paid, cost.amount, tolerance)
    sources = [source for payment in linked for source in payment.evidence_sources]
    return [Finding(
        rule_id="R32", verdict=Verdict.VERIFIED if diff.within_tolerance else Verdict.WARNING, severity=Severity.HIGH,
        reason_code="PAYMENT_RECONCILED" if diff.within_tolerance else "PAYMENT_AMOUNT_MISMATCH",
        message="Payment reconciles to invoice." if diff.within_tolerance else "Payment total differs materially from invoice.",
        facts={"invoice_amount": cost.amount, "payment_amount": paid, "difference": diff.absolute},
        sources=[*cost.sources, *sources],
    )]


register_rule(Rule("R30", "Required payment evidence exists", ExecutionClass.EVIDENCE, Severity.HIGH, evaluate_r30))
register_rule(Rule("R32", "Payment amount reconciles with invoice", ExecutionClass.DETERMINISTIC, Severity.HIGH, evaluate_r32))
