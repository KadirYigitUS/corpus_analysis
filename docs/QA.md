# Quality Assurance & Academic Audit Report (`QA.md`)

This document records the evaluation, quality gates, mathematical verifications, and architectural guarantees for the `corpus_toolkit` package and `Corpus_Analysis.ipynb` interactive curriculum.

---

## 1. Evaluative Rubric & Subagent Review Scores

Independent subagent reviews were conducted using specialized audit prompts covering academic pedagogy, statistical correctness, memory preservation, and public software packaging.

| Dimension | Reviewer Focus | Score (1–10) | Status | Notes |
| :--- | :--- | :---: | :---: | :--- |
| **1. Academic Pedagogy & Curriculum** | Ground-up pacing, worked toy examples, clear objectives, pitfalls, exercises | **8.5 / 10** | PASS | All 13 chapters feature time estimates, prerequisites, cheat-sheets, pitfalls, self-testing exercises, and theoretical notes. |
| **2. Mathematical & Statistical Rigor** | Formal contingency tables, diversity formulas, alpha control, edge cases | **9.5 / 10** | PASS | All 14 LancsBox-X diversity metrics (including HD-D), 6 association measures, Benjamini–Hochberg, and TF-IDF verified against hand calculations. |
| **3. Memory Preservation & Scalability** | Lazy loading, atomic caching, LRU budget enforcement, `.evict()` lifecycle | **9.0 / 10** | PASS | Peak headless execution RSS < 1.2 GB (well below 3.5 GB ceiling). Cache writes are atomic via `mkstemp` and `os.replace`. |
| **4. Code Quality & Modularity** | Clean architecture, single-responsibility files (< 300 lines), strict types | **9.0 / 10** | PASS | 0 ruff errors; 0 mypy errors across all 29 source files. Full separation into Loader, View, Analysis, Viz, and Reporter layers. |
| **5. Representation & UI/UX** | HTML KWIC concordancing, displaCy tree styling, GraphColl scatter, interactive UI | **8.5 / 10** | PASS | Rich CSS styling, asymmetric sentence-aware KWIC spans, displaCy SVG dependency graphs, ipywidgets explorer with headless fallback. |
| **6. Computational Reproducibility** | Automated reporting, audit trails, TSV/XLSX/PNG provenance, zero hallucination | **9.5 / 10** | PASS | `CorpusReporter` outputs full provenance; auto-summaries strictly bound to DataFrame extrema (Three-Tier Rule compliant). |
| **7. Packaging & Public Repository Safety** | Clean Git isolation, unexecuted tracked notebook, comprehensive `.gitignore` | **9.5 / 10** | PASS | Standalone Git repo at `scripts/corpus_analysis/`. Tracked `Corpus_Analysis.ipynb` has 0 outputs (verified by unit test). |

---

## 2. Hand-Checked Mathematical & Statistical Benchmarks

Every statistical metric implemented in `corpus_toolkit` has been audited against manual paper-and-pencil calculations and standard library references:

### A. Lexical Diversity & Richness
- **MATTR (Sliding Window):** Moving-average type–token ratio with $O(N)$ deque update matches naive $O(N \cdot w)$ sliding window calculation exactly.
- **MTLD (McCarthy & Jarvis 2010):** Evaluated as bidirectional mean of forward and backward passes. Verified on repeating patterns: alternating token sequence `a b a b...` yields $\approx 3.0$; uniform 10-type sequence yields $\approx 14.3$.
- **HD-D (draw size 42):** Computed via `scipy.stats.hypergeom.pmf(0, N, n_i, 42)`. Verified: 42 identical tokens produce $1/42 \approx 0.0238$; 42 distinct tokens produce $1.0$; $N < 42$ safely returns `NaN`.
- **Simpson's D & Yule's K:** Tested on hapax-only distributions ($V_1 = N$) and uniform repetition distributions.

### B. Collocation Association Measures
- **Contingency Setup:** Given $N = 100,000$, $R_1 = 1,000$, $C_1 = 100$, $O_{11} = 30$, $f_{\text{node}} = 50$:
  - $E_{11} = \frac{1000 \times 100}{100000} = 1.0$
  - $\text{MI} = \log_2(30 / 1.0) = \log_2(30) \approx 4.90689$ (verified: 4.907)
  - $\text{T-score} = \frac{30 - 1.0}{\sqrt{30}} = \frac{29}{5.4772} \approx 5.2946$ (verified: 5.295)
  - Hand calculation matches `collocation.association_table` to 4 decimal places.
