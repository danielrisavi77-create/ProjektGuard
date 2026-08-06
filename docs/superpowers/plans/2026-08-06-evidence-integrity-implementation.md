# Evidence Integrity v0.2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic Evidence Integrity rules `R35`–`R43` plus an automated TDD/benchmark gate that must pass locally and in GitHub Actions without regressing the merged Financial Integrity Core.

**Architecture:** Extend `AuditContext` with first-class normalized evidence, execution, acceptance, and indicator records. Reuse the existing `Finding`, registry, temporal cutoff, and benchmark infrastructure. Generalize benchmark loading so both Financial and Evidence manifests run through one engine, and add developer gate commands that enforce `RED -> GREEN -> adversarial -> full regression -> both benchmarks`.

**Tech Stack:** Python 3.12, Pydantic 2.x, `Decimal`, pytest 8.x, pytest-cov 5.x, GitHub Actions.

## Global Constraints

- Missing evidence returns `UNKNOWN`; absence is never treated as proof of failure.
- Deterministic contradictions may return `WARNING`; interpretation-heavy cases return `EXPERT_REVIEW`.
- `VERIFIED` requires normalized evidence plus traceable source references where the rule depends on documentary evidence.
- Evidence with `observed_at > AuditContext.as_of` is unavailable.
- No OCR, PDF parsing, LLM extraction, embeddings, database, UI, upload workflow, or automatic legal interpretation in this slice.
- Existing Financial Integrity behavior and its benchmark must remain unchanged and green.
- Financial arithmetic remains `Decimal`-based.
- Every new rule evaluates every relevant entity, not item zero.
- GitHub CI and local development must invoke the same slice gate.

---

## File map

### Domain

- Modify `src/projektguard/domain/enums.py` — add `EvidenceType` and `AcceptanceType`.
- Modify `src/projektguard/domain/models.py` — add `EvidenceRecord`, `ExecutionRecord`, `AcceptanceRecord`, `Indicator`, observable helpers, and four collections on `AuditContext`.

### Rules

- Modify `src/projektguard/rules/__init__.py` — add `EVIDENCE_INTEGRITY_RULE_IDS`, `load_evidence_integrity_rules()`, and `load_all_rules()`.
- Create `src/projektguard/rules/evidence_execution.py` — R35–R39.
- Create `src/projektguard/rules/evidence_indicator.py` — R40–R43.

### Automation

- Create `src/projektguard/dev/__init__.py`.
- Create `src/projektguard/dev/gates.py` — command runner and shared gate definitions.
- Create `src/projektguard/dev/rule_gate.py` — `python -m projektguard.dev.rule_gate R35`.
- Create `src/projektguard/dev/slice_gate.py` — `python -m projektguard.dev.slice_gate evidence-integrity`.
- Modify `pyproject.toml` — optional console aliases only; module commands remain canonical.

### Benchmark

- Modify `src/projektguard/benchmark/evaluator.py` — load all registered rule families, preserving existing metrics.
- Create `benchmark/evidence_integrity/manifest.json`.
- Create `benchmark/evidence_integrity/fixtures/synthetic/*.json`.
- Create retrospective fixtures only when normalized public evidence is defensible; do not fabricate a pre-cutoff case.
- Create `docs/benchmark-evidence-integrity.md`.

### Tests

- Create `tests/domain/test_evidence_models.py`.
- Create `tests/dev/test_rule_gate.py`.
- Create `tests/dev/test_slice_gate.py`.
- Create `tests/rules/evidence/test_r35_execution_evidence.py` through `test_r43_completion_indicator.py`.
- Create `tests/rules/evidence/test_adversarial_evidence.py`.
- Create `tests/benchmark/test_evidence_benchmark.py`.

### CI

- Modify `.github/workflows/ci.yml` — call the shared evidence-integrity slice gate.

---

### Task 1: First-class evidence domain models

**Files:**
- Modify: `src/projektguard/domain/enums.py`
- Modify: `src/projektguard/domain/models.py`
- Test: `tests/domain/test_evidence_models.py`

**Interfaces:**
- Produces: `EvidenceType`, `AcceptanceType`, `EvidenceRecord`, `ExecutionRecord`, `AcceptanceRecord`, `Indicator`.
- Produces: `AuditContext.observable_evidence()`, `observable_executions()`, `observable_acceptances()`.
- Existing `AuditContext` constructor remains backward-compatible because all new collections default to empty lists.

