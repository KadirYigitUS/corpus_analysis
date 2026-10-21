# 05 · Architecture Decision Records (ADRs)

## 1. Overview & Decision Framework

This document records the foundational architectural decisions governing the design, implementation, security, and operation of the **Corpus Analysis Single-Page Application (SPA)** located in [`scripts/corpus_analysis/SPA/`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/SPA/).

Each Architecture Decision Record (ADR) follows the standard structure:
- **Status**: [Proposed | Accepted | Superseded | Deprecated]
- **Context**: Problem statement, constraints, empirical requirements, and evaluated alternatives.
- **Decision**: The specific technical, algorithmic, or architectural choice adopted.
- **Consequences**: Positive benefits, trade-offs, negative implications, and validation strategies.

---

## 2. Master Architecture Decision Log

| ADR ID | Decision Title | Status | Primary Component |
|---|---|---|---|
| **ADR-001** | Reuse of Canonical Analytical Engine (`corpus_toolkit/`) | Accepted | Architecture / Backend |
| **ADR-002** | Flask WSGI Microframework with Layered Blueprints | Accepted | Web Framework / WSGI |
| **ADR-003** | Content-Addressed Parquet Caching (`v3-2026-04-20`) & RSS Ceiling | Accepted | Cache / Memory Management |
| **ADR-004** | 32-Combination `TokenView` Parameter Matrix | Accepted | Text Processing / NLP |
| **ADR-005** | Turkish Lemma Apostrophe Remediation (`clean_lemma`) | Accepted | Morphology / Tokenization |
| **ADR-006** | Whitelisted Deserialization for NDA Caches (`_NdaSafeUnpickler`) | Accepted | Security / Data Access |
| **ADR-007** | Union-Slot $2\times 2$ Contingency Modeling for Collocations | Accepted | Statistics / Collocation |
| **ADR-008** | Offline Custom `displaCy` SVG Generation with Dimmed Function Words | Accepted | Syntax / Visualization |
| **ADR-009** | Virtualized HTML5 DataGrid with 20-Row Pagination | Accepted | Frontend / Presentation |
| **ADR-010** | Strict Content Security Policy (CSP) & Zero External CDN Deliveries | Accepted | Security / Infrastructure |
| **ADR-011** | Regular Expression Denial of Service (ReDoS) Timeout Guardrails | Accepted | Security / Search Engine |
| **ADR-012** | User-Configurable YAML Path and Corpus Metadata Registries | Accepted | Configuration / Extensibility |
| **ADR-013** | Professional Analytics Workstation Scope: Help/Formula Drawer | Accepted | UX / Scope Governance |

---

## 3. Individual Architecture Decision Records

### ADR-001: Reuse of Canonical Analytical Engine (`corpus_toolkit/`)

- **Status**: Accepted
- **Context**: The existing codebase [`corpus_toolkit/`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/corpus_toolkit/) contains 31 thoroughly tested modules implementing corpus loaders, alignment indexers, POS analyzers, dependency visualizers, search engines, 22 LancsBox-X diversity metrics, and report builders. Re-implementing these algorithms in the SPA web backend would introduce code duplication, divergence risks, and synchronization defects.
- **Decision**: The SPA backend shall strictly import and orchestrate the existing production modules in `corpus_toolkit/`. The SPA layer shall act strictly as an MVC/Service/Repository delivery mechanism over the canonical toolkit, introducing zero redundant analytical implementations.
- **Consequences**:
  - *Positive*: 100% mathematical and statistical parity with `Corpus_Analysis_tr.ipynb`. Zero duplication of complex metric routines.
  - *Negative*: Modifications to the toolkit API require backwards compatibility or synchronized updates to both the notebook generators and the SPA.
  - *Mitigation*: Comprehensive automated regression test suite (`tests/`) running against both CLI and web endpoints.

---

### ADR-002: Flask WSGI Microframework with Layered Blueprints

- **Status**: Accepted
- **Context**: The application requires a lightweight, robust Python HTTP server to expose REST endpoints for a single-page frontend. Evaluated options included FastAPI, Django, Tornado, and Flask. FastAPI introduces additional dependencies (`pydantic`, `anyio`) not present in the strict Conda `base` environment where package installations are prohibited (`AGENTS.md` Rule 2).
- **Decision**: Adopt standard **Flask WSGI** utilizing modular Flask Blueprints (`SPA/controllers/`) organized by domain (config, corpus, alignment, syntax, concordance, lexicon, export).
- **Consequences**:
  - *Positive*: Full compatibility with existing Conda `base` environment. Native WSGI compatibility with production runners (Gunicorn, Waitress). Minimal runtime overhead.
  - *Negative*: Lack of native asynchronous ASGI primitives for long-running batch calculations.
  - *Mitigation*: Synchronous chunked streaming responses, threaded execution pool (`threads = 4`), and progressive client-side polling for long-running exports.

