# 10 · End-User Manual / Son Kullanıcı El Kitabı

## 1. Overview and Operational Philosophy / Genel Bakış ve Çalışma Felsefesi

### English
The **Corpus Analysis Single-Page Application (SPA)** is an interactive, professional digital humanities workstation designed for rigorous quantitative analysis of Turkish and English literary corpora. The application integrates the complete analytical pipeline of [`corpus_toolkit`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/corpus_toolkit/) into a responsive web interface. It is organized into:
- A persistent **Global Control Bar** managing corpus scopes, tokenization regimes, and memory bounds.
- **Corpus Info** and **Settings** modals providing visual dossiers and configuration management.
- A sliding **Help & Formulas Drawer** displaying exact mathematical definitions and primary citations.
- **11 Specialized Feature Tabs** covering the entire spectrum of corpus linguistics.

### Türkçe
**Derlem Analizi Tek Sayfa Uygulaması (SPA)**, Türkçe ve İngilizce edebi derlemlerin nicel analizine yönelik geliştirilmiş profesyonel bir dijital beşeri bilimler çalışma istasyonudur. Uygulama, [`corpus_toolkit`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/corpus_toolkit/) kütüphanesinin tüm analitik kabiliyetlerini modern bir web arayüzünde birleştirir:
- Derlem kapsamlarını, belirteçleme (tokenization) rejimlerini ve bellek sınırlarını yöneten kesintisiz bir **Genel Denetim Çubuğu**.
- Görsel kaynak dosyalarını ve yapılandırma yönetimini sağlayan **Derlem Bilgisi** ve **Ayarlar** modalleri.
- Kesin matematiksel formülleri ve akademik referansları sunan **Yardım ve Formüller Çekmecesi**.
- Derlem dilbiliminin tüm aşamalarını kapsayan **11 Uzmanlaşmış Analiz Sekmesi**.

---

## 2. Global Control Bar / Genel Denetim Çubuğu

```
+---------------------------------------------------------------------------------------------------------+
| [Scope: All (13) v] [Field: Lemma v] [FuncWords: Strip v] [Punct: Drop v]  [RSS: 480 MB] [Info] [Settings] [Help] |
+---------------------------------------------------------------------------------------------------------+
```

### 2.1 8 Loader Scopes / 8 Veri Yükleme Kapsamı
- **`all` (All Texts / Tüm Metinler)**: Loads all 13 canonical texts (5 English sources, 5 Turkish translations, 3 Turkish indigenous novels).
- **`english` (All English / İngilizce Kaynaklar)**: Ingests the 5 English pioneer science fiction novels (`IR-IA`, `TL-PA`, `TLP-ML`, `TSP-JL`, `ASD-PKD`).
- **`turkish` (All Turkish / Tüm Türkçe Metinler)**: Ingests all 8 Turkish novels (5 translations + 3 indigenous novels).
- **`pairs` (Translation Pairs / Çeviri Çiftleri)**: Loads the 5 aligned English-Turkish parallel corpora (`IR-IA_BR-SM`, `TL-PA_A-ZB`, `TLP-ML_YG-ZB`, `TSP-JL_KS-ZB`, `ASD-PKD_KT-OK`).
- **`indigenous` (Indigenous Turkish / Telif Türkçe Romanlar)**: Ingests the 3 native Turkish SF novels (`OBI-SM`, `SU-ZB`, `SCS-OK`).
- **`author_related` (Author Sub-corpus / Yazar Alt-Derlemi)**: Loads all texts associated with a selected author (`SM`, `ZB`, or `OK`).
- **`author_tr` (Author Turkish Sub-corpus / Yazar Türkçe Metinleri)**: Loads Turkish translations and indigenous novels for a chosen author.
- **`text` (Single Text / Tek Metin)**: Targets a single text code for isolated micro-analysis.

### 2.2 32-Combination TokenView / 32 Kombinasyonlu Belirteç Rejimi
The application provides full support for 32 distinct tokenization, lemmatization, and filtering combinations:
1. **Field (`tok` | `lem`)**:
   - `tok`: Raw surface tokens as printed in the text.
   - `lem`: Lemmatized base forms with Turkish apostrophe inflection remediation (`clean_lemma`).
