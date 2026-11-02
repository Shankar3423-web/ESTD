import React, { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Calendar,
  Sparkles,
  Bell,
  Clock,
  ArrowRight,
  Cpu,
  Film,
  Trophy,
  GraduationCap,
  TrendingUp,
  Compass,
  Check,
  CalendarPlus,
  ExternalLink,
  Download,
  X,
  Radio,
  Zap,
} from 'lucide-react';
import { getCategoryMeta } from '../../constants/taxonomy';

const RADAR_ITEMS = [
  {
    id: 'radar-1',
    date: 'Oct 28',
    dayName: 'Wednesday',
    relativeTime: 'In 2 Days',
    statusUrgency: 'urgent',
    category: 'Tech',
    tag: 'Product Launch',
    title: 'OpenAI & Anthropic Next-Gen Voice & Reasoning Model Deployments',
    description:
      'Global rollout of advanced voice agent APIs and developer access for ultra-low latency multimodal assistants.',
    accentColor: '#00E5FF',
    icon: Cpu,
    targetDate: '20261028T140000Z',
    endDate: '20261028T160000Z',
    isLiveNow: true, // Used for live alert demo
  },
  {
    id: 'radar-2',
    date: 'Oct 30',
    dayName: 'Friday',
    relativeTime: 'This Friday',
    statusUrgency: 'soon',
    category: 'Entertainment',
    tag: 'Streaming & Box Office',
    title: 'Weekend Global OTT Drops & Major Theatrical Film Premieres',
    description:
      'Prime Video and Netflix slate drops alongside nationwide cinematic debuts with creator watch-parties.',
    accentColor: '#FF20B8',
    icon: Film,
    targetDate: '20261030T180000Z',
    endDate: '20261030T210000Z',
  },
  {
    id: 'radar-3',
    date: 'Nov 01',
    dayName: 'Sunday',
    relativeTime: 'This Weekend',
    statusUrgency: 'soon',
    category: 'Sports',
    tag: 'Live Fixture',
    title: 'Championship Football Derbies & T20 Super League Clashes',
    description:
      'High-stakes weekend matches broadcasting live across global streaming networks with real-time fan telemetry.',
    accentColor: '#10B981',
    icon: Trophy,
    targetDate: '20261101T150000Z',
    endDate: '20261101T180000Z',
  },
  {
    id: 'radar-4',
    date: 'Nov 03',
    dayName: 'Tuesday',
    relativeTime: 'Next Week',
    statusUrgency: 'normal',
    category: 'Education',
    tag: 'Policy & Admissions',
    title: 'National Fellowship & Central University Winter Admission Portal',
    description:
      'Official application opening for postgraduate fellowships, research grants, and NEP-aligned degree tracks.',
    accentColor: '#38BDF8',
    icon: GraduationCap,
    targetDate: '20261103T090000Z',
    endDate: '20261103T180000Z',
  },
  {
    id: 'radar-5',
    date: 'Nov 04',
    dayName: 'Wednesday',
    relativeTime: 'Next Week',
    statusUrgency: 'normal',
    category: 'Business & Finance',
    tag: 'Earnings Catalyst',
    title: 'Big Tech Q3 Earnings & Global Central Bank Benchmark Updates',
    description:
      'Key quarterly financial disclosures and interest rate trajectory statements impacting tech hiring and venture funding.',
    accentColor: '#FFB020',
    icon: TrendingUp,
    targetDate: '20261104T200000Z',
    endDate: '20261104T220000Z',
  },
  {
    id: 'radar-6',
    date: 'Nov 06',
    dayName: 'Friday',
    relativeTime: 'Upcoming',
    statusUrgency: 'normal',
    category: 'Developments',
    tag: 'Science Milestone',
    title: 'Clean Energy Transition & Space Exploration Briefing',
    description:
      'International telemetry disclosures on next-gen solar efficiency standards and upcoming lunar payload readiness.',
    accentColor: '#A855F7',
    icon: Compass,
    targetDate: '20261106T130000Z',
    endDate: '20261106T150000Z',
  },
];

const FILTER_TABS = [
  { id: 'All', label: 'All Drops' },
  { id: 'Tech', label: 'Tech & AI' },
  { id: 'Entertainment', label: 'Entertainment' },
  { id: 'Sports', label: 'Sports' },
  { id: 'Education', label: 'Education & Policy' },
  { id: 'Business & Finance', label: 'Markets' },
];

/**
 * Generate a Google Calendar 1-Click Link
 */
