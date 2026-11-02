"""Automated verification script executing the 7 manual Postman test cases for Step 3."""
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
from backend.main import app

client = TestClient(app)


def print_test_header(num: int, title: str):
    print("\n" + "=" * 80)
    print(f"POSTMAN TEST {num}: {title}")
    print("=" * 80)


def test_1_valid_article():
    print_test_header(1, "Valid Article Cleaning")
    payload = {
        "title": "Quantum Computing Laboratory Achieves Sub-Kelvin Benchmark",
        "description": "Researchers maintain quantum coherence across multi-qubit processor.",
        "url": "https://science.example.com/quantum/sub-kelvin",
        "source_name": "Science Review",
        "source_type": "rss",
        "author": "Dr. Aris Thorne",
        "published_at": "2026-09-30T10:00:00Z",
        "category": "Science",
        "collected_at": "2026-09-30T10:15:00Z",
        "extraction_status": "EXTRACTED",
        "content": (
            "Physicists at the High Energy Consortium have demonstrated quantum telemetry "
            "over a forty-kilometer subterranean optical fiber network.\n\n"
            "The technique maintains coherence across entangled photon pairs despite thermal fluctuations.\n\n"
            "Commercial prototype modules are scheduled for field endurance testing throughout the coming year."
        ),
    }

    print("POST /api/v1/content-cleaning/clean")
    response = client.post("/api/v1/content-cleaning/clean", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    assert response.status_code == 200
    assert data["status"] == "success"
    assert data["data"]["cleaning_status"] == "SUCCESS"
    assert len(data["data"]["cleaned_content"]) > 100
    print("[RESULT] PASS: TEST 1 passed.")


def test_2_html_article():
    print_test_header(2, "HTML Article Cleaning")
    payload = {
        "title": "Autonomous Drone Navigation in GPS-Denied Environments",
        "url": "https://tech.example.com/drones/gps-denied",
        "source_type": "gnews",
        "category": "Technology",
        "collected_at": "2026-09-30T10:00:00Z",
        "extraction_status": "EXTRACTED",
        "content": (
            "<p>Autonomous aerial robotics systems often encounter severe degradation when operating "
            "in subterranean caverns or dense urban canyons where satellite positioning signals are obstructed.</p>"
            "<div class='ad-banner'>Advertisement: Discover Best Drones</div>"
            "<p>A novel vision-inertial odometry pipeline utilizing neuromorphic event cameras has demonstrated "
            "centimeter-level localization accuracy under zero-illumination conditions.</p>"
        ),
    }

    print("POST /api/v1/content-cleaning/clean")
    response = client.post("/api/v1/content-cleaning/clean", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    assert response.status_code == 200
    assert data["status"] == "success"
    assert "<p>" not in data["data"]["cleaned_content"]
    assert "Advertisement" not in data["data"]["cleaned_content"]
    assert "Autonomous aerial robotics systems" in data["data"]["cleaned_content"]
    print("[RESULT] PASS: TEST 2 passed (HTML tags removed, article preserved).")


def test_3_boilerplate_article():
    print_test_header(3, "Article with Boilerplate")
    payload = {
        "title": "Central Bank Announces Digital Currency Pilot",
        "url": "https://finance.example.com/cbdc-pilot",
        "source_type": "newsdata",
        "category": "Business",
        "collected_at": "2026-09-30T10:00:00Z",
        "extraction_status": "EXTRACTED",
        "content": (
            "We use cookies to improve your experience. Accept all cookies.\n\n"
            "ADVERTISEMENT\n\n"
            "The monetary authority unveiled technical specifications for its sovereign retail digital "
            "currency pilot today. Interoperability with existing commercial banking infrastructure was highlighted.\n\n"
            "Sign up for our daily newsletter to receive financial alerts directly in your inbox.\n\n"
            "Share this article on Twitter | Share on LinkedIn\n\n"
            "All rights reserved. Copyright 2026 Global Finance Media."
        ),
    }

    print("POST /api/v1/content-cleaning/clean")
    response = client.post("/api/v1/content-cleaning/clean", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    assert response.status_code == 200
    assert data["status"] == "success"
    cleaned = data["data"]["cleaned_content"]
    assert "We use cookies" not in cleaned
    assert "ADVERTISEMENT" not in cleaned
    assert "Sign up for our daily newsletter" not in cleaned
    assert "All rights reserved" not in cleaned
    assert "The monetary authority unveiled technical specifications" in cleaned
    print("[RESULT] PASS: TEST 3 passed (boilerplate removed).")


def test_4_existing_clean_article():
    print_test_header(4, "Existing Clean Article")
    body = (
        "Higher education institutions are increasingly incorporating adaptive artificial intelligence "
        "tutors into foundational mathematics courses. Preliminary longitudinal data demonstrates a "
        "twelve percent increase in retention rates among first-year engineering cohorts."
    )
    payload = {
        "title": "Universities Adopt Adaptive AI Tutors in STEM Curricula",
        "url": "https://education.example.com/ai-tutors",
        "source_type": "rss",
        "category": "Education",
        "collected_at": "2026-09-30T10:00:00Z",
        "extraction_status": "CONTENT_ALREADY_AVAILABLE",
        "content": body,
    }

    print("POST /api/v1/content-cleaning/clean")
    response = client.post("/api/v1/content-cleaning/clean", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    assert response.status_code == 200
    assert data["status"] == "success"
    assert data["data"]["cleaning_status"] == "SUCCESS"
    assert data["data"]["cleaned_content"] == body
    print("[RESULT] PASS: TEST 4 passed (content remains clean and essentially unchanged).")


def test_5_empty_content():
    print_test_header(5, "Empty Content Handling")
    payload = {
        "title": "Article Missing Extracted Content",
        "url": "https://example.com/no-content-story",
        "source_type": "rss",
        "category": "Technology",
        "collected_at": "2026-09-30T10:00:00Z",
        "extraction_status": "EXTRACTION_FAILED",
        "content": None,
    }

    print("POST /api/v1/content-cleaning/clean")
    response = client.post("/api/v1/content-cleaning/clean", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    assert response.status_code == 200
    assert data["status"] == "failed"
    assert data["data"]["cleaning_status"] == "CLEANING_FAILED"
    assert data["data"]["cleaned_content"] is None
    assert "empty or contains no readable text" in data["data"]["error_message"]
    print("[RESULT] PASS: TEST 5 passed (controlled validation/cleaning failure returned).")


def test_6_invalid_request():
    print_test_header(6, "Invalid Request (Schema Validation)")
    # Missing required fields like title and url, invalid category
    payload = {
        "category": "InvalidCategoryName",
        "content": "Some body text here.",
    }

    print("POST /api/v1/content-cleaning/clean")
    response = client.post("/api/v1/content-cleaning/clean", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    assert response.status_code == 422
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    print("[RESULT] PASS: TEST 6 passed (controlled 422 validation error returned).")


def test_7_real_step2_output():
    print_test_header(7, "Real Step 2 Output Cleaning")
    # Take an actual ExtractedArticle output contract from Step 2
    step2_output = {
        "title": "Frontier AI Safety Framework Published by Research Consortium",
        "description": "Standardized evaluation suite for automated capability assessments.",
        "url": "https://technews.example.com/safety-framework-2026",
        "source_name": "TechNews",
        "source_type": "gnews",
        "author": "Dr. Sarah Lin",
        "published_at": "2026-09-30T14:00:00Z",
        "category": "Artificial Intelligence",
        "image_url": "https://technews.example.com/img/framework.jpg",
        "collected_at": "2026-09-30T14:15:00Z",
        "canonical_url": "https://technews.example.com/safety-framework-2026",
        "extraction_status": "EXTRACTED",
        "extraction_method": "article_web_extraction",
        "extracted_at": "2026-09-30T14:15:05Z",
        "error_message": None,
        "content": (
            "<div>ADVERTISEMENT</div>\n\n"
            "<p>A global coalition of machine learning safety labs today published unified technical "
            "benchmarks for assessing red-teaming resilience in autonomous agents.</p>\n\n"
            "Sign up for our AI newsletter for weekly industry updates.\n\n"
            "<p>The framework specifies rigorous empirical stress tests targeting alignment drift, "
            "cybersecurity vulnerability discovery, and multi-agent coordination risks.</p>\n\n"
            "Share this article on Twitter | Share on LinkedIn"
        ),
    }

    print("POST /api/v1/content-cleaning/clean")
    response = client.post("/api/v1/content-cleaning/clean", json=step2_output)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    assert response.status_code == 200
    assert data["status"] == "success"
    assert data["data"]["cleaning_status"] == "SUCCESS"
    assert data["data"]["category"] == "Artificial Intelligence"
    assert data["data"]["author"] == "Dr. Sarah Lin"
    assert data["data"]["original_content_length"] > data["data"]["cleaned_content_length"]
    assert "A global coalition of machine learning safety labs" in data["data"]["cleaned_content"]
    assert "ADVERTISEMENT" not in data["data"]["cleaned_content"]
    print("[RESULT] PASS: TEST 7 passed (real Step 2 article cleaned successfully).")


def run_all_manual_tests():
    print("\n" + "=" * 80)
    print("ESTD STEP 3 — POSTMAN MANUAL TEST VERIFICATION SUITE")
    print("=" * 80)

    test_1_valid_article()
    test_2_html_article()
    test_3_boilerplate_article()
    test_4_existing_clean_article()
    test_5_empty_content()
    test_6_invalid_request()
    test_7_real_step2_output()

    print("\n" + "=" * 80)
    print("ALL 7 POSTMAN MANUAL VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_manual_tests()
