import React, { useState, useRef, useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { FiHome, FiTrendingUp, FiTarget, FiBell, FiSettings,
         FiMenu, FiUser, FiLogOut, FiChevronRight } from 'react-icons/fi';

export default function Layout() {
  const [collapsed,    setCollapsed]    = useState(false);
  const [avatarOpen,   setAvatarOpen]   = useState(false);
  const avatarRef = useRef(null);
  const navigate  = useNavigate();

  const user = (() => {
    try { return JSON.parse(localStorage.getItem('user') || '{}'); }
    catch { return {}; }
  })();

  const initial = (user.full_name || user.username || 'U')[0].toUpperCase();

  // Close dropdown when clicking outside
  useEffect(() => {
    const handler = (e) => {
      if (avatarRef.current && !avatarRef.current.contains(e.target)) {
        setAvatarOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard',      path: '/',               icon: <FiHome /> },
    { name: 'Market Analysis', path: '/market-analysis', icon: <FiTrendingUp /> },
    { name: 'Predictions',    path: '/predictions',    icon: <FiTarget /> },
    { name: 'Alerts',         path: '/alerts',         icon: <FiBell /> },
    { name: 'Settings',       path: '/settings',       icon: <FiSettings /> },
  ];

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-logo">
          <div className="logo-icon">M</div>
          {!collapsed && <span className="logo-text">Next Move</span>}
        </div>

        <nav className="sidebar-nav">
          <button className="sidebar-toggle" onClick={() => setCollapsed(!collapsed)}>
            <FiMenu />
          </button>

          {navItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) => `sidebar-nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              {!collapsed && <span>{item.name}</span>}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Header */}
      <header className={`header ${collapsed ? 'sidebar-collapsed' : ''}`}>
        <div className="header-left">
          <h2 className="header-title">MarketPulse</h2>
        </div>

        <div className="header-right">
          <div className="market-status open">
            <div className="status-dot"></div>
            Market Open
          </div>

          {/* Bell — goes to alerts */}
          <button
            className="header-icon-btn"
            onClick={() => navigate('/alerts')}
            title="Alerts"
            style={{ cursor: 'pointer' }}
          >
            <FiBell />
            <span className="notification-dot"></span>
          </button>

          {/* Avatar with dropdown */}
          <div ref={avatarRef} style={{ position: 'relative' }}>
            <div
              className="sidebar-user-avatar"
              onClick={() => setAvatarOpen(v => !v)}
              title={user.username || 'Account'}
              style={{ cursor: 'pointer', userSelect: 'none' }}
            >
              {initial}
            </div>

            {avatarOpen && (
              <div style={{
                position: 'absolute', right: 0, top: 'calc(100% + 10px)',
                width: 220, background: 'var(--bg-elevated, #1a2138)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 12, boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
                zIndex: 1000, overflow: 'hidden',
              }}>
                {/* User info */}
                <div style={{ padding: '14px 16px',
                  borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>
                    {user.full_name || user.username || 'User'}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)',
                    marginTop: 2 }}>{user.email || ''}</div>
                  <div style={{ marginTop: 6, display: 'inline-block',
                    padding: '2px 8px', borderRadius: 4, fontSize: '0.7rem',
                    fontWeight: 700, textTransform: 'uppercase',
                    background: 'rgba(0,212,255,0.12)', color: 'var(--cyan)' }}>
                    {user.role || 'free'}
                  </div>
                </div>

                {/* Menu items */}
                {[
                  { label: 'Profile & Settings', icon: <FiUser size={14}/>,
                    action: () => { navigate('/settings'); setAvatarOpen(false); } },
                  { label: 'My Alerts', icon: <FiBell size={14}/>,
                    action: () => { navigate('/alerts'); setAvatarOpen(false); } },
                ].map(item => (
                  <button key={item.label} onClick={item.action}
                    style={{ display: 'flex', alignItems: 'center', gap: 10,
                      width: '100%', padding: '11px 16px', border: 'none',
                      background: 'none', color: 'var(--text-primary)',
                      cursor: 'pointer', fontSize: '0.85rem', textAlign: 'left',
                      borderBottom: '1px solid rgba(255,255,255,0.05)',
                      transition: 'background 0.15s' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'none'}
                  >
                    <span style={{ color: 'var(--text-secondary)' }}>{item.icon}</span>
                    {item.label}
                    <FiChevronRight size={12} style={{ marginLeft: 'auto',
                      color: 'var(--text-tertiary)' }} />
                  </button>
                ))}

                {/* Logout */}
                <button onClick={logout}
                  style={{ display: 'flex', alignItems: 'center', gap: 10,
                    width: '100%', padding: '11px 16px', border: 'none',
                    background: 'none', color: '#ff4757',
                    cursor: 'pointer', fontSize: '0.85rem', textAlign: 'left',
                    transition: 'background 0.15s' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,71,87,0.08)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'none'}
                >
                  <FiLogOut size={14} /> Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className={`main-content ${collapsed ? 'sidebar-collapsed' : ''}`}>
        <div className="page-content">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
