"""Manual API / Postman verification script testing all Step 1 and Step 2 endpoints against a live server."""
import json
import sys
import httpx

BASE_URL = "http://127.0.0.1:8000"


def main():
    print("=" * 70)
    print("ESTD LIVE SERVER MANUAL API VERIFICATION")
    print(f"Target Base URL: {BASE_URL}")
    print("=" * 70)

    results = {}

    with httpx.Client(base_url=BASE_URL, timeout=20.0) as client:
        # 1. Health check
        print("\n[1] Testing GET /health...")
        try:
            r = client.get("/health")
            print(f"Status: {r.status_code} | Body: {r.text}")
            assert r.status_code == 200
            assert r.json().get("status") in ("ok", "healthy")
            results["health"] = "PASS"
        except Exception as e:
            print(f"FAILED: {e}")
            results["health"] = f"FAIL: {e}"

        # 2. Step 1 RSS
        print("\n[2] Testing GET /api/v1/source-collection/rss...")
        try:
            r = client.get("/api/v1/source-collection/rss?category=Technology&limit=2")
            print(f"Status: {r.status_code} | Items: {r.json().get('count')}")
            assert r.status_code == 200
            assert r.json().get("provider") == "rss"
            results["step1_rss"] = "PASS"
        except Exception as e:
            print(f"FAILED: {e}")
            results["step1_rss"] = f"FAIL: {e}"

        # 3. Step 1 GNews
        print("\n[3] Testing GET /api/v1/source-collection/gnews...")
        try:
            r = client.get("/api/v1/source-collection/gnews?category=Technology&limit=1")
            print(f"Status: {r.status_code} | Response: {r.text[:120]}...")
            # Note: GNews returns 200 if key valid, or 502/429/500 if key expired/quota
            results["step1_gnews"] = f"STATUS_{r.status_code}"
        except Exception as e:
            print(f"FAILED: {e}")
            results["step1_gnews"] = f"FAIL: {e}"

        # 4. Step 1 NewsData
        print("\n[4] Testing GET /api/v1/source-collection/newsdata...")
        try:
            r = client.get("/api/v1/source-collection/newsdata?category=Science&limit=1")
            print(f"Status: {r.status_code} | Response: {r.text[:120]}...")
            results["step1_newsdata"] = f"STATUS_{r.status_code}"
        except Exception as e:
            print(f"FAILED: {e}")
            results["step1_newsdata"] = f"FAIL: {e}"

        # 5. Step 2 Test 1: Valid article URL
        print("\n[5] Step 2 Test 1: Valid article URL...")
        payload_test1 = {
            "title": "Artificial Intelligence - Wikipedia",
            "description": "Overview of AI history and concepts.",
            "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
            "source_type": "web",
            "category": "Artificial Intelligence",
        }
        try:
            r = client.post("/api/v1/article-extraction/extract", json=payload_test1)
            print(f"Status: {r.status_code}")
            resp = r.json()
            print(f"Extraction Status: {resp['data']['extraction_status']}")
            print(f"Content Length: {len(resp['data']['content'] or '')}")
            assert r.status_code == 200
            assert resp["data"]["extraction_status"] == "EXTRACTED"
            assert resp["data"]["content"] is not None
            results["step2_test1_valid_url"] = "PASS"
        except Exception as e:
            print(f"FAILED: {e}")
            results["step2_test1_valid_url"] = f"FAIL: {e}"

        # 6. Step 2 Test 2: Existing sufficient content (no scrape)
        print("\n[6] Step 2 Test 2: Existing sufficient content...")
        full_text = (
            "Researchers at the National Renewable Energy Laboratory have demonstrated a scalable "
            "perovskite tandem solar cell retaining ninety-five percent of initial power conversion efficiency "
            "after one thousand hours of continuous unencumbered accelerated thermal stress testing. "
            "The modular prototype will be integrated into distributed regional microgrid pilot installations "
            "commencing in early 2027 across multiple high-insolation test corridors."
        )
        payload_test2 = {
            "title": "Perovskite Tandem Solar Cell Durability Breakthrough",
            "description": full_text,
            "url": "https://example.com/solar-durability",
            "source_type": "rss",
            "category": "Technology",
        }
        try:
            r = client.post("/api/v1/article-extraction/extract", json=payload_test2)
            print(f"Status: {r.status_code}")
            resp = r.json()
            print(f"Extraction Status: {resp['data']['extraction_status']}")
            print(f"Extraction Method: {resp['data']['extraction_method']}")
            assert r.status_code == 200
            assert resp["data"]["extraction_status"] == "CONTENT_ALREADY_AVAILABLE"
            assert resp["data"]["extraction_method"] == "existing_source_content"
            assert resp["data"]["content"] == full_text
            results["step2_test2_existing_content"] = "PASS"
        except Exception as e:
            print(f"FAILED: {e}")
            results["step2_test2_existing_content"] = f"FAIL: {e}"

        # 7. Step 2 Test 3: Invalid URL
        print("\n[7] Step 2 Test 3: Invalid URL...")
        payload_test3 = {
            "title": "Invalid Scheme Item",
            "description": "Short description",
            "url": "ftp://malformed-scheme.com/file",
            "source_type": "gnews",
            "category": "Technology",
        }
        try:
            r = client.post("/api/v1/article-extraction/extract", json=payload_test3)
            print(f"Status: {r.status_code} | Body: {r.text}")
            assert r.status_code == 400
            err = r.json()
            assert "error" in err
            results["step2_test3_invalid_url"] = "PASS"
        except Exception as e:
            print(f"FAILED: {e}")
            results["step2_test3_invalid_url"] = f"FAIL: {e}"

        # 8. Step 2 Test 4: Unreachable URL
        print("\n[8] Step 2 Test 4: Unreachable URL...")
        payload_test4 = {
            "title": "Unreachable Article",
            "description": "Short description",
            "url": "https://unreachable-domain-xyz-987654321.org/story",
            "source_type": "newsdata",
            "category": "Business",
        }
        try:
            r = client.post("/api/v1/article-extraction/extract", json=payload_test4)
            print(f"Status: {r.status_code}")
            resp = r.json()
            print(f"Extraction Status: {resp['data']['extraction_status']}")
            print(f"Error Message: {resp['data']['error_message']}")
            assert r.status_code == 200
            assert resp["status"] == "failed"
            assert resp["data"]["extraction_status"] == "EXTRACTION_FAILED"
            assert resp["data"]["error_message"] is not None
            results["step2_test4_unreachable_url"] = "PASS"
        except Exception as e:
            print(f"FAILED: {e}")
            results["step2_test4_unreachable_url"] = f"FAIL: {e}"

        # 9. Step 2 Test 5: Article page with insufficient extractable content
        print("\n[9] Step 2 Test 5: Insufficient extractable content...")
        payload_test5 = {
            "title": "Non-existent Page",
            "description": "Snippet",
            "url": "https://httpbin.org/status/404",
            "source_type": "gnews",
            "category": "Technology",
        }
        try:
            r = client.post("/api/v1/article-extraction/extract", json=payload_test5)
            print(f"Status: {r.status_code}")
            resp = r.json()
            print(f"Extraction Status: {resp['data']['extraction_status']}")
            print(f"Error Message: {resp['data']['error_message']}")
            assert r.status_code == 200
            assert resp["status"] == "failed"
            assert resp["data"]["extraction_status"] == "EXTRACTION_FAILED"
            results["step2_test5_insufficient_content"] = "PASS"
        except Exception as e:
            print(f"FAILED: {e}")
            results["step2_test5_insufficient_content"] = f"FAIL: {e}"

    print("\n" + "=" * 70)
    print("FINAL SUMMARY RESULTS:")
    print(json.dumps(results, indent=2))
    print("=" * 70)

    # Return exit code based on critical failures
    critical = [
        results.get("health") == "PASS",
        results.get("step1_rss") == "PASS",
        results.get("step2_test1_valid_url") == "PASS",
        results.get("step2_test2_existing_content") == "PASS",
        results.get("step2_test3_invalid_url") == "PASS",
        results.get("step2_test4_unreachable_url") == "PASS",
        results.get("step2_test5_insufficient_content") == "PASS",
    ]
    if all(critical):
        print("ALL CRITICAL POSTMAN / LIVE API TESTS PASSED!")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()
