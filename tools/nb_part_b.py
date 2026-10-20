"""Chapters 6–9: search, KWIC concordancer, batch KWIC statistics, lexical diversity."""

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
          md("""
    **Searching with/without punctuation & in-token punctuation handling (Passim methodology):**
    VNLP-tokenized Turkish texts retain punctuation inside tokens (e.g. `Türkiye'nin`, `Fred'`, `robot-bilim`, `1882'de`),
    and this feature is also retained in lemmatized texts (`fred'`, `ay'da`, `1882'`). Four punctuation modes are supported:
    - `punct='drop'` (default): removes standalone punctuation; retains in-token punctuation.
    - `punct='keep'`: retains standalone punctuation, allowing direct searches for `?`, `!`, `,`, etc.
    - `punct='strip'`: collapses in-token punctuation without splitting (`Türkiye'nin` → `Türkiyenin`, `Fred'` → `Fred`).
    - `punct='split'`: decomposes composite tokens into sub-tokens (`Türkiye'nin` → `['türkiye', 'nin']`, `robot-bilim` → `['robot', 'bilim']`).
    Both `strip` and `split` work seamlessly on surface tokens (`tok`) and lemmatized fields (`lem`).

    **Turkish Lemma Apostrophe Remediation:**
    In raw VNLP outputs, proper nouns and hyphenated compounds retain inflectional suffixes after apostrophes in the lemma field (e.g. `Türkiye'nin` → `türkiye'nin`, `bilim-kurgu'nun` → `bilim-kurgu'nun`, `Fred'` → `fred'`). The toolkit automatically remediates this: all Turkish lemmas have sections after the apostrophe removed (e.g. `türkiye'nin` becomes `türkiye`, `bilim-kurgu'nun` becomes `bilim-kurgu`, preserving the hyphenated compound structure while stripping the case suffix `'nun`). Searches for `türkiye` or `Türkiye'nin` in `field="lem"` now resolve directly to the true base stem.
    """),
          code("""
    # 1. Search with punctuation ('keep'): find question marks
    r_punct = engine.search(search.SearchQuery(["?"], field="tok", punct="keep"), turkish)
    print("Question marks found in Turkish corpus:", len(r_punct), "hits")

    # 2. In-token punctuation: 'strip' (collapse) vs 'split' (decompose) on tokens
    r_strip = engine.search(search.SearchQuery(["Türkiyenin"], field="tok", punct="strip"), turkish)
    r_split = engine.search(search.SearchQuery(["Türkiye"], field="tok", punct="split"), turkish)
    print(f"Türkiyenin (strip): {len(r_strip)} hits;  Türkiye (split): {len(r_split)} hits")

    # 3. Clean Turkish lemmas (apostrophe suffix removed, compound hyphens preserved):
    r_lem = engine.search(search.SearchQuery(["türkiye"], field="lem"), turkish)
    print(f"Remediated Turkish lemma 'türkiye': {len(r_lem)} hits (matches all suffixed forms)")

    # 4. Lemmatized field with in-token punctuation splitting:
    r_lem_sp = engine.search(search.SearchQuery(["bilim"], field="lem", punct="split"), turkish)
    print(f"Lemma 'bilim' (split, finds inside robot-bilim): {len(r_lem_sp)} hits")
    """),

          pitfalls(["Hit counts do not change between `drop` and `mask`; **spans** do (Chapters 7, 10).",
                    "`per10k` divides by running words **of the chosen view** — a content view has a "
                    "smaller denominator, so per10k goes *up* even though hits stay equal.",
                    "In Turkish VNLP, searching for `Fred` in default `punct='drop'` mode misses `Fred'` unless "
                    "`punct='strip'` or `punct='split'` is enabled.",
                    "Regex runs on *folded* forms (lower-case) unless `case_sensitive=True`."]),
          exercises([("How often does the Turkish lemma `makine` appear *near* `robot` (±5) in "
                      "Selma Mine's indigenous novel?",
                      "```python\nr=engine.search(search.SearchQuery(['makine'],'lem',collocate=['robot'],"
                      "collocate_span=(5,5)), list(loader.load_indigenous('SM')))\nr.summary()\n```")]),
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
              ("render.show(conc, view='parallel', loader=loader)", "NDA side-by-side EN ⇄ TR sentence table with SVG links & lemmas", "render.show(conc, 'parallel', loader=loader, max_lines=4)"),
              ("render.show(conc, view='table')", "Interactive paginated (20/page), sortable, resizable table view", "render.show(conc, 'table', max_lines=20)"),
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
          md("#### View 4 — NDA side-by-side parallel view (`view='parallel'`) & View 5 — interactive paged table (`view='table'`)"),
          code("""
    render.show(conc, "parallel", loader=loader, max_lines=3)
    render.show(conc, "table", max_lines=20)
    """),
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
                      "```python\nt=[loader.load_text('IR-IA')]\nr=engine.search(search.SearchQuery(['human'],'lem'),t)\n"
                      "render.show(kwic.Concordancer().run(r,t,'L0R4').sorted('R1'),'kwic')\n```")]),
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
                      "```python\nbk.analyze(['robot','human','machine'], list(loader.load_all_english()),'lem').summary()\n```")]),
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
    show_table(div_raw.round(3), page_size=20, title="Lexical Diversity (All 13 Texts — Raw Lemmas)")
    """),
          code("""
    div_con = analysis.diversity_for(loader, loader.load_all(), field="lem", filter_function_words=True)
    show_table(div_con[["N", "V", "TTR", "STTR", "MATTR_100", "MTLD", "HD_D", "Yule_K", "Hapax_types_pct"]].round(3),
               page_size=20, title="Lexical Diversity (Content Lemmas)")
    """),
          code("""
    # token (surface) vs lemma diversity: agglutination inflates token types in Turkish
    div_tok = analysis.diversity_for(loader, loader.load_all_turkish(), field="tok")
    cmp = pd.DataFrame({"MATTR_100 (tokens)": div_tok["MATTR_100"],
                        "MATTR_100 (lemmas)": div_raw.loc[div_tok.index, "MATTR_100"]})
    display(cmp.round(3))
    """),
          code("""
    # Punctuation mode comparison: drop (standard) vs strip (collapse) vs split (retokenize)
    t_samples = [loader.load_text("BR-SM"), loader.load_text("KT-OK")]
    div_p_drop = analysis.diversity_for(loader, t_samples, field="tok", punct="drop")
    div_p_strip = analysis.diversity_for(loader, t_samples, field="tok", punct="strip")
    div_p_split = analysis.diversity_for(loader, t_samples, field="tok", punct="split")
    p_comp = pd.DataFrame({
        "N (drop)": div_p_drop["N"], "V (drop)": div_p_drop["V"],
        "N (strip)": div_p_strip["N"], "V (strip)": div_p_strip["V"],
        "N (split)": div_p_split["N"], "V (split)": div_p_split["V"],
    })
    display(p_comp)
    for s in t_samples: s.evict()
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
                      "```python\nd=div_con.reset_index(); d[d['index'].str.startswith(('SCS-OK','O-SM','SU-ZB'))].nlargest(1,'MTLD')\n```")]),
          scholarly("""
          **Translational Simplification and Lexical Repertoires (Baker 1993; Toury 2012):**
          Higher diversity in *indigenous* texts than in the same translator's *translations* is
          consistent with the **normalisation / standardisation** tendency of translated language
          (Baker 1993) — but a lexically *poorer* translation may also reflect the source's register
          (Asimov's controlled vocabulary). Always pair the metric with concordance reading.
          """),
          ]
    return c
