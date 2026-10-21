# Use Cases and User Stories: Corpus Analysis Single-Page Application (SPA)

**Document Version:** `v1.0-2026-10-21`  
**Repository Subsystem:** [`/home/ben/Documents/thesis/scripts/corpus_analysis/SPA/`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/SPA/)  
**Target Environment:** Standalone Git Repository (`git@github.com:KadirYigitUS/corpus_analysis.git`, branch `master`), Conda `base` (Python 3.12+, zero external packages)  
**Parent PRD:** [`/home/ben/Documents/thesis/scripts/corpus_analysis/SPA/docs/01_PRD.md`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/SPA/docs/01_PRD.md)  
**Parent SRS:** [`/home/ben/Documents/thesis/scripts/corpus_analysis/SPA/docs/02_SRS.md`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/SPA/docs/02_SRS.md)  

---

## 1. Actor Profiles & Operational Roles

| Actor Identifier | Professional Role | Analytical Responsibilities & Operational Goals | System Access Needs |
|---|---|---|---|
| **ACT-01** | Quantitative Corpus Linguist | Evaluates vocabulary richness growth, lexical diversity ($TTR$, $MATTR$, $MTLD$, $HD\text{-}D$), and POS frequency profiles across translated and indigenous texts without length or punctuation bias. | Global Header, Tabs 1, 4, 8, Help Drawer. |
| **ACT-02** | Translation Studies Researcher | Investigates sentence alignment structures ($1:1$, $1:N$, $N:1$, $N:M$, omissions), length deltas ($\Delta s, \Delta w, \Delta c$), parallel texts, and Neologism Dictionary Annotation (NDA) bilingual link attributions. | Tabs 2, 3, 5, 6, Corpus Info Modal. |
| **ACT-03** | Computational Lexicographer | Conducts complex multi-term lemma searches, analyzes union-slot collocation association scores ($MI, MI^2, MI^3, T, G^2, \text{Log-Dice}$), inspects Juilland's $D$ dispersion, and tests significance. | Tabs 6, 7, 9, 10, 11, Help Drawer. |
| **ACT-04** | Research Software Engineer (Admin) | Manages system paths (`spa_paths.yaml`), verifies filesystem integrity, configures cache policies, monitors process RSS memory, and uploads book/author imagery. | Global Header, Settings Modal, Corpus Info Modal. |

---

## 2. System Preconditions & Global Invariants

1. **Local Server Operational**: The Flask WSGI backend (`app.py`) is executing locally under Conda `base` on `http://127.0.0.1:5000/`.
2. **Corpus Files Present**: All 13 raw TSV corpus files and NDA cache directories exist in the configured locations.
3. **Parquet Cache Intact**: The atomic Parquet cache directory (`.cache/`) is readable and writable with schema version `v3-2026-04-20`.
4. **Zero External Requests**: The client browser loads all resources locally without initiating external requests to third-party CDNs.
5. **Memory Envelope**: The Python server process enforces an RSS memory ceiling $< 1.5\text{ GB}$.

---

## 3. Global Control Bar & Cross-Cutting Modals

### Use Case UC-01: Configure Scope, 32-Combination TokenView & Monitor Memory
- **Primary Actor**: ACT-01 (Corpus Linguist), ACT-02 (Translation Researcher)
- **Preconditions**: SPA loaded in browser; backend running.
- **Postconditions**: Active analytical views reflect selected text scope and tokenization parameters; memory gauge reflects current RSS.
- **User Story**:
  - *As a* quantitative corpus researcher,
  - *I want to* select from 8 corpus loader scopes and toggle between all 32 `TokenView` parameter configurations (field, filter, mode, punctuation),
  - *So that* I can evaluate linguistic patterns without punctuation or closed-class distortions while keeping server memory below 1.5 GB.
