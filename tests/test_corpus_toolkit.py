"""Known-answer tests: every expected value below was computed by hand (see comments)."""

import math

import numpy as np
import pandas as pd
import pytest

from corpus_toolkit import TokenView
from corpus_toolkit.alignment import alignment_type
from corpus_toolkit.cache import CorpusCacheManager
from corpus_toolkit.collocation import association_table, window_slots
from corpus_toolkit.depviz import displacy_payload, render_svg
from corpus_toolkit.diversity import diversity_metrics, mattr_series, mtld, rank_frequency, sttr
from corpus_toolkit.filters import CONTENT, FUNCTION, PUNCT, classify_token
from corpus_toolkit.kwic import Concordancer, resolve_span
from corpus_toolkit.search import CorpusSearchEngine, SearchQuery
from corpus_toolkit.stats import (
    benjamini_hochberg,
    bootstrap_ci,
    chunk_counts,
    cosine,
    juilland_d,
    pearson,
    per10k,
    spearman,
)
from corpus_toolkit.textutil import (
    fold,
    loose_key,
    split_in_token_punct,
    strip_in_token_punct,
    turkish_lower,
)
from corpus_toolkit.tfidf import tfidf_manual


# ------------------------------------------------------------------ text utils
def test_turkish_casing():
    assert turkish_lower("İSTANBUL ISIK") == "istanbul ısık"
    assert fold("I", "en") == "i" and fold("I", "tr") == "ı"
    assert loose_key("Zühtü Bayar") == "zuhtu bayar"
    assert loose_key("Özlem   Kurdoğlu") == "ozlem kurdoglu"


def test_classify_token():
    assert classify_token("PUNCT", "", "en") == PUNCT
    assert classify_token("ADP", "", "en") == FUNCTION
    assert classify_token("NOUN", "", "en") == CONTENT
    assert classify_token("ADV", "bir+Postp", "tr") == FUNCTION  # morph-head guard
    assert classify_token("ADV", "bir+Postp", "en") == CONTENT  # English: UPOS only


# ------------------------------------------------------------------- lazy/view
def test_token_tables_and_evict(mini_text):
    tab = mini_text.tokens
    assert len(tab) == 12 and (tab["fcl"] == PUNCT).sum() == 2
    assert mini_text.sentences["ntok"].tolist() == [6, 6]
    assert mini_text.loaded
    mini_text.evict()
    assert not mini_text.loaded
    assert mini_text.summary()["n_tokens"] == 12  # served from cached meta


def test_cache_second_load_hits_parquet(mini_text):
    _ = mini_text.tokens
    mini_text.evict()
    assert mini_text.cache.has(mini_text._key("tok"))
    assert len(mini_text.tokens) == 12


def test_views(mini_text):
    raw = TokenView(mini_text, "tok", False)
    assert len(raw) == 10 and raw.freq().to_dict() == {"the": 4, "cat": 2, "dog": 2, "saw": 2}
    content = TokenView(mini_text, "lem", True, "drop")
    assert len(content) == 6 and "the" not in content.freq()
    masked = TokenView(mini_text, "lem", True, "mask")
    assert len(masked) == 6 and len(masked.forms) == 10  # sequence keeps function words


# ------------------------------------------------------------------- diversity
def test_diversity_known_answers(mini_text):
    m = diversity_metrics(TokenView(mini_text, "tok", False).analysed())
    assert m["N"] == 10 and m["V"] == 4 and m["TTR"] == pytest.approx(0.4)
    assert m["Guiraud_R"] == pytest.approx(4 / math.sqrt(10))
    assert m["CTTR"] == pytest.approx(4 / math.sqrt(20))
    assert m["Herdan_C"] == pytest.approx(math.log(4) / math.log(10))
    # spectrum: V_4=1, V_2=3 -> sum m^2 V_m = 16 + 12 = 28 -> K = 1e4*(28-10)/100
    assert m["Yule_K"] == pytest.approx(1800.0)
    assert m["Simpson_D"] == pytest.approx(18 / 90)  # sum n(n-1) = 12+2+2+2
    assert m["Honore_R"] == pytest.approx(100 * math.log(10))  # V1 = 0 -> denominator 1
    assert m["Hapax_types_pct"] == 0.0


