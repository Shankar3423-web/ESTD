"""Automated verification script executing the manual Postman test cases for Step 4."""
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

from backend.database.connection.session import get_engine, init_db
from backend.main import app

client = TestClient(app)


def print_test_header(num: int, title: str):
    print("\n" + "=" * 80)
    print(f"POSTMAN TEST {num}: {title}")
    print("=" * 80)


def reset_test_db():
    init_db()
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE estd_duplicate_index RESTART IDENTITY CASCADE;"))
        conn.commit()


def run_postman_tests():
    print("=" * 80)
    print("ESTD STEP 4 — LIVE POSTMAN API SIMULATION VERIFICATION")
    print("=" * 80)

    reset_test_db()

    base_content = (
        "OpenAI released a new reasoning model for software developers today. "
        "The system demonstrates enhanced capabilities across mathematical problem solving, "
        "complex algorithmic code generation, and multi-step logical deduction. "
        "Software engineers can integrate the new model immediately using the standard chat completions API endpoint."
    )

    article_a = {
        "title": "OpenAI released a new model for developers",
        "description": "A new reasoning model designed for developers.",
        "url": "https://techcrunch.com/2026/10/01/openai-reasoning-model",
        "canonical_url": "https://techcrunch.com/2026/10/01/openai-reasoning-model",
        "source_name": "TechCrunch",
        "source_type": "gnews",
        "author": "Jane Doe",
        "published_at": "2026-10-01T10:00:00Z",
        "category": "Artificial Intelligence",
        "collected_at": "2026-10-01T10:15:00Z",
        "cleaned_content": base_content,
        "content": base_content,
        "cleaning_status": "SUCCESS",
    }

    # -------------------------------------------------------------
    # TEST 1: Unique Article
    # -------------------------------------------------------------
    print_test_header(1, "Unique Article Evaluation")
    print("Endpoint: POST /api/v1/duplicate-detection/check")
    resp1 = client.post("/api/v1/duplicate-detection/check", json={"article": article_a})
    print(f"Status Code: {resp1.status_code}")
    data1 = resp1.json()
    print("Response:")
    print(json.dumps(data1, indent=2))

    assert resp1.status_code == 200
    assert data1["status"] == "success"
    assert data1["data"]["status"] == "unique"
    assert data1["data"]["decision"]["status"] == "UNIQUE"
    assert data1["data"]["decision"]["is_duplicate"] is False
    assert data1["data"]["decision"]["duplicate_reason"] is None
    print("[PASS] Test 1: First arrival classified as UNIQUE.")

    # -------------------------------------------------------------
    # TEST 2: Same URL with tracking parameters (Duplicate URL_MATCH)
    # -------------------------------------------------------------
    print_test_header(2, "Same URL Duplicate (URL_MATCH)")
    article_a_tracking = dict(article_a)
    article_a_tracking["url"] = "https://techcrunch.com/2026/10/01/openai-reasoning-model?utm_source=twitter&fbclid=abc"
    article_a_tracking["canonical_url"] = article_a_tracking["url"]

    print("Endpoint: POST /api/v1/duplicate-detection/check")
    resp2 = client.post("/api/v1/duplicate-detection/check", json={"article": article_a_tracking})
    print(f"Status Code: {resp2.status_code}")
    data2 = resp2.json()
    print("Response:")
    print(json.dumps(data2, indent=2))

    assert resp2.status_code == 200
    assert data2["data"]["status"] == "duplicate"
    assert data2["data"]["decision"]["status"] == "DUPLICATE"
    assert data2["data"]["decision"]["is_duplicate"] is True
    assert data2["data"]["decision"]["duplicate_reason"] == "URL_MATCH"
    print("[PASS] Test 2: URL match correctly classified as DUPLICATE via URL_MATCH.")

    # -------------------------------------------------------------
    # TEST 3: Exact Content, Different URL (Duplicate EXACT_CONTENT)
    # -------------------------------------------------------------
    print_test_header(3, "Exact Content Duplicate (EXACT_CONTENT)")
    article_exact = dict(article_a)
    article_exact["url"] = "https://theverge.com/2026/10/01/openai-model-launch"
    article_exact["canonical_url"] = article_exact["url"]
    article_exact["title"] = "The Verge: OpenAI Model Available"

    resp3 = client.post("/api/v1/duplicate-detection/check", json={"article": article_exact})
    print(f"Status Code: {resp3.status_code}")
    data3 = resp3.json()
    print("Response:")
    print(json.dumps(data3, indent=2))

    assert resp3.status_code == 200
    assert data3["data"]["status"] == "duplicate"
    assert data3["data"]["decision"]["duplicate_reason"] == "EXACT_CONTENT"
    print("[PASS] Test 3: Exact content match correctly classified as DUPLICATE via EXACT_CONTENT.")

    # -------------------------------------------------------------
    # TEST 4: Similar Wording, Different URL (Duplicate SIMILARITY)
    # -------------------------------------------------------------
    print_test_header(4, "Similar Wording Duplicate (SIMILARITY)")
    similar_content = (
        "OpenAI released a new reasoning model for software developers today. "
        "The system demonstrates enhanced capabilities across mathematical problem solving, "
        "complex algorithmic code generation, and multi-step logical deduction. "
        "Software engineers can integrate the model immediately using the standard API endpoint."
    )
    article_similar = dict(article_a)
    article_similar["url"] = "https://venturebeat.com/2026/10/01/openai-ai-dev-reasoning"
    article_similar["canonical_url"] = article_similar["url"]
    article_similar["title"] = "VentureBeat: OpenAI Launches AI Reasoning"
    article_similar["cleaned_content"] = similar_content
    article_similar["content"] = similar_content

    resp4 = client.post("/api/v1/duplicate-detection/check", json={"article": article_similar})
    print(f"Status Code: {resp4.status_code}")
    data4 = resp4.json()
    print("Response:")
    print(json.dumps(data4, indent=2))

    assert resp4.status_code == 200
    assert data4["data"]["status"] == "duplicate"
    assert data4["data"]["decision"]["duplicate_reason"] == "SIMILARITY"
    assert data4["data"]["decision"]["similarity_score"] is not None
    print(f"[PASS] Test 4: Similar article classified as DUPLICATE via SIMILARITY (score={data4['data']['decision']['similarity_score']}).")

    # -------------------------------------------------------------
    # TEST 5: Different Article (UNIQUE)
    # -------------------------------------------------------------
    print_test_header(5, "Different Article (UNIQUE)")
    diff_content = (
        "NASA astronomers have discovered an exoplanet orbiting a nearby red dwarf star. "
        "The planet lies within the habitable zone where liquid water could theoretically exist on the surface."
    )
    article_diff = {
        "title": "NASA discovers habitable exoplanet",
        "description": "Astronomers discover promising new world.",
        "url": "https://space.com/2026/10/01/habitable-exoplanet",
        "canonical_url": "https://space.com/2026/10/01/habitable-exoplanet",
        "source_name": "Space.com",
        "source_type": "rss",
        "author": "Dr. Sagan",
        "published_at": "2026-10-01T12:00:00Z",
        "category": "Science",
        "collected_at": "2026-10-01T12:10:00Z",
        "cleaned_content": diff_content,
        "content": diff_content,
        "cleaning_status": "SUCCESS",
    }

    resp5 = client.post("/api/v1/duplicate-detection/check", json={"article": article_diff})
    print(f"Status Code: {resp5.status_code}")
    data5 = resp5.json()
    print("Response:")
    print(json.dumps(data5, indent=2))

    assert resp5.status_code == 200
    assert data5["data"]["status"] == "unique"
    assert data5["data"]["decision"]["status"] == "UNIQUE"
    print("[PASS] Test 5: Different article classified as UNIQUE.")

    # -------------------------------------------------------------
    # TEST 6: Historical Deduplication
    # -------------------------------------------------------------
    print_test_header(6, "Historical Deduplication Persistence Check")
    # Query with article A again
    resp6 = client.post("/api/v1/duplicate-detection/check", json={"article": article_a})
    data6 = resp6.json()
    assert resp6.status_code == 200
    assert data6["data"]["status"] == "duplicate"
    assert data6["data"]["decision"]["detection_scope"] == "HISTORICAL"
    print("[PASS] Test 6: Historical persistence verified: original article recognized as historical duplicate.")

    # -------------------------------------------------------------
    # TEST 7: Batch Deduplication
    # -------------------------------------------------------------
    print_test_header(7, "Batch Deduplication [A, B, C, D]")
    b1 = dict(article_a); b1["url"] = "https://batch.com/1"
    b2 = dict(article_a); b2["url"] = "https://batch.com/2"
    b3 = dict(article_diff); b3["url"] = "https://batch.com/3"
    b4 = dict(article_diff); b4["url"] = "https://batch.com/4"

    resp7 = client.post("/api/v1/duplicate-detection/check-batch", json={"articles": [b1, b2, b3, b4]})
    data7 = resp7.json()
    print(f"Status Code: {resp7.status_code}")
    print(f"Total: {data7['total_count']}, Unique: {data7['unique_count']}, Duplicate: {data7['duplicate_count']}")
    assert resp7.status_code == 200
    assert data7["total_count"] == 4
    print("[PASS] Test 7: Batch deduplication successfully executed.")

    # -------------------------------------------------------------
    # TEST 8: Index Statistics Endpoint
    # -------------------------------------------------------------
    print_test_header(8, "Duplicate Index Statistics")
    resp8 = client.get("/api/v1/duplicate-detection/stats")
    data8 = resp8.json()
    print(f"Status Code: {resp8.status_code}")
    print(json.dumps(data8, indent=2))
    assert resp8.status_code == 200
    assert data8["total_indexed"] > 0
    print(f"[PASS] Test 8: Index stats verified (total_indexed={data8['total_indexed']}).")

    # -------------------------------------------------------------
    # TEST 9: Invalid Request Handling
    # -------------------------------------------------------------
    print_test_header(9, "Invalid Request Validation (422)")
    resp9 = client.post("/api/v1/duplicate-detection/check", json={"article": {"title": "Missing Fields"}})
    print(f"Status Code: {resp9.status_code}")
    print(json.dumps(resp9.json(), indent=2))
    assert resp9.status_code == 422
    print("[PASS] Test 9: Invalid request correctly rejected with 422.")

    print("\n" + "=" * 80)
    print("ALL LIVE POSTMAN SIMULATION TESTS PASSED!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_postman_tests()
