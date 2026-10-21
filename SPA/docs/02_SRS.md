# Software Requirements Specification (SRS): Corpus Analysis Single-Page Application (SPA)

**Document Version:** `v1.0-2026-10-21`  
**Repository Subsystem:** [`/home/ben/Documents/thesis/scripts/corpus_analysis/SPA/`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/SPA/)  
**Target Environment:** Standalone Git Repository (`git@github.com:KadirYigitUS/corpus_analysis.git`, branch `master`), Conda `base` (Python 3.12+, zero external packages)  
**Parent PRD:** [`/home/ben/Documents/thesis/scripts/corpus_analysis/SPA/docs/01_PRD.md`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/SPA/docs/01_PRD.md)  
**Methodological Base:** [`/home/ben/Documents/thesis/scripts/corpus_analysis/docs/METRICS.md`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/docs/METRICS.md)  
**Synthesis Matrix:** [`/home/ben/Documents/thesis/scripts/corpus_analysis/SPA/docs/12_Feature_Comparison_and_Dataflow_Matrix.md`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/SPA/docs/12_Feature_Comparison_and_Dataflow_Matrix.md)  

---

## 1. Introduction & System Constraints

### 1.1 Purpose
This specification details the comprehensive functional (FR-01 through FR-90) and non-functional requirements (NFR-MEM, NFR-PERF, NFR-CSP, NFR-MVC, NFR-SEC) for the **Corpus Analysis Single-Page Application (SPA)**. It defines exact mathematical formulations, operational edge-case guards, UI interactions, and interface behaviors across all 11 workstation tabs, Global Control Header, Corpus Info Modal, Settings Modal, and Help & Calculation Drawer.

### 1.2 System Invariants & Architecture Constraints
1. **Runtime Framework**: Python 3.12+ Flask WSGI application communicating with a Vanilla ES6 modular frontend.
2. **Line Budget**: Every source file in `SPA/` (`.py`, `.js`, `.css`, `.html`) must satisfy $\le 180$ lines pre-formatting, with an absolute upper ceiling of $\le 200$ lines.
3. **Four-Tier Architecture**:
   - `views/` & `static/js/`: ES6 UI controllers, rendering logic, and event dispatchers.
   - `controllers/`: Flask Blueprints exposing JSON REST APIs (`/api/v1/*`).
   - `services/`: Pure business logic, statistical algorithms, and data transformations with zero direct file I/O.
   - `repositories/`: Exclusive data access layer handling filesystem operations, YAML registries, Parquet caches, and pickle deserialization.

---

## 2. Functional Requirements (FR-01 to FR-90)

### 2.1 Global Control Header, TokenView Engine & Process State
- **FR-01 (Scope Selector)**: The header shall provide an interactive dropdown supporting the 8 canonical lazy loader methods: `load_all`, `load_all_english`, `load_all_turkish`, `load_translation_pairs`, `load_indigenous`, `load_author_related(code)`, `load_author_turkish(code)`, and `load_text(code)`. Changing scope updates global application state (`app_state.js`) without full page reloads.
- **FR-02 (32-Combination TokenView Engine)**: The header shall expose 4 toggle controls providing complete support for all $2 \times 2 \times 2 \times 4 = 32$ configurations of:
  $$\{\text{tok}, \text{lem}\} \times \{\text{False}, \text{True}\} \times \{\text{drop}, \text{mask}\} \times \{\text{drop}, \text{keep}, \text{strip}, \text{split}\}$$
- **FR-03 (Field Selection Switch)**: The engine shall toggle between surface word forms (`field='tok'`) and morphologically parsed base lemmas (`field='lem'`).
- **FR-04 (Closed-Class Function Word Filter)**:
  - English: Filters closed-class UPOS tags: $\{\text{DET}, \text{PRON}, \text{CCONJ}, \text{ADP}, \text{AUX}, \text{SCONJ}, \text{INTJ}, \text{PART}\}$.
  - Turkish: Enforces dual UPOS filtering plus Oflazer morphological head guard:
    $$\text{Head} \in \{\text{Postp}, \text{Conj}, \text{Det}, \text{Pron}, \text{Ques}, \text{Interj}, \text{Punc}\}$$
    extracted from `morph.split('+')[1]`.
- **FR-05 (Drop vs. Mask Token Modes)**:
  - `mode='drop'`: Removes function words from the sequence so window spans ($\pm L / \pm R$) count consecutive content words.
  - `mode='mask'`: Preserves original sentence token positions while marking function words ineligible (`elig == False`) as search targets or collocate candidates.
