# 06 · REST API & Interface Specifications

## 1. Executive Summary & API Principles

This specification establishes the formal interface contract for the **Corpus Analysis Single-Page Application (SPA)** REST API (`/api/v1/`).

The interface design adheres to the following principles:
1. **Strict Versioning**: All endpoints reside under the immutable namespace `/api/v1/`. Breaking schema changes require an incremented version path (`/api/v2/`).
2. **Stateless Request Execution**: The backend maintains no server-side HTTP session state. All filter criteria, pagination offsets, sorting directions, and view parameters must be passed explicitly in query parameters or JSON request bodies.
3. **Deterministic Response Envelopes**: All endpoints return uniform JSON envelopes containing `status`, `data`, and optional `meta` or `errors` fields.
4. **Data Transfer Object (DTO) Validation**: Every request is validated against strict typed DTO definitions before reaching the service layer. Invalid requests fail fast with HTTP `422 Unprocessable Entity` and structured validation details.
5. **Standardized HTTP Semantics**: Correct usage of HTTP methods (`GET` for idempotent retrieval, `POST` for search and batch calculations, `PUT` for complete resource updates, `DELETE` for cache eviction) and status codes.

---

## 2. Global Conventions, Envelopes & Status Codes

### 2.1 Uniform Response Envelopes

#### Success Envelope (`200 OK`, `201 Created`)
```json
{
  "status": "success",
  "data": { ... },
  "meta": {
    "timestamp": "2026-10-21T11:00:00Z",
    "execution_ms": 42.8,
    "page": 1,
    "per_page": 20,
    "total_records": 1420,
    "total_pages": 71
  }
}
```

#### Error Envelope (`400`, `404`, `422`, `500`)
```json
{
  "status": "error",
  "code": "VALIDATION_FAILED",
  "message": "The request payload failed schema validation.",
  "errors": [
    {
      "field": "punct",
      "rejected_value": "invalid_mode",
      "expected": "One of ['drop', 'keep', 'strip', 'split']"
    }
  ]
}
```

### 2.2 Standard HTTP Status Codes

| Code | Status Phrase | Usage in Corpus Analysis SPA |
|---|---|---|
| `200` | `OK` | Request succeeded. Body contains requested data entity or calculation result. |
| `201` | `Created` | Asset or report successfully created (e.g., image upload or report finalized). |
| `400` | `Bad Request` | Malformed JSON syntax or missing required path/query parameters. |
| `404` | `Not Found` | Requested text code, alignment pair, or asset path does not exist. |
| `422` | `Unprocessable Entity` | Valid JSON syntax but semantic or validation constraints failed (e.g., invalid span, ReDoS regex pattern detected, window size $< 1$). |
| `500` | `Internal Server Error` | Unexpected backend or engine failure. Includes sanitized error code. |

---

## 3. Data Transfer Objects (DTO) Schema Definitions

### 3.1 `PathConfigDTO`
```json
{
  "paths": {
    "corpus_root": "data/corpus_analysis/",
    "cache_dir": "data/corpus_analysis/.cache/",
    "nda_cache_dir": "data/cache_alignment/",
    "export_dir": "output/reports/",
    "book_images_dir": "SPA/static/assets/img/books/",
    "author_images_dir": "SPA/static/assets/img/authors/"
  }
}
```

### 3.2 `BookMetadataDTO` & `AuthorMetadataDTO`
```json
{
  "text_code": "BR-SM",
  "title_tr": "Ben, Robot",
  "title_orig": "I, Robot",
  "author": {
    "name": "Isaac Asimov",
    "birth_death": "1920–1992",
    "nationality": "American",
    "portrait_image": "authors/asimov.webp"
  },
  "translator": {
    "name": "Gönül Suveren",
    "birth_death": "1932–2018",
    "portrait_image": "authors/suveren.webp"
  },
  "publication_year_orig": 1950,
  "publication_year_tr": 1982,
  "publisher_tr": "Okat Yayınevi",
  "cover_image": "books/br_sm_cover.webp",
  "is_aligned": true,
  "aligned_pair_code": "IR-IA_BR-SM"
}
```