2. **Function Words Filter (`False` | `True`)**:
   - English: Filters closed-class UPOS categories (`DET`, `PRON`, `CCONJ`, `ADP`, `AUX`, `SCONJ`, `INTJ`, `PART`).
   - Turkish: Filters UPOS closed classes and Oflazer morphological head classes (`Postp`, `Conj`, `Det`, `Pron`, `Ques`, `Interj`, `Punc`).
3. **Filter Mode (`drop` | `mask`)**:
   - `drop`: Completely removes excluded items from the token array.
   - `mask`: Replaces excluded tokens with `<MASK>` to preserve positional offsets for distance metrics.
4. **Punctuation Regime (`drop` | `keep` | `strip` | `split`)**:
   - `drop`: Removes standalone punctuation marks while retaining intra-word hyphens and apostrophes.
   - `keep`: Retains punctuation marks as discrete tokens for dialogue and clause analysis.
   - `strip`: Removes punctuation characters within tokens without breaking words (`robot-bilim` $\to$ `robotbilim`).
   - `split`: Decomposes hyphenated and apostrophe-joined compounds into sub-tokens (`türkiye'nin` $\to$ `['türkiye', 'nin']`).

### 2.3 Live RSS Memory Gauge / Canlı Bellek Göstergesi
Displays real-time Resident Set Size (RSS) memory consumption measured from `/proc/self/statm`:
- **Green ($< 1{,}000\text{ MB}$)**: Safe operating zone.
- **Amber ($1{,}000–1{,}350\text{ MB}$)**: Moderate consumption. Background LRU cache active.
- **Red ($> 1{,}350\text{ MB}$)**: Approaching $1{,}500\text{ MB}$ ceiling. Click **Evict Unused** to drop cached objects and trigger garbage collection.

---

## 3. Corpus Info Modal & Visual Dossier / Derlem Bilgi Modali ve Görsel Dosya

Accessed by clicking the **Corpus Info** button in the header or in any row of Tab 1:
- **Detailed Source Tables**: Comprehensive breakdowns of English originals, Turkish translations, indigenous works, and sentence-aligned parallel pairs.
- **Book Cover Imagery**: High-resolution cover images of first editions and canonical translations.
- **Author & Translator Portraits**: Historical photographic portraits of authors (Asimov, Anderson, Lewis, Le Guin, Dick, Sezgin, Belli, Kenter) and translators.
- **Bibliographic Metadata**: Publication years, original titles, publishers, page counts, sentence totals, and token counts.

---

## 4. Settings & Corpus Registry Modal / Ayarlar ve Derlem Kayıt Modali

The **Settings Modal** provides live configuration of paths and metadata without restarting the server:
- **Path Registry (`spa_paths.yaml`)**:
  - Parquet cache directory path.
  - Image assets directory path (`book_covers/`, `author_portraits/`).
  - Report and bundle export output path.
- **Corpus Metadata (`corpus_metadata.yaml`)**:
  - Editable metadata fields: author biography, translator attributions, publication dates, and genre notes.
- **Asset Upload**: Direct file uploader for updating book covers and author portrait images.

---

## 5. Help & Formulas Drawer / Yardım ve Formüller Çekmecesi

Sliding drawer accessible from any tab (`#btn-open-help` or contextual per-pane `?` `.btn-pane-help` buttons) providing mathematical transparency across all 12 catalog sections (`Global Matrix` and `Tab 1` through `Tab 11`):
- **Typographic Semantic HTML/MathML Formulas**: Renders stacked fractions (`.math-frac` / `.math-num` / `.math-den`), radical spans (`.math-sqrt` / `.math-radicand`), subscripts, and superscripts via `formatFormulaHtml(entry)` (`SPA/services/help_catalog_data.py` & `help_docs_drawer.js`) with zero raw LaTeX backslashes (`\frac`, `\text`, `\sqrt`).
- **Contextual `?` Pane Routing**: Clicking `?` in the Global Matrix bar, any tab subtab bar, or any `ChartHost` chart card opens `#help-docs-drawer` automatically filtered to that tab's equations and boundary guards.
- **Edge-Case / NaN Rules**: Explicit documentation of boundary conditions ($N < 42$ for HD-D, $N < 1{,}000$ for STTR, division-by-zero guards, and `mode='drop'` vs `mode='mask'` sliding-window behavior).
- **Primary Methodological Citations**: Complete bibliographic entries linking metrics to foundational literature (Templin 1957, Guiraud 1954, Covington & McFall 2010, McCarthy & Jarvis 2010, Church & Hanks 1990, Dunning 1993, Rychlý 2008, Juilland & Chang-Rodríguez 1964, Benjamini & Hochberg 1995, Spärck Jones 1972).

