# Product Requirements Document (PRD): Corpus Analysis Single-Page Application (SPA)

**Document Version:** `v1.0-2026-10-21`  
**Repository Subsystem:** [`/home/ben/Documents/thesis/scripts/corpus_analysis/SPA/`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/SPA/)  
**Target Environment:** Standalone Git Repository (`git@github.com:KadirYigitUS/corpus_analysis.git`, branch `master`), Conda `base` (Python 3.12+, zero external package installations)  
**Parent System Document:** [`/home/ben/Documents/thesis/scripts/corpus_analysis/docs/Corpus_Analysis_PRD.md`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/docs/Corpus_Analysis_PRD.md)  
**Cross-System Matrix:** [`/home/ben/Documents/thesis/scripts/corpus_analysis/SPA/docs/12_Feature_Comparison_and_Dataflow_Matrix.md`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/SPA/docs/12_Feature_Comparison_and_Dataflow_Matrix.md)  

---

## 1. Executive Summary & Product Positioning

### 1.1 Purpose & Vision
The **Corpus Analysis Single-Page Application (SPA)** is an enterprise-grade computational corpus linguistics, translation alignment, and morphosyntactic analytics workstation. It transforms the analytical capabilities of [`Corpus_Analysis_tr.ipynb`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/Corpus_Analysis_tr.ipynb) and [`corpus_toolkit/`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/corpus_toolkit/) into a unified, interactive, browser-based single-page application.

The workstation enables quantitative researchers, corpus linguists, translation scholars, and lexicographers to investigate the 13-text First-Generation Pioneer Turkish Science Fiction Corpus (`Selma MİNE [SM]`, `Zühtü BAYAR [ZB]`, `Özlem KURDOĞLU [OK]`), inspect sentence-level bilingual alignment, explore neologism candidates alongside parallel corpora, profile Universal POS distributions with bootstrap confidence intervals, evaluate lexical diversity across 22 LancsBox-X metrics, calculate collocation association measures under union-slot window modeling, and generate reproducible research bundles.

### 1.2 Professional Workstation Mandate (Strict Non-Workstation Exclusion)
To preserve the professional rigor, computational responsiveness, and scientific focus of the workstation, the following artifacts are strictly excluded from the SPA runtime user interface:
1. **No Literary or Theoretical Essays**: The application UI shall contain no literary commentary, ideological critique, speculative sociologies of translation, or narrative dissertations.
2. **No Pedagogical Toy Examples**: Monolithic notebook tutorials, beginner coding exercises, and artificial toy string snippets are excluded from workstation views.
3. **No Student Exercises or Quizzes**: The interface contains no interactive self-tests, student evaluation modules, or quizzing apparatus.
4. **Data-First Focus**: Every UI component, table, chart, and modal must serve either live analytical computation, granular data visualization, exact mathematical documentation, corpus provenance inspection, or system configuration.

### 1.3 User Personas
- **Dr. Elif A. (Quantitative Corpus Linguist)**: Needs to test vocabulary richness growth ($TTR$, $MATTR$, $MTLD$, $HD\text{-}D$) across translation vs. indigenous Turkish corpora without bias from document length or punctuation conventions.
- **Murat K. (Translation Studies Researcher)**: Needs sentence-level bilingual alignment ratios ($R_{\text{sent}}$, length deltas $\Delta s, \Delta w, \Delta c$), omission/addition cardinality distributions, and side-by-side parallel view with Neologism Dictionary Annotation (NDA) overlays.
- **Selin T. (Computational Lexicographer)**: Searches multi-term lemmas, evaluates collocation attraction scores ($MI, MI^2, MI^3, T\text{-score}, G^2, \text{Log-Dice}$), inspects Juilland's $D$ dispersion across 10-chunk slices, and exports reproducible tabular bundles.
- **Research Software Engineer (System Administrator)**: Configures file paths, cache retention thresholds, and metadata descriptors via YAML or in-app modals without code modification.

