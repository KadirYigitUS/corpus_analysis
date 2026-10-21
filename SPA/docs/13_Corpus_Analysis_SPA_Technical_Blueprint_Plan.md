# 13 · Master Implementation Blueprint Plan: Corpus Analysis SPA (`v2.1`)

> [!IMPORTANT]
> **GOVERNANCE, `AGENTS.md` & REPOSITORY INVARIANTS**
> - **Authority**: Derived from [`scripts/prompts/Corpus_Analysis_SPA_Technical_Blueprint.md`](file:///home/ben/Documents/thesis/scripts/prompts/Corpus_Analysis_SPA_Technical_Blueprint.md) and [`prompts/Corpus_Analysis_SPA_Blueprint_Plan_20261021_104300.md`](file:///home/ben/Documents/thesis/prompts/Corpus_Analysis_SPA_Blueprint_Plan_20261021_104300.md).
> - **Target Repository**: Standalone repository in [`/home/ben/Documents/thesis/scripts/corpus_analysis`](file:///home/ben/Documents/thesis/scripts/corpus_analysis) (`git@github.com:KadirYigitUS/corpus_analysis.git`, branch **`master`**).
> - **Zero-Error Hard Limits**: Strict $\le 180$ lines pre-formatting target ($\le 200$ lines hard gate) for every `.py, .js, .css, .html` file.
> - **Professional Scope**: Pure workstation for corpus analytics, concordance, visualization, and reports. Dedicated **Help & Calculation Formulas Drawer** (`help_docs_drawer.js` / `/api/v1/help/formulas`) provides operational guides, exact equations, and primary citations without literary/theoretical background essays.
> - **Configurable Corpus Registry & Source Tables**: Dedicated **`Corpus Info` Modal** (`corpus_info_modal.js`) renders full source tables alongside configurable book cover and author/translator portrait images. All paths and metadata are editable via `spa_paths.yaml`, `corpus_metadata.yaml`, and `/api/v1/config/*`.

---

## 1. Executive Architecture & Directory Skeleton

```
scripts/corpus_analysis/SPA/
├── app.py                      # Flask WSGI application factory (<= 140 lines)
├── config/
│   ├── spa_paths.yaml          # Editable input/output/cache directories
│   └── corpus_metadata.yaml    # Editable book metadata, author portraits, book covers
├── models/                     # Immutable DTOs & dataclasses (<= 160 lines/file)
│   ├── config_dto.py           # PathConfigDTO, BookMetadataDTO, AuthorMetadataDTO
│   ├── view_params_dto.py      # TokenViewParamsDTO, CorpusScopeDTO
│   ├── search_dto.py           # SearchQueryDTO, KwicSpanDTO
│   ├── alignment_dto.py        # AlignmentFilterDTO, DeltaSortDTO, NerPillDTO
│   └── stats_dto.py            # CollocationParamsDTO, DiversityParamsDTO, ExportDTO
├── repositories/               # Exclusive file I/O & cache operations (<= 170 lines/file)
│   ├── config_repository.py    # Reads/writes YAML files & manages uploaded images
│   ├── corpus_repository.py    # Wraps CorpusLoader & 2 GB LRU Parquet cache
│   ├── nda_cache_repository.py # Safe _NdaSafeUnpickler deserialization
│   └── export_repository.py    # CorpusReporter markdown/tsv/png/xlsx bundle export
├── services/                   # Pure computational services (<= 175 lines/file)
│   ├── config_metadata_service.py # Path & metadata validation, formula registry
│   ├── inventory_memory_service.py # Source tables, schema inspector, RSS telemetry
│   ├── alignment_delta_service.py # R_sent, word/char ratios, length deltas
│   ├── nda_parallel_service.py # 4 disjoint visual sets, SVG links, attributions
│   ├── pos_service.py          # UPOS distributions, delta-pp, bootstrap CIs (seed=13)
│   ├── depviz_service.py       # CoNLL tables, manual displaCy SVG arc trees
│   ├── search_kwic_service.py  # 5+1 KWIC views, multi-key sort, NLTK cross-check
│   ├── batch_dispersion_service.py # Juilland's D (n=10), Pearson/Spearman/Cosine, BH-FDR
│   ├── diversity_service.py    # 22-column LancsBox-X table with NaN guards, MATTR, Zipf
│   ├── collocation_service.py  # Union-Slot contingency, MI/G2/LogDice, GraphColl
│   ├── tfidf_service.py        # Sublinear TF-IDF, PROPN ablation switch, chunking
│   └── reporter_bundle_service.py # Research report packaging & quick_search console
├── controllers/                # Versioned Flask Blueprints /api/v1/ (<= 160 lines/file)
│   ├── config_controller.py    # /api/v1/config/* & /api/v1/help/*
│   ├── corpus_controller.py    # /api/v1/corpus/*
│   ├── alignment_controller.py # /api/v1/alignment/*
│   ├── syntax_controller.py    # /api/v1/syntax/*
│   ├── concordance_controller.py # /api/v1/concordance/*
│   ├── lexicon_controller.py   # /api/v1/lexicon/*
│   └── export_controller.py    # /api/v1/export/*
├── views/                      # Jinja2 templates & modular ES6 frontend
│   ├── templates/
│   │   ├── index.html          # Shell layout (<= 150 lines)
│   │   └── partials/           # 11 Modular Tab partials + Modals (<= 160 lines each)
│   └── static/
│       ├── css/                # Dark/academic design system variables (<= 180 lines each)
│       ├── js/                 # Modular ES6 controllers (<= 175 lines each)
│       └── i18n/               # Turkish and English locale catalogs
└── tests/                      # Pytest suite & Selenium E2E tests
```

---

## 2. Global Header, Modals & 11 Interactive Workstations

1. **Global Control Header**:
   - 8 Corpus Scope Selectors (`All`, `All EN`, `All TR`, `Trans EN`, `Trans TR`, `Indig TR`, `Aligned Pairs`, `Single Text`).
   - 32-Combination `TokenView` Matrix Bar: `field` $\times$ `filter_function_words` $\times$ `mode` $\times$ `punct`.
   - Real-Time RSS Memory Telemetry Gauge (`< 1500 MB`).
   - `Corpus Info` Button, `Settings` Button, `Help & Formulas` Button, `TR / EN` Switch.
2. **Corpus Info & Sources Modal (`corpus_info_modal.js`)**:
   - Comprehensive source tables for English originals, Turkish translations, and indigenous novels.
   - High-resolution **book cover image cards** and **author/translator portrait dossiers**.
   - Direct "Edit Info / Change Image" actions persisting to `corpus_metadata.yaml`.
3. **Settings & Corpus Registry Modal (`config_editor_modal.js`)**:
   - Live editable input locations, output directories, cache paths, and image storage paths.
   - Hot-reload endpoint validation (`POST /api/v1/config/paths`).
4. **Help, Calculation Formulas & Sources Drawer (`help_docs_drawer.js`)**:
   - Dynamic math documentation with KaTeX rendering, variable definitions, and boundary guards.
   - Primary methodological literature citations (Brezina, Biber, Covington, McCarthy, Juilland, etc.).
5. **11 Workstation Tabs**:
   - **Tab 1: Corpus Inventory & Schema Inspector** (DataGrid, schema inspection, Figure 1 token distribution).
   - **Tab 2: Translation Alignment & Length-Delta Explorer** (Chapter sidebar, stacked alignment bars, $\Delta s, \Delta w, \Delta c$ sorters, NER filter bar).
   - **Tab 3: NDA Parallel Corpora & Tripartite Dictionary** (4 disjoint visual sets, Top-Layer Irrealia > Layer 0 Realia, stepped SVG connectors, tripartite dictionary drawer).
   - **Tab 4: Comparative POS & Morphosyntactic Profiler** (17-tag UPOS, lexical density, $\Delta\text{pp}$ divergence, bootstrap 95% CIs with seed 13).
   - **Tab 5: Syntactic Dependency (`displaCy` UD) Studio** (CoNLL tables, manual SVG arc layout, function-word dimming).
   - **Tab 6: Corpus Search & 5-View KWIC Concordancer** (Multi-term chips, exact/glob/regex, Turkish $\text{İ/I}$ folding, 5 views, multi-key sort).
   - **Tab 7: Batch KWIC, Dispersion & Correlation Matrix** (Juilland's $D$, Pearson/Spearman/Cosine heatmaps with Benjamini–Hochberg FDR $q$-values).
   - **Tab 8: Lexical Diversity & Richness Laboratory** (22-column LancsBox-X table with exact NaN guards, $O(N)$ sliding MATTR, Zipf plots).
   - **Tab 9: Union-Slot Collocation & GraphColl Studio** ($R_1 = |\bigcup \text{slots}|$, MI, $G^2$, Log-Dice, GraphColl scatter).
   - **Tab 10: Sublinear TF-IDF Keyness & Research Reporter** (Sublinear TF, smooth IDF, PROPN ablation switch, `.md/.tsv/.png/.xlsx` bundle export).
   - **Tab 11: Unified Corpus Explorer & Scriptable Console** (Single-screen query explorer + copyable Python script generator).

---

## 3. Formal Acceptance Gate Checklist

- [x] Full architectural synthesis completed across all 14 notebook chapters and 4 sibling systems.
- [x] All 12 engineering specification documents authored, verified, and pushed to `origin/master`.
- [x] Professional workstation scope strictly enforced (Help/Formula drawer instead of narrative prose).
- [x] Configurable path and metadata architecture locked (`spa_paths.yaml` & `corpus_metadata.yaml`).
- [x] Module line-budget table locked at $\le 180$ lines pre-formatting ($\le 200$ lines hard CI gate).
- [x] Tri-Model Audit launched across Claude Sonnet 5.5, GPT-OSS 120B, and Gemini 3.8 Flash.