### 3.3 `CorpusScopeDTO`, `TokenViewParamsDTO` & `parse_scope_and_view`
```json
{
  "scope": {
    "scope": "author_related",
    "author_filter": "SM",
    "text_code": null,
    "pair_code": "IR-IA_BR-SM"
  },
  "view_params": {
    "field": "lem",
    "filter_function_words": false,
    "mode": "drop",
    "punct": "strip"
  }
}
```
*Validation & Propagation Rules (`parse_scope_and_view(args, body)`)*:
- `scope.scope`: One of `["all", "all_en", "all_tr", "trans_en", "trans_tr", "indig_tr", "author_related", "author_turkish", "pairs", "single"]` (also accepts `category` query alias).
- `scope.author_filter`: Optional focal/corpus author code (`SM, ZB, OK, NCK, AS, CE, SG`); required when `scope` is `author_related` or `author_turkish`.
- `scope.text_code`: Required when `scope == "single"`.
- `field`: Must be `"tok"` or `"lem"`.
- `filter_function_words`: Boolean (`true`/`false`/`1`/`0`).
- `mode`: Must be `"drop"` or `"mask"`. Under `mode == "mask"`, bag-of-words metrics (`N, V, TTR, Guiraud_R, Yule_K, Simpson_D, MTLD, HD_D`) use `view.analysed()`, whereas positional window metrics (`MATTR_50/100/500`, `masked_mattr_series`, `CollocationAnalyzer`, `Concordancer`) preserve masked positions (`None` at `eligible == False`).
- `punct`: Must be one of `["drop", "keep", "strip", "split"]`.
- Every `GET` and `POST` analytical/visualization endpoint parses `(scope, view)` via `parse_scope_and_view(request.args, request.get_json(silent=True))` and keys `global_payload_cache` by `(scope.cache_key(), view.cache_key(), *endpoint_args)`.

### 3.4 `SearchQueryDTO`
```json
{
  "text_codes": ["BR-SM", "OBI-SM"],
  "terms": ["robot*"],
  "field": "lem",
  "match": "glob",
  "case_sensitive": false,
  "pos": "NOUN",
  "collocate": "insan",
  "collocate_span": [-3, 3],
  "filter_function_words": false,
  "mode": "drop",
  "punct": "drop",
  "timeout_seconds": 2.5
}
```
*Validation Rules*:
- `terms`: Non-empty array of strings. Maximum 20 terms per query.
- `match`: Must be `"exact"`, `"glob"`, or `"regex"`.
- If `match == "regex"`, pattern undergoes static ReDoS inspection (rejects nested unbounded repetitions `(x+)+`).
- `collocate_span`: Two-element array $[L, R]$ where $-20 \le L \le 0$ and $0 \le R \le 20$.

### 3.5 `CollocationParamsDTO`
```json
{
  "text_code": "BR-SM",
  "node_term": "robot",
  "left_span": 5,
  "right_span": 5,
  "min_freq": 3,
  "sort_by": "G2",
  "sentence_clamped": true,
  "field": "lem",
  "filter_function_words": true,
  "mode": "drop",
  "punct": "drop"
}
```
*Validation Rules*:
- `left_span`, `right_span`: Integers $0 \le \text{span} \le 20$, with $\text{left_span} + \text{right_span} \ge 1$.
- `sort_by`: One of `["MI", "MI2", "MI3", "T", "G2", "LogDice", "O11"]`.

---

## 4. Comprehensive Endpoint Specifications

### 4.1 Configuration & Metadata API

#### `GET /api/v1/config/paths`
- **Description**: Returns all currently active system filesystem directories.
- **Response**: `200 OK` with `PathConfigDTO`.

#### `PUT /api/v1/config/paths`
- **Description**: Updates user-configured filesystem paths in `SPA/config/spa_paths.yaml`.
- **Request Body**: `PathConfigDTO`.
- **Validation**: Verifies directory existence and write permissions on export directories.
- **Response**: `200 OK` or `422 Unprocessable Entity`.

