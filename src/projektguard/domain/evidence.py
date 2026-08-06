from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field

from projektguard.domain.source import SourceRef


class EvidenceType(str, Enum):
    DELIVERY_NOTE = "delivery_note"
    EXECUTION_REPORT = "execution_report"
    ACCEPTANCE_RECORD = "acceptance_record"
    COMMISSIONING_RECORD = "commissioning_record"
    ASSET_REGISTER = "asset_register"
    ENERGY_AUDIT = "energy_audit"
    INDICATOR_REPORT = "indicator_report"
    PROJECT_COMPLETION = "project_completion"
    OTHER = "other"


class AcceptanceType(str, Enum):
    DELIVERY_ACCEPTANCE = "delivery_acceptance"
    WORKS_ACCEPTANCE = "works_acceptance"
    COMMISSIONING = "commissioning"


EvidenceScalar = str | int | Decimal | bool | date
EvidenceValue = EvidenceScalar | list[str] | list[int] | list[Decimal]


class EvidenceRecord(BaseModel):
    evidence_id: str
    evidence_type: EvidenceType
    observed_at: date | None = None
    supports_entity_type: str
    supports_entity_id: str
    facts: dict[str, EvidenceValue] = Field(default_factory=dict)
    sources: list[SourceRef] = Field(default_factory=list)


class ExecutionRecord(BaseModel):
    execution_id: str
    related_cost_id: str | None = None
    related_contract_id: str | None = None
    item_name: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    model: str | None = None
    serial_number: str | None = None
    reference: str | None = None
    execution_date: date | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class AcceptanceRecord(BaseModel):
    acceptance_id: str
    execution_id: str
    acceptance_type: AcceptanceType
    accepted: bool | None = None
    acceptance_date: date | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class Indicator(BaseModel):
    indicator_id: str
    title: str
    baseline: Decimal | None = None
    target: Decimal | None = None
    unit: str
    actual: Decimal | None = None
    required_evidence_types: list[EvidenceType] = Field(default_factory=list)
    calculation_method: str | None = None
    source_ids: list[str] = Field(default_factory=list)