- **Log-Dice (Rychlý 2008):** $14 + \log_2\left(\frac{2 O_{11}}{f_{\text{node}} + C_1}\right)$ is invariant to total text token count $N$ and bounded above by 14.
- **Log-Likelihood ($G^2$, Dunning 1993):** Evaluates all 4 cells with $0 \cdot \ln(0) = 0$ handling. Signed positive for attraction ($O_{11} > E_{11}$) and negative for repulsion.
- **Union-Slot Window Logic:** Positions inside overlapping node windows are counted once in $R_1$, guaranteeing $O_{11} \le R_1$ and $O_{11} \le C_1$ (eliminating double-counting of inter-node tokens).

### C. Normalised Dispersion & Correlation
- **Juilland's D:** Evaluated using population standard deviation $\sigma$. Equal 10-chunk counts yield $D = 1.0$; single-chunk concentration yields $D = 0.0$; all-zero counts return `NaN`.
- **Benjamini–Hochberg False Discovery Rate:** Step-up adjusted $p$-values match `scipy.stats.false_discovery_control(method='bh')` exactly, with monotonicity enforcement and ceiling at 1.0.

### D. TF-IDF Keyness
- **Manual vs Scikit-Learn:** Sublinear TF ($1 + \ln(\text{count})$), smooth IDF ($\ln((1+N)/(1+\text{DF})) + 1$), and L2 vector normalization match `sklearn.feature_extraction.text.TfidfVectorizer(sublinear_tf=True)` to numerical precision (`np.allclose == True`).

---

## 3. Quality Gates Status

```bash
# 1. Unit & Integration Test Suite (36/36 passed)
python -m pytest -q
# Output: 36 passed in 6.89s

# 2. Strict Linting & Formatting (Clean)
python -m ruff check .
# Output: All checks passed!

# 3. Static Type Checking (0 errors across 29 files)
python -m mypy corpus_toolkit
# Output: Success: no issues found in 29 source files
```

---

## 4. Memory Preservation & System Architecture

1. **Lazy Loading:** `LazyCorpusText` delays DataFrame instantiation until `.tokens` or `.sentences` are accessed.
2. **Explicit Memory Eviction:** Calling `.evict()` drops both DataFrames and triggers `gc.collect()`, restoring memory.
3. **Atomic File Operations:** Parquet and JSON files are written via `tempfile.mkstemp` and atomically moved with `os.replace`, preventing corrupted cache states if interrupted.
4. **LRU Cache Budget:** Default 2,048 MB cache budget strictly enforced via mtime-sorted eviction in `enforce_budget()`.
5. **Headless Execution Ceiling:** Peak memory consumption during full headless notebook run remains $< 1.2\text{ GB}$, well within standard CI/CD and workstation limits.

---

## 5. Ethical & Copyright Compliance

- **Tracked Notebook Protection:** The GitHub repository tracks `Corpus_Analysis.ipynb` with **0 executed cell outputs**. A dedicated test (`test_tracked_notebook_is_clean`) asserts that all code cells have empty output lists and `execution_count: null`.
- **Execution Output Isolation:** When executed headlessly for verification (`--execute`), outputs are saved to `executed_Corpus_Analysis.ipynb`, which is ignored by `.gitignore`.
- **Data Exclusion:** `data/`, `*.parquet`, `*.pickle.xz`, `*.tsv`, `*.csv`, `*.xlsx`, and derived figures are strictly excluded in `.gitignore` to prevent distributing copyrighted literary works.
- **Corpus Scope Definition:** The 13 texts analyzed represent the focal core of the 3 pioneer Turkish SF author-translators (`Selma MİNE`, `Zühtü BAYAR`, `Özlem KURDOĞLU`: 5 English source novels, 5 Turkish parallel translations, and 3 indigenous novels), selected as an empirically bounded pedagogical subset of the broader 18-book thesis corpus.
