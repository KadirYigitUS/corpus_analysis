# Product Requirements Document (PRD): `corpus_analysis` (`corpus_toolkit` & Bilingual Pedagogical Notebooks)

**Document Version:** `v3.1-2026-10-20`
**Repository:** `git@github.com:KadirYigitUS/corpus_analysis.git` (`/home/ben/Documents/thesis/scripts/corpus_analysis`)
**Target Environment:** Conda `base` (Python 3.12+, zero external package installation)

---

## 1. Executive Summary & Research Purpose

`corpus_analysis` provides a reproducible, memory-preserving, and pedagogically transparent computational corpus linguistics suite for analyzing the **First-Generation Pioneer Turkish Science Fiction Author-Translators** (`Selma MİNE [SM]`, `Zühtü BAYAR [ZB]`, `Özlem KURDOĞLU [OK]`).

### 1.1 Analytical Scope (13 Pioneer Texts within the 18-Book Dissertation Corpus)
While the broader doctoral dissertation (*"How Translation Shaped the Turkish Science Fiction Repertoire: A Computer-Assisted Analysis of Author-Translators and Neologism Networks"*) encompasses 18 books across 8 author-translators (`10` translated texts + `8` indigenous novels), `corpus_analysis` focuses on the **13-text First-Generation Pioneer Core**:
- **5 English Source Works (`english_source`)**:
  - `IR-IA`: Isaac Asimov — *I, Robot* (1950)
  - `TL-PA`: Poul Anderson — *The Light* (1957)
  - `TLP-ML`: Murray Leinster — *The Lonely Planet* (1949)
  - `TSP-JL`: Jack London — *The Scarlet Plague* (1912)
  - `ASD-PKD`: Philip K. Dick — *A Scanner Darkly* (1977)
- **5 Aligned Turkish Translations (`translation`)**:
  - `BR-SM`: Selma Mine — *Ben, Robot: Mekanik Adam Devri* (1983, paired with `IR-IA`)
  - `A-ZB`: Zühtü Bayar — *Aydınlık* (1998, paired with `TL-PA`)
  - `YG-ZB`: Zühtü Bayar — *Yalnız Gezegen* (1998, paired with `TLP-ML`)
  - `KS-ZB`: Zühtü Bayar — *Kıyametten Sonra (Kızıl Veba)* (1998, paired with `TSP-JL`)
  - `KT-OK`: Özlem Kurdoğlu — *Karanlığı Taramak* (1998, paired with `ASD-PKD`)
- **3 Indigenous Turkish SF Novels (`indigenous`)**:
  - `OBI-SM`: Selma Mine — *OBİ,J.S.927* (1980)
  - `SU-ZB`: Zühtü Bayar — *Sahte Uygarlık* (1999; drafted 1973–1976)
  - `SCS-OK`: Özlem Kurdoğlu — *Son Cephede Şafak* (2000)

---

## 2. Core Architectural Requirements

### 2.1 Lazy Loading, Content-Addressed Parquet Caching & Memory Hygiene
- **Requirement `REQ-MEM-01` (Lazy Materialization)**: Instantiating `CorpusLoader()` or calling any of the 8 loader methods (`load_all`, `load_all_english`, `load_all_turkish`, `load_translation_pairs`, `load_indigenous`, `load_author_related`, `load_author_turkish`, `load_text`) must **never** eagerly load pickle files into RAM (`text.is_loaded() == False`).
- **Requirement `REQ-MEM-02` (Atomic Parquet Cache)**: On first access to `text.tokens` or `text.sentences`, raw `.pickle.xz` files (`ParsedEnglishSentenceRow` / `ParsedTurkishSentenceRow`) are parsed into compact tabular DataFrames (`category` and `int32`/`int16` dtypes, $\approx 7\text{ MB}$ per 70,000-token novel) and atomically persisted in `data/corpus_analysis/.cache/` keyed by `(code, kind, file_mtime_ns, file_size, SCHEMA_VERSION)`.
- **Requirement `REQ-MEM-03 (Eviction & RSS Ceiling)`**: Every `LazyCorpusText` provides `.evict()` and `CorpusSelection` provides `.iter_evicting()` so full-corpus sweeps stay well under a `1.5 GB` RSS envelope (`loader.rss_mb()`).

