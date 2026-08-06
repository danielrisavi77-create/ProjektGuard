from datetime import date

from projektguard.domain.models import AuditContext, EligibilityPeriod, ProjectFinancials


def test_audit_context_accepts_empty_evidence_state_without_breaking_financial_core():
    context = AuditContext(
        project_id="P1",
        as_of=date(2026, 8, 6),
        eligibility=EligibilityPeriod(start=date(2026, 1, 1), end=date(2026, 12, 31)),
        financials=ProjectFinancials(currency="EUR"),
    )
    assert context.evidence == []
    assert context.executions == []
    assert context.acceptances == []
    assert context.indicators == []


def test_execution_and_acceptance_models_preserve_decimal_and_unknown_acceptance():
    from decimal import Decimal
    from projektguard.domain.evidence import AcceptanceRecord, AcceptanceType, ExecutionRecord

    execution = ExecutionRecord(execution_id="E1", quantity=Decimal("2.5"), unit="pcs")
    acceptance = AcceptanceRecord(
        acceptance_id="A1",
        execution_id="E1",
        acceptance_type=AcceptanceType.COMMISSIONING,
        accepted=None,
    )
    assert execution.quantity == Decimal("2.5")
    assert acceptance.accepted is None


def test_evidence_record_keeps_traceable_source():
    from projektguard.domain.evidence import EvidenceRecord, EvidenceType
    from projektguard.domain.models import SourceRef

    record = EvidenceRecord(
        evidence_id="EV1",
        evidence_type=EvidenceType.DELIVERY_NOTE,
        observed_at=date(2026, 8, 1),
        supports_entity_type="cost",
        supports_entity_id="C1",
        facts={"item_name": "Pump A"},
        sources=[SourceRef(document_id="delivery-note.pdf", page=1)],
    )
    assert record.sources[0].document_id == "delivery-note.pdf"