- [ ] **Step 1: Write failing domain tests**

```python
from datetime import date
from decimal import Decimal

from projektguard.domain.enums import AcceptanceType, EvidenceType
from projektguard.domain.models import (
    AcceptanceRecord,
    AuditContext,
    EligibilityPeriod,
    EvidenceRecord,
    ExecutionRecord,
    Indicator,
    ProjectFinancials,
    SourceRef,
)


def base_context(**kwargs):
    return AuditContext(
        project_id="P",
        as_of=date(2026, 5, 1),
        eligibility=EligibilityPeriod(start=date(2026, 1, 1), end=date(2026, 12, 31)),
        financials=ProjectFinancials(currency="EUR"),
        **kwargs,
    )


def test_future_evidence_is_not_observable():
    context = base_context(evidence=[EvidenceRecord(
        evidence_id="E1",
        evidence_type=EvidenceType.DELIVERY_NOTE,
        observed_at=date(2026, 6, 1),
        supports_entity_type="cost",
        supports_entity_id="C1",
        sources=[SourceRef(document_id="delivery.pdf", available_from=date(2026, 6, 1))],
    )])
    assert context.observable_evidence() == []


def test_acceptance_none_is_distinct_from_false():
    record = AcceptanceRecord(
        acceptance_id="A1",
        execution_id="X1",
        acceptance_type=AcceptanceType.COMMISSIONING,
        accepted=None,
    )
    assert record.accepted is None


def test_indicator_decimal_fields_are_exact():
    indicator = Indicator(
        indicator_id="I1", title="Energy saving", unit="percent",
        baseline=Decimal("100.00"), target=Decimal("52.24"),
    )
    assert indicator.target == Decimal("52.24")
```

- [ ] **Step 2: Run RED**

Run:

```bash
python -m pytest tests/domain/test_evidence_models.py -q
```

Expected: FAIL because the evidence enums/models/helpers do not exist.

- [ ] **Step 3: Implement exact enums and models**

Add enums:

```python
class EvidenceType(str, Enum):
    DELIVERY_NOTE = "delivery_note"
    EXECUTION_REPORT = "execution_report"
    ACCEPTANCE_RECORD = "acceptance_record"
    COMMISSIONING_RECORD = "commissioning_record"
    ASSET_REGISTER = "asset_register"
    ENERGY_CERTIFICATE = "energy_certificate"
    FINAL_ENERGY_AUDIT = "final_energy_audit"
    SUPERVISION_REPORT = "supervision_report"
    TECHNICAL_REPORT = "technical_report"
    INDICATOR_CALCULATION = "indicator_calculation"
    PROJECT_COMPLETION = "project_completion"


class AcceptanceType(str, Enum):
    DELIVERY = "delivery"
    ACCEPTANCE = "acceptance"
    COMMISSIONING = "commissioning"
```

Add models:

```python
EvidenceValue = str | int | Decimal | bool | date | list[str] | list[int] | list[Decimal] | list[bool] | list[date]


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
    expected_item_name: str | None = None
    quantity: Decimal | None = None
    expected_quantity: Decimal | None = None
    unit: str | None = None
    model: str | None = None
    expected_model: str | None = None
    serial_number: str | None = None
    expected_serial_number: str | None = None
    reference: str | None = None
    expected_reference: str | None = None
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
```

Add `AuditContext` fields with `Field(default_factory=list)` and observable helpers filtering records whose own date is after `as_of`; evidence with `observed_at=None` remains observable as normalized state but cannot independently satisfy source-dependent `VERIFIED` rules unless its source is traceable.

- [ ] **Step 4: Run GREEN and existing domain regression**

```bash
python -m pytest tests/domain -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/projektguard/domain tests/domain/test_evidence_models.py
git commit -m "feat: add evidence integrity domain models"
```

---

### Task 2: Generalize rule loading and benchmark evaluation

**Files:**
- Modify: `src/projektguard/rules/__init__.py`
- Modify: `src/projektguard/benchmark/evaluator.py`
- Test: `tests/benchmark/test_evidence_benchmark.py`

**Interfaces:**
- Produces: `EVIDENCE_INTEGRITY_RULE_IDS = ("R35", ..., "R43")`.
- Produces: `load_evidence_integrity_rules() -> None`.
- Produces: `load_all_rules() -> None`.
- Benchmark evaluator calls `load_all_rules()` instead of only `load_financial_integrity_rules()`.

