"""Unit tests verifying all new visualization endpoints and payload budgets."""

import pytest

from SPA.app import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_corpus_viz_endpoints(client):
    r1 = client.get("/api/v1/corpus/sizes-chart")
    assert r1.status_code == 200
    assert len(r1.data) < 60_000
    d1 = r1.get_json()
    assert "items" in d1 and "title" in d1

    r2 = client.get("/api/v1/corpus/verify-files")
    assert r2.status_code == 200
    assert "columns" in r2.get_json()

    r3 = client.get("/api/v1/corpus/size-summary")
    assert r3.status_code == 200
    assert "columns" in r3.get_json()

    r4 = client.get("/api/v1/corpus/memory-report")
    assert r4.status_code == 200
    assert "columns" in r4.get_json()

    r5 = client.get("/api/v1/corpus/content-lemmas")
    assert r5.status_code == 200
    assert "columns" in r5.get_json()

    r6 = client.get("/api/v1/corpus/preview/IR-IA?n=3")
    assert r6.status_code == 200
    assert "tokens" in r6.get_json() and "sentences" in r6.get_json()

    r7 = client.post("/api/v1/corpus/evict-all")
    assert r7.status_code == 200
    assert "evicted_count" in r7.get_json()


def test_alignment_viz_endpoints(client):
    r1 = client.get("/api/v1/alignment/structure-summary")
    assert r1.status_code == 200
    assert len(r1.data) < 60_000
    d1 = r1.get_json()
    assert "table" in d1 and "stacked" in d1

    r2 = client.post("/api/v1/alignment/structure-scatter", json={"max_points": 50})
    assert r2.status_code == 200
    assert "series" in r2.get_json()


def test_syntax_viz_endpoints(client):
    r1 = client.get("/api/v1/syntax/pos/matrix?content_only=false")
    assert r1.status_code == 200
    assert len(r1.data) < 60_000
    d1 = r1.get_json()
    assert "rows" in d1 and "cols" in d1 and "values" in d1

    r2 = client.get("/api/v1/syntax/dep/aligned/IR-IA_BR-SM/4?normalize_labels=true&dim_function_words=true")
    assert r2.status_code == 200
    d2 = r2.get_json()
    assert "eng_svg" in d2 and "tur_svg" in d2 and "html" in d2
    assert "<svg" in d2["eng_svg"] and "<svg" in d2["tur_svg"]
    assert "opacity:0.4" in d2["eng_svg"]

    r3 = client.get("/api/v1/syntax/dep/aligned/IR-IA_BR-SM/4?normalize_labels=false&dim_function_words=false")
    assert r3.status_code == 200
    d3 = r3.get_json()
    assert "opacity:0.4" not in d3["eng_svg"]


def test_concordance_viz_endpoints(client):
    r1 = client.post("/api/v1/concordance/summary", json={"term": "robot"})
    assert r1.status_code == 200
    assert "table" in r1.get_json() and "bars" in r1.get_json()

    r2 = client.post("/api/v1/concordance/views-compare", json={"term": "robot"})
    assert r2.status_code == 200
    assert "rows" in r2.get_json()

    r3 = client.post("/api/v1/concordance/nltk", json={"code": "IR-IA", "word": "robot"})
    assert r3.status_code == 200
    assert "concordance" in r3.get_json()

    r4 = client.post("/api/v1/concordance/batch-matrices", json={"raw_input": "robot, uzay"})
    assert r4.status_code == 200
    assert "rates_matrix" in r4.get_json()

    r5 = client.post(
        "/api/v1/concordance/batch-dispersion",
        json={"terms": ["makine alanı: robot, makine | insan alanı: insan, adam"]},
    )
    assert r5.status_code == 200
    d5 = r5.get_json()
    assert len(d5["summary"]) == 4
    assert len(d5["pairwise"]) == 6


