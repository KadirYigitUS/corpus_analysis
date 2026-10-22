# 14 · Input-to-Output Test Matrix and Verification Specification

## 1. Purpose and Verification Scope

This document defines the input-to-output verification matrix for the **Corpus Analysis Single-Page Application (SPA)** (`scripts/corpus_analysis/SPA/`). Each row maps a global control or tab-local input to its REST endpoint, service method, target DOM selector, and automated `pytest` / Playwright E2E test function.

---

## 2. Global Control Bar: 8 Corpus Scopes × 32 `TokenView` Combinations

### 2.1 Corpus Scope Selector (`#global-scope-select` & `#global-scope-subselect`)

| Scope Key | Secondary Filter | Expected Text Count | Repository Method | Verified By (`pytest` ID) |
| :--- | :--- | :---: | :--- | :--- |
| `all` | `None` | `13` | `CorpusRepository.get_texts_by_scope` | `test_corpus_scope_resolution_and_api_counts[all-None-None-13]` |
| `all_tr` | `None` | `8` | `CorpusRepository.get_texts_by_scope` | `test_corpus_scope_resolution_and_api_counts[all_tr-None-None-8]` |
| `trans_en` | `None` | `5` | `CorpusRepository.get_texts_by_scope` | `test_corpus_scope_resolution_and_api_counts[trans_en-None-None-5]` |
| `trans_tr` | `None` | `5` | `CorpusRepository.get_texts_by_scope` | `test_corpus_scope_resolution_and_api_counts[trans_tr-None-None-5]` |
| `indig_tr` | `None` | `3` | `CorpusRepository.get_texts_by_scope` | `test_corpus_scope_resolution_and_api_counts[indig_tr-None-None-3]` |
| `author_related` | `SM` / `ZB` / `OK` | `3` / `7` / `3` | `loader.load_author_related(author)` | `test_corpus_scope_resolution_and_api_counts[author_related-*]` |
| `author_turkish` | `SM` / `ZB` / `OK` | `2` / `4` / `2` | `loader.load_author_turkish(author)` | `test_corpus_scope_resolution_and_api_counts[author_turkish-*]` |
| `single` | `BR-SM` | `1` | `loader.load_text(text_code)` | `test_corpus_scope_resolution_and_api_counts[single-None-BR-SM-1]` |

### 2.2 32-Combination `TokenView` Matrix (`#matrix-field`, `#matrix-filter`, `#matrix-mode`, `#matrix-punct`)

| Parameter | Allowed Values | Mathematical / Sequence Effect | Verified By (`pytest` ID) |
| :--- | :--- | :--- | :--- |
| `field` | `'tok'`, `'lem'` | Selects surface token vs `clean_lemma` (`|V_lem| <= |V_tok|`). | `test_32_tokenview_combinations_invariants` |
| `filter_function_words` | `False`, `True` | Filters closed-class UPOS and Turkish Oflazer morphological heads. | `test_32_tokenview_combinations_invariants` |
| `mode` | `'drop'`, `'mask'` | `drop` compacts `view.analysed()`; `mask` keeps `None` slots in `view.forms` for sliding windows (`MATTR`, `Collocation`, `KWIC`). | `test_drop_vs_mask_punct_and_field_ordering`, `tab08_all_diversity_subtabs_and_drop_vs_mask_reactivity` |
| `punct` | `'drop'`, `'keep'`, `'strip'`, `'split'` | Controls standalone and intra-token punctuation (`|keep| >= |split| >= |drop|`). | `test_drop_vs_mask_punct_and_field_ordering` |

---

## 3. Tab-by-Tab Input-to-Output Verification Matrix (Tabs 1 to 11)

