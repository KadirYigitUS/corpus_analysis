"""Input-to-output unit tests covering all endpoints and sub-components of Tabs 1 to 5."""

from __future__ import annotations

from flask.testing import FlaskClient

from SPA.tests.conftest import assert_finite_number, assert_table_payload


def test_tab01_inventory_and_subtabs_inputs_to_outputs(client: FlaskClient) -> None:
    """Verify Tab 1 Inventory, Schema, Sizes Chart, Verify, Summary, Memory, and Lemmas."""
    inv_all = client.get("/api/v1/corpus/inventory?scope=all&field=tok&punct=drop").get_json()
    inv_cnt = client.get("/api/v1/corpus/inventory?scope=all&field=lem&filter_function_words=true&punct=drop").get_json()
    inv_sm = client.get("/api/v1/corpus/inventory?scope=author_related&author_filter=SM").get_json()
    assert inv_all["total_texts"] == 13
    assert inv_sm["total_texts"] == 3
    assert inv_all["total_tokens"] > inv_cnt["total_tokens"] > 0

    tables_indig = client.get("/api/v1/corpus/source-tables?scope=indig_tr").get_json()
    assert len(tables_indig["indig_tr"]) == 3
    assert "trans_en" not in tables_indig

    schema = client.get("/api/v1/corpus/schema/BR-SM").get_json()
    assert schema["text_code"] == "BR-SM"
    assert len(schema["token_schema"]) >= 7 and len(schema["sentence_schema"]) >= 3

    sizes_all = client.get("/api/v1/corpus/sizes-chart?scope=all").get_json()
    sizes_zb = client.get("/api/v1/corpus/sizes-chart?scope=author_turkish&author_filter=ZB").get_json()
    assert len(sizes_all["items"]) == 13
    assert len(sizes_zb["items"]) == 4

    verify_tbl = client.get("/api/v1/corpus/verify-files?scope=indig_tr").get_json()
    assert_table_payload(verify_tbl, min_rows=3, required_cols=("code", "exists"))

    sum_tbl = client.get("/api/v1/corpus/size-summary?scope=trans_tr").get_json()
    assert_table_payload(sum_tbl, min_rows=5, required_cols=("code", "tokens", "sentences"))

    mem_tbl = client.get("/api/v1/corpus/memory-report").get_json()
    assert_table_payload(mem_tbl, min_rows=1, required_cols=("code", "loaded", "table_mb"))

    lem_drop = client.get(
        "/api/v1/corpus/content-lemmas?scope=indig_tr&field=lem&filter_function_words=true&punct=drop"
    ).get_json()
    lem_tok = client.get(
        "/api/v1/corpus/content-lemmas?scope=indig_tr&field=tok&filter_function_words=false&punct=keep"
    ).get_json()
    assert_table_payload(lem_drop, min_rows=3, required_cols=("code", "content_lemmas"))
    assert lem_tok["rows"][0]["content_lemmas"] > lem_drop["rows"][0]["content_lemmas"]


def test_tab02_alignment_and_structure_inputs_to_outputs(client: FlaskClient) -> None:
    """Verify Tab 2 KPIs, Chapter stats, NER filter, Pagination, and Structure Summary/Scatter."""
    kpi_ir = client.get("/api/v1/alignment/kpis/IR-IA_BR-SM").get_json()
    kpi_ch1 = client.get("/api/v1/alignment/kpis/IR-IA_BR-SM?chapter_no=1").get_json()
    assert kpi_ir["total_alignments"] == 6431
    assert 0 < kpi_ch1["total_alignments"] < kpi_ir["total_alignments"]
    assert_finite_number(kpi_ir["expansion_ratio"], "expansion_ratio")

    stats = client.get("/api/v1/alignment/stats/TL-PA_A-ZB").get_json()
    assert len(stats["series"]) > 100

    rows_p1 = client.post(
        "/api/v1/alignment/rows",
        json={"pair_code": "IR-IA_BR-SM", "page": 1, "page_size": 25, "ner_category": "ALL"},
    ).get_json()
    rows_per = client.post(
        "/api/v1/alignment/rows",
        json={"pair_code": "IR-IA_BR-SM", "page": 1, "page_size": 25, "ner_category": "PER"},
    ).get_json()
    assert rows_p1["total"] == 6431 and len(rows_p1["rows"]) == 25
    assert 0 < rows_per["total"] < rows_p1["total"]

    struct = client.get("/api/v1/alignment/structure-summary").get_json()
    assert_table_payload(struct["table"], min_rows=5, required_cols=("pair", "1:1_pct"))
    assert len(struct["stacked"]["pairs"]) == 5

    scatter = client.post(
        "/api/v1/alignment/structure-scatter",
        json={"pairs": ["IR-IA_BR-SM"], "max_points": 100},
    ).get_json()
    assert len(scatter["series"]) >= 1
    assert_finite_number(scatter["series"][0]["slope"], "OLS slope")


