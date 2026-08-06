from datetime import date
from decimal import Decimal
from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import Verdict
from projektguard.domain.evidence import EvidenceRecord,EvidenceType,Indicator
from projektguard.domain.models import AuditContext,EligibilityPeriod,ProjectFinancials,SourceRef

def ctx(ind, evidence):
 from projektguard.rules import load_evidence_integrity_rules; load_evidence_integrity_rules()
 return AuditContext(project_id='P',as_of=date(2026,8,6),eligibility=EligibilityPeriod(start=date(2026,1,1),end=date(2026,12,31)),financials=ProjectFinancials(currency='EUR'),indicators=[ind],evidence=evidence)
def src(eid,**facts): return EvidenceRecord(evidence_id=eid,evidence_type=EvidenceType.INDICATOR_REPORT,observed_at=date(2026,8,1),supports_entity_type='indicator',supports_entity_id='I',facts=facts,sources=[SourceRef(document_id=eid)])
def v(c): return run_rule('R40',c,TolerancePolicy())[0].verdict
def test_R40_baseline_target_sourced_verified(): assert v(ctx(Indicator(indicator_id='I',title='x',baseline=Decimal('10'),target=Decimal('20'),unit='%',source_ids=['S']),[src('S',baseline=Decimal('10'),target=Decimal('20'))]))==Verdict.VERIFIED
def test_R40_missing_baseline_unknown(): assert v(ctx(Indicator(indicator_id='I',title='x',target=Decimal('20'),unit='%',source_ids=['S']),[src('S')]))==Verdict.UNKNOWN
def test_R40_unresolved_source_unknown(): assert v(ctx(Indicator(indicator_id='I',title='x',baseline=Decimal('10'),target=Decimal('20'),unit='%',source_ids=['NO']),[]))==Verdict.UNKNOWN
def test_R40_conflicting_target_expert_review(): assert v(ctx(Indicator(indicator_id='I',title='x',baseline=Decimal('10'),target=Decimal('20'),unit='%',source_ids=['S1','S2']),[src('S1',target=Decimal('20')),src('S2',target=Decimal('21'))]))==Verdict.EXPERT_REVIEW
