# ProjektGuard

ProjektGuard is an evidence-based pre-flight audit engine for Croatian EU-funded projects.

The first implementation slice is a deterministic **Financial Integrity Core** evaluated against a committed benchmark. It intentionally works with normalized JSON project state. Raw PDF ingestion, OCR, LLM evidence extraction, databases, web UI, authentication, and ZNS submission are out of scope until the audit kernel is reproducible and benchmarked.

## Core safety doctrine

- Missing evidence is `UNKNOWN`, not failure.
- Deterministic rules are never decided by an LLM.
- Interpretative cases escalate to `EXPERT_REVIEW`.
- HIGH/CRITICAL findings must be source-backed whenever normalized evidence is available.
- Financial decisions use `decimal.Decimal`, not binary floating-point arithmetic.
- Materiality is explicit configuration, not a hidden magic number.
- Benchmark tests drive product behavior.

## Financial Integrity Core v0.1

Implemented rules:

`R04, R07, R09, R11, R18, R22, R26, R30, R32, R44, R51, R53, R54, R61, R62`

The committed benchmark contains 30 acceptance cases, including public historical reconstructions for Stare Plavnice, V. OŠ Bjelovar, PŠ Ždralovi, and Tehnoguma, plus deterministic synthetic fixtures.

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
- UNKNOWN discipline >= 95%
- HIGH/CRITICAL source completeness = 100%

See `docs/benchmark-financial-integrity-core.md` for rule-to-benchmark traceability.

## Repository note

The machine-readable benchmark and executable tests are committed directly in this repository. The larger planning spreadsheet and implementation-plan artifact were produced during design/validation and are intentionally kept outside the source tree for now.
