"""Automated simulation script executing the 10 Postman test cases for Step 5."""
import json
import sys
from pathlib import Path

# Add backend and project root to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.common.constants.categories import VALID_CATEGORIES
from backend.database.connection.session import get_engine, init_db
from backend.main import app

client = TestClient(app)


def print_test_header(num: int, title: str):
    print("\n" + "=" * 80)
    print(f"POSTMAN TEST {num}: {title}")
    print("=" * 80)


def reset_test_data():
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM news_articles WHERE url LIKE '%example.com%' OR url LIKE '%postman%';"))
        conn.commit()


def run_postman_tests():
    print("=" * 80)
    print("ESTD STEP 5 — LIVE POSTMAN API SIMULATION VERIFICATION")
    print("=" * 80)

    reset_test_data()
    all_passed = True

    # -------------------------------------------------------------
    # TEST 1: Database health -> 200
    # -------------------------------------------------------------
    print_test_header(1, "Database health -> GET /api/v1/knowledge/health")
    res1 = client.get("/api/v1/knowledge/health")
    print("Status:", res1.status_code)
    print("Response:", json.dumps(res1.json(), indent=2))
    assert res1.status_code == 200
    assert res1.json()["status"] == "healthy"
    print(">>> TEST 1 RESULT: PASS")

    # -------------------------------------------------------------
    # TEST 2: Create valid article -> 201
    # -------------------------------------------------------------
    print_test_header(2, "Create valid article -> POST /api/v1/knowledge/articles")
    payload_article = {
        "title": "Quantum Computing Lab Unveils 1000-Qubit Processor",
        "description": "Commercial availability projected for quantum simulation.",
        "content": "Researchers have successfully operated a 1000-qubit quantum processor with high gate fidelity and error suppression.",
        "url": "https://example.com/postman-quantum-1000",
        "source_name": "Tech Times",
        "source_type": "rss",
        "author": "Dr. Quantum",
        "published_at": "2026-10-05T08:00:00Z",
        "category": "Technology",
    }
    res2 = client.post("/api/v1/knowledge/articles", json=payload_article)
    print("Status:", res2.status_code)
    print("Response:", json.dumps(res2.json(), indent=2))
    assert res2.status_code == 201
    created_id = res2.json()["data"]["id"]
    print(">>> TEST 2 RESULT: PASS")

    # -------------------------------------------------------------
    # TEST 3: Retrieve created article -> 200
    # -------------------------------------------------------------
    print_test_header(3, f"Retrieve created article -> GET /api/v1/knowledge/articles/{created_id}")
    res3 = client.get(f"/api/v1/knowledge/articles/{created_id}")
    print("Status:", res3.status_code)
    print("Response:", json.dumps(res3.json(), indent=2))
    assert res3.status_code == 200
    assert res3.json()["data"]["id"] == created_id
    print(">>> TEST 3 RESULT: PASS")

    # -------------------------------------------------------------
    # TEST 4: List articles -> 200
    # -------------------------------------------------------------
    print_test_header(4, "List articles -> GET /api/v1/knowledge/articles")
    res4 = client.get("/api/v1/knowledge/articles")
    print("Status:", res4.status_code)
    data4 = res4.json()
    print(f"Total returned: {len(data4['data']['items'])} items | pagination: {data4['data']['pagination']}")
    assert res4.status_code == 200
    assert data4["data"]["pagination"]["total_items"] >= 1
    print(">>> TEST 4 RESULT: PASS")

    # -------------------------------------------------------------
    # TEST 5: Filter Science -> only Science articles
    # -------------------------------------------------------------
    print_test_header(5, "Filter Science -> GET /api/v1/knowledge/articles?category=Science")
    # Seed science article first
    client.post("/api/v1/knowledge/articles", json={
        "title": "Exoplanet Biosignature Discovery",
        "content": "Atmospheric methane and oxygen co-occurrence detected on nearby super-Earth world.",
        "url": "https://example.com/postman-science-exoplanet",
        "category": "Science",
    })
    res5 = client.get("/api/v1/knowledge/articles?category=Science")
    print("Status:", res5.status_code)
    items5 = res5.json()["data"]["items"]
    print(f"Science items found: {len(items5)}")
    assert res5.status_code == 200
    assert all(it["category"] == "Science" for it in items5)
    print(">>> TEST 5 RESULT: PASS")

    # -------------------------------------------------------------
    # TEST 6: Filter Technology -> only Technology articles
    # -------------------------------------------------------------
    print_test_header(6, "Filter Technology -> GET /api/v1/knowledge/articles?category=Technology")
    res6 = client.get("/api/v1/knowledge/articles?category=Technology")
    print("Status:", res6.status_code)
    items6 = res6.json()["data"]["items"]
    print(f"Technology items found: {len(items6)}")
    assert res6.status_code == 200
    assert all(it["category"] == "Technology" for it in items6)
    print(">>> TEST 6 RESULT: PASS")

    # -------------------------------------------------------------
    # TEST 7: Invalid category -> 400 validation error
    # -------------------------------------------------------------
    print_test_header(7, "Invalid category -> GET /api/v1/knowledge/articles?category=Sports")
    res7 = client.get("/api/v1/knowledge/articles?category=Sports")
    print("Status:", res7.status_code)
    print("Response:", json.dumps(res7.json(), indent=2))
    assert res7.status_code == 400
    assert res7.json()["error"]["code"] == "INVALID_CATEGORY"
    print(">>> TEST 7 RESULT: PASS")

    # -------------------------------------------------------------
    # TEST 8: Duplicate article -> safely rejected (409)
    # -------------------------------------------------------------
    print_test_header(8, "Duplicate article -> POST /api/v1/knowledge/articles with same URL")
    res8 = client.post("/api/v1/knowledge/articles", json=payload_article)
    print("Status:", res8.status_code)
    print("Response:", json.dumps(res8.json(), indent=2))
    assert res8.status_code == 409
    assert res8.json()["error"]["code"] == "DUPLICATE_ARTICLE"
    print(">>> TEST 8 RESULT: PASS")

    # -------------------------------------------------------------
    # TEST 9: Pagination -> correct page and metadata
    # -------------------------------------------------------------
    print_test_header(9, "Pagination -> GET /api/v1/knowledge/articles?page=1&page_size=1")
    res9 = client.get("/api/v1/knowledge/articles?page=1&page_size=1")
    print("Status:", res9.status_code)
    meta9 = res9.json()["data"]["pagination"]
    print("Pagination metadata:", json.dumps(meta9, indent=2))
    assert res9.status_code == 200
    assert meta9["page"] == 1
    assert meta9["page_size"] == 1
    assert len(res9.json()["data"]["items"]) == 1
    assert meta9["total_items"] >= 2
    print(">>> TEST 9 RESULT: PASS")

    # -------------------------------------------------------------
    # TEST 10: Five category coverage -> all five categories work
    # -------------------------------------------------------------
    print_test_header(10, "Five category coverage -> Verify all 5 categories persist and query")
    res10_cats = client.get("/api/v1/knowledge/categories")
    assert res10_cats.status_code == 200
    assert res10_cats.json()["total"] == 5

    for cat in VALID_CATEGORIES:
        art_res = client.post("/api/v1/knowledge/articles", json={
            "title": f"Coverage Verification Headline for {cat}",
            "content": f"Verified content block demonstrating persistence for category {cat}.",
            "url": f"https://example.com/postman-coverage-{cat.lower().replace(' ', '-')}",
            "category": cat,
        })
        assert art_res.status_code == 201
        print(f"  [Category: {cat}] Persisted ID={art_res.json()['data']['id']}")

        # Query filter for this category
        filter_res = client.get(f"/api/v1/knowledge/articles?category={cat}")
        assert filter_res.status_code == 200
        assert filter_res.json()["data"]["pagination"]["total_items"] >= 1

    print(">>> TEST 10 RESULT: PASS")

    # Clean test data
    reset_test_data()

    print("\n" + "=" * 80)
    print("ALL 10 POSTMAN TEST CASES COMPLETED AND PASSED!")
    print("=" * 80)


if __name__ == "__main__":
    run_postman_tests()
