"""Input-to-output unit tests covering all endpoints and sub-components of Tabs 6 to 11."""

from __future__ import annotations

from flask.testing import FlaskClient

from SPA.tests.conftest import assert_finite_number, assert_table_payload


def test_tab06_kwic_and_subtabs_inputs_to_outputs(client: FlaskClient) -> None:
    """Verify Tab 6 KWIC search modes, spans, sorting, punct compare, summary, views, and NLTK."""
    kw_exact = client.post(
        "/api/v1/concordance/search",
        json={"query": "robot", "match_mode": "exact", "left_span": 3, "right_span": 3, "sort_by": "position", "scope": "indig_tr"},
    ).get_json()
    kw_glob = client.post(
        "/api/v1/concordance/search",
        json={"query": "robot*", "match_mode": "glob", "left_span": 5, "right_span": 5, "sort_by": "R1", "scope": "indig_tr"},
    ).get_json()
    assert kw_exact["total_hits"] > 0
    assert kw_glob["total_hits"] >= kw_exact["total_hits"]
    assert kw_exact["lines"][0] != kw_glob["lines"][0]

    bad_rx = client.post("/api/v1/concordance/search", json={"query": "[unclosed", "match_mode": "regex"})
    assert bad_rx.status_code == 400 and "error" in bad_rx.get_json()

    p_cmp = client.post("/api/v1/concordance/punct-compare", json={"query": "robot", "scope": "indig_tr"}).get_json()
    assert set(p_cmp["counts"].keys()) == {"drop", "keep", "strip", "split"}

    s_sum = client.post("/api/v1/concordance/summary", json={"term": "robot", "match": "exact", "scope": "indig_tr"}).get_json()
    assert_table_payload(s_sum["table"], min_rows=3, required_cols=("code", "hits", "per10k"))
    assert len(s_sum["bars"]) == 3

    v_cmp = client.post("/api/v1/concordance/views-compare", json={"term": "robot", "scope": "indig_tr"}).get_json()
    assert_table_payload(v_cmp, min_rows=4, required_cols=("view_config", "total_hits", "per10k"))

    nltk_res = client.post("/api/v1/concordance/nltk", json={"code": "TL-PA", "word": "light"}).get_json()
    assert len(nltk_res["concordance"]) > 0 and isinstance(nltk_res["similar"], list)


def test_tab07_batch_dispersion_and_matrices_inputs_to_outputs(client: FlaskClient) -> None:
    """Verify Tab 7 labeled group parsing, flat list parsing, Juilland D, BH-FDR, and heatmaps."""
    grouped = client.post(
        "/api/v1/concordance/batch-dispersion",
        json={"terms": ["makine alanı: robot, makine | insan alanı: insan, adam"], "scope": "all_tr"},
    ).get_json()
    assert len(grouped["summary"]) == 4 and len(grouped["pairwise"]) == 6
    for row in grouped["summary"]:
        assert_finite_number(row["D_across_texts"], "D_across_texts")
        assert_finite_number(row["D_within_text(mean)"], "D_within_text(mean)")

    b_mat = client.post(
        "/api/v1/concordance/batch-matrices",
        json={"raw_input": "makine alanı: robot, makine | insan alanı: insan, adam", "scope": "all_tr"},
    ).get_json()
    assert_table_payload(b_mat["counts"], min_rows=2)
    assert_table_payload(b_mat["rates"], min_rows=2)
    assert len(b_mat["rates_matrix"]["rows"]) >= 2
    assert len(b_mat["corr_matrix"]["rows"]) >= 2
    assert len(b_mat["chunk_series"]) >= 1


