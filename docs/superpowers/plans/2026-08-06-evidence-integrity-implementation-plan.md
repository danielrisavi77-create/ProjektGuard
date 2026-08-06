# Evidence Integrity Slice v0.2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement deterministic Evidence Integrity rules `R35`–`R43` on top of the merged Financial Integrity Core, with a repeatable automated TDD pipeline that blocks commits/PR readiness when focused tests, adversarial tests, regression coverage, the Financial benchmark, or the Evidence benchmark fail.

**Architecture:** Extend `AuditContext` with first-class normalized evidence, execution, acceptance, and indicator objects. Rules consume only normalized structured facts; OCR/LLM ingestion remains outside this slice. Development is driven by reusable `rule_gate` and `slice_gate` modules so local development and GitHub CI execute the same gates.

**Tech Stack:** Python 3.12, Pydantic v2, `Decimal`, pytest, pytest-cov, GitHub Actions.

## Global Constraints

- Missing evidence returns `UNKNOWN`, not failure.
- Deterministic contradictions may return `WARNING`.
- Interpretative or unsupported calculations return `EXPERT_REVIEW`.
- `VERIFIED` requires sufficient structured evidence and traceable source(s).
- Evidence observed after `AuditContext.as_of` is unavailable.
- Completion of a project/output never proves indicator achievement.
- No OCR, PDF parsing, LLM extraction, embeddings, database, UI, or upload workflow in Slice 2.
- Existing Financial Integrity Core behavior must remain backward-compatible.
- `python -m pytest --cov=projektguard --cov-report=term --cov-fail-under=90` must remain green.
- `projektguard-benchmark --manifest benchmark/financial_integrity_core/manifest.json` must remain green.
- Every new rule must pass focused RED/GREEN, adversarial hardening, full regression, and Evidence benchmark gates before it is considered complete.

---

## File Structure

### New domain/evidence files

- `src/projektguard/domain/evidence.py` — evidence enums/models: `EvidenceType`, `AcceptanceType`, `EvidenceRecord`, `ExecutionRecord`, `AcceptanceRecord`, `Indicator`.
- `src/projektguard/domain/evidence_queries.py` — temporal/query helpers over evidence state.

### New rule files

- `src/projektguard/rules/evidence_presence.py` — R35, R39.
- `src/projektguard/rules/evidence_reconciliation.py` — R36, R37, R38.
- `src/projektguard/rules/indicator.py` — R40, R41, R42, R43.

### Automated development gates

- `src/projektguard/dev/__init__.py`
- `src/projektguard/dev/rule_gate.py` — focused rule test + rule-specific adversarial test runner.
- `src/projektguard/dev/slice_gate.py` — full Evidence slice gate, full pytest coverage, Financial benchmark, Evidence benchmark.

### Evidence benchmark

- `benchmark/evidence_integrity/manifest.json`
- `benchmark/evidence_integrity/fixtures/synthetic/*.json`
- `benchmark/evidence_integrity/fixtures/retrospective/*.json`
- `src/projektguard/benchmark/evidence_cli.py`
- `src/projektguard/benchmark/evidence_evaluator.py`
- `docs/benchmark-evidence-integrity.md`

### Tests

- `tests/domain/test_evidence_models.py`
- `tests/domain/test_evidence_queries.py`
- `tests/dev/test_rule_gate.py`
- `tests/dev/test_slice_gate.py`
- `tests/rules/evidence/test_r35_execution_evidence.py`
- `tests/rules/evidence/test_r36_item_match.py`
- `tests/rules/evidence/test_r37_quantity_reconciliation.py`
- `tests/rules/evidence/test_r38_identifier_consistency.py`
- `tests/rules/evidence/test_r39_acceptance.py`
- `tests/rules/evidence/test_r40_indicator_traceability.py`
- `tests/rules/evidence/test_r41_indicator_evidence.py`
- `tests/rules/evidence/test_r42_indicator_actual.py`
- `tests/rules/evidence/test_r43_completion_not_achievement.py`
- `tests/rules/evidence/test_adversarial_evidence.py`
- `tests/benchmark/test_evidence_benchmark.py`

