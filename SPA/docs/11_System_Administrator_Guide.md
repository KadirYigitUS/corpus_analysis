# 11 · System Administrator and Deployment Guide

## 1. System Overview and Host Binding Policy

This guide details the deployment, configuration management, resource monitoring, and security administration for the **Corpus Analysis Single-Page Application (SPA)** (`scripts/corpus_analysis/SPA/`).

### 1.1 Local Host Binding Invariant (`127.0.0.1`)
The application is designed for local workstation use and trusted intranet environments.
- **Default Binding**: The application must bind strictly to the loopback interface: `127.0.0.1:5000`.
- **Public Exposure Prohibition**: Binding directly to `0.0.0.0` or public network interfaces without an authenticating reverse proxy (e.g., NGINX with TLS and HTTP Basic/OAuth authentication) is strictly prohibited.
- **Port Selection**: Default port is `5000`. If port 5000 is occupied, configure an alternative port via `--port <PORT>` or the `SPA_PORT` environment variable.

---

## 2. Configuration Management

Configuration is decoupled into two primary YAML registries residing in `SPA/config/`:

```
scripts/corpus_analysis/SPA/config/
├── spa_paths.yaml            # File system paths, cache directories, and export targets
└── corpus_metadata.yaml      # Bibliographic metadata, author attributions, and asset links
```

### 2.1 `spa_paths.yaml` Schema and Path Resolution
All relative paths defined in `spa_paths.yaml` resolve relative to the repository root directory (`scripts/corpus_analysis/`):

```yaml
version: "1.0"
storage:
  parquet_cache_dir: "data/corpus_analysis/.cache/"
  schema_version: "v3-2026-04-20"
  max_cache_size_mb: 2048
  nda_cache_file: "data/alignment/scored_alignment_rows.pickle"
  dictionary_cache_file: "data/alignment/initial_dictionary.pickle"
assets:
  book_covers_dir: "SPA/views/static/images/book_covers/"
  author_portraits_dir: "SPA/views/static/images/author_portraits/"
export:
  reports_output_dir: "output/corpus_reports/"
  bundle_temp_dir: "output/.temp_bundles/"
```

### 2.2 `corpus_metadata.yaml` Schema
Maintains bibliographic details and mapping to image assets:

```yaml
texts:
  BR-SM:
    title: "Ben, Robot"
    author: "Isaac Asimov"
    translator: "Reha Pınar"
    year: 1988
    language: "tr"
    type: "translation"
    pair_code: "IR-IA_BR-SM"
    cover_image: "book_covers/br_sm_cover.jpg"
    author_portrait: "author_portraits/asimov.jpg"
    translator_portrait: "author_portraits/reha_pinar.jpg"
```

### 2.3 Live Configuration Reloading
The application supports hot-reloading of configuration files via administrative REST endpoints:
- `POST /api/v1/config/reload`: Flushes in-memory configuration cache and re-parses YAML files.
- `PUT /api/v1/config/paths`: Updates path settings with schema validation before writing to disk.
- `PUT /api/v1/config/metadata`: Updates bibliographic records with atomic file writes.

---

## 3. Cache Management and Storage Budgets

The application uses content-addressed Parquet files for caching processed token tables and dependency trees.

### 3.1 LRU Cache Budget ($2{,}048\text{ MB}$)
- **Disk Budget**: Maximum disk footprint allocated for the Parquet cache is $2{,}048\text{ MB}$ ($2\text{ GB}$).
- **Key Hashing**: Cache keys are generated deterministically using SHA-256:
  $$\text{Key} = \text{SHA256}(\text{SCHEMA\_VERSION} + \text{namespace} + \text{canonical\_args})[:20]$$
- **Eviction Strategy**: When total cache size exceeds $2{,}048\text{ MB}$, the cache manager initiates Least Recently Used (LRU) pruning, removing oldest `.parquet` files until total storage falls below $1{,}800\text{ MB}$ (10% safety margin).

### 3.2 Cache Retention Policies
Controlled via the `CORPUS_CACHE_POLICY` environment variable:
- `keep` (Default): Retains cache files across server restarts. Pruning occurs only when the 2 GB threshold is exceeded.
- `clear`: Flushes all cached Parquet files on server initialization.
- `ask`: Prompts the administrator in interactive terminal mode before clearing stale cache blocks.

---

## 4. Memory Monitoring and Resource Ceilings ($< 1{,}500\text{ MB}$ RSS)

### 4.1 Process RSS Telemetry
The application monitors its resident memory usage using Linux `/proc/self/statm`.
- **Warning Threshold**: $1{,}000\text{ MB}$.
- **Eviction Action Threshold**: $1{,}350\text{ MB}$.
- **Hard Process Ceiling**: $1{,}500\text{ MB}$.

### 4.2 Automated Eviction Hooks
1. **Streaming Processing**: Batch operations across the 13 books utilize `loader.iter_evicting()`, loading one novel into memory at a time and evicting it immediately after computing metrics.
2. **Explicit Garbage Collection**: Endpoints handling heavy calculations (`/api/v1/lexicon/diversity`, `/api/v1/syntax/pos`) invoke `gc.collect()` following DataFrame transformations.
3. **Manual Eviction Endpoint**:
   ```bash
   curl -X POST http://127.0.0.1:5000/api/v1/corpus/evict -H "Content-Type: application/json" -d '{"scope": "all"}'
   ```

---

## 5. Security Hardening and Isolation

