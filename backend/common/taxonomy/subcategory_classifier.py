"""Intelligent Subcategory Classification and Resolution Engine for ESTD.

Maps raw headlines, content, and metadata to canonical ESTD subcategories and IDs.
Ensures zero unclassified or orphaned articles across all 5 primary categories.
"""
import re
from typing import Dict, List, Optional, Tuple

# Mapping of subcategory names to their seeded PostgreSQL IDs
SUBCATEGORY_ID_MAP: Dict[str, Dict[str, int]] = {
    "Tech": {
        "Artificial Intelligence": 18,
        "Software & Cloud": 19,
        "Consumer Technology & Gadgets": 20,
        "Cybersecurity & Privacy": 21,
        "Developer Technologies & Open Source": 22,
        "Emerging Tech & Semiconductors": 23,
        "Digital Platforms & Big Tech": 24,
    },
    "Entertainment": {
        "Movies & Cinema": 1,
        "Music": 2,
        "TV & OTT": 3,
        "Creators & Influencers": 4,
        "Celebrities & Pop Culture": 5,
        "Gaming & Digital Entertainment": 6,
        "Awards & Events": 7,
        "Digital Storytelling & Culture": 8,
    },
    "Business & Finance": {
        "Financial Markets & Banking": 32,
        "Startups & Venture Capital": 33,
        "Corporate Strategy & Earnings": 34,
        "Personal Finance & Wealth Management": 35,
        "Economy & Macroeconomics": 36,
        "Trade, Supply Chain & Industry": 37,
    },
    "Developments": {
        "Government & Public Policy": 25,
        "Infrastructure & Urban Planning": 26,
        "Energy, Climate & Environment": 27,
        "Health & Medical Sciences": 28,
        "Education & Learning Policy": 29,
        "Science & Research Discoveries": 30,
        "Global Affairs & Geopolitics": 31,
    },
    "Sports": {
        "Cricket": 9,
        "Football": 10,
        "Tennis": 11,
        "Badminton": 12,
        "Motorsport": 13,
        "Hockey": 14,
        "Athletics & Olympic Sports": 15,
        "Esports & Competitive Gaming": 16,
        "Other Sports": 17,
    },
}

