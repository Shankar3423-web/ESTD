import React, { useState, useEffect } from 'react';
import {
  X,
  Play,
  Pause,
  Volume2,
  VolumeX,
  Clock,
  Sparkles,
  Share2,
  Bookmark,
  Check,
  Maximize2,
  Film,
  ExternalLink,
} from 'lucide-react';

export const HUB_DIGEST_CONFIGS = {
  tech: {
    title: 'Tech Sector 180s Executive Intelligence Briefing',
    desk: 'ESTD Silicon & AI Intelligence Bureau',
    youtubeId: 'aircAruvnKk',
    cdnStream: 'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-576p.mp4',
    accent: '#00E5FF',
    badge: 'TECH // 180s EXECUTIVE BRIEFING',
    chapters: [
      { time: '00:00 - 00:45', label: 'AI Reasoning & Compute Scaling', desc: 'Frontier model architectures transitioning from speculative chat benchmarks into enterprise statutory compliance and physical science simulations.' },
      { time: '00:45 - 01:30', label: 'Advanced Packaging & Custom ASICs', desc: 'Silicon sovereignty shifts focus to 2.5D/3D packaging bottlenecks and sovereign datacenter power contracts.' },
      { time: '01:30 - 02:15', label: 'Antitrust Litigation & Mobile Platforms', desc: 'DOJ and EU enforcement challenging default search distribution contracts across Android and iOS.' },
      { time: '02:15 - 03:00', label: 'Strategic 2026-2027 Forward Horizon', desc: 'Agentic commerce models replacing traditional organic search indexing across leading operating systems.' },
    ],
    takeaways: [
      'Frontier model labs are prioritizing system-2 reasoning and compliance over pure parameter count.',
      'Datacenter power availability and custom chiplets dictate enterprise SaaS pricing models.',
      'Antitrust litigation is opening unprecedented distribution opportunities for independent AI engines.',
    ],
  },
  entertainment: {
    title: 'Entertainment & Creator Culture 180s Executive Briefing',
    desk: 'ESTD Cinema, OTT & Creator Intelligence Bureau',
    youtubeId: 'fJ9rUzIMcZQ',
    cdnStream: 'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-576p.mp4',
    accent: '#FF20B8',
    badge: 'ENTERTAINMENT // 180s EXECUTIVE BRIEFING',
    chapters: [
      { time: '00:00 - 00:45', label: 'Theatrical Spectacle Rebound', desc: 'IMAX and 70mm premium large-format screenings delivering record-breaking box office per-screen averages.' },
      { time: '00:45 - 01:30', label: 'Streaming Consolidation & Super-Bundles', desc: 'Platforms merging subscription tiers into hybrid ad-supported models to counter subscriber churn.' },
      { time: '01:30 - 02:15', label: 'Creator Studio Direct-to-Consumer Growth', desc: 'Independent creators bypassing legacy retail networks to launch direct consumer product empires.' },
      { time: '02:15 - 03:00', label: 'Gaming Engine Cross-Media Production', desc: 'Real-time virtual production sets converging gaming IP with prestige television series.' },
    ],
    takeaways: [
      'Audience demand is polarizing toward premium communal cinema and short-form creator video.',
      'Ad-supported streaming bundles have officially surpassed standalone premium tier growth.',
      'Virtual production powered by Unreal Engine 5 is permanently reducing post-production cycles.',
    ],
  },
  'business-finance': {
    title: 'Global Capital & Macro Markets 180s Executive Briefing',
    desk: 'ESTD Capital Markets & Fiscal Policy Bureau',
    youtubeId: '7Pq-S557XQU',
    cdnStream: 'https://vjs.zencdn.net/v/oceans.mp4',
    accent: '#A855F7',
    badge: 'BUSINESS & FINANCE // 180s EXECUTIVE BRIEFING',
    chapters: [
      { time: '00:00 - 00:45', label: 'Central Bank Rate Corridor Guidance', desc: 'Benchmark monetary guidance repricing capital across sovereign bond yield curves and syndicated debt.' },
      { time: '00:45 - 01:30', label: 'Venture Capital Pivot to Free Cash Flow', desc: 'Valuation multiples consolidating around recurring profitability over vanity top-line ARR expansion.' },
      { time: '01:30 - 02:15', label: 'Near-Shoring Industrial Supply Chains', desc: 'Critical supply line rerouting around maritime canal choke points toward regional manufacturing hubs.' },
      { time: '02:15 - 03:00', label: 'Corporate Margin Defense & Automation', desc: 'Enterprise deployment of automated workflow agents expanding operating margins amid flat revenue.' },
    ],
    takeaways: [
      'Higher-for-longer interest rate benchmarks create durable fixed-income asset class demand.',
      'Supply chain resilience has completely overtaken just-in-time inventory manufacturing philosophies.',
      'Enterprise automation adoption is preserving corporate operating margins across S&P 500 firms.',
    ],
  },
  developments: {
    title: 'Civil Infrastructure & Science 180s Executive Briefing',
    desk: 'ESTD Civil Engineering & Planetary Science Bureau',
    youtubeId: 'h4Uu5eyN6VU',
    cdnStream: 'https://vjs.zencdn.net/v/oceans.mp4',
    accent: '#10B981',
    badge: 'DEVELOPMENTS // 180s EXECUTIVE BRIEFING',
    chapters: [
      { time: '00:00 - 00:45', label: 'Clean Baseload Generation Surge', desc: 'Civilian nuclear restarts and geothermal power contracts to satisfy industrial compute load.' },
      { time: '00:45 - 01:30', label: 'High-Speed Transit Electrification', desc: 'Electrified intercity rail corridors stimulating private capital in surrounding urban transit hubs.' },
      { time: '01:30 - 02:15', label: 'AI Structural Biology Accelerators', desc: 'Automated molecular docking accelerating therapeutic compounds from computational labs into clinical trials.' },
      { time: '02:15 - 03:00', label: 'Multipolar Resource Treaties', desc: 'Bilateral technology-sharing accords guaranteeing synchronized critical mineral supply corridors.' },
    ],
    takeaways: [
      'Clean baseload power availability is the new primary bottleneck for global economic expansion.',
      'Transit electrification is reshaping regional density and commercial urban corridors.',
      'Computational biology is compressing clinical development timelines from years to months.',
    ],
  },
  sports: {
    title: 'Competitive Athletics & Tactics 180s Executive Briefing',
    desk: 'ESTD Sports Performance & Tactical Telemetry Bureau',
    youtubeId: 'LXb3EKWsInQ',
    cdnStream: 'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-576p.mp4',
    accent: '#22C55E',
    badge: 'SPORTS // 180s EXECUTIVE BRIEFING',
    chapters: [
      { time: '00:00 - 00:45', label: 'Bilateral Test Cricket Resilience', desc: 'National boards balancing 5-day championship prestige against domestic T20 franchise fixture congestion.' },
      { time: '00:45 - 01:30', label: 'European Football Pressing Schemes', desc: 'Inverted fullbacks and aggressive high-press schemes driving European domestic title races.' },
      { time: '01:30 - 02:15', label: 'Formula 1 Aerodynamic Telemetry', desc: 'Ground-effect aerodynamics dictating severe tire degradation and aggressive undercut pit windows.' },
      { time: '02:15 - 03:00', label: 'National Athletic Honors & Olympic Path', desc: 'Government athletic recognitions unlocking expanded sports science grants for elite training pipelines.' },
    ],
    takeaways: [
      'Real-time biometric telemetry has transformed in-match tactical decision-making across all sports.',
      'Spectator engagement is surging for high-stakes bilateral tests alongside novel hybrid spectacles.',
      'Sports science optimization is achieving unprecedented athletic recovery times between fixtures.',
    ],
  },
};