- [ ] **Step 1: Write failing loader test**

```python
from projektguard.rules import EVIDENCE_INTEGRITY_RULE_IDS, load_all_rules


def test_evidence_rule_catalog_is_declared():
    assert EVIDENCE_INTEGRITY_RULE_IDS == (
        "R35", "R36", "R37", "R38", "R39", "R40", "R41", "R42", "R43",
    )


def test_load_all_rules_preserves_financial_catalog():
    load_all_rules()
    from projektguard.audit.registry import get_rule
    assert get_rule("R30").rule_id == "R30"
```

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/benchmark/test_evidence_benchmark.py -q
```

Expected: FAIL because evidence catalog/loaders do not exist.

- [ ] **Step 3: Implement loader split**

```python
FINANCIAL_INTEGRITY_RULE_IDS = (...existing ids...)
EVIDENCE_INTEGRITY_RULE_IDS = ("R35", "R36", "R37", "R38", "R39", "R40", "R41", "R42", "R43")


def load_financial_integrity_rules() -> None:
    from projektguard.rules import baseline, budget, duplicate, payment, procurement  # noqa: F401


def load_evidence_integrity_rules() -> None:
    from projektguard.rules import evidence_execution, evidence_indicator  # noqa: F401


def load_all_rules() -> None:
    load_financial_integrity_rules()
    load_evidence_integrity_rules()
```

Update evaluator import and call from `load_financial_integrity_rules()` to `load_all_rules()`.

Because rule modules do not exist yet, create empty `evidence_execution.py` and `evidence_indicator.py` modules in this task so `load_all_rules()` is import-safe; rule registrations arrive in later tasks.

- [ ] **Step 4: Run GREEN plus Financial benchmark regression**

```bash
python -m pytest tests/benchmark/test_evaluator.py tests/benchmark/test_hardening_metrics.py tests/benchmark/test_evidence_benchmark.py -q
projektguard-benchmark --manifest benchmark/financial_integrity_core/manifest.json
```

Expected: PASS and existing Financial benchmark remains unchanged.

- [ ] **Step 5: Commit**

```bash
git add src/projektguard/rules src/projektguard/benchmark/evaluator.py tests/benchmark/test_evidence_benchmark.py
git commit -m "refactor: generalize rule and benchmark loading"
```

---

### Task 3: Automated rule gate and slice gate

**Files:**
- Create: `src/projektguard/dev/__init__.py`
- Create: `src/projektguard/dev/gates.py`
- Create: `src/projektguard/dev/rule_gate.py`
- Create: `src/projektguard/dev/slice_gate.py`
- Test: `tests/dev/test_rule_gate.py`
- Test: `tests/dev/test_slice_gate.py`

**Interfaces:**
- `RULE_TEST_FILES: dict[str, str]` maps R35–R43 to focused pytest paths.
- `run_commands(commands: list[list[str]]) -> int` executes sequentially and stops on first non-zero exit.
- `rule_gate(rule_id: str) -> int` runs focused evidence tests.
- `slice_gate(name: str) -> int` supports exactly `evidence-integrity`.

- [ ] **Step 1: Write RED tests with monkeypatched subprocess**

```python
from projektguard.dev.gates import evidence_slice_commands, rule_commands


def test_rule_gate_maps_r35_to_focused_test():
    commands = rule_commands("R35")
    assert commands == [[
        "python", "-m", "pytest", "tests/rules/evidence/test_r35_execution_evidence.py", "-q"
    ]]


def test_evidence_slice_gate_runs_both_benchmarks():
    commands = evidence_slice_commands()
    flattened = [" ".join(command) for command in commands]
    assert any("benchmark/financial_integrity_core/manifest.json" in command for command in flattened)
    assert any("benchmark/evidence_integrity/manifest.json" in command for command in flattened)
    assert any("--cov-fail-under=90" in command for command in flattened)
```

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/dev -q
```

Expected: FAIL because dev gate modules do not exist.

- [ ] **Step 3: Implement deterministic command definitions**

`rule_commands()` must reject unknown rule IDs with `ValueError`.

`evidence_slice_commands()` must return, in order:

```python
[
    ["python", "-m", "pytest", "tests/rules/evidence", "tests/domain/test_evidence_models.py", "tests/dev", "-q"],
    ["python", "-m", "pytest", "--cov=projektguard", "--cov-report=term", "--cov-fail-under=90"],
    ["projektguard-benchmark", "--manifest", "benchmark/financial_integrity_core/manifest.json", "--json-output", "/tmp/projektguard-financial-summary.json"],
    ["projektguard-benchmark", "--manifest", "benchmark/evidence_integrity/manifest.json", "--json-output", "/tmp/projektguard-evidence-summary.json"],
]
```

`rule_gate.py` and `slice_gate.py` parse one positional argument, invoke the appropriate command set, and exit with the first failing command's return code.

- [ ] **Step 4: Run GREEN**

```bash
python -m pytest tests/dev -q
```

Expected: PASS.

Do not run the full slice gate yet because the Evidence benchmark manifest does not exist until Task 8.

- [ ] **Step 5: Commit**

```bash
git add src/projektguard/dev tests/dev
git commit -m "feat: add automated TDD quality gates"
```

---

### Task 4: R35 — required execution/delivery evidence

**Files:**
- Modify: `src/projektguard/rules/evidence_execution.py`
- Create: `tests/rules/evidence/test_r35_execution_evidence.py`

**Interfaces:**
- Produces: `evaluate_r35(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]`.
- Target entity: every observable execution record.
- Required evidence is any observable `EvidenceRecord` referenced by `execution.evidence_ids` with at least one `SourceRef`.

- [ ] **Step 1: RED tests**

Create three cases:

```python
def test_r35_verified_when_execution_has_sourced_observable_evidence(): ...
def test_r35_unknown_when_execution_has_no_evidence(): ...
def test_r35_unknown_when_only_evidence_is_after_cutoff(): ...
```

Positive expectation:

```python
assert finding.verdict == Verdict.VERIFIED
assert finding.reason_code == "EXECUTION_EVIDENCE_PRESENT"
assert finding.subject_type == "execution"
assert finding.subject_id == "X1"
assert finding.sources
```

Missing/future expectation:

```python
assert finding.verdict == Verdict.UNKNOWN
assert finding.reason_code == "EXECUTION_EVIDENCE_NOT_AVAILABLE"
```

- [ ] **Step 2: Verify RED through automated gate**

```bash
python -m projektguard.dev.rule_gate R35
```

Expected: FAIL because R35 is not registered.

- [ ] **Step 3: Minimal GREEN implementation**

For each `context.observable_executions()`, resolve `execution.evidence_ids` against `context.observable_evidence()`. Only sourced evidence counts as sufficient for VERIFIED. Emit one scoped Finding per execution. If no executions exist, emit one project-scoped `UNKNOWN` with reason `EXECUTION_STATE_NOT_AVAILABLE`.

Register:

```python
register_rule(Rule(
    "R35", "Required execution or delivery evidence exists",
    ExecutionClass.EVIDENCE, Severity.HIGH, evaluate_r35,
))
```

- [ ] **Step 4: Run GREEN**

```bash
python -m projektguard.dev.rule_gate R35
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/projektguard/rules/evidence_execution.py tests/rules/evidence/test_r35_execution_evidence.py
git commit -m "feat: add R35 execution evidence rule"
```

---

### Task 5: R36–R38 — deterministic identity, quantity, and identifier reconciliation

**Files:**
- Modify: `src/projektguard/rules/evidence_execution.py`
- Create: `tests/rules/evidence/test_r36_item_match.py`
- Create: `tests/rules/evidence/test_r37_quantity_reconciliation.py`
- Create: `tests/rules/evidence/test_r38_identifier_consistency.py`

**Interfaces:**
- Produces: `evaluate_r36`, `evaluate_r37`, `evaluate_r38`.
- String equality is normalized only with `strip().casefold()`; no fuzzy/semantic matching.
- R37 uses `TolerancePolicy` for quantities only when units match after `strip().casefold()`.

- [ ] **Step 1: R36 RED contract**

Cases:

```python
("Pump X", " pump x ") -> VERIFIED / ITEM_IDENTITY_MATCH
("Pump X", "Pump Y") -> WARNING / ITEM_IDENTITY_MISMATCH
(None, "Pump X") -> UNKNOWN / ITEM_IDENTITY_UNKNOWN
```

Run:

```bash
python -m projektguard.dev.rule_gate R36
```

Expected: FAIL because R36 is not registered.

- [ ] **Step 2: Implement and GREEN R36**

One finding per observable execution. Do not treat partial substrings as match.