def test_honore_with_hapax():
    forms = ["a", "a", "b", "c"]  # V=3, V1=2, N=4
    assert diversity_metrics(forms)["Honore_R"] == pytest.approx(
        100 * math.log(4) / (1 - 2 / 3))


def test_mattr_and_sttr():
    s = mattr_series(list("abab"), 3)
    assert s.tolist() == pytest.approx([2 / 3, 2 / 3])
    assert sttr(list("abcdabcd"), block=4) == pytest.approx(1.0)
    with pytest.warns(UserWarning):
        sttr(list("abc"), block=4)


def test_mtld_known():
    assert mtld(list("aaaa")) == pytest.approx(2.0)  # TTR .5 <= .72 after 2 tokens -> 2 factors
    assert math.isnan(mtld(["a"]))


def test_rank_frequency():
    rf = rank_frequency(["a", "a", "b"])
    assert rf["freq"].tolist() == [2, 1] and rf["rank"].tolist() == [1, 2]


# ------------------------------------------------------------------- statistics
def test_stats_helpers():
    assert per10k(5, 1000) == pytest.approx(50.0)
    assert juilland_d([1, 1, 1, 1]) == pytest.approx(1.0)
    assert juilland_d([4, 0, 0, 0]) == pytest.approx(0.0, abs=1e-12)
    assert chunk_counts([0, 1, 5, 9], 10, 5).tolist() == [2, 0, 1, 0, 1]
    assert cosine([1, 0], [0, 1]) == 0.0 and cosine([1, 2], [2, 4]) == pytest.approx(1.0)
    r, _ = pearson([1, 2, 3, 4], [2, 4, 6, 8])
    rho, _ = spearman([1, 2, 3, 4], [1, 4, 9, 16])
    assert r == pytest.approx(1.0) and rho == pytest.approx(1.0)
    assert all(math.isnan(v) for v in pearson([1, 1, 1], [1, 2, 3]))


def test_benjamini_hochberg():
    q = benjamini_hochberg([0.01, 0.04, 0.03, 0.005])
    assert q.tolist() == pytest.approx([0.02, 0.04, 0.04, 0.02])


def test_bootstrap_is_deterministic():
    a = bootstrap_ci([1, 2, 3, 4, 5], n_boot=200)
    assert a == bootstrap_ci([1, 2, 3, 4, 5], n_boot=200) and a[1] <= a[0] <= a[2]


# ----------------------------------------------------------------- collocation
def test_association_measures_hand_computed():
    t = association_table(np.array([10]), np.array([20]), r1=100, n=1000, f_node=50).iloc[0]
    assert t["E11"] == pytest.approx(2.0)
    assert t["MI"] == pytest.approx(math.log2(5))
    assert t["MI2"] == pytest.approx(math.log2(100 / 2))
    assert t["MI3"] == pytest.approx(math.log2(1000 / 2))
    assert t["T"] == pytest.approx(8 / math.sqrt(10))
    assert t["LogDice"] == pytest.approx(14 + math.log2(2 * 10 / 70))
    cells = [(10, 2), (90, 98), (10, 18), (890, 882)]
    g2 = 2 * sum(o * math.log(o / e) for o, e in cells)
    assert t["G2"] == pytest.approx(g2) and t["p_G2"] < 1e-3


def test_window_slots_union_and_clamp():
    s = window_slots(10, np.array([5]), 2, 1)
    assert np.flatnonzero(s).tolist() == [3, 4, 6]  # own position excluded
    s2 = window_slots(10, np.array([5, 6]), 1, 1)
    assert np.flatnonzero(s2).tolist() == [4, 5, 6, 7]  # neighbouring nodes see each other
    lo, hi = np.array([0] * 10), np.array([5] * 10)
    assert np.flatnonzero(window_slots(10, np.array([5]), 3, 3, lo, hi)).tolist() == [2, 3, 4]


