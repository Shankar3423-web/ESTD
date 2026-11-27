import React, { useState, useMemo, useEffect, useCallback } from 'react';
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
  TrendingUp,
  Compass,
  Check,
  CalendarPlus,
  ExternalLink,
  Download,
  X,
  Zap,
  RefreshCw,
  Newspaper,
} from 'lucide-react';
import {
  fetchWeeklyRadar,
  refreshWeeklyRadar,
  getCachedWeeklyRadar,
} from '../../api/estdApi';

const CATEGORY_VISUALS = {
  Tech: { accentColor: '#00E5FF', icon: Cpu },
  Entertainment: { accentColor: '#FF20B8', icon: Film },
  Sports: { accentColor: '#10B981', icon: Trophy },
  Developments: { accentColor: '#38BDF8', icon: Compass },
  'Business & Finance': { accentColor: '#FFB020', icon: TrendingUp },
};

const FILTER_TABS = [
  { id: 'All', label: 'All Drops' },
  { id: 'Tech', label: 'Tech & AI' },
  { id: 'Entertainment', label: 'Entertainment' },
  { id: 'Sports', label: 'Sports' },
  { id: 'Developments', label: 'Policy & Science' },
  { id: 'Business & Finance', label: 'Markets' },
];

const REMINDERS_STORAGE_KEY = 'estd_radar_reminders_v2';
const FIRED_ALERTS_STORAGE_KEY = 'estd_radar_fired_alerts_v2';

function getReminderKey(item) {
  return item?.drop_key || item?.id;
}

function loadStoredMap(key) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : {};
  } catch {
    return {};
  }
}

function saveStoredMap(key, mapObj) {
  try {
    localStorage.setItem(key, JSON.stringify(mapObj));
  } catch {}
}

/**
 * Dynamically compute local date display, relative badge, and urgency from ISO timestamp.
 */
function computeLocalRadarTiming(item, nowMs) {
  const rawIso = item?.event_date;
  const parsed = rawIso ? new Date(rawIso) : null;
  if (!parsed || Number.isNaN(parsed.getTime())) {
    return {
      date: item?.date || 'Soon',
      dayShort: item?.day_short || 'TBD',
      dayName: item?.day_name || 'Upcoming',
      relativeTime: item?.relative_time || 'Upcoming',
      statusUrgency: item?.status_urgency || 'normal',
      isDueNow: false,
      eventMs: nowMs + 86400000,
    };
  }

  const now = new Date(nowMs);
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const startOfEventDay = new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate()).getTime();
  const deltaDays = Math.round((startOfEventDay - startOfToday) / 86400000);
  const eventMs = parsed.getTime();
  const isDueNow = nowMs >= eventMs;

  const date = parsed.toLocaleDateString('en-US', { month: 'short', day: '2-digit' });
  const dayShort = parsed.toLocaleDateString('en-US', { weekday: 'short' }).toUpperCase();
  const dayName = parsed.toLocaleDateString('en-US', { weekday: 'long' });

  let relativeTime = 'Upcoming';
  let statusUrgency = 'normal';

  if (deltaDays < 0) {
    relativeTime = 'Recent';
    statusUrgency = 'normal';
  } else if (deltaDays === 0) {
    relativeTime = isDueNow ? 'Live Today' : 'Dropping Today';
    statusUrgency = 'urgent';
  } else if (deltaDays === 1) {
    relativeTime = 'Tomorrow';
    statusUrgency = 'urgent';
  } else if (deltaDays === 2) {
    relativeTime = 'In 2 Days';
    statusUrgency = 'urgent';
  } else if (deltaDays <= 6) {
    const evWeekday = parsed.getDay(); // 0=Sun, 6=Sat
    const nowWeekday = now.getDay();
    if ((evWeekday === 0 || evWeekday === 6) && nowWeekday >= 1 && nowWeekday <= 5) {
      relativeTime = 'This Weekend';
    } else {
      relativeTime = `In ${deltaDays} Days`;
    }
    statusUrgency = 'soon';
  } else if (deltaDays <= 13) {
    relativeTime = 'Next Week';
    statusUrgency = 'normal';
  }

  return {
    date,
    dayShort,
    dayName,
    relativeTime,
    statusUrgency,
    isDueNow,
    eventMs,
  };
}