#### `GET /api/v1/config/corpus-metadata`
- **Description**: Returns detailed bibliographic source tables, book covers, and author portraits for all 13 texts.
- **Query Params**:
  - `category` (optional): `translated_en`, `translated_tr`, `indigenous_tr`, `aligned_pairs`.
- **Response**: `200 OK` with list of `BookMetadataDTO`.

#### `POST /api/v1/config/upload-image`
- **Description**: Uploads a replacement or new book cover or author portrait image.
- **Content-Type**: `multipart/form-data`.
- **Form Fields**:
  - `image_type`: `"book"` or `"author"`.
  - `entity_code`: e.g. `"BR-SM"` or `"asimov"`.
  - `file`: Binary image data (`.webp`, `.jpg`, `.png`). Maximum file size $5\text{ MB}$.
- **Response**: `201 Created` with relative asset URL.

---

### 4.2 Corpus Management & Memory API

#### `GET /api/v1/corpus/inventory`
- **Description**: Retrieves the complete 13-novel corpus inventory table.
- **Query Params**:
  - `focal_code` (optional): Filter by author trio code (`SM`, `ZB`, `OK`).
  - `lang` (optional): `"en"` or `"tr"`.
- **Response**: `200 OK` with array of inventory items (author, title, genre, token count, sentence count).

