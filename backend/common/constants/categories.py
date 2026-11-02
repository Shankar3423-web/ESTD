"""ESTD Canonical Category and Subcategory Definitions."""
from enum import Enum
from typing import Dict, Final, List, Optional, Tuple


class ESTDCategory(str, Enum):
    """The 5 canonical ESTD parent categories."""
    ENTERTAINMENT = "Entertainment"
    SPORTS = "Sports"
    TECH = "Tech"
    DEVELOPMENTS = "Developments"
    BUSINESS_FINANCE = "Business & Finance"


VALID_CATEGORIES: Final[Tuple[str, ...]] = tuple(category.value for category in ESTDCategory)

# Stable canonical metadata for top-level categories
CATEGORY_METADATA: Final[Dict[str, Dict[str, str]]] = {
    ESTDCategory.ENTERTAINMENT.value: {
        "code": "ENT",
        "name": "Entertainment",
        "slug": "entertainment",
    },
    ESTDCategory.SPORTS.value: {
        "code": "SPORTS",
        "name": "Sports",
        "slug": "sports",
    },
    ESTDCategory.TECH.value: {
        "code": "TECH",
        "name": "Tech",
        "slug": "tech",
    },
    ESTDCategory.DEVELOPMENTS.value: {
        "code": "DEV",
        "name": "Developments",
        "slug": "developments",
    },
    ESTDCategory.BUSINESS_FINANCE.value: {
        "code": "BIZ_FIN",
        "name": "Business & Finance",
        "slug": "business-finance",
    },
}

CATEGORY_CODE_MAP: Final[Dict[str, str]] = {
    v["code"]: k for k, v in CATEGORY_METADATA.items()
}

CATEGORY_SLUG_MAP: Final[Dict[str, str]] = {
    v["slug"]: k for k, v in CATEGORY_METADATA.items()
}


class ESTDSubcategory(str, Enum):
    """Canonical ESTD subcategories across all parent categories."""
    # 1. Entertainment (8 approved subcategories)
    MOVIES_CINEMA = "Movies & Cinema"
    MUSIC = "Music"
    TV_OTT = "TV & OTT"
    CREATORS_INFLUENCERS = "Creators & Influencers"
    CELEBRITIES_POP_CULTURE = "Celebrities & Pop Culture"
    GAMING_DIGITAL_ENTERTAINMENT = "Gaming & Digital Entertainment"
    AWARDS_EVENTS = "Awards & Events"
    DIGITAL_STORYTELLING_CULTURE = "Digital Storytelling & Culture"

    # 2. Sports
    CRICKET = "Cricket"
    FOOTBALL = "Football"
    TENNIS = "Tennis"
    BADMINTON = "Badminton"
    MOTORSPORT = "Motorsport"
    HOCKEY = "Hockey"
    ATHLETICS_OLYMPICS = "Athletics & Olympic Sports"
    ESPORTS_COMPETITIVE = "Esports & Competitive Gaming"
    OTHER_SPORTS = "Other Sports"

    # 3. Tech
    ARTIFICIAL_INTELLIGENCE = "Artificial Intelligence"
    SOFTWARE_CLOUD = "Software & Cloud"
    CONSUMER_TECH_GADGETS = "Consumer Technology & Gadgets"
    CYBERSECURITY_PRIVACY = "Cybersecurity & Privacy"
    DEVELOPER_TECH = "Developer Technologies & Open Source"
    EMERGING_TECH_SEMICONDUCTORS = "Emerging Tech & Semiconductors"
    DIGITAL_PLATFORMS = "Digital Platforms & Big Tech"

    # 4. Developments
    GOVERNMENT_PUBLIC_POLICY = "Government & Public Policy"
    INFRASTRUCTURE_PLANNING = "Infrastructure & Urban Planning"
    ENERGY_ENVIRONMENT = "Energy, Climate & Environment"
    HEALTH_MEDICAL_SCIENCES = "Health & Medical Sciences"
    EDUCATION_LEARNING_POLICY = "Education & Learning Policy"
    SCIENCE_RESEARCH = "Science & Research Discoveries"
    GLOBAL_AFFAIRS = "Global Affairs & Geopolitics"

    # 5. Business & Finance
    FINANCIAL_MARKETS = "Financial Markets & Banking"
    STARTUPS_VENTURE_CAPITAL = "Startups & Venture Capital"
    CORPORATE_STRATEGY = "Corporate Strategy & Earnings"
    PERSONAL_FINANCE_WEALTH = "Personal Finance & Wealth Management"
    ECONOMY_MACROECONOMICS = "Economy & Macroeconomics"
    TRADE_SUPPLY_CHAIN = "Trade, Supply Chain & Industry"


