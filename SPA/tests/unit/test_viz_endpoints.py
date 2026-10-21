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