- **FR-06 (Four Punctuation Regimes)**:
  - `drop`: Excludes standalone punctuation ($\text{fcl} \ne \text{PUNCT}$) while retaining internal hyphens/apostrophes (`türkiye'nin`, `robot-bilim`).
  - `keep`: Retains standalone punctuation tokens ($\text{fcl} == \text{PUNCT}$) for syntactic and dialogue boundary analysis.
  - `strip`: Collapses non-alphanumeric marks within composite tokens without decomposition (`Türkiye'nin` $\to$ `Türkiyenin`, `robot-bilim` $\to$ `robotbilim`).
  - `split`: Retokenizes composite tokens on punctuation boundaries using regex `[^\W_]+` (`Türkiye'nin` $\to$ `['türkiye', 'nin']`), retaining originating $ch:p:s:tok$ coordinates.
- **FR-07 (Turkish Lemma Apostrophe Remediation — `clean_lemma`)**:
  - Automatically cleaves inflectional suffixes following any of the 7 apostrophe variants:
    $$\text{Apostrophe Set} = \{', ’ , ‘ , ` , ´ , ʼ , ʻ\}$$
  - Preserves internal hyphenated compound stems (`bilim-kurgu'nun` $\to$ `bilim-kurgu`, `1882'de` $\to$ `1882`).
  - Standalone apostrophe tokens are preserved without collapsing into empty strings.

### 2.2 Corpus Info & Sources Modal
- **FR-08 (Corpus Info Trigger)**: The header and Tab 1 shall contain a `Corpus Info` button that opens `corpus_info_modal.js`.
- **FR-09 (Detailed Source Tables)**: The modal shall render 4 sortable source tables: `translated_en` (5 source books), `translated_tr` (5 translations), `indigenous_tr` (3 novels), and `aligned_pairs` (5 translation pairs).
- **FR-10 (High-Resolution Book Cover Cards)**: The modal shall display authenticated cover image cards for each of the 13 corpus books with publication year, publisher imprint, and original language.
- **FR-11 (Author & Translator Portrait Cards)**: The modal shall display portrait photograph cards and biographical dossiers for the 3 Turkish author-translators (`SM`, `ZB`, `OK`) and 5 English source authors (`IA`, `PA`, `ML`, `JL`, `PKD`).
- **FR-12 (File & Checksum Verification)**: The modal shall display file size, modification timestamp, SHA-256 checksum, sentence count, token count, and Parquet cache size for every corpus text.
- **FR-13 (Image Upload Endpoint)**: The modal shall provide an upload interface sending `multipart/form-data` to `POST /api/v1/config/upload-image` to update book covers and author portraits dynamically.

### 2.3 Settings, Path Editor & Configuration Management
- **FR-14 (Settings Modal Trigger)**: The header shall contain a `Settings & Paths` gear button triggering `config_editor_modal.js`.
- **FR-15 (Path Registry Inspection)**: The modal shall display all active paths from `SPA/config/spa_paths.yaml` (raw TSV directory, Parquet cache, NDA cache, export directories).
- **FR-16 (Live Filesystem Path Validation)**: Calling `POST /api/v1/config/validate-paths` shall verify read/write accessibility of each configured path and display status badges (Green = OK, Red = Inaccessible).
- **FR-17 (In-Browser YAML Editor)**: The modal shall include a validated code editor allowing direct modification of `spa_paths.yaml` and `corpus_metadata.yaml` with schema validation before saving.
- **FR-18 (Cache Retention Policy Configuration)**: The modal shall allow switching the startup cache policy between `keep` (retain existing Parquet files), `clear` (flush cache on startup), and `ask` (prompt user).
- **FR-19 (Manual Cache Flush & LRU Threshold)**: The modal shall display total cache disk consumption, allow setting the LRU threshold (default $2{,}048\text{ MB}$), and trigger cache eviction.

### 2.4 Help & Calculation Documentation Drawer
- **FR-20 (Help Drawer Trigger)**: The header and metric cards shall provide triggers opening `help_docs_drawer.js` via a right-side slide-over panel.
- **FR-21 (Dynamic Formula Retrieval)**: The drawer shall fetch mathematical definitions and metadata from `GET /api/v1/help/formulas`.
- **FR-22 (Interactive Search & Category Filter)**: The drawer shall provide real-time search across metric names, mathematical symbols, and categories (Diversity, Collocation, POS, Alignment, Dispersion).
- **FR-23 (Exact Mathematical Notation)**: Every entry shall present formatted LaTeX equations, parameter breakdowns, and asymptotic behavior.
- **FR-24 (Primary Methodological Citations)**: Every formula shall include its canonical bibliographic citation (author, year, title, publisher/journal) hyperlinked to thesis references.

### 2.5 Tab 1: Corpus Inventory, Source Tables & Schemas
- **FR-25 (Inventory DataGrid)**: Tab 1 shall render a 20-row paginated DataGrid listing all 13 corpus books with author codes, publication years, genre categories, sentence counts, and token counts.
- **FR-26 (Author & Genre Filtering)**: Tab 1 shall provide one-click filter pills for Author (`SM`, `ZB`, `OK`) and Genre (`translated_en`, `translation`, `indigenous`).
- **FR-27 (File Verification Engine)**: Tab 1 shall invoke `verify_files()` and display visual health indicators for TSV and Parquet file integrity.
- **FR-28 (Token Size Comparison Chart)**: Tab 1 shall render an interactive horizontal bar chart (Figure 1) comparing running token counts across all 13 books colored by genre.
- **FR-29 (Table Schema Inspector)**: Tab 1 shall allow previewing the underlying column schemas and first 10 rows of both `tokens` and `sentences` DataFrames.
- **FR-30 (Live RSS Gauge & Memory Hygiene)**: Tab 1 shall display current Python process memory via `loader.rss_mb()` and provide an `Evict Unused Texts` button calling `loader.evict_all()`.

### 2.6 Tab 2: Translation Alignment & Length-Delta Explorer
- **FR-31 (Pair Selector)**: Tab 2 shall allow selecting any of the 5 aligned pairs (`IR-IA_BR-SM`, `TL-PA_A-ZB`, `TLP-ML_YG-ZB`, `TSP-JL_KS-ZB`, `ASD-PKD_KT-OK`).
- **FR-32 (Chapter Navigation Sidebar)**: Tab 2 shall provide a left chapter navigation sidebar (`.ch-btn`) displaying chapter indices and row counts.
- **FR-33 (Top KPI Metric Cards)**: Tab 2 shall render top stat cards displaying total alignment units ($ai$), sentence ratio $R_{\text{sent}}$, word ratio, and character ratio:
  $$R_{\text{sent}} = \frac{\sum n_{\text{tur}}}{\sum n_{\text{eng}}}, \quad \text{ratio}_{\text{word}} = \frac{W_{\text{tur}}}{W_{\text{eng}}}, \quad \text{ratio}_{\text{char}} = \frac{C_{\text{tur}}}{C_{\text{eng}}}$$
- **FR-34 (Cardinality Distribution Table)**: Tab 2 shall categorize and count all alignment shapes:
  $$\text{Cardinality} = (|S_{\text{eng}}|, |S_{\text{tur}}|) \to 1{:}1, 1{:}N, N{:}1, N{:}M, \text{omission } (n,0), \text{addition } (0,m)$$
- **FR-35 (Stacked Alignment Horizontal Bar Chart)**: Tab 2 shall render per-chapter stacked bar charts showing the proportional distribution of alignment types.
- **FR-36 (Sentence-Length Scatter Plot)**: Tab 2 shall render an interactive scatter plot (Figure 1B) plotting English sentence length ($x$) against Turkish sentence length ($y$) with an identity line ($y = x$).
- **FR-37 (Delta Sorting & Sentence Badge)**: Tab 2 shall support sorting alignment rows by sentence delta ($\Delta s = |S_{\text{tur}}| - |S_{\text{eng}}|$), word delta ($\Delta w$), and character delta ($\Delta c$), rendering sentence boundaries with golden badges (`.sent-sep` `‖`).

### 2.7 Tab 3: NDA Parallel Corpora & Tripartite Dictionary Viewer
- **FR-38 (NDA Cache Safe Unpickling)**: Tab 3 shall hydrate `scored_alignment_rows.pickle` and `initial_dictionary.pickle` via an isolated `_NdaSafeUnpickler` without `sys.modules['app']` contamination.
- **FR-39 (Disjoint Visual Set Styling)**: Tab 3 shall style tokens according to 4 disjoint visual sets:
  - **Set 1 (Linked Bilingual Pairs)**: Blue background (`#bfdbfe`), border (`#3b82f6`), and superscript link badge `L1..Lk`.
  - **Set 2 (Unlinked Irrealia)**: Teal (`#99f6e4`) for English-only and rose (`#fecdd3`) for Turkish-only Irrealia.
  - **Set 3 (Neologism Candidates)**: Amber-yellow (`#fef08a`) with score badge (`★ score`).
  - **Set 4 (Search Hits)**: Crimson outline (`#be123c`).
- **FR-40 (Layer Precedence Resolution)**: Top-Layer `IRREALIA` (`SCIFI_*`) sorted by $n$-gram length descending shall take rendering precedence over Layer 0 `REALIA` (`NER` tags).
- **FR-41 (Stepped SVG Connector Arcs)**: Tab 3 shall compute and render responsive SVG connector paths (`<svg class="nda-link-svg">`) connecting the first token of English link `L#` in row `ai` to the first token of Turkish link `L#`.
- **FR-42 (Dual-Row Token Box)**: Each token shall be rendered in a `.nda-token-box` displaying surface `tok`, toggleable `lem · pos` sub-row, and hover tooltip containing coordinate `ch:p:s:tok`, UPOS, NER, and candidate scores.
- **FR-43 (Tripartite Global Dictionary Drawer)**: Tab 3 shall include a collapsible side drawer displaying the Tripartite Global Dictionary organized into: `Linked Items`, `English Only Irrealia`, and `Turkish Only Irrealia`.
- **FR-44 (Current Label Attributions Footer)**: Tab 3 shall render a footer (`.nda-summary-footer`) beneath each alignment group summarizing linked pairs, unlinked candidates, and expansion metrics.

### 2.8 Tab 4: Comparative POS & Morphosyntactic Profiler
- **FR-45 (17-Tag Universal POS Profile Table)**: Tab 4 shall compute and display raw frequencies and percentages for all 17 UPOS tags across selected texts or corpus groupings.
- **FR-46 (Lexical Density Calculation)**: Tab 4 shall calculate lexical density:
  $$\text{Lexical Density} = 100 \cdot \frac{\text{NOUN} + \text{VERB} + \text{ADJ} + \text{ADV}}{N_{\text{nonpunct}}}$$
  with an option to include `PROPN`.
- **FR-47 (Noun/Verb Ratio)**: Tab 4 shall evaluate $\text{Noun/Verb Ratio} = \frac{\text{NOUN}}{\text{VERB}}$ (`NaN` if $\text{VERB} = 0$).
- **FR-48 (Turkish Deverbal Suffix Share)**: Tab 4 shall calculate Turkish deverbal derivation share:
  $$\text{Deverbal Share} = 100 \cdot \frac{\sum [\text{morph} \ni (+Inf \lor Part)]}{N_{\text{running}}}$$
- **FR-49 (Pairwise POS Divergence Chart)**: Tab 4 shall render Figure 2B plotting percentage-point differences ($\Delta\text{pp} = \text{Pct}_{\text{TR}} - \text{Pct}_{\text{EN}}$) across UPOS tags for aligned pairs.
- **FR-50 (Group Comparison with Bootstrap 95% CIs)**: Tab 4 shall compute percentile bootstrap 95% confidence intervals over texts using fixed `seed=13` and 2,000 resamples:
  $$\text{CI}_{95\%} = [\text{Percentile}(2.5), \text{Percentile}(97.5)]$$
- **FR-51 (Statistical Significance Tests)**: Tab 4 shall calculate pooled $\chi^2$ test of independence and Cramér's $V$ for categorical POS distributions across corpus groups.

### 2.9 Tab 5: Syntactic Dependency (`displaCy` UD) Studio
- **FR-52 (Sentence Coordinate & Alignment Navigation)**: Tab 5 shall allow selecting sentences by textual coordinate `(text_code, ch, p, s)` or alignment row index `ai`.
- **FR-53 (CoNLL-U Tabular View)**: Tab 5 shall render a tabular breakdown of tokens with columns: ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, and DEPS.
- **FR-54 (Manual `displaCy` SVG Arc Generation)**: Tab 5 shall generate client-side SVG dependency arcs following Universal Dependencies conventions without calling external spaCy binaries.
- **FR-55 (Arc Direction & Boundary Guards)**: Arcs shall have direction $\text{dir} = \text{'left'}$ if dependent precedes head. Heads equal to 0, out of sentence range, or equal to the token itself shall produce no arc.
- **FR-56 (English ClearNLP-to-UD Label Mapping)**: English labels shall be mapped to UD standards (`dobj` $\to$ `obj`, `nsubjpass` $\to$ `nsubj:pass`, `relcl` $\to$ `acl:relcl`).
- **FR-57 (Function Word Dimming & Stacked Bilingual View)**: Tab 5 shall provide a toggle to dim function word arcs (`opacity: 0.4`) and display stacked English and Turkish dependency trees for aligned sentences.

### 2.10 Tab 6: Corpus Search Engine & 5-View KWIC Concordancer
- **FR-58 (Multi-Term Query Input)**: Tab 6 shall accept multiple search terms with matching options: exact match, glob wildcard (`robot*`), or regular expression.
- **FR-59 (Turkish Case Folding Invariance)**: Search shall enforce Turkish `İ/I` and `ı/i` case-folding equivalence (`İstanbul` $\leftrightarrow$ `istanbul`, `Işık` $\leftrightarrow$ `ışık`).
- **FR-60 (POS & Collocate Constraints)**: Tab 6 shall allow constraining hits by target UPOS tag and requiring the co-occurrence of a collocate term within a specified window ($\pm k$ tokens).
- **FR-61 (Normalized Frequency per 10k)**: Tab 6 shall report both raw hit counts and normalized frequency:
  $$\text{per10k} = 10{,}000 \cdot \frac{\text{hits}}{N_{\text{eligible}}}$$
- **FR-62 (5 KWIC Presentation Views)**: Tab 6 shall provide five selectable concordance views:
  1. `kwic`: Traditional Left Context — Node — Right Context display.
  2. `coords`: Concordance lines annotated with $ch:p:s:tok$ coordinates.
  3. `bilingual`: Side-by-side English source and Turkish translation concordance cards.
  4. `parallel`: Full sentence alignment row view with search hits highlighted in crimson.
  5. `table`: Tabular DataGrid export view.
- **FR-63 (Asymmetric Window Sliders)**: Tab 6 shall provide independent sliders for left window ($0 \le L \le 20$) and right window ($0 \le R \le 20$), supporting sentence-boundary clamping.
- **FR-64 (Multi-Key Context Sorting)**: Tab 6 shall support multi-level sorting on context words at relative offsets ($R_1, R_2, L_1, L_2$) using Turkish collation rules.
- **FR-65 (NLTK Concordance Cross-Check Drawer)**: Tab 6 shall provide an expandable drawer running `nltk.text.ConcordanceIndex` to verify hit counts and context boundaries.

### 2.11 Tab 7: Batch KWIC, Juilland's $D$ Dispersion & BH-FDR Correlation Matrix
- **FR-66 (Batch Query Input)**: Tab 7 shall accept newline-delimited term lists or categorized JSON term groups for batch processing.
- **FR-67 (10-Chunk Juilland's $D$ Dispersion)**: For each text, tokens are divided into $n = 10$ equal position slices. Tab 7 shall compute chunk rates $\text{rate}_k = 10{,}000 \cdot \frac{\text{hits}_k}{N_k}$ and Juilland's $D$:
  $$D = 1 - \frac{V}{\sqrt{n - 1}}, \quad V = \frac{\sigma_{\text{pop}}}{\mu} = \frac{\sqrt{\frac{1}{n} \sum (\text{rate}_k - \mu)^2}}{\mu}$$
  Guards: If $\mu = 0 \implies D = \text{NaN}$. If all chunk counts are equal $\implies V = 0 \implies D = 1.0$. Tab 7 reports both *across-text* and *within-text* dispersion.
- **FR-68 (Dispersion Barcode Strip)**: Tab 7 shall render visual barcode strips illustrating the exact positional distribution of hits across the 10 text chunks.
- **FR-69 (Pairwise Association Metrics)**: Tab 7 shall calculate pairwise association matrices across all query terms:
  - Cosine similarity: $\cos(x, y) = \frac{x \cdot y}{\|x\| \|y\|}$ ($0$ if either vector is zero).
  - Pearson correlation $r$ and Spearman rank correlation $\rho$ (constant vectors yield `NaN`).
- **FR-70 (Benjamini–Hochberg FDR $q$-Values)**: Tab 7 shall calculate False Discovery Rate adjusted $q$-values over all $m$ word-pair tests:
  $$q_{(i)} = \min_{j \ge i} \left(\frac{m}{j} p_{(j)}\right), \quad \text{capped at } 1.0$$
- **FR-71 (Interactive Correlation Heatmaps)**: Tab 7 shall render interactive heatmaps (Figure 3B, 3C) displaying term frequency rates, correlation coefficients, and significance markers ($* q < 0.05, ** q < 0.01$).

### 2.12 Tab 8: Lexical Diversity & Richness Laboratory
- **FR-72 (22-Column LancsBox-X Table Generation)**: Tab 8 shall compute and display the complete 22-column diversity table across selected texts with full edge-case protection:
  1. $N$: Running eligible tokens ($N = 0 \implies \text{all metrics NaN}$).
  2. $V$: Case-folded vocabulary types.
  3. $\text{TTR} = \frac{V}{N}$.
  4. $\text{Guiraud } R = \frac{V}{\sqrt{N}}$.
  5. $\text{CTTR} = \frac{V}{\sqrt{2N}}$.
  6. $\text{Herdan } C = \frac{\ln V}{\ln N}$ ($N \le 1 \implies \text{NaN}$).
  7. $\text{Dugast } U = \frac{(\ln N)^2}{\ln N - \ln V}$ ($V = N \implies \text{NaN}$).
  8. $\text{Maas } a^2 = \frac{\ln N - \ln V}{(\ln N)^2}$ ($N \le 1 \implies \text{NaN}$).
  9. $\text{Yule } K = 10^4 \cdot \frac{\sum m^2 V_m - N}{N^2}$.
  10. $\text{Simpson } D = \sum \frac{n_i(n_i - 1)}{N(N - 1)}$ ($N \le 1 \implies \text{NaN}$).
  11. $\text{Honoré } R = 100 \cdot \frac{\ln N}{1 - V_1/V}$ ($V_1 = V \implies \text{NaN}$).
  12. $\text{Hapax } \%_{\text{types}} = 100 \cdot \frac{V_1}{V}$ ($V = 0 \implies \text{NaN}$).
  13. $\text{Hapax } \%_{\text{tokens}} = 100 \cdot \frac{V_1}{N}$ ($N = 0 \implies \text{NaN}$).
  14. $\text{STTR}$: Mean TTR of consecutive 1,000-token blocks; trailing partial block dropped ($N < 1000 \implies \text{TTR} + \text{warning}$).
  15. $\text{MATTR}_{50}$: Mean TTR of sliding window $w = 50$ ($N < 50 \implies \text{TTR} + \text{warning}$).
  16. $\text{MATTR}_{100}$: Mean TTR of sliding window $w = 100$ ($N < 100 \implies \text{TTR} + \text{warning}$).
  17. $\text{MATTR}_{500}$: Mean TTR of sliding window $w = 500$ ($N < 500 \implies \text{TTR} + \text{warning}$).
  18. $\text{MTLD}$: Bidirectional mean $\frac{\text{MTLD}_{\text{fwd}} + \text{MTLD}_{\text{bwd}}}{2}$, factor threshold $0.72$, partial factor $\frac{1 - \text{TTR}}{1 - 0.72}$ ($N < 2 \implies \text{NaN}$).
  19. $\text{HD-D}$: Draw size 42; $\sum_{i=1}^V \frac{1 - \text{HypergeomPMF}(0, N, n_i, 42)}{42}$ ($N < 42 \implies \text{NaN}$).
  20. $\text{Sichel } S = \frac{V_2}{V}$ ($V = 0 \implies \text{NaN}$).
  21. $\text{Michéa } M = \frac{V}{V_1}$ ($V_1 = 0 \implies \text{NaN}$).
  22. $\text{Entropy } H = -\sum p_i \log_2 p_i, \quad p_i = \frac{n_i}{N}$.
- **FR-73 ($O(N)$ Sliding-Window MATTR Engine)**: Tab 8 shall evaluate MATTR using an $O(N)$ deque update algorithm maintaining running type frequencies rather than $O(N \cdot w)$ naive recomputation.
- **FR-74 (MATTR Window Slider & Trajectories)**: Tab 8 shall provide a slider ($10 \le w \le 1000$) and render line trajectories (Figure 4B) showing diversity changes across token sequence length.
- **FR-75 (6-Axis Diversity Radar Chart)**: Tab 8 shall render an interactive 6-axis radar chart (Figure 4A) comparing normalized metrics across translations and indigenous works.
- **FR-76 (Zipf Log-Log Rank-Frequency Curves)**: Tab 8 shall plot $\log_{10}(\text{rank})$ vs. $\log_{10}(\text{frequency})$ (Figure 4C) with theoretical Zipf slope reference lines.
- **FR-77 (View Comparison Matrix)**: Tab 8 shall allow toggling between surface `tok` and lemmatized `lem`, raw vs. content, and the 4 punctuation regimes to evaluate impact on diversity scores.
- **FR-78 (Metric Tooltip Cards)**: Hovering over any table column header shall display an info card quoting its closed-form formula and edge-case behavior.

### 2.13 Tab 9: Union-Slot Collocation & GraphColl Studio
- **FR-79 (Union-Slot Window Modeling)**: Context windows are computed as the union of all slots surrounding node occurrences (node position excluded from its own window; clamped to sentence boundaries by default):
  $$R_1 = \left| \bigcup_{k=1}^{f_{\text{node}}} \text{Window}(k) \right|, \quad O_{11} \le R_1, \quad O_{11} \le C_1, \quad E_{11} = \frac{R_1 \cdot C_1}{N}$$
  Contingency matrix:
  $$\begin{pmatrix} O_{11} & R_1 - O_{11} \\ C_1 - O_{11} & N - R_1 - C_1 + O_{11} \end{pmatrix}$$
- **FR-80 (Pointwise Mutual Information Measures)**: Tab 9 shall evaluate:
  $$\text{MI} = \log_2 \frac{O_{11}}{E_{11}}, \quad \text{MI}^2 = \log_2 \frac{O_{11}^2}{E_{11}}, \quad \text{MI}^3 = \log_2 \frac{O_{11}^3}{E_{11}}$$
- **FR-81 (Student's $T$-Score)**: Tab 9 shall compute $T = \frac{O_{11} - E_{11}}{\sqrt{O_{11}}}$ ($O_{11} = 0 \implies \text{NaN}$).
- **FR-82 (Signed Log-Likelihood Ratio $G^2$)**: Tab 9 shall compute:
  $$G^2 = 2 \sum_{i,j} O_{ij} \ln \frac{O_{ij}}{E_{ij}} \quad (0 \ln 0 = 0), \quad \text{sign}(G^2) = -1 \text{ if } O_{11} < E_{11}$$
- **FR-83 (Log-Dice Association Score)**: Tab 9 shall compute Rychlý's corpus-size invariant Log-Dice using raw frequencies:
  $$\text{Log-Dice} = 14 + \log_2 \left(\frac{2 O_{11}}{f_{\text{node}} + C_1}\right)$$
- **FR-84 (Radial GraphColl Scatter Plot)**: Tab 9 shall render Figure 5 plotting effect size ($\text{MI}$ / $\text{Log-Dice}$, $x$-axis) against statistical evidence ($G^2$ / $T$-score, $y$-axis) with interactive collocate node labels.

### 2.14 Tab 10: Sublinear TF-IDF Keyness & Reproducible Research Reporter
- **FR-85 (Scikit-Learn Parity TF-IDF Engine)**: Tab 10 shall fit TF-IDF keyness models separately for English and Turkish corpora using exact manual formulations:
  $$\text{TF} = 1 + \ln(\text{count}) \quad (\text{count} > 0), \quad \text{IDF} = \ln \left(\frac{1 + n}{1 + \text{df}}\right) + 1, \quad v_{\text{norm}} = \frac{v}{\|v\|_2}$$
- **FR-86 (PROPN Exclusion Ablation Switch)**: Tab 10 shall provide a toggle to exclude proper nouns (`exclude_pos={'PROPN'}`) to eliminate character and place name bias from thematic keywords.
- **FR-87 (Pseudo-Document Chunk Slider)**: Tab 10 shall allow partitioning texts into $k$ equal chunks ($2 \le k \le 20$) to evaluate intra-textual keyword distribution.
- **FR-88 (Top-$K$ Keyword Bar Charts)**: Tab 10 shall render horizontal bar charts (Figure 6) displaying the top $K$ keyness terms per text or corpus partition.

### 2.15 Tab 11: Unified Corpus Explorer & Scriptable Console
- **FR-89 (Unified Scriptable Search Console)**: Tab 11 shall provide a unified search interface executing cross-category lexical searches and outputting auto-generated Python scripts matching `corpus_toolkit` syntax.
- **FR-90 (Reproducible Research Bundle Export)**: The application shall allow bundling active analytical outputs into an atomic ZIP archive containing `.md` reports, UTF-8 `.tsv` tables, 300-DPI `.png` charts, and multi-sheet `.xlsx` workbooks saved to the configured export directory.

---

## 3. Non-Functional Requirements (NFRs)

### 3.1 NFR-MEM: Memory Ceiling & Hygiene
- **NFR-MEM-01 (Resident Set Size Ceiling)**: The total memory consumption of the application process shall remain strictly below $1.5\text{ GB}$ ($< 1500\text{ MB}$ RSS) during any operation.
- **NFR-MEM-02 (Lazy Loading Contract)**: No corpus text shall deserialize tokens or sentences into RAM upon loader initialization. DataFrames must be loaded on demand and evicted via `.evict()` or `.iter_evicting()`.
- **NFR-MEM-03 (Content-Addressed Cache Key)**: Parquet caches must be keyed by $\text{SHA256}(\text{SCHEMA\_VERSION}, \text{ns}, \text{args})[:20]$ with atomic `os.replace` persistence.

### 3.2 NFR-PERF: Computational Responsiveness
- **NFR-PERF-01 (API Latency)**: Metadata endpoints shall return in $< 50\text{ ms}$; single-text searches in $< 350\text{ ms}$; full-corpus sweeps in $< 1.2\text{ s}$.
- **NFR-PERF-02 (Diversity Computation)**: The 22-column diversity table for a 75,000-word novel shall execute in $< 1.5\text{ s}$.
- **NFR-PERF-03 (Client Rendering)**: The columnar DataGrid (`table_grid.js`) shall paginate and sort 2,000 rows in $< 16\text{ ms}$ (60 FPS).

### 3.3 NFR-CSP: Content Security Policy & Offline Isolation
- **NFR-CSP-01 (Zero External Assets)**: The application shall not issue external network requests. All scripts, fonts, icons, and styles must be served locally.
- **NFR-CSP-02 (CSP Headers)**: The server shall enforce `default-src 'self'`. Dynamic string execution (`eval`, `new Function`) is prohibited.

### 3.4 NFR-MVC: Strict Modular Budget & Architecture
- **NFR-MVC-01 (200-Line Upper Ceiling)**: Every `.py`, `.js`, `.css`, and `.html` file must remain $\le 180$ lines pre-formatting and $\le 200$ lines hard limit.
- **NFR-MVC-02 (Strict Layering)**: Zero file I/O in Services; zero business logic in Controllers; exclusive data persistence in Repositories.

### 3.5 NFR-SEC: Security & Input Sanitation
- **NFR-SEC-01 (Regex Denial of Service Protection)**: User regex search queries shall be executed with timeout guards to prevent ReDoS.
- **NFR-SEC-02 (Path Traversal Protection)**: Path inputs in settings and image uploads must be sanitized against directory traversal attacks (`..`).

---

## 4. Acceptance Gate Checklist

| Checkpoint Identifier | Specification Requirement | Verification Method | Status |
|---|---|---|---|
| **GATE-SRS-01** | FR-01 to FR-07 (Header & 32 TokenViews) | Unit test all 32 combinations against `TokenView` | Verified |
| **GATE-SRS-02** | FR-08 to FR-13 (Corpus Info Modal & Images) | Verify 13 cover cards, 8 author portraits, checksums | Verified |
| **GATE-SRS-03** | FR-14 to FR-19 (Settings & Path Registry) | Verify YAML validation, path verification, cache flush | Verified |
| **GATE-SRS-04** | FR-20 to FR-24 (Help & Formula Drawer) | Verify `/api/v1/help/formulas` JSON & LaTeX rendering | Verified |
| **GATE-SRS-05** | FR-25 to FR-37 (Tabs 1 & 2 Alignment) | Verify DataGrid, cardinality table, $R_{\text{sent}}$, scatter plot | Verified |
| **GATE-SRS-06** | FR-38 to FR-44 (Tab 3 NDA Parallel) | Verify safe unpickling, 4 visual sets, SVG arcs | Verified |
| **GATE-SRS-07** | FR-45 to FR-51 (Tab 4 POS Profiler) | Verify UPOS table, lexical density, bootstrap seed 13 CIs | Verified |
| **GATE-SRS-08** | FR-52 to FR-57 (Tab 5 Dependency Studio) | Verify CoNLL table, manual displaCy SVG arc layout | Verified |
| **GATE-SRS-09** | FR-58 to FR-65 (Tab 6 Search & KWIC) | Verify Turkish I/İ folding, 5 KWIC views, context sorting | Verified |
| **GATE-SRS-10** | FR-66 to FR-71 (Tab 7 Batch & Juilland) | Verify 10-chunk Juilland $D$, pairwise matrix, BH-FDR | Verified |
| **GATE-SRS-11** | FR-72 to FR-78 (Tab 8 Lexical Diversity) | Verify all 22 LancsBox-X formulas and NaN guards | Verified |
| **GATE-SRS-12** | FR-79 to FR-84 (Tab 9 Union-Slot Colloc) | Verify union slots, 6 association measures, GraphColl | Verified |
| **GATE-SRS-13** | FR-85 to FR-90 (Tabs 10 & 11 TF-IDF & Rep) | Verify sklearn parity, PROPN switch, ZIP bundle export | Verified |
| **GATE-SRS-14** | NFR-MEM-01 to NFR-MEM-03 (Memory Envelope) | Process RSS verified $< 1.5\text{ GB}$ under full load | Verified |
| **GATE-SRS-15** | NFR-CSP & NFR-MVC (Line Budget & Security) | Zero CDN requests, all SPA source files $\le 200$ lines | Verified |

---
*End of Document `02_SRS.md`.*
