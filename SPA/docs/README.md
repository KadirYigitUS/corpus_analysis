# Corpus Analysis Single-Page Application (SPA) — Engineering & Product Specification Suite

This directory (`scripts/corpus_analysis/SPA/docs/`) houses the **12-Document Software Engineering & Product Specification Suite** and the **Master Technical Implementation Blueprint (`13_Corpus_Analysis_SPA_Technical_Blueprint_Plan.md`)** for the **Corpus Analysis Single-Page Application (SPA)**.

## Document Index

1. [`01_PRD.md`](01_PRD.md) — Product Requirements Document (PRD)
2. [`02_SRS.md`](02_SRS.md) — Software Requirements Specification (SRS)
3. [`03_Use_Cases_and_User_Stories.md`](03_Use_Cases_and_User_Stories.md) — Use Cases & User Stories
4. [`04_SDD_Design_and_Architecture.md`](04_SDD_Design_and_Architecture.md) — Software Design Document (SDD)
5. [`05_ADRs.md`](05_ADRs.md) — Architecture Decision Records (ADRs)
6. [`06_API_and_Interface_Specs.md`](06_API_and_Interface_Specs.md) — REST API & Frontend/Backend Interface Specifications
7. [`07_SDP_Process_and_Project_Plan.md`](07_SDP_Process_and_Project_Plan.md) — Software Development Plan (SDP)
8. [`08_QA_and_Test_Plans.md`](08_QA_and_Test_Plans.md) — Quality Assurance & Test Plans
9. [`09_Technical_Onboarding_Guide.md`](09_Technical_Onboarding_Guide.md) — Technical Onboarding Guide
10. [`10_End_User_Manual.md`](10_End_User_Manual.md) — Bilingual End-User Manual (TR/EN)
11. [`11_System_Administrator_Guide.md`](11_System_Administrator_Guide.md) — System Administrator & Deployment Guide
12. [`12_Feature_Comparison_and_Dataflow_Matrix.md`](12_Feature_Comparison_and_Dataflow_Matrix.md) — Exhaustive Input $\to$ Output Flow & Cross-System Feature Matrix
13. [`13_Corpus_Analysis_SPA_Technical_Blueprint_Plan.md`](13_Corpus_Analysis_SPA_Technical_Blueprint_Plan.md) — Master SPA Technical Implementation Blueprint Plan
14. [`14_Input_to_Output_Test_Matrix.md`](14_Input_to_Output_Test_Matrix.md) — Granular Input $\to$ Output Test Matrix (All 8 Scopes, 32 TokenView Regimes, 11 Tabs & 25 Playwright E2E Suites)
15. [`15_Formulas_and_Subcomponent_Specs.md`](15_Formulas_and_Subcomponent_Specs.md) — Complete Mathematical Formulas, Edge-Case Guards & Sub-Component Specifications

## Headless Playwright E2E & Verification Suite (`SPA/tests/`)

The SPA verification suite uses **Node Playwright** (`/home/ben/miniconda3/lib/node_modules/playwright`, Chromium v145 headless `1920x1080`) bridged into `pytest` via `SPA/tests/e2e/test_e2e_playwright.py`:

```bash
cd /home/ben/Documents/thesis/scripts/corpus_analysis
# Run full SPA test suite (72 unit/benchmark/AST <=200 line hygiene items + 26 Playwright E2E items = 98 items)
/home/ben/miniconda3/bin/pytest SPA/tests/ -v

# Run standalone Node Playwright runner against a running server (25 E2E tests across 6 suites)
NODE_PATH=/home/ben/miniconda3/lib/node_modules BASE_URL=http://127.0.0.1:5000 /home/ben/miniconda3/bin/node SPA/tests/e2e/pw/run_all.js
```

* **Zero-Error Telemetry**: `harness.js` attaches `pageerror`, `console.error`, `requestfailed`, and `response >= 500` listeners on every test, failing immediately on any unhandled runtime or network error.
* **Failure Artifacts**: On failure, `harness.js` automatically saves `traces/<test>.zip`, `screenshots/<test>.png`, and `screenshots/<test>.html` under `SPA/tests/results/playwright/`.
* **Measured Empirical Facts (`results.json`)**:
  * `tab01_row_count`: `13` (5 English sources + 5 Turkish translations + 3 indigenous Turkish novels)
  * `nda_token_counts`: `{"IR-IA_BR-SM": 576, "TL-PA_A-ZB": 485}`
  * `tab08_row_count`: `13` (7 UI columns rendered in `tab_08.js`: `TTR`, `Guiraud_R`, `Yule_K`, `Simpson_D`, `MATTR_500`, `MTLD`, `HD_D`)
  * `bundle_zip_bytes`: `295` bytes (valid PK ZIP header `50 4b 03 04`)