# Rich keyword signals for weighted deterministic matching
SUBCATEGORY_SIGNALS: Dict[str, Dict[str, List[str]]] = {
    "Tech": {
        "Artificial Intelligence": [
            "artificial intelligence", "ai model", "ai agent", "ai chip", "llm", "gpt",
            "openai", "anthropic", "claude", "gemini", "deepmind", "neural", "machine learning",
            "genai", "computer vision", "diffusion", "chatbot", "autonomous agent", "copilot",
            "hugging face", "transformer", "prompt engineering", "ai startup"
        ],
        "Software & Cloud": [
            "software", "cloud", "aws", "azure", "google cloud", "saas", "database", "storage",
            "kubernetes", "docker", "operating system", "windows update", "macos", "linux",
            "foot traffic software", "software-defined", "enterprise software", "firmware",
            "crm", "erp", "cloud infrastructure", "serverless", "it infrastructure"
        ],
        "Consumer Technology & Gadgets": [
            "smartphone", "phone", "iphone", "android", "pixel", "samsung galaxy", "oneplus",
            "gadget", "tablet", "ipad", "laptop", "macbook", "tv", "mini-led", "smart tv",
            "earbuds", "headphones", "smart home", "ring doorbell", "doorbell", "wearable",
            "smartwatch", "apple watch", "camera", "usb", "charger", "battery", "cast iron engine",
            "speaker", "display", "monitor", "audio"
        ],
        "Cybersecurity & Privacy": [
            "cyber", "security", "cyberattack", "hack", "hacker", "breach", "ransomware",
            "malware", "phishing", "privacy", "vulnerability", "zero-day", "sspm", "firewall",
            "encryption", "auth", "identity theft", "spyware", "ddos", "infosec", "threat actor"
        ],
        "Developer Technologies & Open Source": [
            "developer", "open source", "programming", "github", "coding", "python", "javascript",
            "typescript", "rust", "golang", "dev community", "api", "framework", "sdk", "compiler",
            "git", "pull request", "backend", "frontend", "devops", "codebase", "npm"
        ],
        "Emerging Tech & Semiconductors": [
            "semiconductor", "chip", "chipmaker", "processor", "cpu", "gpu", "nvidia", "amd",
            "intel", "tsmc", "qualcomm", "arm", "foundry", "wafer", "lithography", "quantum",
            "quantum computing", "superconductor", "nanometer", "3d laser", "profiler", "photonics"
        ],
        "Digital Platforms & Big Tech": [
            "meta quest", "vr", "virtual reality", "augmented reality", "ar headset", "vision pro",
            "social media", "twitter", "x.com", "elon musk", "grimes", "tiktok", "instagram",
            "youtube", "big tech", "antitrust", "app store", "digital platform", "marketplace"
        ],
    },
    "Entertainment": {
        "Movies & Cinema": [
            "movie", "cinema", "film", "box office", "theatrical", "director", "filmmaker",
            "hollywood", "bollywood", "tollywood", "actor", "actress", "trailer", "teaser",
            "screening", "hungergames", "avengers", "marvel", "dc", "paramount", "warner"
        ],
        "Music": [
            "music", "song", "album", "track", "singer", "concert", "tour", "billboard",
            "spotify", "grammy", "band", "rapper", "pop star", "orchestra", "dj", "festival"
        ],
        "TV & OTT": [
            "ott", "streaming", "netflix", "prime video", "hotstar", "jiohotstar", "hbo",
            "disney+", "series", "season", "episode", "show", "gilded age", "sitcom", "television"
        ],
        "Creators & Influencers": [
            "creator", "influencer", "youtuber", "streamer", "vlog", "twitch", "content creator",
            "mrbeast", "podcast host", "social star"
        ],
        "Celebrities & Pop Culture": [
            "celebrity", "celeb", "star", "marriage", "divorce", "relationship", "gossip",
            "red carpet", "met gala", "fashion", "lifestyle", "rumour"
        ],
        "Gaming & Digital Entertainment": [
            "game", "gaming", "playstation", "xbox", "nintendo", "steam", "epic games",
            "video game", "gamer", "rpg", "gta", "fortnite"
        ],
        "Awards & Events": [
            "award", "emmy", "oscar", "golden globe", "bafta", "cannes", "filmfare",
            "nomination", "jury", "film festival", "gala"
        ],
        "Digital Storytelling & Culture": [
            "storytelling", "comic", "anime", "manga", "animation", "graphic novel",
            "literature", "digital art", "culture", "heritage", "folk"
        ],
    },
    "Business & Finance": {
        "Financial Markets & Banking": [
            "stock", "market", "sensex", "nifty", "shares", "nasdaq", "dow", "wall street",
            "bull", "bear", "trading", "bank", "banking", "rbi", "federal reserve", "bond",
            "yield", "equity", "rupee", "dollar", "forex", "fpi", "fii"
        ],
        "Startups & Venture Capital": [
            "startup", "start-up", "vc", "venture capital", "funding", "seed round", "series a",
            "series b", "unicorn", "angel investor", "founder", "incubator", "accelerator"
        ],
        "Corporate Strategy & Earnings": [
            "earnings", "quarterly", "q1", "q2", "q3", "q4", "revenue", "profit", "loss",
            "ebitda", "merger", "acquisition", "buyout", "tata steel", "apollo tubes", "ceo",
            "board approved", "stake sale", "divestment", "subsidiary", "ipo"
        ],
        "Personal Finance & Wealth Management": [
            "tax", "income tax", "capital gains", "harvesting gains", "itr", "insurance",
            "motor cover", "policyholder", "savings", "pension", "retirement", "mutual fund",
            "gold purchase", "jewellery consumption", "gjc", "wealth"
        ],
        "Economy & Macroeconomics": [
            "economy", "gdp", "inflation", "cpi", "fiscal", "monetary", "interest rate",
            "trade deficit", "central bank", "economic progress", "macro", "unemployment",
            "growth rate", "austerity", "recession"
        ],
        "Trade, Supply Chain & Industry": [
            "trade", "export", "import", "supply chain", "logistics", "trade pact", "fta",
            "manufacturing", "factory", "steel", "automotive", "car sales", "fada",
            "ev sales", "retail", "freight", "port", "cargo", "tyre production"
        ],
    },
    "Developments": {
        "Government & Public Policy": [
            "government", "govt", "policy", "cabinet", "parliament", "bill", "ordinance",
            "supreme court", "high court", "ration card", "welfare", "order", "modi",
            "election", "bjp", "congress", "minister", "administration"
        ],
        "Infrastructure & Urban Planning": [
            "infrastructure", "highway", "expressway", "metro", "railway", "rail", "airport",
            "choice lanes", "bridge", "transit", "urban", "smart city", "housing", "construction",
            "coach services", "tdot"
        ],
        "Energy, Climate & Environment": [
            "climate", "environment", "renewable", "solar", "wind energy", "green energy",
            "carbon", "pollution", "emission", "earthshot prize", "mobility", "forest",
            "wildlife", "electricity bill", "tnb", "weather", "cyclone"
        ],
        "Health & Medical Sciences": [
            "health", "medical", "hospital", "doctor", "disease", "vaccine", "drug", "fda",
            "clinical", "cancer", "pharma", "rna", "olezarsen", "antisense", "radiology",
            "blood pressure", "who"
        ],
        "Education & Learning Policy": [
            "education", "school", "schools", "ips", "college", "university", "student",
            "students", "exam", "neet", "jee", "cbse", "ugc", "teacher", "curriculum",
            "reading scores", "campus", "academic"
        ],
        "Science & Research Discoveries": [
            "science", "research", "satellite", "isro", "nasa", "space", "astronomy", "physics",
            "chemistry", "biology", "genetics", "telescope", "discovery", "laboratory",
            "scientific", "brain-like models"
        ],
        "Global Affairs & Geopolitics": [
            "geopolitics", "diplomacy", "international", "foreign policy", "bilateral",
            "summit", "treaty", "united nations", "war", "conflict", "ambassador", "embassy",
            "zambian", "eff", "peace pact"
        ],
    },
    "Sports": {
        "Cricket": [
            "cricket", "bcci", "ipl", "test match", "odi", "t20", "century", "wicket",
            "bowler", "batsman", "runs", "icc", "rohit", "virat", "bumrah"
        ],
        "Football": [
            "football", "soccer", "fifa", "premier league", "champions league", "messi",
            "ronaldo", "goal", "striker", "penalty", "la liga", "manchester", "real madrid"
        ],
        "Tennis": [
            "tennis", "grand slam", "wimbledon", "us open", "roland garros", "australian open",
            "atp", "wta", "djokovic", "alcaraz", "sinner"
        ],
        "Badminton": [
            "badminton", "shuttler", "bwf", "smash", "pv sindhu", "lakshya sen"
        ],
        "Motorsport": [
            "f1", "formula 1", "grand prix", "racing", "ferrari", "red bull", "mercedes",
            "verstappen", "hamilton", "motogp"
        ],
        "Hockey": [
            "hockey", "fih", "drag flick", "penalty corner", "world cup hockey"
        ],
        "Athletics & Olympic Sports": [
            "athletics", "olympics", "olympic", "javelin", "marathon", "sprint", "gold medal",
            "neeraj chopra", "track and field"
        ],
        "Esports & Competitive Gaming": [
            "esports", "competitive gaming", "valorant", "cs:go", "counter-strike",
            "bgmi", "dota", "league of legends"
        ],
        "Other Sports": [
            "nfl", "seahawks", "49ers", "american football", "quarterback", "super bowl",
            "nba", "basketball", "baseball", "golf", "boxing", "wrestling", "kabaddi", "chess"
        ],
    },
}

