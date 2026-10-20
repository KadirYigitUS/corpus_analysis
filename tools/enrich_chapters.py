"""Generate enriched nb_part_b.py and nb_part_c.py with complete pedagogy."""

from pathlib import Path

HERE = Path(__file__).resolve().parent

# =====================================================================
# nb_part_b.py
# =====================================================================
part_b = '''"""Chapters 6–9: search, KWIC concordancer, batch KWIC statistics, lexical diversity."""

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

    # ------------------------------------------------------------------ Chapter 6
    c += [chapter_header(6, "The search engine", 25,
                         ["search by token, lemma, glob, regex and UPOS",
                          "require a context word (collocate constraint)",
                          "search the *content-word* view (function words hidden) and understand "
                          "`drop` vs `mask`"],
                         "Chapters 0–2", "Find every occurrence of what you are curious about."),
          md("""
    ### 6.1 Theory
    A **node** is the word you search for. Because Turkish packs inflection into suffixes,
    searching the *surface token* `robot` misses `robotlar`, `robotun`, … while searching the
    **lemma** `robot` finds them all. Four levers refine a search:

    | `SearchQuery` option | meaning | example |
    |---|---|---|
    | `terms` | one or more words (a *list* is aggregated) | `["robot", "makine"]` |
    | `field` | `'lem'` lemma / `'tok'` token | `field='tok'` |
    | `match` | `'exact'`, `'glob'` (`*`,`?`), `'regex'` | `match='glob'` with `gel*` |
    | `case_sensitive` | off by default (Turkish İ/I aware) | |
    | `pos` | UPOS filter on the node | `{"NOUN"}` (nouns only) |
    | `collocate`, `collocate_span` | require a context word within −L/+R | `collocate=["insan"], collocate_span=(5,5)` |
    | `filter_function_words`, `mode` | content-word view; `drop` or `mask` | see below |

    **Function-word-free search (from `scripts/passim_analysis`).** With
    `filter_function_words=True` determiners, pronouns, adpositions, auxiliaries, conjunctions,
    particles and interjections are hidden (Turkish also uses the morphological head guard
    `Postp, Conj, Det, Pron, Ques, Interj, Punc`). **`drop`** removes them from the sequence, so
    ±5 means five *content* words; **`mask`** keeps them in the sequence so ±5 stays five
    *running* words, but they can no longer match or collocate.

    ### 6.2 Worked toy example
    Text: “the cat saw the dog | the dog saw the cat”. Search lemma `saw` → 2 hits. With
    `collocate=['dog'], span=(1,1)` only the second sentence (“dog saw”) qualifies, because in the
    first, `dog` is two words away. (This is exactly unit-test `test_search_options`.)
    """),
          cheat_sheet("Search Query Options", [
              ("SearchQuery(['term'], field='lem')", "Lemma search (inflections aggregated)", "SearchQuery(['robot'], field='lem')"),
              ("SearchQuery(['gel*'], match='glob')", "Wildcard glob search (* for 0+, ? for 1)", "SearchQuery(['gel*'], match='glob')"),
              ("SearchQuery(['^rob'], match='regex')", "Regular expression search", "SearchQuery([r'^[a-z]+ing$'], match='regex')"),
              ("SearchQuery(['...'], pos={'NOUN'})", "Constrain match to specific UPOS tags", "SearchQuery(['robot'], pos={'NOUN'})"),
              ("SearchQuery(['...'], collocate=['...'], collocate_span=(5, 5))", "Require co-occurrence of context lemma within span", "SearchQuery(['robot'], collocate=['insan'])"),
              ("CorpusSearchEngine().search(q, texts)", "Execute search across a list of texts", "engine.search(q, texts)"),
          ]),
          code("""
    engine = search.CorpusSearchEngine()
    all_texts = list(loader.load_all())
    q = search.SearchQuery(["robot"], field="lem")
    res = engine.search(q, all_texts)
    print(q.describe())
    display(res.summary())             # hits and per10k (hits per 10 000 running words)
    display(res.hits.head(6))
    """),
          md("**Lemma vs token** — the same Turkish word with and without inflection:"),
          code("""
    turkish = list(loader.load_all_turkish())
    for field in ("tok", "lem"):
        r = engine.search(search.SearchQuery(["robot"], field=field), turkish)
        print(f"field={field}: {len(r)} hits")
    r = engine.search(search.SearchQuery(["robot*"], field="tok", match="glob"), turkish)
    print("glob robot*:", len(r), "hits;", r.hits["token"].str.lower().value_counts().head(6).to_dict())
    """),
          md("**POS and context constraints** — nouns only, near *insan* (human):"),
          code("""
    r1 = engine.search(search.SearchQuery(["robot"], "lem", pos={"NOUN"}), turkish)
    r2 = engine.search(search.SearchQuery(["robot"], "lem", pos={"NOUN"}, collocate=["insan"],
                                          collocate_span=(10, 10)), turkish)
    print(f"robot (NOUN): {len(r1)} hits;  … within ±10 of 'insan': {len(r2)} hits")
    display(r2.summary())
    """),
          md("**Regex** — Turkish forms ending in a possessive/plural pattern, English `-ing` forms:"),
          code("""
    r = engine.search(search.SearchQuery([r"^robot(lar)?(ın|un|ı)?$"], "tok", match="regex"), turkish)
    print(len(r), r.hits["token"].str.lower().value_counts().head(8).to_dict())
    en_texts = list(loader.load_all_english())
    r = engine.search(search.SearchQuery([r"^[a-z]+ing$"], "tok", match="regex", pos={"VERB"}), en_texts)
    print(len(r), r.hits["token"].str.lower().value_counts().head(8).to_dict())
    """),
          md("**Function-word-free search** — raw vs content, drop vs mask (hit counts for `robot`):"),
          code("""
    rows = []
    for fw, mode in [(False, "drop"), (True, "drop"), (True, "mask")]:
        r = engine.search(search.SearchQuery(["robot"], "lem", filter_function_words=fw, mode=mode),
                          turkish)
        s = r.summary()
        rows.append({"filter_function_words": fw, "mode": mode, "hits": s["hits"].sum(),
                     "running_words": s["running_words"].sum(),
                     "per10k": 1e4 * s["hits"].sum() / s["running_words"].sum()})
    display(pd.DataFrame(rows))
    """),
          pitfalls(["Hit counts do not change between `drop` and `mask`; **spans** do (Chapters 7, 10).",
                    "`per10k` divides by running words **of the chosen view** — a content view has a "
                    "smaller denominator, so per10k goes *up* even though hits stay equal.",
                    "Regex runs on *folded* forms (lower-case) unless `case_sensitive=True`."]),
          exercises([("How often does the Turkish lemma `makine` appear *near* `robot` (±5) in "
                      "Selma Mine's indigenous novel?",
                      "```python\\nr=engine.search(search.SearchQuery(['makine'],'lem',collocate=['robot'],"
                      "collocate_span=(5,5)), list(loader.load_indigenous('SM')))\\nr.summary()\\n```")]),
          scholarly("""
          **Node Selection and Repertoire Profiling (Sinclair 1991; Stubbs 2001):**
          In translation corpus analysis, query design determines what aspects of the lexical
          repertoire are illuminated. Lemmatised queries uncover semantic field expansion, while
          morphosyntactically constrained queries reveal target-language translation routines.
          """),
          ]

    # ------------------------------------------------------------------ Chapter 7
    c += [chapter_header(7, "KWIC concordancer", 30,
                         ["explain KWIC and choose a span", "read aligned, chip and sentence-card "
                          "views", "sort lines by the word to the left/right of the node",
                          "cross-check against NLTK"],
                         "Chapter 6", "Read the evidence, not just the counts."),
          md("""
    ### 7.1 What is KWIC?
    **KWIC = Key Word In Context.** A concordance lists *every* occurrence of a **node** word with
    the words immediately left and right of it, **aligned on the node** so recurring patterns pop out
    visually (Luhn 1960; Sinclair 1991, *Corpus, Concordance, Collocation*). Counting tells you
    *how often*; a concordance shows *how it is used*.

    ### 7.2 Choosing the span
    | spec | (L, R) | use for |
    |---|---|---|
    | `'phrase'` | (3, 3) | idioms, fixed phrases, determiner patterns |
    | `'collocation'` | (5, 5) | classic collocation window (Sinclair 1991) |
    | `'extended'` | (10, 10) | semantic prosody, topical context |
    | `'discourse'` | (20, 20) | discourse-level framing |
    | `'sentence'` | whole sentence | full context |
    | `7`, `(5, 2)`, `'L5R2'` | custom | asymmetric: *what follows?* → `(0, 4)`; *what precedes?* → `(4, 0)` |

    `sentence_clamped=True` (default) never lets a span cross a sentence boundary.

    ### 7.3 Worked toy example: Concordance lines and sorting
    Given sentences:
    1. *“The smart **robot** moved quickly .”* → L1=`smart`, node=`robot`, R1=`moved`
    2. *“A tiny **robot** spoke quietly .”* → L1=`tiny`, node=`robot`, R1=`spoke`
    - Sorting by **R1** orders: line 1 (`moved`), then line 2 (`spoke`).
    - Sorting by **L1** orders: line 1 (`smart`), then line 2 (`tiny`).
    """),
          cheat_sheet("Concordancer Commands & Views", [
              ("Concordancer().run(search_res, texts, span='collocation')", "Extracts KwicLine objects for all hits with chosen span", "conc = kwic.Concordancer().run(res, texts, span='L5R2')"),
              ("conc.sorted('R1')", "Sorts concordance lines by first word to the right (R1...R5, L1...L5)", "conc_sorted = conc.sorted('R1')"),
              ("render.show(conc, view='kwic')", "HTML aligned node view with highlighted keyword", "render.show(conc, 'kwic')"),
              ("render.show(conc, view='chips')", "Compact coordinate chips for scholarly citations (ch·p·s·tok)", "render.show(conc, 'chips')"),
              ("render.show(conc, view='cards', loader=loader)", "Sentence cards with bilingual aligned parallel sentences", "render.show(conc, 'cards', loader=loader)"),
              ("render.show(conc, view='console')", "Plain text view suitable for terminal and log inspection", "render.show(conc, 'console')"),
          ]),
          code("""
    pair_texts = [loader.load_text("IR-IA"), loader.load_text("BR-SM")]
    print(loader.registry.display(pair_texts[0]))
    print(loader.registry.display(pair_texts[1]))
    res = engine.search(search.SearchQuery(["robot"], "lem", pos={"NOUN"}), pair_texts)
    conc = kwic.Concordancer().run(res, pair_texts, span="collocation", max_lines_per_text=12)
    print(len(conc), "lines shown of", conc.total_hits, "hits")
    """),
          md("#### View 1 — aligned KWIC (node centred; badge = text type; hover for author)"),
          code("render.show(conc, 'kwic', max_lines=14)"),
          md("#### View 2 — coordinate chips (every hit is citable: chapter · paragraph · sentence · token)"),
          code("render.show(conc, 'chips', max_lines=8)"),
          md("#### View 3 — bilingual sentence cards (the aligned counterpart appears below)"),
          code("render.show(conc, 'cards', loader=loader, max_lines=4)"),
          md("#### Console view (terminal / logs)"),
          code("render.show(conc, 'console', max_lines=8)"),
          md("#### Sorting reveals patterns — by the word *right* of the node (`R1`), then *left* (`L1`)"),
          code("""
    render.show(conc.sorted("R1"), "kwic", max_lines=10)
    render.show(conc.sorted("L1"), "kwic", max_lines=10)
    """),
          md("""
    #### Spans are asymmetric and sentence-aware
    Only what *follows* the node (`'L0R4'`), then the whole sentence:
    """),
          code("""
    render.show(kwic.Concordancer().run(res, pair_texts, span="L0R4", max_lines_per_text=5), "kwic", max_lines=8)
    render.show(kwic.Concordancer().run(res, pair_texts, span="sentence", max_lines_per_text=3), "cards", loader=loader, max_lines=3)
    """),
          md("""
    #### Content-word concordance (function words dimmed)
    With `filter_function_words=True` the span counts *content* words (`drop`); dimmed words are
    shown only so the line remains readable.
    """),
          code("""
    res_c = engine.search(search.SearchQuery(["robot"], "lem", pos={"NOUN"}, filter_function_words=True, mode="drop"), pair_texts)
    conc_c = kwic.Concordancer().run(res_c, pair_texts, span=(4, 4), max_lines_per_text=8)
    render.show(conc_c, "kwic", max_lines=10)
    """),
          md("#### Cross-check with NLTK (a different, simpler algorithm)"),
          code("""
    v = TokenView(loader.load_text("IR-IA"), "tok", False)
    for line in nltk_adapter.nltk_concordance(v, "robot", width=70, lines=5):
        print(line)
    print(nltk_adapter.nltk_similar(v, "robot", 6))     # distributional neighbours
    """),
          pitfalls(["NLTK's concordance counts *all* tokens including punctuation and ignores "
                    "sentence borders — its lines will differ slightly from ours by design.",
                    "A span that reaches the sentence edge also shows the edge punctuation."]),
          exercises([("Show *only* what comes after the English lemma `human` (4 words) in "
                      "*I, Robot*, sorted by the next word.",
                      "```python\\nt=[loader.load_text('IR-IA')]\\nr=engine.search(search.SearchQuery(['human'],'lem'),t)\\n"
                      "render.show(kwic.Concordancer().run(r,t,'L0R4').sorted('R1'),'kwic')\\n```")]),
          scholarly("""
          **Qualitative Concordancing and Units of Meaning (Sinclair 1991; Luhn 1960):**
          Concordance reading is **qualitative evidence** for quantitative patterns: before claiming that
          a translator domesticates a term, read 20–30 lines in each language and note the *syntactic
          frames* (Sinclair's *unit of meaning*). Record coordinates (`ch·p·s·tok`) so every example
          in your prose is traceable.
          """),
          ]

    # ------------------------------------------------------------------ Chapter 8
    c += [chapter_header(8, "Batch KWIC: lists of words, aggregates and correlations", 30,
                         ["analyse a *list* of words at once", "compute per10k, dispersion "
                          "(Juilland's D) and chunk profiles",
                          "interpret Pearson r, Spearman ρ, cosine and FDR-corrected p-values"],
                         "Chapters 6–7", "From single words to semantic fields."),
          md("""
    ### 8.1 Theory
    Studying a *lexical field* (e.g. robot / human / machine) needs numbers that are comparable
    across texts of different length and that tell us **how evenly** a word is spread.

    1. **Normalise**: `per10k = 10 000 · hits / running words`.
    2. **Dispersion — Juilland's D** (Juilland & Chang-Rodríguez 1964; Gries 2008):
       split each text into *n = 10* equal chunks, let `V = σ/μ` of the chunk counts (population σ):
       `D = 1 − V/√(n−1)` — 1 = even, 0 = all in one chunk.
    3. **Profiles**: each word gets a vector of chunk-rates (10 per text). **Pearson r**
       (linear), **Spearman ρ** (rank, ties averaged) and **cosine** (angle) compare words.
    4. **Multiple testing**: many word pairs ⇒ many p-values; **Benjamini–Hochberg FDR**
       (1995) turns them into q-values.

    ### 8.2 Worked toy example
    Chunk rates of word *a*: [1, 2, 3, 4]; word *b*: [2, 4, 6, 8] ⇒ identical *shape*, so
    Pearson r = 1, Spearman ρ = 1, cosine = 1. Word *c*: [4, 3, 2, 1] ⇒ r = −1, cosine = 0.84.
    For counts [4, 0, 0, 0]: μ = 1, σ = √3 ⇒ V = √3 ⇒ D = 1 − √3/√3 = **0** (completely clumped).
    """),
          cheat_sheet("Batch KWIC Commands", [
              ("BatchKwicAnalyzer().analyze(words, texts, field='lem')", "Analyzes multiple terms or semantic field dict across texts", "bk.analyze(['robot', 'insan'], texts)"),
              ("result.summary()", "DataFrame of total hits, per10k frequency, and Juilland D per term", "display(out.summary())"),
              ("result.pairwise()", "Pairwise Pearson r, Spearman rho, cosine similarity, and FDR q-values", "display(out.pairwise())"),
              ("result.matrix('pearson_r')", "Square correlation matrix between term chunk profiles", "out.matrix('pearson_r')"),
          ]),
          code("""
    a, b, cvec = [1, 2, 3, 4], [2, 4, 6, 8], [4, 3, 2, 1]
    print("pearson a,b", stats.pearson(a, b)[0], "| a,c", stats.pearson(a, cvec)[0])
    print("cosine  a,c", round(stats.cosine(a, cvec), 3))
    print("Juilland D [4,0,0,0] =", round(stats.juilland_d([4, 0, 0, 0]), 6),
          "| [1,1,1,1] =", stats.juilland_d([1, 1, 1, 1]))
    """),
          md("""
    ### 8.3 Run it on Turkish texts (lemmas, raw view)
    Provide a **list** (each word separate) or a **dict** (named groups that are aggregated):
    `{"machine words": ["robot", "makine"], "human words": ["insan", "kişi"]}`.
    """),
          code("""
    bk = batch_kwic.BatchKwicAnalyzer()
    turkish = list(loader.load_all_turkish())
    words = ["robot", "insan", "makine", "bilgisayar", "uzay", "dünya"]
    out = bk.analyze(words, turkish, field="lem")
    display(out.counts); display(out.rates.round(1)); display(out.summary().round(3))
    """),
          code("""
    display(out.pairwise().round(3))
    fig = viz.heatmap(out.rates, "Rate per 10 000 running words", fmt=".0f"); plt.show()
    fig = viz.heatmap(out.matrix("pearson_r"), "Pearson r between word profiles", cmap="vlag",
                      center=0, fmt=".2f"); plt.show()
    fig = viz.chunk_dispersion({k: out.chunks[k] for k in ["robot", "insan"]}, out.codes); plt.show()
    """),
          md("**Named groups** (aggregate functions over a *KWIC list*) and the content-word view:"),
          code("""
    groups = {"machine field": ["robot", "makine", "bilgisayar"], "human field": ["insan", "kişi", "adam"]}
    g_raw = bk.analyze(groups, turkish, "lem")
    g_con = bk.analyze(groups, turkish, "lem", filter_function_words=True, mode="drop")
    display(g_raw.summary().round(3)); display(g_con.summary().round(3))
    display(g_raw.pairwise().round(3))
    """),
          pitfalls(["Chunks of one text are **autocorrelated**: p-values here are screening devices — "
                    "report r/ρ/cosine and D first.",
                    "A word absent from a text yields an all-zero profile: Pearson/Spearman return NaN, "
                    "cosine 0 — that is *correct*, not a bug.",
                    "Very short texts (*The Light*) make 10 chunks of ~400 words; D is noisy."]),
          exercises([("Compare English `robot`, `human`, `machine` across the 5 English sources.",
                      "```python\\nbk.analyze(['robot','human','machine'], list(loader.load_all_english()),'lem').summary()\\n```")]),
          scholarly("""
          **Semantic Fields and Lexical Dispersion in Peripheral Genres (Gries 2008; Juilland 1964):**
          Term frequency alone does not reveal whether a term belongs to the core generic repertoire
          or is confined to an episodic scene. Juilland's $D$ measures evenness of distribution,
          allowing researchers to distinguish canonized SF terms (high $D$) from localized coinages.
          """),
          ]

    # ------------------------------------------------------------------ Chapter 9
    c += [chapter_header(9, "Lexical richness & diversity (LancsBox-X family)", 35,
                         ["explain why raw TTR cannot compare texts of different length",
                          "compute and interpret 14+ diversity metrics",
                          "read the radar, MATTR-trajectory and Zipf figures"],
                         "Chapters 0–2", "How varied is each author's vocabulary — fairly measured?"),
          md("""
    ### 9.1 Theory: the length problem
    **TTR = types ÷ tokens** *falls* as a text grows — each new token is more likely a repeat
    (Heaps' law). So TTR of a short story and of a novel are not comparable. Modern work uses
    measures that are (approximately) length-independent: **STTR** (mean TTR of 1000-word blocks),
    **MATTR** (moving-average TTR over windows; Covington & McFall 2010), **MTLD**
    (McCarthy & Jarvis 2010), and **HD-D** (McCarthy & Jarvis 2007, 2010; hypergeometric modeling).
    *LancsBox X* (Brezina, Weill-Tessier & McEnery 2021) reports this family; we implement it from scratch.

    | metric | formula | higher means | length robust? |
    |---|---|---|---|
    | TTR | V/N | more diverse | ❌ falls with N |
    | Guiraud R | V/√N | more diverse | ❌ |
    | CTTR (Carroll) | V/√(2N) | more diverse | ❌ |
    | Herdan C | ln V / ln N | more diverse | ❌ |
    | Dugast U | ln²N / (ln N − ln V) | more diverse | ❌ |
    | Maas a² | (ln N − ln V)/ln²N | **less** diverse | ❌ |
    | Yule K | 10⁴(Σm²V_m − N)/N² | **less** diverse (repetitive) | ✅ |
    | Simpson D | Σn(n−1)/(N(N−1)) | **less** diverse | ✅ |
    | Honoré R | 100 ln N/(1 − V₁/V) | richer vocabulary | ❌ |
    | Hapax % | V₁/V, V₁/N | many one-off words | ❌ |
    | STTR (L=1000) | mean TTR of 1000-word blocks | more diverse | ✅ |
    | MATTR (w=50/100/500) | mean TTR of sliding windows | more diverse | ✅ |
    | MTLD | N / factors (TTR ≤ 0.72), mean of forward & backward | more diverse | ✅ |
    | HD-D | Σ (1 − C(N−f, 42)/C(N, 42)) / 42 (hypergeometric draw) | more diverse | ✅ |

    ### 9.2 Worked toy example
    Tokens `the cat saw the dog the dog saw the cat` (N = 10): types {the 4, cat 2, dog 2, saw 2}
    ⇒ V = 4, TTR = 0.4, Guiraud = 4/√10 = 1.26, Yule K = 10⁴(16+3·4−10)/100 = **1800**,
    Simpson D = (12+2+2+2)/90 = **0.2** — all checked in `tests/test_corpus_toolkit.py`.
    """),
          cheat_sheet("Diversity Methods", [
              ("diversity.diversity_metrics(forms)", "Dict of all 14+ LancsBox-X metrics", "diversity.diversity_metrics(forms)"),
              ("diversity.mattr(forms, window=100)", "Moving-average TTR across sliding windows", "diversity.mattr(forms, 100)"),
              ("diversity.mtld(forms, threshold=0.72)", "Mean of forward and backward MTLD factor passes", "diversity.mtld(forms)"),
              ("diversity.hdd(forms, sample_size=42)", "Hypergeometric HD-D sampling expectation", "diversity.hdd(forms)"),
              ("analysis.diversity_for(loader, texts, field='lem')", "Cached summary table across multiple texts", "analysis.diversity_for(loader, texts)"),
          ]),
          md("#### 9.3 See the length problem with your own eyes"),
          code("""
    text = loader.load_text("IR-IA")
    print(loader.registry.display(text))
    forms = TokenView(text, "lem", False).analysed()
    sizes = np.unique(np.linspace(500, len(forms), 14).astype(int))
    rows = [{"N": n, "TTR": diversity.ttr(forms[:n]),
             "MATTR_100": diversity.mattr(forms[:n], 100), "MTLD": diversity.mtld(forms[:n])}
            for n in sizes]
    df = pd.DataFrame(rows).set_index("N")
    ax = df[["TTR", "MATTR_100"]].plot(marker="o", figsize=(7, 4), title="TTR collapses with length; MATTR does not")
    plt.show(); display(df.round(3).T)
    text.evict()
    """),
          md("#### 9.4 Diversity of all 13 texts (lemmas, raw view) — cached after the first run"),
          code("""
    div_raw = analysis.diversity_for(loader, loader.load_all(), field="lem", filter_function_words=False)
    display(div_raw.round(3))
    """),
          code("""
    div_con = analysis.diversity_for(loader, loader.load_all(), field="lem", filter_function_words=True)
    display(div_con[["N", "V", "TTR", "STTR", "MATTR_100", "MTLD", "HD_D", "Yule_K", "Hapax_types_pct"]].round(3))
    """),
          code("""
    # token (surface) vs lemma diversity: agglutination inflates token types in Turkish
    div_tok = analysis.diversity_for(loader, loader.load_all_turkish(), field="tok")
    cmp = pd.DataFrame({"MATTR_100 (tokens)": div_tok["MATTR_100"],
                        "MATTR_100 (lemmas)": div_raw.loc[div_tok.index, "MATTR_100"]})
    display(cmp.round(3))
    """),
          md("#### 9.5 Figures: radar, MATTR trajectory, Zipf"),
          code("""
    fig = viz.diversity_radar(div_raw.loc[[i for i in div_raw.index if i.split(' · ')[0] in
                                           ('IR-IA','BR-SM','O-SM','ASD-PKD','KT-OK','SCS-OK')]]); plt.show()
    sel = [loader.load_text(c) for c in ("IR-IA", "BR-SM", "O-SM")]
    for s in sel: print(loader.registry.display(s))
    traj = analysis.mattr_trajectories_for(sel, window=500)
    fig = viz.mattr_trajectories(traj, 500); plt.show()
    fig = viz.zipf_plot(analysis.zipf_for(sel)); plt.show()
    for s in sel: s.evict()
    """),
          pitfalls(["`STTR` falls back to TTR (with a warning) when N < 1000; `MATTR` falls back when N < w. "
                    "*The Light* (≈ 4 000 words) is on the edge — treat it cautiously.",
                    "Dugast/Honoré are undefined (NaN) when V = N or V₁ = V.",
                    "Compare **lemma views with lemma views** and **raw with raw**."]),
          exercises([("Which indigenous novel has the highest MTLD (lemmas, content view)?",
                      "```python\\nd=div_con.reset_index(); d[d['index'].str.startswith(('SCS-OK','O-SM','SU-ZB'))].nlargest(1,'MTLD')\\n```")]),
          scholarly("""
          **Translational Simplification and Lexical Repertoires (Baker 1993; Toury 2012):**
          Higher diversity in *indigenous* texts than in the same translator's *translations* is
          consistent with the **normalisation / standardisation** tendency of translated language
          (Baker 1993) — but a lexically *poorer* translation may also reflect the source's register
          (Asimov's controlled vocabulary). Always pair the metric with concordance reading.
          """),
          ]
    return c
'''

