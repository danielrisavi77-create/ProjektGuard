# Evidence Integrity Slice — TDD & Automation Design

## Goal

Build Slice 2 (`R35`–`R43`) as a deterministic evidence-integrity layer on top of the merged Financial Integrity Core, while making the development process itself reproducible and gate-driven.

The slice must be developed through a repeatable automated TDD pipeline:

`RED -> minimal GREEN -> adversarial hardening -> full regression -> benchmark -> CI -> commit`

No rule is considered complete because its implementation "looks right". It is complete only when the automated gates pass.

## Scope

Slice 2 covers:

- `R35` — required execution/delivery evidence exists
- `R36` — delivered/executed item matches approved/contracted item
- `R37` — quantity reconciliation across cost/delivery/execution evidence
- `R38` — model/serial/reference consistency across evidence
- `R39` — required acceptance/commissioning evidence exists
- `R40` — indicator baseline and target are defined and traceable
- `R41` — required indicator evidence exists
- `R42` — actual indicator value is supported by prescribed evidence/calculation
- `R43` — project/output completion does not itself verify indicator achievement

Out of scope for this slice:

- OCR
- PDF parsing
- LLM extraction
- embeddings/vector search
- database persistence
- UI
- document upload workflow
- automatic legal interpretation

The engine receives normalized JSON evidence state. A later ingestion layer will create that state from documents.

## Architecture

### EvidenceRecord

First-class evidence object. It records what type of evidence exists, when it was observable, which project entity it supports, and which structured facts were extracted.

Required shape:

```python
class EvidenceRecord(BaseModel):
    evidence_id: str
    evidence_type: EvidenceType
    observed_at: date | None = None
    supports_entity_type: str
    supports_entity_id: str
    facts: dict[str, EvidenceValue] = Field(default_factory=dict)
    sources: list[SourceRef] = Field(default_factory=list)
```

`EvidenceValue` must remain structured and deterministic for v0.2. It may contain strings, integers, decimals, booleans, dates, and lists of those values. Arbitrary model-generated prose must not drive deterministic VERIFIED/WARNING decisions.

### ExecutionRecord

Represents delivered or executed project output.

```python
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
```

### AcceptanceRecord

```python
class AcceptanceRecord(BaseModel):
    acceptance_id: str
    execution_id: str
    acceptance_type: AcceptanceType
    accepted: bool | None = None
    acceptance_date: date | None = None
    evidence_ids: list[str] = Field(default_factory=list)
```

`accepted=None` means unknown, not rejected.

### Indicator