function formatSyncAge(isoString, nowMs) {
  if (!isoString) return null;
  const ts = new Date(isoString).getTime();
  if (Number.isNaN(ts)) return null;
  const diffMins = Math.max(0, Math.floor((nowMs - ts) / 60000));
  if (diffMins < 1) return 'Synced just now';
  if (diffMins < 60) return `Synced ${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `Synced ${diffHours}h ago`;
  return `Synced ${Math.floor(diffHours / 24)}d ago`;
}

function createGoogleCalendarUrl(item) {
  const text = encodeURIComponent(`[ESTD Radar] ${item.title}`);
  const details = encodeURIComponent(
    `${item.description}\n\nTracked live on ESTD News Platform.\nCategory: ${item.category} • ${item.tag}`
  );
  const location = encodeURIComponent('ESTD News Live Wire');
  const startIcs = item.target_date_ics || new Date(item.event_date).toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
  const endIcs = item.end_date_ics || startIcs;
  return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${text}&details=${details}&location=${location}&dates=${startIcs}/${endIcs}`;
}

function downloadIcsCalendar(item) {
  const startDate =
    item.target_date_ics || new Date(item.event_date).toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
  const endDate = item.end_date_ics || startDate;
  const now = new Date().toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';

  const icsBody = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//ESTD News Platform//Radar Forward Intel//EN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'BEGIN:VEVENT',
    `UID:${item.drop_key || item.id}@estd.news`,
    `DTSTAMP:${now}`,
    `DTSTART:${startDate}`,
    `DTEND:${endDate}`,
    `SUMMARY:[ESTD Radar] ${item.title}`,
    `DESCRIPTION:${(item.description || '').replace(/\r?\n/g, ' ')}`,
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
  anchor.download = `${item.id || 'radar-drop'}-calendar-reminder.ics`;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.URL.revokeObjectURL(url);
}

