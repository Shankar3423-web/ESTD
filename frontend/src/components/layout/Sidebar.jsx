import React from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  Home,
  Video,
  Radio,
  Search,
  Bookmark,
  User,
  Film,
  Trophy,
  Cpu,
  Compass,
  TrendingUp,
  Sparkles,
} from 'lucide-react';
import { CATEGORIES } from '../../constants/taxonomy';

export default function Sidebar({ onOpenDiagnostics, systemStatus }) {
  const location = useLocation();
  const navigate = useNavigate();

  const primaryDestinations = [
    { label: 'Home (For You)', path: '/', icon: Home, accent: '#00E5FF' },
    { label: 'Watch', path: '/watch', icon: Video, accent: '#FF20B8', badge: 'VIDEO' },
    { label: 'Live', path: '/live', icon: Radio, accent: '#EF4444', isLive: true },
    { label: 'Ask ESTD', path: '/search', icon: Search, accent: '#B8FF3B' },
    { label: 'Saved', path: '/saved', icon: Bookmark, accent: '#FFB020' },
    { label: 'Profile', path: '/you', icon: User, accent: '#A855F7' },
  ];

  const categoryDestinations = CATEGORIES.map((cat) => ({
    label: cat.name,
    path: `/category/${cat.slug}`,
    icon: getCategoryIcon(cat.code),
    accent: cat.color,
    code: cat.code,
  }));

  function getCategoryIcon(code) {
    switch (code) {
      case 'ENT':
        return Film;
      case 'SPORTS':
        return Trophy;
      case 'TECH':
        return Cpu;
      case 'DEV':
        return Compass;
      case 'BIZ_FIN':
        return TrendingUp;
      default:
        return Sparkles;
    }
  }

  return (
    <aside className="app-sidebar" aria-label="ESTD Navigation">
      {/* Brand Header */}
      <div className="brand-wrapper">
        <NavLink to="/" className="brand-logo">
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: 'linear-gradient(135deg, #00E5FF, #FF20B8)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#07080B',
              fontWeight: 900,
              fontSize: 16,
              boxShadow: '0 0 16px rgba(0, 229, 255, 0.4)',
            }}
          >
            E
          </div>
          <span>ESTD</span>
        </NavLink>
        <span className="brand-badge">DESKTOP</span>
      </div>

      {/* Nav links */}
      <nav className="sidebar-nav">
        <div className="nav-section-label">Feed & Intelligence</div>
        {primaryDestinations.map((item) => {
          const Icon = item.icon;
          const isActive = item.path === '/'
            ? location.pathname === '/'
            : location.pathname.startsWith(item.path);

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`nav-link ${isActive ? 'active' : ''}`}
              style={{ '--accent-color': item.accent }}
            >
              <Icon size={18} style={{ color: isActive ? item.accent : 'currentColor' }} />
              <span style={{ flex: 1 }}>{item.label}</span>
              {item.isLive && (
                <span className="sidebar-live-dot" />
              )}
              {item.badge && (
                <span
                  style={{
                    fontSize: 9.5,
                    fontWeight: 800,
                    padding: '2px 6px',
                    borderRadius: 4,
                    background: `${item.accent}22`,
                    color: item.accent,
                    border: `1px solid ${item.accent}44`,
                    letterSpacing: '0.04em',
                  }}
                >
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}

        <div className="nav-section-label" style={{ marginTop: 8 }}>Categories</div>
        {categoryDestinations.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname.startsWith(item.path);
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`nav-link ${isActive ? 'active' : ''}`}
              style={{ '--accent-color': item.accent }}
            >
              <span
                className="nav-link-dot"
                style={{
                  background: item.accent,
                  boxShadow: isActive ? `0 0 8px ${item.accent}` : 'none',
                }}
              />
              <span style={{ flex: 1 }}>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Sidebar Footer */}
      <div className="sidebar-footer" />
    </aside>
  );
}
