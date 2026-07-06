import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import { FiLogIn, FiUser, FiLock } from 'react-icons/fi';

export default function Login() {
  const [form,    setForm]    = useState({ username: '', password: '' });
  const [error,   setError]   = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.post('/auth/login', form);
      localStorage.setItem('token',    res.data.access_token);
      localStorage.setItem('user',     JSON.stringify(res.data.user));
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center',
      justifyContent: 'center', background: 'var(--bg-primary)' }}>
      <div style={{ width: '100%', maxWidth: 400, padding: '2rem' }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ fontSize: '2rem', fontWeight: 800,
            background: 'linear-gradient(135deg, var(--cyan), var(--emerald))',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            MarketPulse
          </div>
          <p style={{ color: 'var(--text-secondary)', marginTop: 6, fontSize: '0.9rem' }}>
            Sign in to your account
          </p>
        </div>

        <form onSubmit={handleSubmit} className="card" style={{ gap: '1rem', display: 'flex', flexDirection: 'column' }}>
          {error && (
            <div style={{ padding: '10px 14px', borderRadius: 8,
              background: 'rgba(255,71,87,0.12)', color: '#ff4757',
              fontSize: '0.85rem' }}>{error}</div>
          )}

          <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)',
              textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Username / Email
            </span>
            <div style={{ position: 'relative' }}>
              <FiUser style={{ position: 'absolute', left: 12, top: '50%',
                transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
              <input
                type="text" autoComplete="username" required
                value={form.username}
                onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                style={{ width: '100%', padding: '10px 12px 10px 36px',
                  background: 'var(--bg-tertiary)', border: '1px solid rgba(255,255,255,0.08)',
                  borderRadius: 8, color: 'var(--text-primary)', fontSize: '0.9rem',
                  outline: 'none', boxSizing: 'border-box' }}
              />
            </div>
          </label>

          <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)',
              textTransform: 'uppercase', letterSpacing: '0.05em' }}>Password</span>
            <div style={{ position: 'relative' }}>
              <FiLock style={{ position: 'absolute', left: 12, top: '50%',
                transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
              <input
                type="password" autoComplete="current-password" required
                value={form.password}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                style={{ width: '100%', padding: '10px 12px 10px 36px',
                  background: 'var(--bg-tertiary)', border: '1px solid rgba(255,255,255,0.08)',
                  borderRadius: 8, color: 'var(--text-primary)', fontSize: '0.9rem',
                  outline: 'none', boxSizing: 'border-box' }}
              />
            </div>
          </label>

          <button type="submit" disabled={loading}
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center',
              gap: 8, padding: '11px', borderRadius: 8, border: 'none',
              background: loading ? 'rgba(0,212,255,0.3)' : 'var(--cyan)',
              color: 'var(--bg-primary)', fontWeight: 700, fontSize: '0.95rem',
              cursor: loading ? 'not-allowed' : 'pointer', marginTop: 4 }}>
            <FiLogIn size={16} /> {loading ? 'Signing in…' : 'Sign In'}
          </button>

          <p style={{ textAlign: 'center', fontSize: '0.85rem',
            color: 'var(--text-secondary)', margin: 0 }}>
            No account?{' '}
            <Link to="/register" style={{ color: 'var(--cyan)', textDecoration: 'none' }}>
              Create one
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
