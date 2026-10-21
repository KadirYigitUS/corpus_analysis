# 07 · Software Development Plan (SDP), Process & Project Plan

## 1. Executive Summary & Governance Model

This Software Development Plan (SDP) establishes the engineering lifecycle, multi-agent collaboration model, Work Breakdown Structure (WBS), dual-repository version control workflow, and risk mitigation framework for the **Corpus Analysis Single-Page Application (SPA)** located in [`scripts/corpus_analysis/SPA/`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/SPA/).

The project executes under an autonomous, multi-agent collaborative engineering paradigm governed by four strict operational invariants:
1. **Zero Package Installations**: All Python code must execute strictly within the existing Conda `base` environment (`conda activate base`). Installing new packages via `pip` or `conda` is strictly prohibited (`AGENTS.md` Rule 2).
2. **Clean Notebook Gate**: Tracked Jupyter notebooks (`Corpus_Analysis.ipynb` and `Corpus_Analysis_tr.ipynb`) must maintain 0 cell outputs and exact 186-cell structural parity.
3. **Hard Modular Line-Count Budget**: Every module across the Python backend must satisfy the target $\le 180$ LOC and cannot exceed the automated hard CI gate of $\le 200$ physical lines.
4. **Dual-Repository Coherence**: The standalone `corpus_analysis` repository (`scripts/corpus_analysis/`) and the root thesis repository (`thesis/`) must remain synchronized without merge conflicts, detached HEAD states, or cross-repo commit pollution.

---

## 2. Multi-Agent Team Roles & Allocation Matrix

To maximize engineering velocity, architectural consistency, and rigorous verification, development responsibilities are distributed among four specialized AI model agents:

```
+---------------------------------------------------------------------------------------+
|                                    Gemini 4 Argon                                     |
|           Lead Architect • Master Orchestrator • Cross-System Synthesis               |
+---------------------------------------------------------------------------------------+
           |                                                                |
           v                                                                v
+---------------------------------------+      +----------------------------------------+
|           Claude Sonnet 5.5           |      |              GPT-OSS 120B              |
| Backend Lead • Analytical Algorithms  |      |   Frontend Lead • UI State Machine     |
| Service/Repo Layer • Line Budget Gate |      |   Virtualized DataGrid • SVG Rendering |
+---------------------------------------+      +----------------------------------------+
           |                                                                |
           +-------------------------------+--------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                                  Gemini 3.8 Flash                                     |
|           QA Automation • Notebook Parity Auditor • Documentation Reviewer            |
+---------------------------------------------------------------------------------------+
```

| Agent Persona | Model Identity | Core Responsibilities & Artifact Ownership |
|---|---|---|
| **Lead Architect** | Gemini 4 Argon | • Overall system design, architectural invariants, and ADR formulation.<br>• Cross-system feature synthesis (`Neologism_Dictionary_Annotation`, `passim_analysis`, `alignment_view.html`).<br>• Technical blueprint governance and inter-agent synchronization. |
| **Backend & Analytical Lead** | Claude Sonnet 5.5 | • Strict MVC + Service + Repository layer construction (`SPA/controllers/`, `SPA/services/`, `SPA/repositories/`).<br>• DTO data modeling and schema validation.<br>• Integration with `corpus_toolkit/` modules.<br>• Automated line budget enforcement ($\le 180$ LOC target, $\le 200$ LOC gate). |
| **Frontend & UI Lead** | GPT-OSS 120B | • HTML5 single-page application shell (`index.html`) and responsive CSS layout.<br>• Modular Vanilla ES6 client-side components (`datagrid.js`, `api_client.js`, tabs).<br>• Stepped SVG link connectors, displaCy tree rendering, and offline Plotly visualizations.<br>• Local asset bundling and strict Content Security Policy (CSP) compliance. |
| **QA & Verification Lead** | Gemini 3.8 Flash | • Pytest test suite implementation (unit, integration, regression).<br>• Notebook output parity auditing (0 cell outputs, 186-cell parity).<br>• Memory stress testing ($< 1{,}500\text{ MB}$ RSS ceiling verification).<br>• Documentation review, Markdown linting, and acceptance gate verification. |

---

## 3. Work Breakdown Structure (WBS) & Milestones

The project is structured into seven sequential phases:

```
Phase 0: Workspace & Scaffolding
   |
Phase 1: Deep Script & Mathematical Extraction Matrix
   |
Phase 2: Comprehensive 12-Document Specification Suite
   |
Phase 3: Backend MVC Core, Services & Repositories
   |
Phase 4: Frontend Single-Page Application & Workstations
   |
Phase 5: Automated Testing, Benchmarking & Acceptance Gate
   |
Phase 6: Deployment, System Administration & Final Release
```