def test_lexicon_viz_endpoints(client):
    r1 = client.post("/api/v1/lexicon/diversity/sensitivity", json={"code": "IR-IA"})
    assert r1.status_code == 200
    assert "series" in r1.get_json()

    r2 = client.get("/api/v1/lexicon/diversity/compare")
    assert r2.status_code == 200
    assert "token_vs_lemma" in r2.get_json()

    r3 = client.post("/api/v1/lexicon/diversity/radar", json={"codes": ["IR-IA", "BR-SM"]})
    assert r3.status_code == 200
    assert "series" in r3.get_json()

    r4 = client.post("/api/v1/lexicon/diversity/mattr-trajectories", json={"codes": ["IR-IA"], "window": 200})
    assert r4.status_code == 200
    assert "series" in r4.get_json()

    r5 = client.post("/api/v1/lexicon/diversity/zipf-curves", json={"codes": ["IR-IA"]})
    assert r5.status_code == 200
    assert "series" in r5.get_json()

    r6 = client.post("/api/v1/lexicon/collocation/scatter", json={"code": "BR-SM", "node": "robot"})
    assert r6.status_code == 200
    assert "series" in r6.get_json()

    r7 = client.post("/api/v1/lexicon/collocation/sensitivity", json={"code": "BR-SM", "node": "robot"})
    assert r7.status_code == 200
    assert "measures_table" in r7.get_json()

    r8 = client.post("/api/v1/lexicon/collocation/nltk", json={"code": "BR-SM"})
    assert r8.status_code == 200
    assert "collocations" in r8.get_json()

    r9 = client.get("/api/v1/lexicon/report/preview")
    assert r9.status_code == 200
    assert "markdown" in r9.get_json()


def test_single_shared_corpus_loader_and_payload_cache_keying():
    from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
    from SPA.services.payload_cache import global_payload_cache

    app = create_app()
    repo = app.extensions["corpus_repo"]
    services = app.extensions["services"]
    assert len(services) >= 15

    loader_id = id(repo._loader)
    for name, svc in services.items():
        assert hasattr(svc, "_repo"), f"Service {name} missing _repo attribute"
        assert id(svc._repo) == id(repo), f"Service {name} uses duplicate CorpusRepository"
        assert id(svc._repo._loader) == loader_id, f"Service {name} uses duplicate CorpusLoader"

    # Verify PayloadCache.build_key distinguishes scope and view_params
    s_all = CorpusScopeDTO(scope="all")
    s_tr = CorpusScopeDTO(scope="all_tr", author_filter="SM")
    v_tok = TokenViewParamsDTO(field="tok", filter_function_words=False, mode="drop", punct="drop")
    v_lem = TokenViewParamsDTO(field="lem", filter_function_words=True, mode="mask", punct="split")

    k1 = global_payload_cache.build_key("inv:sizes_chart", scope=s_all, view=v_tok)
    k2 = global_payload_cache.build_key("inv:sizes_chart", scope=s_tr, view=v_tok)
    k3 = global_payload_cache.build_key("inv:sizes_chart", scope=s_all, view=v_lem)
    assert len({k1, k2, k3}) == 3

    # Verify /api/v1/corpus/evict-all clears global_payload_cache
    global_payload_cache.put(k1, {"dummy": 1})
    assert global_payload_cache.get(k1) == {"dummy": 1}
    with app.test_client() as c:
        resp = c.post("/api/v1/corpus/evict-all")
        assert resp.status_code == 200
    assert global_payload_cache.get(k1) is None

    # Verify endpoints return distinct results across scopes and TokenView params
    with app.test_client() as c:
        s_all_resp = c.get("/api/v1/corpus/sizes-chart?scope=all").get_json()
        s_ind_resp = c.get("/api/v1/corpus/sizes-chart?scope=indig_tr").get_json()
        assert len(s_all_resp["items"]) == 13
        assert len(s_ind_resp["items"]) == 3

        s_auth_resp = c.get("/api/v1/corpus/sizes-chart?scope=author_related&author_filter=SM").get_json()
        assert len(s_auth_resp["items"]) == 3

        qs_tr = c.post(
            "/api/v1/export/quick-search",
            json={"term": "robot", "scope": {"scope": "author_turkish", "author_filter": "SM"}, "view_params": {"field": "lem", "filter_function_words": True, "mode": "mask", "punct": "strip"}},
        ).get_json()
        assert "author='SM'" in qs_tr["python_snippet"]
        assert "mode='mask'" in qs_tr["python_snippet"]