Run gate again; expected PASS.

- [ ] **Step 3: R37 RED contract**

Cases:

```python
expected_quantity=Decimal("10"), quantity=Decimal("10"), unit="pcs" -> VERIFIED
expected_quantity=Decimal("10"), quantity=Decimal("8"), unit="pcs" -> WARNING
expected_quantity=Decimal("10"), quantity=Decimal("10"), unit=None -> UNKNOWN
```

Add a case where expected and actual units are represented by two fields. Extend `ExecutionRecord` in Task 1 implementation with `expected_unit: str | None = None`; R37 requires both units and they must normalize equal. If unequal, return `EXPERT_REVIEW / QUANTITY_UNIT_CONVERSION_REQUIRES_REVIEW` rather than guessing conversion.

Run gate; expected RED, then implement and GREEN.

- [ ] **Step 4: R38 RED contract**

For each populated expected identifier (`expected_model`, `expected_serial_number`, `expected_reference`):

- all populated expected identifiers match -> `VERIFIED / EXECUTION_IDENTIFIERS_MATCH`
- any deterministic mismatch -> `WARNING / EXECUTION_IDENTIFIER_MISMATCH`
- no expected identifier is available -> `UNKNOWN / EXECUTION_IDENTIFIER_REQUIREMENT_UNKNOWN`

Add regression that two execution records must not share the same non-empty serial number. The second occurrence returns `WARNING / DUPLICATE_SERIAL_NUMBER`.

Run gate; expected RED, implement, then GREEN.

- [ ] **Step 5: Run grouped regression**

```bash
python -m pytest tests/rules/evidence/test_r36_item_match.py tests/rules/evidence/test_r37_quantity_reconciliation.py tests/rules/evidence/test_r38_identifier_consistency.py -q
python -m pytest tests/rules/payment.py 2>/dev/null || true
```

The second command is intentionally not part of the canonical gate; the actual full regression happens in Task 9. The first command must PASS.

- [ ] **Step 6: Commit**

```bash
git add src/projektguard/domain/models.py src/projektguard/rules/evidence_execution.py tests/rules/evidence
git commit -m "feat: add execution reconciliation rules R36 to R38"
```

---

### Task 6: R39 — acceptance and commissioning evidence

**Files:**
- Modify: `src/projektguard/rules/evidence_execution.py`
- Create: `tests/rules/evidence/test_r39_acceptance.py`

**Interfaces:**
- Produces `evaluate_r39`.
- An acceptance only applies when `acceptance.execution_id == execution.execution_id`.
- Acceptance evidence IDs must resolve to observable sourced evidence.

- [ ] **Step 1: RED contract**

Required cases:

```python
accepted=True + sourced observable acceptance evidence -> VERIFIED / ACCEPTANCE_CONFIRMED
accepted=None -> UNKNOWN / ACCEPTANCE_STATUS_UNKNOWN
no acceptance record -> UNKNOWN / ACCEPTANCE_EVIDENCE_NOT_AVAILABLE
accepted=False -> WARNING / ACCEPTANCE_REJECTED
accepted=True but only future evidence -> UNKNOWN / ACCEPTANCE_EVIDENCE_NOT_AVAILABLE
```

- [ ] **Step 2: Verify RED**

```bash
python -m projektguard.dev.rule_gate R39
```

Expected: FAIL because R39 is not registered.

- [ ] **Step 3: Implement minimal deterministic behavior**

Emit one finding per observable execution. If multiple acceptance records conflict (`True` and `False` for same execution at cutoff), emit `EXPERT_REVIEW / ACCEPTANCE_RECORDS_CONFLICT`.

- [ ] **Step 4: Run GREEN**

```bash
python -m projektguard.dev.rule_gate R39
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/projektguard/rules/evidence_execution.py tests/rules/evidence/test_r39_acceptance.py
git commit -m "feat: add R39 acceptance evidence rule"
```

---

### Task 7: R40–R43 — indicator evidence integrity

**Files:**
- Modify: `src/projektguard/rules/evidence_indicator.py`
- Create: `tests/rules/evidence/test_r40_indicator_traceability.py`
- Create: `tests/rules/evidence/test_r41_indicator_evidence.py`
- Create: `tests/rules/evidence/test_r42_indicator_actual.py`
- Create: `tests/rules/evidence/test_r43_completion_indicator.py`

