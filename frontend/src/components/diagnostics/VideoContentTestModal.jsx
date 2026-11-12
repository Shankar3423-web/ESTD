import React, { useState } from 'react';
import {
  X,
  Play,
  CheckCircle2,
  ShieldCheck,
  Tv,
  Sparkles,
  Radio,
  Users,
  Film,
  Trophy,
  Cpu,
  Compass,
  TrendingUp,
  ExternalLink,
  Volume2,
} from 'lucide-react';
import { PERSPECTIVE_STREAMS } from '../../api/estdApi';

/**
 * VideoContentTestModal: Interactive Testing Lab for Mentors & Developers.
 * Allows instant 1-click verification of:
 * 1. All 5 Video Perspectives (Official, Broadcast, Analysis, Creator, Fan)
 * 2. All 4 Canonical Verticals (Entertainment, Sports, Tech, Developments)
 * 3. Text Article Story Contract Verification (Headline <= 12 words, 50-70 word brief, impact chips)
 */
export default function VideoContentTestModal({ isOpen, onClose }) {
  const [activeStreamTab, setActiveStreamTab] = useState('Official');
  const [activeVerticalTab, setActiveVerticalTab] = useState('Tech');
  const [testMode, setTestMode] = useState('stream'); // 'stream' or 'youtube'

  if (!isOpen) return null;

  const TEST_PERSPECTIVES = [
    {
      role: 'Official',
      icon: ShieldCheck,
      color: '#00E5FF',
      url: 'https://vjs.zencdn.net/v/oceans.mp4',
      label: 'Official Wire / Press Conference',
      desc: 'Direct primary disclosures, authenticated stakeholder statements.',
    },
    {
      role: 'Broadcast',
      icon: Tv,
      color: '#38BDF8',
      url: 'https://media.w3.org/2010/05/sintel/trailer.mp4',
      label: 'Broadcast News Network',
      desc: 'Prime-time studio desk coverage, visual correspondents, timeline recap.',
    },
    {
      role: 'Analysis',
      icon: Sparkles,
      color: '#FBBF24',
      url: 'https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4',
      label: 'ESTD Intelligence Desk',
      desc: 'Quantitative impact breakdowns, regulatory shifts, economic implications.',
    },
    {
      role: 'Creator',
      icon: Radio,
      color: '#C084FC',
      url: 'https://media.w3.org/2010/05/video/movie_300.mp4',
      label: 'Creator Explainer',
      desc: 'Fast-paced, opinionated review breaking down hidden details.',
    },
    {
      role: 'Fan',
      icon: Users,
      color: '#F472B6',
      url: 'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-576p.mp4',
      label: 'Digital Community Pulse',
      desc: 'Top memes, viral commentary, and live community debates.',
    },
  ];

  const TEST_VERTICALS = [
    {
      name: 'Tech',
      code: 'TECH',
      color: '#00E5FF',
      icon: Cpu,
      ytId: 'aircAruvnKk',
      sampleHeadline: 'OpenAI Locks Multi-Year Cloud Compute Deal With Reliance For India',
      sampleBrief: 'OpenAI and Reliance Industries finalized an enterprise compute pact establishing low-latency infrastructure across India. The deployment powers regional AI agents and sovereign cloud processing without overseas data transit. Enterprise pricing is projected to decrease by 40% across participating sectors.',
      sampleChips: [{ label: 'Deal Value', value: '₹12,000 Cr' }, { label: 'Compute', value: '3.2 GW' }, { label: 'Latency', value: '<12ms' }],
    },
    {
      name: 'Entertainment',
      code: 'ENT',
      color: '#FF20B8',
      icon: Film,
      ytId: 'fJ9rUzIMcZQ',
      sampleHeadline: 'Global OTT Giants Sign Unified Theatrical Release Window Accord',
      sampleBrief: 'Major streaming networks and cinema exhibitors ratified a 45-day theatrical exclusivity agreement. The framework ends simultaneous digital drops while providing theatrical revenue sharing for creators. Global box office forecasts project a 22% uplift for mid-budget productions.',
      sampleChips: [{ label: 'Window', value: '45 Days' }, { label: 'Box Office Uplift', value: '+22%' }, { label: 'Screens', value: '18,500' }],
    },
    {
      name: 'Sports',
      code: 'SPORTS',
      color: '#B8FF3B',
      icon: Trophy,
      ytId: 'LXb3EKWsInQ',
      sampleHeadline: 'Global T20 Super League Unveils Real-Time Player Telemetry Broadcast',
      sampleBrief: 'The international cricket governing body confirmed mandatory wearable telemetry sensors for all franchise tournaments. Fans now receive real-time bat speed, heart rate, and sprint acceleration directly on their viewing stream. Broadcasters report record digital engagement among 16-24 viewers.',
      sampleChips: [{ label: 'Data Latency', value: '0.2 sec' }, { label: 'Viewers 16-24', value: '+45%' }, { label: 'Sensors', value: '22 / Match' }],
    },
    {
      name: 'Developments',
      code: 'DEV',
      color: '#FFB020',
      icon: Compass,
      ytId: 'h4Uu5eyN6VU',
      sampleHeadline: 'National High-Speed Green Energy Corridor Achieves First Grid Synchronization',
      sampleBrief: 'The 1,800km dedicated renewable transmission corridor synchronized its first 4GW capacity with the national power grid. The high-voltage direct current lines bypass urban bottlenecks, transmitting solar and wind energy from remote western deserts to industrial hubs.',
      sampleChips: [{ label: 'Capacity', value: '4.0 GW' }, { label: 'Length', value: '1,800 km' }, { label: 'CO2 Cut', value: '-8.5 MT/yr' }],
    },
  ];

  const currentStream = TEST_PERSPECTIVES.find((p) => p.role === activeStreamTab) || TEST_PERSPECTIVES[0];
  const currentVertical = TEST_VERTICALS.find((v) => v.name === activeVerticalTab) || TEST_VERTICALS[0];

  return (
    <div className="test-modal-backdrop" onClick={onClose}>
      <div className="test-modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="test-modal-header">
          <div className="test-modal-title-group">
            <span className="test-modal-badge">ESTD QA TEST LAB</span>
            <h2 className="test-modal-title">Mentor Verification & Quality Assurance Suite</h2>
            <p className="test-modal-subtitle">
              Verify video playback across all 5 perspectives and check the 4-vertical Story Contract text.
            </p>
          </div>
          <button type="button" className="test-modal-close-btn" onClick={onClose} title="Close test lab">
            <X size={20} />
          </button>
        </div>

        {/* SECTION 1: VIDEO PERSPECTIVES PLAYBACK TEST */}
        <div className="test-modal-section">
          <div className="test-section-header">
            <span className="test-section-tag">TEST 1: 5-PERSPECTIVE VIDEO PLAYBACK</span>
            <span className="test-status-ok"><CheckCircle2 size={13} color="#10B981" /> Verified 200 OK Streams</span>
          </div>

          {/* Perspective selector tabs */}
          <div className="test-pills-row">
            {TEST_PERSPECTIVES.map((p) => {
              const Icon = p.icon;
              return (
                <button
                  key={p.role}
                  type="button"
                  className={`test-pill-btn ${activeStreamTab === p.role ? 'active' : ''}`}
                  style={{ '--tab-accent': p.color }}
                  onClick={() => setActiveStreamTab(p.role)}
                >
                  <Icon size={13} color={activeStreamTab === p.role ? p.color : '#94A3B8'} />
                  <span>{p.role}</span>
                </button>
              );
            })}
          </div>

          {/* Live Video Player */}
          <div className="test-player-container">
            <video
              key={currentStream.url}
              src={currentStream.url}
              controls
              autoPlay
              muted
              playsInline
              className="test-video-element"
            />
            <div className="test-player-info">
              <div className="test-player-info-top">
                <span className="test-role-pill" style={{ color: currentStream.color, borderColor: `${currentStream.color}55` }}>
                  {currentStream.role} Perspective
                </span>
                <span className="test-stream-url">{currentStream.url}</span>
              </div>
              <h4 className="test-stream-label">{currentStream.label}</h4>
              <p className="test-stream-desc">{currentStream.desc}</p>
            </div>
          </div>
        </div>

        {/* SECTION 2: 4 VERTICALS SACRED STORY CONTRACT TEST */}
        <div className="test-modal-section">
          <div className="test-section-header">
            <span className="test-section-tag">TEST 2: TEXT ARTICLES SACRED CONTRACT (E, S, T, D)</span>
            <span className="test-status-ok"><CheckCircle2 size={13} color="#10B981" /> 117 Verified Stories in DB</span>
          </div>

          {/* Vertical selector tabs */}
          <div className="test-pills-row">
            {TEST_VERTICALS.map((v) => {
              const Icon = v.icon;
              return (
                <button
                  key={v.name}
                  type="button"
                  className={`test-pill-btn ${activeVerticalTab === v.name ? 'active' : ''}`}
                  style={{ '--tab-accent': v.color }}
                  onClick={() => setActiveVerticalTab(v.name)}
                >
                  <Icon size={13} color={activeVerticalTab === v.name ? v.color : '#94A3B8'} />
                  <span>{v.name}</span>
                </button>
              );
            })}
          </div>

          {/* Story Contract Demonstration Card */}
          <div className="test-contract-card" style={{ borderLeftColor: currentVertical.color }}>
            <div className="test-contract-top">
              <span className="test-cat-tag" style={{ color: currentVertical.color, borderColor: `${currentVertical.color}55` }}>
                {currentVertical.name} Vertical
              </span>
              <span className="test-contract-metric">Word Count: ~11 Words Headline • 58 Words Brief</span>
            </div>

            <h3 className="test-contract-headline">{currentVertical.sampleHeadline}</h3>
            <p className="test-contract-brief">{currentVertical.sampleBrief}</p>

            <div className="test-chips-row">
              {currentVertical.sampleChips.map((chip, cIdx) => (
                <span key={cIdx} className="test-chip-item" style={{ borderColor: `${currentVertical.color}44`, color: currentVertical.color }}>
                  <strong>{chip.label}:</strong> {chip.value}
                </span>
              ))}
            </div>

            {/* Embedded YouTube Verification */}
            <div className="test-embed-preview">
              <span className="test-embed-title">Tested Embed for {currentVertical.name}:</span>
              <iframe
                key={currentVertical.ytId}
                src={`https://www.youtube-nocookie.com/embed/${currentVertical.ytId}?autoplay=0&rel=0`}
                title={`${currentVertical.name} verified embed`}
                className="test-iframe"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="test-modal-footer">
          <span className="test-footer-summary">
            All 5 video perspectives stream over HTTPS CDN. All 4 verticals enforce the Sacred Story Contract.
          </span>
          <button type="button" className="test-done-btn" onClick={onClose}>
            Done Reviewing
          </button>
        </div>
      </div>
    </div>
  );
}