Path(HERE / "nb_part_b.py").write_text(part_b, encoding="utf-8")
print("Wrote enriched nb_part_b.py")


# =====================================================================
# nb_part_c.py
# =====================================================================
part_c = '''"""Chapters 10–13 + references: collocations, TF-IDF, reporter, explorer."""

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

    # ----------------------------------------------------------------- Chapter 10
    c += [chapter_header(10, "Collocations & association measures", 35,
                         ["build the 2×2 contingency table of node and collocate",
                          "compute MI, MI², MI³, T-score, log-likelihood (G²) and Log-Dice by hand",
                          "tell strength from evidence (GraphColl-style scatter plot)",
                          "understand union-slot window counting vs pairwise co-occurrence"],
                         "Chapters 6–7", "Which words keep company with the node significantly more than chance predicts?"),
          md("""
    ### 10.1 Theory
    Firth (1957): *“You shall know a word by the company it keeps.”* Fix a **node** and a window
    (left $L$, right $R$). With:

    - $N$: total running words in corpus / text,
    - $R_1$: window **slots** (positions covered by any node window, node itself excluded).
      In our toolkit, overlapping windows count each position **once** (union slots), guaranteeing
      $O_{11} \\le R_1$ and $O_{11} \\le C_1$ without double-counting words situated between two close nodes.
    - $C_1$: total frequency of the candidate collocate across the text,
    - $O_{11}$: observed count of the candidate word *inside* the node's window slots,
    - $E_{11} = \\frac{R_1 \\cdot C_1}{N}$: expected co-occurrence count under independent random distribution,

    the $2 \\times 2$ contingency table is:

    | | In window ($W$) | Outside window ($\\neg W$) | Total |
    |---|---|---|---|
    | **Candidate ($C$)** | $O_{11}$ | $O_{12} = C_1 - O_{11}$ | $C_1$ |
    | **Other tokens ($\\neg C$)** | $O_{21} = R_1 - O_{11}$ | $O_{22} = N - R_1 - C_1 + O_{11}$ | $N - C_1$ |
    | **Total** | $R_1$ | $N - R_1$ | $N$ |

    The standard association measures:

    | Measure | Formula | Favours / Properties |
    |---|---|---|
    | **MI** (Church & Hanks 1990) | $\\log_2 \\frac{O_{11}}{E_{11}}$ | Strength of attraction; strongly favours low-frequency words |
    | **MI²** (Daille 1994) | $\\log_2 \\frac{O_{11}^2}{E_{11}}$ | Intermediate; tempers low-frequency bias |
    | **MI³** (Daille 1994) | $\\log_2 \\frac{O_{11}^3}{E_{11}}$ | Strong and frequent recurrent pairs |
    | **T-score** (Church et al. 1991) | $\\frac{O_{11} - E_{11}}{\\sqrt{O_{11}}}$ | Certainty / evidence; favours frequent grammatical partners |
    | **G²** (Dunning 1993) | $2 \\sum_{i,j} O_{ij} \\ln \\frac{O_{ij}}{E_{ij}}$ | Signed likelihood ratio test; positive = attraction, negative = repulsion |
    | **Log-Dice** (Rychlý 2008) | $14 + \\log_2 \\frac{2 O_{11}}{f_{\\text{node}} + C_1}$ | Corpus-size independent; maximum 14 for perfect co-occurrence |

    **Strength vs Evidence (GraphColl, Brezina et al. 2015).** MI measures *effect size* (strength),
    while $G^2$ measures *statistical evidence* (sample size / certainty). A scatter plot of MI vs $G^2$
    reveals four distinct quadrants: rare exclusive partners (high MI, low $G^2$), central topical
    collocates (high MI, high $G^2$), grammatical collocations (low MI, high $G^2$), and noise.

    ### 10.2 Worked toy example (hand-checkable)
    Given: $N = 1000$, $R_1 = 100$, $C_1 = 20$, $O_{11} = 10$, $f_{\\text{node}} = 50$:
    1. $E_{11} = \\frac{100 \\times 20}{1000} = 2.0$
    2. $\\text{MI} = \\log_2(10 / 2) = \\log_2(5) \\approx 2.322$
    3. $\\text{MI}^2 = \\log_2(100 / 2) = \\log_2(50) \\approx 5.644$
    4. $\\text{MI}^3 = \\log_2(1000 / 2) = \\log_2(500) \\approx 8.966$
    5. $\\text{T-score} = \\frac{10 - 2}{\\sqrt{10}} = \\frac{8}{3.1623} \\approx 2.530$
    6. $\\text{Log-Dice} = 14 + \\log_2 \\left(\\frac{20}{50 + 20}\\right) = 14 + \\log_2(0.2857) = 14 - 1.8074 \\approx 12.193$
    """),
          cheat_sheet("Collocation Commands", [
              ("collocation.association_table([o11], [c1], r1, n, f_node)", "Compute all 6 association measures for given contingency counts", "collocation.association_table([10], [20], 100, 1000, 50)"),
              ("collocation.collocates(view, 'node', left=5, right=5, min_freq=5)", "Extract collocates table sorted by G2/MI/LogDice", "collocation.collocates(view, 'robot', 5, 5, min_freq=5, sort_by='G2')"),
              ("viz.collocation_scatter(tab, 'node', x='MI', y='G2')", "Plot strength (MI) vs evidence (G2) scatter graph", "viz.collocation_scatter(tab, 'robot')"),
              ("TokenView(text, 'lem', filter_function_words=True, mode='drop')", "Content-word view for topical collocations", "TokenView(text, 'lem', True, 'drop')"),
              ("nltk_adapter.nltk_collocations(view, n=10, min_freq=5)", "Cross-check with NLTK bigram association measures", "nltk_adapter.nltk_collocations(view)"),
          ]),
          code("""
    # Hand-checked toy example verification
    toy = collocation.association_table([10], [20], r1=100, n=1000, f_node=50)
    display(toy.round(3))
    """),
          code("""
    # Extract collocations for 'robot' in Selma Mine's translation of I, Robot
    br = loader.load_text("BR-SM")
    print("Analyzing:", loader.registry.display(br))
    node_view = TokenView(br, "lem", False, "drop")
    tab = collocation.collocates(node_view, "robot", left=5, right=5, min_freq=5, sort_by="G2")
    print("Contingency parameters:", tab.attrs)
    display(tab.head(12).round(2))
    """),
          code("""
    # GraphColl-style strength vs evidence visualization
    fig = viz.collocation_scatter(tab, "robot", x="MI", y="G2")
    plt.show()

    # Compare top partners ranked by different association measures
    for measure in ("MI", "T", "LogDice", "G2"):
        top_words = tab.sort_values(measure, ascending=False)["collocate"].head(8).tolist()
        print(f"{measure:8s} → {top_words}")
    """),
          md("""
    #### Spans, clamping and the content-word view
    The window is a parameter of the *research question*:
    - Narrow spans ($\\pm 1, \\pm 2$) capture **morphosyntax** and immediate valency (prepositions, auxiliary verbs, modifiers).
    - Wider spans ($\\pm 5, \\pm 10$) capture **thematic/discourse** associations.
    - With function words filtered, **`drop`** measures distance in *content words*, while **`mask`** keeps running positions intact.
    """),
          code("""
    def top_collocates(view, left, right, sort_by="G2"):
        res = collocation.collocates(view, "robot", left=left, right=right, min_freq=5, sort_by=sort_by)
        return res["collocate"].head(8).tolist()

    print("Raw span ±2     :", top_collocates(TokenView(br, "lem", False), 2, 2))
    print("Raw span ±10    :", top_collocates(TokenView(br, "lem", False), 10, 10))
    print("Content 'drop'  :", top_collocates(TokenView(br, "lem", True, "drop"), 5, 5))
    print("Content 'mask'  :", top_collocates(TokenView(br, "lem", True, "mask"), 5, 5))
    """),
          md("#### Cross-check: NLTK bigram collocations (adjacent pairs)"),
          code("""
    display(nltk_adapter.nltk_collocations(TokenView(br, "lem", True), n=10, min_freq=5, measure="likelihood_ratio"))
    display(nltk_adapter.top_ngrams(TokenView(br, "lem", True), n=2, top=8))
    br.evict()
    """),
          pitfalls(["Character names (*Susan Calvin*, *Mike Donovan*) dominate raw collocations: filter out proper nouns (`exclude_pos={'PROPN'}`) to surface thematic vocabulary.",
                    "Window slots are counted once per position (union slots): this prevents overlapping windows from counting the same token twice, ensuring $O_{11} \\le C_1$.",
                    "$G^2$ is signed: negative values indicate repulsion (words that co-occur *less* frequently than chance expects)."]),
          exercises([("Which English lemmas collocate with `human` (±4) in Isaac Asimov's *I, Robot* by Log-Dice?",
                      "```python\\nir = loader.load_text('IR-IA')\\nprint(loader.registry.display(ir))\\nv = TokenView(ir, 'lem', True)\\ndisplay(collocation.collocates(v, 'human', 4, 4, min_freq=3, sort_by='LogDice').head(10))\\nir.evict()\\n```")]),
          scholarly("""
          **Firthian Semantics and Repertoire Modeling (Firth 1957; Sinclair 1991):**
          In polysystem theory (Even-Zohar 1990), collocational profiles reveal whether translated
          texts import foreign lexical combinations (*calques*, e.g., *pozitronik beyin*) or adapt
          to indigenous target repertoire patterns. Log-Dice (Rychlý 2008) provides an ideal metric
          for comparing author-translators across different text lengths because it is invariant to
          total corpus token count.
          """),
          ]

    # ----------------------------------------------------------------- Chapter 11
    c += [chapter_header(11, "TF-IDF keyness", 20,
                         ["compute TF-IDF by hand and verify identical output with scikit-learn",
                          "fit English and Turkish subcorpora separately",
                          "read keyness heatmaps and isolate genre vocabulary by excluding proper nouns"],
                         "Chapters 0–2", "Which words characterise each text in the corpus?"),
          md("""
    ### 11.1 Theory
    TF-IDF (Spärck Jones 1972) weights words by multiplying within-document frequency (**TF**)
    with across-corpus distinctiveness (**IDF**). In our implementation (matching scikit-learn):

    - **Sublinear TF**: $\\text{TF}(t, d) = 1 + \\ln(\\text{count}(t, d))$ for $\\text{count} > 0$ (diminishing returns of repetition).
    - **Smooth IDF**: $\\text{IDF}(t) = \\ln\\left(\\frac{1 + N}{1 + \\text{DF}(t)}\\right) + 1$, where $N$ is total documents and $\\text{DF}(t)$ is document frequency.
    - **L2 Normalisation**: $\\vec{v}_{\\text{norm}} = \\frac{\\vec{v}}{\\|\\vec{v}\\|_2}$ ensures document length does not distort keyness.

    Because English and Turkish possess fundamentally distinct morphological structures and vocabularies,
    they are fitted as **separate subcorpora**.

    ### 11.2 Worked toy example — hand calculation vs scikit-learn
    Three documents: $d_1 = [a, b, b]$, $d_2 = [a, c]$, $d_3 = [c, c, d]$ ($N = 3$).
    - $a$: in $d_1, d_2$ $\\Rightarrow \\text{DF} = 2 \\Rightarrow \\text{IDF} = \\ln(4/3) + 1 \\approx 1.2877$
    - $b$: in $d_1$ $\\Rightarrow \\text{DF} = 1 \\Rightarrow \\text{IDF} = \\ln(4/2) + 1 = \\ln(2) + 1 \\approx 1.6931$
    - $c$: in $d_2, d_3$ $\\Rightarrow \\text{DF} = 2 \\Rightarrow \\text{IDF} = \\ln(4/3) + 1 \\approx 1.2877$
    - $d$: in $d_3$ $\\Rightarrow \\text{DF} = 1 \\Rightarrow \\text{IDF} = \\ln(4/2) + 1 = \\ln(2) + 1 \\approx 1.6931$

    In $d_1$: $\\text{tf}(a) = 1 + \\ln(1) = 1.0$; $\\text{tf}(b) = 1 + \\ln(2) \\approx 1.6931$.
    Unnormalized: $w(a) = 1.0 \\times 1.2877 = 1.2877$; $w(b) = 1.6931 \\times 1.6931 \\approx 2.8667$.
    L2 norm: $\\sqrt{1.2877^2 + 2.8667^2} = \\sqrt{1.6582 + 8.2180} = 3.1427$.
    Normalized $d_1$: $a \\approx 0.410$, $b \\approx 0.912$.
    """),
          cheat_sheet("TF-IDF Analyzer Commands", [
              ("tfidf.tfidf_manual(docs)", "Compute sublinear smooth TF-IDF table from token lists", "tfidf.tfidf_manual([['a', 'b'], ['b', 'c']])"),
              ("tfidf.TfidfAnalyzer()", "Initialize corpus TF-IDF analyzer", "analyzer = tfidf.TfidfAnalyzer()"),
              ("analyzer.fit(texts, field='lem', filter_function_words=True)", "Fit subcorpus and compute document keyness vectors", "res = analyzer.fit(texts, 'lem', True)"),
              ("res.top_terms(doc_id, n=10)", "Extract top n key terms for a specific text", "res.top_terms('BR-SM', 10)"),
              ("res.dense_top(top_k=5)", "Extract dense DataFrame of top terms across all documents", "res.dense_top(5)"),
              ("viz.heatmap(df, title)", "Plot keyness heatmap across documents", "viz.heatmap(matrix, 'Keyness')"),
          ]),
          code("""
    # Hand calculation verification matching scikit-learn exactly
    docs = [["a", "b", "b"], ["a", "c"], ["c", "c", "d"]]
    manual = tfidf.tfidf_manual(docs)
    display(manual.round(3))

    from sklearn.feature_extraction.text import TfidfVectorizer
    skl = TfidfVectorizer(analyzer=lambda x: x, sublinear_tf=True).fit_transform(docs).toarray()
    print("Exact match with scikit-learn:", np.allclose(skl, manual[sorted(manual.columns)].to_numpy()))
    """),
          code("""
    # Fit English and Turkish subcorpora separately
    T = tfidf.TfidfAnalyzer()
    en = T.fit(loader.load_all_english(), "lem", filter_function_words=True)
    tr = T.fit(loader.load_all_turkish(), "lem", filter_function_words=True)

    print("--- Top English Distinctive Lemmas ---")
    for d in en.doc_ids[:3]:
        full_title = loader.registry.title_of(d)
        print(f"{d} ({full_title}): {en.top_terms(d, 6)['term'].tolist()}")

    print()
    print("--- Top Turkish Distinctive Lemmas ---")
    for d in tr.doc_ids[:3]:
        full_title = loader.registry.title_of(d)
        print(f"{d} ({full_title}): {tr.top_terms(d, 6)['term'].tolist()}")
    """),
          md("""
    As observed, **character proper names** (*Powell*, *Donovan*, *Arctor*) dominate keyness.
    To uncover the **thematic and lexical repertoire**, we exclude proper nouns (`exclude_pos={'PROPN'}`):
    """),
          code("""
    tr_np = T.fit(loader.load_all_turkish(), "lem", filter_function_words=True, exclude_pos={"PROPN"})
    fig = viz.heatmap(tr_np.dense_top(5).T, "TF-IDF Keyness (Turkish SF Texts, Names Excluded)",
                      cmap="mako_r", fmt=".2f", annotate=False)
    plt.show()

    for d in tr_np.doc_ids:
        print(f"{d:8s} ({loader.registry.title_of(d)[:30]}...) → {tr_np.top_terms(d, 6)['term'].tolist()}")
    """),
          md("""
    With small document counts (5 English / 8 Turkish novels), IDF is coarse. Chunking texts
    into smaller sections (`n_chunks=5`) simulates a larger library for exploratory tracking:
    """),
          code("""
    ch = T.fit(loader.load_all_turkish(), "lem", filter_function_words=True, n_chunks=5, exclude_pos={"PROPN"})
    print(f"Generated {len(ch.doc_ids)} chunked documents.")
    print("First chunk of BR-SM (Ben, Robot):", ch.top_terms("BR-SM#1", 6)["term"].tolist())
    """),
          pitfalls(["Words appearing in every document get IDF ≈ 1.0 and low keyness weight — by design.",
                    "TF-IDF is an exploratory weighting metric, not a hypothesis test: use $G^2$ keyness when claiming statistically significant divergence between corpora."]),
          exercises([("What are the 8 most distinctive English lemmas of Philip K. Dick's *A Scanner Darkly* (names excluded)?",
                      "```python\\nr = T.fit(loader.load_all_english(), 'lem', True, exclude_pos={'PROPN'})\\ndisplay(r.top_terms('ASD-PKD', 8))\\n```")]),
          scholarly("""
          **Keyword Analysis in Corpus Stylistics (Spärck Jones 1972; Scott 1997):**
          In translation studies, keyword profiling differentiates authorial style from translator
          habitus (Simeoni 1998). Filtering proper nouns isolates the *novum* (Suvin 1979) and
          techno-scientific vocabulary imported through translation.
          """),
          ]

    # ----------------------------------------------------------------- Chapter 12
    c += [chapter_header(12, "The reporter", 15,
                         ["collect tables and figures into a reproducible report",
                          "inspect outputs under `data/corpus_analysis/…`",
                          "generate data-grounded automatic summaries following the Three-Tier Rule"],
                         "Chapters 0–11", "Generating auditable, publication-ready research outputs."),
          md("""
    ### 12.1 Reproducible research and provenance
    Every empirical claim in a digital humanities thesis must be grounded in an auditable data pipeline.
    The `CorpusReporter` automatically saves structured outputs into dedicated directories outside version control:

    ```
    data/corpus_analysis/
    ├── .cache/     derived Parquet token tables (atomic, bounded LRU)
    ├── reports/    <run_name>_<timestamp>.md (+ formatted Excel workbook .xlsx)
    ├── tables/     every analysis table saved as UTF-8 TSV
    └── figures/    every plot exported as high-resolution 300-DPI PNG
    ```

    **Strict Data-Evidence Contract:** The reporter's `top_bottom_summary` calculates exact statistical
    extrema directly from DataFrames. It never generates speculative or ungrounded prose.
    """),
          cheat_sheet("CorpusReporter Commands", [
              ("reporter.CorpusReporter(config, registry, run_name='...')", "Initialize reporter session with metadata tracking", "rep = reporter.CorpusReporter(loader.config, loader.registry, 'my_run')"),
              ("rep.note(key=value)", "Log provenance parameters (span, field, filters)", "rep.note(field='lem', span='phrase')"),
              ("rep.add_section('Title', 'Markdown text')", "Add descriptive markdown section", "rep.add_section('POS Analysis', 'Overview...')"),
              ("rep.add_table('name', df, caption='...')", "Save TSV table and add to report + Excel", "rep.add_table('diversity', df, caption='Table 1')"),
              ("rep.add_figure('name', fig, caption='...')", "Save 300-DPI PNG and link in report", "rep.add_figure('radar', fig, caption='Figure 1')"),
              ("rep.add_summary(reporter.top_bottom_summary(df, col, id_col))", "Add data-grounded mathematical summary", "rep.add_summary(reporter.top_bottom_summary(df, 'MTLD', 'pair'))"),
              ("rep.finalize()", "Compile Markdown report and multi-sheet Excel workbook", "report_path = rep.finalize()"),
              ("analysis.standard_report(loader, run_name='...')", "One-liner standard pipeline report (Inventory, Alignment, POS, Diversity)", "analysis.standard_report(loader, 'std')"),
          ]),
          code("""
    # Build a comprehensive empirical report
    rep = reporter.CorpusReporter(loader.config, loader.registry, run_name="notebook_demo")
    rep.note(field="lem", function_words="filtered", span="sentence-clamped")

    # Add Alignment Section
    rep.add_section("Sentence Alignment Structure", "Cross-lingual alignment distribution across 5 parallel pairs.")
    rep.add_table("alignment_summary", summary.round(3), caption="Sentence alignment counts and proportions.")
    rep.add_figure("alignment_stacked", viz.alignment_stacked(summary), caption="Figure 1: Alignment category proportions.")
    rep.add_summary(reporter.top_bottom_summary(summary, "R_sent", "pair"))

    # Add Lexical Diversity Section
    rep.add_section("Lexical Diversity Analysis", "LancsBox-X 14-metric battery evaluated on Turkish texts.")
    rep.add_table("diversity_raw", div_raw.round(3), caption="Raw token diversity metrics across Turkish corpus.", index=True)
    rep.add_summary(reporter.top_bottom_summary(div_raw.reset_index(), "MTLD", "index"))

    # Finalize report (writes Markdown, TSVs, PNGs, and Excel workbook)
    report_path = rep.finalize()
    print("Report written to:", report_path)
    """),
          code("""
    # Preview generated Markdown report
    content = report_path.read_text(encoding="utf-8")
    print(content[:1500])
    """),
          md("#### The one-liner standard report (Inventory, Alignment, POS, Diversity):"),
          code("""
    std_path = analysis.standard_report(loader, run_name="standard_run")
    print("Standard report generated at:", std_path)
    """),
          pitfalls(["Re-running reports with identical run names without timestamping can overwrite previous runs: keep default timestamping enabled.",
                    "Ensure Excel workbooks (.xlsx) are closed in spreadsheet software before re-finalizing to avoid file lock errors."]),
          exercises([("Inspect the sheets of the generated Excel workbook using pandas.",
                      "```python\\nimport pandas as pd\\nxlsx_path = report_path.with_suffix('.xlsx')\\nprint('Excel sheets:', pd.ExcelFile(xlsx_path).sheet_names)\\n```")]),
          scholarly("""
          **Computational Reproducibility and Audit Trails (Peng 2011):**
          Modern digital humanities requires that statistical claims be verifiable down to the
          underlying token and alignment offsets. By storing raw tables in TSV and Excel alongside
          high-resolution figures, the reporter ensures full transparency for thesis defense and peer review.
          """),
          ]

    # ----------------------------------------------------------------- Chapter 13
    c += [chapter_header(13, "Interactive explorer", 15,
                         ["drive search, concordance, and collocates from an interactive widget panel",
                          "use `quick_search` as the headless scripting equivalent",
                          "manage memory by explicitly clearing and evicting cached texts"],
                         "Chapters 6–10", "A unified exploratory instrument for corpus hermeneutics."),
          md("""
    ### 13.1 The unified corpus explorer panel
    The interactive widget panel connects every toolkit capability into a single responsive GUI.
    Each control maps directly to the functional API parameters explored across previous chapters:

    - **Corpus / Category**: Filters texts by parallel translations, author-translator pairs, or indigenous novels.
    - **Author**: Restricts scope to a specific author-translator (`Selma MİNE`, `Zühtü BAYAR`, `Özlem KURDOĞLU`).
    - **Words**: Comma-separated query terms (aggregated search).
    - **Field**: Lemma (`lem`) vs surface token (`tok`).
    - **Match**: Exact match, wildcard glob (`*`), or regular expression.
    - **Filter Function Words**: Toggles content-word analysis (`drop` vs `mask`).
    - **Span**: Phrase, sentence, or symmetric window ($\\pm L / \\pm R$).
    - **View**: Concordance (`kwic`, `sentence`, `table`) or statistical `summary`.
    """),
          cheat_sheet("Interactive Explorer Commands", [
              ("explorer.CorpusExplorerUI(loader).show()", "Render interactive ipywidgets search and concordance panel", "ui = explorer.CorpusExplorerUI(loader); ui.show()"),
              ("explorer.quick_search(loader, ['word'], ...)", "Headless, scriptable equivalent returning DataFrame", "quick_search(loader, ['robot'], author='Selma Mine')"),
              ("loader.evict_all()", "Evict all loaded text tables from memory", "loader.evict_all()"),
          ]),
          code("""
    # Launch interactive widget panel (falls back gracefully in headless CI)
    try:
        from corpus_toolkit import explorer
        ui = explorer.CorpusExplorerUI(loader)
        ui.show()
    except Exception as exc:
        print("Interactive widgets unavailable in headless mode:", exc)
    """),
          md("### 13.2 Headless scriptable equivalent: `quick_search`"),
          code("""
    # Scriptable search across Selma Mine's texts for 'robot' as noun
    from corpus_toolkit.explorer import quick_search
    qs_res = quick_search(loader, ["robot"], category="Author-translator related texts",
                          author="Selma Mine", field="lem", pos={"NOUN"},
                          span="phrase", view="kwic", max_lines=6)
    display(qs_res)
    """),
          code("""
    # Explicit memory cleanup: evict all tables after exploration
    loader.evict_all()
    print("Memory clean: all cached text tables evicted.")
    """),
          pitfalls(["Interactive widgets require an active Jupyter notebook environment with `ipywidgets` installed and enabled.",
                    "Iterative browsing can accumulate multiple texts in RAM: call `loader.evict_all()` periodically during extended exploratory sessions."]),
          exercises([("Execute a quick search for `uzay` (space) across all Turkish translations and inspect the first 5 hits.",
                      "```python\\nfrom corpus_toolkit.explorer import quick_search\\nres = quick_search(loader, ['uzay'], category='Turkish translations', field='lem', view='kwic', max_lines=5)\\ndisplay(res)\\n```")]),
          scholarly("""
          **Exploratory Data Analysis and Hermeneutic Inquiry (Tukey 1977; Rockwell & Sinclair 2016):**
          In digital literary studies, computer-assisted reading does not replace close reading;
          it orchestrates a dialectic between macro-analytic distant reading and micro-analytic
          textual interpretation (*Hermeneutica*).
          """),
          md("""
    ---
    ## 📚 References
    - Baker, M. (1993). Corpus linguistics and translation studies: Implications and applications. In M. Baker, G. Francis, & E. Tognini-Bonelli (Eds.), *Text and Technology: In Honour of John Sinclair* (pp. 233–250). John Benjamins.
    - Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: A practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society: Series B (Methodological)*, 57(1), 289–300.
    - Biber, D. (1988). *Variation across speech and writing*. Cambridge University Press.
    - Bourdieu, P. (1993). *The Field of Cultural Production: Essays on Art and Literature*. Columbia University Press.
    - Brezina, V., McEnery, T., & Wattam, S. (2015). Collocations in context: A new perspective on collocation networks. *International Journal of Corpus Linguistics*, 20(2), 139–173.
    - Brezina, V., Weill-Tessier, P., & McEnery, T. (2021). *#LancsBox v. 6.0* [Computer software]. Lancaster University.
    - Church, K. W., & Hanks, P. (1990). Word association norms, mutual information, and lexicography. *Computational Linguistics*, 16(1), 22–29.
    - Church, K. W., Gale, W., Hanks, P., & Hindle, D. (1991). Using statistics in lexical analysis. In U. Zernik (Ed.), *Lexical Acquisition: Exploiting On-Line Resources to Build a Lexicon* (pp. 115–164). Lawrence Erlbaum.
    - Covington, M. A., & McFall, J. D. (2010). Cutting the Gordian knot: The Moving-Average Type–Token Ratio (MATTR). *Journal of Quantitative Linguistics*, 17(2), 94–100.
    - Daille, B. (1994). *Approche mixte pour l'extraction de terminologie: statistique et linguistique* [Doctoral dissertation, Université Paris 7].
    - Dugast, D. (1979). *Vocabulaire et stylistique: II. Les indices de richesse lexicale et leurs applications*. Slatkine.
    - Dunning, T. (1993). Accurate methods for the statistics of surprise and coincidence. *Computational Linguistics*, 19(1), 61–74.
    - Even-Zohar, I. (1990). Polysystem studies. *Poetics Today*, 11(1), 1–268.
    - Firth, J. R. (1957). A synopsis of linguistic theory, 1930–1955. In *Studies in Linguistic Analysis* (pp. 1–32). Philological Society.
    - Gries, S. T. (2008). Dispersions and adjusted frequencies in corpora. *International Journal of Corpus Linguistics*, 13(4), 403–437.
    - Guiraud, P. (1954). *Les caractères statistiques du vocabulaire*. Presses Universitaires de France.
    - Herdan, G. (1960). *Type-token mathematics: A textbook of mathematical linguistics*. Mouton.
    - Honoré, A. (1979). Some simple measures of richness of vocabulary. *ALLC Bulletin*, 7(2), 172–177.
    - Juilland, A., & Chang-Rodríguez, E. (1964). *Frequency dictionary of Spanish words*. Mouton.
    - Luhn, H. P. (1960). Key word-in-context index for technical literature (KWIC index). *American Documentation*, 11(4), 288–295.
    - Maas, H. D. (1972). Über den Zusammenhang zwischen Wortschatzumfang und Länge eines Textes. *Zeitschrift für Literaturwissenschaft und Linguistik*, 2(8), 73–96.
    - McCarthy, P. M., & Jarvis, S. (2010). MTLD, vocd-D, and HD-D: A validation study of sophisticated approaches to lexical diversity assessment. *Behavior Research Methods*, 42(2), 381–392.
    - Nivre, J., et al. (2016). Universal Dependencies v1: A multilingual treebank collection. *Proceedings of LREC 2016*, 1659–1666.
    - Peng, R. D. (2011). Reproducible research in computational science. *Science*, 334(6060), 1226–1227.
    - Rockwell, G., & Sinclair, S. (2016). *Hermeneutica: Computer-assisted interpretation in the humanities*. MIT Press.
    - Rychlý, P. (2008). A lexicographer-friendly association score. *Proceedings of Recent Advances in Slavonic Natural Language Processing (RASLAN 2008)*, 6–9.
    - Simeoni, D. (1998). The pivotal status of the translator's habitus. *Target: International Journal of Translation Studies*, 10(1), 1–39.
    - Simpson, E. H. (1949). Measurement of diversity. *Nature*, 163, 688.
    - Sinclair, J. (1991). *Corpus, Concordance, Collocation*. Oxford University Press.
    - Spärck Jones, K. (1972). A statistical interpretation of term specificity and its application in retrieval. *Journal of Documentation*, 28(1), 11–21.
    - Suvin, D. (1979). *Metamorphoses of Science Fiction: On the Poetics and History of a Literary Genre*. Yale University Press.
    - Toury, G. (2012). *Descriptive Translation Studies – and beyond* (2nd ed.). John Benjamins.
    - Tukey, J. W. (1977). *Exploratory Data Analysis*. Addison-Wesley.
    - Yule, G. U. (1944). *The Statistical Study of Literary Vocabulary*. Cambridge University Press.

    <sub>*All citations logged in the thesis research truth table (`chapter_count_truth_table.tsv`).*</sub>
    """),
          ]
    return c
'''

Path(HERE / "nb_part_c.py").write_text(part_c, encoding="utf-8")
print("Wrote enriched nb_part_c.py")

