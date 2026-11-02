"""ESTD Step 7 — Master Validation and Verification Script.

Executes and verifies:
1. Gemini API connectivity & model availability
2. MCP-First Article Retrieval (Step 7 -> Step 6 MCP -> PostgreSQL)
3. End-to-End Real Generation on 5 Categories:
   - Artificial Intelligence
   - Technology
   - Business
   - Education
   - Science
4. Anti-Hallucination & Source Grounding Verification
5. Duplicate Generation Prevention Check
6. Security & Credential Protection Checks
"""
import json
import sys
import time
from pathlib import Path

# Ensure paths
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.common.constants.categories import ESTDCategory, VALID_CATEGORIES
from backend.step6_mcp.services.mcp_service import MCPService
from backend.step7_content_generation.client.gemini_client import GeminiClient
from backend.step7_content_generation.config.gemini_settings import get_gemini_settings
from backend.step7_content_generation.schemas.generated_news import GeneratedNews
from backend.step7_content_generation.schemas.generation_request import (
    ArticleGenerationRequest,
    GenerationResponse,
)
from backend.step7_content_generation.services.generation_service import GenerationService
from backend.step7_content_generation.services.mcp_generation_service import (
    MCPGenerationService,
)
from backend.step7_content_generation.validators.generation_validator import (
    GenerationValidator,
)


def print_header(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()}")
    print("=" * 80)