- **Scenario 1.1: Switching Corpus Scope and TokenView Configuration**:
  - **Given** the user is viewing any analytical tab in the SPA,
  - **When** the user selects `load_all_turkish()` from the Scope dropdown and toggles `field='lem'`, `filter_function_words=True`, `mode='drop'`, and `punct='strip'`,
  - **Then** `app_state.js` dispatches an `app:state-changed` event,
  - **And** all active tab widgets refresh their datasets using the requested 32-combination view,
  - **And** the Live RSS Gauge updates its memory reading in megabytes.
- **Scenario 1.2: Triggering Process Memory Eviction**:
  - **Given** the Live RSS Gauge indicates memory consumption exceeding 1,000 MB,
  - **When** the user clicks the `Evict RAM` button in the Global Header,
  - **Then** the frontend issues `POST /api/v1/corpus/evict`,
  - **And** the server releases in-memory cached DataFrames via `loader.evict_all()`,
  - **And** the RSS memory indicator drops below 300 MB without losing UI tab state.

### Use Case UC-02: Inspect Corpus Dossier, Book Covers & Author Portraits
- **Primary Actor**: ACT-02 (Translation Researcher), ACT-04 (Admin)
- **Preconditions**: Corpus metadata and visual assets configured.
- **Postconditions**: User views authenticated cover art, portrait photographs, and metadata records.
- **User Story**:
  - *As a* translation scholar,
  - *I want to* inspect high-resolution book covers, author/translator portraits, and source metadata,
  - *So that* I can verify historical publication details, translator roles, and physical text provenance.
- **Scenario 2.1: Viewing Book Covers and Author Portraits**:
  - **Given** the user is on any workstation tab,
  - **When** the user clicks the `Corpus Info` button in the Global Header,
  - **Then** `corpus_info_modal.js` displays a modal with 4 tabs: `Source Texts`, `Translations`, `Indigenous`, and `Alignment Pairs`,
  - **And** each book entry renders a high-resolution book cover card, publication year, publisher imprint, and SHA-256 checksum,
  - **And** each author entry renders an authenticated biographical portrait card with literary role and active dates.
- **Scenario 2.2: Uploading a New Book Cover or Portrait Image**:
  - **Given** the user has opened the `Corpus Info` modal,
  - **When** the user selects an entity card, chooses an image file (`.jpg`, `.png`, `.webp`), and clicks `Upload Asset`,
  - **Then** the client submits `POST /api/v1/config/upload-image`,
  - **And** the server stores the image in the configured image directory and updates `corpus_metadata.yaml`,
  - **And** the modal immediately updates the visual card without page reload.

### Use Case UC-03: Validate System Paths, YAML Configuration & Cache Retention
- **Primary Actor**: ACT-04 (System Administrator)
- **Preconditions**: Administrator desires to inspect or update server paths or cache parameters.
- **Postconditions**: Server paths and cache policies are updated and persisted to disk.
- **User Story**:
  - *As a* research software engineer,
  - *I want to* validate filesystem paths, edit `spa_paths.yaml`, and configure cache retention policies in the UI,
  - *So that* the application operates reliably across diverse server filesystem environments.
- **Scenario 3.1: Validating Server Paths and Editing YAML**:
  - **Given** the user clicks the `Settings & Paths` gear button in the Global Header,
  - **When** the user inspects the configured directories for TSV data, Parquet cache, and report exports,
  - **Then** the modal displays green health badges for valid readable/writable paths,
  - **And** allows editing the YAML content with real-time syntax checking,
  - **And** clicking `Save Configuration` persists changes to disk and reloads system repositories.
- **Scenario 3.2: Modifying Cache Retention Policy**:
  - **Given** the user is in the `Settings & Paths` modal,
  - **When** the user changes the startup cache policy from `keep` to `clear` and sets the LRU threshold to 4,096 MB,
  - **Then** the server updates its internal `CorpusCacheManager` settings,
  - **And** displays confirmation of total cached files and current disk consumption.

