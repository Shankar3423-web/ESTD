/**
 * ESTD Relational Intelligence Engine: Cluster Relations & Cross-Story Synthesis.
 * Analyzes and maps "Why These Stories Connect" across all 37 subcategories.
 */

export const CLUSTER_RELATIONS_META = {
  // ==========================================
  // TECH INTELLIGENCE HUB
  // ==========================================
  'Artificial Intelligence': {
    unifyingThread:
      'The transition of frontier AI from speculative benchmarks into institutional compliance, physical climate modeling, and foundational cognitive boundary inquiries.',
    keyThemes: ['#EnterpriseAI', '#ClimateSimulation', '#CognitiveBoundaries', '#System2Reasoning'],
    focusArea: 'Foundational models, autonomous reasoning, enterprise adoption, and societal implications.',
    relationships: [
      {
        from: 'Commercial Market Solutions',
        to: 'Scientific Climate Modeling',
        connection: 'Enterprise capital filings reflect massive compute investments now driving physical science simulations.',
      },
      {
        from: 'Scientific Climate Modeling',
        to: 'Cognitive & Consciousness Inquiries',
        connection: 'As neural networks model complex planetary dynamics, theoretical discourse focuses on the distinction between statistical capability and sentience.',
      },
    ],
  },
  'Software & Cloud': {
    unifyingThread:
      'The decoupling of legacy monolithic architecture toward multi-cloud resilient microservices, autonomous DevOps pipelines, and sovereign data residency compliance.',
    keyThemes: ['#MultiCloud', '#DevOpsAutomation', '#DataSovereignty', '#Microservices'],
    focusArea: 'Cloud infrastructure, enterprise middleware, distributed systems, and software engineering velocity.',
    relationships: [
      {
        from: 'Infrastructure Scaling',
        to: 'Autonomous Orchestration',
        connection: 'Cloud cost optimization pressures are driving engineering teams to adopt AI-assisted distributed infrastructure managers.',
      },
    ],
  },
  'Consumer Technology & Gadgets': {
    unifyingThread:
      'Edge compute miniaturization reshaping wearable devices, spatial computing headsets, and next-generation silicon-efficient smartphones.',
    keyThemes: ['#EdgeAI', '#SpatialComputing', '#HardwareMiniaturization', '#SiliconEfficiency'],
    focusArea: 'Smartphones, wearables, smart home systems, display tech, and consumer silicon.',
    relationships: [
      {
        from: 'Wearable Biosensors',
        to: 'Spatial Interfaces',
        connection: 'Real-time physiological tracking is converging with augmented spatial computing to create context-aware personal assistants.',
      },
    ],
  },
  'Cybersecurity & Privacy': {
    unifyingThread:
      'The asymmetric arms race between automated vulnerability exploit generation and zero-trust cryptographic defense frameworks.',
    keyThemes: ['#ZeroTrust', '#PostQuantumCrypto', '#RansomwareDefense', '#NationStateSec'],
    focusArea: 'Threat intelligence, cryptographic integrity, critical infrastructure protection, and privacy regulation.',
    relationships: [
      {
        from: 'Vulnerability Detection',
        to: 'Zero-Trust Architecture',
        connection: 'Escalating firmware-level threats compel enterprises to mandate continuous cryptographic identity verification across all network endpoints.',
      },
    ],
  },
  'Developer Technologies & Open Source': {
    unifyingThread:
      'The rapid proliferation of open-weights models and AI code-generation agents altering software craftsmanship and open-source licensing governance.',
    keyThemes: ['#OpenWeights', '#AICodeGen', '#OpenSourceGovernance', '#CompilerOptimization'],
    focusArea: 'Compilers, programming frameworks, open-source maintainership, and developer tooling.',
    relationships: [
      {
        from: 'Open-Source Ecosystems',
        to: 'Automated Code Generation',
        connection: 'Community repository governance is restructuring around synthetic code contributions and automated pull-request validation pipelines.',
      },
    ],
  },
  'Emerging Tech & Semiconductors': {
    unifyingThread:
      'The geopolitical race for sub-2nm fabrication dominance, advanced 2.5D/3D packaging packaging bottlenecks, and photonic interconnect breakthroughs.',
    keyThemes: ['#SiliconSovereignty', '#AdvancedPackaging', '#EUVLithography', '#PhotonicCompute'],
    focusArea: 'Foundries, extreme ultraviolet lithography, custom ASICs, and quantum computing materials.',
    relationships: [
      {
        from: 'Foundry Capacity',
        to: 'Interconnect Bandwidth',
        connection: 'Physical limits of transistor scaling shift semiconductor innovation toward chiplet packaging and photonic communications.',
      },
    ],
  },
  'Digital Platforms & Big Tech': {
    unifyingThread:
      'Global antitrust enforcement confronting platform default monopolies, interoperability mandates, and the shift from algorithmic feeds to agentic commerce.',
    keyThemes: ['#AntitrustEnforcement', '#AppStoreMonopolies', '#PlatformGovernance', '#AgenticCommerce'],
    focusArea: 'Ecosystem lock-in, regulatory compliance, platform distribution deals, and monetization models.',
    relationships: [
      {
        from: 'Distribution Agreements',
        to: 'Market Interoperability',
        connection: 'Regulatory sanctions against exclusive revenue-sharing distribution deals catalyze new independent software marketplaces.',
      },
    ],
  },

  // ==========================================
  // ENTERTAINMENT INTELLIGENCE HUB
  // ==========================================
  'Movies & Cinema': {
    unifyingThread:
      'The theatrical rebound anchored by premium large format (IMAX/70mm) spectacle filmmaking contrasted against mid-budget distribution evolution.',
    keyThemes: ['#TheatricalRebound', '#PremiumLargeFormat', '#SpectacleCinema', '#BoxOfficeResilience'],
    focusArea: 'Theatrical distribution, box office telemetry, franchise development, and cinematic production craft.',
    relationships: [
      {
        from: 'Event Screenings',
        to: 'Box Office Momentum',
        connection: 'Audience demand for communal, high-fidelity theatrical experiences drives disproportionate revenue to premium screen formats.',
      },
    ],
  },
  'Music': {
    unifyingThread:
      'Streaming royalty model reform, catalog acquisition financialization, and the integration of generative spatial audio tools in modern recording.',
    keyThemes: ['#RoyaltyReform', '#CatalogSecuritization', '#SpatialAudio', '#IndependentDistribution'],
    focusArea: 'Recording industry economics, touring revenue, streaming payout mechanics, and audio innovation.',
    relationships: [
      {
        from: 'Streaming Revenue Models',
        to: 'Live Touring Economies',
        connection: 'Streaming margin compressions push artists toward high-yield global arena tours and immersive residency experiences.',
      },
    ],
  },
  'TV & OTT': {
    unifyingThread:
      'The consolidation of fragmented subscription tiers into ad-supported bundles and algorithmic viewer retention wars.',
    keyThemes: ['#StreamingConsolidation', '#FASTChannels', '#AdSupportedTiers', '#SubscriberChurn'],
    focusArea: 'Streaming networks, linear television transition, series commissioning, and viewer engagement metrics.',
    relationships: [
      {
        from: 'Ad-Supported Tiers',
        to: 'Franchise Retention',
        connection: 'Platforms utilize high-budget episodic prestige television as anchor points to minimize churn across hybrid advertising subscriptions.',
      },
    ],
  },
  'Creators & Influencers': {
    unifyingThread:
      'The professionalization of creator studios into vertically integrated consumer brands and diversified direct-to-consumer media empires.',
    keyThemes: ['#CreatorEconomy', '#D2CBrands', '#MultiPlatformDistribution', '#AlgorithmicSponsorship'],
    focusArea: 'Creator monetization, influencer talent agencies, algorithmic reach, and synthetic video production tools.',
    relationships: [
      {
        from: 'Audience Equity',
        to: 'Consumer Brand Expansion',
        connection: 'Top-tier creators leverage high-trust relationship loops with audiences to bypass legacy retail distribution entirely.',
      },
    ],
  },
  'Celebrities & Pop Culture': {
    unifyingThread:
      'The accelerated lifecycle of viral cultural moments amplified across global digital micro-communities and cultural diplomacy.',
    keyThemes: ['#FandomDynamics', '#CulturalDiplomacy', '#ViralNarratives', '#PublicRelations'],
    focusArea: 'Cultural touchpoints, premiere events, brand ambassadorships, and international entertainment diplomacy.',
    relationships: [
      {
        from: 'Digital Fandoms',
        to: 'Cultural Resonance',
        connection: 'Grassroots digital communities dictate global box-office and social discourse faster than centralized PR campaigns.',
      },
    ],
  },
  'Gaming & Digital Entertainment': {
    unifyingThread:
      'Cross-media IP convergence, cloud gaming infrastructure maturation, and the expansion of immersive interactive digital sandbox worlds.',
    keyThemes: ['#CrossMediaIP', '#CloudGaming', '#SandboxEconomies', '#UnrealEngine5'],
    focusArea: 'AAA game development, indie studio dynamics, esports broadcast technologies, and game engine advancements.',
    relationships: [
      {
        from: 'Game Engine Realism',
        to: 'Film/TV Virtual Production',
        connection: 'Real-time rendering tools developed for gaming now form the technical backbone of virtual film production sets.',
      },
    ],
  },
  'Awards & Events': {
    unifyingThread:
      'Global prestige ceremonies modernizing broadcast formats and voting metrics to reflect internationalized cinema and digital storytellers.',
    keyThemes: ['#AcademyRecognition', '#FestivalPremieres', '#PrestigeCircuit', '#AudienceEngagement'],
    focusArea: 'Film festivals, award academies, critical acclaim consensus, and ceremonial broadcast transformations.',
    relationships: [
      {
        from: 'Festival Laurels',
        to: 'Commercial Distribution',
        connection: 'Critical acclaim at international festivals acts as the primary de-risking catalyst for global indie distribution deals.',
      },
    ],
  },
  'Digital Storytelling & Culture': {
    unifyingThread:
      'Interactive non-linear narratives, immersive web documentaries, and generative media synthesis challenging traditional storytelling formats.',
    keyThemes: ['#InteractiveNarratives', '#SyntheticMedia', '#TransmediaCulture', '#DigitalPreservation'],
    focusArea: 'New media art, interactive documentaries, internet lore archives, and algorithmic narrative design.',
    relationships: [
      {
        from: 'Non-Linear Media',
        to: 'Audience Participation',
        connection: 'Dynamic participatory narrative models allow viewers to influence perspective, pacing, and visual story branches.',
      },
    ],
  },

  // ==========================================
  // BUSINESS & FINANCE INTELLIGENCE HUB
  // ==========================================
  'Financial Markets & Banking': {
    unifyingThread:
      'Central bank interest rate recalibration, sovereign bond liquidity stress, and systemic banking balance sheet resilience.',
    keyThemes: ['#MonetaryPolicy', '#BondYields', '#BankCapitalRatios', '#LiquidityManagement'],
    focusArea: 'Equities, debt capital markets, central bank policy, and commercial banking stability.',
    relationships: [
      {
        from: 'Interest Rate Decisions',
        to: 'Corporate Borrowing Spreads',
        connection: 'Benchmark monetary guidance directly reprices capital across commercial credit lines and syndicated debt markets.',
      },
    ],
  },
  'Startups & Venture Capital': {
    unifyingThread:
      'The pivot from hyper-growth subsidized customer acquisition to unit-economic profitability, capital efficiency, and strategic enterprise software consolidation.',
    keyThemes: ['#UnitEconomics', '#SeedToScale', '#VCDownRounds', '#SaaSProfitability'],
    focusArea: 'Venture funding cycles, founder governance, early-stage traction metrics, and secondary liquidity windows.',
    relationships: [
      {
        from: 'Capital Preservation',
        to: 'Valuation Realism',
        connection: 'Tighter venture term sheets compel founders to prioritize recurring free-cash-flow over vanity ARR multipliers.',
      },
    ],
  },
  'Corporate Strategy & Earnings': {
    unifyingThread:
      'Margin defense through operational AI automation, capital expenditure discipline, and strategic M&A portfolio rebalancing.',
    keyThemes: ['#OperatingMargins', '#CapExDiscipline', '#EarningsSurprises', '#MergersAndAcquisitions'],
    focusArea: 'Quarterly financial disclosures, executive management guidance, corporate governance, and cost structures.',
    relationships: [
      {
        from: 'Efficiency Initiatives',
        to: 'Guidance Upgrades',
        connection: 'Automated back-office deployments enable enterprise firms to expand operating margins even during flat top-line growth.',
      },
    ],
  },
  'Personal Finance & Wealth Management': {
    unifyingThread:
      'Retirement asset allocation shifts toward high-yield liquid instruments, tax-advantaged accounts, and wealth preservation against inflation.',
    keyThemes: ['#YieldMaximization', '#InflationHedges', '#IndexFundInflows', '#RetirementLongevity'],
    focusArea: 'Retail investing, fixed-income yields, portfolio diversification, and consumer credit trends.',
    relationships: [
      {
        from: 'Cash Yields',
        to: 'Equity Market Risk Appetite',
        connection: 'Higher risk-free benchmark yields create a durable alternative asset class for conservative retail wealth managers.',
      },
    ],
  },
  'Economy & Macroeconomics': {
    unifyingThread:
      'Global labor market persistence, supply-side disinflation, and sovereign deficit management across major developing and advanced economies.',
    keyThemes: ['#DisinflationTrends', '#LaborResilience', '#FiscalDeficits', '#GlobalTradeFlows'],
    focusArea: 'GDP projections, consumer price index readings, employment data, and international fiscal policy.',
    relationships: [
      {
        from: 'Labor Market Tightness',
        to: 'Consumer Spending Dynamics',
        connection: 'Wage gains offset inflation drags, maintaining core domestic services demand across leading economic zones.',
      },
    ],
  },
  'Trade, Supply Chain & Industry': {
    unifyingThread:
      'Friend-shoring and near-shoring industrial manufacturing, maritime shipping choke-point rerouting, and strategic mineral resource stockpiles.',
    keyThemes: ['#NearShoring', '#MaritimeLogistics', '#CriticalMinerals', '#IndustrialCapacity'],
    focusArea: 'Global logistics networks, container freight rates, manufacturing reshoring, and customs tariffs.',
    relationships: [
      {
        from: 'Shipping Choke-Points',
        to: 'Inventory Buffer Stocks',
        connection: 'Geopolitical canal delays force manufacturers to transition from just-in-time inventory to resilient localized buffer warehouses.',
      },
    ],
  },

  // ==========================================
  // DEVELOPMENTS INTELLIGENCE HUB
  // ==========================================
  'Government & Public Policy': {
    unifyingThread:
      'Legislative adaptation to artificial intelligence regulation, national security data restrictions, and federal fiscal modernization.',
    keyThemes: ['#LegislativeReform', '#NationalSecurity', '#RegulatoryFrameworks', '#CivicTech'],
    focusArea: 'Parliamentary bills, executive orders, statutory compliance, and civic administration efficiency.',
    relationships: [
      {
        from: 'Statutory Mandates',
        to: 'Public Agency Execution',
        connection: 'New regulatory standards compel rapid digital modernization and oversight mechanisms across federal oversight bodies.',
      },
    ],
  },
  'Infrastructure & Urban Planning': {
    unifyingThread:
      'High-speed transit electrification, resilient civil flood mitigation projects, and the expansion of fiber/telecom corridors in megacities.',
    keyThemes: ['#GridModernization', '#TransitElectrification', '#CivilResilience', '#UrbanMobility'],
    focusArea: 'Public works engineering, urban transit authorities, bridge and highway retrofits, and telecommunications conduits.',
    relationships: [
      {
        from: 'Transit Connectivity',
        to: 'Economic Density',
        connection: 'Electrified high-capacity rail hubs attract surrounding private capital, catalyzing modern high-density mixed-use districts.',
      },
    ],
  },
  'Energy, Climate & Environment': {
    unifyingThread:
      'The race between clean baseload deployment (nuclear/geothermal) and escalating electrical load demands from industrial datacenters and fabs.',
    keyThemes: ['#CleanBaseload', '#GridInterconnection', '#DatacenterEnergy', '#Decarbonization'],
    focusArea: 'Renewable energy generation, grid battery storage, emissions telemetry, and carbon capture infrastructure.',
    relationships: [
      {
        from: 'Industrial Power Surges',
        to: 'Zero-Carbon Power Contracts',
        connection: 'Hyperscalers sign long-term power purchase agreements directly with clean generation operators to guarantee 24/7 reliability.',
      },
    ],
  },
  'Health & Medical Sciences': {
    unifyingThread:
      'AI-accelerated structural biology discoveries, personalized mRNA therapies, and clinical trial timeline compressions.',
    keyThemes: ['#ComputationalBiology', '#PrecisionMedicine', '#mRNAPlatforms', '#ClinicalAccelerators'],
    focusArea: 'Drug discovery pipelines, genomics, epidemiological monitoring, and healthcare delivery automation.',
    relationships: [
      {
        from: 'Target Identification',
        to: 'Clinical Translation',
        connection: 'Automated molecular docking accelerates the transition of therapeutic compounds from computational labs into human trials.',
      },
    ],
  },
  'Education & Learning Policy': {
    unifyingThread:
      'Personalized adaptive learning tutors, STEM curriculum modernization, and institutional credentialing reform in the automation era.',
    keyThemes: ['#AdaptiveLearning', '#STEMInitiatives', '#CredentialingReform', '#DigitalPedagogy'],
    focusArea: 'Primary/higher education policy, vocational training, educational equity, and cognitive pedagogical research.',
    relationships: [
      {
        from: 'AI Pedagogical Tutors',
        to: 'Skill Mastery Verification',
        connection: 'Continuous formative assessments replace rigid standardized testing, tailoring feedback to individual learning speeds.',
      },
    ],
  },
  'Science & Research Discoveries': {
    unifyingThread:
      'Space-borne observation arrays, deep planetary core analysis, and quantum materials demonstrating exotic topological states.',
    keyThemes: ['#Astrophysics', '#QuantumMaterials', '#DeepEarthGeophysics', '#ScientificInstrumentation'],
    focusArea: 'Fundamental physics, astrophysics, materials science, and scientific laboratory instrumentation.',
    relationships: [
      {
        from: 'Novel Instrumentation',
        to: 'Empirical Breakthroughs',
        connection: 'Advanced cryogenic sensors enable the first empirical verification of long-standing theoretical particle behavior.',
      },
    ],
  },
  'Global Affairs & Geopolitics': {
    unifyingThread:
      'Multipolar diplomatic realignments, maritime sovereignty treaties, and trade corridor security alliances.',
    keyThemes: ['#MultipolarDiplomacy', '#MaritimeSecurity', '#SanctionsArchitecture', '#ResourceAlliances'],
    focusArea: 'Bilateral treaties, international security summits, border sovereignty, and diplomatic envoys.',
    relationships: [
      {
        from: 'Bilateral Accords',
        to: 'Cross-Border Economic Security',
        connection: 'Strategic security pacts increasingly mandate joint technology sharing and synchronized critical mineral export controls.',
      },
    ],
  },

  // ==========================================
  // SPORTS INTELLIGENCE HUB
  // ==========================================
  'Cricket': {
    unifyingThread:
      'High-stakes international bilateral test matches, multi-format player workload telemetry, and the worldwide expansion of domestic franchise leagues.',
    keyThemes: ['#ICCChampionships', '#WorkloadManagement', '#FranchiseProliferation', '#PitchTactics'],
    focusArea: 'Test cricket resilience, T20 franchise economics, player conditioning analytics, and tactical bowling variations.',
    relationships: [
      {
        from: 'Bilateral Test Grit',
        to: 'Franchise Calendar Pressure',
        connection: 'National boards balance the prestige of long-format test championships with the lucrative financial demands of franchise cricket.',
      },
    ],
  },
  'Football': {
    unifyingThread:
      'European domestic league title races, multi-club ownership financial sustainability regulations, and tactically fluid high-press tactical schemes.',
    keyThemes: ['#PremierLeagueTactics', '#FinancialFairPlay', '#MultiClubOwnership', '#InvertedFullbacks'],
    focusArea: 'League title races, UEFA continental competitions, transfer market finance, and tactical innovations.',
    relationships: [
      {
        from: 'Financial Fair Play Rules',
        to: 'Youth Academy Investment',
        connection: 'Stricter profit and sustainability spending limits incentivize elite clubs to prioritize home-grown academy talent pipelines.',
      },
    ],
  },
  'Tennis': {
    unifyingThread:
      'The competitive changing of the guard across the Grand Slam calendar, extreme baseline athletic recovery, and unified ATP/WTA governance talks.',
    keyThemes: ['#GrandSlamRace', '#BaselineAthleticism', '#TourMergerTalks', '#CourtBiomechanics'],
    focusArea: 'Major tournaments, ranking dynamics, biometric injury prevention, and tour revenue equity.',
    relationships: [
      {
        from: 'Endurance Baseline Play',
        to: 'Recovery Telemetry',
        connection: 'Physical demands of modern 5-set matches necessitate advanced physiological monitoring to maintain peak competitive stamina.',
      },
    ],
  },
  'Badminton': {
    unifyingThread:
      'Rapid net reflex dominance, BWF World Tour travel demands, and Asian powerhouse dominance challenged by emerging European singles contenders.',
    keyThemes: ['#BWFWorldTour', '#NetReflexes', '#SmashTelemetry', '#InternationalRivalries'],
    focusArea: 'World Tour Super 1000 events, shuttlecock speed aerodynamics, tactical deception, and doubles chemistry.',
    relationships: [
      {
        from: 'Smash Speed & Defense',
        to: 'Tactical Deception',
        connection: 'Defensive court coverage advancements force elite shuttlers to invent tighter net drops and deceptive wrist flick variations.',
      },
    ],
  },
  'Motorsport': {
    unifyingThread:
      'Aerodynamic ground-effect regulations, battery thermal management in hybrid powertrains, and high-speed telemetry pit-stop execution.',
    keyThemes: ['#GroundEffectAero', '#HybridPowertrains', '#TelemetryStrategy', '#PirelliTireDeg'],
    focusArea: 'Formula 1 technical directives, endurance hypercars, race strategy algorithms, and driver g-force stamina.',
    relationships: [
      {
        from: 'Aero Efficiency',
        to: 'Tire Degradation Window',
        connection: 'High-downforce aerodynamic setups degrade tire compounds faster, dictating aggressive undercut pit strategy calculations.',
      },
    ],
  },
  'Hockey': {
    unifyingThread:
      'FIH Pro League tactical pressing, high-drag penalty corner drag-flick mechanics, and synthetic turf turf surface advancements.',
    keyThemes: ['#FIHProLeague', '#PenaltyCornerFlicks', '#TurfSpeedDynamics', '#TacticalPressing'],
    focusArea: 'International field hockey championships, shootout execution, drag-flick biomechanics, and tactical counter-attacks.',
    relationships: [
      {
        from: 'Penalty Corner Conversions',
        to: 'Defensive Rusher Gear',
        connection: 'Extreme velocity drag-flicks prompt advanced ballistic protective equipment for defensive rushers on short corners.',
      },
    ],
  },
  'Athletics & Olympic Sports': {
    unifyingThread:
      'Track biomechanics, national award recognition for athletic excellence, and sports science optimization for Olympic quadrennials.',
    keyThemes: ['#NationalHonors', '#SprintBiomechanics', '#OlympicPreparations', '#HighPerformanceTraining'],
    focusArea: 'Track and field, gymnastics, swimming, national sporting federations, and high-performance training camps.',
    relationships: [
      {
        from: 'Elite National Accolades',
        to: 'Institutional Training Funding',
        connection: 'Government athletic award recognitions unlock expanded sports science grants and international coaching resources.',
      },
    ],
  },
  'Esports & Competitive Gaming': {
    unifyingThread:
      'Tier-1 international arena tournaments, franchise league financial restructuring, and millisecond tactical team coordination in multiplayer titles.',
    keyThemes: ['#WorldChampionships', '#FranchiseSustainability', '#TacticalMicro', '#BroadcastReach'],
    focusArea: 'MOBA/FPS global championships, team organizations, broadcast streaming production, and player career longevity.',
    relationships: [
      {
        from: 'Tournament Prize Pools',
        to: 'Organizational Sponsorships',
        connection: 'Shifting from speculative venture funding toward sustainable brand sponsorships and localized regional leagues.',
      },
    ],
  },
  'Other Sports': {
    unifyingThread:
      'Emerging hybrid disciplines, unconventional combat arts, and regional sporting cultures breaking into global televised circuits.',
    keyThemes: ['#HybridAthletics', '#GlobalPhenomena', '#GrassrootsCulture', '#AlternativeSpectacle'],
    focusArea: 'Chess boxing, extreme sports, regional folk wrestling, and novel spectator disciplines.',
    relationships: [
      {
        from: 'Niche Comic Origins',
        to: 'Televised Global Circuits',
        connection: 'Hybrid spectacles that fuse mental calculation with physical combat find viral international audiences through creator broadcasts.',
      },
    ],
  },
};