---

## 2. Product Scope & Functional Architecture

### 2.1 The 11 Core Analytical Workstations (Tabs)
The SPA organizes all analytical features into 11 specialized workstation tabs:
1. **Tab 1: Corpus Inventory, Source Tables, Book/Author Info Cards & Schema Inspector**: Displays source tables, book covers, author/translator portraits, corpus metadata, lazy load statistics, and memory gauges.
2. **Tab 2: Translation Alignment & Length-Delta Explorer**: Interactive chapter navigation, cardinality tables (`1:1, 1:N, N:1, N:M, omission, addition`), sentence length scatter plots, and $\Delta s / \Delta w / \Delta c$ delta sorting.
3. **Tab 3: NDA Parallel Corpora & Tripartite Dictionary Viewer**: Side-by-side bilingual parallel text with 4 disjoint visual sets, Layer 0 Realia vs Top-Layer Irrealia resolution, stepped SVG links, and tripartite dictionary drawer.
4. **Tab 4: Comparative POS & Morphosyntactic Profiler**: 17-tag Universal POS profiles, lexical density, noun/verb ratio, Turkish deverbal derivation share (`+Inf`/`Part`), and 2000-iteration bootstrap 95% confidence intervals.
5. **Tab 5: Syntactic Dependency (`displaCy` UD) Studio**: CoNLL-U token tables, manual `displaCy` SVG arc rendering, dimmed function words, and stacked bilingual dependency trees.
6. **Tab 6: Corpus Search Engine & 5-View KWIC Concordancer**: Multi-term search (exact, glob, regex) with Turkish `İ/I` folding, POS/collocate constraints, and 5 KWIC presentation views (`kwic`, `coords`, `bilingual`, `parallel`, `table`).
7. **Tab 7: Batch KWIC, Juilland's $D$ Dispersion & BH-FDR Correlation Matrix**: 10-chunk dispersion metrics, pairwise Pearson $r$ / Spearman $\rho$ / cosine matrices, Benjamini–Hochberg False Discovery Rate $q$-values, and dispersion barcode plots.
8. **Tab 8: Lexical Diversity & Richness Laboratory**: 22-column LancsBox-X diversity table, $O(N)$ sliding-window MATTR trajectories, 6-axis radar charts, and Zipf rank-frequency plots.
9. **Tab 9: Union-Slot Collocation & GraphColl Association Studio**: $2 \times 2$ contingency matrix under union-slot window modeling, 6 association measures ($MI, MI^2, MI^3, T, G^2, \text{Log-Dice}$), and radial GraphColl scatter plots.
10. **Tab 10: Sublinear TF-IDF Keyness & Research Reporter**: Scikit-learn parity TF-IDF with `PROPN` exclusion, chunked pseudo-documents, and one-click reproducible research bundle exporter (`.md, .tsv, .png, .xlsx`).
11. **Tab 11: Unified Corpus Explorer & Scriptable `quick_search` Console**: High-speed unified search interface with auto-generated Python script snippets mirroring `corpus_toolkit` syntax.

### 2.2 Global Control Header & Application State
- **Persistent Header Bar**: Positioned at the top of the viewport across all tabs.
- **Corpus Scope Selector**: Dropdown supporting the 8 canonical lazy loader methods:
  `load_all()`, `load_all_english()`, `load_all_turkish()`, `load_translation_pairs()`, `load_indigenous()`, `load_author_related(code)`, `load_author_turkish(code)`, and `load_text(code)`.
- **32-Combination TokenView Engine**: 4 interactive toggle switches controlling:
  - `field`: `tok` (surface token) vs. `lem` (morphological lemma with apostrophe remediation).
  - `filter_function_words`: `False` (all words) vs. `True` (content words only).
  - `mode`: `drop` (remove function words from sequence) vs. `mask` (keep positional slots but mark ineligible).
  - `punct`: `drop` (default, remove standalone punctuation), `keep` (include punctuation), `strip` (collapse non-alphanumeric within tokens), `split` (retokenize on internal punctuation).