---

### Task 1: Evidence domain model and backward-compatible AuditContext extension

**Files:**
- Create: `src/projektguard/domain/evidence.py`
- Modify: `src/projektguard/domain/models.py`
- Test: `tests/domain/test_evidence_models.py`

**Interfaces:**
- Produces: `EvidenceType`, `AcceptanceType`, `EvidenceRecord`, `ExecutionRecord`, `AcceptanceRecord`, `Indicator`.
- Extends: `AuditContext.evidence`, `AuditContext.executions`, `AuditContext.acceptances`, `AuditContext.indicators`, all with empty-list defaults.

- [ ] **Step 1: Write failing model tests**

Test exact behavior:

```python
from datetime import date
from decimal import Decimal

from projektguard.domain.evidence import (
    AcceptanceRecord,
    AcceptanceType,
    EvidenceRecord,
    EvidenceType,
    ExecutionRecord,
)
from projektguard.domain.models import AuditContext, EligibilityPeriod, ProjectFinancials, SourceRef


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
```

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/domain/test_evidence_models.py -q
```

Expected: FAIL because `projektguard.domain.evidence` and the new `AuditContext` collections do not exist.

- [ ] **Step 3: Implement minimal models**

Implement enums with at least:

```python
class EvidenceType(str, Enum):
    DELIVERY_NOTE = "delivery_note"
    EXECUTION_REQUIREMENT = "execution_requirement"
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
```

Use `dict[str, str | int | Decimal | bool | date | list[str] | list[int] | list[Decimal]]` for `EvidenceRecord.facts`. Do not introduce arbitrary nested objects or free-form model output.

- [ ] **Step 4: Run GREEN + Financial regression**

```bash
python -m pytest tests/domain/test_evidence_models.py -q
python -m pytest tests/rules -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/projektguard/domain/evidence.py src/projektguard/domain/models.py tests/domain/test_evidence_models.py
git commit -m "feat: add normalized evidence domain models"
```

---

### Task 2: Temporal evidence query layer

**Files:**
- Create: `src/projektguard/domain/evidence_queries.py`
- Test: `tests/domain/test_evidence_queries.py`

**Interfaces:**
- Produces:
  - `observable_evidence(context: AuditContext) -> list[EvidenceRecord]`
  - `evidence_for(context, *, entity_type: str, entity_id: str, evidence_types: set[EvidenceType] | None = None) -> list[EvidenceRecord]`
  - `execution_for_cost(context, cost_id: str) -> list[ExecutionRecord]`
  - `acceptances_for_execution(context, execution_id: str) -> list[AcceptanceRecord]`
  - `indicator_by_id(context, indicator_id: str) -> Indicator | None`

- [ ] **Step 1: Write failing temporal/query tests**

```python
from datetime import date

from projektguard.domain.evidence import EvidenceRecord, EvidenceType
from projektguard.domain.evidence_queries import evidence_for, observable_evidence
from projektguard.domain.models import AuditContext, EligibilityPeriod, ProjectFinancials, SourceRef


def base_context(*, evidence):
    return AuditContext(
        project_id="P1",
        as_of=date(2026, 8, 6),
        eligibility=EligibilityPeriod(start=date(2026, 1, 1), end=date(2026, 12, 31)),
        financials=ProjectFinancials(currency="EUR"),
        evidence=evidence,
    )


def test_evidence_after_cutoff_is_not_observable():
    future = EvidenceRecord(
        evidence_id="EV-future",
        evidence_type=EvidenceType.DELIVERY_NOTE,
        observed_at=date(2026, 8, 7),
        supports_entity_type="cost",
        supports_entity_id="C1",
        sources=[SourceRef(document_id="future.pdf")],
    )
    context = base_context(evidence=[future])
    assert observable_evidence(context) == []


