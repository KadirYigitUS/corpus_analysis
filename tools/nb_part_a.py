"""Chapters 0–5: orientation, ingestion, alignment, POS, dependency trees."""

from nbcells import (
    Cell,
    chapter_header,
    cheat_sheet,
    code,
    exercises,
    md,
    pitfalls,
    scholarly,
)


def chapters() -> list[Cell]:
    c: list[Cell] = []

    # ------------------------------------------------------------------ Chapter 0
    c += [md("""
    # 📖 Corpus Analysis of Turkish SF Author-Translators
    ### A ground-up, academic, memory-preserving notebook

    **Scope & Context.** This notebook studies the complete corpus of the **three pioneer
    Turkish science fiction author-translators**:
    **Selma Mine**, **Zühtü Bayar** and **Özlem Kurdoğlu** — comprising exactly **13 texts**:
    - **5 English source works**: Asimov (*I, Robot*), Anderson (*The Light*), Leinster (*The Lonely Planet*), London (*The Scarlet Plague*), Dick (*A Scanner Darkly*);
    - **5 Turkish translations**: *Ben, Robot* (Mine 1983), *Aydınlık* (Bayar 1998), *Yalnız Gezegen* (Bayar 1998), *Kıyametten Sonra* (Bayar 1998), *Karanlığı Taramak* (Kurdoğlu 1998);
    - **3 indigenous Turkish SF novels**: *OBİ,J.S.927* (Mine 1980), *Sahte Uygarlık* (Bayar 1999), *Son Cephede Şafak* (Kurdoğlu 2000).

    These 13 texts form the pioneer author-translator core of the PhD thesis's broader 18-book
    analytical corpus (8 author-translators, 10 translated texts, 8 indigenous novels).
    Every menu, table and message displays **full author names and full book titles** (the short codes
    such as `BR-SM` are used solely as internal keys).

    **How the notebook teaches.** Each chapter follows the same pedagogical template:
    🎯 learning objectives → 🧪 a tiny worked example you can verify by hand →
    🧰 parameter cheat-sheet → ▶️ executable code on the real corpus → ⚠️ pitfalls →
    ✏️ exercises with solutions → 🎓 scholarly interpretation with citations.
    Nothing is a black box: every statistic is implemented in `corpus_toolkit/` in readable,
    commented Python and unit-tested against hand-computed answers.

    | colour | meaning |
    |---|---|
    | 🟦 cyan badge | English source text |
    | 🟧 amber badge | Turkish translation |
    | 🟩 emerald badge | Turkish indigenous novel |
    | 🌹 rose highlight | the search *node* |
    | figures: purple / green / blue | Selma Mine / Zühtü Bayar / Özlem Kurdoğlu |
    """),
          chapter_header(0, "Orientation, vocabulary & cache policy", 10,
                         ["distinguish **token / type / lemma**, **raw / content** views and "
                          "**drop / mask** spans",
                          "explain why this notebook is *lazy* and *cached*",
                          "choose the cache policy (keep / clear)"],
                         "none", "Three switches define every number you will compute."),
          md("""
    ### 0.1 Vocabulary you need

    | term | definition | example (Turkish) |
    |---|---|---|
    | **token** | one running word/punctuation unit of the text | `robotların` |
    | **type** | a *distinct* token form | `robotların` counted once however often it occurs |
    | **lemma** | dictionary form after morphological analysis | `robot` |
    | **content word** | open-class word: NOUN, VERB, ADJ, ADV, PROPN, NUM | `robot`, `yap-` |
    | **function word** | closed-class word: DET, PRON, ADP, AUX, CCONJ, SCONJ, PART, INTJ | `bir`, `ve`, `bu` |

    Turkish is **agglutinative**: one lemma yields very many surface forms
    (`robot, robotlar, robotların, robotlara …`). *Lemma* analysis therefore groups what a
    token analysis scatters — this is why every tool here has `field='lem'` **and** `field='tok'`.

    ### 0.2 The three switches
    | switch | values | effect |
    |---|---|---|
    | `field` | `'tok'` / `'lem'` | analyse surface forms or lemmas |
    | `filter_function_words` | `False` (**raw**) / `True` (**content**) | rules vendored from `scripts/passim_analysis` (`UposFilterService`); punctuation is *never* counted |
    | `mode` | `'drop'` / `'mask'` | when function words are hidden: *drop* removes them from the sequence (a ±5 span = five content words); *mask* keeps them so spans stay in running words but they cannot be nodes/collocates |

    ### 0.3 Why lazy + cached?
    A stored pickle holds list columns as *strings*; turning them into usable columns costs ≈ 2 s
    per novel. We (1) load a text **only when first needed**, (2) convert it to a compact
    one-row-per-token table (`category` dtypes ≈ 7 MB for 70 000 tokens), (3) store that table as
    **Parquet in `data/corpus_analysis/.cache/`** keyed by *file signature + schema version*, and
    (4) **evict** it from RAM after use (`text.evict()`, or `selection.iter_evicting()`).
    If a source pickle changes, its cache entry is automatically invalidated.
    """),
          md("""
    ### 0.4 Worked toy example: The three switches in action
    Sentence: *“Robotlar insanları gördü ve hızla kaçtı .”*
    - **Tokens (N=7)**: `['Robotlar', 'insanları', 'gördü', 've', 'hızla', 'kaçtı', '.']` (V=7 types)
    - **Lemmas (N=7)**: `['robot', 'insan', 'gör', 've', 'hız', 'kaç', '.']`
    - **Content words (`filter_function_words=True`, punctuation excluded)**: `['robot', 'insan', 'gör', 'hız', 'kaç']` (5 tokens, `ve` is CCONJ = function, `.` is PUNCT = excluded).
    - **`drop` span (±1 around `gör`)**: `[insan, hız]` (consecutive content words)
    - **`mask` span (±1 around `gör`)**: `[insan, ve]` (consecutive running words, `ve` cannot match/collocate)
    """),
          cheat_sheet("Analysis Switches", [
              ("field='lem'", "Lemmatised representation (recommended for Turkish)", "TokenView(text, field='lem')"),
              ("field='tok'", "Surface orthographic tokens", "TokenView(text, field='tok')"),
              ("filter_function_words=True", "Content words only (UPOS closed-classes hidden)", "TokenView(text, filter_function_words=True)"),
              ("mode='drop'", "Collapse positions when filtering function words", "TokenView(text, filter_function_words=True, mode='drop')"),
              ("mode='mask'", "Preserve running-text positions, mask function words", "TokenView(text, filter_function_words=True, mode='mask')"),
          ]),
          code("""
    import os, sys, warnings
    from pathlib import Path

    # the notebook lives in the repository root; make `corpus_toolkit` importable
    sys.path.insert(0, str(Path.cwd()))
    warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

    import numpy as np
    import pandas as pd
    import nltk                                   # the reference toolbox (used in Ch. 7, 10)
    import matplotlib.pyplot as plt
    from IPython.display import HTML, display

    from corpus_toolkit import CorpusLoader, TokenView
    from corpus_toolkit import (alignment, analysis, batch_kwic, collocation, depviz, diversity,
                                kwic, nltk_adapter, pos, render, reporter, search, stats, style,
                                tfidf, viz)
    display(HTML(style.CSS))                      # one CSS block for all HTML views
    pd.set_option("display.max_columns", 40); pd.set_option("display.width", 160)
    """),
          md("""
    ### 0.5 Choose the cache policy
    Running the next cell **asks** whether to clear `data/corpus_analysis/.cache/`
    (answer `y` for a clean start; anything else keeps it). In headless runs
    (`jupyter nbconvert --execute`) there is no keyboard, so the cache is **kept**.
    You can also decide beforehand with `CORPUS_CACHE_POLICY=keep|clear` in the environment.
    """),
          code("""
    loader = CorpusLoader()               # builds registry, asks about the cache, nothing else
    print(loader.cache.info())
    """),
          pitfalls(["Do not compare raw TTR of a 5 000-word story with a 70 000-word novel "
                    "(Chapter 9 shows why).",
                    "`mask` and `drop` give different span semantics — always report which one you used."]),
          scholarly("""
          **Polysystem Positioning & Stylistic Variables (Even-Zohar 1990; Toury 2012):**
          In peripheral literary polysystems such as 20th-century Turkish science fiction,
          translated texts introduce lexical models, grammatical structures, and neologisms.
          Switching between surface tokens and lemmas allows the researcher to disentangle
          inflectional variation from underlying lexical repertoire formation.
          """),
          ]

    # ------------------------------------------------------------------ Chapter 1
    c += [chapter_header(1, "Corpus inventory", 10,
                         ["list every author-translator, text and translation pair by full name",
                          "verify that all 13 pickle files exist",
                          "read basic size statistics (sentences, tokens)"],
                         "Chapter 0", "Know your data before you measure it."),
          md("""
    ### 1.1 Why an inventory first?
    Corpus linguistics begins with *corpus design* (Baker 1993; Biber 1988): what is in the corpus,
    how big is it, and how balanced? Our sub-corpus is **small and uneven** — *The Light* has
    ≈ 4 000 words, *A Scanner Darkly* ≈ 88 000 — so most comparisons in later chapters use
    length-robust measures and are labelled *descriptive*.
    """),
          md("""
    ### 1.2 Worked toy example: Querying the inventory
    We filter the inventory DataFrame for author-translator Selma Mine (`SM`):
    - Expected records: exactly 3 books (1 English source *I, Robot*, 1 Turkish translation *Ben, Robot*, 1 indigenous novel *OBİ,J.S.927*).
    - Each entry contains code, author, title, genre category, and year.
    """),
          code("""
    inv = loader.registry.inventory()
    display(inv[inv["focal_code"] == "SM"][["code", "creator", "title", "type", "year"]])
    """),
          cheat_sheet("Registry & Inventory Commands", [
              ("loader.registry.inventory()", "Returns a full DataFrame of all 13 texts with metadata", "display(loader.registry.inventory())"),
              ("loader.registry.verify_files()", "Checks that every .pickle.xz file exists on disk", "loader.registry.verify_files()"),
              ("loader.registry.display(rec)", "Human-readable label: 'Author — Title [CODE]'", "print(loader.registry.display('BR-SM'))"),
              ("loader.registry.resolve_author(query)", "Resolves code or full name to author code", "loader.registry.resolve_author('Selma Mine')"),
              ("loader.registry.resolve_text(query)", "Resolves code or title substring to TextRecord", "loader.registry.resolve_text('Ben, Robot')"),
          ]),
          md("### 1.3 Full corpus verification and size distribution"),
          code("""
    display(loader.registry.inventory())
    display(loader.registry.verify_files())
    """),
          code("""
    loader.load_all().describe();
    sizes = loader.load_all().summary()          # first run builds the cache (≈ 20 s once)
    display(sizes.sort_values(["author_translator", "type"]))
    """),
          code("""
    fig, ax = plt.subplots(figsize=(9, 4))
    d = sizes.merge(loader.registry.inventory()[["code", "focal_code", "year"]], on="code")
    ax.bar(d["code"], d["tokens"], color=[viz.color_for(c) for c in d["focal_code"]],
           alpha=0.85)
    ax.set_ylabel("tokens (incl. punctuation)"); ax.set_title("Size of each text")
    plt.xticks(rotation=45, ha="right"); plt.show()
    """),
          pitfalls(["`tokens` here include punctuation; analyses later use *running words* "
                    "(punctuation removed).",
                    "Do not extrapolate statistical generalisations across authors without checking individual book lengths."]),
          exercises([("Which author-translator has the largest *indigenous* text, and how many "
                      "tokens does it have?",
                      "```python\nsizes[sizes['type']=='indigenous'].nlargest(1,'tokens')"
                      "[['author_translator','title','tokens']]\n```")]),
          scholarly("""
          **Corpus Representativeness and Author-Translator Sampling (Toury 2012; Biber 1988):**
          The trio Selma Mine, Zühtü Bayar, and Özlem Kurdoğlu constitutes the founding generation
          of modern Turkish science fiction author-translators. Including both their translation
          work and their indigenous novels creates a natural quasi-experimental design for
          investigating the internalization of translational norms into indigenous authorial habitus.
          """),
          ]

    # ------------------------------------------------------------------ Chapter 2
    c += [chapter_header(2, "Lazy, memory-preserving loading", 15,
                         ["use all 8 loaders", "inspect the compact token table",
                          "measure memory and use `evict()`"],
                         "Chapters 0–1", "Load what you need, when you need it, and give the memory back."),
          md("""
    ### 2.1 The eight loaders
    | method | returns | texts |
    |---|---|---|
    | `load_all_english()` | selection | 5 English sources |
    | `load_all_turkish()` | selection | 5 translations + 3 indigenous |
    | `load_translation_pairs([author])` | parallel corpus | 5 aligned pairs |
    | `load_indigenous([author])` | selection | 3 indigenous novels |
    | `load_all()` | selection | all 13 |
    | `load_author_related([author])` | selection | pairs + indigenous of an author |
    | `load_author_turkish([author])` | selection | translations + indigenous of an author |
    | `load_text(code or title)` | one text | e.g. `'BR-SM'` or `'Karanlığı Taramak'` |

    `author` accepts a code (`'SM'`) **or** a name (`'Selma Mine'`, `'selma mine'`, `'ozlem kurdoglu'`).
    """),
          md("""
    ### 2.2 Worked toy example: The lifecycle of a LazyCorpusText
    1. Loading does not materialize the data table (`text.is_loaded() == False`).
    2. Accessing `text.tokens` loads it from Parquet/pickle into RAM (`text.is_loaded() == True`).
    3. Calling `text.evict()` frees the table and triggers garbage collection.
    """),
          code("""
    toy_t = loader.load_text("BR-SM")
    print("Before accessing tokens:", toy_t.is_loaded())
    _ = toy_t.tokens
    print("After accessing tokens:", toy_t.is_loaded(), f"({toy_t.memory_mb():.1f} MB)")
    toy_t.evict()
    print("After evict():", toy_t.is_loaded())
    """),
          cheat_sheet("Loader Methods", [
              ("loader.load_all_english()", "5 English SF source texts", "loader.load_all_english()"),
              ("loader.load_all_turkish()", "5 translations + 3 indigenous novels", "loader.load_all_turkish()"),
              ("loader.load_translation_pairs(author=None)", "5 parallel aligned pairs", "loader.load_translation_pairs('SM')"),
              ("loader.load_indigenous(author=None)", "3 indigenous novels", "loader.load_indigenous('ZB')"),
              ("loader.load_all()", "All 13 texts in the focal corpus", "loader.load_all()"),
              ("loader.load_text(identifier)", "Single text by code or title substring", "loader.load_text('BR-SM')"),
              ("text.evict()", "Release DataFrame memory and trigger gc.collect()", "text.evict()"),
          ]),
          code("""
    loader.load_all_english().describe()
    loader.load_all_turkish().describe()
    loader.load_translation_pairs().describe()
    loader.load_indigenous().describe()
    loader.load_author_related("Özlem Kurdoğlu").describe()
    loader.load_author_turkish("zuhtu bayar").describe();
    """),
          md("""
    ### 2.3 The token table
    One row per token; columns `sid`(sentence), `ti`(position), `tok`, `lem`, `pos`(UPOS),
    `morph`, `head`, `rel`(dependency), `fcl`(0 content / 1 function / 2 punctuation).
    """),
          code("""
    import time
    text = loader.load_text("Ben, Robot: Mekanik Adam Devri")     # still lazy …
    print(loader.registry.display(text))
    t0 = time.perf_counter(); tab = text.tokens                    # … materialised now
    print(f"{len(tab):,} tokens in {time.perf_counter()-t0:.2f}s · table ≈ {text.memory_mb():.1f} MB")
    display(tab.head(8))
    """),
          code("""
    # cold vs warm: evict, then reload from the Parquet cache
    text.evict(verbose=True)
    t0 = time.perf_counter(); _ = text.tokens
    print(f"reload from cache: {time.perf_counter()-t0:.3f}s")
    display(loader.memory_report())
    """),
          code("""
    # memory-safe loop over many texts: each text is evicted right after use
    rows = []
    for t in loader.load_all().iter_evicting():
        n = len(TokenView(t, "lem", filter_function_words=True))
        rows.append((t.record.focal_name, t.record.title, n))
    pd.DataFrame(rows, columns=["author_translator", "title", "content_lemmas"])
    """),
          pitfalls(["A `LazyCorpusText` held in a variable keeps its tables in RAM until you call "
                    "`.evict()` (or loop with `iter_evicting()`).",
                    "Editing a `.pickle.xz` invalidates its cache entry automatically; "
                    "deleting `.cache/` is always safe."]),
          exercises([("Load the translation pairs of Zühtü Bayar and print how many sentences "
                      "each English/Turkish text has.",
                      "```python\nfor pair, en, tr in loader.load_translation_pairs('ZB'):\n"
                      "    print(en.summary()['title'], en.summary()['n_sentences'], '→', "
                      "tr.summary()['title'], tr.summary()['n_sentences'])\n```")]),
          scholarly("""
          **Computational Memory Preservation in Digital Translation Studies (Sinclair 1991):**
          Analyzing book-length parallel and comparable corpora requires principled memory hygiene.
          By lazy-materializing DataFrames on demand, caching optimized column subsets, and evicting
          exhausted structures, we preserve an execution envelope below 1.5 GB RAM even across
          hundreds of thousands of annotated tokens.
          """),
          ]

    # ------------------------------------------------------------------ Chapter 3
    c += [chapter_header(3, "Alignment structure of the parallel corpus", 20,
                         ["classify sentence alignments into 1:1, 1:N, N:1, N:M, omission, addition",
                          "compute and interpret `R_sent`, word- and character-ratios",
                          "read Figures 1A and 1B critically"],
                         "Chapters 0–2", "How do translators cut and join sentences?"),
          md("""
    ### 3.1 Theory
    A sentence aligner pairs *groups* of English and Turkish sentences. The **shape** of the
    group is evidence of translator decisions (Toury 2012: *adequacy* vs. *acceptability*;
    Baker 1993: *explicitation, simplification*):

    | type | (English, Turkish) | reading |
    |---|---|---|
    | 1:1 | (1, 1) | sentence kept |
    | 1:N | (1, n≥2) | English sentence **split** |
    | N:1 | (n≥2, 1) | sentences **merged** |
    | N:M | (n≥2, m≥2) | restructured |
    | omission | (n, 0) | English material with no Turkish counterpart |
    | addition | (0, m) | Turkish material with no English counterpart |

    `R_sent = Turkish sentences ÷ English sentences` (>1: Turkish uses more sentences).

    ### 3.2 Worked toy example
    Six alignment groups: shapes (1,1), (1,1), (1,2), (2,1), (1,0), (0,1).
    English sentences = 1+1+1+2+1+0 = 6; Turkish = 1+1+2+1+0+1 = 6 → `R_sent = 1.0`
    even though two groups show restructuring — *a ratio near 1 can hide opposite movements*.
    """),
          code("""
    toy = [(1,1),(1,1),(1,2),(2,1),(1,0),(0,1)]
    print([alignment.alignment_type(a, b) for a, b in toy])
    print("R_sent =", sum(b for _, b in toy) / sum(a for a, _ in toy))
    """),
          cheat_sheet("Alignment Structure Commands", [
              ("alignment.alignment_type(n_en, n_tr)", "Classifies cardinality into '1:1', '1:N', 'N:1', 'N:M', 'omission', 'addition'", "alignment.alignment_type(1, 2)"),
              ("AlignmentStructureAnalyzer(cache).summary(pairs)", "Summary DataFrame with percentages and R_sent for all pairs", "ana.summary(pairs)"),
              ("AlignmentStructureAnalyzer.cardinality_table(pair)", "Per-alignment-group table with token counts and types", "ana.cardinality_table(pair)"),
              ("AlignmentIndex.texts(ai)", "Returns (eng_text, tur_text) tuple for alignment id ai", "idx.texts(14)"),
          ]),
          code("""
    pairs = [p for p, _, _ in loader.load_translation_pairs()]
    ana = alignment.AlignmentStructureAnalyzer(loader.cache)
    summary = ana.summary(pairs)
    display(summary.round(2))
    """),
          code("""
    fig = viz.alignment_stacked(summary); plt.show()                       # Figure 1A
    tables = {p.tur.title[:28]: ana.cardinality_table(p) for p in pairs}
    fig = viz.alignment_scatter(tables); plt.show()                        # Figure 1B
    """),
          md("""
    ### 3.3 Interpretation guide
    - **Mostly 1:1** → the translation keeps sentence boundaries; high **1:N** → splitting
      (typical when English long sentences are rendered into Turkish clause chains).
    - **omission / addition** may be *translator decisions* **or aligner artefacts** (paratext,
      different editions, OCR). Always inspect examples (use `AlignmentIndex.texts(ai)`)
      before attributing them to a translator.
    - `word_ratio < 1` is typical for English→Turkish because Turkish packs function words
      into suffixes (agglutination) — it is **typological**, not necessarily stylistic.
    """),
          code("""
    # inspect the first omissions of one pair (always look at examples!)
    pair = pairs[1]
    idx = loader.alignment_index(pair)
    tab = ana.cardinality_table(pair)
    for ai in tab[tab["type"] == "omission"]["ai"].head(3):
        print(ai, "| EN:", idx.texts(ai)[0][:120])
    """),
          pitfalls(["Percentages are over *alignment groups*, `R_sent` is over *sentences* — "
                    "they answer different questions.",
                    "Very small texts (*The Light*) produce unstable percentages."]),
          exercises([("Which pair has the highest share of N:M restructuring?",
                      "```python\nsummary.loc[summary['N:M_pct'].idxmax(), ['pair','N:M_pct']]\n```")]),
          scholarly("""
          **Translational Norms and Textual Segmentation (Toury 2012; Baker 1993):**
          Toury distinguishes between source-oriented *adequacy* (retaining the syntactic segmentation
          and sentence breaks of the original) and target-oriented *acceptability* (resegmenting
          into target-normative period lengths). The ratio $R_{\\text{sent}}$ and the proportion
          of 1:N splits operationalize the translator's position on this spectrum.
          """),
          ]

    # ------------------------------------------------------------------ Chapter 4
    c += [chapter_header(4, "Part-of-speech comparative analysis", 25,
                         ["compute UPOS profiles, lexical density and noun/verb ratios",
                          "compare English vs Turkish within a pair",
                          "compare translated vs indigenous Turkish with uncertainty"],
                         "Chapters 0–2", "Do translators write their own books differently from "
                         "the books they translate?"),
          md("""
    ### 4.1 Theory
    UPOS (Universal POS, Nivre et al. 2016) gives a language-neutral tag set. Two classical
    descriptors: **lexical density** = content words ÷ running words (Ure 1971; Halliday 1985)
    and the **noun/verb ratio** (nominal vs verbal style; Biber 1988).
    In our tables lexical density = (NOUN+VERB+ADJ+ADV) ÷ non-punctuation tokens × 100.
    English and Turkish differ *typologically*, so English↔Turkish gaps are read as **profiles**,
    not as quality. The *meaningful* comparison for the thesis is **translation ↔ indigenous**
    within Turkish (a habitus question: Simeoni 1998), reported with bootstrap confidence
    intervals; with only 5 vs 3 texts the result is **descriptive**, not inferential.

    ### 4.2 Worked toy example
    Sentence “The cat saw the dog .” → tags DET NOUN VERB DET NOUN PUNCT. Non-punctuation
    tokens = 5; content = NOUN, VERB, NOUN = 3 → lexical density 60 %; noun/verb = 2.
    """),
          cheat_sheet("POS Analyzer Methods", [
              ("PosComparativeAnalyzer().profile_table(texts)", "UPOS % columns and scalar metrics for every text", "P.profile_table(loader.load_all())"),
              ("PosComparativeAnalyzer().pair_comparison(en, tr)", "Direct parallel pair UPOS comparison with percentage-point differences", "P.pair_comparison(en, tr)"),
              ("PosComparativeAnalyzer().group_comparison(g1, g2, labels)", "Bootstrap confidence intervals of mean differences across sub-corpora", "P.group_comparison(trans, indig, ('trans', 'indig'))"),
          ]),
          code("""
    P = pos.PosComparativeAnalyzer()
    profile = P.profile_table(loader.load_all())
    display(profile.round(1))
    fig = viz.pos_heatmap(profile, pos.UPOS_ORDER); plt.show()             # Figure 2A
    """),
          md("""
    ### 4.3 One translation pair (Figure 2B)
    Change the codes to any pair printed in Chapter 2 (`IR-IA ⇄ BR-SM`, `ASD-PKD ⇄ KT-OK`, …).
    """),
          code("""
    en, tr = loader.load_text("IR-IA"), loader.load_text("BR-SM")
    print(loader.registry.display(en)); print(loader.registry.display(tr))
    cmp_df = P.pair_comparison(en, tr)
    display(cmp_df.round(1))
    fig = viz.pos_pair(cmp_df, f"{en.record.title} → {tr.record.title}"); plt.show()
    en.evict(); tr.evict()
    """),
          md("""
    ### 4.4 Translated vs indigenous Turkish (Figure 2C)
    Per-UPOS mean difference with a 95 % bootstrap CI over **texts**, plus a pooled-count χ² and
    Cramér's V (effect size). Texts are the unit of replication; tokens within a text are *not*
    independent, so the χ² p-value is only a rough screen.
    """),
          code("""
    trans = [loader.load_text(c) for c in ["BR-SM", "A-ZB", "YG-ZB", "KS-ZB", "KT-OK"]]
    indig = list(loader.load_indigenous())
    print("Translations:", ", ".join(loader.registry.display(t) for t in trans))
    print("Indigenous:", ", ".join(loader.registry.display(t) for t in indig))
    grp = P.group_comparison(trans, indig, ("translation", "indigenous"))
    display(grp.round(2)); print(grp.attrs)
    fig = viz.pos_group(grp, ("translation", "indigenous")); plt.show()
    """),
          code("""
    # same question restricted to content words only (function words hidden)
    grp_c = P.group_comparison(trans, indig, ("translation", "indigenous"), content_only=True)
    display(grp_c.round(2))
    """),
          pitfalls(["Different taggers/lemmatisers for English and Turkish ⇒ tag *inventories* are "
                    "comparable, tag *accuracy* is not.",
                    "Bootstrap CIs with n=3–5 texts are wide — say 'consistent with' not 'proves'.",
                    "Tokens within a book are non-independent: use Cramér's V effect size rather than p-values."]),
          exercises([("Compute lexical density for *indigenous* texts only and report the mean.",
                      "```python\nprofile[profile['type']=='indigenous']['lexical_density'].mean()\n```")]),
          scholarly("""
          **Translating Habitus and Translation Universals (Simeoni 1998; Toury 2012):**
          If translated Turkish is *more nominal* or *less dense* than indigenous prose by the same
          author, this is consistent with source-text pressure (*interference*, Toury 2012) — but it
          could equally reflect genre/period differences between a 1950s American novel and a 1999
          Turkish one. Only the designed pairs (same translator, translation vs own novel) let us
          argue about **habitus** rather than genre.
          """),
          ]

    # ------------------------------------------------------------------ Chapter 5
    c += [chapter_header(5, "Dependency trees (English & Turkish)", 20,
                         ["read a dependency tree", "render spaCy-style trees for both languages",
                          "dim function words without breaking the tree", "view aligned sentence groups"],
                         "Chapters 0–2", "Syntax made visible."),
          md("""
    ### 5.1 Theory
    A **dependency tree** attaches every word (*dependent*) to one *head* with a labelled
    relation; the sentence root has head 0 (Tesnière 1959; Nivre et al. 2016). Arcs are drawn
    above the sentence, arrowheads at dependents.

    **How other tools display it.** The VNLP Turkish `DependencyParser` returns
    *(index, word, head, label)* tuples and documents no built-in tree renderer; our `table()` reproduces
    that tuple view and `svg()` adds spaCy's **displaCy** drawing (`manual=True`, no model
    needed). English labels are ClearNLP/spaCy style (`dobj, prep, pobj …`), Turkish labels are
    UD (`obj, case, nmod:poss …`); `normalize_labels=True` maps English *names* to UD names
    (label-only — English still attaches objects under prepositions).

    **Function words** are *dimmed*, never deleted: deleting them would disconnect the tree.

    ### 5.2 Worked toy example: A 3-token dependency tree
    Sentence: *“Selma robotu gördü .”*
    - Tokens: `[1: Selma, 2: robotu, 3: gördü, 4: .]`
    - Heads: `[3, 3, 0, 3]` (1-based head indices; 0 is root)
    - Labels: `[nsubj, obj, root, punct]`
    - Arcs: 1 (`Selma`) → 3 (`gördü`) as subject; 2 (`robotu`) → 3 (`gördü`) as object; 3 is the sentence root.
    """),
          cheat_sheet("Dependency Visualizer Commands", [
              ("dv.sid_of(text, (ch, p, s))", "Resolves book coordinates to sequential sentence id", "sid = dv.sid_of(text, (1, 4, 4))"),
              ("dv.table(text, sid)", "Tabular representation of (id, token, lemma, pos, head, deprel)", "dv.table(text, sid)"),
              ("dv.html(text, sid)", "Renders displaCy dependency arc HTML", "dv.html(text, sid, compact=True)"),
              ("dv.svg(text, sid)", "Returns standalone SVG string suitable for file export", "svg = dv.svg(text, sid)"),
              ("dv.alignment_html(code, ai)", "Stacked bilingual trees of both English and Turkish sentences in alignment group ai", "dv.alignment_html('BR-SM', 4)"),
          ]),
          code("""
    dv = depviz.DependencyVisualizer(loader)
    en = loader.load_text("IR-IA")
    print(loader.registry.display(en))
    sid = dv.sid_of(en, (1, 4, 4))            # 'A robot may not injure a human being, …'
    display(dv.table(en, sid))
    """),
          code("""
    display(HTML(style.CSS + "<div class='ct'>" + dv.html(en, sid) + "</div>"))
    """),
          code("""
    tr = loader.load_text("BR-SM")
    print(loader.registry.display(tr))
    sid_tr = dv.sid_of(tr, (1, 2, 3))         # the Turkish rendering of the same sentence area
    display(dv.table(tr, sid_tr))
    display(HTML(style.CSS + "<div class='ct'>" + dv.html(tr, sid_tr) + "</div>"))
    """),
          md("""
    ### 5.3 An aligned group: English and Turkish trees stacked
    `alignment_html(code, ai)` draws every English sentence of alignment group `ai`, then every
    Turkish one. Use the alignment ids you saw in Chapter 3.
    """),
          code("""
    display(HTML(style.CSS + dv.alignment_html("BR-SM", 4)))
    """),
          code("""
    # raw labels instead of UD-normalised English labels, content words only highlighted
    display(HTML(style.CSS + "<div class='ct'>" + dv.html(en, sid, normalize_labels=False,
                                                       dim_function_words=True) + "</div>"))
    for t in (en, tr): t.evict()
    """),
          pitfalls(["Dimmed ≠ removed: arcs through function words are still drawn.",
                    "Parser output is *predicted*, not gold — errors are common in long sentences.",
                    "Very long sentences scroll horizontally; use `compact=True` to shrink."]),
          exercises([("Render the tree of the first sentence of *Karanlığı Taramak* and list the "
                      "root word.",
                      "```python\nt=loader.load_text('KT-OK'); s=dv.sid_of(t,(1,1,1)); "
                      "tab=dv.table(t,s); tab[tab['deprel']=='root']\n```")]),
          scholarly("""
          **Dependency Syntax and Structural Shifts in Translation (Catford 1965; Tesnière 1959):**
          English is primarily head-initial at the clausal level (SVO), while Turkish is head-final (SOV).
          Visualizing aligned dependency trees directly demonstrates Catford's *unit shifts* and
          *structure shifts*: English prepositional complements (`prep` + `pobj`) transform into
          Turkish postpositional case inflections attached directly to nouns, and English clausal
          subordinations are compressed into non-finite deverbal converbial chains.
          """),
          ]
    return c