function createGoogleCalendarUrl(item) {
  const text = encodeURIComponent(`[ESTD Radar] ${item.title}`);
  const details = encodeURIComponent(
    `${item.description}\n\nTracked live on ESTD News Platform.\nCategory: ${item.category} • ${item.tag}`
  );
  const location = encodeURIComponent('ESTD News Live Wire (https://estd.news)');
  const dates = `${item.targetDate || '20261028T140000Z'}/${item.endDate || '20261028T160000Z'}`;
  return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${text}&details=${details}&location=${location}&dates=${dates}`;
}

/**
 * Download a standard .ICS Calendar File for Apple Calendar / Outlook / Mobile
 */
function downloadIcsCalendar(item) {
  const startDate = item.targetDate || '20261028T140000Z';
  const endDate = item.endDate || '20261028T160000Z';
  const now = new Date().toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';

  const icsBody = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//ESTD News Platform//Radar Forward Intel//EN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'BEGIN:VEVENT',
    `UID:${item.id}@estd.news`,
    `DTSTAMP:${now}`,
    `DTSTART:${startDate}`,
    `DTEND:${endDate}`,
    `SUMMARY:[ESTD Radar] ${item.title}`,
    `DESCRIPTION:${item.description}`,
    'LOCATION:ESTD News Live Wire',
    'STATUS:CONFIRMED',
    'BEGIN:VALARM',
    'TRIGGER:-PT15M',
    'ACTION:DISPLAY',
    'DESCRIPTION:Reminder: ESTD Radar Event Launching',
    'END:VALARM',
    'END:VEVENT',
    'END:VCALENDAR',
  ].join('\r\n');

  const blob = new Blob([icsBody], { type: 'text/calendar;charset=utf-8' });
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `${item.id}-calendar-reminder.ics`;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.URL.revokeObjectURL(url);
}

export default function WeeklyRadarDrop() {
  const navigate = useNavigate();
  const [selectedFilter, setSelectedFilter] = useState('All');

  // Reminders tracked in localStorage
  const [reminders, setReminders] = useState(() => {
    try {
      const saved = localStorage.getItem('estd_radar_reminders');
      return new Set(saved ? JSON.parse(saved) : ['radar-1']); // Default demo has radar-1 armed
    } catch {
      return new Set(['radar-1']);
    }
  });

  // Calendar dropdown active menu
  const [calendarMenuOpenId, setCalendarMenuOpenId] = useState(null);

  // Live Launched Reminder Popup State
  const [activeAlertPopup, setActiveAlertPopup] = useState(null);

  // Check if any armed reminder should popup on load
  useEffect(() => {
    // If radar-1 is reminded, trigger the live reminder notification toast
    if (reminders.has('radar-1')) {
      const timer = setTimeout(() => {
        const item = RADAR_ITEMS.find((r) => r.id === 'radar-1');
        if (item) setActiveAlertPopup(item);
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, []);

  const toggleReminder = async (item) => {
    const id = item.id;
    const isCurrentlyReminded = reminders.has(id);

    setReminders((prev) => {
      const next = new Set(prev);
      if (isCurrentlyReminded) {
        next.delete(id);
      } else {
        next.add(id);
      }
      try {
        localStorage.setItem('estd_radar_reminders', JSON.stringify([...next]));
      } catch {}
      return next;
    });

    if (!isCurrentlyReminded) {
      // 1. Request Native Browser Notification permission if supported
      if ('Notification' in window) {
        try {
          if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
            const perm = await Notification.requestPermission();
            if (perm === 'granted') {
              new Notification('🔔 ESTD Radar Reminder Set!', {
                body: `We will alert you when "${item.title}" officially launches.`,
                icon: '/favicon.ico',
              });
            }
          }
        } catch (e) {
          console.debug('Notification permission notice:', e);
        }
      }

      // 2. Trigger on-screen launch alert toast for demonstration
      setActiveAlertPopup(item);
    }
  };

  const filteredItems = useMemo(() => {
    if (selectedFilter === 'All') return RADAR_ITEMS;
    return RADAR_ITEMS.filter((item) => {
      if (selectedFilter === 'Education') {
        return item.category === 'Education' || item.category === 'Developments';
      }
      return item.category === selectedFilter;
    });
  }, [selectedFilter]);

  return (
    <section className="weekly-radar-section" aria-label="What is Dropping This Week" style={{ position: 'relative' }}>
      {/* ============================================================== */}
      {/* LIVE REMINDER ALERT TOAST POPUP                                */}
      {/* Pops up and alerts the user when their drop occurs / launches   */}
      {/* ============================================================== */}
      {activeAlertPopup && (
        <div
          className="radar-live-alert-toast"
          style={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            zIndex: 99999,
            background: 'linear-gradient(135deg, #0e121e 0%, #080a11 100%)',
            border: `2px solid ${activeAlertPopup.accentColor || '#00E5FF'}`,
            boxShadow: `0 16px 48px rgba(0, 0, 0, 0.85), 0 0 32px ${activeAlertPopup.accentColor || '#00E5FF'}55`,
            borderRadius: 18,
            padding: '20px 22px',
            maxWidth: 440,
            animation: 'radarSlideUp 0.35s ease-out',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, marginBottom: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {/* Blinking Radar Beacon */}
              <span
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  background: activeAlertPopup.accentColor || '#00E5FF',
                  boxShadow: `0 0 12px ${activeAlertPopup.accentColor || '#00E5FF'}`,
                  display: 'inline-block',
                  animation: 'radarPulseBeacon 1.2s infinite',
                }}
              />
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 900,
                  color: activeAlertPopup.accentColor || '#00E5FF',
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                }}
              >
                🔔 REMINDER ALERT // EVENT LAUNCHED!
              </span>
            </div>

            <button
              type="button"
              onClick={() => setActiveAlertPopup(null)}
              style={{
                background: 'none',
                border: 'none',
                color: '#94a3b8',
                cursor: 'pointer',
                padding: 0,
                display: 'flex',
                alignItems: 'center',
              }}
              title="Dismiss Alert"
            >
              <X size={16} />
            </button>
          </div>

          <h4
            style={{
              fontSize: 15,
              fontWeight: 800,
              color: '#ffffff',
              lineHeight: 1.4,
              margin: '0 0 6px 0',
            }}
          >
            {activeAlertPopup.title}
          </h4>

          <p style={{ fontSize: 12.5, color: '#cbd5e1', lineHeight: 1.5, margin: '0 0 14px 0' }}>
            This event was scheduled for today and has officially dropped! You set a reminder for this drop on ESTD.
          </p>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <button
              type="button"
              onClick={() => {
                const targetItem = activeAlertPopup;
                setActiveAlertPopup(null);
                const query = encodeURIComponent(targetItem.title);
                const category = encodeURIComponent(targetItem.category);
                navigate(`/search?q=${query}&category=${category}&from=radar`);
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '8px 16px',
                borderRadius: 9,
                background: activeAlertPopup.accentColor || '#00E5FF',
                color: '#000000',
                fontSize: 12.5,
                fontWeight: 800,
                border: 'none',
                cursor: 'pointer',
                boxShadow: `0 0 16px ${activeAlertPopup.accentColor || '#00E5FF'}80`,
                transition: 'all 0.15s ease',
              }}
            >
              <Sparkles size={14} />
              <span>Open Live Gemini Briefing</span>
              <ArrowRight size={13} />
            </button>

            <button
              type="button"
              onClick={() => setActiveAlertPopup(null)}
              style={{
                padding: '7px 12px',
                borderRadius: 8,
                background: 'rgba(255, 255, 255, 0.06)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                color: '#cbd5e1',
                fontSize: 12,
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* SECTION HEADER                                                 */}
      {/* ============================================================== */}
      <div className="weekly-radar-header">
        <div className="weekly-radar-title-group">
          <div className="weekly-radar-icon-badge">
            <Calendar size={18} />
          </div>
          <div className="weekly-radar-titles">
            <div className="weekly-radar-heading-row">
              <h2 className="weekly-radar-heading">The Radar: What's Dropping This Week</h2>
              <span className="weekly-radar-badge">
                <Sparkles size={11} />
                <span>Forward Intel</span>
              </span>
            </div>
            <p className="weekly-radar-sub">
              Upcoming tech launches, streaming releases, major match fixtures & policy milestones
            </p>
          </div>
        </div>

        {/* Action Controls: Live Alert Simulation & Filter Chips */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          {/* Quick Simulation Trigger Button */}
          <button
            type="button"
            onClick={() => {
              const testItem = RADAR_ITEMS[0];
              setActiveAlertPopup(testItem);
            }}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '6px 12px',
              borderRadius: 20,
              fontSize: 11.5,
              fontWeight: 800,
              background: 'linear-gradient(135deg, rgba(0, 229, 255, 0.18), rgba(0, 229, 255, 0.05))',
              border: '1px solid rgba(0, 229, 255, 0.35)',
              color: '#00E5FF',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
            title="Preview how a reminder alerts you when an event drops"
          >
            <Zap size={13} />
            <span>Simulate Drop Alert</span>
          </button>

          {/* Filter Chips */}
          <div className="weekly-radar-filters">
            {FILTER_TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                className={`weekly-radar-filter-btn ${selectedFilter === tab.id ? 'active' : ''}`}
                onClick={() => setSelectedFilter(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ============================================================== */}
      {/* RADAR CARDS GRID                                               */}
      {/* ============================================================== */}
      <div className="weekly-radar-grid">
        {filteredItems.map((item) => {
          const isReminded = reminders.has(item.id);
          const IconComp = item.icon || Sparkles;
          const isMenuOpen = calendarMenuOpenId === item.id;

          return (
            <article
              key={item.id}
              className={`weekly-radar-card ${isReminded ? 'radar-card-armed' : ''}`}
              style={{
                '--radar-accent': item.accentColor,
                border: isReminded
                  ? `1.5px solid ${item.accentColor}`
                  : '1px solid rgba(255, 255, 255, 0.08)',
                boxShadow: isReminded
                  ? `0 8px 30px rgba(0, 0, 0, 0.5), 0 0 20px ${item.accentColor}30`
                  : 'none',
                position: 'relative',
              }}
            >
              {/* Card Top Row: Date Pill & Status Cluster */}
              <div className="radar-card-top">
                <div className="radar-date-pill">
                  <span className="radar-date-num">{item.date}</span>
                  <span className="radar-date-day">{item.dayName.slice(0, 3).toUpperCase()}</span>
                </div>

                <div className="radar-status-cluster">
                  {/* Blinking Indicator if Reminder is Armed */}
                  {isReminded && (
                    <span
                      className="radar-badge-pill radar-armed-pill"
                      style={{
                        background: `${item.accentColor}18`,
                        borderColor: `${item.accentColor}50`,
                        color: item.accentColor,
                      }}
                    >
                      <span
                        className="radar-beacon-dot"
                        style={{
                          background: item.accentColor,
                          boxShadow: `0 0 8px ${item.accentColor}`,
                        }}
                      />
                      <span>Alert Armed</span>
                    </span>
                  )}

                  <span className={`radar-badge-pill radar-urgency-tag ${item.statusUrgency}`}>
                    <Clock size={11} style={{ flexShrink: 0 }} />
                    <span>{item.relativeTime}</span>
                  </span>
                </div>
              </div>

              {/* Category & Tag */}
              <div className="radar-card-meta">
                <span
                  className="radar-category-pill"
                  style={{
                    backgroundColor: `${item.accentColor}18`,
                    borderColor: `${item.accentColor}44`,
                    color: item.accentColor,
                  }}
                >
                  <IconComp size={12} />
                  <span>{item.category}</span>
                </span>

                <span className="radar-tag-pill">{item.tag}</span>
              </div>

              {/* Title & Description */}
              <h3
                className="radar-card-title"
                style={{ cursor: 'pointer', transition: 'color 0.15s ease' }}
                onClick={() => {
                  const query = encodeURIComponent(item.title);
                  const category = encodeURIComponent(item.category);
                  navigate(`/search?q=${query}&category=${category}&from=radar`);
                }}
                title="Read live dispatch via Gemini AI"
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = item.accentColor || '#00E5FF';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = '#FFFFFF';
                }}
              >
                {item.title}
              </h3>
              <p className="radar-card-desc">{item.description}</p>

              {/* Card Action Row: Remind Me + Add to Calendar */}
              <div
                className="radar-card-footer"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 8,
                  position: 'relative',
                }}
              >
                {/* Remind Me Button */}
                <button
                  type="button"
                  className={`radar-remind-btn ${isReminded ? 'active' : ''}`}
                  onClick={() => toggleReminder(item)}
                  style={{
                    background: isReminded ? item.accentColor : 'rgba(255, 255, 255, 0.05)',
                    color: isReminded ? '#000000' : 'rgba(255, 255, 255, 0.75)',
                    border: isReminded ? `1px solid ${item.accentColor}` : '1px solid rgba(255, 255, 255, 0.1)',
                    boxShadow: isReminded ? `0 0 14px ${item.accentColor}66` : 'none',
                    fontWeight: 800,
                  }}
                  aria-label={isReminded ? 'Alert armed' : 'Remind me of this drop'}
                >
                  {isReminded ? (
                    <>
                      <Check size={13} strokeWidth={3} />
                      <span>Alert Armed</span>
                    </>
                  ) : (
                    <>
                      <Bell size={13} />
                      <span>Remind Me</span>
                    </>
                  )}
                </button>

                {/* Calendar Add Button */}
                <div style={{ position: 'relative' }}>
                  <button
                    type="button"
                    onClick={() => setCalendarMenuOpenId(isMenuOpen ? null : item.id)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 5,
                      padding: '5px 10px',
                      borderRadius: 8,
                      fontSize: 11.5,
                      fontWeight: 700,
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.12)',
                      color: '#cbd5e1',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                    title="Add to Calendar"
                  >
                    <CalendarPlus size={13} />
                    <span>Calendar</span>
                  </button>

                  {/* Calendar Options Dropdown */}
                  {isMenuOpen && (
                    <div
                      style={{
                        position: 'absolute',
                        bottom: '100%',
                        right: 0,
                        marginBottom: 6,
                        zIndex: 20,
                        background: '#0D101A',
                        border: '1px solid rgba(255, 255, 255, 0.15)',
                        borderRadius: 10,
                        padding: 6,
                        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 4,
                        minWidth: 170,
                      }}
                    >
                      {/* Google Calendar Link */}
                      <a
                        href={createGoogleCalendarUrl(item)}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={() => setCalendarMenuOpenId(null)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8,
                          padding: '6px 10px',
                          borderRadius: 6,
                          fontSize: 11.5,
                          fontWeight: 700,
                          color: '#ffffff',
                          textDecoration: 'none',
                          background: 'rgba(255, 255, 255, 0.04)',
                          transition: 'all 0.15s ease',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = 'rgba(0, 229, 255, 0.15)';
                          e.currentTarget.style.color = '#00E5FF';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                          e.currentTarget.style.color = '#ffffff';
                        }}
                      >
                        <ExternalLink size={12} />
                        <span>Google Calendar</span>
                      </a>

                      {/* Download .ICS */}
                      <button
                        type="button"
                        onClick={() => {
                          downloadIcsCalendar(item);
                          setCalendarMenuOpenId(null);
                        }}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8,
                          padding: '6px 10px',
                          borderRadius: 6,
                          fontSize: 11.5,
                          fontWeight: 700,
                          color: '#ffffff',
                          background: 'rgba(255, 255, 255, 0.04)',
                          border: 'none',
                          cursor: 'pointer',
                          textAlign: 'left',
                          width: '100%',
                          transition: 'all 0.15s ease',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = 'rgba(0, 229, 255, 0.15)';
                          e.currentTarget.style.color = '#00E5FF';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                          e.currentTarget.style.color = '#ffffff';
                        }}
                      >
                        <Download size={12} />
                        <span>Apple / Outlook (.ics)</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </article>
          );
        })}
      </div>

      {/* Global Embedded Keyframes for Beacon & Slide-up Animation */}
      <style>{`
        .radar-card-top {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          min-height: 24px;
        }
        .radar-date-pill {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          flex-shrink: 0;
        }
        .radar-date-num {
          font-size: 1.02rem;
          font-weight: 800;
          color: #FFFFFF;
          letter-spacing: -0.01em;
          line-height: 1;
        }
        .radar-date-day {
          font-size: 0.66rem;
          color: rgba(255, 255, 255, 0.55);
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          line-height: 1;
          padding: 2px 5px;
          border-radius: 4px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .radar-status-cluster {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          flex-shrink: 0;
        }
        .radar-badge-pill {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 4px;
          height: 22px;
          padding: 0 7px;
          border-radius: 6px;
          font-size: 11px;
          font-weight: 700;
          line-height: 1;
          white-space: nowrap;
          box-sizing: border-box;
          vertical-align: middle;
        }
        .radar-armed-pill {
          letter-spacing: 0.02em;
        }
        .radar-beacon-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          display: inline-block;
          flex-shrink: 0;
          animation: radarPulseBeacon 1.2s infinite;
        }
        .radar-urgency-tag {
          font-size: 11px;
        }
        @keyframes radarPulseBeacon {
          0%, 100% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.3;
            transform: scale(1.3);
          }
        }
        @keyframes radarSlideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .radar-card-armed {
          transition: border-color 0.3s ease, box-shadow 0.3s ease;
        }
      `}</style>
    </section>
  );
}