def test_evidence_without_observation_date_is_not_observable():
    undated = EvidenceRecord(
        evidence_id="EV-undated",
        evidence_type=EvidenceType.DELIVERY_NOTE,
        observed_at=None,
        supports_entity_type="cost",
        supports_entity_id="C1",
        sources=[SourceRef(document_id="undated.pdf")],
    )
    context = base_context(evidence=[undated])
    assert observable_evidence(context) == []


def test_evidence_for_filters_by_entity_and_type():
    delivery = EvidenceRecord(
        evidence_id="EV-delivery",
        evidence_type=EvidenceType.DELIVERY_NOTE,
        observed_at=date(2026, 8, 1),
        supports_entity_type="cost",
        supports_entity_id="C1",
        sources=[SourceRef(document_id="delivery.pdf")],
    )
    completion = EvidenceRecord(
        evidence_id="EV-completion",
        evidence_type=EvidenceType.PROJECT_COMPLETION,
        observed_at=date(2026, 8, 1),
        supports_entity_type="project",
        supports_entity_id="P1",
        sources=[SourceRef(document_id="completion.pdf")],
    )
    context = base_context(evidence=[delivery, completion])
    result = evidence_for(
        context,
        entity_type="cost",
        entity_id="C1",
        evidence_types={EvidenceType.DELIVERY_NOTE},
    )
    assert [row.evidence_id for row in result] == ["EV-delivery"]
```

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/domain/test_evidence_queries.py -q
```

Expected: FAIL because query helpers do not exist.

- [ ] **Step 3: Implement only deterministic filtering**

Rules:

```text
record.observed_at is None -> not observable for deterministic verification
record.observed_at <= context.as_of -> observable
record.observed_at > context.as_of -> unavailable
```

Execution/acceptance objects are linked by IDs; evidence observability is resolved through their `evidence_ids` when rules need source proof.

- [ ] **Step 4: Run GREEN**

```bash
python -m pytest tests/domain/test_evidence_queries.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/projektguard/domain/evidence_queries.py tests/domain/test_evidence_queries.py
git commit -m "feat: add temporal evidence query helpers"
```

---

### Task 3: Automated per-rule and full-slice TDD gates

**Files:**
- Create: `src/projektguard/dev/__init__.py`
- Create: `src/projektguard/dev/rule_gate.py`
- Create: `src/projektguard/dev/slice_gate.py`
- Test: `tests/dev/test_rule_gate.py`
- Test: `tests/dev/test_slice_gate.py`

**Interfaces:**
- CLI/module: `python -m projektguard.dev.rule_gate R35`
- CLI/module: `python -m projektguard.dev.slice_gate evidence-integrity`
- Exit code `0` only if all required subprocesses succeed.

**Rule-to-test map:**

```python
RULE_TESTS = {
    "R35": "tests/rules/evidence/test_r35_execution_evidence.py",
    "R36": "tests/rules/evidence/test_r36_item_match.py",
    "R37": "tests/rules/evidence/test_r37_quantity_reconciliation.py",
    "R38": "tests/rules/evidence/test_r38_identifier_consistency.py",
    "R39": "tests/rules/evidence/test_r39_acceptance.py",
    "R40": "tests/rules/evidence/test_r40_indicator_traceability.py",
    "R41": "tests/rules/evidence/test_r41_indicator_evidence.py",
    "R42": "tests/rules/evidence/test_r42_indicator_actual.py",
    "R43": "tests/rules/evidence/test_r43_completion_not_achievement.py",
}
```

After `tests/rules/evidence/test_adversarial_evidence.py` exists, `rule_gate` must also run it with `-k <RULE_ID>`. Adversarial test names must include the uppercase rule ID, for example `test_R35_second_cost_without_evidence_is_unknown`.

- [ ] **Step 1: Write failing gate tests using monkeypatched subprocess**

Test that `rule_gate`:
- rejects unknown rule IDs with non-zero exit;
- runs the focused test path for the requested rule;
- stops and returns non-zero if focused pytest fails;
- when the adversarial file exists, runs `pytest tests/rules/evidence/test_adversarial_evidence.py -q -k R35` for R35;
- returns zero only when every configured command returns zero.

