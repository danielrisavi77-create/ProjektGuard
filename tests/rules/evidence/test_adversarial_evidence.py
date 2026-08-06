from datetime import date
from decimal import Decimal

from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import Verdict
from projektguard.domain.evidence import AcceptanceRecord, AcceptanceType, EvidenceRecord, EvidenceType, ExecutionRecord, Indicator
from projektguard.domain.models import AuditContext, Cost, EligibilityPeriod, ProjectFinancials, SourceRef
from projektguard.rules import load_evidence_integrity_rules

load_evidence_integrity_rules()


def base(**kwargs):
    data=dict(project_id='P',as_of=date(2026,8,6),eligibility=EligibilityPeriod(start=date(2026,1,1),end=date(2026,12,31)),financials=ProjectFinancials(currency='EUR'))
    data.update(kwargs); return AuditContext(**data)

def finding(rule,ctx): return run_rule(rule,ctx,TolerancePolicy())

def test_R35_future_source_cannot_verify():
    c=Cost(cost_id='C',invoice_number='1',invoice_date=date(2026,8,1),amount=Decimal('1'),currency='EUR',budget_line_id='B')
    e=EvidenceRecord(evidence_id='E',evidence_type=EvidenceType.DELIVERY_NOTE,observed_at=date(2026,8,1),supports_entity_type='cost',supports_entity_id='C',sources=[SourceRef(document_id='d',available_from=date(2026,8,7))])
    assert finding('R35',base(costs=[c],claimed_cost_ids=['C'],evidence=[e]))[0].verdict==Verdict.UNKNOWN

def test_R36_second_execution_mismatch_is_visible():
    xs=[ExecutionRecord(execution_id='X1',item_name='A'),ExecutionRecord(execution_id='X2',item_name='B')]
    es=[EvidenceRecord(evidence_id='E1',evidence_type=EvidenceType.EXECUTION_REPORT,observed_at=date(2026,8,1),supports_entity_type='execution',supports_entity_id='X1',facts={'expected_item_name':'A'},sources=[SourceRef(document_id='d')]),EvidenceRecord(evidence_id='E2',evidence_type=EvidenceType.EXECUTION_REPORT,observed_at=date(2026,8,1),supports_entity_type='execution',supports_entity_id='X2',facts={'expected_item_name':'A'},sources=[SourceRef(document_id='d')])]
    fs=finding('R36',base(executions=xs,evidence=es)); assert fs[1].verdict==Verdict.WARNING

def test_R37_equal_numbers_in_different_units_not_verified():
    x=ExecutionRecord(execution_id='X',quantity=Decimal('10'),unit='kg')
    e=EvidenceRecord(evidence_id='E',evidence_type=EvidenceType.EXECUTION_REPORT,observed_at=date(2026,8,1),supports_entity_type='execution',supports_entity_id='X',facts={'expected_quantity':Decimal('10'),'expected_unit':'pcs'},sources=[SourceRef(document_id='d')])
    assert finding('R37',base(executions=[x],evidence=[e]))[0].verdict==Verdict.EXPERT_REVIEW

def test_R38_same_serial_two_assets_warning():
    xs=[ExecutionRecord(execution_id='X1',serial_number='S'),ExecutionRecord(execution_id='X2',serial_number='S')]
    es=[EvidenceRecord(evidence_id='E'+x.execution_id,evidence_type=EvidenceType.EXECUTION_REPORT,observed_at=date(2026,8,1),supports_entity_type='execution',supports_entity_id=x.execution_id,facts={'expected_serial_number':'S'},sources=[SourceRef(document_id='d')]) for x in xs]
    assert all(f.verdict==Verdict.WARNING for f in finding('R38',base(executions=xs,evidence=es)))

def test_R39_unresolved_acceptance_evidence_unknown():
    x=ExecutionRecord(execution_id='X'); a=AcceptanceRecord(acceptance_id='A',execution_id='X',acceptance_type=AcceptanceType.COMMISSIONING,accepted=True,evidence_ids=['MISSING'])
    assert finding('R39',base(executions=[x],acceptances=[a]))[0].verdict==Verdict.UNKNOWN

def test_R40_future_source_cannot_trace_indicator():
    i=Indicator(indicator_id='I',title='x',baseline=Decimal('1'),target=Decimal('2'),unit='%',source_ids=['E'])
    e=EvidenceRecord(evidence_id='E',evidence_type=EvidenceType.INDICATOR_REPORT,observed_at=date(2026,8,1),supports_entity_type='indicator',supports_entity_id='I',sources=[SourceRef(document_id='d',available_from=date(2026,8,7))])
    assert finding('R40',base(indicators=[i],evidence=[e]))[0].verdict==Verdict.UNKNOWN

def test_R41_wrong_evidence_type_unknown():
    i=Indicator(indicator_id='I',title='x',unit='%',required_evidence_types=[EvidenceType.ENERGY_AUDIT])
    e=EvidenceRecord(evidence_id='E',evidence_type=EvidenceType.PROJECT_COMPLETION,observed_at=date(2026,8,1),supports_entity_type='indicator',supports_entity_id='I',sources=[SourceRef(document_id='d')])
    assert finding('R41',base(indicators=[i],evidence=[e]))[0].verdict==Verdict.UNKNOWN

def test_R42_completion_number_cannot_substitute_energy_audit():
    i=Indicator(indicator_id='I',title='x',unit='%',actual=Decimal('52'),required_evidence_types=[EvidenceType.ENERGY_AUDIT],calculation_method='direct')
    e=EvidenceRecord(evidence_id='E',evidence_type=EvidenceType.PROJECT_COMPLETION,observed_at=date(2026,8,1),supports_entity_type='indicator',supports_entity_id='I',facts={'actual_value':Decimal('52')},sources=[SourceRef(document_id='d')])
    assert finding('R42',base(indicators=[i],evidence=[e]))[0].verdict==Verdict.UNKNOWN

def test_R43_target_and_completion_without_actual_stays_unknown():
    i=Indicator(indicator_id='I',title='x',target=Decimal('52'),unit='%')
    e=EvidenceRecord(evidence_id='E',evidence_type=EvidenceType.PROJECT_COMPLETION,observed_at=date(2026,8,1),supports_entity_type='project',supports_entity_id='P',sources=[SourceRef(document_id='d')])
    assert finding('R43',base(indicators=[i],evidence=[e]))[0].verdict==Verdict.UNKNOWN
