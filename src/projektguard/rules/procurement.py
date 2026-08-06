from projektguard.audit.finding import Finding
from projektguard.audit.registry import Rule, register_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import ExecutionClass, Severity, Verdict
from projektguard.domain.models import AuditContext
from projektguard.domain.money import compare_amounts


def _first_linked_pair(context: AuditContext):
    if not context.contracts:
        return None, None
    contract = context.contracts[0]
    procurement = next((p for p in context.procurements if p.procurement_id == contract.procurement_id), None)
    return procurement, contract


def evaluate_r18(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    procurement, contract = _first_linked_pair(context)
    if procurement is None or contract is None:
        return [Finding(rule_id="R18", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="PROCUREMENT_OR_CONTRACT_MISSING", message="Award/contract comparison is unavailable.")]
    diff = compare_amounts(contract.amount, procurement.award_amount, tolerance)
    ok = diff.within_tolerance
    return [Finding(
        rule_id="R18", verdict=Verdict.VERIFIED if ok else Verdict.WARNING, severity=Severity.HIGH,
        reason_code="AWARD_CONTRACT_MATCH" if ok else "CONTRACT_AWARD_AMOUNT_MISMATCH",
        message="Contract value reconciles to award." if ok else "Contract value differs materially from award.",
        facts={"award_amount": procurement.award_amount, "contract_amount": contract.amount,
               "difference": diff.absolute, "difference_percent": diff.relative_percent},
        sources=[*procurement.sources, *contract.sources],
    )]


def evaluate_r22(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    if not context.contracts:
        return [Finding(rule_id="R22", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="INVOICING_DATA_UNKNOWN", message="No contract is available for invoicing reconciliation.")]
    contract = context.contracts[0]
    if contract.actual_invoiced is None:
        return [Finding(rule_id="R22", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="INVOICING_DATA_UNKNOWN", message="Actual invoicing total is not available.")]
    diff = compare_amounts(contract.actual_invoiced, contract.amount, tolerance)
    over = contract.actual_invoiced > contract.amount and not diff.within_tolerance
    return [Finding(
        rule_id="R22", verdict=Verdict.WARNING if over else Verdict.VERIFIED, severity=Severity.HIGH,
        reason_code="ACTUAL_INVOICING_EXCEEDS_CONTRACT" if over else "INVOICING_WITHIN_CONTRACT",
        message="Actual invoicing exceeds the contract ceiling." if over else "Actual invoicing is within the contract ceiling.",
        facts={"contract_amount": contract.amount, "actual_invoiced": contract.actual_invoiced, "difference": diff.absolute},
        sources=contract.sources,
    )]


def evaluate_r51(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    if not context.contracts:
        return [Finding(rule_id="R51", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="ACTUAL_PAYMENT_TOTAL_UNKNOWN", message="No contract execution data is available.")]
    contract = context.contracts[0]
    if contract.actual_paid is None:
        return [Finding(rule_id="R51", verdict=Verdict.UNKNOWN, severity=Severity.HIGH,
                        reason_code="ACTUAL_PAYMENT_TOTAL_UNKNOWN", message="Actual paid total is not available.")]
    diff = compare_amounts(contract.actual_paid, contract.amount, tolerance)
    over = contract.actual_paid > contract.amount and not diff.within_tolerance
    return [Finding(
        rule_id="R51", verdict=Verdict.WARNING if over else Verdict.VERIFIED, severity=Severity.HIGH,
        reason_code="ACTUAL_PAID_EXCEEDS_CONTRACT" if over else "ACTUAL_PAID_WITHIN_CONTRACT",
        message="Actual paid amount exceeds the original contract value." if over else "Actual paid amount is within the contract value.",
        facts={"contract_amount": contract.amount, "actual_paid": contract.actual_paid, "difference": diff.absolute},
        sources=contract.sources,
    )]


def evaluate_r61(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    if not context.contracts or context.contracts[0].actual_paid is None:
        return [Finding(rule_id="R61", verdict=Verdict.UNKNOWN, severity=Severity.LOW,
                        reason_code="COMPARISON_NOT_AVAILABLE", message="Materiality comparison is unavailable.")]
    contract = context.contracts[0]
    diff = compare_amounts(contract.actual_paid, contract.amount, tolerance)
    return [Finding(
        rule_id="R61", verdict=Verdict.VERIFIED if diff.within_tolerance else Verdict.WARNING,
        severity=Severity.INFO if diff.within_tolerance else Severity.LOW,
        reason_code="DIFFERENCE_IMMATERIAL" if diff.within_tolerance else "DIFFERENCE_MATERIAL",
        message="Difference is within configured tolerance." if diff.within_tolerance else "Difference exceeds configured tolerance.",
        facts={"difference": diff.absolute, "difference_percent": diff.relative_percent},
        sources=contract.sources,
    )]


register_rule(Rule("R18", "Contract value matches award decision", ExecutionClass.DETERMINISTIC, Severity.HIGH, evaluate_r18))
register_rule(Rule("R22", "Procurement value reconciles to actual invoicing", ExecutionClass.DETERMINISTIC, Severity.HIGH, evaluate_r22))
register_rule(Rule("R51", "Actual payments exceeding contract trigger review", ExecutionClass.DETERMINISTIC, Severity.HIGH, evaluate_r51))
register_rule(Rule("R61", "Materiality suppresses immaterial differences", ExecutionClass.DETERMINISTIC, Severity.LOW, evaluate_r61))