Test that `slice_gate` executes exactly these five stages, in order:

```text
1. focused evidence rule files excluding test_adversarial_evidence.py
2. tests/rules/evidence/test_adversarial_evidence.py
3. full pytest with coverage >= 90
4. Financial benchmark
5. Evidence benchmark
```

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/dev -q
```

- [ ] **Step 3: Implement subprocess runner**

Use `subprocess.run(command, check=False)` and propagate the first non-zero return code. Print the stage name before execution so CI logs reveal the exact failing gate.

Before Task 11 creates the adversarial file, `rule_gate` may skip the adversarial command only when `Path("tests/rules/evidence/test_adversarial_evidence.py").exists()` is false. After the file exists, a failure in that command must block the gate.

- [ ] **Step 4: Run GREEN**

```bash
python -m pytest tests/dev -q
```

- [ ] **Step 5: Commit**

```bash
git add src/projektguard/dev tests/dev
git commit -m "feat: automate Evidence Integrity TDD gates"
```

---

### Task 4: R35 and R39 — evidence existence and acceptance state

**Files:**
- Create: `src/projektguard/rules/evidence_presence.py`
- Modify: `src/projektguard/rules/__init__.py`
- Test: `tests/rules/evidence/test_r35_execution_evidence.py`
- Test: `tests/rules/evidence/test_r39_acceptance.py`

**Interfaces:**
- Registers `R35` and `R39` in the existing rule registry.
- Findings remain entity-scoped with `subject_type`/`subject_id`.
- R35 evidence requirement is represented by observable `EvidenceRecord` entries of type `EXECUTION_REQUIREMENT` linked to the cost/contract. The requirement record may contain `facts["required_types"]` as a list of evidence-type string values.

- [ ] **Step 1: RED for R35**

Required tests:
- observable requirement + required delivery/execution evidence with source -> `VERIFIED`;
- requirement known but required evidence absent -> `UNKNOWN`;
- required evidence exists only after cutoff -> `UNKNOWN`;
- two costs where only the second lacks evidence -> findings include an `UNKNOWN` for the second cost.

Run:

```bash
python -m pytest tests/rules/evidence/test_r35_execution_evidence.py -q
```

Expected: FAIL because R35 is not registered.

- [ ] **Step 2: Minimal R35 GREEN**

Do not infer non-delivery from missing evidence. Source-less evidence cannot produce `VERIFIED`.

```bash
python -m projektguard.dev.rule_gate R35
```

Expected: PASS.

- [ ] **Step 3: RED for R39**

Required tests:
- `accepted=True` + observable acceptance evidence -> `VERIFIED`;
- acceptance record missing -> `UNKNOWN`;
- `accepted=None` -> `UNKNOWN`;
- `accepted=False` -> `WARNING`;
- acceptance evidence after cutoff -> `UNKNOWN`.

- [ ] **Step 4: Minimal R39 GREEN**

```bash
python -m projektguard.dev.rule_gate R39
```

- [ ] **Step 5: Commit**

```bash
git add src/projektguard/rules/evidence_presence.py src/projektguard/rules/__init__.py tests/rules/evidence/test_r35_execution_evidence.py tests/rules/evidence/test_r39_acceptance.py
git commit -m "feat: add evidence presence and acceptance rules"
```

---

### Task 5: R36 and R37 — item identity and quantity reconciliation

**Files:**
- Create: `src/projektguard/rules/evidence_reconciliation.py`
- Test: `tests/rules/evidence/test_r36_item_match.py`
- Test: `tests/rules/evidence/test_r37_quantity_reconciliation.py`

**Interfaces:**
- Expected identity/quantity comes from observable linked `EXECUTION_REQUIREMENT` evidence facts: `expected_item_name`, `expected_quantity`, `unit`.
- Actual identity/quantity comes from `ExecutionRecord.item_name`, `quantity`, and `unit`.
- R36 compares exact normalized strings only.
- R37 compares `Decimal` quantities only when units are identical after `strip().lower()` normalization.

- [ ] **Step 1: RED for R36**

Tests:
- exact normalized match (`"Pump A"` vs `" pump a "`) -> `VERIFIED`;
- deterministic mismatch -> `WARNING`;
- expected or executed identity missing -> `UNKNOWN`;
- second execution mismatches while first matches -> findings include the second `WARNING`.

- [ ] **Step 2: Minimal R36 GREEN**

No fuzzy similarity. No substring matching. No LLM semantic matching.

```bash
python -m projektguard.dev.rule_gate R36
```

- [ ] **Step 3: RED for R37**

Tests:
- 10 pcs expected / 10 pcs delivered -> `VERIFIED`;
- 10 pcs / 8 pcs -> `WARNING`;
- quantity missing -> `UNKNOWN`;
- `pcs` vs `kg` with both quantities known -> `EXPERT_REVIEW`;
- future requirement/evidence cannot reconcile a current quantity.

- [ ] **Step 4: Minimal R37 GREEN**

Use exact `Decimal` equality in v0.2. Do not reuse the financial absolute/relative money tolerance for physical quantities.

```bash
python -m projektguard.dev.rule_gate R37
```

- [ ] **Step 5: Commit**

```bash
git add src/projektguard/rules/evidence_reconciliation.py tests/rules/evidence/test_r36_item_match.py tests/rules/evidence/test_r37_quantity_reconciliation.py
git commit -m "feat: add item and quantity evidence reconciliation"
```

---

### Task 6: R38 — model/serial/reference consistency

**Files:**
- Modify: `src/projektguard/rules/evidence_reconciliation.py`
- Test: `tests/rules/evidence/test_r38_identifier_consistency.py`

- [ ] **Step 1: RED**

Tests:
- expected serial/model from `EXECUTION_REQUIREMENT` exactly matches execution -> `VERIFIED`;
- model mismatch -> `WARNING`;
- serial mismatch -> `WARNING`;
- required serial missing -> `UNKNOWN`;
- duplicate same serial across two different executions -> `WARNING` for both involved subjects;
- one matching identifier must not verify a second execution with missing identity.

- [ ] **Step 2: GREEN**

Normalize identifiers with whitespace trimming and case folding only. Preserve original values in `Finding.facts`.

```bash
python -m projektguard.dev.rule_gate R38
```

- [ ] **Step 3: Commit**

```bash
git add src/projektguard/rules/evidence_reconciliation.py tests/rules/evidence/test_r38_identifier_consistency.py
git commit -m "feat: add execution identifier consistency rule"
```

---

### Task 7: R40 — indicator baseline and target traceability

**Files:**
- Create: `src/projektguard/rules/indicator.py`
- Test: `tests/rules/evidence/test_r40_indicator_traceability.py`

- [ ] **Step 1: RED**

Tests:
- baseline + target + at least one observable source ID resolving to sourced evidence -> `VERIFIED`;
- baseline missing -> `UNKNOWN`;
- target missing -> `UNKNOWN`;
- source ID missing/unresolvable -> `UNKNOWN`;
- two observable evidence records referenced by `Indicator.source_ids` provide contradictory `baseline` or `target` facts -> `EXPERT_REVIEW`.

- [ ] **Step 2: GREEN**

R40 must never choose between contradictory sourced indicator values. It must return `EXPERT_REVIEW` with all conflicting facts/sources.

```bash
python -m projektguard.dev.rule_gate R40
```

- [ ] **Step 3: Commit**

```bash
git add src/projektguard/rules/indicator.py tests/rules/evidence/test_r40_indicator_traceability.py
git commit -m "feat: add indicator traceability rule"
```

---

### Task 8: R41 — prescribed indicator evidence type

**Files:**
- Modify: `src/projektguard/rules/indicator.py`
- Test: `tests/rules/evidence/test_r41_indicator_evidence.py`

- [ ] **Step 1: RED**

Tests:
- indicator requires `ENERGY_AUDIT`, observable sourced energy audit exists and supports that indicator -> `VERIFIED`;
- only `PROJECT_COMPLETION` evidence exists -> `UNKNOWN`;
- required evidence type exists only after cutoff -> `UNKNOWN`;
- multiple required types where only one is present -> `UNKNOWN`;
- evidence record exists but has no source -> `UNKNOWN`.

- [ ] **Step 2: GREEN**

All values in `indicator.required_evidence_types` must be satisfied. A generic evidence type cannot substitute for a prescribed one.

```bash
python -m projektguard.dev.rule_gate R41
```

- [ ] **Step 3: Commit**

```bash
git add src/projektguard/rules/indicator.py tests/rules/evidence/test_r41_indicator_evidence.py
git commit -m "feat: validate prescribed indicator evidence"
```

---

### Task 9: R42 — actual indicator value supported by evidence

**Files:**
- Modify: `src/projektguard/rules/indicator.py`
- Test: `tests/rules/evidence/test_r42_indicator_actual.py`

**v0.2 deterministic calculation contract:**
- `calculation_method in {None, "direct"}`: evidence fact `actual_value` may be compared directly with `Indicator.actual` as `Decimal`.
- Any other non-empty method: `EXPERT_REVIEW` in v0.2.

- [ ] **Step 1: RED**

Tests:
- actual=52.24, prescribed sourced evidence `actual_value=52.24`, direct method -> `VERIFIED`;
- actual conflicts with sourced direct evidence -> `WARNING`;
- actual missing -> `UNKNOWN`;
- required evidence absent -> `UNKNOWN`;
- `calculation_method="energy_audit_formula_v2"` -> `EXPERT_REVIEW`, not guessed arithmetic.

- [ ] **Step 2: GREEN**

Use `Decimal(str(value))` only for evidence numeric values that pass model validation. Never compare binary floats.

```bash
python -m projektguard.dev.rule_gate R42
```

- [ ] **Step 3: Commit**

```bash
git add src/projektguard/rules/indicator.py tests/rules/evidence/test_r42_indicator_actual.py
git commit -m "feat: validate supported indicator actual values"
```

---

### Task 10: R43 — completion never implies indicator achievement

**Files:**
- Modify: `src/projektguard/rules/indicator.py`
- Test: `tests/rules/evidence/test_r43_completion_not_achievement.py`

- [ ] **Step 1: RED**

Tests:
- observable project completion evidence + indicator actual missing -> `UNKNOWN`;
- output execution exists + no prescribed indicator evidence -> `UNKNOWN`;
- actual + required evidence is present and internally supported -> R43 returns `NOT_APPLICABLE` because the unsafe inference condition does not exist;
- project completion evidence after cutoff does not affect current snapshot.

- [ ] **Step 2: GREEN**

R43 exists as a guardrail rule. It must not generate a `WARNING` merely because an outcome is not yet evidenced; missing outcome proof remains `UNKNOWN`.

```bash
python -m projektguard.dev.rule_gate R43
```

- [ ] **Step 3: Commit**

```bash
git add src/projektguard/rules/indicator.py tests/rules/evidence/test_r43_completion_not_achievement.py
git commit -m "feat: prevent completion from verifying outcomes"
```

---

### Task 11: Cross-rule adversarial hardening

**Files:**
- Create: `tests/rules/evidence/test_adversarial_evidence.py`

- [ ] **Step 1: Add adversarial regressions with rule IDs in test names**

Required tests:

```text
test_R35_first_cost_has_evidence_second_cost_is_unknown
test_R35_future_delivery_evidence_is_not_observable
test_R36_first_execution_matches_second_execution_warns
test_R37_equal_numbers_with_conflicting_units_require_expert_review
test_R38_same_serial_reused_on_two_executions_warns
test_R39_acceptance_with_unresolved_evidence_id_is_unknown
test_R40_indicator_sources_after_cutoff_are_unknown
test_R41_project_completion_does_not_satisfy_energy_audit_requirement
test_R42_completion_report_number_does_not_substitute_for_prescribed_evidence
test_R43_project_complete_target_present_actual_absent_is_unknown
```

- [ ] **Step 2: Run every rule gate**

```bash
for rule in R35 R36 R37 R38 R39 R40 R41 R42 R43; do
  python -m projektguard.dev.rule_gate "$rule" || exit 1