```
+-------------------------------------------------------------------------------+
| Client Browser                                                                |
|   |  Content Security Policy (script-src 'self', frame-ancestors 'none')      |
|   v                                                                           |
| Flask HTTP Controller (127.0.0.1)                                             |
|   |  Input Sanitization (ReDoS regex timeout, filename verification)          |
|   v                                                                           |
| Deserialization Sandbox (_NdaSafeUnpickler: Whitelist only)                   |
|   |  Blocks os.system, subprocess, eval, arbitrary class instantiation        |
|   v                                                                           |
| File System Storage (Parquet, YAML, Image Assets confined to SPA directories)  |
+-------------------------------------------------------------------------------+
```

### 5.1 Content Security Policy (CSP) Headers
The application injects the following security headers on all HTTP responses:

```http
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
```
- **No `unsafe-eval`**: JavaScript `eval()` and Function constructor are forbidden.
- **No External CDNs**: All scripts, stylesheets, and fonts must be served locally from `/static/`.

### 5.2 Deserialization Isolation (`_NdaSafeUnpickler`)
To prevent Remote Code Execution (RCE) via pickled NDA alignment overlays:
- All deserialization operations bypass the standard `pickle.Unpickler`.
- Ingestion routes use `_NdaSafeUnpickler`, which enforces an explicit class whitelist:
  - Allowed: `builtins.int`, `builtins.float`, `builtins.str`, `builtins.bool`, `builtins.list`, `builtins.tuple`, `builtins.dict`, `builtins.set`.
  - Blocked: Any module or class outside the whitelist raises `pickle.UnpicklingError` immediately.

### 5.3 Regular Expression Denial of Service (ReDoS) Defense
User queries submitted to `/api/v1/concordance/search` undergo validation:
- **Maximum Pattern Length**: Capped at 256 characters.
- **Execution Timeout**: Regex matching processes run with a 500 ms CPU timeout guard.
- **Static Pattern Inspection**: Rejects nested repetition patterns (e.g., `(a+)+`, `(x|y+)+`) that trigger polynomial or exponential backtracking.

### 5.4 File Upload Hardening
Asset uploads via `/api/v1/config/upload-image` are restricted:
- **Allowed MIME Types**: `image/jpeg`, `image/png`, `image/webp`.
- **Maximum File Size**: $5\text{ MB}$.
- **Filename Sanitization**: Sanitized using `werkzeug.utils.secure_filename` to prevent path traversal (`../`).
- **Directory Confinement**: Files are written strictly inside `SPA/views/static/images/`.

---

## 6. Service Management and Runbooks

### 6.1 Running as a Systemd Service (Linux Workstation)
To run the SPA persistently on a local Linux workstation, create `/etc/systemd/system/corpus-analysis-spa.service`:

```ini
[Unit]
Description=Corpus Analysis SPA Analytics Service
After=network.target

[Service]
Type=simple
User=ben
WorkingDirectory=/home/ben/Documents/thesis/scripts/corpus_analysis
Environment="PATH=/home/ben/anaconda3/bin:/usr/local/bin:/usr/bin"
Environment="CORPUS_CACHE_POLICY=keep"
ExecStart=/home/ben/anaconda3/bin/python SPA/run_spa.py --port 5000
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable corpus-analysis-spa.service
sudo systemctl start corpus-analysis-spa.service
sudo systemctl status corpus-analysis-spa.service
```

### 6.2 Healthcheck and Troubleshooting Runbook

#### Health Check
```bash
curl -f -s http://127.0.0.1:5000/api/v1/health | jq .
```
Expected response:
```json
{
  "status": "UP",
  "version": "1.0.0",
  "memory": {
    "rss_mb": 420.1,
    "ceiling_mb": 1500.0
  },
  "cache": {
    "size_mb": 340.5,
    "limit_mb": 2048
  }
}
```

#### Incident: High Memory Consumption (RSS $> 1{,}350\text{ MB}$)
1. Issue manual eviction command:
   ```bash
   curl -X POST http://127.0.0.1:5000/api/v1/corpus/evict -H "Content-Type: application/json" -d '{"scope": "all"}'
   ```
2. Verify RSS drops below $500\text{ MB}$.
3. If memory does not decrease, restart the application service:
   ```bash
   sudo systemctl restart corpus-analysis-spa.service
   ```

#### Incident: Disk Cache Full ($> 2{,}048\text{ MB}$)
1. Inspect current cache directory:
   ```bash
   du -sh data/corpus_analysis/.cache/
   ```
2. Manually trigger cache cleanup:
   ```bash
   python -c "from corpus_toolkit.cache import CorpusCacheManager; CorpusCacheManager().prune_lru(target_mb=1500)"
   ```

---

## 7. Acceptance Gate Checklist

- [x] Host binding strictly restricted to loopback (`127.0.0.1`).
- [x] Configuration management defined for `spa_paths.yaml` and `corpus_metadata.yaml` with hot-reloading endpoints.
- [x] Parquet disk cache budget ($2{,}048\text{ MB}$) and SHA-256 LRU eviction policy documented.
- [x] Memory monitoring (< 1.5 GB RSS) specified with Linux `/proc/self/statm` telemetry and eviction hooks.
- [x] Content Security Policy (CSP) documented with `unsafe-eval` prohibition and local asset restrictions.
- [x] Deserialization isolation documented with `_NdaSafeUnpickler` whitelist enforcement.
- [x] ReDoS defenses (length caps, timeout guards, nested repetition blocking) established.
- [x] Image upload security controls (MIME validation, size cap, directory confinement) documented.
- [x] Systemd service configuration and troubleshooting runbooks detailed.
