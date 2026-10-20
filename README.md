# corpus-toolkit · Corpus analysis of Turkish SF author-translators

An **educational, memory-preserving** Jupyter notebook and Python toolkit for analysing an
empirically grounded English–Turkish science-fiction corpus: **5 English source novels, their 5 Turkish
translations (5 parallel pairs) and 3 indigenous Turkish novels** by three pioneer author-translators —
**Selma MİNE**, **Zühtü BAYAR**, **Özlem KURDOĞLU**.

> [!NOTE]
> **Analytical Corpus Scope:**
> The 13 texts in this toolkit constitute the focal pioneer core subset of the PhD thesis's broader
> 18-book analytical corpus (which comprises 10 translated texts and 8 indigenous novels across 8 Turkish
> author-translators). This educational subcorpus concentrates on the first-generation pioneer trio whose
> complete NLP annotations (BookNLP + VNLP/KeNet sentence alignment) enable full parallel and comparative
> stylometric exploration.

* 📓 `Corpus_Analysis.ipynb` — 14 chapters in English, ground-up and academic (objectives → toy example →
  cheat-sheet → code → pitfalls → exercises → theoretical notes).
* 🇹🇷 `Corpus_Analysis_tr.ipynb` — 14 bölümlük Türkçe ders not defteri (pedagojik başlıklar, terim sözlüğü,
  adım adım oyuncak örnekler, kodlar, sık yapılan hatalar, çözümlü alıştırmalar ve kuramsal çeviribilim notları).
* 🧰 `corpus_toolkit/` — the tested Python package behind it (lazy loading, parquet cache,
  search, KWIC, collocations, diversity, TF-IDF, dependency trees, reporter, widgets, CLI).
* ✅ `tests/` — known-answer unit tests (every metric and number hand-computed and benchmarked).

Every user-facing message prints **full author names and book titles**; short codes are internal keys only.

---