done
```

Expected: all PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/rules/evidence/test_adversarial_evidence.py src/projektguard/dev/rule_gate.py
git commit -m "test: harden Evidence Integrity rules adversarially"
```

---

### Task 12: Evidence Integrity benchmark and machine-readable gate

**Files:**
- Create: `benchmark/evidence_integrity/manifest.json`
- Create: `benchmark/evidence_integrity/fixtures/synthetic/*.json`
- Create: `benchmark/evidence_integrity/fixtures/retrospective/B05-zdralovi-evidence.json`
- Create: `benchmark/evidence_integrity/fixtures/retrospective/B06-tehnoguma-evidence.json`
- Create: `src/projektguard/benchmark/evidence_evaluator.py`
- Create: `src/projektguard/benchmark/evidence_cli.py`
- Test: `tests/benchmark/test_evidence_benchmark.py`

**Benchmark minimum:**
- at least 2 cases per rule -> minimum 18 synthetic cases;
- at least 1 `UNKNOWN` case per rule where missing evidence is meaningful;
- at least 1 deterministic contradiction for each rule capable of `WARNING`;
- retrospective B05/B06 cases explicitly labeled `retrospective`, never `pre_cutoff` unless source timing is independently proven.

- [ ] **Step 1: RED benchmark contract test**