---

### ADR-003: Content-Addressed Parquet Caching (`v3-2026-04-20`) & RSS Ceiling

- **Status**: Accepted
- **Context**: Parsing raw TSV files for 13 novels (over 1.5 million tokens) on every HTTP request induces severe latency ($> 8\text{ seconds}$). Caching entire parsed DataFrames in memory causes process memory to rapidly exceed the system ceiling ($> 3\text{ GB}$), leading to kernel Out-Of-Memory (OOM) terminations.
- **Decision**: Utilize content-addressed Apache Parquet caching governed by `SCHEMA_VERSION = "v3-2026-04-20"` in `data/corpus_analysis/.cache/`. Cache keys are constructed via $\text{SHA256}(\text{schema}, \text{namespace}, \text{args})[:20]$. Implement an explicit memory ceiling ($< 1{,}500\text{ MB}$ RSS) with proactive `.evict()` and streaming `.iter_evicting()` methods in `CorpusRepository`.
- **Consequences**:
  - *Positive*: Sub-100ms disk reload times for token and sentence DataFrames. Process memory guaranteed to remain below $1.5\text{ GB}$.
  - *Negative*: Parquet cache invalidation must be handled when underlying TSV files or schema versions change.
  - *Mitigation*: Global UI cache badge displays active disk size and provides a manual "Clear Cache" button (`/api/v1/corpus/cache/evict`).

---

### ADR-004: 32-Combination `TokenView` Parameter Matrix

- **Status**: Accepted
- **Context**: Corpus linguistic research requires switching between raw tokens, morphological lemmas, closed-class filtered views, masked positions, and multiple punctuation handling strategies. A rigid view leads to skewed statistical conclusions.
- **Decision**: Implement full parameterization supporting all $2 \times 2 \times 2 \times 4 = 32$ configurations of:
  $$\{\text{tok}, \text{lem}\} \times \{\text{False}, \text{True}\} \times \{\text{drop}, \text{mask}\} \times \{\text{drop}, \text{keep}, \text{strip}, \text{split}\}$$
  Closed-class filtering enforces UPOS-only for English and dual UPOS + Oflazer morphological head classification for Turkish.
- **Consequences**:
  - *Positive*: Unprecedented research precision and flexibility across all 11 SPA tabs. Full compatibility with LancsBox-X and NLTK conventions.
  - *Negative*: High state space for caching and cache-key proliferation.
  - *Mitigation*: Standardized `TokenViewParamsDTO` normalizes query parameters into deterministic hash keys.

---

### ADR-005: Turkish Lemma Apostrophe Remediation (`clean_lemma`)