### Use Case UC-04: Consult Mathematical Formulas, Edge-Case Guards & Citations
- **Primary Actor**: ACT-01 (Corpus Linguist), ACT-03 (Lexicographer)
- **Preconditions**: User requires exact mathematical definitions or methodological citations.
- **Postconditions**: Help drawer displays exact LaTeX formulas, parameter definitions, and Zotero-linked citations.
- **User Story**:
  - *As a* quantitative linguist,
  - *I want to* inspect exact mathematical formulas, boundary conditions, and primary methodological citations,
  - *So that* my research papers adhere strictly to scientific standards and data-first epistemology.
- **Scenario 4.1: Opening Formula Drawer from Metric Tooltip**:
  - **Given** the user is analyzing metrics in Tab 8 (Lexical Diversity) or Tab 9 (Collocations),
  - **When** the user clicks the formula button (`ƒx`) adjacent to `MATTR` or `Log-Dice`,
  - **Then** `help_docs_drawer.js` slides open from the right edge,
  - **And** automatically scrolls to the exact mathematical definition, closed-form equation, and edge-case guards,
  - **And** displays canonical citations (e.g., Covington & McFall 2010, Rychlý 2008) with DOI links.

---

## 4. Analytical Workstation Tab Use Cases & User Stories

### Use Case UC-05: Tab 1 — Inspect Inventory, Schema Tables & Token Distribution
- **Primary Actor**: ACT-01 (Corpus Linguist), ACT-02 (Translation Researcher)
- **Preconditions**: Corpus inventory loaded in `corpus_registry`.
- **Postconditions**: User examines text counts, schema layouts, and token distribution plots.
- **User Story**:
  - *As a* researcher,
  - *I want to* inspect the 13-text pioneer corpus inventory, examine DataFrame schemas, and view running token totals,
  - *So that* I understand corpus composition before executing statistical analyses.
- **Scenario 5.1: Filtering Inventory and Viewing Figure 1**:
  - **Given** the user navigates to Tab 1 (Corpus Inventory),
  - **When** the user clicks the `SM` author filter pill,
  - **Then** the 20-row DataGrid filters to display texts by Selma Mine (`IR-IA`, `BR-SM`, `OBI-SM`),
  - **And** Figure 1 (Token Size Horizontal Bar Chart) updates to highlight token lengths across the selected texts.
- **Scenario 5.2: Inspecting DataFrame Schemas**:
  - **Given** the user selects text `BR-SM` in Tab 1,
  - **When** the user clicks `Inspect Schema`,
  - **Then** the UI displays the first 10 rows and data types (`int32`, `category`, `object`) of both `tokens` and `sentences` DataFrames.

### Use Case UC-06: Tab 2 — Explore Sentence Alignment, Cardinality & Length Deltas
- **Primary Actor**: ACT-02 (Translation Researcher)
- **Preconditions**: Aligned translation pairs available.
- **Postconditions**: Alignment shapes, cardinality ratios, and length delta tables are displayed.
- **User Story**:
  - *As a* translation scholar,
  - *I want to* analyze sentence alignment cardinalities ($1:1, 1:N, N:1, N:M$), length ratios, and length deltas,
  - *So that* I can identify omissions, additions, and translation expansion strategies.
- **Scenario 6.1: Evaluating Cardinality and Sentence Ratios**:
  - **Given** the user selects pair `IR-IA_BR-SM` in Tab 2,
  - **When** the page renders,
  - **Then** top KPI cards display total units ($ai$), sentence ratio $R_{\text{sent}}$, word ratio, and character ratio,
  - **And** the cardinality table categorizes alignment groups into $1:1$, $1:N$, $N:1$, $N:M$, omissions, and additions,
  - **And** Figure 1B displays an interactive scatter plot of English vs. Turkish sentence lengths.
- **Scenario 6.2: Sorting by Length Deltas and Navigating Chapters**:
  - **Given** the user clicks Chapter 3 in the left sidebar,
  - **When** the user sorts the table by Character Delta ($\Delta c$) descending,
  - **Then** the rows reorder to show sentences with the highest text expansion,
  - **And** each row renders sentence boundaries marked with golden separator badges (`‖`).