def main():
    print_header("ESTD STEP 7 — REAL PIPELINE INTEGRATION VERIFICATION")
    settings = get_gemini_settings()

    # -------------------------------------------------------------------------
    # 1. Gemini Configuration & Connectivity Verification
    # -------------------------------------------------------------------------
    print_header("1. GEMINI CONFIGURATION & CONNECTIVITY")
    assert settings.has_api_key(), "FAIL: GEMINI_API_KEY is not configured in backend/.env"
    print(f"[*] API Key Present: YES (length={len(settings.get_gemini_api_key())}, sanitized)")
    print(f"[*] Model Selected:  {settings.gemini_model}")
    print(f"[*] Temperature:     {settings.gemini_temperature}")
    print(f"[*] Max Retries:     {settings.gemini_max_retries}")

    client = GeminiClient(settings=settings)
    conn_result = client.test_connectivity()
    print(f"[*] Connectivity:    {conn_result['status'].upper()} (Latency: {conn_result['latency_ms']}ms)")
    assert conn_result["status"] == "connected", "FAIL: Could not ping Gemini API"
    print("[PASS] Gemini Connectivity Verified successfully.\n")

    # -------------------------------------------------------------------------
    # 2. Step 6 PostgreSQL MCP Discovery & Retrieval
    # -------------------------------------------------------------------------
    print_header("2. STEP 6 MCP -> POSTGRESQL ARTICLE RETRIEVAL")
    mcp_service = MCPService()
    mcp_gen_service = MCPGenerationService(mcp_service=mcp_service, generation_service=GenerationService(settings, client))

    eligible = mcp_gen_service.list_eligible_articles(limit=20)
    print(f"[*] Eligible Articles Discovered via MCP: {len(eligible)}")
    for a in eligible:
        print(f"    - ID: {a.id:<3} | Category: {a.category:<24} | Source: {str(a.source_name):<20} | Length: {a.content_length} chars")
    assert len(eligible) > 0, "FAIL: No eligible articles found in PostgreSQL via MCP"
    print("[PASS] Step 6 MCP Database Access & Discovery Verified.\n")

    # -------------------------------------------------------------------------
    # 3. Five-Category Live End-to-End Generation Test
    # -------------------------------------------------------------------------
    print_header("3. FIVE-CATEGORY LIVE GENERATION TEST (MCP -> GEMINI -> VALIDATION)")
    
    category_map = {
        "Artificial Intelligence": 1,
        "Technology": 4,
        "Business": 5,
        "Education": 6,
        "Science": 8,
    }

    print(f"[*] Selected Article IDs across categories:")
    for cat in VALID_CATEGORIES:
        art_id = category_map.get(cat)
        print(f"    - {cat:<24} : Article ID {art_id}")
        assert art_id is not None, f"FAIL: Missing article for category '{cat}'"

    category_results = {}
    generated_records = {}

    for cat in VALID_CATEGORIES:
        art_id = category_map[cat]
        print(f"\n---> Testing Category: [{cat}] using Article ID {art_id}...")
        req = ArticleGenerationRequest(article_id=art_id)
        start_t = time.monotonic()
        resp: GenerationResponse = mcp_gen_service.generate_from_mcp_article(req, force_regenerate=True)
        dur = round((time.monotonic() - start_t) * 1000, 1)

        assert resp.success is True, f"FAIL: Generation failed for {cat}: {resp.error}"
        assert resp.data is not None, f"FAIL: No data returned for {cat}"
        gen: GeneratedNews = resp.data

        # Category check
        assert gen.category == cat, f"FAIL: Category mismatch: expected {cat}, got {gen.category}"
        assert len(gen.title) >= 5, "FAIL: Title too short"
        assert len(gen.summary) >= 20, "FAIL: Summary too short"
        assert len(gen.content) >= 100, "FAIL: Content too short"
        assert gen.source_url.startswith("http"), "FAIL: Invalid source URL"

        print(f"    [OK] Generation successful ({dur}ms, Model: {resp.model_used})")
        print(f"    Title:    {gen.title}")
        print(f"    Subtitle: {gen.subtitle}")
        print(f"    Category: {gen.category}")
        print(f"    Source:   {gen.source_name} ({gen.source_url})")
        print(f"    Summary:  {gen.summary[:120]}...")
        print(f"    Body len: {len(gen.content)} chars")

        category_results[cat] = "PASS"
        generated_records[cat] = gen

    print("\n" + "-" * 50)
    print("FIVE CATEGORY RESULTS:")
    for cat, status in category_results.items():
        print(f"  {cat:<24}: {status}")
    assert all(s == "PASS" for s in category_results.values())
    print("[PASS] All Five Categories Successfully Generated & Validated.\n")

    # -------------------------------------------------------------------------
    # 4. Anti-Hallucination & Source Grounding Verification
    # -------------------------------------------------------------------------
    print_header("4. ANTI-HALLUCINATION & SOURCE GROUNDING VERIFICATION")
    # Test with Science article
    sci_id = category_map["Science"]
    sci_raw = mcp_gen_service.fetch_article_via_mcp(sci_id)
    sci_gen = generated_records["Science"]

    print(f"[*] Raw Source Publisher: {sci_raw['source_name']}")
    print(f"[*] Raw Source URL:       {sci_raw['url']}")
    print(f"[*] Generated Source:     {sci_gen.source_name}")
    print(f"[*] Generated URL:        {sci_gen.source_url}")

    assert sci_gen.source_url.strip() == sci_raw["url"].strip(), "FAIL: Source URL was altered or hallucinated!"
    GenerationValidator.verify_grounding(sci_gen, sci_raw["content"])
    print("[PASS] Factual Source Grounding Verified: Zero fake sources or fabricated URLs.\n")

    # -------------------------------------------------------------------------
    # 5. Duplicate Generation Cache Verification
    # -------------------------------------------------------------------------
    print_header("5. DUPLICATE GENERATION CACHE VERIFICATION")
    first_id = eligible[0].id
    print(f"[*] Requesting Article ID {first_id} a second time without force_regenerate...")
    req_dup = ArticleGenerationRequest(article_id=first_id)
    cached_resp = mcp_gen_service.generate_from_mcp_article(req_dup, force_regenerate=False)
    assert cached_resp.generation_time_ms == 0.0, "FAIL: Duplicate call was not served from cache!"
    print(f"[PASS] Duplicate Protection Active: Served from in-memory cache in {cached_resp.generation_time_ms}ms.\n")

    # -------------------------------------------------------------------------
    # 6. Security & Credential Protection Checks
    # -------------------------------------------------------------------------
    print_header("6. SECURITY & CREDENTIAL HYGIENE CHECKS")
    # Verify .gitignore
    gitignore_path = backend_dir / ".gitignore"
    assert gitignore_path.exists(), "FAIL: .gitignore missing"
    gitignore_text = gitignore_path.read_text(encoding="utf-8")
    assert ".env" in gitignore_text, "FAIL: .env is not in .gitignore"
    print("[PASS] .env is properly gitignored.")

    # Verify .env.example has no secrets
    env_example_path = backend_dir / ".env.example"
    env_example_text = env_example_path.read_text(encoding="utf-8")
    assert "AIza" not in env_example_text, "FAIL: .env.example contains a real API key!"
    print("[PASS] .env.example contains only safe placeholders.")

    # Verify settings masking
    raw_key = settings.get_gemini_api_key()
    test_leak = f"Error: Failed with key={raw_key}"
    masked = settings.mask_secret(test_leak)
    assert raw_key not in masked, "FAIL: mask_secret did not redact raw key"
    assert "[REDACTED_API_KEY]" in masked, "FAIL: Redaction marker missing"
    print("[PASS] Secret masking and redaction verified.")

    print_header("STEP 7 MASTER VERIFICATION COMPLETE — ALL CRITERIA MET")


if __name__ == "__main__":
    main()