### 2.2 Token Representation: The Three Switches & Four Punctuation Regimes (`TokenView`)
- **Requirement `REQ-VIEW-01 (Field Switch)`**: Every analytical tool must accept `field='tok'` (surface token) or `field='lem'` (morphological lemma).
- **Requirement `REQ-VIEW-02 (Function-Word Filter & Drop/Mask Semantics)`**:
  - `filter_function_words=False`: Retains all non-punctuation running words (`fcl in {0, 1}`).
  - `filter_function_words=True`: Filters closed-class UPOS tags (`DET, PRON, ADP, AUX, CCONJ, SCONJ, PART, INTJ`) plus the Passim Turkish morphological head guard (`Postp, Conj, Det, Pron, Ques, Interj, Punc` on the last derivational suffix).
  - `mode='drop'`: Removes function words from the sequence so window spans ($\pm L / \pm R$) count *consecutive content words*.
  - `mode='mask'`: Keeps function words in their running-text positions so window spans count *consecutive running words*, while marking function words ineligible (`elig == False`) as search nodes or collocates.
- **Requirement `REQ-VIEW-03 (Punctuation Taxonomy)`**:
  - `punct='drop'` (default): Drops standalone punctuation (`fcl == 2`); preserves in-token punctuation (`Türkiye'nin`, `robot-bilim`).
  - `punct='keep'`: Retains standalone punctuation tokens (`?`, `!`, `,`, `.`) as searchable/countable items.
  - `punct='strip'`: Strips internal punctuation from composite tokens without splitting (`Türkiye'nin` $\to$ `Türkiyenin`, `Fred'` $\to$ `Fred`).
  - `punct='split'`: Splits composite tokens on internal punctuation into sub-tokens (`Türkiye'nin` $\to$ `['türkiye', 'nin']`, `robot-bilim` $\to$ `['robot', 'bilim']`) while preserving exact sentence and token-coordinate provenance (`ch · p · s · tok`).