| Tab | Sub-Component / Pane | Input Controls | REST Endpoint | Target DOM Selector | Unit Test & Playwright E2E Test |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Tab 1: Inventory** | 1.1 Inventory & Source Tables | `#global-scope-select`, `.grid-search`, `th[data-col]` | `GET /api/v1/corpus/source-tables` | `#t1-inventory-grid`, `#t1-total-texts` | `test_tab01_inventory_and_subtabs_inputs_to_outputs`, `tab01_inventory_grid_search_sort_and_schema` |
| **Tab 1: Inventory** | 1.2 Schema Inspector | `.btn-inspect-schema` | `GET /api/v1/corpus/schema/<code>` | `#t1-schema-pane`, `#t1-schema-columns-grid` | `test_tab01_inventory_and_subtabs_inputs_to_outputs`, `tab01_inventory_grid_search_sort_and_schema` |
| **Tab 1: Inventory** | 1.3 Sizes Chart (`Şekil 1`) | `[data-pane="t1-pane-sizes-chart"]` | `GET /api/v1/corpus/sizes-chart` | `#t1-sizes-chart-container canvas#t1-sizes-canvas` | `test_tab01_inventory_and_subtabs_inputs_to_outputs`, `tab01_all_subtabs_charts_tables_and_scope_invalidation` |
| **Tab 1: Inventory** | 1.4 Verify Files Table | `[data-pane="t1-pane-verify"]` | `GET /api/v1/corpus/verify-files` | `#t1-verify-grid .datagrid-table` | `test_tab01_inventory_and_subtabs_inputs_to_outputs`, `tab01_all_subtabs_charts_tables_and_scope_invalidation` |
| **Tab 1: Inventory** | 1.5 Size Summary Table | `[data-pane="t1-pane-summary"]` | `GET /api/v1/corpus/size-summary` | `#t1-summary-grid .datagrid-table` | `test_tab01_inventory_and_subtabs_inputs_to_outputs`, `tab01_all_subtabs_charts_tables_and_scope_invalidation` |
| **Tab 1: Inventory** | 1.6 Memory & Content Lemmas | `[data-pane="t1-pane-memory"]` | `GET /api/v1/corpus/memory-report`, `/content-lemmas` | `#t1-memory-grid`, `#t1-lemmas-grid` | `test_tab01_inventory_and_subtabs_inputs_to_outputs`, `tab01_all_subtabs_charts_tables_and_scope_invalidation` |
| **Tab 2: Alignment** | 2.1 Pair Explorer & NER | `#t2-select-pair`, `.ner-pill-btn`, `.ch-btn` | `GET /api/v1/alignment/kpis/<pair>`, `POST /rows` | `#t2-alignment-grid`, `#t2-sent-diff-canvas` | `test_tab02_alignment_and_structure_inputs_to_outputs`, `tab02_alignment_kpis_chapters_ner_and_pair_switch` |
| **Tab 2: Alignment** | 2.2 Structure Summary (`1A/1B`) | `[data-pane="t2-pane-structure"]` | `GET /api/v1/alignment/structure-summary`, `POST /structure-scatter` | `#t2-stacked-canvas`, `#t2-structure-summary-grid`, `#t2-scatter-canvas` | `test_tab02_alignment_and_structure_inputs_to_outputs`, `tab02_structure_summary_and_scatter_subtab` |
| **Tab 3: NDA Parallel** | 3.1 Parallel Stage & SVG | `#t3-select-pair`, `#t3-select-mode`, `#t3-input-hits` | `GET /api/v1/alignment/nda/html/<pair>` | `#t3-nda-stage`, `svg.nda-link-svg path` | `test_tab03_nda_parallel_and_dictionary_inputs_to_outputs`, `tab03_nda_parallel_tokens_svg_links_and_dictionary_drawer` |
| **Tab 3: NDA Parallel** | 3.2 Tripartite Dictionary | `#btn-toggle-nda-dict` | `GET /api/v1/alignment/nda/dictionary/<pair>` | `#t3-dict-drawer`, `#t3-dict-linked-list` | `test_tab03_nda_parallel_and_dictionary_inputs_to_outputs`, `tab03_nda_parallel_tokens_svg_links_and_dictionary_drawer` |
| **Tab 4: POS** | 4.1 UPOS Profiles & Matrix | `#t4-select-comp-2c`, `#t4-check-content-only` | `POST /api/v1/syntax/pos/profiles`, `GET /author-summary` | `#t4-pos-profiles-grid`, `#t4-author-summary-table` | `test_tab04_pos_and_tab05_depviz_inputs_to_outputs`, `tab04_pos_profiles_pair_delta_and_group_comparison` |
| **Tab 4: POS** | 4.2 Heatmap (`Şekil 2A`) | `[data-pane="t4-pane-heatmap"]` | `GET /api/v1/syntax/pos/matrix` | `#t4-heatmap-chart-container canvas#t4-heatmap-canvas` | `test_tab04_pos_and_tab05_depviz_inputs_to_outputs`, `tab04_pos_heatmap_dumbbell_and_forest_subtabs` |
| **Tab 4: POS** | 4.3 Dumbbell (`Şekil 2B`) | `[data-pane="t4-pane-dumbbell"]`, `#t4-select-pair-2b` | `GET /api/v1/syntax/pos/pair-delta/<pair>` | `#t4-dumbbell-chart-container canvas#t4-dumbbell-canvas` | `test_tab04_pos_and_tab05_depviz_inputs_to_outputs`, `tab04_pos_heatmap_dumbbell_and_forest_subtabs` |
| **Tab 4: POS** | 4.4 Forest Plot (`Şekil 2C`) | `[data-pane="t4-pane-forest"]` | `POST /api/v1/syntax/pos/group-comparison` | `#t4-forest-chart-container canvas#t4-forest-canvas` | `test_tab04_pos_and_tab05_depviz_inputs_to_outputs`, `tab04_pos_heatmap_dumbbell_and_forest_subtabs` |
| **Tab 5: Dependency** | 5.1 Single Sentence Tree | `#t5-input-text`, `#t5-input-ch`, `#t5-input-p`, `#t5-input-s` | `POST /api/v1/syntax/dep/tree-svg`, `POST /dep/conll` | `#t5-tree-stage svg`, `#t5-conll-grid` | `test_tab04_pos_and_tab05_depviz_inputs_to_outputs`, `tab05_dependency_tree_svg_conll_and_download` |
| **Tab 5: Dependency** | 5.2 Bilingual Aligned Trees | `[data-pane="t5-pane-aligned"]`, `#t5-select-pair`, `#t5-check-dim` | `GET /api/v1/syntax/dep/aligned/<pair>/<ai>` | `#t5-aligned-tree-stage svg` (`2` trees) | `test_tab04_pos_and_tab05_depviz_inputs_to_outputs`, `tab05_aligned_bilingual_trees_and_tab06_kwic_subtabs` |
| **Tab 6: KWIC** | 6.1 KWIC Grid & Punct Compare | `#t6-input-query`, `#t6-select-match`, `#t6-select-sort` | `POST /api/v1/concordance/search`, `POST /punct-compare` | `#t6-kwic-grid`, `#t6-punct-pane` | `test_tab06_kwic_and_subtabs_inputs_to_outputs`, `tab06_kwic_modes_spans_sort_punct_compare_and_invalid_regex` |
| **Tab 6: KWIC** | 6.2 Search Summary & Views | `[data-pane="t6-pane-summary"]`, `[data-pane="t6-pane-views"]` | `POST /api/v1/concordance/summary`, `POST /views-compare` | `#t6-summary-bars-canvas`, `#t6-summary-table-container`, `#t6-views-table-container` | `test_tab06_kwic_and_subtabs_inputs_to_outputs`, `tab05_aligned_bilingual_trees_and_tab06_kwic_subtabs` |
| **Tab 6: KWIC** | 6.3 NLTK Cross-Check | `[data-pane="t6-pane-nltk"]`, `#t6-btn-run-nltk` | `POST /api/v1/concordance/nltk` | `#t6-nltk-lines-container`, `#t6-nltk-similar-container` | `test_tab06_kwic_and_subtabs_inputs_to_outputs`, `tab05_aligned_bilingual_trees_and_tab06_kwic_subtabs` |
| **Tab 7: Dispersion** | 7.1 Juilland D & BH-FDR | `#t7-input-terms`, `#t7-btn-run-batch` | `POST /api/v1/concordance/batch-dispersion` | `#t7-summary-grid`, `#t7-correlation-grid` | `test_tab07_batch_dispersion_and_matrices_inputs_to_outputs`, `tab07_batch_dispersion_and_correlation_grids` |
| **Tab 7: Dispersion** | 7.2 Counts, Heatmaps & Curves | `[data-pane="t7-pane-tables"]`, `t7-pane-rates-heatmap`, `t7-pane-corr-matrix`, `t7-pane-dispersion-curves` | `POST /api/v1/concordance/batch-matrices` | `#t7-counts-table`, `#t7-rates-canvas`, `#t7-corr-canvas`, `#t7-chunk-canvas` | `test_tab07_batch_dispersion_and_matrices_inputs_to_outputs`, `tab07_labeled_groups_tables_heatmaps_and_dispersion_curves` |
| **Tab 8: Diversity** | 8.1 LancsBox-X Table & MATTR | `#t8-select-text`, `#t8-btn-view-mattr`, `#matrix-mode` | `POST /api/v1/lexicon/diversity/table`, `POST /diversity/mattr` | `#t8-diversity-grid`, `#t8-mattr-pane` | `test_tab08_diversity_and_subtabs_inputs_to_outputs`, `tab08_lexical_diversity_table_and_mattr_trajectory` |
| **Tab 8: Diversity** | 8.2 Sensitivity, Compare, Radar, MATTR, Zipf | `[data-pane="t8-pane-sensitivity"]` .. `[data-pane="t8-pane-zipf"]` | `POST /api/v1/lexicon/diversity/{sensitivity,compare,radar,mattr-trajectories,zipf-curves}` | `#t8-sens-canvas`, `#t8-tok-lem-table`, `#t8-radar-canvas`, `#t8-mattr-canvas`, `#t8-zipf-canvas` | `test_tab08_diversity_and_subtabs_inputs_to_outputs`, `tab08_all_diversity_subtabs_and_drop_vs_mask_reactivity` |
| **Tab 9: Collocation** | 9.1 Union-Slot Table & Radial SVG | `#t9-input-node`, `#t9-select-metric`, `#t9-input-min-freq` | `POST /api/v1/lexicon/collocation/table` | `#t9-collocation-grid`, `#t9-graphcoll-stage svg` | `test_tab09_collocation_tab10_tfidf_and_tab11_explorer`, `tab09_collocation_6_metrics_min_freq_and_graphcoll` |
| **Tab 9: Collocation** | 9.2 Scatter, Sensitivity & NLTK | `[data-pane="t9-pane-scatter"]`, `t9-pane-sensitivity`, `t9-pane-nltk` | `POST /api/v1/lexicon/collocation/{scatter,sensitivity,nltk}` | `#t9-scatter-canvas`, `#t9-measures-table`, `#t9-window-table`, `#t9-nltk-collocs-table` | `test_tab09_collocation_tab10_tfidf_and_tab11_explorer`, `tab09_collocation_and_tab10_tfidf_all_subtabs` |
| **Tab 10: TF-IDF** | 10.1 Keywords & Bundle ZIP | `#t10-input-topk`, `#t10-check-exclude-propn`, `#t10-btn-download-bundle` | `POST /api/v1/lexicon/tfidf/keywords`, `POST /api/v1/export/bundle` | `#t10-keywords-container .kpi-card` | `test_tab09_collocation_tab10_tfidf_and_tab11_explorer`, `tab10_tfidf_keywords_propn_toggle_and_bundle_download` |
| **Tab 10: TF-IDF** | 10.2 Heatmap & Structured Report | `[data-pane="t10-pane-heatmap"]`, `[data-pane="t10-pane-report-preview"]` | `POST /api/v1/lexicon/tfidf/dense`, `GET /api/v1/lexicon/report/preview` | `#t10-heatmap-canvas`, `#t10-report-markdown-preview .report-section-card`, `#t10-report-summary-table` | `test_tab09_collocation_tab10_tfidf_and_tab11_explorer`, `tab09_collocation_and_tab10_tfidf_all_subtabs` |
| **Tab 11: Explorer** | 11.1 Quick Search & Python Twin | `#t11-input-term`, `#t11-btn-run-console`, `#t11-btn-evict-all` | `POST /api/v1/export/quick-search`, `POST /api/v1/corpus/evict-all` | `#t11-hits-badge`, `#t11-samples-container`, `#t11-python-snippet` | `test_tab09_collocation_tab10_tfidf_and_tab11_explorer`, `tab11_explorer_quick_search_and_clipboard_copy` |
| **Help & Formulas** | 12.1 Contextual `?` & Drawer | `#btn-open-help`, `.btn-pane-help[data-help-tab]` | `GET /api/v1/help/formulas` | `#help-docs-drawer`, `.formula-card .math-frac` | `test_help_formulas_catalog_completeness_and_zero_raw_latex`, `shell_modals_and_help_drawer` |
