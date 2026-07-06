import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import { FiUserPlus, FiUser, FiMail, FiLock } from 'react-icons/fi';

export default function Register() {
  const [form,    setForm]    = useState({ username: '', email: '', password: '', full_name: '' });
  const [error,   setError]   = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.post('/auth/register', form);
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('user',  JSON.stringify(res.data.user));
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const field = (name, label, type = 'text', Icon, autocomplete) => (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)',
        textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</span>
      <div style={{ position: 'relative' }}>
        <Icon style={{ position: 'absolute', left: 12, top: '50%',
          transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
        <input type={type} autoComplete={autocomplete} required={name !== 'full_name'}
          value={form[name]}
          onChange={e => setForm(f => ({ ...f, [name]: e.target.value }))}
          style={{ width: '100%', padding: '10px 12px 10px 36px',
            background: 'var(--bg-tertiary)', border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 8, color: 'var(--text-primary)', fontSize: '0.9rem',
            outline: 'none', boxSizing: 'border-box' }} />
      </div>
    </label>
  );

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center',
      justifyContent: 'center', background: 'var(--bg-primary)' }}>
      <div style={{ width: '100%', maxWidth: 420, padding: '2rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ fontSize: '2rem', fontWeight: 800,
            background: 'linear-gradient(135deg, var(--cyan), var(--emerald))',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            MarketPulse
          </div>
          <p style={{ color: 'var(--text-secondary)', marginTop: 6, fontSize: '0.9rem' }}>
            Create your account
          </p>
        </div>

        <form onSubmit={handleSubmit} className="card"
          style={{ gap: '1rem', display: 'flex', flexDirection: 'column' }}>
          {error && (
            <div style={{ padding: '10px 14px', borderRadius: 8,
              background: 'rgba(255,71,87,0.12)', color: '#ff4757',
              fontSize: '0.85rem' }}>{error}</div>
          )}

          {field('full_name', 'Full Name',  'text',     FiUser,    'name')}
          {field('username',  'Username',   'text',     FiUser,    'username')}
          {field('email',     'Email',      'email',    FiMail,    'email')}
          {field('password',  'Password',  'password', FiLock,    'new-password')}

          <p style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', margin: 0 }}>
            Password: 8+ chars, uppercase letter, number required.
          </p>

          <button type="submit" disabled={loading}
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center',
              gap: 8, padding: '11px', borderRadius: 8, border: 'none',
              background: loading ? 'rgba(0,230,138,0.3)' : 'var(--emerald, #00e68a)',
              color: 'var(--bg-primary)', fontWeight: 700, fontSize: '0.95rem',
              cursor: loading ? 'not-allowed' : 'pointer', marginTop: 4 }}>
            <FiUserPlus size={16} /> {loading ? 'Creating account…' : 'Create Account'}
          </button>

          <p style={{ textAlign: 'center', fontSize: '0.85rem',
            color: 'var(--text-secondary)', margin: 0 }}>
            Already have an account?{' '}
            <Link to="/login" style={{ color: 'var(--cyan)', textDecoration: 'none' }}>
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
