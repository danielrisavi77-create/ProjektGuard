from datetime import date
from decimal import Decimal
from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import Verdict
from projektguard.domain.evidence import EvidenceRecord,EvidenceType,Indicator,ExecutionRecord
from projektguard.domain.models import AuditContext,EligibilityPeriod,ProjectFinancials,SourceRef

def ctx(actual=None,evidence=None,executions=None):
 from projektguard.rules import load_evidence_integrity_rules; load_evidence_integrity_rules()
 ind=Indicator(indicator_id='I',title='x',unit='%',actual=Decimal(str(actual)) if actual is not None else None,required_evidence_types=[EvidenceType.ENERGY_AUDIT])
 return AuditContext(project_id='P',as_of=date(2026,8,6),eligibility=EligibilityPeriod(start=date(2026,1,1),end=date(2026,12,31)),financials=ProjectFinancials(currency='EUR'),indicators=[ind],evidence=evidence or [],executions=executions or [])
def completion(when=date(2026,8,1)): return EvidenceRecord(evidence_id='C',evidence_type=EvidenceType.PROJECT_COMPLETION,observed_at=when,supports_entity_type='project',supports_entity_id='P',sources=[SourceRef(document_id='completion')])
def audit(): return EvidenceRecord(evidence_id='A',evidence_type=EvidenceType.ENERGY_AUDIT,observed_at=date(2026,8,1),supports_entity_type='indicator',supports_entity_id='I',facts={'actual_value':Decimal('52')},sources=[SourceRef(document_id='audit')])
def v(c): return run_rule('R43',c,TolerancePolicy())[0].verdict
def test_R43_completion_actual_missing_unknown(): assert v(ctx(evidence=[completion()]))==Verdict.UNKNOWN
def test_R43_output_execution_without_indicator_proof_unknown(): assert v(ctx(executions=[ExecutionRecord(execution_id='X')]))==Verdict.UNKNOWN
def test_R43_actual_and_required_evidence_not_applicable(): assert v(ctx(actual=52,evidence=[audit()]))==Verdict.NOT_APPLICABLE
def test_R43_future_completion_does_not_affect_snapshot(): assert v(ctx(evidence=[completion(date(2026,8,7))]))==Verdict.NOT_APPLICABLE