# ---------------------------------------------------------------------- search
def test_search_options(mini_text):
    eng = CorpusSearchEngine()
    assert len(eng.search(SearchQuery(["saw"], "tok"), [mini_text])) == 2
    assert len(eng.search(SearchQuery(["ca*"], "tok", match="glob"), [mini_text])) == 2
    assert len(eng.search(SearchQuery(["^d.g$"], "tok", match="regex"), [mini_text])) == 2
    assert len(eng.search(SearchQuery(["saw"], "tok", pos={"NOUN"}), [mini_text])) == 0
    assert len(eng.search(SearchQuery(["the"], "tok", filter_function_words=True),
                          [mini_text])) == 0
    near = SearchQuery(["saw"], "tok", collocate=["dog"], collocate_span=(1, 1))
    wide = SearchQuery(["saw"], "tok", collocate=["dog"], collocate_span=(2, 2))
    assert len(eng.search(near, [mini_text])) == 1  # only sentence 2: 'dog saw' adjacent
    assert len(eng.search(wide, [mini_text])) == 2
    res = eng.search(SearchQuery(["saw"], "tok"), [mini_text])
    assert res.summary()["per10k"].iloc[0] == pytest.approx(1e4 * 2 / 10)


# ----------------------------------------------------------------------- KWIC
def test_resolve_span():
    assert resolve_span("collocation") == (5, 5) and resolve_span(7) == (7, 7)
    assert resolve_span("L5R2") == (5, 2) and resolve_span((3, 0)) == (3, 0)
    assert resolve_span("sentence")[0] > 1000
    with pytest.raises(ValueError):
        resolve_span(21)
    with pytest.raises(ValueError):
        resolve_span((0, 0))


def test_concordance_lines(mini_text):
    q = SearchQuery(["saw"], "tok")
    res = CorpusSearchEngine().search(q, [mini_text])
    conc = Concordancer().run(res, [mini_text], span=(1, 1))
    first = conc.lines[0]
    assert first.left_text() == "cat" and first.node[0] == "saw" and first.right_text() == "the"
    assert first.coordinate == "ch 1 · p 1 · s 1 · tok 3"
    q2 = SearchQuery(["saw"], "tok", filter_function_words=True)
    conc2 = Concordancer().run(CorpusSearchEngine().search(q2, [mini_text]), [mini_text], (1, 1))
    assert conc2.lines[0].right_text() == "the dog ."  # span reaches sentence end; function word kept (dimmed)
    whole = Concordancer().run(res, [mini_text], span="sentence")
    assert whole.lines[0].left_text() == "The cat" and whole.lines[0].right_text() == "the dog ."


# ------------------------------------------------------------------- alignment
@pytest.mark.parametrize("a,b,expected", [
    (1, 1, "1:1"), (1, 2, "1:N"), (3, 1, "N:1"), (2, 2, "N:M"), (2, 0, "omission"),
    (0, 3, "addition")])
def test_alignment_type(a, b, expected):
    assert alignment_type(a, b) == expected


# ------------------------------------------------------------------------ tf-idf
def test_tfidf_manual_matches_sklearn():
    from sklearn.feature_extraction.text import TfidfVectorizer

    docs = [["a", "b", "b"], ["a", "c"], ["c", "c", "d"]]
    vec = TfidfVectorizer(analyzer=lambda x: x, sublinear_tf=True)
    skl = vec.fit_transform(docs).toarray()
    man = tfidf_manual(docs)[list(vec.get_feature_names_out())].to_numpy()
    assert np.allclose(skl, man)


# -------------------------------------------------------------------------- dep
def test_dep_payload_and_svg():
    p = displacy_payload(["a", "b", "c"], ["DET", "NOUN", "VERB"], [2, 3, 0],
                         ["det", "nsubj", "ROOT"], "en")
    assert p["arcs"][0] == {"start": 0, "end": 1, "label": "det", "dir": "left"}
    assert len(p["arcs"]) == 2
    bad = displacy_payload(["a", "b"], ["X", "X"], [1, 9], ["x", "y"], "tr")
    assert bad["arcs"] == []  # self-head and out-of-range heads are skipped
    mapped = displacy_payload(["a", "b"], ["X", "X"], [2, 0], ["dobj", "ROOT"], "en")
    assert mapped["arcs"][0]["label"] == "obj"
    assert "displacy" in render_svg(p, dim={0})