---

## 6. Walkthrough of the 11 Feature Tabs / 11 Analitik Çalışma İstasyonu

### Tab 1: Corpus Inventory & Schema Inspector
- **Inventory DataGrid**: Displays file codes, language, author, genre, sentence count, and token totals. Sortable by any column with quick text filtering.
- **Token Size Distribution (Figure 1)**: Interactive horizontal bar chart comparing word counts across texts.
- **Schema Inspector**: Inspects token and sentence schemas, verifying column types (`tok_id`, `surface`, `lemma`, `upos`, `xpos`, `deprel`, `head`).

### Tab 2: Translation Alignment & Length-Delta Explorer
- **Left Chapter Sidebar**: Fast jumping between chapters with per-chapter alignment row counters.
- **Alignment Cardinality Bar (Figure 1A)**: Visualizes distribution of $1{:}1, 1{:}N, N{:}1, N{:}M$, omission, and addition rows.
- **Sentence-Length Delta Sorters**: Sort alignment units by sentence count delta ($\Delta s$), word count delta ($\Delta w$), or character count delta ($\Delta c$).
- **Color-Coded Row Display**: Background styling indicating alignment type (`row-one`, `row-eng`, `row-tur`, `row-empty`).

### Tab 3: NDA Parallel Corpora & Tripartite Dictionary Viewer
- **Side-by-Side Parallel View**: English source sentences rendered alongside aligned Turkish translations.
- **Tripartite Global Dictionary Drawer**:
  - `Linked Items`: Cross-lingual alignment pairs.
  - `English Only`: Unmatched source terms.
  - `Turkish Only`: Unmatched target terms.
- **Stepped SVG Link Connectors**: Renders dynamic connecting lines linking corresponding source and target entity spans.
- **Visual Sets**: Distinct color-coding across 4 disjoint sets with Layer 0 Realia vs Top-Layer Irrealia resolution.

### Tab 4: Comparative POS & Morphosyntactic Profiler
- **17-Tag UPOS Heatmap (Figure 2A)**: Visualizes distribution percentages of Universal POS tags across all corpus texts.
- **Translation vs Original Delta ($\Delta\text{pp}$ Divergence, Figure 2B)**: Bar chart showing percentage point shifts between English source and Turkish translation profiles.
- **Group Comparison & Bootstrap CIs (Figure 2C)**: Compares translated vs indigenous corpora with 95% bootstrap confidence intervals ($2{,}000$ resamples) and $\chi^2$ test of homogeneity.

### Tab 5: Syntactic Dependency (`displaCy` UD) Studio
- **Sentence Coordinate & Alignment Picker**: Direct lookup by chapter/paragraph/sentence coordinates or alignment index (`ai`).
- **CoNLL-U Tabular Breakdown**: Shows token index, lemma, UPOS, syntactic head, and Universal Dependency relation.
- **Interactive SVG Tree Canvas**: Zoomable and pannable dependency tree displaying directed arcs from heads to dependents.
- **Function Word Dimming**: Toggle to dim closed-class auxiliary and connective words (`opacity: 0.4`), highlighting core clausal structure.

### Tab 6: Corpus Search Engine & 5-View KWIC Concordancer
- **Multi-Term Query Builder**: Supports exact string matches, wildcards (`robot*`), and regex (`[bB]ilim.*`).
- **Linguistic Filters**: Constrain matches by UPOS tag and collocate co-occurrence within an asymmetric window ($L, R \le 20$).
- **5-View KWIC Presentations**:
  1. `kwic`: Classic center-aligned keyword in context with adjustable left/right horizons.
  2. `coords`: Search hits with chapter, paragraph, and sentence coordinate metadata.
  3. `bilingual`: Aligned translation cards showing parallel English and Turkish contexts.
  4. `parallel`: NDA-styled parallel sentences with SVG link overlays.
  5. `table`: Tabular DataGrid exportable directly to TSV or clipboard.
