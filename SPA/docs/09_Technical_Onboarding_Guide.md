# 09 · Technical Onboarding Guide

## 1. Introduction and Architectural Mindset

Welcome to the **Corpus Analysis Single-Page Application (SPA)** codebase (`scripts/corpus_analysis/SPA/`).

This subsystem provides a high-performance, interactive corpus linguistics analytics workstation. It operationalizes the 14 chapters of [`Corpus_Analysis_tr.ipynb`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/Corpus_Analysis_tr.ipynb) and the 31 production modules of [`corpus_toolkit/`](file:///home/ben/Documents/thesis/scripts/corpus_analysis/corpus_toolkit/).

### Core Invariants Every Developer Must Know
1. **Zero New Package Installations**: The application runs exclusively within the pre-configured Anaconda `base` environment (`conda run -n base python`). Installing third-party packages with `pip` or `conda` is strictly prohibited.
2. **Strict $\le 200$ Line-Count Limit**: No file (`.py`, `.js`, `.css`, `.html`) may exceed 200 physical lines. All code must target $\le 180$ lines pre-formatting to provide an operational safety margin.
3. **Four-Layer MVC Architecture**:
   - `Controllers`: Flask Blueprints handling HTTP routing, query parsing, and JSON response encoding. Zero business logic or file I/O.
   - `Services`: Pure computational and analytical orchestration. Zero file system I/O.
   - `Repositories`: Exclusive interface for file system access, YAML configurations, Parquet cache, and unpickling.
   - `Models`: Typed dataclasses and schemas. Zero dependencies on higher layers.
4. **Standalone Git Repository**: The repository is located at `scripts/corpus_analysis/` on branch `master`. Always verify repository status before and after modifications.

---

## 2. Development Environment Setup

### 2.1 Activating the Anaconda Base Environment
All development, testing, and server execution occurs under Anaconda `base`:

```bash
# Verify Conda base environment
conda activate base

# Confirm Python version (Python 3.11.x)
python --version

# Verify core dependencies are available
python -c "import flask, pandas, pyarrow, scipy, sklearn, networkx, selenium; print('Environment OK')"
```

### 2.2 Working Directory Verification
Commands must be run from `scripts/corpus_analysis/`:

```bash
cd /home/ben/Documents/thesis/scripts/corpus_analysis
git status
```

---

## 3. Directory Layout and File Responsibilities

The codebase follows a modular structure where each functional responsibility is isolated into small, testable units:

```
scripts/corpus_analysis/SPA/
├── run_spa.py                    # Local application entrypoint (binds 127.0.0.1:5000)
├── config/
│   ├── spa_paths.yaml            # Configurable file system paths (Parquet, cache, images)
│   └── corpus_metadata.yaml      # Configurable book/author metadata and portrait paths
├── controllers/                  # Flask Blueprints (HTTP parsing & status codes)
│   ├── config_controller.py      # /api/v1/config/* and /api/v1/help/*
│   ├── corpus_controller.py      # /api/v1/corpus/* (inventory, scopes, memory)
│   ├── alignment_controller.py   # /api/v1/alignment/* (cardinality, delta, NDA)
│   ├── syntax_controller.py      # /api/v1/syntax/* (POS profiler, displaCy trees)
│   ├── concordance_controller.py # /api/v1/concordance/* (search, 5-view KWIC, batch)
│   ├── lexicon_controller.py     # /api/v1/lexicon/* (diversity, collocation, TF-IDF)
│   └── export_controller.py      # /api/v1/export/* (atomic reports, bundle ZIP)
├── services/                     # Business logic (Pure functions, zero file I/O)
│   ├── config_metadata_service.py# Path validation and metadata resolution
│   ├── inventory_memory_service.py# TokenView generation and memory monitoring
│   ├── alignment_delta_service.py# Alignment cardinality and sentence/word deltas
│   ├── nda_parallel_service.py   # Overlay formatting and SVG link coordinates
│   ├── pos_service.py            # UPOS distributions, delta-pp, bootstrap CIs
│   ├── depviz_service.py         # CoNLL parsing, manual displaCy SVG arc layouts
│   ├── search_kwic_service.py    # Search node resolution, 5-view KWIC builders
│   ├── batch_dispersion_service.py# 10-chunk Juilland's D, BH-FDR correlations
│   ├── diversity_service.py      # 22 LancsBox-X metrics and MATTR sliding window
│   ├── collocation_service.py    # Union-slot contingency and 6 association scores
│   ├── tfidf_service.py          # Sublinear TF-IDF and keyness ranking
│   └── reporter_bundle_service.py# Structured research bundle packaging
├── repositories/                 # File I/O and cache management
│   ├── config_repository.py      # spa_paths.yaml and corpus_metadata.yaml reader/writer
│   ├── corpus_repository.py      # CorpusLoader interface and Parquet cache
│   ├── nda_cache_repository.py   # _NdaSafeUnpickler and NdaOverlay interface
│   └── export_repository.py      # File export and ZIP archive creation
├── models/                       # Dataclasses and typing protocols
│   ├── config_models.py          # PathConfig and CorpusMetadata schemas
│   ├── corpus_models.py          # TextRecord and InventoryItem schemas
│   └── analysis_models.py        # TokenViewParams and MetricResult schemas
├── views/                        # Frontend UI assets
│   ├── index.html                # Master HTML shell and layout
│   ├── partials/                 # HTML partials for Tabs 1–11, modals, and drawer
│   ├── static/
│   │   ├── css/                  # Scoped stylesheets (<= 200 lines per file)
│   │   └── js/                   # Vanilla ES6 modules (<= 200 lines per file)
│   │       ├── app_state.js      # Global state container and event bus
│   │       ├── api_client.js     # Fetch abstraction with error handling
│   │       ├── table_grid.js     # 20-row paginated, resizable DataGrid
│   │       └── tabs/             # Tab controllers (tab_01.js to tab_11.js)
└── tests/                        # Automated test suite (Unit, Benchmark, AST, E2E)
```

---

## 4. Line-Budget Rules and Automated AST Validation

### 4.1 The $\le 200$ Line Invariant
Every file in the repository must not exceed 200 physical lines. This rule prevents architectural decay, simplifies code review, and enables rapid refactoring.

- **Target Pre-Format Budget**: 160–180 lines.
- **Hard Upper Bound**: 200 lines.
- **Refactoring Strategy**: When a service or controller approaches 180 lines, extract helper routines into dedicated utility modules (e.g., `pos_bootstrap_helper.py`, `kwic_sort_helper.py`).

### 4.2 Running AST Hygiene Tests
Before committing changes, execute the AST line-budget validation test:

```bash
# Run line-count and AST import boundary validation
pytest SPA/tests/ast_hygiene/test_file_line_counts.py -v
pytest SPA/tests/ast_hygiene/test_layer_dependencies.py -v
```

---

## 5. Debugging and Observability

### 5.1 Starting the Development Server
Launch the application bound to localhost:

```bash
# Start SPA server in debug mode
python SPA/run_spa.py --debug --port 5000
```
Open `http://127.0.0.1:5000` in your web browser.

### 5.2 Server-Side Memory Inspection
The application monitors memory usage using Linux `/proc/self/statm`. You can inspect the live memory status via the REST API:

```bash
curl -s http://127.0.0.1:5000/api/v1/corpus/memory | jq .
```
Expected output:
```json
{
  "rss_mb": 412.5,
  "rss_peak_mb": 680.2,
  "ceiling_mb": 1500.0,
  "status": "healthy"
}
```

### 5.3 Browser Console and Content Security Policy (CSP)
The application operates under a strict Content Security Policy. Inline scripts and eval expressions are blocked. Use the browser developer tools (F12) to monitor:
- Network requests to `/api/v1/*`.
- Console errors or CSP violation reports.
- Memory usage and layout metrics.

---

## 6. Step-by-Step Tutorial: Adding a New SPA Tab

This tutorial demonstrates how to add a new tab: **Tab 12: Morphological Suffix & Inflection Inspector**.

### Step 1: Define Schemas in Models Layer
Create `SPA/models/morphology_models.py` ($\le 180$ lines):

```python
from dataclasses import dataclass
from typing import List, Dict

@dataclass(frozen=True)
class SuffixFrequency:
    suffix: str
    count: int
    percentage: float

@dataclass(frozen=True)
class MorphologyInspectionResult:
    text_code: str
    total_words: int
    top_suffixes: List[SuffixFrequency]
```

### Step 2: Implement Logic in Service Layer
Create `SPA/services/morphology_service.py` ($\le 180$ lines, zero file I/O):

```python
from typing import List
from collections import Counter
from SPA.models.morphology_models import SuffixFrequency, MorphologyInspectionResult

class MorphologyService:
    @staticmethod
    def inspect_suffixes(tokens: List[str], text_code: str, top_k: int = 20) -> MorphologyInspectionResult:
        suffixes = [t.split("'")[-1] for t in tokens if "'" in t and len(t.split("'")[-1]) > 0]
        total = len(tokens)
        counts = Counter(suffixes).most_common(top_k)
        
        freqs = [
            SuffixFrequency(suffix=s, count=c, percentage=round(100.0 * c / max(1, total), 3))
            for s, c in counts
        ]
        return MorphologyInspectionResult(text_code=text_code, total_words=total, top_suffixes=freqs)
```

### Step 3: Implement HTTP Endpoint in Controller Layer
Create `SPA/controllers/morphology_controller.py` ($\le 180$ lines):

```python
from flask import Blueprint, jsonify, request
from SPA.services.morphology_service import MorphologyService
from SPA.repositories.corpus_repository import CorpusRepository

morphology_bp = Blueprint("morphology", __name__, url_prefix="/api/v1/morphology")

@morphology_bp.route("/inspect", methods=["GET"])
def inspect_suffixes():
    text_code = request.args.get("text_code", "BR-SM")
    text = CorpusRepository.get_text(text_code)
    tokens = list(text.tokens)
    result = MorphologyService.inspect_suffixes(tokens, text_code=text_code)
    return jsonify({
        "text_code": result.text_code,
        "total_words": result.total_words,
        "top_suffixes": [{"suffix": s.suffix, "count": s.count, "percentage": s.percentage}
                         for s in result.top_suffixes]
    }), 200
```
Register the blueprint in `SPA/run_spa.py`.

### Step 4: Author UI Partial and CSS
Create `SPA/views/partials/tab_12_morphology.html` ($\le 180$ lines):

```html
<section id="tab-12-panel" class="tab-panel" hidden>
  <div class="panel-header">
    <h2>Tab 12: Morphological Suffix & Inflection Inspector</h2>
    <span class="badge">Experimental</span>
  </div>
  <div class="panel-toolbar">
    <label for="morph-text-select">Select Text:</label>
    <select id="morph-text-select" class="form-select"></select>
    <button id="morph-run-btn" class="btn btn-primary">Inspect Suffixes</button>
  </div>
  <div id="morph-grid-container" class="grid-container"></div>
</section>
```

### Step 5: Implement Frontend JavaScript Controller
Create `SPA/views/static/js/tabs/tab_12_morphology.js` ($\le 180$ lines):

```javascript
import { ApiClient } from '../api_client.js';
import { TableGrid } from '../table_grid.js';
import { AppState } from '../app_state.js';

export class Tab12Morphology {
  constructor() {
    this.container = document.getElementById('morph-grid-container');
    this.select = document.getElementById('morph-text-select');
    this.runBtn = document.getElementById('morph-run-btn');
    this.grid = null;
  }

  init() {
    this.runBtn.addEventListener('click', () => this.loadData());
  }

  async loadData() {
    const textCode = this.select.value || AppState.activeTextCode;
    const response = await ApiClient.get(`/api/v1/morphology/inspect?text_code=${textCode}`);
    if (response.ok) {
      const data = await response.json();
      this.renderGrid(data.top_suffixes);
    }
  }

  renderGrid(rows) {
    if (!this.grid) {
      this.grid = new TableGrid(this.container, [
        { field: 'suffix', label: 'Suffix Morpheme', sortable: true },
        { field: 'count', label: 'Raw Frequency', sortable: true },
        { field: 'percentage', label: 'Token Share (%)', sortable: true }
      ]);
    }
    this.grid.setData(rows);
  }
}
```

### Step 6: Add Unit and E2E Tests
1. **Unit Test**: In `SPA/tests/unit/test_morphology_service.py`, assert that suffix percentages sum accurately and empty token lists return empty collections.
2. **E2E Test**: In `SPA/tests/e2e/test_e2e_tab12_morphology.py`, use Selenium to select a book, click `Inspect Suffixes`, and assert that the DataGrid populates rows.
3. **AST Line Gate**: Run `pytest SPA/tests/ast_hygiene/` to verify all new files adhere to the $\le 200$ line-count limit.

---

## 7. Acceptance Gate Checklist

- [x] Environment invariant documented: Anaconda `base` required, zero new package installations permitted.
- [x] Repository layout documented covering Controllers, Services, Repositories, Models, Views, Config, and Tests.
- [x] Line-budget policy detailed: target $\le 180$ lines, hard limit $\le 200$ lines for all file types.
- [x] AST automated line-budget and dependency-direction validation commands documented.
- [x] Debugging workflows documented (local server execution, live RSS memory inspection, browser console checks).
- [x] Step-by-step tutorial provided for adding a new tab across all four architectural layers.
- [x] Testing requirements documented for new components (Unit, AST hygiene, and E2E Selenium tests).