# ------------------------------------------------------------------------ cache
def test_cache_policy(tmp_path, monkeypatch):
    cache = CorpusCacheManager(tmp_path / ".cache")
    k = cache.key("x", 1, "a")
    cache.save_frame(k, pd.DataFrame({"a": [1, 2]}))
    assert cache.load_frame(k)["a"].tolist() == [1, 2]
    assert cache.key("x", 1, "a") == k and cache.key("x", 2, "a") != k

    def boom(*_a, **_k):
        raise EOFError

    monkeypatch.setattr("builtins.input", boom)
    assert cache.apply_policy("ask", verbose=False) == "kept"  # headless -> keep
    assert cache.apply_policy("clear", verbose=False) == "cleared"
    assert cache.entries() == []


def test_cache_budget(tmp_path):
    cache = CorpusCacheManager(tmp_path / ".cache", max_mb=0.0005)
    for i in range(3):
        cache.save_frame(f"k{i}", pd.DataFrame({"a": np.arange(2000)}))
    assert len(cache.entries()) < 3  # LRU eviction kicked in


# ----------------------------------------------------------------- integration
@pytest.mark.data
def test_registry_resolves_thirteen_texts(real_config):
    from corpus_toolkit.registry import CorpusRegistry

    reg = CorpusRegistry.from_config(real_config)
    assert len(reg.texts) == 13 and len(reg.pairs) == 5
    assert reg.verify_files()["exists"].all()
    assert reg.resolve_author("selma mine") == "SM" and reg.resolve_author("OK") == "OK"
    assert reg.resolve_text("karanligi taramak").code == "KT-OK"
    assert "Zühtü Bayar" in reg.display(reg.resolve_text("A-ZB"))


def test_hdd_known():
    from corpus_toolkit.diversity import hdd

    # 42 identical tokens -> HD-D is 1 / 42 (exactly 1 type sampled)
    assert round(hdd(["word"] * 42), 4) == round(1 / 42, 4)
    # 42 distinct tokens -> HD-D is 1.0 (all types sampled)
    assert round(hdd([f"w{i}" for i in range(42)]), 4) == 1.0
    # Less than 42 tokens -> NaN
    assert np.isnan(hdd(["a"] * 41))


def test_tracked_notebook_is_clean():
    import json
    from pathlib import Path

    for nb_name in ("Corpus_Analysis.ipynb", "Corpus_Analysis_tr.ipynb"):
        nb_path = Path(__file__).resolve().parents[1] / nb_name
        if not nb_path.exists():
            pytest.skip(f"{nb_name} not yet generated")
        data = json.loads(nb_path.read_text(encoding="utf-8"))
        for i, cell in enumerate(data.get("cells", [])):
            if cell.get("cell_type") == "code":
                assert not cell.get("outputs", []), (
                    f"Cell {i} in {nb_name} has outputs! Tracked notebook must be stripped to prevent committing "
                    f"copyrighted text to git."
                )
                assert cell.get("execution_count") is None, f"Cell {i} in {nb_name} has execution_count set!"


def test_notebook_markdown_integrity():
    """Markdown cells must be flush-left (no code-block rendering) and free of control chars (broken LaTeX)."""
    import json
    import re
    from pathlib import Path

    for nb_name in ("Corpus_Analysis.ipynb", "Corpus_Analysis_tr.ipynb"):
        nb_path = Path(__file__).resolve().parents[1] / nb_name
        if not nb_path.exists():
            pytest.skip(f"{nb_name} not yet generated")
        for i, cell in enumerate(json.loads(nb_path.read_text(encoding="utf-8"))["cells"]):
            if cell["cell_type"] != "markdown":
                continue
            src = "".join(cell["source"])
            assert not any(ord(c) < 32 and c not in "\n" for c in src), f"{nb_name} cell {i}: control char"
            first = next((ln for ln in src.splitlines() if ln.strip()), "")
            assert not first.startswith("    "), f"{nb_name} cell {i}: indented first line"
            prose = re.sub(r"`[^`]*`", "", src)  # `$` inside code spans (regex anchors) is not math
            assert prose.count("$") % 2 == 0, f"{nb_name} cell {i}: unbalanced $"