```python
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

### AuditContext extension

`AuditContext` receives four new collections:

```python
evidence: list[EvidenceRecord]
executions: list[ExecutionRecord]
acceptances: list[AcceptanceRecord]
indicators: list[Indicator]
```

Financial Core models and behavior remain backward-compatible.

## Safety semantics

The existing doctrine remains binding:

- Missing evidence -> `UNKNOWN`, never automatic failure.
- Contradictory evidence -> `WARNING` when contradiction is deterministic.
- Interpretative evidence -> `EXPERT_REVIEW`.
- `VERIFIED` requires sufficient structured evidence and traceable sources.
- Evidence observed after `AuditContext.as_of` is unavailable to the audit snapshot.
- Completion of an activity/project is not evidence that an outcome indicator was achieved.
- A source document existing is not enough; the required claim must be supported by the required evidence type.
- LLM-generated confidence must never upgrade a deterministic verdict.

## Rule behavior

### R35 — Required execution/delivery evidence exists

For each cost/contract/output that requires execution evidence:

- evidence present and observable -> `VERIFIED`
- evidence requirement known but evidence absent -> `UNKNOWN`
- evidence exists only after `as_of` -> `UNKNOWN`

The rule must emit entity-scoped findings.

### R36 — Item identity match

Compare normalized expected item identity to execution evidence.

- deterministic match -> `VERIFIED`
- deterministic mismatch -> `WARNING`
- insufficient normalized identity -> `UNKNOWN`

Fuzzy semantic similarity is out of scope for deterministic v0.2.

### R37 — Quantity reconciliation

Compare expected/claimed quantity with execution/delivery quantity.

- same unit + within explicit tolerance -> `VERIFIED`
- same unit + material mismatch -> `WARNING`
- incompatible/missing units -> `UNKNOWN` or `EXPERT_REVIEW` when conversion requires interpretation

### R38 — Model/serial/reference consistency

Evaluate every relevant execution object.

- all required identifiers consistent -> `VERIFIED`
- deterministic conflict -> `WARNING`
- missing identifier required by profile -> `UNKNOWN`

One matching serial number must never verify multiple assets.

### R39 — Acceptance/commissioning evidence

- required acceptance exists, observable, and accepted=True -> `VERIFIED`
- required record missing or accepted=None -> `UNKNOWN`
- accepted=False -> `WARNING`

### R40 — Indicator baseline/target traceability

- baseline and target defined with traceable source -> `VERIFIED`
- required value/source missing -> `UNKNOWN`
- contradictory approved values across current evidence -> `EXPERT_REVIEW`

### R41 — Required indicator evidence exists

Evidence type must satisfy the indicator's required evidence type list.

A generic project-completion document must not satisfy a final-energy-audit requirement.

### R42 — Actual indicator supported

- actual value + prescribed evidence + deterministic calculation -> `VERIFIED`
- actual value conflicts with deterministic evidence -> `WARNING`
- calculation requires professional interpretation -> `EXPERT_REVIEW`
- missing actual/evidence -> `UNKNOWN`

### R43 — Completion is not indicator achievement

If project/output completion is known but actual indicator evidence is absent:

- result -> `UNKNOWN`

Never infer indicator achievement from project status alone.

## Automated TDD pipeline

### Per-rule loop

Every rule follows the same state machine.

#### Stage 1 — RED contract

Create the minimal focused test file before production code:

```text
tests/rules/evidence/test_r35_execution_evidence.py
...
tests/rules/evidence/test_r43_completion_indicator.py
```

Each rule starts with at least:

- one expected positive case
- one expected `UNKNOWN` case
- one negative/conflict case when the rule can deterministically fail

Run only that rule's test file.

The stage is valid only when the new test fails for the intended missing behavior, not due to import/syntax/setup failure.

#### Stage 2 — Minimal GREEN

Implement only enough production code to satisfy the focused contract.

Run:

```bash
python -m pytest tests/rules/evidence/test_rXX_*.py -q
```

No refactor or unrelated feature is allowed during this stage.

#### Stage 3 — Adversarial hardening

Before declaring the rule complete, add adversarial cases applicable to the rule:

- second/third entity contains the defect
- evidence exists after `as_of`
- evidence source missing
- contradictory sources
- duplicate serial/reference
- missing unit
- incompatible units
- empty evidence list
- partial evidence coverage across multiple costs/assets
- one valid entity plus one invalid entity
- one valid entity plus one unknown entity

Run the focused rule suite again.

#### Stage 4 — Cross-slice regression

Run the complete project suite:

```bash
python -m pytest --cov=projektguard --cov-report=term --cov-fail-under=90
```

Financial Core must remain green.

#### Stage 5 — Evidence benchmark

Run:

```bash
projektguard-evidence-benchmark \
  --manifest benchmark/evidence_integrity/manifest.json \
  --json-output evidence-benchmark-summary.json
