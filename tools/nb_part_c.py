"""Chapters 10–13 + references: collocations, TF-IDF, reporter, explorer."""

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
      $O_{11} \le R_1$ and $O_{11} \le C_1$ without double-counting words situated between two close nodes.
    - $C_1$: total frequency of the candidate collocate across the text,
    - $O_{11}$: observed count of the candidate word *inside* the node's window slots,
    - $E_{11} = \frac{R_1 \cdot C_1}{N}$: expected co-occurrence count under independent random distribution,

    the $2 \times 2$ contingency table is:

    | | In window ($W$) | Outside window ($\neg W$) | Total |
    |---|---|---|---|
    | **Candidate ($C$)** | $O_{11}$ | $O_{12} = C_1 - O_{11}$ | $C_1$ |
    | **Other tokens ($\neg C$)** | $O_{21} = R_1 - O_{11}$ | $O_{22} = N - R_1 - C_1 + O_{11}$ | $N - C_1$ |
    | **Total** | $R_1$ | $N - R_1$ | $N$ |

    The standard association measures:

    | Measure | Formula | Favours / Properties |
    |---|---|---|
    | **MI** (Church & Hanks 1990) | $\log_2 \frac{O_{11}}{E_{11}}$ | Strength of attraction; strongly favours low-frequency words |
    | **MI²** (Daille 1994) | $\log_2 \frac{O_{11}^2}{E_{11}}$ | Intermediate; tempers low-frequency bias |
    | **MI³** (Daille 1994) | $\log_2 \frac{O_{11}^3}{E_{11}}$ | Strong and frequent recurrent pairs |
    | **T-score** (Church et al. 1991) | $\frac{O_{11} - E_{11}}{\sqrt{O_{11}}}$ | Certainty / evidence; favours frequent grammatical partners |
    | **G²** (Dunning 1993) | $2 \sum_{i,j} O_{ij} \ln \frac{O_{ij}}{E_{ij}}$ | Signed likelihood ratio test; positive = attraction, negative = repulsion |
    | **Log-Dice** (Rychlý 2008) | $14 + \log_2 \frac{2 O_{11}}{f_{\text{node}} + C_1}$ | Corpus-size independent; maximum 14 for perfect co-occurrence |

    **Strength vs Evidence (GraphColl, Brezina et al. 2015).** MI measures *effect size* (strength),
    while $G^2$ measures *statistical evidence* (sample size / certainty). A scatter plot of MI vs $G^2$
    reveals four distinct quadrants: rare exclusive partners (high MI, low $G^2$), central topical
    collocates (high MI, high $G^2$), grammatical collocations (low MI, high $G^2$), and noise.

    ### 10.2 Worked toy example (hand-checkable)
    Given: $N = 1000$, $R_1 = 100$, $C_1 = 20$, $O_{11} = 10$, $f_{\text{node}} = 50$:
    1. $E_{11} = \frac{100 \times 20}{1000} = 2.0$
    2. $\text{MI} = \log_2(10 / 2) = \log_2(5) \approx 2.322$
    3. $\text{MI}^2 = \log_2(100 / 2) = \log_2(50) \approx 5.644$
    4. $\text{MI}^3 = \log_2(1000 / 2) = \log_2(500) \approx 8.966$
    5. $\text{T-score} = \frac{10 - 2}{\sqrt{10}} = \frac{8}{3.1623} \approx 2.530$
    6. $\text{Log-Dice} = 14 + \log_2 \left(\frac{20}{50 + 20}\right) = 14 + \log_2(0.2857) = 14 - 1.8074 \approx 12.193$
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
    - Narrow spans ($\pm 1, \pm 2$) capture **morphosyntax** and immediate valency (prepositions, auxiliary verbs, modifiers).
    - Wider spans ($\pm 5, \pm 10$) capture **thematic/discourse** associations.
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
                    "Window slots are counted once per position (union slots): this prevents overlapping windows from counting the same token twice, ensuring $O_{11} \le C_1$.",
                    "$G^2$ is signed: negative values indicate repulsion (words that co-occur *less* frequently than chance expects)."]),
          exercises([("Which English lemmas collocate with `human` (±4) in Isaac Asimov's *I, Robot* by Log-Dice?",
                      "```python\nir = loader.load_text('IR-IA')\nprint(loader.registry.display(ir))\nv = TokenView(ir, 'lem', True)\ndisplay(collocation.collocates(v, 'human', 4, 4, min_freq=3, sort_by='LogDice').head(10))\nir.evict()\n```")]),
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

    - **Sublinear TF**: $\text{TF}(t, d) = 1 + \ln(\text{count}(t, d))$ for $\text{count} > 0$ (diminishing returns of repetition).
    - **Smooth IDF**: $\text{IDF}(t) = \ln\left(\frac{1 + N}{1 + \text{DF}(t)}\right) + 1$, where $N$ is total documents and $\text{DF}(t)$ is document frequency.
    - **L2 Normalisation**: $\vec{v}_{\text{norm}} = \frac{\vec{v}}{\|\vec{v}\|_2}$ ensures document length does not distort keyness.

    Because English and Turkish possess fundamentally distinct morphological structures and vocabularies,
    they are fitted as **separate subcorpora**.

    ### 11.2 Worked toy example — hand calculation vs scikit-learn
    Three documents: $d_1 = [a, b, b]$, $d_2 = [a, c]$, $d_3 = [c, c, d]$ ($N = 3$).
    - $a$: in $d_1, d_2$ $\Rightarrow \text{DF} = 2 \Rightarrow \text{IDF} = \ln(4/3) + 1 \approx 1.2877$
    - $b$: in $d_1$ $\Rightarrow \text{DF} = 1 \Rightarrow \text{IDF} = \ln(4/2) + 1 = \ln(2) + 1 \approx 1.6931$
    - $c$: in $d_2, d_3$ $\Rightarrow \text{DF} = 2 \Rightarrow \text{IDF} = \ln(4/3) + 1 \approx 1.2877$
    - $d$: in $d_3$ $\Rightarrow \text{DF} = 1 \Rightarrow \text{IDF} = \ln(4/2) + 1 = \ln(2) + 1 \approx 1.6931$

    In $d_1$: $\text{tf}(a) = 1 + \ln(1) = 1.0$; $\text{tf}(b) = 1 + \ln(2) \approx 1.6931$.
    Unnormalized: $w(a) = 1.0 \times 1.2877 = 1.2877$; $w(b) = 1.6931 \times 1.6931 \approx 2.8667$.
    L2 norm: $\sqrt{1.2877^2 + 2.8667^2} = \sqrt{1.6582 + 8.2180} = 3.1427$.
    Normalized $d_1$: $a \approx 0.410$, $b \approx 0.912$.
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
                      "```python\nr = T.fit(loader.load_all_english(), 'lem', True, exclude_pos={'PROPN'})\ndisplay(r.top_terms('ASD-PKD', 8))\n```")]),
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
                      "```python\nimport pandas as pd\nxlsx_path = report_path.with_suffix('.xlsx')\nprint('Excel sheets:', pd.ExcelFile(xlsx_path).sheet_names)\n```")]),
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
    - **Span**: Phrase, sentence, or symmetric window ($\pm L / \pm R$).
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
                      "```python\nfrom corpus_toolkit.explorer import quick_search\nres = quick_search(loader, ['uzay'], category='Turkish translations', field='lem', view='kwic', max_lines=5)\ndisplay(res)\n```")]),
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