- **Requirement `REQ-VIEW-04 (Turkish Lemma Apostrophe Remediation)`**:
  - `clean_lemma()` automatically strips inflectional suffixes following any of the 7 apostrophe characters (`'`, `’`, `‘`, `` ` ``, `´`, `ʼ`, `ʻ`) in Turkish lemmas while preserving internal compound hyphens (`türkiye'nin` $\to$ `türkiye`, `bilim-kurgu'nun` $\to$ `bilim-kurgu`, `1882'de` $\to$ `1882`).

---

## 3. Visualization & Interactive View Requirements

### 3.1 NDA-Aligned Parallel Corpora View (`corpus_toolkit/parallel_view.py`)
- **Requirement `REQ-PAR-01 (NDA Cache Integration & Safe Unpickling)`**:
  - Must load both `initial_dictionary.pickle` (`DictionaryModel`) and `scored_alignment_rows.pickle` (`dict[int, AlignmentRow]`) from `data/Neologism_Dictionary_Annotation_Cache/<Pair>/` via an isolated `_NdaSafeUnpickler` (preventing `sys.modules['app']` collisions) and memoize overlays per `pair_id`.
- **Requirement `REQ-PAR-02 (Multi-Sentence Coordinate Resolution)`**:
  - Must resolve both sentence-local `(lang, ch_no, p_no, s_no, sent_idx)` (dynamically reconstructing `sent_idx` when `sent_idx == -1`) and alignment-row-wide `(lang, ai, token_idx)` coordinates across `1:1`, `1:N`, `N:1`, and `N:M` alignment groups.
- **Requirement `REQ-PAR-03 (Disjoint Set Visual Hierarchy & Layer Ordering)`**:
  - **Set 1 — Linked Bilingual Pairs (`link_type in ('manual', 'auto')` with both EN and TR tokens)**: Blue highlight (`#bfdbfe` background, `#3b82f6` border), superscript badge `L1..Lk`, and per-alignment-row (`ai`) first-token SVG anchor (`data-link-first="L#"`).
  - **Set 2 — Unlinked Single-Language Irrealia (`single_eng` / `single_tur`)**: Light teal (`#99f6e4`) for English-only and light rose (`#fecdd3`) for Turkish-only Irrealia with category badge (`[IRREALIA: Subcategory]`), never assigned false bilingual `L#` numbers.
  - **Set 3 — Neologism Candidates (`is_neologism_candidate` / `neologism_score > 0`)**: Soft amber-yellow (`#fef08a`) with candidate score badge (`★ score`).
  - **Set 4 — Search Query Hits**: Crimson outline (`#be123c`).
  - **Layer Priority**: Top-layer `IRREALIA` (`SCIFI_*`) sorted by $n$-gram span length descending takes visual precedence over Layer 0 `REALIA` (`NER` tags).
- **Requirement `REQ-PAR-04 (Dual-Row Token Pills, SVG Connector Overlay & Summary Footer)`**:
  - Render each token as a `.nda-token-box` showing surface `tok`, toggleable `lem · pos` sub-row, and rich hover tooltip (`[ch:p:s:tok] | tok / lem | POS | NER | Irrealia | NeoScore`).
  - Draw stepped SVG connector paths with arrowheads (`<svg class="nda-link-svg">`) from the bottom-center of the first English token of each link `L#` in row `ai` to the bottom-center of the first Turkish token in row `ai`, with interactive toolbar checkboxes (`🔗 SVG Links`, `🔤 Lemmas & POS`, `🏷️ Layer 0 NER`).
  - Render a **Current Label Attributions (`.nda-summary-footer`)** block at the bottom of each alignment group summarizing Linked Bilingual Pairs, Unlinked Irrealia/Candidates, and Sentence Cardinality/Expansion metrics.

### 3.2 Flexible Interactive Columnar Table View (`corpus_toolkit/table_view.py`)
- **Requirement `REQ-TBL-01 (Zero-Install, CSP-Safe Self-Contained DataGrid)`**:
  - Must operate with zero external Python packages or external CDN requests so tables function offline in JupyterLab, VS Code Notebooks, and exported `nbconvert` HTML files.
- **Requirement `REQ-TBL-02 (Client-Side Pagination — 20 Rows/Page Default)`**:
  - Display `20` rows per page by default, with interactive page-size selector (`10`, `20`, `50`, `100`, `All`), First (`«`), Prev (`‹`), direct page buttons, Next (`›`), Last (`»`), and live row range counter.
- **Requirement `REQ-TBL-03 (Ascending/Descending Multi-Type Sorting)`**:
  - Clicking any column header cycles **Ascending (`▲`)** $\to$ **Descending (`▼`)** $\to$ **Original Order (`⇅`)**, using numeric sorting (`NaN`-last) for numeric/percentage columns and `Intl.Collator('tr', {numeric: true, sensitivity: 'base'})` for Turkish/English text columns.
- **Requirement `REQ-TBL-04 (Interactive Column Width Resizing & Layout Presets)`**:
  - Provide drag-to-resize column splitters (`.ct-col-resizer`) on every `<th>` right border (plus double-click auto-fit) and layout mode buttons (`Auto-Fit`, `Wrap Text`, `Compact`), alongside an instant substring search box and `📋 Copy TSV` button.
- **Requirement `REQ-TBL-05 (UUID-Scoped Lazy JS State & Row Cap)`**:
  - Encapsulate table state on `root._ctState` keyed by a unique instance UUID (`ct-tbl-{uid}`) and enforce a configurable `max_rows=2000` cap to prevent notebook DOM bloat.

---

## 4. Analytical Modules & Statistical Verification Contract

| Module | Primary Classes / Functions | Key Metrics & Algorithms |
| :--- | :--- | :--- |
| `alignment.py` | `AlignmentIndex`, `AlignmentStructureAnalyzer` | `1:1, 1:N, N:1, N:M, omission, addition` shapes; $R_{\text{sent}}$, word & char ratios |
| `pos.py` | `PosComparativeAnalyzer` | 17-tag UPOS profile, lexical density, noun/verb ratio, bootstrap 95% CIs, $\chi^2$, Cramér's $V$ |
| `depviz.py` | `DependencyVisualizer` | CoNLL-style dependency tables, manual spaCy `displaCy` SVG/HTML arcs, stacked parallel trees |
| `search.py` | `SearchQuery`, `CorpusSearchEngine` | Exact/glob/regex matching, Turkish `İ/I` case folding, UPOS & collocate window constraints |
| `kwic.py` | `Concordancer`, `ConcordanceResult`, `KwicLine` | Sentence-clamped symmetric/asymmetric spans, `L1..L5`/`R1..R5` sorting, `_repr_html_()` |
| `batch_kwic.py` | `BatchKwicAnalyzer` | Per-10k rates, Juilland's $D$ dispersion, Pearson $r$, Spearman $\rho$, cosine, BH-FDR $q$-values |
| `diversity.py` | `diversity_metrics`, `mattr`, `mtld`, `hdd` | 14+ LancsBox-X metrics: TTR, Guiraud $R$, CTTR, Herdan $C$, Dugast $U$, Maas $a^2$, Yule $K$, Simpson $D$, Honoré $R$, Sichel $S$, Michéa $M$, Entropy $H$, STTR, MATTR, MTLD, HD-D |
| `collocation.py` | `collocates`, `association_table` | Union-slot $2 \times 2$ contingency table; MI, $\text{MI}^2$, $\text{MI}^3$, $T$-score, signed $G^2$, Log-Dice |
| `tfidf.py` | `TfidfAnalyzer`, `tfidf_manual` | Sublinear TF ($1 + \ln f$), smooth IDF ($\ln\frac{1+N}{1+\text{DF}} + 1$), L2 norm (exact `sklearn` parity) |
| `reporter.py` | `CorpusReporter`, `top_bottom_summary` | Reproducible `.md` report, UTF-8 `.tsv` tables, 300-DPI `.png` figures, multi-sheet `.xlsx` |
| `explorer.py` | `CorpusExplorerUI`, `quick_search` | Interactive `ipywidgets` GUI + headless scriptable `quick_search` |

---

## 5. Bilingual Pedagogical Notebook Parity & Quality Gates

1. **100% Cell-for-Cell Structural Parity**:
   - [`Corpus_Analysis_tr.ipynb`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/Corpus_Analysis_tr.ipynb) (generated by `tools/build_notebook_tr.py` from `tools/nb_part_{a,b,c}_tr.py`) and [`Corpus_Analysis.ipynb`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/Corpus_Analysis.ipynb) (generated by `tools/build_notebook.py` from `tools/nb_part_{a,b,c}.py`) must have the **exact same number of cells** and **identical `(cell_type)` sequence** across Chapters 0–13 + References.
2. **Clean Tracked Notebooks vs. Headless Acceptance Artifacts**:
   - Tracked `Corpus_Analysis.ipynb` and `Corpus_Analysis_tr.ipynb` must contain **0 cell outputs** (`test_tracked_notebook_is_clean`).
   - Headless execution (`--execute`) writes `executed_Corpus_Analysis.ipynb` and `executed_Corpus_Analysis_tr.ipynb` (gitignored) with **0 failing cells**.
3. **Automated Quality Suite**:
   - `ruff check .` $\to$ `0` lint errors.
   - `pytest -q` $\to$ `100%` pass rate across all unit, numerical, view, and notebook parity tests.