### Use Case UC-07: Tab 3 — Examine NDA Parallel Text, Tripartite Dictionary & SVG Links
- **Primary Actor**: ACT-02 (Translation Researcher), ACT-03 (Lexicographer)
- **Preconditions**: NDA cache hydrated for the active translation pair.
- **Postconditions**: Bilingual parallel text rendered with 4 disjoint visual sets, stepped SVG links, and tripartite dictionary.
- **User Story**:
  - *As a* neologism researcher,
  - *I want to* inspect aligned bilingual sentences with overlaid neologism annotations, tripartite dictionary drawers, and stepped SVG connector lines,
  - *So that* I can trace how science fiction terms and irrealia are translated into Turkish.
- **Scenario 7.1: Viewing Disjoint Sets and SVG Connector Arcs**:
  - **Given** the user is viewing alignment rows in Tab 3 for `I_Robot`,
  - **When** alignment rows render,
  - **Then** Linked Bilingual Pairs appear in blue (`#bfdbfe`) with `L#` superscript badges,
  - **And** Unlinked Irrealia appear in teal (English) and rose (Turkish),
  - **And** Neologism Candidates appear in amber-yellow (`#fef08a`),
  - **And** responsive stepped SVG arcs connect corresponding English and Turkish link tokens.
- **Scenario 7.2: Filtering via Tripartite Global Dictionary**:
  - **Given** the user opens the Tripartite Global Dictionary drawer in Tab 3,
  - **When** the user clicks on dictionary item `positronic brain` $\leftrightarrow$ `pozitronik beyin`,
  - **Then** the parallel view automatically scrolls to and highlights all alignment rows containing that pair,
  - **And** the Current Label Attributions footer updates its occurrence metrics.

### Use Case UC-08: Tab 4 — Profile Comparative Universal POS & Bootstrap Confidence Intervals
- **Primary Actor**: ACT-01 (Corpus Linguist)
- **Preconditions**: Parsed Universal POS data available across texts.
- **Postconditions**: 17-tag UPOS tables, lexical density, Turkish deverbal share, and bootstrap 95% CIs are rendered.
- **User Story**:
  - *As a* quantitative linguist,
  - *I want to* compare 17-tag Universal POS profiles and calculate bootstrap 95% confidence intervals,
  - *So that* I can detect structural morphosyntactic shifts between translated and indigenous Turkish.
- **Scenario 8.1: Calculating Lexical Density and Deverbal Share**:
  - **Given** the user selects `load_all_turkish()` in Tab 4,
  - **When** the POS profiler completes execution,
  - **Then** the table displays raw counts and percentages for all 17 UPOS tags,
  - **And** reports Lexical Density percentage, Noun/Verb ratio, and Turkish Deverbal Suffix Share (`+Inf`/`Part`).
- **Scenario 8.2: Group Comparison with Bootstrap 95% Confidence Intervals**:
  - **Given** the user compares Group A (Translations) against Group B (Indigenous),
  - **When** the user clicks `Run Bootstrap (N=2000)`,
  - **Then** the server runs 2,000 bootstrap iterations with fixed `seed=13`,
  - **And** Figure 2C displays group comparison bars with exact 95% confidence interval error bars,
  - **And** reports pooled $\chi^2$ and Cramér's $V$ statistics.

### Use Case UC-09: Tab 5 — Visualize Syntactic Dependency Trees & Bilingual ClearNLP/UD
- **Primary Actor**: ACT-01 (Corpus Linguist), ACT-02 (Translation Researcher)
- **Preconditions**: CoNLL-U parsed dependency annotations present.
- **Postconditions**: Interactive SVG dependency trees rendered with UD tags and function-word dimming.
- **User Story**:
  - *As a* syntactic researcher,
  - *I want to* view interactive `displaCy` SVG dependency trees and CoNLL tables for English and Turkish sentences,
  - *So that* I can compare clause structures and grammatical relations between source and translation.