# -------------------------------------------------------- specialized punct tests
def test_punctuation_helpers():
    # Passim-style stripping (collapse)
    assert strip_in_token_punct("Türkiye'nin") == "Türkiyenin"
    assert strip_in_token_punct("Fred'") == "Fred"
    assert strip_in_token_punct("robot-bilim") == "robotbilim"
    assert strip_in_token_punct("sn'lik") == "snlik"
    assert strip_in_token_punct("00000001'dir") == "00000001dir"
    assert strip_in_token_punct("1882'") == "1882"
    assert strip_in_token_punct("ay'da") == "ayda"
    assert strip_in_token_punct("-") == ""
    assert strip_in_token_punct("'") == ""

    # Passim-style splitting (retokenization / decomposition)
    assert split_in_token_punct("Türkiye'nin") == ["Türkiye", "nin"]
    assert split_in_token_punct("Fred'") == ["Fred"]
    assert split_in_token_punct("robot-bilim") == ["robot", "bilim"]
    assert split_in_token_punct("sn'lik") == ["sn", "lik"]
    assert split_in_token_punct("00000001'dir") == ["00000001", "dir"]
    assert split_in_token_punct("1882'") == ["1882"]
    assert split_in_token_punct("ay'da") == ["ay", "da"]
    assert split_in_token_punct("-") == []
    assert split_in_token_punct("'") == []


def test_turkish_tokenview_punct_modes(turkish_mini_text):
    # 1. Surface tokens: 'drop' (default)
    v_drop = TokenView(turkish_mini_text, field="tok", punct="drop")
    assert len(v_drop) == 9
    assert "türkiye'nin" in v_drop.forms
    assert "robot-bilim" in v_drop.forms
    assert "fred'" in v_drop.forms
    assert "." not in v_drop.forms

    # 2. Surface tokens: 'keep' (with punctuation)
    v_keep = TokenView(turkish_mini_text, field="tok", punct="keep")
    assert len(v_keep) == 11
    assert "." in v_keep.forms and "?" in v_keep.forms

    # 3. Surface tokens: 'strip' (in-token collapsed)
    v_strip = TokenView(turkish_mini_text, field="tok", punct="strip")
    assert len(v_strip) == 9
    assert "türkiyenin" in v_strip.forms
    assert "robotbilim" in v_strip.forms
    assert "fred" in v_strip.forms
    assert "türkiye'nin" not in v_strip.forms

    # 4. Surface tokens: 'split' (in-token decomposed)
    v_split = TokenView(turkish_mini_text, field="tok", punct="split")
    assert len(v_split) == 13
    assert "türkiye" in v_split.forms and "nin" in v_split.forms
    assert "robot" in v_split.forms and "bilim" in v_split.forms
    assert "fred" in v_split.forms

    # 5. Lemmatized field: 'strip'
    v_lem_strip = TokenView(turkish_mini_text, field="lem", punct="strip")
    assert len(v_lem_strip) == 9
    assert "türkiye" in v_lem_strip.forms
    assert "robotbilim" in v_lem_strip.forms
    assert "uzman" in v_lem_strip.forms
    assert "fred" in v_lem_strip.forms
    assert "1882" in v_lem_strip.forms

    # 6. Lemmatized field: 'split'
    v_lem_split = TokenView(turkish_mini_text, field="lem", punct="split")
    assert len(v_lem_split) == 10
    assert "türkiye" in v_lem_split.forms
    assert "robot" in v_lem_split.forms and "bilim" in v_lem_split.forms
    assert "uzman" in v_lem_split.forms
    assert "fred" in v_lem_split.forms


