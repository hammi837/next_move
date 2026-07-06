import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { FiBell, FiPlus, FiTrash2, FiToggleLeft, FiToggleRight, FiRefreshCw } from 'react-icons/fi';

const SYMBOLS    = ['GOLD', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'AMZN'];
const CONDITIONS = [
  { value: 'above',   label: 'Price goes above' },
  { value: 'below',   label: 'Price drops below' },
  { value: 'crosses', label: 'Price crosses (~0.5%)' },
];

const fmtPrice = v =>
  v != null ? '$' + Number(v).toLocaleString('en-US', { minimumFractionDigits: 2 }) : '—';

const conditionColor = { above: '#00e68a', below: '#ff4757', crosses: '#ffc107' };

export default function Alerts() {
  const [alerts,  setAlerts]  = useState([]);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');
  const [form,    setForm]    = useState({
    symbol: 'GOLD', condition: 'above', threshold_value: '', note: '', alert_type: 'price',
  });
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const authHeader = () => {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const fetchAlerts = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/alerts', { headers: authHeader() });
      setAlerts(res.data);
    } catch (e) {
      if (e.response?.status === 401) {
        setError('Please log in to manage alerts.');
      } else {
        setError('Failed to load alerts.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAlerts(); }, []);

  const createAlert = async (e) => {
    e.preventDefault();
    if (!form.threshold_value) return;
    setCreating(true);
    try {
      const res = await api.post('/alerts', {
        ...form,
        threshold_value: parseFloat(form.threshold_value),
      }, { headers: authHeader() });
      setAlerts(prev => [res.data, ...prev]);
      setForm(f => ({ ...f, threshold_value: '', note: '' }));
      setShowForm(false);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create alert');
    } finally {
      setCreating(false);
    }
  };

  const deleteAlert = async (id) => {
    try {
      await api.delete(`/alerts/${id}`, { headers: authHeader() });
      setAlerts(prev => prev.filter(a => a.id !== id));
    } catch { /* ignore */ }
  };

  const toggleAlert = async (alert) => {
    try {
      const res = await api.put(`/alerts/${alert.id}`,
        { is_active: !alert.is_active },
        { headers: authHeader() });
      setAlerts(prev => prev.map(a => a.id === alert.id ? res.data : a));
    } catch { /* ignore */ }
  };

  const active    = alerts.filter(a => a.is_active && !a.is_triggered);
  const triggered = alerts.filter(a => a.is_triggered);
  const inactive  = alerts.filter(a => !a.is_active && !a.is_triggered);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between',
        alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1>Price Alerts</h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: 2 }}>
            Get notified when prices hit your targets
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button onClick={fetchAlerts} className="btn"
            style={{ background: 'var(--glass-bg)', color: 'var(--text-primary)' }}>
            <FiRefreshCw size={14} />
          </button>
          <button onClick={() => setShowForm(v => !v)}
            style={{ display: 'flex', alignItems: 'center', gap: 6, border: 'none',
              borderRadius: 'var(--radius-md)', padding: '8px 16px',
              background: showForm ? 'rgba(0,212,255,0.15)' : 'var(--cyan)',
              color: showForm ? 'var(--cyan)' : 'var(--bg-primary)',
              fontWeight: 700, cursor: 'pointer' }}>
            <FiPlus size={15} /> {showForm ? 'Cancel' : 'New Alert'}
          </button>
        </div>
      </div>

      {error && (
        <div className="card" style={{ color: '#ff4757', marginBottom: '1rem',
          fontSize: '0.88rem' }}>{error}</div>
      )}

      {/* Create form */}
      {showForm && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ marginBottom: '1rem', fontSize: '0.95rem' }}>Create Alert</h3>
          <form onSubmit={createAlert}
            style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
              gap: '0.75rem', alignItems: 'end' }}>

            <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)',
                textTransform: 'uppercase' }}>Symbol</span>
              <select value={form.symbol}
                onChange={e => setForm(f => ({ ...f, symbol: e.target.value }))}
                style={{ padding: '8px 10px', background: 'var(--bg-tertiary)',
                  border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8,
                  color: 'var(--text-primary)', fontSize: '0.88rem' }}>
                {SYMBOLS.map(s => <option key={s}>{s}</option>)}
              </select>
            </label>

            <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)',
                textTransform: 'uppercase' }}>Condition</span>
              <select value={form.condition}
                onChange={e => setForm(f => ({ ...f, condition: e.target.value }))}
                style={{ padding: '8px 10px', background: 'var(--bg-tertiary)',
                  border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8,
                  color: 'var(--text-primary)', fontSize: '0.88rem' }}>
                {CONDITIONS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </label>

            <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)',
                textTransform: 'uppercase' }}>Price ($)</span>
              <input type="number" step="0.01" required
                placeholder="e.g. 4500"
                value={form.threshold_value}
                onChange={e => setForm(f => ({ ...f, threshold_value: e.target.value }))}
                style={{ padding: '8px 10px', background: 'var(--bg-tertiary)',
                  border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8,
                  color: 'var(--text-primary)', fontSize: '0.88rem', outline: 'none' }} />
            </label>

            <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)',
                textTransform: 'uppercase' }}>Note (optional)</span>
              <input type="text" placeholder="e.g. Resistance level"
                value={form.note}
                onChange={e => setForm(f => ({ ...f, note: e.target.value }))}
                style={{ padding: '8px 10px', background: 'var(--bg-tertiary)',
                  border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8,
                  color: 'var(--text-primary)', fontSize: '0.88rem', outline: 'none' }} />
            </label>

            <button type="submit" disabled={creating}
              style={{ padding: '9px 18px', border: 'none', borderRadius: 8,
                background: 'var(--cyan)', color: 'var(--bg-primary)',
                fontWeight: 700, cursor: creating ? 'not-allowed' : 'pointer' }}>
              {creating ? 'Creating…' : '+ Create'}
            </button>
          </form>
        </div>
      )}

      {loading && (
        <div style={{ textAlign: 'center', padding: '3rem',
          color: 'var(--text-secondary)' }}>Loading alerts…</div>
      )}

      {!loading && (
        <>
          {/* Active */}
          {active.length > 0 && (
            <div className="card" style={{ marginBottom: '1rem' }}>
              <h3 style={{ marginBottom: '1rem', fontSize: '0.88rem',
                color: '#00e68a', textTransform: 'uppercase',
                letterSpacing: '0.05em' }}>
                <FiBell size={13} style={{ marginRight: 6 }} />
                Active ({active.length})
              </h3>
              {active.map(a => <AlertRow key={a.id} alert={a}
                onDelete={deleteAlert} onToggle={toggleAlert} />)}
            </div>
          )}

          {/* Triggered */}
          {triggered.length > 0 && (
            <div className="card" style={{ marginBottom: '1rem' }}>
              <h3 style={{ marginBottom: '1rem', fontSize: '0.88rem',
                color: '#ffc107', textTransform: 'uppercase',
                letterSpacing: '0.05em' }}>
                ✓ Triggered ({triggered.length})
              </h3>
              {triggered.map(a => <AlertRow key={a.id} alert={a}
                onDelete={deleteAlert} onToggle={toggleAlert} />)}
            </div>
          )}

          {/* Inactive */}
          {inactive.length > 0 && (
            <div className="card">
              <h3 style={{ marginBottom: '1rem', fontSize: '0.88rem',
                color: 'var(--text-tertiary)', textTransform: 'uppercase',
                letterSpacing: '0.05em' }}>
                Paused ({inactive.length})
              </h3>
              {inactive.map(a => <AlertRow key={a.id} alert={a}
                onDelete={deleteAlert} onToggle={toggleAlert} />)}
            </div>
          )}

          {alerts.length === 0 && !error && (
            <div style={{ textAlign: 'center', padding: '4rem',
              color: 'var(--text-secondary)' }}>
              <FiBell size={40} color="var(--text-tertiary)" />
              <p style={{ marginTop: '1rem' }}>No alerts yet. Create one above.</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function AlertRow({ alert, onDelete, onToggle }) {
  const color = conditionColor[alert.condition] || '#8b95a8';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem',
      padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,0.04)',
      flexWrap: 'wrap' }}>
      <span style={{ fontWeight: 700, width: 56, color: 'var(--text-primary)',
        fontSize: '0.88rem' }}>{alert.symbol}</span>
      <span style={{ padding: '2px 8px', borderRadius: 5, fontSize: '0.75rem',
        fontWeight: 600, background: color + '22', color }}>
        {alert.condition}
      </span>
      <span style={{ fontWeight: 600, color: 'var(--text-primary)',
        fontSize: '0.9rem', minWidth: 80 }}>
        ${Number(alert.threshold_value).toLocaleString('en-US', { minimumFractionDigits: 2 })}
      </span>
      {alert.note && (
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.78rem',
          flex: 1 }}>{alert.note}</span>
      )}
      {alert.is_triggered && (
        <span style={{ fontSize: '0.75rem', color: '#ffc107' }}>
          ✓ triggered @ {alert.triggered_price ? `$${Number(alert.triggered_price).toFixed(2)}` : '—'}
        </span>
      )}
      <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem' }}>
        <button onClick={() => onToggle(alert)} title={alert.is_active ? 'Pause' : 'Resume'}
          style={{ background: 'none', border: 'none', cursor: 'pointer',
            color: alert.is_active ? '#00e68a' : 'var(--text-tertiary)' }}>
          {alert.is_active ? <FiToggleRight size={20} /> : <FiToggleLeft size={20} />}
        </button>
        <button onClick={() => onDelete(alert.id)} title="Delete"
          style={{ background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--text-tertiary)' }}>
          <FiTrash2 size={15} />
        </button>
      </div>
    </div>
  );
}

const conditionColor = { above: '#00e68a', below: '#ff4757', crosses: '#ffc107' };