**Interfaces:**
- Produces: `evaluate_r40`, `evaluate_r41`, `evaluate_r42`, `evaluate_r43`.
- Indicator `source_ids` resolve to `EvidenceRecord.evidence_id`.
- R42 does not invent calculations from prose; only explicit normalized actual values and supporting required evidence are deterministic.

- [ ] **Step 1: R40 RED/GREEN**

Cases:

```python
baseline + target + sourced source_ids -> VERIFIED / INDICATOR_BASELINE_TARGET_TRACEABLE
missing baseline or target -> UNKNOWN / INDICATOR_BASELINE_TARGET_UNKNOWN
source_ids missing/unresolved -> UNKNOWN / INDICATOR_SOURCE_NOT_AVAILABLE
```

Run `python -m projektguard.dev.rule_gate R40`, observe RED, implement, rerun GREEN.

- [ ] **Step 2: R41 RED/GREEN**

For each indicator, every type in `required_evidence_types` must have at least one observable sourced EvidenceRecord linked via `source_ids`.

Cases:

```python
required=[FINAL_ENERGY_AUDIT], linked final-energy-audit exists -> VERIFIED / REQUIRED_INDICATOR_EVIDENCE_PRESENT
required=[FINAL_ENERGY_AUDIT], only PROJECT_COMPLETION exists -> UNKNOWN / REQUIRED_INDICATOR_EVIDENCE_NOT_AVAILABLE
required=[] -> UNKNOWN / INDICATOR_EVIDENCE_REQUIREMENT_UNKNOWN
```

Run gate RED -> implement -> GREEN.

- [ ] **Step 3: R42 RED/GREEN**

Cases:

```python
actual present + all required sourced evidence + calculation_method="direct_reported_value" -> VERIFIED / INDICATOR_ACTUAL_SUPPORTED
actual missing -> UNKNOWN / INDICATOR_ACTUAL_UNKNOWN
actual present but required evidence missing -> UNKNOWN / INDICATOR_ACTUAL_EVIDENCE_NOT_AVAILABLE
calculation_method="expert_energy_model" -> EXPERT_REVIEW / INDICATOR_CALCULATION_REQUIRES_REVIEW
```

Do not add generalized expression evaluation in v0.2.

- [ ] **Step 4: R43 RED/GREEN**

R43 specifically prevents false inference from completion evidence.

Cases:

```python
PROJECT_COMPLETION linked + actual=None -> UNKNOWN / COMPLETION_DOES_NOT_VERIFY_INDICATOR
PROJECT_COMPLETION linked + actual present + required evidence satisfied -> VERIFIED / INDICATOR_ACHIEVEMENT_SEPARATELY_SUPPORTED
no completion evidence -> NOT_APPLICABLE / PROJECT_COMPLETION_NOT_ESTABLISHED
```

Run rule gate RED -> implement -> GREEN.

- [ ] **Step 5: Grouped indicator regression and commit**

```bash
python -m pytest tests/rules/evidence/test_r4*.py -q
```

Expected: PASS.

```bash
git add src/projektguard/rules/evidence_indicator.py tests/rules/evidence
git commit -m "feat: add indicator evidence rules R40 to R43"
```

---

### Task 8: Evidence Integrity benchmark manifest and fixtures

**Files:**
- Create: `benchmark/evidence_integrity/manifest.json`
- Create: `benchmark/evidence_integrity/fixtures/synthetic/*.json`
- Create: `tests/benchmark/test_evidence_benchmark.py` or extend the file created in Task 2
- Create: `docs/benchmark-evidence-integrity.md`

**Interfaces:**
- Reuses existing `BenchmarkCase`, `evaluate_manifest`, and CLI.
- Evidence manifest starts with synthetic cases only unless a public retrospective fixture can be cited without inventing private evidence.

- [ ] **Step 1: Create minimum benchmark matrix before fixtures**

At least these 22 cases:

```text
R35 present / missing / future
R36 match / mismatch / unknown
R37 match / mismatch / unit-review
R38 match / mismatch / duplicate-serial
R39 accepted / unknown / rejected
R40 traceable / missing
R41 required-present / wrong-type
R42 supported / missing / expert-review
R43 completion-only / separately-supported
```

Each manifest row contains exact expected verdict, severity, reason code, and `requires_source` when VERIFIED/WARNING depends on documentary evidence.

- [ ] **Step 2: RED benchmark test**

