# ProjektGuard

ProjektGuard is an evidence-based pre-flight audit engine for Croatian EU-funded projects.

The first implementation slice is intentionally narrow: a deterministic **Financial Integrity Core** evaluated against the committed ProjektGuard benchmark. Document extraction, OCR, LLM reasoning, web UI, databases, and ZNS submission are out of scope until the audit kernel is reproducible and benchmarked.

## Design principles

- Missing evidence is `UNKNOWN`, not failure.
- Deterministic rules are not decided by an LLM.
- Interpretative cases escalate to `EXPERT_REVIEW`.
- HIGH/CRITICAL findings must be source-backed whenever evidence is available.
- Money decisions use exact decimal arithmetic.
- Benchmark tests drive product behavior.

## Reference artifacts

- `docs/ProjektGuard_Benchmark_v1.xlsx` — human-readable benchmark and rule matrix.
- `docs/Financial_Integrity_Core_Implementation_Plan.md` — TDD implementation plan for the first 15 rules.

## Development

The first development branch is `agent/financial-integrity-core`.
