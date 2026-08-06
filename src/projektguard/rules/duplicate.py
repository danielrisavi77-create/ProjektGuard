from collections import Counter, defaultdict

from projektguard.audit.finding import Finding
from projektguard.audit.registry import Rule, register_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import ExecutionClass, Severity, Verdict
from projektguard.domain.models import AuditContext, Cost


def _norm_invoice(cost: Cost) -> str:
    return cost.invoice_number.strip().casefold()


def _duplicate_groups(costs: list[Cost]) -> tuple[list[list[str]], bool]:
    by_hash: dict[str, list[str]] = defaultdict(list)
    by_supplier_invoice: dict[tuple[str, str], list[str]] = defaultdict(list)
    invoice_to_costs: dict[str, list[Cost]] = defaultdict(list)
    for cost in costs:
        invoice = _norm_invoice(cost)
        if invoice:
            invoice_to_costs[invoice].append(cost)
        if cost.document_hash:
            by_hash[cost.document_hash].append(cost.cost_id)
        if cost.supplier_id and invoice:
            by_supplier_invoice[(cost.supplier_id.strip().casefold(), invoice)].append(cost.cost_id)

    groups: list[list[str]] = []
    seen = set()
    for ids in [*by_hash.values(), *by_supplier_invoice.values()]:
        if len(ids) > 1:
            key = tuple(sorted(ids))
            if key not in seen:
                groups.append(list(key))
                seen.add(key)

    identity_incomplete = any(
        len(items) > 1 and not all(item.supplier_id for item in items)
        for items in invoice_to_costs.values()
    )
    return groups, identity_incomplete


def evaluate_r26(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    costs = context.observable_costs()
    if not costs or not any(_norm_invoice(cost) for cost in costs):
        return [Finding(rule_id="R26", verdict=Verdict.UNKNOWN, severity=Severity.CRITICAL,
                        reason_code="INVOICE_DATA_UNKNOWN", message="No observable invoice identity is available.")]
    groups, identity_incomplete = _duplicate_groups(costs)
    if groups:
        ids = sorted({cost_id for group in groups for cost_id in group})
        return [Finding(
            rule_id="R26", verdict=Verdict.WARNING, severity=Severity.CRITICAL,
            reason_code="DUPLICATE_INVOICE_IDENTITY", message="Duplicate invoice identity detected.",
            facts={"duplicate_cost_ids": ids},
            sources=[source for cost in costs if cost.cost_id in ids for source in cost.sources],
        )]
    if identity_incomplete:
        return [Finding(
            rule_id="R26", verdict=Verdict.UNKNOWN, severity=Severity.CRITICAL,
            reason_code="DUPLICATE_INVOICE_IDENTITY_INCOMPLETE",
            message="Repeated invoice numbers cannot be resolved because supplier/document identity is incomplete.",
        )]
    return [Finding(
        rule_id="R26", verdict=Verdict.VERIFIED, severity=Severity.CRITICAL,
        reason_code="INVOICE_IDENTITIES_UNIQUE", message="No duplicate invoice identity is present in the evaluated context.",
        sources=[source for cost in costs for source in cost.sources],
    )]


def evaluate_r44(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    if not context.claimed_cost_ids:
        return [Finding(rule_id="R44", verdict=Verdict.UNKNOWN, severity=Severity.CRITICAL,
                        reason_code="CLAIM_DATA_UNKNOWN", message="No ZNS claim mapping is available.")]
    repeated_ids = sorted(cost_id for cost_id, count in Counter(context.claimed_cost_ids).items() if count > 1)
    costs_by_id = {cost.cost_id: cost for cost in context.observable_costs()}
    missing_claims = sorted({cost_id for cost_id in context.claimed_cost_ids if cost_id not in costs_by_id})
    claimed_costs = [costs_by_id[cost_id] for cost_id in dict.fromkeys(context.claimed_cost_ids) if cost_id in costs_by_id]
    groups, identity_incomplete = _duplicate_groups(claimed_costs)
    duplicate_ids = sorted({*repeated_ids, *(cost_id for group in groups for cost_id in group)})
    if duplicate_ids:
        return [Finding(
            rule_id="R44", verdict=Verdict.WARNING, severity=Severity.CRITICAL,
            reason_code="DUPLICATE_CLAIM_DETECTED", message="The same cost or invoice identity is claimed more than once.",
            facts={"duplicate_cost_ids": duplicate_ids},
            sources=[source for cost in claimed_costs if cost.cost_id in duplicate_ids for source in cost.sources],
        )]
    if missing_claims or identity_incomplete:
        return [Finding(
            rule_id="R44", verdict=Verdict.UNKNOWN, severity=Severity.CRITICAL,
            reason_code="CLAIM_IDENTITY_INCOMPLETE", message="Claim uniqueness cannot be fully verified from available cost identity data.",
            facts={"missing_claimed_cost_ids": missing_claims},
        )]
    return [Finding(
        rule_id="R44", verdict=Verdict.VERIFIED, severity=Severity.CRITICAL,
        reason_code="CLAIMS_UNIQUE", message="No duplicated cost claim is present.",
        sources=[source for cost in claimed_costs for source in cost.sources],
    )]


register_rule(Rule("R26", "Duplicate invoice identity detection", ExecutionClass.DETERMINISTIC, Severity.CRITICAL, evaluate_r26))
register_rule(Rule("R44", "Same invoice is not claimed twice", ExecutionClass.DETERMINISTIC, Severity.CRITICAL, evaluate_r44))