### Detailed Phase Specifications

#### Phase 0: Workspace & Scaffolding
- Initialize standalone Git repository configuration and ignore rules (`.gitignore`).
- Establish `SPA/` directory structure (`config/`, `controllers/`, `services/`, `repositories/`, `models/`, `views/`, `static/`, `docs/`).
- Create initial user configuration YAMLs (`spa_paths.yaml`, `corpus_metadata.yaml`).
- *Gate*: Clean Git status in both standalone and parent repositories.

#### Phase 1: Deep Script & Mathematical Extraction Matrix
- Perform exhaustive cell-by-cell decomposition of all 186 cells in `Corpus_Analysis_tr.ipynb`.
- Catalog all 31 `corpus_toolkit/` Python modules, public interfaces, and data models.
- Document the 22 LancsBox-X diversity equations, Union-Slot collocation models, and Juilland's $D$ formulas.
- Author `12_Feature_Comparison_and_Dataflow_Matrix.md`.
- *Gate*: Matrix verified against running toolkit outputs.

#### Phase 2: Comprehensive 12-Document Specification Suite
- Author all 12 formal engineering documents in `SPA/docs/` in Simplified Technical English:
  - Batch A: `01_PRD.md`, `02_SRS.md`, `03_Use_Cases_and_User_Stories.md`.
  - Batch B: `04_SDD_Design_and_Architecture.md`, `05_ADRs.md`, `06_API_and_Interface_Specs.md`, `07_SDP_Process_and_Project_Plan.md`.
  - Batch C: `08_QA_and_Test_Plans.md`, `09_Technical_Onboarding_Guide.md`, `10_End_User_Manual.md`, `11_System_Administrator_Guide.md`.
  - Master: `13_Corpus_Analysis_SPA_Technical_Blueprint_Plan.md`.
- *Gate*: Every document ends with a validated Acceptance Gate checklist.

#### Phase 3: Backend MVC Core, Services & Repositories
- Implement Flask factory and WSGI application in `app.py` with CSP middleware.
- Construct `SPA/models/` DTO dataclasses with complete serialization contracts.
- Build `SPA/repositories/` (`config_repository.py`, `corpus_repository.py`, `nda_cache_repository.py`, `export_repository.py`).
- Enforce restricted `_NdaSafeUnpickler` security boundary.
- Implement `SPA/services/` with zero file I/O operations.
- Implement `SPA/controllers/` Flask Blueprints with DTO validation.
- *Gate*: Line count test passes for all Python modules ($\le 200$ physical lines).

#### Phase 4: Frontend Single-Page Application & Workstations
- Construct `index.html` shell with Global Control Header, Tab Navigation, and Status Footer.
- Implement responsive CSS architecture (`spa_base.css`, `spa_layout.css`, `spa_components.css`, `spa_viz.css`).
- Build core JavaScript modules (`app.js`, `api_client.js`, `datagrid.js`, `svg_connector.js`).
- Implement 11 tab workstation modules (`tabs/tab1_inventory.js` through `tab11_corpus_explorer.js`).
- Implement Help/Formula Drawer (`help_docs_drawer.js`) and Corpus Info Modal (`corpus_info_modal.js`).
- Bundle vendor dependencies locally (offline Plotly.js).
- *Gate*: Zero external network requests initiated by browser; all tabs interactive.

#### Phase 5: Automated Testing, Benchmarking & Acceptance Gate
- Implement unit tests for all DTOs, repositories, and services (`tests/test_spa_*.py`).
- Implement end-to-end API integration tests for all `/api/v1/` routes.
- Execute RSS memory stress test: verify peak usage remains $< 1{,}500\text{ MB}$.
- Verify ReDoS regex timeout protections and whitelisted unpickling security.
- Execute notebook parity test: verify tracked notebooks have 0 cell outputs and 186 cells.
- *Gate*: 100% test pass rate with pytest.

#### Phase 6: Deployment, System Administration & Final Release
- Package WSGI production runners (Gunicorn / Waitress configuration scripts).
- Verify deployment on Linux server environments.
- Validate bilingual end-user manual and administrator operations.
- Synchronize dual-repo Git commits and push to remote remotes.
- *Gate*: Final release tag `v1.0.0-spa` cut and pushed.

---

## 4. Dual-Repository Git Workflow & Invariants

The application lives within a dual-repository version control topology:
- **Subsystem Repository**: [`scripts/corpus_analysis/`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/)
  - Origin: `git@github.com:KadirYigitUS/corpus_analysis.git`
  - Canonical Branch: **`master`**