- **Scenario 9.1: Rendering Stacked Bilingual Dependency Trees**:
  - **Given** the user enters sentence coordinate `(BR-SM, 4, 12, 1)`,
  - **When** the user clicks `Render Tree`,
  - **Then** Tab 5 renders CoNLL-U token tables and an interactive SVG dependency tree,
  - **And** maps English ClearNLP tags to UD standards (`dobj` $\to$ `obj`),
  - **And** generates arcs with correct direction ($\text{dir} = \text{'left'}$ when dependent precedes head).
- **Scenario 9.2: Dimming Function Words**:
  - **Given** the user is viewing a complex dependency tree,
  - **When** the user toggles the `Dim Function Words` switch,
  - **Then** arcs connecting closed-class function words transition to `opacity: 0.4`,
  - **And** content word relationships remain highlighted for immediate syntactic inspection.

### Use Case UC-10: Tab 6 — Execute Advanced Corpus Search & 5-View KWIC Concordance
- **Primary Actor**: ACT-01 (Corpus Linguist), ACT-03 (Lexicographer)
- **Preconditions**: Corpus texts loaded in memory or Parquet cache.
- **Postconditions**: Multi-term search results and 5 KWIC concordance views rendered.
- **User Story**:
  - *As a* lexicographer,
  - *I want to* search words using exact, glob, or regex patterns with Turkish `İ/I` folding and view results in 5 KWIC modes,
  - *So that* I can analyze context patterns, relative offset collocations, and bilingual sentence alignments.
- **Scenario 10.1: Searching with Turkish Apostrophe Remediation and Glob Matching**:
  - **Given** the user enters search query `robot*` with `field='lem'` and `match='glob'`,
  - **When** the search executes,
  - **Then** the engine matches stems correctly regardless of suffix inflection (`robotlar`, `robotik`),
  - **And** applies `clean_lemma` to strip apostrophe suffixes,
  - **And** reports total hit count and normalized frequency per 10k running words.
- **Scenario 10.2: Switching Between 5 KWIC Concordance Views**:
  - **Given** the user has search hits for query `uzay`,
  - **When** the user switches between view tabs `kwic`, `coords`, `bilingual`, `parallel`, and `table`,
  - **Then** the display changes seamlessly from traditional KWIC to bilingual aligned cards or DataGrid tables,
  - **And** allows sorting lines by right context $R_1$ or left context $L_1$ using Turkish collation.

### Use Case UC-11: Tab 7 — Compute Batch Juilland's $D$ Dispersion & BH-FDR Correlations
- **Primary Actor**: ACT-03 (Lexicographer), ACT-01 (Corpus Linguist)
- **Preconditions**: User specifies a list of lexical items.
- **Postconditions**: 10-chunk Juilland's $D$ dispersion, barcode strips, correlation heatmaps, and BH-FDR $q$-values computed.
- **User Story**:
  - *As a* corpus analyst,
  - *I want to* analyze the dispersion of term sets across 10 text chunks and compute pairwise correlations with BH-FDR corrections,
  - *So that* I can distinguish evenly distributed genre vocabulary from clustered thematic bursts.
- **Scenario 11.1: Calculating 10-Chunk Juilland's $D$ Dispersion**:
  - **Given** the user submits a batch list of 10 science fiction keywords,
  - **When** the analyzer processes the active corpus scope,
  - **Then** each text is partitioned into $n = 10$ equal position slices,
  - **And** calculates Juilland's $D = 1 - \frac{V}{\sqrt{n - 1}}$ both across texts and within texts,
  - **And** renders Figure 3A barcode strips showing hit positions across chunks.
- **Scenario 11.2: Evaluating Pairwise Correlations with Benjamini–Hochberg FDR**:
  - **Given** the batch analysis results are loaded,
  - **When** the user views the Pairwise Correlation tab,
  - **Then** Tab 7 renders interactive heatmaps of Pearson $r$, Spearman $\rho$, and Cosine similarity,
  - **And** calculates Benjamini–Hochberg adjusted $q$-values, marking statistically significant correlations ($q < 0.05$).