- **Process Memory Gauge**: Real-time RSS memory meter with visual color alerts (`< 800 MB` Green, `800–1200 MB` Amber, `> 1200 MB` Red), dynamic eviction button (`Evict RAM`), and cache status badge.
- **Utility Action Buttons**: Quick-access modal triggers for `Corpus Info`, `Settings & Paths`, and `Help & Formulas`.

---

## 3. Dedicated Help, Formula Documentation & Methodological Grounding

### 3.1 Help & Calculation Drawer (`help_docs_drawer.js` / `/api/v1/help/formulas`)
The application shall not embed speculative pedagogical tutorials in analytical tabs. Instead, comprehensive operational documentation and mathematical derivations are housed within an accessible, slide-over **Help & Calculation Drawer**:
- **Slide-Over Panel**: Opens from the right viewport boundary upon clicking the `Help & Formulas` button in the Global Header or clicking the formula helper icon (`ƒx`) adjacent to any analytical metric card.
- **REST Endpoint**: Hydrated dynamically via `GET /api/v1/help/formulas` returning structured JSON containing formula categories, LaTeX expressions, prose explanations, edge-case guards, and bibliographic references.
- **Searchable Index**: Provides instant client-side filtering across metric names, symbols, and statistical methods.

### 3.2 Exhaustive Mathematical & Statistical Catalog
The drawer provides exact mathematical definitions, boundary conditions, and `NaN` guards for every metric:
1. **LancsBox-X Lexical Diversity (22 Metrics)**: Complete closed-form equations for $TTR, \text{Guiraud } R, \text{CTTR}, \text{Herdan } C, \text{Dugast } U, \text{Maas } a^2, \text{Yule } K, \text{Simpson } D, \text{Honoré } R, \text{Hapax \%}, \text{STTR}, \text{MATTR}_{50/100/500}, \text{MTLD}, \text{HD-D}, \text{Sichel } S, \text{Michéa } M, \text{Entropy } H$.
2. **Collocation Association Measures (Union-Slot Modeling)**: Derivation of the $2 \times 2$ contingency table with union-slot context size $R_1$, expected frequency $E_{11} = \frac{R_1 \cdot C_1}{N}$, $MI, MI^2, MI^3, T\text{-score}, G^2$ (signed), and Rychlý's corpus-size invariant $\text{Log-Dice}$.
3. **Dispersion & Correlation**: 10-chunk slice rate calculations, Juilland's $D = 1 - \frac{V}{\sqrt{n-1}}$, population coefficient of variation $V = \frac{\sigma}{\mu}$, Pearson $r$, Spearman $\rho$, cosine similarity, and Benjamini–Hochberg step-up procedure for FDR control:
   $$q_{(i)} = \min_{j \ge i} \left(\frac{m}{j} p_{(j)}\right), \quad \text{capped at } 1.0$$
4. **Morphosyntactic Profiling**: Lexical density percentage, Noun/Verb ratio, Turkish deverbal derivation share ($\sum [\text{morph} \ni (+Inf \lor Part)]$), percentile bootstrap 95% confidence intervals (fixed seed 13, 2000 resamples), pooled $\chi^2$, and Cramér's $V$.
5. **Sublinear TF-IDF Keyness**: Manual formulation matching scikit-learn defaults:
   $$\text{TF} = 1 + \ln(\text{count}) \quad (\text{count} > 0), \quad \text{IDF} = \ln \left(\frac{1 + n}{1 + \text{df}}\right) + 1, \quad v_{\text{norm}} = \frac{v}{\|v\|_2}$$

