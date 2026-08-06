from datetime import date
from decimal import Decimal

from projektguard.domain.evidence import AcceptanceRecord, AcceptanceType, EvidenceRecord, EvidenceType, ExecutionRecord, Indicator
from projektguard.domain.models import AuditContext, EligibilityPeriod, ProjectFinancials, SourceRef


def context(**kwargs):
    base = dict(project_id='P', as_of=date(2026,8,6), eligibility=EligibilityPeriod(start=date(2026,1,1), end=date(2026,12,31)), financials=ProjectFinancials(currency='EUR'))
    base.update(kwargs)
    return AuditContext(**base)


def test_evidence_after_cutoff_is_not_observable():
    from projektguard.domain.evidence_queries import observable_evidence
    ctx = context(evidence=[EvidenceRecord(evidence_id='EV', evidence_type=EvidenceType.DELIVERY_NOTE, observed_at=date(2026,8,7), supports_entity_type='cost', supports_entity_id='C', sources=[SourceRef(document_id='d')])])
    assert observable_evidence(ctx) == []


def test_evidence_without_observation_date_is_not_observable():
    from projektguard.domain.evidence_queries import observable_evidence
    ctx = context(evidence=[EvidenceRecord(evidence_id='EV', evidence_type=EvidenceType.DELIVERY_NOTE, supports_entity_type='cost', supports_entity_id='C')])
    assert observable_evidence(ctx) == []


def test_evidence_for_filters_entity_and_type():
    from projektguard.domain.evidence_queries import evidence_for
    rows = [
        EvidenceRecord(evidence_id='EV1', evidence_type=EvidenceType.DELIVERY_NOTE, observed_at=date(2026,8,1), supports_entity_type='cost', supports_entity_id='C1'),
        EvidenceRecord(evidence_id='EV2', evidence_type=EvidenceType.EXECUTION_REPORT, observed_at=date(2026,8,1), supports_entity_type='cost', supports_entity_id='C1'),
        EvidenceRecord(evidence_id='EV3', evidence_type=EvidenceType.DELIVERY_NOTE, observed_at=date(2026,8,1), supports_entity_type='cost', supports_entity_id='C2'),
    ]
    result = evidence_for(context(evidence=rows), entity_type='cost', entity_id='C1', evidence_types={EvidenceType.DELIVERY_NOTE})
    assert [r.evidence_id for r in result] == ['EV1']


def test_link_helpers_return_related_objects():
    from projektguard.domain.evidence_queries import acceptances_for_execution, execution_for_cost, indicator_by_id
    ex=ExecutionRecord(execution_id='X', related_cost_id='C')
    ac=AcceptanceRecord(acceptance_id='A', execution_id='X', acceptance_type=AcceptanceType.COMMISSIONING)
    ind=Indicator(indicator_id='I', title='Savings', unit='%')
    ctx=context(executions=[ex], acceptances=[ac], indicators=[ind])
    assert execution_for_cost(ctx,'C') == [ex]
    assert acceptances_for_execution(ctx,'X') == [ac]
    assert indicator_by_id(ctx,'I') == ind