```python
assert summary.total >= 18
assert summary.pass_rate >= 0.98
assert summary.unknown_discipline >= 0.95
assert summary.critical_false_positives == 0
assert summary.high_critical_source_completeness == 1.0
```

- [ ] **Step 2: Implement evaluator/CLI**

Do not duplicate Financial benchmark safety logic unnecessarily. Reuse shared verdict/source/temporal helpers where possible, but load Evidence rules separately.

```bash
python -m projektguard.benchmark.evidence_cli \
  --manifest benchmark/evidence_integrity/manifest.json \
  --json-output evidence-benchmark-summary.json
```

- [ ] **Step 3: Run benchmark GREEN**

```bash
python -m pytest tests/benchmark/test_evidence_benchmark.py -q
python -m projektguard.benchmark.evidence_cli --manifest benchmark/evidence_integrity/manifest.json --json-output evidence-benchmark-summary.json
```

- [ ] **Step 4: Commit**

```bash
git add benchmark/evidence_integrity src/projektguard/benchmark/evidence_evaluator.py src/projektguard/benchmark/evidence_cli.py tests/benchmark/test_evidence_benchmark.py
git commit -m "test: add Evidence Integrity benchmark"
```

---

### Task 13: Full automated slice gate and CI integration

**Files:**
- Modify: `src/projektguard/dev/slice_gate.py`
- Modify: `.github/workflows/ci.yml`
- Test: `tests/dev/test_slice_gate.py`