### 3.3 Primary Methodological Citations
Every equation is tied to its canonical methodological reference, accessible directly in the drawer and hyperlinked to bibliographic records:
- *Lexical Richness & Diversity*: Biber (1988), Carroll (1964), Covington & McFall (2010), Dugast (1979), Guiraud (1954), Herdan (1960), Honoré (1979), Maas (1972), McCarthy & Jarvis (2010), Michéa (1953), Sichel (1975), Simpson (1949), Templin (1957), Yule (1944).
- *Collocation & Association*: Brezina, McEnery & Wattam (2015), Church & Hanks (1990), Dunning (1993), Firth (1957), Rychlý (2008), Sinclair (1991).
- *Dispersion & False Discovery*: Benjamini & Hochberg (1995), Juilland & Chang-Rodríguez (1964), Gries (2008).
- *Syntax & Dependency Grammar*: Nivre et al. (2016), Tesnière (1959).
- *Corpus-Based Translation Studies*: Baker (1993), Toury (2012), Simeoni (1998).

---

## 4. Corpus Inventory, Detailed Source Tables & Visual Asset Management

### 4.1 Detailed Source Tables
Tab 1 and the Corpus Info Modal present four exhaustive, filterable source tables:
1. **`translated_en` (English Source Texts, 5 books)**:
   - `IR-IA`: Isaac Asimov, *I, Robot* (1950, Gnome Press), 74,482 running tokens.
   - `TL-PA`: Poul Anderson, *The Light* (1957, Galaxy SF), 6,104 running tokens.
   - `TLP-ML`: Murray Leinster, *The Lonely Planet* (1949, Thrilling Wonder Stories), 11,489 running tokens.
   - `TSP-JL`: Jack London, *The Scarlet Plague* (1912, Macmillan), 20,443 running tokens.
   - `ASD-PKD`: Philip K. Dick, *A Scanner Darkly* (1977, Doubleday), 89,864 running tokens.
2. **`translated_tr` (Aligned Turkish Translations, 5 books)**:
   - `BR-SM`: Selma Mine (trans.), *Ben, Robot: Mekanik Adam Devri* (1983, Okat Yayınevi).
   - `A-ZB`: Zühtü Bayar (trans.), *Aydınlık* (1998, Çiviyazıları).
   - `YG-ZB`: Zühtü Bayar (trans.), *Yalnız Gezegen* (1998, Çiviyazıları).
   - `KS-ZB`: Zühtü Bayar (trans.), *Kıyametten Sonra (Kızıl Veba)* (1998, Çiviyazıları).
   - `KT-OK`: Özlem Kurdoğlu (trans.), *Karanlığı Taramak* (1998, Sarmal Yayınevi).
3. **`indigenous_tr` (Indigenous Turkish SF Novels, 3 books)**:
   - `OBI-SM`: Selma Mine, *OBİ,J.S.927* (1980, Okat Yayınevi).
   - `SU-ZB`: Zühtü Bayar, *Sahte Uygarlık* (1999, Çiviyazıları; drafted 1973–1976).
   - `SCS-OK`: Özlem Kurdoğlu, *Son Cephede Şafak* (2000, Sarmal Yayınevi).
4. **`aligned_pairs` (5 Bipartite Translation Pairs)**:
   - Pair codes, total alignment row counts ($ai$), sentence expansion ratios ($R_{\text{sent}}$), token ratios, character ratios, and NDA cache hydration status.

### 4.2 Interactive Corpus Info & Sources Modal (`corpus_info_modal.js`)
Accessible via the `Corpus Info` button in the Global Header and per-row inspection buttons in Tab 1:
- **High-Resolution Book Cover Dossier**: Displays authenticated cover art for all 13 books. Covers are rendered in responsive portrait cards with image zoom modal, publication metadata, publisher imprint, and physical page counts.
- **Author & Translator Biographical Portrait Dossier**: Displays verified portrait photographs and formal biographical dossiers for:
  - Turkish Author-Translators: Selma Mine, Zühtü Bayar, Özlem Kurdoğlu.
  - English Source Authors: Isaac Asimov, Poul Anderson, Murray Leinster, Jack London, Philip K. Dick.
  - Dossier Cards summarize active literary period, primary aesthetic disposition, translation norms, and dual authorial/translatorial roles.
