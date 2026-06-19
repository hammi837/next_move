import React, { useState } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { FiHome, FiTrendingUp, FiTarget, FiBell, FiSettings, FiMenu } from 'react-icons/fi';

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);

  const navItems = [
    { name: 'Dashboard', path: '/', icon: <FiHome /> },
    { name: 'Market Analysis', path: '/market-analysis', icon: <FiTrendingUp /> },
    { name: 'Predictions', path: '/predictions', icon: <FiTarget /> },
    { name: 'Alerts', path: '/alerts', icon: <FiBell /> },
    { name: 'Settings', path: '/settings', icon: <FiSettings /> },
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
          <button className="header-icon-btn">
            <FiBell />
            <span className="notification-dot"></span>
          </button>
          <div className="sidebar-user-avatar">H</div>
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