```python
from decimal import Decimal
from pathlib import Path

from projektguard.audit.tolerance import TolerancePolicy
from projektguard.benchmark.evaluator import evaluate_manifest


def test_committed_evidence_manifest_meets_acceptance_thresholds():
    rows, summary = evaluate_manifest(
        Path("benchmark/evidence_integrity/manifest.json"),
        TolerancePolicy(absolute=Decimal("0.01"), relative_percent=Decimal("0.1")),
    )
    assert len(rows) >= 22
    assert summary.pass_rate >= 0.98
    assert summary.critical_false_positives == 0
    assert summary.critical_false_negatives == 0
    assert summary.unknown_discipline >= 0.95
    assert summary.high_critical_source_completeness == 1.0
```

Run:

```bash
python -m pytest tests/benchmark/test_evidence_benchmark.py -q
```

Expected: FAIL until manifest/fixtures are complete.

- [ ] **Step 3: Build fixtures rule-by-rule**

Use only normalized JSON types accepted by `AuditContext`. Every source-dependent positive case contains `SourceRef(document_id=..., available_from <= as_of)`.

Do not add `mode="pre_cutoff"` unless there is an independently checkable public later outcome meeting the existing strict temporal contract.

- [ ] **Step 4: Run Evidence benchmark GREEN**

```bash
projektguard-benchmark --manifest benchmark/evidence_integrity/manifest.json --json-output /tmp/projektguard-evidence-summary.json
```

Expected: exit 0 and >=98% pass rate.

- [ ] **Step 5: Document traceability and commit**

`docs/benchmark-evidence-integrity.md` must map every R35–R43 rule to its synthetic/adversarial cases and explicitly state that normalized fixtures validate engine behavior, not OCR/LLM extraction accuracy.

```bash
git add benchmark/evidence_integrity tests/benchmark/test_evidence_benchmark.py docs/benchmark-evidence-integrity.md
git commit -m "test: add evidence integrity benchmark"
```

---

### Task 9: Adversarial hardening and full automated slice gate

**Files:**
- Create: `tests/rules/evidence/test_adversarial_evidence.py`
- Modify production files only when a failing adversarial test demonstrates a real bug.

**Interfaces:**
- Uses the canonical `python -m projektguard.dev.slice_gate evidence-integrity` command.

- [ ] **Step 1: Add adversarial tests before fixes**

Required adversarial cases:

1. First execution valid, second execution missing evidence — second must be UNKNOWN.
2. First execution valid, second item mismatch — second must WARNING.
3. One matching serial repeated by two executions — duplicate must WARNING.
4. Evidence exists but has zero `sources` — must not VERIFIED a source-dependent rule.
5. Evidence is future-dated — must be ignored.
6. Acceptance `True` without observable acceptance evidence — UNKNOWN.
7. Acceptance records `True` and `False` conflict — EXPERT_REVIEW.
8. Required FINAL_ENERGY_AUDIT but only ENERGY_CERTIFICATE exists — UNKNOWN unless profile explicitly requires either; v0.2 uses exact types.
9. Project completion evidence plus missing indicator actual — UNKNOWN.
10. Indicator actual exists but calculation method is expert-only — EXPERT_REVIEW.
11. R37 identical numeric quantities but incompatible units — EXPERT_REVIEW, not VERIFIED.
12. Unknown expected item/model/serial must not become VERIFIED just because actual exists.

- [ ] **Step 2: Run focused adversarial RED/GREEN cycles**

```bash
python -m pytest tests/rules/evidence/test_adversarial_evidence.py -q
```

For each failure: confirm it fails for the intended correctness gap, apply minimal production fix, rerun until PASS.

- [ ] **Step 3: Run the canonical full slice gate**

```bash
python -m projektguard.dev.slice_gate evidence-integrity
```

Expected all four stages succeed:

1. focused Evidence/domain/dev tests;
2. full pytest with >=90% total coverage;
3. Financial benchmark exit 0;
4. Evidence benchmark exit 0.

- [ ] **Step 4: Confirm Financial benchmark did not drift**

Compare machine-readable summary against merged baseline expectations:

```text
critical_false_positives = 0
critical_false_negatives = 0
unknown_discipline >= 0.95
pre_cutoff_temporal_integrity = 1.0
```

Do not require exact total test count because Slice 2 adds tests.

- [ ] **Step 5: Commit**

