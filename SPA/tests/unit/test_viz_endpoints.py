"""Unit tests verifying all visualization endpoints, help catalog, and payload budgets."""

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
    assert r1.status_code == 200 and len(r1.data) < 60_000
    d1 = r1.get_json()
    assert "items" in d1 and "title" in d1

    for url in (
        "/api/v1/corpus/verify-files",
        "/api/v1/corpus/size-summary",
        "/api/v1/corpus/memory-report",
        "/api/v1/corpus/content-lemmas",
    ):
        resp = client.get(url)
        assert resp.status_code == 200 and "columns" in resp.get_json()

    r6 = client.get("/api/v1/corpus/preview/IR-IA?n=3")
    assert r6.status_code == 200 and "tokens" in r6.get_json() and "sentences" in r6.get_json()

    r7 = client.post("/api/v1/corpus/evict-all")
    assert r7.status_code == 200 and "evicted_count" in r7.get_json()


def test_alignment_viz_endpoints(client):
    r1 = client.get("/api/v1/alignment/structure-summary")
    assert r1.status_code == 200 and len(r1.data) < 60_000
    d1 = r1.get_json()
    assert "table" in d1 and "stacked" in d1

    r2 = client.post("/api/v1/alignment/structure-scatter", json={"max_points": 50})
    assert r2.status_code == 200 and "series" in r2.get_json()


def test_syntax_viz_endpoints(client):
    r1 = client.get("/api/v1/syntax/pos/matrix?content_only=false")
    assert r1.status_code == 200 and len(r1.data) < 60_000
    d1 = r1.get_json()
    assert "rows" in d1 and "cols" in d1 and "values" in d1

    r2 = client.get("/api/v1/syntax/dep/aligned/IR-IA_BR-SM/4?normalize_labels=true&dim_function_words=true")
    assert r2.status_code == 200
    d2 = r2.get_json()
    assert "eng_svg" in d2 and "tur_svg" in d2 and "html" in d2
    assert "<svg" in d2["eng_svg"] and "opacity:0.4" in d2["eng_svg"]

    r3 = client.get("/api/v1/syntax/dep/aligned/IR-IA_BR-SM/4?normalize_labels=false&dim_function_words=false")
    assert r3.status_code == 200 and "opacity:0.4" not in r3.get_json()["eng_svg"]


def test_concordance_viz_endpoints(client):
    r1 = client.post("/api/v1/concordance/summary", json={"term": "robot"})
    assert r1.status_code == 200 and "table" in r1.get_json() and "bars" in r1.get_json()

    r2 = client.post("/api/v1/concordance/views-compare", json={"term": "robot"})
    assert r2.status_code == 200 and "rows" in r2.get_json()

    r3 = client.post("/api/v1/concordance/nltk", json={"code": "IR-IA", "word": "robot"})
    assert r3.status_code == 200 and "concordance" in r3.get_json()

    r4 = client.post("/api/v1/concordance/batch-matrices", json={"raw_input": "robot, uzay"})
    assert r4.status_code == 200 and "rates_matrix" in r4.get_json()

    r5 = client.post(
        "/api/v1/concordance/batch-dispersion",
        json={"terms": ["makine alanı: robot, makine | insan alanı: insan, adam"]},
    )
    assert r5.status_code == 200
    d5 = r5.get_json()
    assert len(d5["summary"]) == 4 and len(d5["pairwise"]) == 6


def test_lexicon_viz_endpoints(client):
    for url, payload, key in (
        ("/api/v1/lexicon/diversity/sensitivity", {"code": "IR-IA"}, "series"),
        ("/api/v1/lexicon/diversity/radar", {"codes": ["IR-IA", "BR-SM"]}, "series"),
        ("/api/v1/lexicon/diversity/mattr-trajectories", {"codes": ["IR-IA"], "window": 200}, "series"),
        ("/api/v1/lexicon/diversity/zipf-curves", {"codes": ["IR-IA"]}, "series"),
        ("/api/v1/lexicon/collocation/scatter", {"code": "BR-SM", "node": "robot"}, "series"),
        ("/api/v1/lexicon/collocation/sensitivity", {"code": "BR-SM", "node": "robot"}, "measures_table"),
        ("/api/v1/lexicon/collocation/nltk", {"code": "BR-SM"}, "collocations"),
    ):
        resp = client.post(url, json=payload)
        assert resp.status_code == 200 and key in resp.get_json()

    r2 = client.get("/api/v1/lexicon/diversity/compare")
    assert r2.status_code == 200 and "token_vs_lemma" in r2.get_json()

    r9 = client.get("/api/v1/lexicon/report/preview")
    assert r9.status_code == 200
    d9 = r9.get_json()
    assert "markdown" in d9 and "sections" in d9 and "kpis" in d9
    assert len(d9["sections"]) >= 2

    r10 = client.get("/api/v1/help/formulas")
    assert r10.status_code == 200
    d10 = r10.get_json()
    assert len(d10) == 12
    raw_help = r10.get_data(as_text=True)
    for forbidden in (r"\frac", r"\text", r"\sqrt"):
        assert forbidden not in raw_help
    assert "math-frac" in raw_help and "math-sqrt" in raw_help


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

    s_all = CorpusScopeDTO(scope="all")
    s_tr = CorpusScopeDTO(scope="all_tr", author_filter="SM")
    v_tok = TokenViewParamsDTO(field="tok", filter_function_words=False, mode="drop", punct="drop")
    v_lem = TokenViewParamsDTO(field="lem", filter_function_words=True, mode="mask", punct="split")

    k1 = global_payload_cache.build_key("inv:sizes_chart", scope=s_all, view=v_tok)
    k2 = global_payload_cache.build_key("inv:sizes_chart", scope=s_tr, view=v_tok)
    k3 = global_payload_cache.build_key("inv:sizes_chart", scope=s_all, view=v_lem)
    assert len({k1, k2, k3}) == 3

    global_payload_cache.put(k1, {"dummy": 1})
    assert global_payload_cache.get(k1) == {"dummy": 1}
    with app.test_client() as c:
        resp = c.post("/api/v1/corpus/evict-all")
        assert resp.status_code == 200
    assert global_payload_cache.get(k1) is None

    with app.test_client() as c:
        assert len(c.get("/api/v1/corpus/sizes-chart?scope=all").get_json()["items"]) == 13
        assert len(c.get("/api/v1/corpus/sizes-chart?scope=indig_tr").get_json()["items"]) == 3
        assert len(c.get("/api/v1/corpus/sizes-chart?scope=author_related&author_filter=SM").get_json()["items"]) == 3

        qs_tr = c.post(
            "/api/v1/export/quick-search",
            json={"term": "robot", "scope": {"scope": "author_turkish", "author_filter": "SM"}, "view_params": {"field": "lem", "filter_function_words": True, "mode": "mask", "punct": "strip"}},
        ).get_json()
        assert "author='SM'" in qs_tr["python_snippet"] and "mode='mask'" in qs_tr["python_snippet"]