- [ ] **Step 1: Lock exact five-stage full gate**

`python -m projektguard.dev.slice_gate evidence-integrity` must execute:

```text
1. python -m pytest tests/rules/evidence --ignore=tests/rules/evidence/test_adversarial_evidence.py -q
2. python -m pytest tests/rules/evidence/test_adversarial_evidence.py -q
3. python -m pytest --cov=projektguard --cov-report=term --cov-fail-under=90
4. projektguard-benchmark --manifest benchmark/financial_integrity_core/manifest.json --json-output benchmark-summary.json
5. python -m projektguard.benchmark.evidence_cli --manifest benchmark/evidence_integrity/manifest.json --json-output evidence-benchmark-summary.json
```

Stop immediately on first failure.

- [ ] **Step 2: Update CI**

Replace the current standalone test/Financial benchmark steps with:

```yaml
- name: Evidence Integrity slice gate
  run: python -m projektguard.dev.slice_gate evidence-integrity
```

The slice gate itself retains the full pytest coverage and Financial benchmark, so no safety gate is removed.

- [ ] **Step 3: Run local full gate**

```bash
python -m projektguard.dev.slice_gate evidence-integrity
```

Expected: exit 0.

- [ ] **Step 4: Commit**

```bash
git add src/projektguard/dev/slice_gate.py .github/workflows/ci.yml tests/dev/test_slice_gate.py
git commit -m "ci: enforce Evidence Integrity slice gate"
```