## Table of contents
1. [Features](#features) · 2. [Install](#install) · 3. [Data layout](#data-layout) ·
4. [Quick start](#quick-start) · 5. [Python API with examples](#python-api-with-examples) ·
6. [Command-line interface](#command-line-interface) · 7. [Notebook chapters](#notebook-chapters) ·
8. [Memory & cache](#memory--cache) · 9. [Configuration](#configuration) ·
10. [Metrics and formulas](#metrics-and-formulas) · 11. [Development](#development) ·
12. [Troubleshooting](#troubleshooting) · 13. [Citing & licence](#citing--licence)

## Features
| area | what you get |
|---|---|
| **Loading** | 8 lazy loaders (English / Turkish / pairs / indigenous / all / author-related / author-Turkish / single text); compact token tables; `evict()` |
| **Views** | tokens **or** lemmas (with Turkish VNLP apostrophe suffix remediation: `Türkiye'nin` → `türkiye`) · raw **or** content (function words hidden, rules from `passim_analysis`) · `drop` **or** `mask` spans · 4 punctuation modes (`drop`, `keep`, `strip`, `split`) |

| **Search** | token, lemma, glob, regex, UPOS filter, context-word (collocate) constraint, with/without punctuation, in-token strip & split |
| **KWIC & Views** | spans `phrase/collocation/extended/discourse/sentence/N/L5R2`, 5 notebook views (`kwic`, `chips`, `cards`, `parallel`, `table`) + `console`, sorting by L1…R5 |
| **NDA Parallel View** | side-by-side English ↔ Turkish alignment groups (`parallel_view.py`) importing `Neologism_Dictionary_Annotation` caches: dual-row `tok` + `lem · pos` pills, 4 disjoint visual sets (`Linked L#`, `Single-EN` teal, `Single-TR` rose, `Candidate` amber, `Hit` crimson), Layer 0 Realia (NER) vs Top-Layer Irrealia, interactive per-row SVG connector lines (`first EN ↔ first TR`), and Current Label Attributions summary footer |
| **Columnar Table View** | flexible, self-contained HTML5/ES6 DataGrid (`table_view.py`): 20-row default client-side pagination (`10/20/50/100/All`), multi-type ascending/descending sorting (`NaN`-last numeric + Turkish/English `Intl.Collator`), drag-to-resize column splitters, layout presets (`Auto-Fit`, `Wrap Text`, `Compact`), instant filter, and one-click TSV copy |
| **Statistics** | per10k, Juilland D, Pearson/Spearman/cosine, BH-FDR, MI/MI²/MI³/T/G²/Log-Dice, TF-IDF, 14+ lexical-diversity metrics |
| **Parallel corpus** | alignment shapes (1:1 … omission/addition), `R_sent`, word/char ratios |
| **Grammar** | POS comparative analysis, lexical density, noun/verb ratio, translated-vs-indigenous bootstrap CIs |
| **Syntax** | dependency trees (English **and** Turkish) in spaCy displaCy style, function words dimmed |
| **Outputs** | Markdown/TSV/PNG/XLSX written to `data/corpus_analysis/{reports,tables,figures}` |
| **Safety** | content-addressed Parquet cache with atomic writes, size budget, optional clear-on-start |

## Install
The toolkit uses only widely available scientific-Python packages (no model downloads):

```bash
python -m venv .venv && source .venv/bin/activate        # or use an existing conda env
pip install -e ".[dev]"                                   # numpy pandas scipy scikit-learn matplotlib seaborn nltk pyarrow spacy ...
```
Python ≥ 3.10. Run the notebook with `jupyter lab Corpus_Analysis.ipynb`
(or execute headlessly, see below).

## Data layout
The toolkit **reads** the thesis workspace (not stored in this repository):

```
<thesis>/corpus/SF_Novels/txt_translation_book_locations.tsv     # metadata of pairs
<thesis>/corpus/SF_Novels/txt_indigenous_book_locations.tsv      # metadata of indigenous novels
<thesis>/data/alignment/<Pair>/<code>.pickle.xz                  # NLP-annotated texts (+ *_alignment.pickle, *_sentence_map_*.pickle)
<thesis>/data/indigenous/<code>/<code>_<timestamp>.pickle.xz
```
and **writes** to `<thesis>/data/corpus_analysis/` (`.cache/ reports/ tables/ figures/`).
This repository sits at `<thesis>/scripts/corpus_analysis/`; override locations with environment
variables ([Configuration](#configuration)).

## Quick start
```bash
cd scripts/corpus_analysis
python -m pytest -q                                   # 47 known-answer tests
python -m corpus_toolkit inventory                    # all 13 texts, full names
python -m corpus_toolkit search robot --category "All Turkish texts" --pos NOUN --span L3R2
jupyter lab Corpus_Analysis.ipynb                     # the teaching notebook (186 cells; or Corpus_Analysis_tr.ipynb)
```

Headless execution (also the notebooks' acceptance test):
```bash
python tools/build_notebook.py --execute              # rebuilds + executes + saves executed_Corpus_Analysis.ipynb
python tools/build_notebook_tr.py --execute           # rebuilds + executes + saves executed_Corpus_Analysis_tr.ipynb
# or:  CORPUS_CACHE_POLICY=keep python -m jupyter nbconvert --to notebook --execute Corpus_Analysis.ipynb
```

## Python API with examples
```python
from corpus_toolkit import CorpusLoader, TokenView
from corpus_toolkit import search, kwic, render, collocation, diversity, batch_kwic, tfidf, pos, alignment, depviz

loader = CorpusLoader()                      # asks to clear the cache; headless → keep
loader.registry.inventory()                  # table with full author & book names
```

### 1 · Loaders
```python
loader.load_all_english().describe()                      # 5 English sources
loader.load_all_turkish().describe()                      # 5 translations + 3 indigenous
loader.load_translation_pairs().describe()                # 5 parallel pairs
loader.load_indigenous("Zühtü Bayar").describe()          # author by name or code ("ZB")
loader.load_all()                                         # 13 texts
loader.load_author_related("Selma Mine")                  # pairs + indigenous of one author
loader.load_author_turkish("OK")                          # Turkish texts of one author
text = loader.load_text("Karanlığı Taramak")              # one text (code or title)
text.tokens.head(); text.memory_mb(); text.evict()        # compact table, RAM use, release
for t in loader.load_all().iter_evicting(): ...           # memory-safe loop
```

### 2 · Views (field, function words, span mode, and punctuation)
```python
TokenView(text, field="lem")                                          # raw lemmas (default punct='drop')
TokenView(text, field="tok", filter_function_words=True)              # content tokens (drop function words)
TokenView(text, field="lem", filter_function_words=True, mode="mask") # keep sequence, mask function words
TokenView(text, field="tok", punct="keep")                            # keep standalone punctuation (e.g. '?', '.')
TokenView(text, field="tok", punct="strip")                           # collapse in-token punctuation (Türkiye'nin -> Türkiyenin)
TokenView(text, field="lem", punct="split")                           # split composite lemmas (robot-bilim -> ['robot', 'bilim'])
```

### 3 · Search
```python
engine = search.CorpusSearchEngine()
q = search.SearchQuery(["robot"], field="lem", pos={"NOUN"})
res = engine.search(q, list(loader.load_all_turkish()))
res.summary()                      # hits, running words, per10k
res.hits.head()                    # code, title, ch/p/s/tok coordinates, token, lemma, form, UPOS

search.SearchQuery(["gel*"], "lem", match="glob")                          # wildcard
search.SearchQuery([r"^robot(lar)?$"], "tok", match="regex")               # regex
search.SearchQuery(["robot"], "lem", collocate=["insan"], collocate_span=(10, 10))   # needs 'insan' within ±10
search.SearchQuery(["robot"], "lem", filter_function_words=True, mode="drop")        # content view
search.SearchQuery(["?"], "tok", punct="keep")                             # search punctuation directly
search.SearchQuery(["Türkiye'nin"], "tok", punct="strip")                  # in-token strip (matches Türkiyenin)
search.SearchQuery(["bilim"], "lem", punct="split")                        # in-token split (matches inside robot-bilim)
search.SearchQuery(["türkiye"], "lem")                                     # matches all inflected forms via lemma remediation
search.SearchQuery(["Türkiye'nin"], "lem")                                 # inflected query term automatically resolves to base stem
```


### 4 · KWIC concordance
```python
texts = [loader.load_text("IR-IA"), loader.load_text("BR-SM")]
res = engine.search(search.SearchQuery(["robot"], "lem"), texts)
conc = kwic.Concordancer().run(res, texts, span="collocation")   # or 'phrase','extended','discourse','sentence', 7, (5,2), 'L5R2'
render.show(conc, "kwic")                       # aligned table
render.show(conc, "chips")                      # coordinate chips  (ch · p · s · tok)
render.show(conc, "cards", loader=loader)       # sentence cards + aligned counterpart sentence
render.show(conc, "parallel", loader=loader)    # NDA side-by-side parallel view with SVG links & tags
render.show(conc, "table", page_size=20)        # interactive 20-row paginated, sortable, resizable DataGrid
render.show_parallel(loader, "BR-SM", [4, 5], hits={"robot"})  # direct parallel group inspection
render.show_table(res.summary(), page_size=20, title="Search Summary")  # interactive DataFrame table
render.show(conc.sorted("R1"), "console")       # sort by first word right of the node (L1…R3, node, text)
conc.to_frame()                                 # plain DataFrame
```
| span | (left, right) |
|---|---|
| `phrase` | (3, 3) |
| `collocation` | (5, 5) |
| `extended` | (10, 10) |
| `discourse` | (20, 20) |
| `sentence` | whole sentence |
| `7` / `(5, 2)` / `"L5R2"` | custom, 0–20 per side |

### 5 · Batch KWIC (lists of words)
```python
bk = batch_kwic.BatchKwicAnalyzer()
out = bk.analyze(["robot", "insan", "makine"], list(loader.load_all_turkish()), field="lem")
out.summary(); out.pairwise(); out.matrix("pearson_r")          # per10k, Juilland D, Pearson/Spearman/cosine + BH q
bk.analyze({"machine": ["robot", "makine"], "human": ["insan", "kişi"]}, texts)   # named groups
```

### 6 · Collocations
```python
view = TokenView(loader.load_text("BR-SM"), "lem", filter_function_words=False)
tab = collocation.collocates(view, "robot", left=5, right=5, min_freq=5, sort_by="G2")   # MI MI2 MI3 T G2 LogDice
```

### 7 · Lexical diversity
```python
from corpus_toolkit import analysis
analysis.diversity_for(loader, loader.load_all(), field="lem", filter_function_words=True)   # cached
diversity.mtld(forms); diversity.mattr(forms, 100); diversity.sttr(forms)
```

### 8 · TF-IDF · POS · alignment · dependency trees
```python
tfidf.TfidfAnalyzer().fit(loader.load_all_turkish(), "lem", True, exclude_pos={"PROPN"}).top_terms("BR-SM", 10)
pos.PosComparativeAnalyzer().group_comparison(translations, indigenous, ("translation", "indigenous"))
alignment.AlignmentStructureAnalyzer(loader.cache).summary([p for p, _, _ in loader.load_translation_pairs()])
dv = depviz.DependencyVisualizer(loader); sid = dv.sid_of(text, (1, 4, 4)); dv.table(text, sid); dv.svg(text, sid)
dv.alignment_html("BR-SM", 4)               # stacked English + Turkish trees of one aligned group
```

### 9 · Reports and the explorer widget
```python
from corpus_toolkit import reporter
rep = reporter.CorpusReporter(loader.config, loader.registry, "my_run")
rep.add_table("diversity", div, index=True); rep.add_figure("radar", fig); rep.finalize()
analysis.standard_report(loader, "standard")             # inventory + alignment + POS + diversity
from corpus_toolkit.explorer import CorpusExplorerUI, quick_search
CorpusExplorerUI(loader).show()                           # widget panel
quick_search(loader, ["robot"], category="All Turkish texts", span="phrase")
```

## Command-line interface
Run commands with `python -m corpus_toolkit <command>` (or the `corpus-toolkit` executable if installed via `pip install -e .`):

| Command | Description | Example Call |
| :--- | :--- | :--- |
| `inventory` | Print complete metadata table of all 13 texts | `python -m corpus_toolkit inventory` |
| `search` | Multi-word search with UPOS and span constraints | `python -m corpus_toolkit search robot --category "All Turkish texts" --pos NOUN --span L5R2` |
| | Glob wildcard and regex search | `python -m corpus_toolkit search "gel*" --match glob --field lem --content --mode mask` |
| | Context collocate constraint | `python -m corpus_toolkit search robot --with insan --author "Selma Mine"` |
| `collocate` | Extract 6 association measures for a given node | `python -m corpus_toolkit collocate robot --text BR-SM --left 5 --right 5 --sort G2` |
| `diversity` | Compute full 14-metric LancsBox-X battery | `python -m corpus_toolkit diversity --category "All Turkish texts" --field lem --content` |
| `pos` | Comparative POS distributions and lexical density | `python -m corpus_toolkit pos` |
| `align` | Parallel sentence alignment cardinalities & ratios | `python -m corpus_toolkit align` |
| `dep` | Print token table and render SVG dependency tree | `python -m corpus_toolkit dep BR-SM --coord 1 2 3 --svg output_tree.svg` |
| `tfidf` | Extract top distinctive key terms per document | `python -m corpus_toolkit tfidf --lang tr --top 8 --chunks 5` |
| `report` | Generate Markdown, TSV, PNG, and XLSX reports | `python -m corpus_toolkit report --name standard_run` |
| `cache` | Inspect cache entries or clear safely | `python -m corpus_toolkit cache info` · `python -m corpus_toolkit cache clear` |

### Understanding Content View: `drop` vs `mask`
When searching or computing collocations on content words (`--content` / `filter_function_words=True`):
- **`drop`** (default for topical collocations): Function words (determiners, pronouns, adpositions, conjunctions, particles, interjections) are completely eliminated from the token sequence. A span of $\pm 5$ words covers **5 content words**, regardless of intervening function words.
- **`mask`** (default for structural analysis): Function words remain in their original sequence positions to preserve running text distance, but are masked so they can never match as a node or candidate collocate. A span of $\pm 5$ covers **5 running words**, but ignores any function words within that window.

### Punctuation Handling: `drop` vs `keep` vs `strip` vs `split`
In Turkish VNLP tokenization and lemmatization, in-token punctuation is preserved within compound words and inflections (e.g. `Türkiye'nin`, `Fred'`, `robot-bilim`, `sn'lik`, `ay'da`, `1882'de`, `1882'`). Four explicit modes are available across CLI and API:
- **`--punct drop`** (default): Standalone punctuation tokens (`PUNCT`, `SYM`) are excluded; in-token punctuation is retained as-is (`Türkiye'nin`, `robot-bilim`).
- **`--punct keep`** (or `--with-punct`): Standalone punctuation is retained in the view. Allows searching directly for punctuation marks:
  ```bash
  python -m corpus_toolkit search "?" --punct keep --category "All Turkish texts"
  ```
- **`--punct strip`**: Standalone punctuation is dropped, and in-token punctuation characters are collapsed/stripped without splitting (Passim `remove_punctuations` style). Both surface tokens and lemmas are stripped (`Türkiye'nin` → `Türkiyenin`, `Fred'` → `Fred`, `robot-bilim` → `robotbilim`):
  ```bash
  python -m corpus_toolkit search "Türkiyenin" --punct strip
  python -m corpus_toolkit diversity --punct strip
  ```
- **`--punct split`**: Standalone punctuation is dropped, and composite tokens are decomposed into constituent word tokens (Passim `retokenizer` style). Sub-tokens share the original token's sentence ID and coordinate mapping (`Türkiye'nin` → `['Türkiye', 'nin']`, `robot-bilim` → `['robot', 'bilim']`):
  ```bash
  python -m corpus_toolkit search "bilim" --field lem --punct split
  python -m corpus_toolkit diversity --punct split
  ```

### Cache Policy: `ask` vs `keep` vs `clear`
- In interactive Python or Jupyter notebook sessions, `CORPUS_CACHE_POLICY` defaults to **`ask`**, prompting the user at kernel startup to choose whether to keep or clear cached Parquet files. If run headlessly (e.g. CI or `nbconvert` with no stdin), it falls back safely to **`keep`**.
- In the CLI, the default cache policy is **`keep`** to avoid blocking automated terminal scripts. You can pass `--cache-policy clear` to force a clean cache rebuild.

### Sample CLI Outputs

#### 1. Sentence Alignment Profile (`python -m corpus_toolkit align`)
```text
pair           A Scanner Darkly → Karanlığı Taramak  I, Robot → Ben, Robot: Mekanik Adam Devri
translator                           Özlem Kurdoğlu                                 Selma Mine
alignments                                     7434                                       6431
eng_sentences                                  7652                                       6591
tur_sentences                                  8268                                       7612
1:1_pct                                       87.89                                      74.27
1:N_pct                                        8.96                                      16.76
N:1_pct                                        2.17                                       2.74
R_sent                                         1.08                                       1.15
word_ratio                                     0.80                                       0.73
char_ratio                                     1.05                                       0.99
```

#### 2. Collocation Analysis (`python -m corpus_toolkit collocate robot --text BR-SM --left 5 --right 5 --sort G2`)
```text
node=robot f=729 N=51632 R1=4596
collocate  O11   C1     E11    MI   MI2    MI3     T      G2  p_G2  LogDice
        d   45   48   4.273 3.397 8.889 14.380 6.071 196.219   0.0   10.890
        b   43   50   4.451 3.272 8.698 14.125 5.879 169.195   0.0   10.821
   merkez   38   45   4.006 3.246 8.494 13.742 5.515 146.522   0.0   10.652
    firma   24   46   4.095 2.551 7.136 11.721 4.063  56.624   0.0    9.987
  mekanik   17   31   2.759 2.623 6.711 10.798 3.454  42.219   0.0    9.518
```


## Notebook chapters
| # | chapter | new idea |
|---|---|---|
| 0 | Orientation | token/type/lemma, raw/content, drop/mask, cache policy |
| 1 | Inventory | corpus design, sizes |
| 2 | Lazy loading | 8 loaders, token table, memory, evict |
| 3 | Alignment structure | 1:1/1:N/N:1/N:M/omission/addition, `R_sent` |
| 4 | POS comparison | lexical density, translated-vs-indigenous bootstrap |
| 5 | Dependency trees | EN + TR trees, function words dimmed |
| 6 | Search | token/lemma/glob/regex/POS/context, content-word view |
| 7 | KWIC | spans, views, sorting, NLTK cross-check |
| 8 | Batch KWIC | per10k, Juilland D, Pearson/Spearman/cosine, FDR |
| 9 | Lexical diversity | TTR problem, STTR/MATTR/MTLD + 11 more |
| 10 | Collocations | MI/MI²/MI³/T/G²/Log-Dice, strength vs evidence |
| 11 | TF-IDF | keyness, names excluded |
| 12 | Reporter | Markdown/TSV/PNG/XLSX reports |
| 13 | Explorer | widget panel + `quick_search` |

## Memory & cache
* Texts are **lazy**; tables are `category`-typed (≈ 7 MB per 70 000-token novel); peak RAM for the full
  notebook stays well below 3.5 GB (tested with `tracemalloc`, see `docs/QA.md`).
* Cache: `data/corpus_analysis/.cache/` — Parquet/JSON, keyed by *file signature + schema version +
  arguments*, atomic writes, LRU size budget (default 2 GB). Policy `CORPUS_CACHE_POLICY=keep|clear|ask`.
  `ask` prompts once at start; headless runs fall back to `keep`.
* `python -m corpus_toolkit cache clear` removes everything derived; source pickles are never touched.

## Configuration
| variable | default | meaning |
|---|---|---|
| `CORPUS_THESIS_ROOT` | `<repo>/../..` | workspace holding `corpus/` and `data/` |
| `CORPUS_DATA_DIR` | `<thesis>/data/corpus_analysis` | output root (cache, reports, tables, figures) |
| `CORPUS_AUTHOR_CODES` | `SM,ZB,OK` | focal author-translators |
| `CORPUS_CACHE_POLICY` | `ask` | `keep` \| `clear` \| `ask` |

## Documentation, PRD, Metrics and Formulas
See:
* [`docs/Corpus_Analysis_PRD.md`](docs/Corpus_Analysis_PRD.md) — full Product Requirements Document (13-text pioneer scope, lazy Parquet cache, 3-switch + 4-punctuation `TokenView`, NDA parallel view, and interactive columnar table specifications).
* [`docs/ARCHITECTURE_AND_DATAFLOW.md`](docs/ARCHITECTURE_AND_DATAFLOW.md) — end-to-end data flow diagrams and stage specifications from alignment & NDA pickles into `TokenView`, `ParallelView`, and `TableView`.
* [`docs/METRICS.md`](docs/METRICS.md) — every mathematical formula, edge-case rule, and citation.
* [`docs/QA.md`](docs/QA.md) — quality rubric, hand-checked benchmarks, and acceptance results.

## Development
```bash
python -m pytest -q          # known-answer tests (integration tests auto-skip without the corpus)
ruff check .                 # lint
mypy corpus_toolkit          # types (see docs/QA.md for documented overrides)
python tools/build_notebook.py --execute   # regenerate + run the notebook
```
The notebook is *generated* from `tools/nb_part_*.py` so that its text is diff-friendly; edit
those files, not the `.ipynb`.

## Troubleshooting
| symptom | fix |
|---|---|
| `Metadata file not found` | set `CORPUS_THESIS_ROOT` to the thesis workspace |
| `No '<code>*.pickle.xz' in …` | the annotated pickles are missing; check `data/alignment/` and `data/indigenous/` |
| notebook prompt blocks | set `CORPUS_CACHE_POLICY=keep` |
| stale numbers after editing a pickle | automatic; or `python -m corpus_toolkit cache clear` |
| `displacy` import error | install `spacy` (no model required) |

## Citing & licence
Cite via [`CITATION.cff`](CITATION.cff). MIT licence (see `pyproject.toml`). The corpus texts are **not**
redistributed here.