#### `GET /api/v1/corpus/memory`
- **Description**: Retrieves real-time process memory footprint and lazy loader retention status.
- **Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "rss_mb": 412.5,
    "ceiling_mb": 1500.0,
    "utilization_pct": 27.5,
    "active_loaded_texts": ["BR-SM", "IR-IA"],
    "cached_files_count": 26,
    "cache_disk_mb": 84.2
  }
}
```

#### `POST /api/v1/corpus/cache/evict`
- **Description**: Evicts cached in-memory DataFrames or flushes on-disk Parquet caches.
- **Request Body**:
```json
{
  "target": "memory", // "memory" or "all"
  "policy": "clear"   // "clear", "keep", "lru"
}
```
- **Response**: `200 OK` with updated memory metrics.

---

### 4.3 Alignment & Parallel Corpora API

#### `GET /api/v1/alignment/pairs`
- **Description**: Lists all 5 available bilingual alignment translation pairs.
- **Response**: `200 OK` returning pair metadata (e.g. `IR-IA_BR-SM`, `TL-PA_A-ZB`).

#### `GET /api/v1/alignment/cardinality`
- **Description**: Retrieves alignment cardinality distributions ($1{:}1, 1{:}N, N{:}1, N{:}M$, omission, addition).
- **Query Params**:
  - `pair_code`: Required (e.g., `"IR-IA_BR-SM"`).
- **Response**: `200 OK` with counts, percentages, and length ratios ($R_{\text{sent}}, \text{ratio}_{\text{word}}, \text{ratio}_{\text{char}}$).

#### `GET /api/v1/alignment/length-deltas`
- **Description**: Retrieves paginated alignment rows sorted by sentence, word, or character count deltas.
- **Query Params**:
  - `pair_code`: Required.
  - `sort_by`: `"sent_delta"`, `"word_delta"`, `"char_delta"`.
  - `direction`: `"desc"` or `"asc"`.
  - `page`: Default `1`.
  - `per_page`: Default `20`.
- **Response**: `200 OK` with paginated rows containing English and Turkish text spans and NER entities.

#### `GET /api/v1/alignment/parallel`
- **Description**: Generates side-by-side bilingual parallel text with NDA overlay highlights and stepped SVG connectors.
- **Query Params**:
  - `pair_code`: Required.
  - `start_row`: Integer start index.
  - `end_row`: Integer end index (maximum range 50 rows per request).
  - `overlay`: Boolean (default `true`).
  - `hit_lemmas`: Optional comma-separated list of search terms to highlight.
- **Response**: `200 OK` with parallel row representations, token span tags, and connector link vectors.

---

### 4.4 Morphosyntax & Dependency API

#### `POST /api/v1/syntax/pos-profile`
- **Description**: Calculates 17-tag UPOS profile distributions, lexical density, and noun/verb ratios.
- **Request Body**:
```json
{
  "text_codes": ["BR-SM", "IR-IA", "OBI-SM"],
  "content_only": false
}
```
- **Response**: `200 OK` with raw counts, percentage matrices, and deverbal share metrics for Turkish texts.

#### `POST /api/v1/syntax/pos-comparison`
- **Description**: Computes comparative divergence ($\Delta\text{pp}$), percentile bootstrap 95% confidence intervals, and pooled $\chi^2$ / Cramér's $V$ statistics.
- **Request Body**:
```json
{
  "group_a": ["IR-IA", "TL-PA"],
  "group_b": ["BR-SM", "A-ZB"],
  "n_bootstrap": 2000,
  "seed": 13
}
```
- **Response**: `200 OK` with delta percentages, bootstrap upper/lower bounds, and significance values.

#### `GET /api/v1/syntax/displacy-tree`
- **Description**: Generates an offline Universal Dependencies SVG dependency tree for a specific sentence.
- **Query Params**:
  - `text_code`: Required.
  - `sentence_id`: Coordinates `ch:p:s` or sequential sentence index.
  - `dim_function_words`: Boolean (default `true`).
- **Response**: `200 OK` returning `{ "svg": "<svg ...>...</svg>", "tokens_table": [...] }`.

---

### 4.5 Concordance & Dispersion API

#### `POST /api/v1/concordance/search`
- **Description**: Executes node search across selected texts with full 32-combo `TokenView` support.
- **Request Body**: `SearchQueryDTO`.
- **Response**: `200 OK` with hit count, normalized `per10k` rate, and coordinate locations.

#### `POST /api/v1/concordance/kwic`
- **Description**: Formats search results into one of the 5 canonical KWIC views.
- **Request Body**:
```json
{
  "search_id": "optional_prior_query_hash",
  "query": { ... }, // SearchQueryDTO
  "view_mode": "kwic", // "kwic", "coords", "bilingual", "parallel", "table"
  "span": [-5, 5],
  "sentence_clamped": true,
  "sort_keys": ["R1", "L1"],
  "page": 1,
  "per_page": 20
}
```
- **Response**: `200 OK` returning paginated KWIC lines with left context, node token, and right context.

#### `POST /api/v1/concordance/batch-dispersion`
- **Description**: Computes within-text and across-text Juilland's $D$, 10-chunk rates, and Benjamini-Hochberg FDR corrected correlation matrices.
- **Request Body**:
```json
{
  "text_codes": ["BR-SM", "A-ZB", "YG-ZB"],
  "terms": ["robot", "uzay", "dünya", "gemi"],
  "field": "lem",
  "punct": "drop"
}
```
- **Response**: `200 OK` with chunk rate matrices, Juilland $D$ scores, Pearson/Spearman correlation coefficients, and $q$-value significance matrices.

---

### 4.6 Lexical Diversity & Collocation API

#### `POST /api/v1/lexicon/diversity`
- **Description**: Generates the complete 22-column LancsBox-X lexical diversity table across texts.
- **Request Body**:
```json
{
  "text_codes": ["BR-SM", "IR-IA", "OBI-SM"],
  "view_params": {
    "field": "lem",
    "filter_function_words": false,
    "mode": "drop",
    "punct": "drop"
  },
  "mattr_windows": [50, 100, 500],
  "sttr_block": 1000,
  "mtld_threshold": 0.72,
  "hdd_sample": 42
}
```
- **Response**: `200 OK` with all 22 metrics ($N, V, \text{TTR}, \text{Guiraud}, \text{CTTR}, \text{Herdan}, \text{Dugast}, \text{Maas}, \text{Yule } K, \text{Simpson}, \text{Honoré}, \text{Hapax } \%, \text{STTR}, \text{MATTR}_{50/100/500}, \text{MTLD}, \text{HD-D}, \text{Sichel}, \text{Michéa}$) including exact $\text{NaN}$ and warning flags.

#### `POST /api/v1/lexicon/collocations`
- **Description**: Computes Union-Slot $2\times 2$ contingency association metrics for a target node word.
- **Request Body**: `CollocationParamsDTO`.
- **Response**: `200 OK` with association table containing $O_{11}, R_1, C_1, E_{11}, \text{MI}, \text{MI}^2, \text{MI}^3, T, \text{signed } G^2, \text{Log-Dice}$ and GraphColl scatter coordinates.

---

### 4.7 TF-IDF & Research Reporting API

#### `POST /api/v1/export/tfidf`
- **Description**: Computes sublinear TF + smooth IDF + L2 normalized keyness rankings.
- **Request Body**:
```json
{
  "text_codes": ["BR-SM", "OBI-SM", "KS-ZB"],
  "top_k": 20,
  "exclude_pos": ["PROPN"],
  "n_chunks": 5
}
```
- **Response**: `200 OK` with ranked keyword tables and chunked pseudo-document distributions.

#### `POST /api/v1/export/generate-bundle`
- **Description**: Compiles an atomic reproducible research bundle (.md manuscript, .tsv tables, .png 300 DPI figures, multi-sheet .xlsx workbook).
- **Request Body**:
```json
{
  "report_title": "Comparative Repertoire Analysis SM-ZB-OK",
  "include_tabs": [1, 4, 8, 9, 10],
  "dpi": 300
}
```
- **Response**: `200 OK` with manifest summary and download token.

#### `GET /api/v1/export/download/<download_token>`
- **Description**: Streams the generated `.zip` research archive to the client.
- **Response**: Binary stream with header `Content-Disposition: attachment; filename="corpus_report_<timestamp>.zip"`.

---

### 4.8 Help & Mathematical Formulas API

#### `GET /api/v1/help/formulas`
- **Description**: Returns operational guides, exact LaTeX mathematical formulas, and `NaN` boundary rules for all analytical tools.
- **Response**: `200 OK` containing categorized formula objects:
```json
{
  "status": "success",
  "data": {
    "lexical_diversity": [
      {
        "id": "mattr",
        "name": "Moving-Average Type-Token Ratio (MATTR)",
        "formula_latex": "\\text{MATTR}_w = \\frac{1}{N - w + 1} \\sum_{i=1}^{N - w + 1} \\frac{V_i}{w}",
        "nan_rule": "If N < w, falls back to raw TTR with warning flag.",
        "primary_source": "Covington, M. A., & McFall, J. D. (2010). Cutting the Gordian knot of length-dependent diversity. J. Quant. Linguist., 17(2), 94-100."
      }
    ],
    "collocations": [
      {
        "id": "log_dice",
        "name": "Log-Dice Association Score",
        "formula_latex": "\\text{Log-Dice} = 14 + \\log_2 \\left(\\frac{2 O_{11}}{f_{\\text{node}} + C_1}\\right)",
        "nan_rule": "NaN if O11 = 0. Theoretical maximum is 14.0.",
        "primary_source": "Rychlý, P. (2008). A lexicographer-friendly association score. RASLAN 2008, 6-9."
      }
    ]
  }
}
```

---

## 5. Acceptance Gate Checklist

- [ ] Versioned `/api/v1/` prefix enforced across all endpoints.
- [ ] Complete DTO schemas specified with JSON request/response bodies and validation constraints.
- [ ] Standard HTTP status codes (`200, 201, 400, 404, 422, 500`) mapped to structured JSON error envelopes.
- [ ] Full coverage of all 11 SPA tab workstations and global drawers documented.
- [ ] Static ReDoS pattern detection constraint formalized for regex search endpoints.
- [ ] Union-Slot collocation contingency parameters ($O_{11}, R_1, C_1, E_{11}$) documented.
- [ ] User-configurable path and metadata management endpoints documented.
- [ ] Help/Formula drawer operational documentation endpoint formalized.