DEFAULT_SUBCATEGORY: Dict[str, str] = {
    "Tech": "Software & Cloud",
    "Entertainment": "Movies & Cinema",
    "Business & Finance": "Economy & Macroeconomics",
    "Developments": "Government & Public Policy",
    "Sports": "Cricket",
}


def classify_article_subcategory(
    category: str,
    title: str = "",
    content: str = "",
    current_sub: Optional[str] = None,
) -> Tuple[str, int]:
    """Deterministically classifies an article into its canonical ESTD subcategory and ID.

    Args:
        category: Primary ESTD category (Tech, Entertainment, Business & Finance, Developments, Sports).
        title: Headline of the article.
        content: Body text, summary, or description.
        current_sub: Existing subcategory string if present.

    Returns:
        Tuple of (canonical_subcategory_name, canonical_subcategory_id).
    """
    valid_subs = SUBCATEGORY_ID_MAP.get(category, {})
    if not valid_subs:
        # Fallback to Tech if unknown
        valid_subs = SUBCATEGORY_ID_MAP["Tech"]
        category = "Tech"

    # 1. If already valid canonical subcategory, return directly
    if current_sub and current_sub.strip():
        norm_curr = current_sub.strip()
        for canonical_name, sub_id in valid_subs.items():
            if norm_curr.lower() == canonical_name.lower():
                return canonical_name, sub_id

    # 2. Textual pattern and keyword signal scoring
    full_text = f"{title} {title} {content}".lower()  # Weight title 2x

    best_match = None
    best_score = 0

    category_signals = SUBCATEGORY_SIGNALS.get(category, {})
    for sub_name, keywords in category_signals.items():
        score = 0
        for kw in keywords:
            # Word boundary regex search to prevent partial false positives
            pattern = r"\b" + re.escape(kw) + r"\b"
            matches = len(re.findall(pattern, full_text))
            if matches > 0:
                # Multi-word phrases give higher confidence
                weight = 3 if " " in kw else 1
                score += matches * weight

        if score > best_score:
            best_score = score
            best_match = sub_name

    # 3. If confident match found, return it
    if best_match and best_score >= 1:
        return best_match, valid_subs[best_match]

    # 4. Fallback to sensible category default
    fallback = DEFAULT_SUBCATEGORY.get(category, list(valid_subs.keys())[0])
    return fallback, valid_subs[fallback]