- **Status**: Accepted
- **Context**: Turkish NLP pipelines (including Stanza/Zemberek) frequently attach apostrophes and following inflectional case suffixes to the lemma (e.g., `türkiye'nin` instead of `türkiye`, `1882'de` instead of `1882`). However, legitimate hyphenated compound nouns (e.g., `bilim-kurgu`) must not be split.
- **Decision**: Enforce canonical lemma cleaning via `textutil.clean_lemma()`. The algorithm strips all inflectional suffixes appearing after the first apostrophe from the universal set $\{', ’ , ‘ , ` , ´ , ʼ , ʻ\}$ while strictly preserving hyphens and preventing empty-string collapses for isolated punctuation marks.
- **Consequences**:
  - *Positive*: Accurate type counts, valid TTR/MATTR calculations, and clean dictionary lookups without agglutinative suffix contamination.
  - *Negative*: Highly specialized proper nouns with non-standard apostrophe orthography might have valid root characters truncated.
  - *Mitigation*: Apostrophe cleaning only triggers when an apostrophe variant is present; raw token representations remain intact in `tok` field.

---

### ADR-006: Whitelisted Deserialization for NDA Caches (`_NdaSafeUnpickler`)

- **Status**: Accepted
- **Context**: Neologism Dictionary Annotation (NDA) caches are stored as Python `.pickle` files (`scored_alignment_rows.pickle`, `initial_dictionary.pickle`). Standard `pickle.load()` is vulnerable to arbitrary remote code execution (RCE) via `__reduce__` exploit payloads.
- **Decision**: Implement a restricted unpickling subclass `_NdaSafeUnpickler` in `NdaCacheRepository`. Overwrite `find_class(module, name)` to enforce a strict whitelist permitting only primitive builtins (`dict`, `list`, `set`, `tuple`, `int`, `float`, `str`, `bool`), NumPy data types, Pandas DataFrames/Indexes, and verified internal NDA dataclasses. All other classes raise `pickle.UnpicklingError`.
- **Consequences**:
  - *Positive*: Complete mitigation of arbitrary code execution vulnerabilities during cache ingestion.
  - *Negative*: Loading new serialized custom objects requires explicit additions to the whitelist.
  - *Mitigation*: Whitelist is centralized and documented in `nda_cache_repository.py`.

---

### ADR-007: Union-Slot $2\times 2$ Contingency Modeling for Collocations

- **Status**: Accepted
- **Context**: In bidirectional collocation analysis within a span $[-L, +R]$, multiple occurrences of the same collocate type within the window can artificially inflate observed frequencies $O_{11}$ beyond the marginal totals ($R_1$ or $C_1$), violating the axioms of hypergeometric and multinomial distribution models.
- **Decision**: Adopt the **Union-Slot contingency table model** where:
  $$R_1 = \left|\bigcup_{i=1}^{k} \text{slots}(\text{node}_i)\right|$$
  This mathematical formulation guarantees $O_{11} \le R_1$ and $O_{11} \le C_1$. All 6 association metrics ($\text{MI}, \text{MI}^2, \text{MI}^3, T\text{-score}, \text{signed } G^2, \text{Log-Dice}$) are derived from this consistent $2 \times 2$ matrix.
- **Consequences**:
  - *Positive*: Strict mathematical validity; eliminates impossible probabilities and negative expected values. Full parity with LancsBox-X and Sketch Engine.
  - *Negative*: Slightly higher computation time during window extraction due to set-union aggregation.
  - *Mitigation*: Vectorized NumPy slice indexing over contiguous sentence arrays.

---

### ADR-008: Offline Custom `displaCy` SVG Generation with Dimmed Function Words

- **Status**: Accepted
- **Context**: Visualizing syntactic dependency trees typically requires loading Spacy's heavy web assets or rendering via external services. External CDNs violate security guidelines, and default tree renderers clutter visual analysis by highlighting function words identically to content words.
- **Decision**: Build an offline SVG generator in `depviz_service.py` that implements manual SVG arc rendering. The renderer applies the Universal Dependencies (UD) tag mappings, positions dependent arcs left/right based on head offsets, and automatically sets `opacity: 0.4` on function words ($\text{DET}, \text{ADP}, \text{CCONJ}, \text{AUX}, \text{SCONJ}$).
- **Consequences**:
  - *Positive*: Zero external network requests. Crystal-clear visual hierarchy emphasizing lexical-predicate relations.
  - *Negative*: Complex manual SVG coordinate calculations for curved Bezier arcs.
  - *Mitigation*: Reuses proven layout formulas from `corpus_toolkit/depviz.py`.

---

### ADR-009: Virtualized HTML5 DataGrid with 20-Row Pagination

- **Status**: Accepted
- **Context**: Displaying hundreds of thousands of concordance hits or diversity metrics directly in browser DOM elements causes catastrophic browser UI lag, DOM thrashing, and high client-side memory usage.
- **Decision**: Implement a lightweight, virtualized HTML5 DataGrid component (`datagrid.js`). The component renders a fixed 20-row viewport with client-side sortable headers, column resize splitters, and fast page navigation.
- **Consequences**:
  - *Positive*: Instantaneous rendering ($< 16\text{ms}$ frame time), negligible DOM footprint, smooth user experience across large query results.
  - *Negative*: In-browser text selection across entire multi-page result sets is not native.
  - *Mitigation*: Dedicated "Export to TSV / Clipboard" buttons provide immediate access to complete result sets.

---

### ADR-010: Strict Content Security Policy (CSP) & Zero External CDN Deliveries

- **Status**: Accepted
- **Context**: Digital Humanities research applications must function in offline, air-gapped, or privacy-restricted campus network environments. Relying on Google Fonts, unpkg, or CDNJS exposes user queries to external tracking and causes runtime failure when offline.
- **Decision**: Enforce a strict HTTP Content Security Policy (CSP):
  `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; font-src 'self';`
  All JavaScript libraries (e.g., Plotly.js) and typography are bundled locally within `SPA/static/assets/vendor/`.
- **Consequences**:
  - *Positive*: Total air-gapped resilience, zero third-party telemetry, robust defense against cross-site scripting (XSS).
  - *Negative*: Repository size increases slightly to store local asset bundles (~3 MB).
  - *Mitigation*: Asset bundles are committed once and cached aggressively by the browser via HTTP `Cache-Control` headers.

---

### ADR-011: Regular Expression Denial of Service (ReDoS) Timeout Guardrails

- **Status**: Accepted
- **Context**: Providing arbitrary regex search functionality across millions of tokens allows malicious or accidental entry of catastrophic backtracking patterns (e.g., `(a+)+$`), freezing the single-threaded WSGI backend indefinitely.
- **Decision**: Implement regular expression execution safeguards in `search_kwic_service.py`:
  1. Regex pattern static analysis to detect nested quantifiers before compilation.
  2. Signal-based or subprocess execution timeout capped strictly at $2.5\text{ seconds}$ per text.
  3. Pre-flight query validation returning `422 Unprocessable Entity` for identified hazardous patterns.
- **Consequences**:
  - *Positive*: Backend immunity against accidental or hostile ReDoS denial-of-service freezes.
  - *Negative*: Highly complex legitimate multi-token regex searches might encounter timeout limits.
  - *Mitigation*: Clear error messaging guiding users to refine queries using POS filters or bounded lookaheads.

---

### ADR-012: User-Configurable YAML Path and Corpus Metadata Registries

- **Status**: Accepted
- **Context**: Hardcoding filesystem paths for raw TSV files, NDA caches, or output directories impairs portability across developer workstations, cluster nodes, and lab machines. Researchers also need to customize book metadata and upload new cover/author portrait images without touching source code.
- **Decision**: Externalize all path and metadata configurations into two user-editable YAML files:
  - `SPA/config/spa_paths.yaml`: Absolute and relative filesystem locations for caches, TSVs, exports, and assets.
  - `SPA/config/corpus_metadata.yaml`: 13-book bibliographic records, author/translator biographical data, and image mappings.
  Provide interactive UI editing via the Settings Modal backed by REST endpoints (`/api/v1/config/*`).
- **Consequences**:
  - *Positive*: Complete platform portability; researchers can manage assets and source tables without modifying code.
  - *Negative*: File permissions and path validation must be enforced on every write operation.
  - *Mitigation*: `ConfigRepository` validates directory existence, write permissions, and image MIME types (`image/png`, `image/jpeg`, `image/webp`) before committing YAML updates.

---

### ADR-013: Professional Analytics Workstation Scope: Help/Formula Drawer

- **Status**: Accepted
- **Context**: Early concept drafts proposed embedding introductory literary essays, sociological theory explainers, and student self-testing quizzes inside the SPA UI. This clutters the analytics workstation, distracts expert researchers, and increases code maintenance costs.
- **Decision**: Strictly isolate the application scope to a **Professional Analytics Workstation**. Remove all essay prose and pedagogical quizzes from the main interface. Provide a dedicated, non-intrusive **Help & Calculation Formula Drawer** (`help_docs_drawer.js` / `/api/v1/help/formulas`) accessible via a persistent `[?]` button. The drawer strictly contains operational usage manuals, exact mathematical equations, edge-case/`NaN` handling rules, and primary peer-reviewed literature citations.
- **Consequences**:
  - *Positive*: Clean, high-density, professional UI focused entirely on research analytics and data discovery.
  - *Negative*: Introductory users must consult external thesis documentation for historical literary context.
  - *Mitigation*: Help Drawer provides direct bibliographic links and APA 7 citations for all theoretical grounding.

---

## 4. Acceptance Gate Checklist

- [ ] All 13 ADRs documented with complete Status, Context, Decision, and Consequences sections.
- [ ] Direct references to canonical toolkit reuse (`corpus_toolkit/`) and Conda `base` environment constraints established.
- [ ] Parquet cache versioning (`v3-2026-04-20`) and $< 1{,}500\text{ MB}$ RSS memory ceiling recorded in ADR-003.
- [ ] Deserialization security whitelist (`_NdaSafeUnpickler`) formally recorded in ADR-006.
- [ ] Union-slot collocation contingency table ($R_1 = |\bigcup \text{slots}|$) formalized in ADR-007.
- [ ] Air-gapped CSP and local asset mandates formalized in ADR-010.
- [ ] ReDoS guardrails and query timeout parameters specified in ADR-011.
- [ ] User configurability for paths and metadata recorded in ADR-012.
- [ ] Professional workstation scope isolation (Help/Formula Drawer) established in ADR-013.