def test_clean_lemma_cases():
    from corpus_toolkit.textutil import clean_lemma, clean_lemmas

    assert clean_lemma("Türkiye'nin") == "Türkiye"
    assert clean_lemma("Türkiye’nin") == "Türkiye"  # Curly right apostrophe U+2019
    assert clean_lemma("türkiye'nin") == "türkiye"
    assert clean_lemma("bilim-kurgu'nun") == "bilim-kurgu"  # preserves hyphenated compound before apostrophe
    assert clean_lemma("Fred'") == "Fred"
    assert clean_lemma("ay'da") == "ay"
    assert clean_lemma("1882'de") == "1882"
    assert clean_lemma("1882'") == "1882"
    assert clean_lemma("Hâlâ'nın") == "Hâlâ"  # Circumflex vowel
    assert clean_lemma("kâğıt'ta") == "kâğıt"  # Circumflex vowel
    assert clean_lemma("ak'çiçek") == "ak"  # Compound with internal apostrophe
    assert clean_lemma("'") == "'"
    assert clean_lemma("‘") == "‘"
    assert clean_lemma("’") == "’"
    assert clean_lemma("") == ""
    assert clean_lemmas(["Türkiye'nin", "bilim-kurgu'nun", "uzman"]) == ["Türkiye", "bilim-kurgu", "uzman"]



def test_search_punct_modes(turkish_mini_text):
    eng = CorpusSearchEngine()

    # Search with punct='keep': find punctuation
    q_punct = SearchQuery(["?"], field="tok", punct="keep")
    res_punct = eng.search(q_punct, [turkish_mini_text])
    assert len(res_punct) == 1
    assert res_punct.hits["token"].iloc[0] == "?"

    # Search with punct='strip': query with or without apostrophe
    q_strip1 = SearchQuery(["Türkiye'nin"], field="tok", punct="strip")
    q_strip2 = SearchQuery(["Türkiyenin"], field="tok", punct="strip")
    res_s1 = eng.search(q_strip1, [turkish_mini_text])
    res_s2 = eng.search(q_strip2, [turkish_mini_text])
    assert len(res_s1) == 1 and len(res_s2) == 1
    assert res_s1.hits["form"].iloc[0] == "türkiyenin"
    assert res_s1.hits["token"].iloc[0] == "Türkiye'nin"

    # Search with punct='split': query constituent parts of composite words
    q_sp_r = SearchQuery(["robot"], field="tok", punct="split")
    q_sp_b = SearchQuery(["bilim"], field="tok", punct="split")
    res_r = eng.search(q_sp_r, [turkish_mini_text])
    res_b = eng.search(q_sp_b, [turkish_mini_text])
    assert len(res_r) == 1 and res_r.hits["token"].iloc[0] == "robot-bilim"
    assert len(res_b) == 1 and res_b.hits["token"].iloc[0] == "robot-bilim"

    # Search on lemmas with punct='strip' and 'split'
    q_lem_fred = SearchQuery(["fred"], field="lem", punct="strip")
    res_f = eng.search(q_lem_fred, [turkish_mini_text])
    assert len(res_f) == 1 and res_f.hits["lemma"].iloc[0] == "fred"

    # Searching with or without suffix on lemma matches cleaned lemma
    q_lem_tur1 = SearchQuery(["türkiye"], field="lem")
    q_lem_tur2 = SearchQuery(["Türkiye'nin"], field="lem")
    res_t1 = eng.search(q_lem_tur1, [turkish_mini_text])
    res_t2 = eng.search(q_lem_tur2, [turkish_mini_text])
    assert len(res_t1) == 1 and res_t1.hits["lemma"].iloc[0] == "türkiye"
    assert len(res_t2) == 1 and res_t2.hits["lemma"].iloc[0] == "türkiye"
    assert res_t1.hits["token"].iloc[0] == "Türkiye'nin"



def test_concordance_with_punct(turkish_mini_text):
    eng = CorpusSearchEngine()
    q_split = SearchQuery(["robot"], field="tok", punct="split")
    res = eng.search(q_split, [turkish_mini_text])
    conc = Concordancer().run(res, [turkish_mini_text], span=(2, 2))
    assert len(conc) == 1
    line = conc.lines[0]
    assert line.node[0] == "robot-bilim"