def test_tab08_diversity_and_subtabs_inputs_to_outputs(client: FlaskClient) -> None:
    """Verify Tab 8 Diversity table (drop vs mask) and all 5 visualization subtabs."""
    t_drop = client.post(
        "/api/v1/lexicon/diversity/table",
        json={"scope": "indig_tr", "field": "lem", "filter_function_words": True, "mode": "drop", "punct": "drop"},
    ).get_json()["items"]
    t_mask = client.post(
        "/api/v1/lexicon/diversity/table",
        json={"scope": "indig_tr", "field": "lem", "filter_function_words": True, "mode": "mask", "punct": "drop"},
    ).get_json()["items"]
    assert len(t_drop) == 3 and len(t_mask) == 3
    assert t_drop[0]["MATTR_500"] != t_mask[0]["MATTR_500"]

    sens = client.post("/api/v1/lexicon/diversity/sensitivity", json={"code": "BR-SM"}).get_json()
    assert len(sens["series"]) >= 2
    assert_table_payload(sens["table"], min_rows=3)

    cmp_tbls = client.post("/api/v1/lexicon/diversity/compare", json={"scope": "indig_tr"}).get_json()
    assert_table_payload(cmp_tbls["token_vs_lemma"], min_rows=3)
    assert_table_payload(cmp_tbls["punct_regimes"], min_rows=2)

    radar = client.post("/api/v1/lexicon/diversity/radar", json={"scope": "indig_tr"}).get_json()
    assert len(radar["axes"]) >= 5 and len(radar["series"]) == 3

    mattr_c = client.post("/api/v1/lexicon/diversity/mattr-trajectories", json={"scope": "indig_tr", "window": 200}).get_json()
    zipf_c = client.post("/api/v1/lexicon/diversity/zipf-curves", json={"scope": "indig_tr"}).get_json()
    assert len(mattr_c["series"]) == 3 and len(zipf_c["series"]) == 3


def test_tab09_collocation_tab10_tfidf_and_tab11_explorer(client: FlaskClient) -> None:
    """Verify Tab 9 Collocations, Tab 10 TF-IDF/Report, and Tab 11 Explorer Quick Search."""
    for metric in ("LogDice", "MI", "G2", "T", "MI2", "MI3"):
        res = client.post(
            "/api/v1/lexicon/collocation/table",
            json={"node_query": "robot", "text_code": "BR-SM", "min_freq": 2, "stat_metric": metric},
        ).get_json()
        assert res["metric"] == metric and len(res["items"]) > 0

    scat = client.post("/api/v1/lexicon/collocation/scatter", json={"code": "BR-SM", "node": "robot", "min_freq": 2}).get_json()
    sens = client.post("/api/v1/lexicon/collocation/sensitivity", json={"code": "BR-SM", "node": "robot", "min_freq": 2}).get_json()
    nltk_b = client.post("/api/v1/lexicon/collocation/nltk", json={"code": "BR-SM"}).get_json()
    assert len(scat["series"]) >= 1
    assert_table_payload(sens["measures_table"], min_rows=3)
    assert_table_payload(sens["window_table"], min_rows=3)
    assert_table_payload(nltk_b["collocations"], min_rows=1)

    kw_no_propn = client.post("/api/v1/lexicon/tfidf/keywords", json={"scope": "indig_tr", "top_k": 8, "exclude_pos": ["PROPN"]}).get_json()
    kw_with_propn = client.post("/api/v1/lexicon/tfidf/keywords", json={"scope": "indig_tr", "top_k": 8, "exclude_pos": []}).get_json()
    assert kw_no_propn["texts_keywords"] != kw_with_propn["texts_keywords"]

    dense = client.post("/api/v1/lexicon/tfidf/dense", json={"scope": "indig_tr", "top_k": 5}).get_json()
    assert len(dense["documents"]) == 3 and len(dense["matrix"]) == 3

    rep = client.post("/api/v1/lexicon/report/preview", json={"scope": "indig_tr"}).get_json()
    assert rep["kpis"]["text_count"] == 3 and len(rep["sections"]) >= 2
    assert_table_payload(rep["summary_table"], min_rows=3)

    qs = client.post(
        "/api/v1/export/quick-search",
        json={"term": "robot", "scope": "author_turkish", "author_filter": "SM", "field": "lem", "filter_function_words": True, "mode": "mask", "punct": "strip"},
    ).get_json()
    assert qs["total_hits"] > 0
    assert "author='SM'" in qs["python_snippet"]
    assert "mode='mask'" in qs["python_snippet"] and "punct='strip'" in qs["python_snippet"]