export default function HubDigestModalPlayer({
  isOpen,
  onClose,
  categorySlug = 'tech',
}) {
  if (!isOpen) return null;

  const normSlug = (categorySlug || 'tech').toLowerCase();
  const digest = HUB_DIGEST_CONFIGS[normSlug] || HUB_DIGEST_CONFIGS.tech;

  const [activeChapter, setActiveChapter] = useState(0);
  const [streamSource, setStreamSource] = useState('youtube'); // 'youtube' | 'cdn'
  const [copied, setCopied] = useState(false);
  const [isSaved, setIsSaved] = useState(false);

  // Close on Escape key
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handleShare = () => {
    navigator.clipboard?.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        background: 'rgba(5, 7, 13, 0.88)',
        backdropFilter: 'blur(12px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 16,
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: 960,
          background: '#0B0D14',
          border: `1.5px solid ${digest.accent}55`,
          borderRadius: 20,
          overflow: 'hidden',
          boxShadow: `0 24px 60px rgba(0, 0, 0, 0.8), 0 0 30px ${digest.accent}20`,
          position: 'relative',
          display: 'flex',
          flexDirection: 'column',
          maxHeight: '92vh',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Bar */}
        <div
          style={{
            padding: '16px 22px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'rgba(0, 0, 0, 0.4)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span
              style={{
                width: 9,
                height: 9,
                borderRadius: '50%',
                background: digest.accent,
                boxShadow: `0 0 10px ${digest.accent}`,
                display: 'inline-block',
              }}
            />
            <span
              style={{
                fontSize: 11,
                fontWeight: 800,
                letterSpacing: '0.1em',
                padding: '3px 10px',
                borderRadius: 4,
                background: `${digest.accent}20`,
                color: digest.accent,
                border: `1px solid ${digest.accent}55`,
              }}
            >
              {digest.badge}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {/* Stream Source Selector */}
            <div
              style={{
                display: 'flex',
                background: 'rgba(255, 255, 255, 0.06)',
                borderRadius: 6,
                padding: 2,
                border: '1px solid rgba(255, 255, 255, 0.1)',
              }}
            >
              <button
                onClick={() => setStreamSource('youtube')}
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  padding: '3px 9px',
                  borderRadius: 4,
                  border: 'none',
                  cursor: 'pointer',
                  background: streamSource === 'youtube' ? digest.accent : 'transparent',
                  color: streamSource === 'youtube' ? '#000000' : '#94a3b8',
                }}
              >
                1080p Stream
              </button>
              <button
                onClick={() => setStreamSource('cdn')}
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  padding: '3px 9px',
                  borderRadius: 4,
                  border: 'none',
                  cursor: 'pointer',
                  background: streamSource === 'cdn' ? digest.accent : 'transparent',
                  color: streamSource === 'cdn' ? '#000000' : '#94a3b8',
                }}
              >
                Direct HD MP4
              </button>
            </div>

            {/* Close Button */}
            <button
              onClick={onClose}
              style={{
                width: 32,
                height: 32,
                borderRadius: '50%',
                background: 'rgba(255, 255, 255, 0.08)',
                border: 'none',
                color: '#ffffff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                transition: 'background 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)')}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Video Player Screen (16:9 viewport) */}
        <div
          style={{
            position: 'relative',
            width: '100%',
            paddingTop: '52%',
            background: '#000000',
          }}
        >
          <div
            style={{
              position: 'absolute',
              inset: 0,
              width: '100%',
              height: '100%',
            }}
          >
            {streamSource === 'youtube' ? (
              <iframe
                src={`https://www.youtube-nocookie.com/embed/${digest.youtubeId}?autoplay=1&rel=0&modestbranding=1&controls=1`}
                title={digest.title}
                style={{
                  width: '100%',
                  height: '100%',
                  border: 'none',
                }}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            ) : (
              <video
                src={digest.cdnStream}
                controls
                autoPlay
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain',
                }}
              />
            )}
          </div>
        </div>

        {/* Video Metadata & Chapter Hub Body */}
        <div
          style={{
            padding: '20px 24px',
            overflowY: 'auto',
            flex: 1,
          }}
        >
          {/* Title & Desk Row */}
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: 11.5, color: digest.accent, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
                {digest.desk} • 3-Minute Continuous Executive Reel
              </div>
              <h2 style={{ fontSize: 20, fontWeight: 900, color: '#ffffff', margin: 0, letterSpacing: '-0.01em' }}>
                {digest.title}
              </h2>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <button
                onClick={() => setIsSaved(!isSaved)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '6px 12px',
                  borderRadius: 8,
                  fontSize: 12,
                  fontWeight: 700,
                  cursor: 'pointer',
                  background: isSaved ? `${digest.accent}20` : 'rgba(255, 255, 255, 0.06)',
                  color: isSaved ? digest.accent : '#94a3b8',
                  border: isSaved ? `1px solid ${digest.accent}55` : '1px solid rgba(255, 255, 255, 0.1)',
                }}
              >
                <Bookmark size={14} />
                <span>{isSaved ? 'Saved' : 'Save'}</span>
              </button>

              <button
                onClick={handleShare}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '6px 12px',
                  borderRadius: 8,
                  fontSize: 12,
                  fontWeight: 700,
                  cursor: 'pointer',
                  background: 'rgba(255, 255, 255, 0.06)',
                  color: '#94a3b8',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
              >
                {copied ? <Check size={14} style={{ color: '#4ADE80' }} /> : <Share2 size={14} />}
                <span>{copied ? 'Copied' : 'Share'}</span>
              </button>
            </div>
          </div>

          {/* Interactive 4-Chapter Briefing Timeline */}
          <div style={{ marginBottom: 18 }}>
            <div style={{ fontSize: 11, fontWeight: 800, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>
              Executive Briefing Chapters (180s Timeline)
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 8 }}>
              {digest.chapters.map((ch, idx) => {
                const isActive = activeChapter === idx;
                return (
                  <div
                    key={idx}
                    onClick={() => setActiveChapter(idx)}
                    style={{
                      padding: '10px 12px',
                      borderRadius: 10,
                      background: isActive ? `${digest.accent}15` : 'rgba(255, 255, 255, 0.03)',
                      border: isActive ? `1.5px solid ${digest.accent}` : '1px solid rgba(255, 255, 255, 0.06)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 10, fontWeight: 800, color: digest.accent }}>
                        CH 0{idx + 1}
                      </span>
                      <span style={{ fontSize: 10, color: '#64748b', fontWeight: 600 }}>
                        {ch.time}
                      </span>
                    </div>
                    <div style={{ fontSize: 12, fontWeight: 700, color: isActive ? '#ffffff' : '#cbd5e1' }}>
                      {ch.label}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Active Chapter Detail Card */}
            <div
              style={{
                marginTop: 10,
                padding: '12px 16px',
                borderRadius: 8,
                background: 'rgba(255, 255, 255, 0.02)',
                borderLeft: `3px solid ${digest.accent}`,
              }}
            >
              <span style={{ fontSize: 11, fontWeight: 800, color: digest.accent, textTransform: 'uppercase' }}>
                Active Segment Overview:
              </span>
              <p style={{ fontSize: 12.5, color: '#e2e8f0', margin: '4px 0 0 0', lineHeight: 1.5 }}>
                {digest.chapters[activeChapter].desc}
              </p>
            </div>
          </div>

          {/* Key Takeaways Section */}
          <div
            style={{
              padding: '14px 16px',
              borderRadius: 12,
              background: 'rgba(0, 0, 0, 0.4)',
              border: '1px solid rgba(255, 255, 255, 0.06)',
            }}
          >
            <div style={{ fontSize: 11, fontWeight: 800, color: digest.accent, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>
              Key Executive Takeaways (3-Minute Digest Summary)
            </div>
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12.5, color: '#cbd5e1', lineHeight: 1.6 }}>
              {digest.takeaways.map((t, idx) => (
                <li key={idx} style={{ marginBottom: 4 }}>
                  {t}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

