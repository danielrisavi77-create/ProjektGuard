# ProjektGuard

ProjektGuard is an evidence-based pre-flight audit engine for Croatian EU-funded projects.

The first implementation slice is a deterministic **Financial Integrity Core** evaluated against a committed benchmark. It intentionally works with normalized JSON project state. Raw PDF ingestion, OCR, LLM evidence extraction, databases, web UI, authentication, and ZNS submission are out of scope until the audit kernel is reproducible and benchmarked.

## Core safety doctrine

- Missing evidence is `UNKNOWN`, not failure.
- Deterministic rules are never decided by an LLM.
- Interpretative cases escalate to `EXPERT_REVIEW`.
- HIGH/CRITICAL source requirements are explicit benchmark expectations, not inferred from unrelated files in a fixture.
- Financial decisions use `decimal.Decimal`, not binary floating-point arithmetic.
- Currency mismatches are never silently reconciled.
- Audit cutoffs exclude future-dated costs/payments and future-observed execution totals.
- Strict pre-cutoff cases require dated proof that each benchmark/source input was observable by the cutoff.
- Materiality is explicit configuration, not a hidden magic number.
- Benchmark tests drive product behavior.

## Financial Integrity Core v0.1.1

Implemented rules:

`R04, R07, R09, R11, R18, R22, R26, R30, R32, R44, R51, R53, R54, R61, R62`

The v0.1.1 hardening pass adds per-entity evaluation, cumulative budget-line checks, currency guards, temporal cutoff behavior, supplier-aware duplicate identity, tri-state baseline-change state, and stricter benchmark safety metrics.

The committed benchmark contains 31 acceptance cases. Four public historical cases (Stare Plavnice, V. OŠ Bjelovar, PŠ Ždralovi, and Tehnoguma) are explicitly classified as **retrospective**. One additional Stare Plavnice case is a strict **pre-cutoff** temporal benchmark.

## Windows local quick start

Docker is **not required**.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
projektguard-benchmark --manifest benchmark/financial_integrity_core/manifest.json
```

The project is designed to run from a user-owned Python virtual environment and does not require administrator privileges.

## Benchmark

Run the benchmark with a machine-readable summary:

```powershell
projektguard-benchmark --manifest benchmark/financial_integrity_core/manifest.json --json-output benchmark-summary.json
```

Acceptance thresholds:

- pass rate >= 98%
- CRITICAL false positives = 0
- CRITICAL false negatives = 0
- UNKNOWN discipline >= 95%
- explicitly source-required findings = 100% source-complete
- pre-cutoff fixture temporal integrity = 100%

The benchmark summary reports both retrospective and genuine pre-cutoff historical case counts. A pre-cutoff case is only valid when its source observation dates prove that the engine's inputs existed by the stated audit cutoff.

See `docs/benchmark-financial-integrity-core.md` for rule-to-benchmark traceability.

## Historical validation status

The first strict public pre-cutoff case uses Stare Plavnice with a cutoff of 10 December 2019. The original contract amount was already publicly observable, while the final execution total was not. ProjektGuard therefore returns `UNKNOWN` for R51 rather than a false `VERIFIED`; a later public register resolves the ground-truth state to `WARNING` because final execution exceeded the original contract.

This validates **temporal isolation and calibrated uncertainty**. It does not yet prove full-document controller-finding recall, because the private invoice/payment evidence and the full contents of later supplement requests are not public.