# Subcategory metadata mapping: display name -> {code, slug, parent_category}
SUBCATEGORY_METADATA: Final[Dict[str, Dict[str, str]]] = {
    # Entertainment
    ESTDSubcategory.MOVIES_CINEMA.value: {
        "code": "ENT_MOVIES",
        "slug": "movies-cinema",
        "parent_category": ESTDCategory.ENTERTAINMENT.value,
    },
    ESTDSubcategory.MUSIC.value: {
        "code": "ENT_MUSIC",
        "slug": "music",
        "parent_category": ESTDCategory.ENTERTAINMENT.value,
    },
    ESTDSubcategory.TV_OTT.value: {
        "code": "ENT_TV_OTT",
        "slug": "tv-ott",
        "parent_category": ESTDCategory.ENTERTAINMENT.value,
    },
    ESTDSubcategory.CREATORS_INFLUENCERS.value: {
        "code": "ENT_CREATORS",
        "slug": "creators-influencers",
        "parent_category": ESTDCategory.ENTERTAINMENT.value,
    },
    ESTDSubcategory.CELEBRITIES_POP_CULTURE.value: {
        "code": "ENT_CELEBS",
        "slug": "celebrities-pop-culture",
        "parent_category": ESTDCategory.ENTERTAINMENT.value,
    },
    ESTDSubcategory.GAMING_DIGITAL_ENTERTAINMENT.value: {
        "code": "ENT_GAMING",
        "slug": "gaming-digital-entertainment",
        "parent_category": ESTDCategory.ENTERTAINMENT.value,
    },
    ESTDSubcategory.AWARDS_EVENTS.value: {
        "code": "ENT_AWARDS",
        "slug": "awards-events",
        "parent_category": ESTDCategory.ENTERTAINMENT.value,
    },
    ESTDSubcategory.DIGITAL_STORYTELLING_CULTURE.value: {
        "code": "ENT_DIGITAL_CULTURE",
        "slug": "digital-storytelling-culture",
        "parent_category": ESTDCategory.ENTERTAINMENT.value,
    },
    # Sports
    ESTDSubcategory.CRICKET.value: {
        "code": "SPORTS_CRICKET",
        "slug": "cricket",
        "parent_category": ESTDCategory.SPORTS.value,
    },
    ESTDSubcategory.FOOTBALL.value: {
        "code": "SPORTS_FOOTBALL",
        "slug": "football",
        "parent_category": ESTDCategory.SPORTS.value,
    },
    ESTDSubcategory.TENNIS.value: {
        "code": "SPORTS_TENNIS",
        "slug": "tennis",
        "parent_category": ESTDCategory.SPORTS.value,
    },
    ESTDSubcategory.BADMINTON.value: {
        "code": "SPORTS_BADMINTON",
        "slug": "badminton",
        "parent_category": ESTDCategory.SPORTS.value,
    },
    ESTDSubcategory.MOTORSPORT.value: {
        "code": "SPORTS_MOTORSPORT",
        "slug": "motorsport",
        "parent_category": ESTDCategory.SPORTS.value,
    },
    ESTDSubcategory.HOCKEY.value: {
        "code": "SPORTS_HOCKEY",
        "slug": "hockey",
        "parent_category": ESTDCategory.SPORTS.value,
    },
    ESTDSubcategory.ATHLETICS_OLYMPICS.value: {
        "code": "SPORTS_ATHLETICS",
        "slug": "athletics-olympics",
        "parent_category": ESTDCategory.SPORTS.value,
    },
    ESTDSubcategory.ESPORTS_COMPETITIVE.value: {
        "code": "SPORTS_ESPORTS",
        "slug": "esports-competitive-gaming",
        "parent_category": ESTDCategory.SPORTS.value,
    },
    ESTDSubcategory.OTHER_SPORTS.value: {
        "code": "SPORTS_OTHER",
        "slug": "other-sports",
        "parent_category": ESTDCategory.SPORTS.value,
    },
    # Tech
    ESTDSubcategory.ARTIFICIAL_INTELLIGENCE.value: {
        "code": "TECH_AI",
        "slug": "artificial-intelligence",
        "parent_category": ESTDCategory.TECH.value,
    },
    ESTDSubcategory.SOFTWARE_CLOUD.value: {
        "code": "TECH_SOFTWARE_CLOUD",
        "slug": "software-cloud",
        "parent_category": ESTDCategory.TECH.value,
    },
    ESTDSubcategory.CONSUMER_TECH_GADGETS.value: {
        "code": "TECH_CONSUMER_GADGETS",
        "slug": "consumer-technology-gadgets",
        "parent_category": ESTDCategory.TECH.value,
    },
    ESTDSubcategory.CYBERSECURITY_PRIVACY.value: {
        "code": "TECH_CYBERSECURITY",
        "slug": "cybersecurity-privacy",
        "parent_category": ESTDCategory.TECH.value,
    },
    ESTDSubcategory.DEVELOPER_TECH.value: {
        "code": "TECH_DEV_TOOLS",
        "slug": "developer-technologies",
        "parent_category": ESTDCategory.TECH.value,
    },
    ESTDSubcategory.EMERGING_TECH_SEMICONDUCTORS.value: {
        "code": "TECH_EMERGING_HARDWARE",
        "slug": "emerging-tech-semiconductors",
        "parent_category": ESTDCategory.TECH.value,
    },
    ESTDSubcategory.DIGITAL_PLATFORMS.value: {
        "code": "TECH_PLATFORMS",
        "slug": "digital-platforms",
        "parent_category": ESTDCategory.TECH.value,
    },
    # Developments
    ESTDSubcategory.GOVERNMENT_PUBLIC_POLICY.value: {
        "code": "DEV_GOV_POLICY",
        "slug": "government-public-policy",
        "parent_category": ESTDCategory.DEVELOPMENTS.value,
    },
    ESTDSubcategory.INFRASTRUCTURE_PLANNING.value: {
        "code": "DEV_INFRA",
        "slug": "infrastructure-planning",
        "parent_category": ESTDCategory.DEVELOPMENTS.value,
    },
    ESTDSubcategory.ENERGY_ENVIRONMENT.value: {
        "code": "DEV_ENERGY_CLIMATE",
        "slug": "energy-environment",
        "parent_category": ESTDCategory.DEVELOPMENTS.value,
    },
    ESTDSubcategory.HEALTH_MEDICAL_SCIENCES.value: {
        "code": "DEV_HEALTH_MED",
        "slug": "health-medical-sciences",
        "parent_category": ESTDCategory.DEVELOPMENTS.value,
    },
    ESTDSubcategory.EDUCATION_LEARNING_POLICY.value: {
        "code": "DEV_EDUCATION",
        "slug": "education-learning-policy",
        "parent_category": ESTDCategory.DEVELOPMENTS.value,
    },
    ESTDSubcategory.SCIENCE_RESEARCH.value: {
        "code": "DEV_SCIENCE_RESEARCH",
        "slug": "science-research",
        "parent_category": ESTDCategory.DEVELOPMENTS.value,
    },
    ESTDSubcategory.GLOBAL_AFFAIRS.value: {
        "code": "DEV_GLOBAL_AFFAIRS",
        "slug": "global-affairs",
        "parent_category": ESTDCategory.DEVELOPMENTS.value,
    },
    # Business & Finance
    ESTDSubcategory.FINANCIAL_MARKETS.value: {
        "code": "BIZ_MARKETS",
        "slug": "financial-markets-banking",
        "parent_category": ESTDCategory.BUSINESS_FINANCE.value,
    },
    ESTDSubcategory.STARTUPS_VENTURE_CAPITAL.value: {
        "code": "BIZ_STARTUPS",
        "slug": "startups-venture-capital",
        "parent_category": ESTDCategory.BUSINESS_FINANCE.value,
    },
    ESTDSubcategory.CORPORATE_STRATEGY.value: {
        "code": "BIZ_CORP_STRATEGY",
        "slug": "corporate-strategy-earnings",
        "parent_category": ESTDCategory.BUSINESS_FINANCE.value,
    },
    ESTDSubcategory.PERSONAL_FINANCE_WEALTH.value: {
        "code": "BIZ_PERSONAL_FINANCE",
        "slug": "personal-finance-wealth",
        "parent_category": ESTDCategory.BUSINESS_FINANCE.value,
    },
    ESTDSubcategory.ECONOMY_MACROECONOMICS.value: {
        "code": "BIZ_MACROECONOMY",
        "slug": "economy-macroeconomics",
        "parent_category": ESTDCategory.BUSINESS_FINANCE.value,
    },
    ESTDSubcategory.TRADE_SUPPLY_CHAIN.value: {
        "code": "BIZ_TRADE_INDUSTRY",
        "slug": "trade-industry",
        "parent_category": ESTDCategory.BUSINESS_FINANCE.value,
    },
}

