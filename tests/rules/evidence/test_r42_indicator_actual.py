from datetime import date
from decimal import Decimal
from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import Verdict
from projektguard.domain.evidence import EvidenceRecord,EvidenceType,Indicator
from projektguard.domain.models import AuditContext,EligibilityPeriod,ProjectFinancials,SourceRef

def ctx(actual='52.24',value='52.24',method='direct',etype=EvidenceType.ENERGY_AUDIT):
 from projektguard.rules import load_evidence_integrity_rules; load_evidence_integrity_rules()
 ind=Indicator(indicator_id='I',title='x',unit='%',actual=Decimal(actual) if actual is not None else None,required_evidence_types=[EvidenceType.ENERGY_AUDIT],calculation_method=method)
 ev=[] if value is None else [EvidenceRecord(evidence_id='E',evidence_type=etype,observed_at=date(2026,8,1),supports_entity_type='indicator',supports_entity_id='I',facts={'actual_value':Decimal(value)},sources=[SourceRef(document_id='audit')])]
 return AuditContext(project_id='P',as_of=date(2026,8,6),eligibility=EligibilityPeriod(start=date(2026,1,1),end=date(2026,12,31)),financials=ProjectFinancials(currency='EUR'),indicators=[ind],evidence=ev)
def v(c): return run_rule('R42',c,TolerancePolicy())[0].verdict
def test_R42_direct_actual_supported_verified(): assert v(ctx())==Verdict.VERIFIED
def test_R42_direct_actual_conflict_warning(): assert v(ctx(value='50'))==Verdict.WARNING
def test_R42_missing_actual_unknown(): assert v(ctx(actual=None))==Verdict.UNKNOWN
def test_R42_missing_prescribed_evidence_unknown(): assert v(ctx(value=None))==Verdict.UNKNOWN
def test_R42_unsupported_method_expert_review(): assert v(ctx(method='energy_audit_formula_v2'))==Verdict.EXPERT_REVIEW