### Use Case UC-12: Tab 8 — Calculate 22 LancsBox-X Diversity Metrics & MATTR Trajectories
- **Primary Actor**: ACT-01 (Corpus Linguist)
- **Preconditions**: Texts selected; TokenView configured.
- **Postconditions**: 22-column diversity DataGrid, MATTR trajectories, 6-axis radar, and Zipf plots rendered.
- **User Story**:
  - *As a* quantitative stylometrician,
  - *I want to* compute the full 22-column LancsBox-X diversity table with $O(N)$ sliding-window MATTR,
  - *So that* I can evaluate vocabulary richness across texts of unequal length without sample size bias.
- **Scenario 12.1: Generating 22-Column LancsBox-X Table**:
  - **Given** the user is on Tab 8 with all 13 texts selected,
  - **When** the user clicks `Compute Diversity Table`,
  - **Then** the system evaluates all 22 metrics ($TTR, \text{Guiraud } R, \text{CTTR}, \text{Herdan } C, \text{Dugast } U, \text{Maas } a^2, \text{Yule } K, \text{Simpson } D, \text{Honoré } R, \text{Hapax \%}, \text{STTR}, \text{MATTR}_{50/100/500}, \text{MTLD}, \text{HD-D}, \text{Sichel } S, \text{Michéa } M, \text{Entropy } H$),
  - **And** renders a 20-row sortable DataGrid with full edge-case and `NaN` guards.
- **Scenario 12.2: Adjusting MATTR Window Slider and Viewing Trajectories**:
  - **Given** the user adjusts the MATTR window slider to $w = 250$,
  - **When** the update triggers,
  - **Then** the $O(N)$ sliding-window algorithm recomputes rolling TTR in $< 200\text{ ms}$,
  - **And** Figure 4B updates its trajectory curves across the full token length of each text.

### Use Case UC-13: Tab 9 — Analyze Union-Slot Collocations & GraphColl Radial Visualizations
- **Primary Actor**: ACT-03 (Lexicographer)
- **Preconditions**: Node term specified; span window defined.
- **Postconditions**: Union-slot contingency table, 6 association measures, and GraphColl scatter plot rendered.
- **User Story**:
  - *As a* lexicographer,
  - *I want to* calculate collocation association scores using union-slot context modeling and explore GraphColl plots,
  - *So that* I can discover strong lexical affinities and genre-specific multi-word expressions.
- **Scenario 13.1: Computing Association Scores under Union-Slot Modeling**:
  - **Given** the user inputs node term `insan` with span $L = 5, R = 5$ and `sentence_clamped=True`,
  - **When** the collocator processes the text,
  - **Then** it computes union context size $R_1$, contingency frequencies $O_{11}, C_1$, and expected frequency $E_{11} = \frac{R_1 \cdot C_1}{N}$,
  - **And** computes 6 association measures: $MI, MI^2, MI^3, T\text{-score}, G^2$ (signed), and Rychlý's $\text{Log-Dice}$.
- **Scenario 13.2: Exploring GraphColl Radial Scatter Plot**:
  - **Given** collocation results are generated,
  - **When** the user views Figure 5 (GraphColl Radial Scatter Plot),
  - **Then** collocates are plotted with association strength on the $x$-axis and statistical evidence on the $y$-axis,
  - **And** hovering over any collocate node reveals contingency counts and exact score values.

### Use Case UC-14: Tab 10 — Fit Sublinear TF-IDF Keyness & Generate Research Bundles
- **Primary Actor**: ACT-01 (Corpus Linguist), ACT-03 (Lexicographer)
- **Preconditions**: Texts selected; export directory configured.
- **Postconditions**: Top-$K$ TF-IDF keywords rendered; reproducible ZIP archive generated and downloaded.
- **User Story**:
  - *As a* researcher,
  - *I want to* compute sublinear TF-IDF keyness with proper-noun ablation and export reproducible research bundles,
  - *So that* I can document analytical findings in publications with full data provenance.