/**
 * Retrieves the comprehensive relational intelligence for any subcategory cluster.
 * Combines curated relational metadata with dynamic fallback if stories evolve.
 */
export function getClusterSynthesis(categoryName, subcategoryName, stories = []) {
  const meta = CLUSTER_RELATIONS_META[subcategoryName] || {
    unifyingThread: `Curated news intelligence tracking key developments across ${subcategoryName} in ${categoryName}.`,
    keyThemes: [`#${subcategoryName.replace(/[^A-Za-z0-9]/g, '')}`, `#${categoryName.replace(/[^A-Za-z0-9]/g, '')}`, '#VerifiedIntelligence'],
    focusArea: `Active dispatches and strategic analysis for ${subcategoryName}.`,
    relationships: [],
  };

  // If there are specific stories, generate contextual pairwise relationships
  let dynamicRelations = [...(meta.relationships || [])];

  if (stories.length >= 2 && dynamicRelations.length === 0) {
    for (let i = 0; i < stories.length - 1; i++) {
      const s1 = stories[i];
      const s2 = stories[i + 1];
      dynamicRelations.push({
        from: s1.sourceName || 'Primary Dispatch',
        to: s2.sourceName || 'Secondary Dispatch',
        connection: `Cross-reporting shows connected momentum between "${s1.headline.slice(0, 45)}..." and "${s2.headline.slice(0, 45)}...".`,
      });
    }
  }

  return {
    ...meta,
    relationships: dynamicRelations,
    storyCount: stories.length,
  };
}