- **Multi-Key Sorting**: Stable sorting by first right word ($R_1$), second right word ($R_2$), or left context ($L_1$).

### Tab 7: Batch KWIC, Juilland's $D$ Dispersion & BH-FDR Correlation Matrix
- **Batch Query Input**: Textarea for multi-term lists or JSON term groupings.
- **Juilland's $D$ Dispersion Barcodes (Figure 3A)**: Evaluates term dispersion across 10 equal text chunks ($D \approx 1$ represents even distribution; $D \approx 0$ represents localized clustering).
- **Per-10k Rate Heatmap (Figure 3B)**: Normalized frequency matrix across all corpus texts.
- **Pairwise Correlation & BH-FDR (Figure 3C)**: Pairwise Pearson $r$, Spearman $\rho$, and cosine similarity matrices with Benjamini-Hochberg False Discovery Rate $q$-value significance thresholds ($q < 0.05$).

### Tab 8: Lexical Diversity & Richness Laboratory
- **22-Column LancsBox-X DataGrid**: Comprehensive richness metrics with sorting, CSV export, and hover tooltips explaining formula semantics.
- **Radar Profiles (Figure 4A)**: 6-axis standardized radar chart comparing vocabulary breadth across texts.
- **MATTR Trajectories (Figure 4B)**: Moving-Average TTR curves plotted across text length for window sizes 50, 100, and 500.
- **Zipf Rank-Frequency Curves (Figure 4C)**: Double-logarithmic ($\log_{10} \text{rank}$ vs $\log_{10} \text{frequency}$) plots verifying power-law scaling.

### Tab 9: Union-Slot Collocation & GraphColl Studio
- **Node & Window Controls**: Select node lemma and configure left/right window horizons ($L, R \le 20$, clamped to sentence boundaries).
- **6 Association Measures**: Rank candidates by Pointwise Mutual Information ($\text{MI}, \text{MI}^2, \text{MI}^3$), Student's $T$-score, signed Log-Likelihood ($G^2$), or Log-Dice.
- **Union-Slot $2 \times 2$ Contingency Display**: Explicit display of observed ($O_{11}$), expected ($E_{11}$), node window total ($R_1$), and collocate total ($C_1$).
- **GraphColl Scatter Plot (Figure 5)**: Association strength vs statistical evidence plot with interactive node hovering.

### Tab 10: Sublinear TF-IDF Keyness & Research Reporter
- **Keyness Extraction**: Sublinear TF-IDF ranking highlighting distinctive vocabulary per book or chunk.
- **PROPN Exclusion Toggle**: Filter out proper nouns to focus exclusively on thematic and stylistic vocabulary.
- **Small-Multiple Bar Charts (Figure 6)**: Horizontal bar charts displaying top-$K$ keyness terms for each novel.
- **Research Bundle Exporter**: One-click download packaging Markdown documentation (`.md`), data tables (`.tsv`), high-resolution charts (`.png`), and an Excel workbook (`.xlsx`) into a single ZIP archive.

### Tab 11: Unified Corpus Explorer & Scriptable Console
- **Unified Query Runner**: Run cross-cutting searches combining token constraints, POS filters, and KWIC formatting.
- **Copy-as-Python-Script Console**: Automatically translates GUI query configurations into executable Python scripts matching `corpus_toolkit` syntax.
- **Session Memory Management**: Explicit **Evict All** trigger to flush loaded corpus models from RAM.

---

## 7. Acceptance Gate Checklist / Kabul Kapısı Kontrol Listesi

- [x] Bilingual documentation structure complete (TR/EN) for all primary sections.
- [x] Global Control Bar fully detailed across 8 scopes, 32 TokenView combinations, and live RSS memory gauge.
- [x] Corpus Info Modal documented with source tables, book covers, and author portraits.
- [x] Settings Modal documented with editable paths, metadata registry, and image upload workflow.
- [x] Help & Formulas Drawer documented with mathematical formulas and primary citations.
- [x] All 11 feature tabs documented with specific controls, visual figures, and user workflows.
