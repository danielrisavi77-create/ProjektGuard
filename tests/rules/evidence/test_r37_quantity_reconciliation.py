from datetime import date
from decimal import Decimal
from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import Verdict
from projektguard.domain.evidence import EvidenceRecord,EvidenceType,ExecutionRecord
from projektguard.domain.models import AuditContext,EligibilityPeriod,ProjectFinancials,SourceRef

def ctx(actual='10',unit='pcs',expected='10',expected_unit='pcs'):
 from projektguard.rules import load_evidence_integrity_rules; load_evidence_integrity_rules()
 facts={}
 if expected is not None: facts['expected_quantity']=Decimal(expected)
 if expected_unit is not None: facts['expected_unit']=expected_unit
 ev=[EvidenceRecord(evidence_id='REQ',evidence_type=EvidenceType.EXECUTION_REPORT,observed_at=date(2026,8,1),supports_entity_type='execution',supports_entity_id='X',facts=facts,sources=[SourceRef(document_id='spec')])]
 ex=ExecutionRecord(execution_id='X',quantity=Decimal(actual) if actual is not None else None,unit=unit)
 return AuditContext(project_id='P',as_of=date(2026,8,6),eligibility=EligibilityPeriod(start=date(2026,1,1),end=date(2026,12,31)),financials=ProjectFinancials(currency='EUR'),executions=[ex],evidence=ev)
def v(c): return run_rule('R37',c,TolerancePolicy())[0].verdict
def test_R37_equal_quantity_verified(): assert v(ctx())==Verdict.VERIFIED
def test_R37_mismatch_warning(): assert v(ctx(actual='8'))==Verdict.WARNING
def test_R37_missing_quantity_unknown(): assert v(ctx(actual=None))==Verdict.UNKNOWN
def test_R37_incompatible_units_expert_review(): assert v(ctx(unit='kg',expected_unit='pcs'))==Verdict.EXPERT_REVIEW