- **Physical File & Integrity Metrics**: Displays raw file paths, file sizes, last modified timestamps, SHA-256 checksums, Parquet cache sizes, sentence row counts, and token counts.

### 4.3 Image Asset Management & Upload Endpoint
- **Storage Directory**: User-configured directory defined in `SPA/config/spa_paths.yaml` (defaulting to `SPA/static/img/covers/` and `SPA/static/img/portraits/`).
- **Upload API Endpoint**: `POST /api/v1/config/upload-image` accepting `multipart/form-data` with fields `image_type` (`cover` | `portrait`), `entity_code` (e.g., `IR-IA`, `SM`), and image binary (`.jpg`, `.jpeg`, `.png`, `.webp`).
- **Fallback Placeholder**: In the absence of an image file on disk, the UI gracefully renders an SVG placeholder badge displaying the entity code and book title without breaking layout.

---

## 5. Full User Configurability & Path Architecture

### 5.1 YAML Configuration Registry
The application shall contain zero hardcoded absolute paths or immutable corpus metadata. System configuration is externalized into two human-readable YAML registries:

1. **`SPA/config/spa_paths.yaml` (System Paths Registry)**:
   ```yaml
   paths:
     corpus_raw_tsv_dir: "/home/ben/Documents/thesis/data/corpus_analysis/raw_tsv"
     corpus_parquet_cache_dir: "/home/ben/Documents/thesis/data/corpus_analysis/.cache"
     nda_cache_dir: "/home/ben/Documents/thesis/data/Neologism_Dictionary_Annotation_Cache"
     reports_export_dir: "/home/ben/Documents/thesis/output/corpus_analysis/reports"
     figures_export_dir: "/home/ben/Documents/thesis/output/corpus_analysis/figures"
     tables_export_dir: "/home/ben/Documents/thesis/output/corpus_analysis/tables"
     image_assets_dir: "/home/ben/Documents/thesis/scripts/corpus_analysis/SPA/static/img"
   cache:
     policy: "keep"  # keep | clear | ask
     lru_threshold_mb: 2048
     memory_rss_alert_mb: 1200
   ```

2. **`SPA/config/corpus_metadata.yaml` (Corpus Entities & Visual Assets Registry)**:
   ```yaml
   authors:
     SM:
       name: "Selma Mine"
       role: "Author-Translator"
       period: "1980–1995"
       portrait_image: "portraits/selma_mine.jpg"
       bio_tr: "Türk bilimkurgu edebiyatının öncü kadın yazarı ve çevirmeni..."
     ZB:
       name: "Zühtü Bayar"
       role: "Author-Translator"
       period: "1973–2002"
       portrait_image: "portraits/zuhtu_bayar.jpg"
       bio_tr: "Şair, araştırmacı, Türk bilimkurgusunda kavramsal kuramcı..."
   books:
     IR-IA:
       code: "IR-IA"
       title: "I, Robot"
       author_code: "IA"
       year: 1950
       publisher: "Gnome Press"
       cover_image: "covers/IR-IA.jpg"
       language: "en"
       genre: "translated_source"
   ```

### 5.2 Settings & Path Editor Modal (`config_editor_modal.js`)
Accessible via the `Settings & Paths` gear icon in the Global Header:
- **Live Path Verification**: Real-time validation verifying whether configured directories exist on the server filesystem, are readable, and are writable.
- **In-Browser YAML Editor**: Validated code editor allowing administrators to modify `spa_paths.yaml` and `corpus_metadata.yaml` directly from the browser with syntax checking and rollback protection.
- **Cache Management Controls**: One-click actions to inspect Parquet cache size, trigger LRU eviction, purge cached files, or switch the startup cache policy (`keep`, `clear`, `ask`).

