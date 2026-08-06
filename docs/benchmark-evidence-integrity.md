# ProjektGuard Evidence Integrity Benchmark v0.2

## Scope

This benchmark covers deterministic Evidence Integrity rules `R35`–`R43` over normalized evidence state. OCR, PDF parsing, LLM extraction, databases, UI, and legal interpretation are outside this slice.

## Safety contract

- Missing evidence is `UNKNOWN`, not failure.
- Deterministic contradictions may be `WARNING`.
- Unsupported or interpretative calculations become `EXPERT_REVIEW`.
- `VERIFIED` requires structured evidence and traceable sources where the benchmark marks sources as required.
- Evidence after `AuditContext.as_of` is excluded.
- Project/output completion never proves outcome-indicator achievement.
- Prescribed evidence types cannot be substituted by generic completion evidence.

## Rules

| Rule | Purpose |
| --- | --- |
| R35 | Required execution/delivery evidence exists |
| R36 | Delivered/executed item matches expected item |
| R37 | Quantity and unit reconciliation |
| R38 | Model/serial/reference consistency |
| R39 | Acceptance/commissioning evidence and state |
| R40 | Indicator baseline/target traceability |
| R41 | Prescribed indicator evidence exists |
| R42 | Actual indicator value is supported |
| R43 | Completion does not imply indicator achievement |

## Automated gate

Run:

```bash
python -m projektguard.dev.slice_gate evidence-integrity
```

The gate executes, in order:

1. Evidence rule tests.
2. Evidence adversarial tests.
3. Full project pytest coverage with a 90% floor.
4. Existing Financial Integrity benchmark.
5. Evidence Integrity benchmark.

The committed Evidence benchmark contains 18 synthetic cases, two per rule. Historical public evidence cases are not labeled `pre_cutoff` unless source timing and later ground truth are independently demonstrated.

## Claims boundary

Passing this benchmark validates the deterministic rule contract and UNKNOWN/source discipline. It does not yet establish controller-finding recall on private ZNS document packages. That requires genuine pre-cutoff project evidence plus independently observed later controller ground truth.