# Parent to Subcategories mapping
CATEGORY_SUBCATEGORIES_MAP: Final[Dict[str, Tuple[str, ...]]] = {
    cat.value: tuple(
        sub_name
        for sub_name, meta in SUBCATEGORY_METADATA.items()
        if meta["parent_category"] == cat.value
    )
    for cat in ESTDCategory
}

# Legacy categories mapping to support backward compatibility and historical resolution
LEGACY_CATEGORY_MAP: Final[Dict[str, Tuple[str, Optional[str]]]] = {
    "Artificial Intelligence": (ESTDCategory.TECH.value, ESTDSubcategory.ARTIFICIAL_INTELLIGENCE.value),
    "Technology": (ESTDCategory.TECH.value, None),
    "Business": (ESTDCategory.BUSINESS_FINANCE.value, None),
    "Education": (ESTDCategory.DEVELOPMENTS.value, ESTDSubcategory.EDUCATION_LEARNING_POLICY.value),
    "Science": (ESTDCategory.DEVELOPMENTS.value, ESTDSubcategory.SCIENCE_RESEARCH.value),
}


def resolve_canonical_category(cat_str: str) -> Optional[str]:
    """Resolve category string (case-insensitive, code, slug, or legacy) to canonical name."""
    cleaned = cat_str.strip()
    # Direct match
    for valid_cat in VALID_CATEGORIES:
        if cleaned.lower() == valid_cat.lower():
            return valid_cat
    # Code match
    if cleaned.upper() in CATEGORY_CODE_MAP:
        return CATEGORY_CODE_MAP[cleaned.upper()]
    # Slug match
    if cleaned.lower() in CATEGORY_SLUG_MAP:
        return CATEGORY_SLUG_MAP[cleaned.lower()]
    # Legacy match
    for legacy_name, (canonical_name, _) in LEGACY_CATEGORY_MAP.items():
        if cleaned.lower() == legacy_name.lower():
            return canonical_name
    return None


def resolve_subcategory(
    subcategory_str: Optional[str], parent_category: Optional[str] = None
) -> Optional[str]:
    """Validate and resolve subcategory string belonging to the specified (or any) parent category."""
    if not subcategory_str:
        return None
    cleaned = subcategory_str.strip()
    if parent_category:
        valid_subs = CATEGORY_SUBCATEGORIES_MAP.get(parent_category, ())
        for sub in valid_subs:
            if cleaned.lower() == sub.lower():
                return sub
            meta = SUBCATEGORY_METADATA.get(sub, {})
            if cleaned.upper() == meta.get("code", "").upper():
                return sub
            if cleaned.lower() == meta.get("slug", "").lower():
                return sub
        return None

    # If parent_category not provided, search across all subcategories
    for sub, meta in SUBCATEGORY_METADATA.items():
        if cleaned.lower() == sub.lower():
            return sub
        if cleaned.upper() == meta.get("code", "").upper():
            return sub
        if cleaned.lower() == meta.get("slug", "").lower():
            return sub
    return None