def test_diversity_with_punct_and_caching(turkish_mini_text, tmp_path):
    from corpus_toolkit.analysis import diversity_for
    from corpus_toolkit.loader import CorpusLoader

    loader = CorpusLoader(cache_policy="keep", verbose=False)
    d_drop = diversity_for(loader, [turkish_mini_text], field="tok", punct="drop")
    d_keep = diversity_for(loader, [turkish_mini_text], field="tok", punct="keep")
    d_strip = diversity_for(loader, [turkish_mini_text], field="tok", punct="strip")
    d_split = diversity_for(loader, [turkish_mini_text], field="tok", punct="split")

    # Lengths (N) reflect the distinct tokenization views
    assert d_drop.iloc[0]["N"] == 9
    assert d_keep.iloc[0]["N"] == 11
    assert d_strip.iloc[0]["N"] == 9
    assert d_split.iloc[0]["N"] == 13


def test_concordance_result_repr_and_html(turkish_mini_text):
    eng = CorpusSearchEngine()
    q = SearchQuery(["robot"], field="tok", punct="split")
    res = eng.search(q, [turkish_mini_text])
    conc = Concordancer().run(res, [turkish_mini_text], span=(2, 2))
    assert repr(conc).startswith("<ConcordanceResult: 1 line(s)")
    assert repr(conc.lines[0]).startswith("<KwicLine")
    html = conc._repr_html_()
    assert "<table" in html
    assert "robot-bilim" in html
    conc.meta["view"] = "table"
    tbl_html = conc._repr_html_()
    assert "ct-tbl-wrap" in tbl_html and 'data-page-size="1"' in tbl_html


def test_table_view_pagination_sorting_resizing():
    from corpus_toolkit.table_view import (
        disable_interactive_tables,
        enable_interactive_tables,
        table_html,
    )

    df = pd.DataFrame({
        "title": [f"Book_{i}" for i in range(45)],
        "tokens": [1000 * i for i in range(45)],
        "ratio": [round(i * 0.1234, 4) for i in range(45)],
    })
    html = table_html(df, page_size=20, title="Unit Test Grid")
    assert 'data-page-size="20"' in html
    assert "Rows 1–20 of 45 (Page 1/3)" in html
    assert "ct-col-resizer" in html
    assert "_ctTblSort(" in html
    assert "_ctTblStartResize(" in html
    assert 'data-type="num"' in html
    assert 'data-type="str"' in html

    enable_interactive_tables(page_size=20)
    try:
        assert "ct-tbl-wrap" in df._repr_html_()
    finally:
        disable_interactive_tables()


def test_parallel_view_nda_overlay():
    from corpus_toolkit.loader import CorpusLoader
    from corpus_toolkit.parallel_view import NdaOverlay, parallel_html

    loader = CorpusLoader(cache_policy="keep", verbose=False)
    ov = NdaOverlay.load(loader, "I_Robot")
    assert "NDA overlay:" in ov.status
    assert len(ov.tokens) > 1000
    assert len(ov.legend) >= 60

    html = parallel_html(loader, "BR-SM", [3350, 4288, 4313], overlay=True, hits={"brain"})
    assert "nda-table-stage" in html
    assert "nda-link-svg" in html
    assert "data-link-first=" in html
    assert "nda-summary-footer" in html
    assert "single-tr" in html
    assert "hit" in html


def test_bilingual_notebook_parity():
    import sys
    from pathlib import Path

    tools_dir = Path(__file__).resolve().parents[1] / "tools"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    import nb_part_a
    import nb_part_a_tr
    import nb_part_b
    import nb_part_b_tr
    import nb_part_c
    import nb_part_c_tr

    en_cells = nb_part_a.chapters() + nb_part_b.chapters() + nb_part_c.chapters()
    tr_cells = nb_part_a_tr.chapters() + nb_part_b_tr.chapters() + nb_part_c_tr.chapters()
    assert len(en_cells) == len(tr_cells)
    assert [c[0] for c in en_cells] == [c[0] for c in tr_cells]