- **Parent Thesis Repository**: [`/home/ben/Documents/thesis/`](file:///home/ben/Documents/thesis/)
  - Origin: `git@github.com:KadirYigitUS/thesis.git`
  - Canonical Branch: **`main`**

### 4.1 Commit & Staging Rules

1. **Subsystem Working Directory Isolation**:
   - All Git commands directly modifying `corpus_toolkit/`, `SPA/`, or `Corpus_Analysis*.ipynb` must be executed with working directory `Cwd: /home/ben/Documents/thesis/scripts/corpus_analysis`.
   - Never commit from the parent directory while the subsystem repository has uncommitted staged changes.
2. **Commit Message Conventional Format**:
   - Format: `<type>(spa): <imperative description>`
   - Allowed Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.
   - Example: `feat(spa): implement 22 LancsBox-X diversity metrics service`
3. **Sequential Commit Protocol**:
   ```bash
   # Step 1: Commit and push within subsystem repo
   cd /home/ben/Documents/thesis/scripts/corpus_analysis
   git status
   git add SPA/ docs/
   git commit -m "feat(spa): complete Phase 2 Batch B documentation suite"
   git push origin master

   # Step 2: Synchronize parent repository submodule / pointer
   cd /home/ben/Documents/thesis
   git status
   git add scripts/corpus_analysis
   git commit -m "chore(corpus_analysis): update subsystem commit pointer"
   git push origin main
   ```
4. **Detached HEAD Prevention**:
   - Before any commit operation, verify active branch via `git branch --show-current`. If detached, execute `git checkout master` before applying edits.

---

## 5. Risk Assessment & Mitigation Matrix

| Risk ID | Risk Description | Severity | Probability | Mitigation Strategy |
|---|---|---|---|---|
| **RSK-01** | **Process RSS Memory Exceeds 1.5 GB Ceiling**<br>Simultaneous loading of multiple large novels causes OOM crash. | Critical | Moderate | Enforce content-addressed Parquet caching, single-process WSGI (`workers=1`), streaming generator `.iter_evicting()`, and proactive `.evict_all()` when RSS exceeds $1{,}200\text{ MB}$. |
| **RSK-02** | **ReDoS Vulnerability in Regex Search**<br>Pathological regex patterns trigger catastrophic backtracking, locking the server. | High | Moderate | Static pattern inspection for nested quantifiers `(x+)+` in `search_kwic_service.py`; hard $2.5\text{s}$ execution timeout; reject invalid patterns with `422 Unprocessable Entity`. |
| **RSK-03** | **Arbitrary Code Execution via Pickled NDA Caches**<br>Loading untrusted `.pickle` files executes malicious payloads. | Critical | Low | Restrict unpickling strictly through `_NdaSafeUnpickler` with an immutable class whitelist (primitives, NumPy, Pandas, NDA models). Reject unauthorized classes. |
| **RSK-04** | **Conda Base Dependency Contamination**<br>Accidental `pip install` breaks existing environment dependencies. | High | Low | Enforce strict no-install invariant (`AGENTS.md` Rule 2). All code restricted to standard library, Flask, NumPy, SciPy, Pandas, PyArrow, NetworkX, and NLTK present in base. |
| **RSK-05** | **Notebook Output Parity Drift**<br>Running test notebooks accidentally saves cell outputs or alters the 186-cell structure. | High | Moderate | Automated CI check `test_tracked_notebook_is_clean` executes pre-commit; strips outputs automatically; verifies cell count is exactly 186. |
| **RSK-06** | **Dual-Repo Merge Desynchronization**<br>Subsystem and parent git commits drift or create detached HEAD states. | Medium | Moderate | Mandatory 2-step synchronization protocol; pre-commit branch check; automated verification scripts. |
| **RSK-07** | **Codebase Bloat & Monolithic Degradation**<br>Modules expand beyond manageable size, making testing and maintenance difficult. | Medium | Moderate | Hard automated line budget gate: pre-format target $\le 180$ LOC, hard CI gate $\le 200$ LOC. Violations fail CI build automatically. |

---

## 6. Acceptance Gate Checklist

- [ ] All 7 development phases (Phase 0 through Phase 6) defined with clear deliverables and exit gates.
- [ ] 4-agent collaborative roles (Gemini 4 Argon, Claude Sonnet 5.5, GPT-OSS 120B, Gemini 3.8 Flash) formalized.
- [ ] Dual-repository Git workflow documented with exact command sequences and staging rules.
- [ ] Clean notebook gate (0 cell outputs, 186 cells) recorded as a core project invariant.
- [ ] Conda `base` no-install invariant enforced across all project phases.
- [ ] Comprehensive 7-point risk matrix documented with concrete mitigation strategies.
- [ ] Modular line budget ($\le 180$ target, $\le 200$ gate) integrated into development workflow.
