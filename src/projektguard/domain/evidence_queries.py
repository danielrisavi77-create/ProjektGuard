from projektguard.domain.evidence import AcceptanceRecord, EvidenceRecord, EvidenceType, ExecutionRecord, Indicator
from projektguard.domain.models import AuditContext


def observable_evidence(context: AuditContext) -> list[EvidenceRecord]:
    return [row for row in context.evidence if row.observed_at is not None and row.observed_at <= context.as_of]


def evidence_for(context: AuditContext, *, entity_type: str, entity_id: str, evidence_types: set[EvidenceType] | None = None) -> list[EvidenceRecord]:
    rows = [row for row in observable_evidence(context) if row.supports_entity_type == entity_type and row.supports_entity_id == entity_id]
    if evidence_types is not None:
        rows = [row for row in rows if row.evidence_type in evidence_types]
    return rows


def evidence_by_id(context: AuditContext, evidence_id: str) -> EvidenceRecord | None:
    return next((row for row in observable_evidence(context) if row.evidence_id == evidence_id), None)


def execution_for_cost(context: AuditContext, cost_id: str) -> list[ExecutionRecord]:
    return [row for row in context.executions if row.related_cost_id == cost_id]


def acceptances_for_execution(context: AuditContext, execution_id: str) -> list[AcceptanceRecord]:
    return [row for row in context.acceptances if row.execution_id == execution_id]


def indicator_by_id(context: AuditContext, indicator_id: str) -> Indicator | None:
    return next((row for row in context.indicators if row.indicator_id == indicator_id), None)


def sourced_observable_evidence_ids(context: AuditContext, evidence_ids: list[str]) -> list[EvidenceRecord]:
    result = []
    for evidence_id in evidence_ids:
        row = evidence_by_id(context, evidence_id)
        if row is not None and row.sources:
            result.append(row)
    return result