---

## 6. Non-Functional & Operational Requirements

### 6.1 Process Memory Ceiling & Lazy Materialization (`NFR-MEM`)
- **RSS Memory Limit**: The total resident set size (RSS) of the application server process shall remain strictly below `1.5 GB` (`< 1500 MB`) under full 13-book corpus operations.
- **Lazy Loading Contract**: Invoking loader methods must never deserialize tokens or sentences into RAM eagerly. Tokens and sentences must be materialized on-demand via content-addressed Parquet chunks and evicted immediately after aggregate reduction via `.evict()` or `.iter_evicting()`.

### 6.2 Execution Performance (`NFR-PERF`)
- **API Response Latency**:
  - Metadata and inventory endpoints (`/api/v1/corpus/inventory`, `/api/v1/config/*`) shall respond in $< 50\text{ ms}$.
  - Search, KWIC, and concordance queries shall return within $< 350\text{ ms}$ for single texts and $< 1.2\text{ s}$ for full-corpus sweeps.
  - 22-column diversity table generation shall complete in $< 1.5\text{ s}$ using the optimized $O(N)$ sliding-window MATTR algorithm.
- **DataGrid Rendering**: The HTML5 DataGrid (`table_grid.js`) shall paginate, sort, and resize 2,000 tabular rows in $< 16\text{ ms}$ (60 FPS DOM paint).

### 6.3 Content Security Policy & Offline Isolation (`NFR-CSP`)
- **Zero External Requests**: The SPA shall function entirely offline without initiating HTTP requests to third-party CDNs, external Google Fonts, unpkg, cdnjs, or tracking endpoints.
- **Strict CSP Header**:
  ```http
  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self';
  ```
- **No `eval()` or Inline Script Handlers**: All JavaScript logic must reside in standalone external modules loaded via standard `<script>` tags without `eval()` or inline `onclick` attributes.

### 6.4 Strict Modular Budget (`NFR-MVC`)
- **Line Count Limit**: To maintain clean modular boundaries and maintainability, every Python (`.py`), JavaScript (`.js`), CSS (`.css`), and HTML template file in `scripts/corpus_analysis/SPA/` must remain strictly $\le 180$ lines pre-formatting and $\le 200$ lines hard limit.
- **Separation of Concerns**: Controllers handle HTTP routing; Services execute pure business and analytical logic with zero direct file I/O; Repositories manage filesystem, YAML, Parquet, and pickle access.

---

## 7. Acceptance Gate Checklist

| Checkpoint Identifier | Description | Verification Criterion | Status |
|---|---|---|---|
| **GATE-PRD-01** | Professional Workstation Positioning | Zero literary essays, toy examples, or student quiz modules in UI | Verified |
| **GATE-PRD-02** | Dedicated Help & Formula Drawer | `/api/v1/help/formulas` + `help_docs_drawer.js` with exact LaTeX & citations | Verified |
| **GATE-PRD-03** | Corpus Info & Visual Modal | Cover images, author portraits, source tables, and upload API present | Verified |
| **GATE-PRD-04** | User Configurability | `spa_paths.yaml` & `corpus_metadata.yaml` fully editable via UI | Verified |
| **GATE-PRD-05** | Memory Envelope Compliance | Process RSS strictly $< 1.5\text{ GB}$ with live gauge and eviction | Verified |
| **GATE-PRD-06** | 32 TokenView Combinations | 4 interactive switches controlling field, filter, mode, and punct | Verified |
| **GATE-PRD-07** | CSP & Offline Self-Containment | Zero external CDN requests; strict local script/style execution | Verified |
| **GATE-PRD-08** | Modular Line-Count Budget | All SPA source files strictly $\le 200$ lines ($\le 180$ lines target) | Verified |

---
*End of Document `01_PRD.md`.*
