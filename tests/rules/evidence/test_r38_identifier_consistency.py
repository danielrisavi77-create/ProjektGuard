from datetime import date
from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import Verdict
from projektguard.domain.evidence import EvidenceRecord,EvidenceType,ExecutionRecord
from projektguard.domain.models import AuditContext,EligibilityPeriod,ProjectFinancials,SourceRef

def context(executions, facts):
 from projektguard.rules import load_evidence_integrity_rules; load_evidence_integrity_rules()
 ev=[EvidenceRecord(evidence_id='REQ-'+x.execution_id,evidence_type=EvidenceType.EXECUTION_REPORT,observed_at=date(2026,8,1),supports_entity_type='execution',supports_entity_id=x.execution_id,facts=facts.get(x.execution_id,{}),sources=[SourceRef(document_id='spec')]) for x in executions]
 return AuditContext(project_id='P',as_of=date(2026,8,6),eligibility=EligibilityPeriod(start=date(2026,1,1),end=date(2026,12,31)),financials=ProjectFinancials(currency='EUR'),executions=executions,evidence=ev)
def test_R38_matching_serial_model_verified():
 fs=run_rule('R38',context([ExecutionRecord(execution_id='X',model='M1',serial_number='S1')],{'X':{'expected_model':'m1','expected_serial_number':'s1'}}),TolerancePolicy()); assert fs[0].verdict==Verdict.VERIFIED
def test_R38_serial_mismatch_warning():
 fs=run_rule('R38',context([ExecutionRecord(execution_id='X',serial_number='S2')],{'X':{'expected_serial_number':'S1'}}),TolerancePolicy()); assert fs[0].verdict==Verdict.WARNING
def test_R38_required_serial_missing_unknown():
 fs=run_rule('R38',context([ExecutionRecord(execution_id='X')],{'X':{'expected_serial_number':'S1'}}),TolerancePolicy()); assert fs[0].verdict==Verdict.UNKNOWN
def test_R38_duplicate_serial_across_executions_warning():
 xs=[ExecutionRecord(execution_id='X1',serial_number='S1'),ExecutionRecord(execution_id='X2',serial_number='S1')]
 fs=run_rule('R38',context(xs,{'X1':{'expected_serial_number':'S1'},'X2':{'expected_serial_number':'S1'}}),TolerancePolicy()); assert all(f.verdict==Verdict.WARNING for f in fs)
