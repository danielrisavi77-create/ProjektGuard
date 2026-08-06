from decimal import Decimal

from projektguard.audit.finding import Finding
from projektguard.audit.registry import Rule, register_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import ExecutionClass, Severity, Verdict
from projektguard.domain.models import AuditContext
from projektguard.domain.money import compare_amounts


def _target_costs(context: AuditContext):
    observable = {cost.cost_id: cost for cost in context.observable_costs()}
    if context.claimed_cost_ids:
        return [(cost_id, observable.get(cost_id)) for cost_id in dict.fromkeys(context.claimed_cost_ids)]
    return [(cost.cost_id, cost) for cost in observable.values()]


def evaluate_r30(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    targets = _target_costs(context)
    if not targets:
        return [Finding(rule_id="R30", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="PAYMENT_EVIDENCE_NOT_AVAILABLE",
                        message="No observable cost is available for payment-evidence testing.")]
    payments = context.observable_payments()
    findings = []
    for cost_id, cost in targets:
        if cost is None:
            findings.append(Finding(
                rule_id="R30", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                reason_code="CLAIMED_COST_NOT_AVAILABLE", message="Claimed cost is not available at the audit cutoff.",
                subject_type="cost", subject_id=cost_id,
            ))
            continue
        linked = [payment for payment in payments if cost_id in payment.related_cost_ids]
        evidence = [source for payment in linked for source in payment.evidence_sources]
        findings.append(Finding(
            rule_id="R30", verdict=Verdict.VERIFIED if evidence else Verdict.UNKNOWN, severity=Severity.HIGH,
            reason_code="PAYMENT_EVIDENCE_PRESENT" if evidence else "PAYMENT_EVIDENCE_NOT_AVAILABLE",
            message="Payment evidence is available." if evidence else "Payment evidence is not available for this cost.",
            subject_type="cost", subject_id=cost_id,
            sources=evidence,
        ))
    return findings


def evaluate_r32(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    costs = context.observable_costs()
    if not costs:
        return [Finding(rule_id="R32", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="PAYMENT_RECONCILIATION_UNKNOWN", message="No observable cost is available for reconciliation.")]
    payments = context.observable_payments()
    findings = []
    for cost in costs:
        linked = [payment for payment in payments if cost.cost_id in payment.related_cost_ids]
        if not linked:
            findings.append(Finding(
                rule_id="R32", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                reason_code="PAYMENT_RECONCILIATION_UNKNOWN", message="No linked payment is available at the audit cutoff.",
                subject_type="cost", subject_id=cost.cost_id, sources=cost.sources,
            ))
            continue
        currencies = {payment.currency for payment in linked}
        if currencies != {cost.currency}:
            findings.append(Finding(
                rule_id="R32", verdict=Verdict.WARNING, severity=Severity.HIGH,
                reason_code="PAYMENT_CURRENCY_MISMATCH",
                message="Linked payment currency does not match the invoice currency.",
                subject_type="cost", subject_id=cost.cost_id,
                facts={"invoice_currency": cost.currency, "payment_currencies": sorted(currencies)},
                sources=[*cost.sources, *[source for payment in linked for source in payment.evidence_sources]],
            ))
            continue
        paid = sum((payment.amount for payment in linked), Decimal("0"))
        diff = compare_amounts(paid, cost.amount, tolerance)
        sources = [source for payment in linked for source in payment.evidence_sources]
        findings.append(Finding(
            rule_id="R32", verdict=Verdict.VERIFIED if diff.within_tolerance else Verdict.WARNING, severity=Severity.HIGH,
            reason_code="PAYMENT_RECONCILED" if diff.within_tolerance else "PAYMENT_AMOUNT_MISMATCH",
            message="Payment reconciles to invoice." if diff.within_tolerance else "Payment total differs materially from invoice.",
            subject_type="cost", subject_id=cost.cost_id,
            facts={"invoice_amount": cost.amount, "payment_amount": paid, "difference": diff.absolute},
            sources=[*cost.sources, *sources],
        ))
    return findings


register_rule(Rule("R30", "Required payment evidence exists", ExecutionClass.EVIDENCE, Severity.HIGH, evaluate_r30))
register_rule(Rule("R32", "Payment amount reconciles with invoice", ExecutionClass.DETERMINISTIC, Severity.HIGH, evaluate_r32))