---

### Task 14: Documentation, self-audit, and draft PR

**Files:**
- Create: `docs/benchmark-evidence-integrity.md`
- Modify: `README.md`

- [ ] **Step 1: Document exact rule semantics and benchmark denominators**

The document must list for every R35–R43:
- required normalized inputs;
- possible verdicts;
- reason codes;
- synthetic benchmark cases;
- adversarial cases;
- historical mode (`retrospective`/`pre_cutoff`) where applicable.

State explicitly that no controller-recall claim is made without a genuine pre-cutoff document package and later ground truth.

- [ ] **Step 2: Run final self-audit**

Check for:
- first-item-only bugs;
- future evidence leakage;
- source-less VERIFIED findings;
- one evidence record incorrectly verifying multiple entities;
- generic completion evidence satisfying prescribed evidence types;
- `UNKNOWN` converted into `WARNING` because a document is absent;
- unsupported calculation methods producing deterministic answers.

Add a regression test before fixing any discovered issue.

- [ ] **Step 3: Run final verification**

```bash
python -m projektguard.dev.slice_gate evidence-integrity
python -m compileall -q src
```

Expected: all gates green.

- [ ] **Step 4: Open draft PR**

Title:

```text
Evidence Integrity Core v0.2
```

PR body must report actual CI values only after GitHub Actions runs: test count, coverage, Financial benchmark result, Evidence benchmark result, UNKNOWN discipline, source completeness, and counts of retrospective/pre-cutoff evidence cases.

- [ ] **Step 5: Keep PR draft until code audit is complete**

Do not merge immediately. Perform the same production-style code audit used on PR #1, fix blockers via RED regression tests, rerun GitHub CI, then decide readiness.

---

## Automated Development Loop for Every Rule

For a concrete rule such as R35, execution is:

```text
1. Add the R35 focused failing test.
2. Run the R35 focused test and confirm intended RED failure.
3. Implement minimal R35 behavior.
4. Run `python -m projektguard.dev.rule_gate R35`.
5. Add/update the R35 adversarial regression.
6. Re-run `python -m projektguard.dev.rule_gate R35`.
7. Run `python -m projektguard.dev.slice_gate evidence-integrity`.
8. Commit only when all gates are green.
9. Repeat the same sequence for the next concrete rule ID.
```

If any gate fails, the loop returns to the failing stage. Never weaken an expectation solely to make a test pass; first determine whether the fixture or implementation violates the written rule contract.

## Definition of Done — Slice 2

Slice 2 is complete only when all of the following are true:

- R35–R43 are registered and entity-scoped.
- Every rule has focused positive/UNKNOWN/conflict coverage appropriate to its semantics.
- Cross-rule adversarial suite is green.
- Full project coverage is at least 90%.
- Existing Financial benchmark remains green.
- Evidence benchmark pass rate is at least 98%.
- CRITICAL false positives are 0 in the Evidence benchmark.
- UNKNOWN discipline is at least 95%.
- Explicitly source-required HIGH/CRITICAL findings are 100% source-complete.
- Future-dated evidence does not enter current audit snapshots.
- No LLM/OCR component participates in deterministic verdict generation.
- GitHub Actions runs the same five-stage full slice gate used locally.
- Draft PR receives a production-style code audit before merge.
