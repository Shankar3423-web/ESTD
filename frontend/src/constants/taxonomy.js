/**
 * Canonical ESTD Category and Subcategory Taxonomy.
 * Strict alignment with backend models and mentor's design specification.
 */

export const CATEGORIES = [
  {
    id: 1,
    name: 'Tech',
    code: 'TECH',
    slug: 'tech',
    color: '#00E5FF', // Cyan
    glow: 'rgba(0, 229, 255, 0.25)',
    description: 'Artificial intelligence, cloud infrastructure, consumer hardware, and developer ecosystems.',
    icon: 'Cpu',
  },
  {
    id: 2,
    name: 'Entertainment',
    code: 'ENT',
    slug: 'entertainment',
    color: '#FF20B8', // Magenta
    glow: 'rgba(255, 32, 184, 0.25)',
    description: 'Cinema, streaming, creator economy, music, digital storytelling, and pop culture.',
    icon: 'Film',
  },
  {
    id: 3,
    name: 'Business & Finance',
    code: 'BIZ_FIN',
    slug: 'business-finance',
    color: '#A855F7', // Violet
    glow: 'rgba(168, 85, 247, 0.25)',
    description: 'Financial markets, venture capital, macroeconomic policy, enterprise strategy, and supply chains.',
    icon: 'TrendingUp',
  },
  {
    id: 4,
    name: 'Developments',
    code: 'DEV',
    slug: 'developments',
    color: '#FFB020', // Amber
    glow: 'rgba(255, 176, 32, 0.25)',
    description: 'Public policy, scientific discoveries, health sciences, energy transitions, and geopolitics.',
    icon: 'Compass',
  },
  {
    id: 5,
    name: 'Sports',
    code: 'SPORTS',
    slug: 'sports',
    color: '#B8FF3B', // Lime
    glow: 'rgba(184, 255, 59, 0.25)',
    description: 'Cricket, football, motorsport, tennis, athletics, and tactical sports intelligence.',
    icon: 'Trophy',
  },
];

export const HOME_CATEGORY_CHIPS = [
  CATEGORIES.find((c) => c.code === 'ENT'),
  CATEGORIES.find((c) => c.code === 'SPORTS'),
  CATEGORIES.find((c) => c.code === 'TECH'),
  CATEGORIES.find((c) => c.code === 'DEV'),
  CATEGORIES.find((c) => c.code === 'BIZ_FIN'),
].filter(Boolean);

export const CATEGORY_MAP = Object.fromEntries(
  CATEGORIES.map((cat) => [cat.name, cat])
);

export const CATEGORY_SLUG_MAP = Object.fromEntries(
  CATEGORIES.map((cat) => [cat.slug, cat])
);

export const SUBCATEGORIES_BY_CATEGORY = {
  Entertainment: [
    'Movies & Cinema',
    'Music',
    'TV & OTT',
    'Creators & Influencers',
    'Celebrities & Pop Culture',
    'Gaming & Digital Entertainment',
    'Awards & Events',
    'Digital Storytelling & Culture',
  ],
  Sports: [
    'Cricket',
    'Football',
    'Tennis',
    'Badminton',
    'Motorsport',
    'Hockey',
    'Athletics & Olympic Sports',
    'Esports & Competitive Gaming',
    'Other Sports',
  ],
  Tech: [
    'Artificial Intelligence',
    'Software & Cloud',
    'Consumer Technology & Gadgets',
    'Cybersecurity & Privacy',
    'Developer Technologies & Open Source',
    'Emerging Tech & Semiconductors',
    'Digital Platforms & Big Tech',
  ],
  Developments: [
    'Government & Public Policy',
    'Infrastructure & Urban Planning',
    'Energy, Climate & Environment',
    'Health & Medical Sciences',
    'Education & Learning Policy',
    'Science & Research Discoveries',
    'Global Affairs & Geopolitics',
  ],
  'Business & Finance': [
    'Financial Markets & Banking',
    'Startups & Venture Capital',
    'Corporate Strategy & Earnings',
    'Personal Finance & Wealth Management',
    'Economy & Macroeconomics',
    'Trade, Supply Chain & Industry',
  ],
};

export function getCategoryMeta(categoryName) {
  if (!categoryName) return null;
  return (
    CATEGORY_MAP[categoryName] ||
    CATEGORY_SLUG_MAP[categoryName.toLowerCase()] || {
      name: categoryName,
      color: '#00E5FF',
      glow: 'rgba(0, 229, 255, 0.25)',
      description: '',
      icon: 'Tag',
    }
  );
}

export function slugify(text) {
  if (!text) return '';
  return text
    .toString()
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '-')
    .replace(/&/g, 'and')
    .replace(/[^\w\-]+/g, '')
    .replace(/\-\-+/g, '-');
}
