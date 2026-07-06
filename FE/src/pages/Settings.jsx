import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { FiUser, FiLogOut, FiSave, FiBriefcase, FiPlus, FiTrash2 } from 'react-icons/fi';

const fmtPrice = v =>
  v != null ? '$' + Number(v).toLocaleString('en-US', { minimumFractionDigits: 2 }) : '—';

export default function Settings() {
  const navigate = useNavigate();
  const [user,       setUser]       = useState(null);
  const [portfolios, setPortfolios] = useState([]);
  const [tab,        setTab]        = useState('profile');
  const [saving,     setSaving]     = useState(false);
  const [msg,        setMsg]        = useState('');
  const [newPf,      setNewPf]      = useState({ name: '', initial_investment: '' });

  const authHeader = () => {
    const t = localStorage.getItem('token');
    return t ? { Authorization: `Bearer ${t}` } : {};
  };

  useEffect(() => {
    const stored = localStorage.getItem('user');
    if (stored) setUser(JSON.parse(stored));

    api.get('/auth/me', { headers: authHeader() })
      .then(r => { setUser(r.data); localStorage.setItem('user', JSON.stringify(r.data)); })
      .catch(() => {});

    api.get('/portfolio', { headers: authHeader() })
      .then(r => setPortfolios(r.data))
      .catch(() => {});
  }, []);

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const createPortfolio = async (e) => {
    e.preventDefault();
    try {
      const res = await api.post('/portfolio', {
        name: newPf.name,
        initial_investment: parseFloat(newPf.initial_investment || 0),
      }, { headers: authHeader() });
      setPortfolios(p => [...p, res.data]);
      setNewPf({ name: '', initial_investment: '' });
      setMsg('Portfolio created.');
    } catch (e) {
      setMsg('Failed to create portfolio.');
    }
  };

  const deletePortfolio = async (id) => {
    try {
      await api.delete(`/portfolio/${id}`, { headers: authHeader() });
      setPortfolios(p => p.filter(x => x.id !== id));
    } catch { /* ignore */ }
  };

  const TABS = [
    { id: 'profile',   label: 'Profile',    Icon: FiUser       },
    { id: 'portfolio', label: 'Portfolios', Icon: FiBriefcase  },
  ];

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1>Settings</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: 2 }}>
          Account preferences & portfolio management
        </p>
      </div>

      {/* Tab bar */}
      <div style={{ display: 'flex', gap: '0.25rem', padding: 4,
        background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)',
        marginBottom: '1.5rem', width: 'fit-content' }}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            style={{ display: 'flex', alignItems: 'center', gap: 6, border: 'none',
              borderRadius: 'var(--radius-sm)', cursor: 'pointer',
              padding: '6px 16px', fontWeight: 600, fontSize: '0.82rem',
              background: tab === t.id ? 'var(--cyan)' : 'transparent',
              color:      tab === t.id ? 'var(--bg-primary)' : 'var(--text-secondary)' }}>
            <t.Icon size={13} /> {t.label}
          </button>
        ))}
      </div>

      {msg && (
        <div style={{ padding: '8px 14px', borderRadius: 8, marginBottom: '1rem',
          background: 'rgba(0,212,255,0.1)', color: 'var(--cyan)',
          fontSize: '0.85rem' }}>{msg}</div>
      )}

      {/* Profile tab */}
      {tab === 'profile' && user && (
        <div style={{ display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '1rem' }}>

          <div className="card">
            <h3 style={{ marginBottom: '1.25rem', fontSize: '0.95rem' }}>Account Info</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {[
                { label: 'Username',  value: user.username  },
                { label: 'Email',     value: user.email     },
                { label: 'Full Name', value: user.full_name },
                { label: 'Role',      value: user.role      },
                { label: 'Last Login',value: user.last_login
                    ? new Date(user.last_login).toLocaleString() : '—' },
              ].map(({ label, value }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between',
                  padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>{label}</span>
                  <span style={{ fontWeight: 600, fontSize: '0.88rem',
                    textTransform: 'capitalize' }}>{value || '—'}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h3 style={{ marginBottom: '1.25rem', fontSize: '0.95rem' }}>Actions</h3>
            <button onClick={logout}
              style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%',
                padding: '10px 16px', border: '1px solid rgba(255,71,87,0.3)',
                borderRadius: 8, background: 'rgba(255,71,87,0.08)',
                color: '#ff4757', fontWeight: 600, cursor: 'pointer',
                fontSize: '0.88rem' }}>
              <FiLogOut size={15} /> Sign Out
            </button>
          </div>
        </div>
      )}

      {/* Portfolio tab */}
      {tab === 'portfolio' && (
        <div>
          {/* Create form */}
          <div className="card" style={{ marginBottom: '1rem' }}>
            <h3 style={{ marginBottom: '1rem', fontSize: '0.95rem' }}>New Portfolio</h3>
            <form onSubmit={createPortfolio}
              style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap',
                alignItems: 'flex-end' }}>
              <label style={{ flex: 2, minWidth: 140, display: 'flex',
                flexDirection: 'column', gap: 5 }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)',
                  textTransform: 'uppercase' }}>Name</span>
                <input required type="text" placeholder="My Portfolio"
                  value={newPf.name}
                  onChange={e => setNewPf(p => ({ ...p, name: e.target.value }))}
                  style={{ padding: '8px 12px', background: 'var(--bg-tertiary)',
                    border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8,
                    color: 'var(--text-primary)', outline: 'none' }} />
              </label>
              <label style={{ flex: 1, minWidth: 120, display: 'flex',
                flexDirection: 'column', gap: 5 }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)',
                  textTransform: 'uppercase' }}>Initial ($)</span>
                <input type="number" placeholder="10000"
                  value={newPf.initial_investment}
                  onChange={e => setNewPf(p => ({ ...p, initial_investment: e.target.value }))}
                  style={{ padding: '8px 12px', background: 'var(--bg-tertiary)',
                    border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8,
                    color: 'var(--text-primary)', outline: 'none' }} />
              </label>
              <button type="submit"
                style={{ padding: '9px 18px', border: 'none', borderRadius: 8,
                  background: 'var(--cyan)', color: 'var(--bg-primary)',
                  fontWeight: 700, cursor: 'pointer', whiteSpace: 'nowrap' }}>
                <FiPlus size={14} style={{ marginRight: 6 }} /> Create
              </button>
            </form>
          </div>

          {/* Portfolio list */}
          {portfolios.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem',
              color: 'var(--text-secondary)' }}>
              <FiBriefcase size={36} color="var(--text-tertiary)" />
              <p style={{ marginTop: '1rem' }}>No portfolios yet.</p>
            </div>
          ) : (
            <div style={{ display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
              gap: '1rem' }}>
              {portfolios.map(pf => (
                <div key={pf.id} className="card" style={{ marginBottom: 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between',
                    alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                    <div>
                      <h3 style={{ margin: 0, fontSize: '1rem' }}>{pf.name}</h3>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)',
                        textTransform: 'capitalize' }}>{pf.risk_level} risk</span>
                    </div>
                    <button onClick={() => deletePortfolio(pf.id)}
                      style={{ background: 'none', border: 'none', cursor: 'pointer',
                        color: 'var(--text-tertiary)' }}>
                      <FiTrash2 size={14} />
                    </button>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between',
                    fontSize: '0.82rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Invested</span>
                    <span>{fmtPrice(pf.initial_investment)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between',
                    fontSize: '0.82rem', marginTop: 4 }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Current Value</span>
                    <span>{fmtPrice(pf.current_value)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
