# ProjektGuard Financial Integrity Core — Benchmark Contract v0.1.1

## Purpose

This benchmark is the executable contract for the first ProjektGuard audit slice. Each manifest row maps one canonical rule to a normalized JSON fixture and an expected verdict.

The benchmark distinguishes three modes:

- `synthetic` — deterministic acceptance/regression fixture;
- `retrospective` — historical reconstruction that may use evidence published after the original project event;
- `pre_cutoff` — strict historical snapshot where every evidence source/fact used by the engine must have been observable on or before `as_of`.

A retrospective correction or supplement is a **ground-truth signal**, not proof that ProjektGuard predicted the controller's exact reason. Only `pre_cutoff` cases may be used for predictive/blind-validation claims.

For `pre_cutoff` cases, the manifest must record `source_observed_at`, every normalized `SourceRef` used by the rule must have `available_from`, and any later ground-truth artifact must have `ground_truth_observed_at > as_of`. A URL without an observation date is not sufficient proof of historical availability.

## Safety behavior added in v0.1.1

- Rules that apply to costs/contracts evaluate every relevant entity rather than item zero.
- Findings may carry `subject_type` and `subject_id` so a warning is attributable to a concrete cost/contract/budget line.
- Costs and payments dated after `as_of` are not used in the audit snapshot.
- Contract execution totals can carry observation dates; future-observed totals are unavailable at an earlier cutoff.
- Cross-currency comparisons never silently compare raw numeric values.
- R09 uses cumulative spend per approved budget line, not a single invoice.
- R30 verifies payment evidence per claimed/observable cost.
- `baseline_changed` is tri-state; absent knowledge produces `UNKNOWN`.
- Duplicate identity uses supplier/document identity rather than invoice number alone.

## Traceability

| Rule | Check | Benchmark coverage | Historical/public trace where applicable |
|---|---|---|---|
| R04 | Cost eligibility date | synthetic valid + observable outside-period fixtures; adversarial future-cutoff test | n/a |
| R07 | Budget line exists | synthetic found + missing; adversarial multi-cost mapping | n/a |
| R09 | Cumulative budget ceiling | synthetic within + exceeded; adversarial cumulative, unapproved-budget and currency tests | n/a |
| R11 | Active budget version | synthetic current + no-current + unapproved version behavior | B04 context |
| R18 | Contract vs award | synthetic exact + material mismatch; adversarial multi-contract + currency mismatch | n/a |
| R22 | Contract vs invoicing | synthetic within + over; adversarial multi-contract | B03-style execution logic |
| R26 | Duplicate invoice identity | supplier/document-aware synthetic + adversarial different-supplier case | n/a |
| R30 | Payment evidence | missing + linked bank evidence + adversarial per-claimed-cost coverage | public project files generally lack full bank evidence |
| R32 | Invoice/payment reconciliation | exact + material mismatch + adversarial multi-cost/currency/cutoff tests | n/a |
| R44 | Duplicate claim | repeated cost-id + duplicate invoice identity across different cost IDs | n/a |
| R51 | Paid amount vs contract | synthetic within + B03 retrospective + B07 strict pre-cutoff + adversarial multi-contract/cutoff | Stare Plavnice |
| R53 | Execution vs project baseline | synthetic within + over + cross-currency expert-review test | B03-style historical logic |
| R54 | Baseline change approval | synthetic approved + B04 retrospective `UNKNOWN` + tri-state regression | V. OŠ Bjelovar |
| R61 | Materiality tolerance | B05 retrospective four-HRK delta + synthetic material difference + multi-contract regression | PŠ Ždralovi |
| R62 | Total/eligible/grant distinction | B06 retrospective valid layering + synthetic invalid ordering | Tehnoguma |

## Historical cases in v0.1.1

### B03 — Stare Plavnice — `retrospective`

The fixture uses the later public contract register to reconstruct original contract value and known final execution. Its `as_of` is therefore the date that evidence was publicly observable, not 30 June 2020. The later supplement requests remain a category-level historical signal only.

### B04 — V. osnovna škola Bjelovar — `retrospective`

The fixture records a known financial-baseline change with approval evidence intentionally absent from normalized state. The public final-ZNS correction/addendum is a historical signal; this fixture is not counted as blind prediction.

### B05 — PŠ Ždralovi — `retrospective`

The four-HRK supervision delta comes from a later public register and is used to regression-test materiality noise suppression. It is not represented as a pre-correction prediction.

### B06 — Tehnoguma — `retrospective`

The completed public project baseline verifies only the distinction between total cost, eligible cost and grant amount. It does not infer invoice-level eligibility.

### B07 — Stare Plavnice execution state — `pre_cutoff`

Cutoff: **10 December 2019**. The City of Bjelovar's 2018 contract register was publicly listed on **3 January 2019** and already contained contract `4-06-Ra/18` for **5,112,109.13 HRK**. At the cutoff, the public snapshot did not contain a final `actual_paid` value, so `R51` must return `UNKNOWN`, not `VERIFIED`.

A later public contract register (26 November 2021) records final execution of **5,259,796.34 HRK**, above the original contract value, which resolves the later ground-truth state of `R51` to `WARNING`. Separately, public City acts show two supplement requests on **1 July 2020** and **23 July 2020**. The benchmark does **not** claim those supplement requests were caused by the R51 difference.

This is the first strict public `pre_cutoff` case. It validates temporal isolation and calibrated uncertainty; it is not yet a proof of full-document controller-finding recall because the private invoice/payment package was not public.

## Acceptance metrics

The CLI exits successfully only when all published gates pass:

- `pass_rate >= 0.98`
- `critical_false_positives == 0`
- `critical_false_negatives == 0`
- `unknown_discipline >= 0.95`
- `high_critical_source_completeness == 1.0` for cases explicitly marked `requires_source`
- `pre_cutoff_temporal_integrity == 1.0`

The summary always reports:

- `source_required_cases`;
- `pre_cutoff_cases`;
- `retrospective_cases`.

This prevents a vacuous 100% metric from being presented without its denominator.

## Adding a new rule or regression

Every new behavior follows this sequence:

1. real problem or reproducible bug;
2. failing adversarial/benchmark test;
3. minimal implementation;
4. passing focused test;
5. full regression suite;
6. benchmark execution;
7. if historical, explicit `synthetic` / `retrospective` / `pre_cutoff` classification.

Do not add rules solely because an AI feature sounds useful.
