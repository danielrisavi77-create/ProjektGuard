from datetime import date
from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import Verdict
from projektguard.domain.evidence import EvidenceRecord,EvidenceType,ExecutionRecord
from projektguard.domain.models import AuditContext,EligibilityPeriod,ProjectFinancials,SourceRef

def ctx(item='Pump A',expected='Pump A'):
 from projektguard.rules import load_evidence_integrity_rules; load_evidence_integrity_rules()
 ev=[] if expected is None else [EvidenceRecord(evidence_id='REQ',evidence_type=EvidenceType.EXECUTION_REPORT,observed_at=date(2026,8,1),supports_entity_type='execution',supports_entity_id='X',facts={'expected_item_name':expected},sources=[SourceRef(document_id='spec')])]
 return AuditContext(project_id='P',as_of=date(2026,8,6),eligibility=EligibilityPeriod(start=date(2026,1,1),end=date(2026,12,31)),financials=ProjectFinancials(currency='EUR'),executions=[ExecutionRecord(execution_id='X',item_name=item)],evidence=ev)
def v(c): return run_rule('R36',c,TolerancePolicy())[0].verdict
def test_R36_normalized_exact_match_verified(): assert v(ctx(' pump a ','Pump A'))==Verdict.VERIFIED
def test_R36_mismatch_warning(): assert v(ctx('Pump B','Pump A'))==Verdict.WARNING
def test_R36_missing_expected_unknown(): assert v(ctx('Pump A',None))==Verdict.UNKNOWN
def test_R36_missing_actual_unknown(): assert v(ctx(None,'Pump A'))==Verdict.UNKNOWN
