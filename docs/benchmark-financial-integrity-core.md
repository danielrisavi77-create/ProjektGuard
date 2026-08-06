# ProjektGuard Financial Integrity Core — Benchmark Contract

## Purpose

This benchmark is the executable contract for the first ProjektGuard audit slice. Each manifest row maps one canonical rule to a normalized JSON fixture and an expected verdict. Historical fixtures contain only facts supported by the public reconstruction; unavailable invoice, bank, approval, or evidentiary facts remain absent rather than being invented.

A historical correction or supplement is treated as a **ground-truth signal**, not proof that ProjektGuard predicted the exact controller reason unless the underlying controller document is public.

## Traceability

| Rule | Check | Benchmark coverage | Historical/public trace where applicable |
|---|---|---|---|
| R04 | Cost eligibility date | synthetic valid + outside-period fixtures; future public-data UNKNOWN fixtures | n/a |
| R07 | Budget line exists | synthetic found + missing fixtures | n/a |
| R09 | Budget ceiling | synthetic within + exceeded fixtures | n/a |
| R11 | Current budget version | synthetic current + no-current; B04-style baseline/version logic | B04: https://www.bjelovar.hr/akti-gradonacelnika-srpanj-2021-rujan-2021/ |
| R18 | Contract vs award | synthetic exact + material mismatch fixtures | n/a |
| R22 | Procurement vs invoicing | synthetic within + over-contract fixtures; B03-style execution logic | B03: https://www.bjelovar.hr/akti-gradonacelnika-srpanj-2020-rujan-2020/ |
| R26 | Duplicate invoice | synthetic unique + duplicate invoice fixtures | n/a |
| R30 | Payment evidence | synthetic missing (`UNKNOWN`) + linked bank evidence (`VERIFIED`) | public project files generally lack full bank evidence |
| R32 | Invoice/payment reconciliation | synthetic exact + material mismatch fixtures | n/a |
| R44 | Duplicate claim | synthetic unique + duplicate ZNS claim fixture | n/a |
| R51 | Paid amount vs contract | synthetic within + B03 Stare Plavnice-style historical fixture | https://www.bjelovar.hr/akti-gradonacelnika-srpanj-2020-rujan-2020/ |
| R53 | Execution vs project baseline | synthetic within + over-baseline fixtures; B03-style historical logic | https://www.bjelovar.hr/akti-gradonacelnika-srpanj-2020-rujan-2020/ |
| R54 | Baseline change approval | synthetic approved + B04 V. OŠ historical `UNKNOWN` fixture | https://www.bjelovar.hr/akti-gradonacelnika-srpanj-2021-rujan-2021/ |
| R61 | Materiality tolerance | B05 PŠ Ždralovi 4-HRK-style fixture + synthetic material difference | https://www.bjelovar.hr/akti-gradonacelnika-srpanj-2019-rujan-2019/ |
| R62 | Total/eligible/grant distinction | B06 Tehnoguma historical valid layering + synthetic invalid ordering | https://tehnoguma-zg.hr/eu-projekti/energetski-i-resursno-ucinkovita-tranzicija-poduzeca-tehnoguma-d-o-o/ |

## Historical cases in v0.1

### B03 — Stare Plavnice

The normalized fixture records the publicly reconstructed original works contract and later known paid execution. Public records also establish two subsequent supplement requests after the pre-cutoff state. The benchmark uses this as a category-level historical signal; it does **not** claim the controller's exact questions were caused by the contract delta.

### B04 — V. osnovna škola Bjelovar

The pre-cutoff fixture records that a project financial baseline change exists while the approval evidence is intentionally absent from the normalized state. Public records later show a final ZNS correction and an addendum. Expected verdict: `UNKNOWN`, not an accusation of an unapproved change.

### B05 — PŠ Ždralovi

The supervision contract pattern contains a four-HRK execution delta. With the published materiality policy (absolute 10 units, relative 0.1%), this must not create noisy HIGH findings. Public records separately establish a ZNS correction and procurement-plan update; the benchmark does not claim the four-HRK difference caused either event.

### B06 — Tehnoguma

The public project baseline distinguishes total project cost, eligible cost, and EU grant. R62 verifies only the logical financial layering represented in the normalized fixture; it does not infer invoice-level eligibility from public project marketing information.

## Acceptance metrics

The CLI exits successfully only when all published gates pass:

- `pass_rate >= 0.98`
- `critical_false_positives == 0`
- `unknown_discipline >= 0.95`
- `high_critical_source_completeness == 1.0`

`UNKNOWN` is a safety behavior: missing evidence must not be transformed into a fabricated compliance failure or approval.

## Adding a new rule or regression

Every new behavior follows this sequence:

1. real problem or reproducible bug;
2. benchmark example;
3. failing test;
4. minimal implementation;
5. passing test;
6. historical/regression execution.

Do not add rules solely because an AI feature sounds useful.