export default function WeeklyRadarDrop() {
  const navigate = useNavigate();
  const [selectedFilter, setSelectedFilter] = useState('All');
  const [nowMs, setNowMs] = useState(() => Date.now());

  const initialCache = useMemo(() => getCachedWeeklyRadar(), []);
  const [radarItems, setRadarItems] = useState(() => initialCache?.items || []);
  const [generatedAt, setGeneratedAt] = useState(() => initialCache?.generated_at || null);
  const [loading, setLoading] = useState(() => !(initialCache?.items?.length > 0));
  const [refreshing, setRefreshing] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // Armed reminders stored as { [drop_key]: { ...snapshot } }
  const [remindersMap, setRemindersMap] = useState(() => {
    try {
      localStorage.removeItem('estd_radar_reminders'); // Clean up legacy static demo keys
    } catch {}
    return loadStoredMap(REMINDERS_STORAGE_KEY);
  });
  const [firedAlertsMap, setFiredAlertsMap] = useState(() => loadStoredMap(FIRED_ALERTS_STORAGE_KEY));

  const [calendarMenuOpenId, setCalendarMenuOpenId] = useState(null);
  const [activeAlertPopup, setActiveAlertPopup] = useState(null);
  const [armNotice, setArmNotice] = useState(null);

  // Keep local clock ticking every 60s so relative labels & due reminders stay live
  useEffect(() => {
    const timer = setInterval(() => setNowMs(Date.now()), 60000);
    return () => clearInterval(timer);
  }, []);

  const loadRadar = useCallback(async ({ forceRefresh = false } = {}) => {
    if (forceRefresh) {
      setRefreshing(true);
    } else if (radarItems.length === 0) {
      setLoading(true);
    }
    setErrorMsg(null);
    try {
      const res = forceRefresh ? await refreshWeeklyRadar() : await fetchWeeklyRadar();
      if (res && Array.isArray(res.items)) {
        setRadarItems(res.items);
        setGeneratedAt(res.generated_at || new Date().toISOString());
      }
    } catch (err) {
      console.warn('Failed to load dynamic Weekly Radar:', err);
      if (radarItems.length === 0) {
        setErrorMsg(err.message || 'Unable to sync live Weekly Radar events.');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [radarItems.length]);

  useEffect(() => {
    loadRadar({ forceRefresh: false });
  }, []);

  // Automatically trigger live alert popup + notification when any armed reminder reaches its drop time
  useEffect(() => {
    if (!radarItems.length) return;
    for (const item of radarItems) {
      const key = getReminderKey(item);
      if (!remindersMap[key] || firedAlertsMap[key]) continue;

      const timing = computeLocalRadarTiming(item, nowMs);
      if (timing.isDueNow) {
        const visual = CATEGORY_VISUALS[item.category] || { accentColor: '#00E5FF' };
        const enriched = { ...item, accentColor: visual.accentColor, isSimulated: false };
        setActiveAlertPopup(enriched);

        const nextFired = { ...firedAlertsMap, [key]: new Date(nowMs).toISOString() };
        setFiredAlertsMap(nextFired);
        saveStoredMap(FIRED_ALERTS_STORAGE_KEY, nextFired);

        if ('Notification' in window && Notification.permission === 'granted') {
          try {
            new Notification('🔔 ESTD Radar Event Dropping Now!', {
              body: item.title,
              icon: '/favicon.ico',
            });
          } catch {}
        }
        break;
      }
    }
  }, [radarItems, remindersMap, firedAlertsMap, nowMs]);

  const toggleReminder = async (item, timing, visual) => {
    const key = getReminderKey(item);
    const isCurrentlyReminded = Boolean(remindersMap[key]);

    if (isCurrentlyReminded) {
      const next = { ...remindersMap };
      delete next[key];
      setRemindersMap(next);
      saveStoredMap(REMINDERS_STORAGE_KEY, next);
      setArmNotice(null);
      return;
    }

    const next = {
      ...remindersMap,
      [key]: {
        id: item.id,
        drop_key: key,
        title: item.title,
        event_date: item.event_date,
        category: item.category,
        armed_at: new Date().toISOString(),
      },
    };
    setRemindersMap(next);
    saveStoredMap(REMINDERS_STORAGE_KEY, next);

    if ('Notification' in window) {
      try {
        if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
          const perm = await Notification.requestPermission();
          if (perm === 'granted') {
            new Notification('🔔 ESTD Radar Reminder Armed', {
              body: `${timing.date} (${timing.relativeTime}): "${item.title}"`,
              icon: '/favicon.ico',
            });
          }
        }
      } catch {}
    }

    if (timing.isDueNow) {
      setActiveAlertPopup({ ...item, accentColor: visual.accentColor, isSimulated: false });
      const nextFired = { ...firedAlertsMap, [key]: new Date().toISOString() };
      setFiredAlertsMap(nextFired);
      saveStoredMap(FIRED_ALERTS_STORAGE_KEY, nextFired);
    } else {
      setArmNotice(`Reminder armed for ${timing.date} (${timing.relativeTime}) — we will alert you when it drops.`);
      setTimeout(() => {
        setArmNotice((curr) => (curr && curr.includes(timing.date) ? null : curr));
      }, 4500);
    }
  };

  const enrichedItems = useMemo(() => {
    return radarItems.map((item) => {
      const visual = CATEGORY_VISUALS[item.category] || { accentColor: '#00E5FF', icon: Sparkles };
      const timing = computeLocalRadarTiming(item, nowMs);
      const rawTitle = (item.title || '').replace(/\s+\|\s+[^|]+$/, '').trim();
      const conciseTitle = rawTitle.length > 82 ? rawTitle.slice(0, 82).replace(/\s+\S*$/, '') + '...' : rawTitle;
      const rawDesc = (item.description || '').replace(/\s+/g, ' ').trim();
      const conciseDesc = rawDesc.length > 135 ? rawDesc.slice(0, 135).replace(/\s+\S*$/, '') + '...' : rawDesc;
      return {
        ...item,
        conciseTitle,
        conciseDesc,
        accentColor: visual.accentColor,
        icon: visual.icon,
        timing,
      };
    });
  }, [radarItems, nowMs]);

  const filteredItems = useMemo(() => {
    if (selectedFilter === 'All') return enrichedItems;
    return enrichedItems.filter((item) => item.category === selectedFilter);
  }, [enrichedItems, selectedFilter]);

  const syncLabel = formatSyncAge(generatedAt, nowMs);

  return (
    <section className="weekly-radar-section" aria-label="What is Dropping This Week" style={{ position: 'relative' }}>
      {/* LIVE REMINDER ALERT TOAST POPUP */}
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
                {activeAlertPopup.isSimulated
                  ? '⚡ ALERT PREVIEW // DROP SIMULATION'
                  : '🔔 REMINDER ALERT // EVENT DROPPING NOW!'}
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
            {activeAlertPopup.isSimulated
              ? 'Preview of how your armed ESTD Radar alerts appear when a tracked event reaches its scheduled drop window.'
              : 'This scheduled event has reached its drop window on ESTD. Open the live AI briefing or source coverage below.'}
          </p>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
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

      {/* SECTION HEADER */}
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
              {syncLabel && (
                <span
                  style={{
                    fontSize: '0.68rem',
                    fontWeight: 600,
                    color: 'rgba(0, 229, 255, 0.85)',
                    background: 'rgba(0, 229, 255, 0.08)',
                    border: '1px solid rgba(0, 229, 255, 0.22)',
                    padding: '2px 8px',
                    borderRadius: 999,
                  }}
                >
                  {syncLabel}
                </span>
              )}
            </div>
            <p className="weekly-radar-sub">
              Upcoming launches, streaming drops, live fixtures & policy milestones extracted automatically from this week's news
            </p>
          </div>
        </div>

        {/* Action Controls: Sync Live News, Alert Preview & Filter Chips */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <button
            type="button"
            disabled={refreshing}
            onClick={() => loadRadar({ forceRefresh: true })}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '6px 12px',
              borderRadius: 20,
              fontSize: 11.5,
              fontWeight: 700,
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.14)',
              color: '#e2e8f0',
              cursor: refreshing ? 'wait' : 'pointer',
              opacity: refreshing ? 0.7 : 1,
              transition: 'all 0.15s ease',
            }}
            title="Re-scan the latest ingested news stories for upcoming events this week"
          >
            <RefreshCw size={13} className={refreshing ? 'radar-spin-icon' : ''} />
            <span>{refreshing ? 'Scanning News...' : 'Sync Live News'}</span>
          </button>

          {enrichedItems.length > 0 && (
            <button
              type="button"
              onClick={() => {
                const target = filteredItems[0] || enrichedItems[0];
                if (target) {
                  setActiveAlertPopup({ ...target, isSimulated: true });
                }
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
          )}

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

        {armNotice && (
          <div
            style={{
              fontSize: 12,
              color: '#00E5FF',
              background: 'rgba(0, 229, 255, 0.08)',
              border: '1px solid rgba(0, 229, 255, 0.25)',
              borderRadius: 10,
              padding: '8px 12px',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              alignSelf: 'flex-start',
            }}
          >
            <Bell size={13} />
            <span>{armNotice}</span>
          </div>
        )}
      </div>

      {/* LOADING / ERROR / EMPTY STATES */}
      {loading && radarItems.length === 0 ? (
        <div className="weekly-radar-grid">
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className="weekly-radar-card"
              style={{ minHeight: 190, opacity: 0.55, justifyContent: 'space-between' }}
            >
              <div style={{ height: 22, width: '55%', borderRadius: 6, background: 'rgba(255,255,255,0.08)' }} />
              <div style={{ height: 48, width: '92%', borderRadius: 8, background: 'rgba(255,255,255,0.06)' }} />
              <div style={{ height: 32, width: '100%', borderRadius: 8, background: 'rgba(255,255,255,0.05)' }} />
            </div>
          ))}
        </div>
      ) : errorMsg && radarItems.length === 0 ? (
        <div
          className="weekly-radar-card"
          style={{
            padding: 20,
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 12,
          }}
        >
          <span style={{ fontSize: 13, color: '#cbd5e1' }}>{errorMsg}</span>
          <button
            type="button"
            onClick={() => loadRadar({ forceRefresh: true })}
            className="weekly-radar-filter-btn active"
          >
            Retry Live Sync
          </button>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="weekly-radar-card" style={{ padding: 20 }}>
          <span style={{ fontSize: 13, color: 'rgba(255, 255, 255, 0.68)' }}>
            No upcoming events detected in this category yet for this week. Click{' '}
            <strong>Sync Live News</strong> or select <strong>All Drops</strong>.
          </span>
        </div>
      ) : (
        /* RADAR CARDS GRID */
        <div className="weekly-radar-grid">
          {filteredItems.map((item) => {
            const key = getReminderKey(item);
            const isReminded = Boolean(remindersMap[key]);
            const IconComp = item.icon || Sparkles;
            const isMenuOpen = calendarMenuOpenId === item.id;
            const { timing } = item;

            return (
              <article
                key={key}
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
                    <span className="radar-date-num">{timing.date}</span>
                    <span className="radar-date-day">{timing.dayShort}</span>
                  </div>

                  <div className="radar-status-cluster">
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

                    <span className={`radar-badge-pill radar-urgency-tag ${timing.statusUrgency}`}>
                      <Clock size={11} style={{ flexShrink: 0 }} />
                      <span>{timing.relativeTime}</span>
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
                  {item.conciseTitle || item.title}
                </h3>
                <p className="radar-card-desc">{item.conciseDesc || item.description}</p>

                {item.source_name && (
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 5,
                      fontSize: 11,
                      color: 'rgba(255, 255, 255, 0.45)',
                      marginTop: -2,
                    }}
                  >
                    <Newspaper size={11} />
                    <span>Via {item.source_name}</span>
                  </div>
                )}

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
                  <button
                    type="button"
                    className={`radar-remind-btn ${isReminded ? 'active' : ''}`}
                    onClick={() => toggleReminder(item, timing, item)}
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
      )}

      {/* Global Embedded Keyframes for Beacon, Spin & Slide-up Animation */}
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
        .radar-spin-icon {
          animation: radarSpin 0.9s linear infinite;
        }
        @keyframes radarSpin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
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