def test_tab03_nda_parallel_and_dictionary_inputs_to_outputs(client: FlaskClient) -> None:
    """Verify Tab 3 NDA parallel view modes, hit highlighting, and tripartite dictionary."""
    p_linked = client.get("/api/v1/alignment/nda/html/IR-IA_BR-SM?mode=linked&page=1&max_rows=10").get_json()
    p_all = client.get("/api/v1/alignment/nda/html/IR-IA_BR-SM?mode=all&page=1&max_rows=10").get_json()
    p_hits = client.get("/api/v1/alignment/nda/html/IR-IA_BR-SM?mode=all&hits=robot&max_rows=10").get_json()
    assert p_linked["pair_code"] == "IR-IA_BR-SM"
    assert ".pv table.pv-grid" in p_linked["html"]
    assert p_all["total_groups"] >= p_linked["total_groups"]
    assert "hit" in p_hits["html"]

    ndict = client.get("/api/v1/alignment/nda/dictionary/IR-IA_BR-SM").get_json()
    assert "entries" in ndict
    entries = ndict["entries"]
    assert "linked" in entries and "single_eng" in entries and "single_tur" in entries
    assert ndict["linked_count"] == len(entries["linked"])


def test_tab04_pos_and_tab05_depviz_inputs_to_outputs(client: FlaskClient) -> None:
    """Verify Tab 4 POS Profiles/Heatmap/Dumbbell/Forest and Tab 5 Single/Aligned Dependency Trees."""
    prof_all = client.post("/api/v1/syntax/pos/profiles", json={"scope": "all", "content_only": False}).get_json()
    prof_tr = client.post("/api/v1/syntax/pos/profiles", json={"scope": "indig_tr", "content_only": True}).get_json()
    assert len(prof_all["items"]) == 13 and len(prof_tr["items"]) == 3
    assert prof_all["items"][0] != prof_tr["items"][0]

    delta_raw = client.get("/api/v1/syntax/pos/pair-delta/IR-IA_BR-SM?content_only=false").get_json()
    delta_cnt = client.get("/api/v1/syntax/pos/pair-delta/IR-IA_BR-SM?content_only=true").get_json()
    assert delta_raw["items"][0]["eng_pct"] != delta_cnt["items"][0]["eng_pct"]

    comp_sm = client.post("/api/v1/syntax/pos/group-comparison", json={"comparison_key": "SM"}).get_json()
    comp_ok = client.post("/api/v1/syntax/pos/group-comparison", json={"comparison_key": "OK"}).get_json()
    assert comp_sm["author"] == "SM" and comp_ok["author"] == "OK"
    assert comp_sm["chi2"] != comp_ok["chi2"]

    mat_f = client.get("/api/v1/syntax/pos/matrix?scope=all_tr&content_only=false").get_json()
    mat_t = client.get("/api/v1/syntax/pos/matrix?scope=all_tr&content_only=true").get_json()
    assert len(mat_f["rows"]) == 8 and mat_f["values"][0] != mat_t["values"][0]

    conll = client.post(
        "/api/v1/syntax/dep/conll",
        json={"text_code": "BR-SM", "chapter_no": 1, "paragraph_no": 1, "sentence_no": 1},
    ).get_json()
    assert len(conll["tokens"]) > 0 and "deprel" in conll["tokens"][0]

    svg_dim = client.post(
        "/api/v1/syntax/dep/tree-svg",
        json={"text_code": "BR-SM", "chapter_no": 1, "paragraph_no": 1, "sentence_no": 1, "dim_function_words": True},
    ).get_json()
    assert "<svg" in svg_dim["svg"] and "opacity:0.4" in svg_dim["svg"]

    al_dim = client.get("/api/v1/syntax/dep/aligned/IR-IA_BR-SM/4?normalize_labels=true&dim_function_words=true").get_json()
    al_nodim = client.get("/api/v1/syntax/dep/aligned/IR-IA_BR-SM/4?normalize_labels=false&dim_function_words=false").get_json()
    assert "<svg" in al_dim["eng_svg"] and "<svg" in al_dim["tur_svg"]
    assert "opacity:0.4" in al_dim["eng_svg"] and "opacity:0.4" not in al_nodim["eng_svg"]