```

A rule is not complete until its benchmark fixtures pass.

#### Stage 6 — Commit

One logical rule or tightly coupled rule family per commit.

Commit examples:

```text
feat: add R35 execution evidence checks
feat: add R36 item identity reconciliation
test: harden evidence identity edge cases
```

Do not bundle unrelated rules into a single large commit merely to reduce commit count.

## Automation commands

### Focused developer gate

Introduce a small deterministic command:

```bash
python -m projektguard.dev.rule_gate R35
```

It maps a rule ID to its focused test file and runs only that file.

Exit code:

- `0` -> focused tests pass
- nonzero -> rule cannot progress to regression stage

It does not automatically write production code or convert RED to GREEN; its purpose is to make every test stage reproducible.

### Slice gate

Introduce:

```bash
python -m projektguard.dev.slice_gate evidence-integrity
```

The slice gate runs in order:

1. all Evidence Integrity unit tests
2. full pytest suite with coverage >= 90%
3. existing Financial Integrity benchmark
4. Evidence Integrity benchmark
5. benchmark-metric validation

Any failure stops the command immediately with a non-zero exit code.

The same command is used locally and by CI to prevent local/remote drift.

## Evidence benchmark structure

```text
benchmark/evidence_integrity/
├── manifest.json
├── fixtures/
│   ├── synthetic/
│   ├── adversarial/
│   └── historical/
└── README.md
```

Manifest rows reuse the existing benchmark concepts where possible:

- `test_id`
- `case_id`
- `rule_id`
- `fixture`
- expected verdict/severity/reason
- source requirement
- mode (`synthetic`, `retrospective`, `pre_cutoff`)

Do not create a second incompatible benchmark framework. Evidence benchmark evaluation should reuse the existing benchmark primitives and extend only what is evidence-specific.

## Evidence benchmark acceptance gates

Initial v0.2 gates:

- pass rate >= 98%
- CRITICAL false positives = 0
- CRITICAL false negatives = 0
- UNKNOWN discipline >= 95%
- HIGH/CRITICAL findings marked source-required = 100% source-complete
- evidence temporal integrity = 100%
- each R35–R43 rule has >= 1 positive and >= 1 missing-evidence/UNKNOWN benchmark fixture
- every deterministic mismatch-capable rule has >= 1 negative benchmark fixture

A metric with a zero denominator must display its denominator and must not be marketed as validation evidence.

## CI pipeline

Current CI already runs full pytest coverage and the Financial Integrity benchmark. Slice 2 extends it to call one canonical slice command rather than duplicating logic in YAML.

Target GitHub Actions flow:

```text
Checkout
  -> Python 3.12
  -> pip install -e .[dev]
  -> python -m projektguard.dev.slice_gate evidence-integrity
```

`slice_gate evidence-integrity` internally runs both old and new regression gates.

This guarantees that adding Evidence Integrity cannot silently break the already-merged Financial Integrity Core.

## Development ordering

Use this order because later rules depend on earlier evidence primitives:

1. evidence domain models + temporal helpers
2. R35 execution/delivery evidence presence
3. R39 acceptance/commissioning presence
4. R36 item identity
5. R38 serial/model/reference consistency
6. R37 quantity reconciliation
7. indicator model and R40
8. R41 required indicator evidence
9. R42 actual indicator support/calculation
10. R43 completion-vs-outcome safety rule
11. benchmark integration
12. automated `rule_gate` / `slice_gate`
13. adversarial audit pass
14. draft PR + remote CI

## Adversarial audit before PR readiness

After all R35–R43 tests are green, run a deliberate audit pass independent of the happy-path test matrix.

At minimum attempt to break:

- multiple entities where only the first is valid
- evidence reuse across two assets
- duplicate serial numbers
- evidence after cutoff
- source-less HIGH finding
- project-complete but indicator unknown
- actual indicator value with wrong evidence type
- quantity mismatch hidden by tolerance
- mixed units
- accepted=None interpreted as accepted
- conflicting current indicator baselines

Every confirmed bug becomes a permanent regression test before fixing production code.

## Definition of Done

Slice 2 is ready for merge only when all are true:

- R35–R43 implemented
- every rule has focused TDD tests
- adversarial audit completed
- all confirmed bugs converted into regression tests
- full project coverage >= 90%
- Financial Integrity benchmark remains green
- Evidence Integrity benchmark meets all acceptance thresholds
- CI runs the same canonical slice gate used locally
- no strict `pre_cutoff` case is counted without dated input sources and a later independently checkable outcome
- draft PR receives a final code audit before being marked ready

## Working principle

The automated pipeline controls promotion between stages, but it does not replace TDD discipline.

The required sequence remains:

```text
real requirement / bug
        ↓
failing focused test
        ↓
minimal implementation
        ↓
focused GREEN
        ↓
adversarial tests
        ↓
full regression
        ↓
evidence benchmark
        ↓
CI
        ↓
commit / PR
```

If a test written after implementation passes immediately, that test does not prove the implementation was driven by TDD. New behavior must first be observed failing for the intended reason.