- **Scenario 14.1: Fitting Sublinear TF-IDF with PROPN Exclusion**:
  - **Given** the user is on Tab 10,
  - **When** the user enables `Exclude PROPN` and sets top-$K = 15$,
  - **Then** the engine fits separate models for English and Turkish using $\text{TF} = 1 + \ln(\text{count})$ and smooth $\text{IDF}$,
  - **And** Figure 6 displays horizontal bar charts of the top 15 keyness terms per text without proper-name bias.
- **Scenario 14.2: Exporting Atomic Research Bundle (ZIP)**:
  - **Given** the user has completed an analytical workflow across multiple tabs,
  - **When** the user clicks `Export Research Bundle`,
  - **Then** the server compiles active figures, tables, and provenance metadata into an atomic ZIP archive containing `.md` report, `.tsv` tables, 300-DPI `.png` charts, and multi-sheet `.xlsx`,
  - **And** prompts the user for local browser download while saving a copy in the configured export directory.

### Use Case UC-15: Tab 11 — Execute Scriptable Unified Queries with Python Code Generation
- **Primary Actor**: ACT-03 (Lexicographer), ACT-04 (Admin)
- **Preconditions**: Corpus loader initialized.
- **Postconditions**: Search results displayed; copyable Python code snippet generated mirroring `corpus_toolkit`.
- **User Story**:
  - *As a* computational researcher,
  - *I want to* test queries interactively and get copyable Python snippets matching `corpus_toolkit` syntax,
  - *So that* I can transition from interactive exploration to reproducible headless scripting.
- **Scenario 15.1: Generating Scriptable Python Snippets**:
  - **Given** the user configures a complex query in Tab 11 with custom POS filters, spans, and views,
  - **When** the query executes,
  - **Then** the results are displayed in a clean unified DataGrid,
  - **And** the bottom code drawer renders a copyable Python code block using `CorpusSearchEngine` and `Concordancer` classes identical to notebook syntax,
  - **And** clicking `Copy Python Code` copies the snippet to the clipboard.

---

## 5. Acceptance Gate Checklist

| Checkpoint Identifier | Specification Requirement | Verification Method | Status |
|---|---|---|---|
| **GATE-UC-01** | Actor Profiles & System Roles | 4 distinct professional actors documented with exact needs | Verified |
| **GATE-UC-02** | UC-01 (Global Control Bar & TokenView) | Given/When/Then scenarios for all 32 views & RSS eviction | Verified |
| **GATE-UC-03** | UC-02 (Corpus Info Modal & Images) | Scenarios for cover art, author portraits & asset uploads | Verified |
| **GATE-UC-04** | UC-03 (Settings & Path Editor Modal) | Scenarios for live path checks, YAML editor & cache policies | Verified |
| **GATE-UC-05** | UC-04 (Help & Calculation Drawer) | Scenarios for LaTeX equations, boundary conditions & DOIs | Verified |
| **GATE-UC-06** | UC-05 to UC-07 (Tabs 1–3 Alignment & NDA) | Scenarios for inventory, $\Delta s/\Delta w/\Delta c$, SVG arcs, 4 sets | Verified |
| **GATE-UC-07** | UC-08 to UC-10 (Tabs 4–6 POS, Tree & Search) | Scenarios for bootstrap CIs, displaCy trees, 5 KWIC views | Verified |
| **GATE-UC-08** | UC-11 to UC-13 (Tabs 7–9 Dispersion & Diversity) | Scenarios for Juilland $D$, 22 LancsBox metrics, GraphColl | Verified |
| **GATE-UC-09** | UC-14 to UC-15 (Tabs 10–11 TF-IDF & Scripts) | Scenarios for PROPN ablation, ZIP exports & Python snippets | Verified |
| **GATE-UC-10** | Professional Tone & STE Clarity | Simplified Technical English verified across all scenarios | Verified |

---
*End of Document `03_Use_Cases_and_User_Stories.md`.*