```bash
git add tests/rules/evidence src/projektguard
git commit -m "test: harden evidence integrity against adversarial cases"
```

---

### Task 10: CI parity, release metadata, and draft PR

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `README.md`
- Modify: `pyproject.toml`

**Interfaces:**
- GitHub Actions calls the same `python -m projektguard.dev.slice_gate evidence-integrity` command used locally.
- Package version becomes `0.2.0` only after the entire slice gate is green.

- [ ] **Step 1: RED CI-parity test**

Add to `tests/dev/test_slice_gate.py` a source-level assertion that `.github/workflows/ci.yml` contains:

```text
python -m projektguard.dev.slice_gate evidence-integrity
```

Run test; expected FAIL before workflow modification.

- [ ] **Step 2: Replace duplicated CI commands with canonical gate**

Keep Checkout, Python setup, and install steps. Replace separate test/benchmark steps with:

```yaml
- name: Evidence Integrity quality gate
  run: python -m projektguard.dev.slice_gate evidence-integrity
```

Because the slice gate includes the Financial benchmark, the prior Financial acceptance protection remains active.

- [ ] **Step 3: Update README and package version**

Set:

```toml
version = "0.2.0"
```

README must state:

- Financial Integrity v0.1.1 is merged baseline.
- Evidence Integrity v0.2 adds R35–R43 over normalized evidence state.
- OCR/LLM ingestion remains out of scope.
- Canonical developer gate: `python -m projektguard.dev.slice_gate evidence-integrity`.

- [ ] **Step 4: Fresh local verification**

Run exactly:

```bash
python -m projektguard.dev.slice_gate evidence-integrity
python -m compileall -q src
python -m pip wheel . --no-deps -w /tmp/projektguard-dist
git diff --check
```

All must exit 0.

- [ ] **Step 5: Commit CI/release metadata**

```bash
git add .github/workflows/ci.yml README.md pyproject.toml tests/dev/test_slice_gate.py
git commit -m "ci: gate Evidence Integrity v0.2"
```

- [ ] **Step 6: Open draft PR**

Create draft PR from `agent/evidence-integrity` to `main` titled:

```text
Evidence Integrity Core v0.2
```

PR body must include:

- implemented R35–R43;
- Evidence model contract;
- automated rule/slice TDD gates;
- Evidence benchmark totals and metrics from the actual run;
- Financial benchmark regression status;
- explicit limitation: no OCR/LLM extraction validation yet.

- [ ] **Step 7: Verify actual GitHub Actions on PR head**

Do not report completion from local results alone. Fetch the workflow run for the exact PR head and require:

```text
Install = success
Evidence Integrity quality gate = success
```

If GitHub CI differs from local behavior, treat GitHub failure as a real blocker and debug root cause before review.

---

## Final Definition of Done

Evidence Integrity v0.2 is ready for code audit only when all conditions hold:

- R35–R43 are registered and individually gateable.
- Every rule has positive/UNKNOWN/conflict coverage appropriate to its semantics.
- All entity-scoped rules evaluate every relevant entity.
- Future evidence cannot enter the audit snapshot.
- Missing source-dependent evidence cannot produce VERIFIED.
- Indicator completion and indicator achievement remain separate concepts.
- Evidence benchmark pass rate >=98%.
- Evidence CRITICAL false positives = 0.
- Evidence CRITICAL false negatives = 0.
- Evidence UNKNOWN discipline >=95%.
- Evidence explicitly source-required findings are 100% source-complete.
- Existing Financial benchmark still passes its acceptance gate.
- Overall pytest coverage >=90%.
- `python -m projektguard.dev.slice_gate evidence-integrity` passes locally.
- The exact same gate passes on GitHub Actions for the PR head.
- PR remains draft until a separate adversarial code audit is completed.

## Self-review result

- **Spec coverage:** R35–R43, first-class evidence models, temporal isolation, source traceability, automated TDD, adversarial hardening, benchmark, Financial regression, and CI parity are each mapped to a task.
- **Placeholder scan:** no TBD/TODO/"implement later" requirements remain.
- **Type consistency:** all tasks use the same `EvidenceRecord`, `ExecutionRecord`, `AcceptanceRecord`, `Indicator`, `EVIDENCE_INTEGRITY_RULE_IDS`, `load_all_rules`, `rule_gate`, and `slice_gate` names.
- **Scope check:** OCR/LLM ingestion is explicitly excluded so this remains one independently testable subsystem.
