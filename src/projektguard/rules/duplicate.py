from collections import Counter

from projektguard.audit.finding import Finding
from projektguard.audit.registry import Rule, register_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import ExecutionClass, Severity, Verdict
from projektguard.domain.models import AuditContext


def evaluate_r26(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    numbers = [cost.invoice_number.strip().casefold() for cost in context.costs if cost.invoice_number.strip()]
    if not numbers:
        return [Finding(rule_id="R26", verdict=Verdict.UNKNOWN, severity=Severity.CRITICAL,
                        reason_code="INVOICE_DATA_UNKNOWN", message="No invoice numbers are available.")]
    duplicates = sorted(number for number, count in Counter(numbers).items() if count > 1)
    return [Finding(
        rule_id="R26", verdict=Verdict.WARNING if duplicates else Verdict.VERIFIED, severity=Severity.CRITICAL,
        reason_code="DUPLICATE_INVOICE_NUMBER" if duplicates else "INVOICE_NUMBERS_UNIQUE",
        message="Duplicate invoice number detected." if duplicates else "Invoice numbers are unique in the evaluated context.",
        facts={"duplicate_invoice_numbers": duplicates},
        sources=[source for cost in context.costs for source in cost.sources],
    )]


def evaluate_r44(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    if not context.claimed_cost_ids:
        return [Finding(rule_id="R44", verdict=Verdict.UNKNOWN, severity=Severity.CRITICAL,
                        reason_code="CLAIM_DATA_UNKNOWN", message="No ZNS claim mapping is available.")]
    duplicates = sorted(cost_id for cost_id, count in Counter(context.claimed_cost_ids).items() if count > 1)
    sources = [source for cost in context.costs if cost.cost_id in duplicates for source in cost.sources]
    return [Finding(
        rule_id="R44", verdict=Verdict.WARNING if duplicates else Verdict.VERIFIED, severity=Severity.CRITICAL,
        reason_code="DUPLICATE_CLAIM_DETECTED" if duplicates else "CLAIMS_UNIQUE",
        message="A cost is claimed more than once." if duplicates else "No duplicated cost claim is present.",
        facts={"duplicate_cost_ids": duplicates},
        sources=sources if duplicates else [source for cost in context.costs for source in cost.sources],
    )]


register_rule(Rule("R26", "Duplicate invoice number detection", ExecutionClass.DETERMINISTIC, Severity.CRITICAL, evaluate_r26))
register_rule(Rule("R44", "Same invoice is not claimed twice", ExecutionClass.DETERMINISTIC, Severity.CRITICAL, evaluate_r44))
