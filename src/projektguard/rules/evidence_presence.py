from projektguard.audit.finding import Finding
from projektguard.audit.registry import Rule, register_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import ExecutionClass, Severity, Verdict
from projektguard.domain.evidence import EvidenceType
from projektguard.domain.evidence_queries import evidence_by_id, evidence_for
from projektguard.domain.models import AuditContext

_EXECUTION_TYPES = {EvidenceType.DELIVERY_NOTE, EvidenceType.EXECUTION_REPORT}


def _has_observable_source(row, context: AuditContext) -> bool:
    return any(source.available_from is None or source.available_from <= context.as_of for source in row.sources)


def evaluate_r35(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    costs = context.observable_costs()
    if context.claimed_cost_ids:
        wanted = set(context.claimed_cost_ids)
        costs = [cost for cost in costs if cost.cost_id in wanted]
    if not costs:
        return [Finding(rule_id="R35", verdict=Verdict.NOT_APPLICABLE, severity=Severity.HIGH, reason_code="NO_RELEVANT_COSTS", message="No observable relevant costs require execution evidence.")]
    findings = []
    for cost in costs:
        rows = evidence_for(context, entity_type="cost", entity_id=cost.cost_id, evidence_types=_EXECUTION_TYPES)
        sourced = [row for row in rows if _has_observable_source(row, context)]
        ok = bool(sourced)
        findings.append(Finding(rule_id="R35", verdict=Verdict.VERIFIED if ok else Verdict.UNKNOWN, severity=Severity.HIGH, reason_code="EXECUTION_EVIDENCE_PRESENT" if ok else "EXECUTION_EVIDENCE_NOT_AVAILABLE", message="Observable sourced execution evidence exists." if ok else "Required execution evidence is not available at the audit cutoff.", subject_type="cost", subject_id=cost.cost_id, sources=[source for row in sourced for source in row.sources]))
    return findings


def evaluate_r39(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    if not context.executions:
        return [Finding(rule_id="R39", verdict=Verdict.NOT_APPLICABLE, severity=Severity.HIGH, reason_code="NO_EXECUTIONS", message="No execution records require acceptance testing.")]
    findings = []
    for execution in context.executions:
        records = [row for row in context.acceptances if row.execution_id == execution.execution_id]
        if not records:
            findings.append(Finding(rule_id="R39", verdict=Verdict.UNKNOWN, severity=Severity.HIGH, reason_code="ACCEPTANCE_NOT_AVAILABLE", message="Acceptance or commissioning record is not available.", subject_type="execution", subject_id=execution.execution_id))
            continue
        record = records[-1]
        evidence = [row for evidence_id in record.evidence_ids if (row := evidence_by_id(context, evidence_id)) is not None and _has_observable_source(row, context)]
        sources = [source for row in evidence for source in row.sources]
        if not evidence:
            verdict, reason, message = Verdict.UNKNOWN, "ACCEPTANCE_EVIDENCE_NOT_AVAILABLE", "Acceptance state lacks observable sourced evidence."
        elif record.accepted is None:
            verdict, reason, message = Verdict.UNKNOWN, "ACCEPTANCE_STATE_UNKNOWN", "Acceptance state is unknown."
        elif record.accepted:
            verdict, reason, message = Verdict.VERIFIED, "ACCEPTANCE_CONFIRMED", "Acceptance or commissioning is confirmed."
        else:
            verdict, reason, message = Verdict.WARNING, "ACCEPTANCE_REJECTED", "Acceptance or commissioning is explicitly rejected."
        findings.append(Finding(rule_id="R39", verdict=verdict, severity=Severity.HIGH, reason_code=reason, message=message, subject_type="execution", subject_id=execution.execution_id, sources=sources))
    return findings


register_rule(Rule("R35", "Required execution or delivery evidence exists", ExecutionClass.EVIDENCE, Severity.HIGH, evaluate_r35))
register_rule(Rule("R39", "Required acceptance or commissioning evidence exists", ExecutionClass.EVIDENCE, Severity.HIGH, evaluate_r39))
