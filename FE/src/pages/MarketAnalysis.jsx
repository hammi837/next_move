import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import {
  FiTrendingUp, FiTrendingDown, FiMinus,
  FiRefreshCw, FiActivity, FiBarChart2, FiLayers
} from 'react-icons/fi';

// ── Helpers ───────────────────────────────────────────────────────────────

const fmt = (v, dec = 2) =>
  v != null ? Number(v).toFixed(dec) : '—';

const fmtPrice = (v) =>
  v != null
    ? '$' + Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : '—';

const SignalBadge = ({ signal }) => {
  const map = {
    BUY:     { bg: 'rgba(0,230,138,0.15)', color: '#00e68a', label: '▲ BUY'  },
    SELL:    { bg: 'rgba(255,71,87,0.15)',  color: '#ff4757', label: '▼ SELL' },
    HOLD:    { bg: 'rgba(255,193,7,0.15)',  color: '#ffc107', label: '◼ HOLD' },
    bullish: { bg: 'rgba(0,230,138,0.15)', color: '#00e68a', label: '▲ BULLISH' },
    bearish: { bg: 'rgba(255,71,87,0.15)',  color: '#ff4757', label: '▼ BEARISH' },
    neutral: { bg: 'rgba(255,193,7,0.15)',  color: '#ffc107', label: '◼ NEUTRAL' },
    unknown: { bg: 'rgba(90,100,120,0.2)',  color: '#8b95a8', label: '— —' },
  };
  const s = map[signal] || map.unknown;
  return (
    <span style={{
      padding: '3px 10px', borderRadius: 6, fontSize: '0.78rem',
      fontWeight: 700, background: s.bg, color: s.color,
    }}>{s.label}</span>
  );
};

const StatRow = ({ label, value, color }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
    <span style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>{label}</span>
    <span style={{ fontWeight: 600, fontSize: '0.88rem', color: color || 'var(--text-primary)' }}>{value}</span>
  </div>
);

// ── Mini gauge bar (0-100) ────────────────────────────────────────────────
const Gauge = ({ value, min = 0, max = 100, low = 30, high = 70 }) => {
  const pct = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));
  const color = value < low ? '#00e68a' : value > high ? '#ff4757' : '#ffc107';
  return (
    <div style={{ marginTop: 6 }}>
      <div style={{ height: 6, background: 'rgba(255,255,255,0.08)', borderRadius: 3, position: 'relative' }}>
        {/* zones */}
        <div style={{ position: 'absolute', left: `${low}%`, width: `${high - low}%`, height: '100%',
          background: 'rgba(255,193,7,0.1)', borderRadius: 3 }} />
        {/* thumb */}
        <div style={{ position: 'absolute', left: `${pct}%`, top: -3, width: 12, height: 12,
          background: color, borderRadius: '50%', transform: 'translateX(-50%)',
          boxShadow: `0 0 8px ${color}` }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem',
        color: 'var(--text-tertiary)', marginTop: 3 }}>
        <span>Oversold</span><span>Neutral</span><span>Overbought</span>
      </div>
    </div>
  );
};

// ── Card wrapper ──────────────────────────────────────────────────────────
const Card = ({ title, icon: Icon, children, accent = '#00d4ff' }) => (
  <div className="card" style={{ marginBottom: 0 }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: '1rem',
      paddingBottom: '0.75rem', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
      {Icon && <Icon size={16} color={accent} />}
      <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600 }}>{title}</h3>
    </div>
    {children}
  </div>
);

// ── Pattern pill ──────────────────────────────────────────────────────────
const PatternPill = ({ pattern, signal }) => {
  const colors = { bullish: '#00e68a', bearish: '#ff4757', neutral: '#ffc107' };
  const color  = colors[signal] || '#8b95a8';
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '6px 10px', borderRadius: 6, background: 'rgba(255,255,255,0.04)',
      marginBottom: 4, border: `1px solid ${color}22` }}>
      <span style={{ textTransform: 'capitalize', fontSize: '0.82rem' }}>
        {pattern.replace(/_/g, ' ')}
      </span>
      <span style={{ fontSize: '0.75rem', fontWeight: 700, color }}>{signal}</span>
    </div>
  );
};

// ── Main page ─────────────────────────────────────────────────────────────
const SYMBOLS = ['GOLD', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'AMZN'];

export default function MarketAnalysis() {
  const [symbol,   setSymbol]   = useState('GOLD');
  const [data,     setData]     = useState(null);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState(null);
  const [tab,      setTab]      = useState('indicators'); // indicators | patterns | trend

  const fetchData = useCallback(async (sym) => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/indicators/${sym}/summary?days=90`);
      setData(res.data);
    } catch (e) {
      setError('Failed to load analysis data. Make sure the backend is running.');
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(symbol); }, [symbol, fetchData]);

  const ind  = data?.indicators;
  const tr   = data?.trend;
  const ta   = data?.trend_analysis;
  const sr   = data?.support_resistance;
  const pats = data?.patterns || [];

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1>Market Analysis</h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: 2 }}>
            Technical indicators · Pattern recognition · Trend analysis
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
          {/* Symbol selector */}
          <div style={{ display: 'flex', gap: '0.25rem', padding: 4,
            background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)' }}>
            {SYMBOLS.map(s => (
              <button key={s} onClick={() => setSymbol(s)}
                style={{ border: 'none', borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                  fontWeight: 600, padding: '4px 10px', fontSize: '0.8rem',
                  background: symbol === s ? 'var(--cyan)' : 'transparent',
                  color: symbol === s ? 'var(--bg-primary)' : 'var(--text-secondary)' }}>
                {s}
              </button>
            ))}
          </div>
          <button onClick={() => fetchData(symbol)} className="btn"
            style={{ background: 'var(--glass-bg)', color: 'var(--text-primary)' }}>
            <FiRefreshCw /> Refresh
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="card" style={{ color: '#ff4757', marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
          <h3 className="gradient-text">Analysing {symbol}…</h3>
        </div>
      )}

      {!loading && data && (
        <>
          {/* Top summary strip */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem', marginBottom: '1.5rem' }}>

            {/* Current price */}
            <div className="card" style={{ marginBottom: 0 }}>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', textTransform: 'uppercase',
                letterSpacing: '0.05em', marginBottom: 4 }}>Current Price</p>
              <h2 className="gradient-text" style={{ margin: 0, fontSize: '1.6rem' }}>
                {fmtPrice(ind?.current_price)}
              </h2>
            </div>

            {/* Overall signal */}
            <div className="card" style={{ marginBottom: 0 }}>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', textTransform: 'uppercase',
                letterSpacing: '0.05em', marginBottom: 8 }}>Signal</p>
              <SignalBadge signal={ind?.signals?.overall || 'HOLD'} />
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: 6 }}>
                Score: {fmt(ind?.signals?.score)}
              </p>
            </div>

            {/* Trend */}
            <div className="card" style={{ marginBottom: 0 }}>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', textTransform: 'uppercase',
                letterSpacing: '0.05em', marginBottom: 8 }}>Trend</p>
              <SignalBadge signal={tr?.direction || 'unknown'} />
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: 6 }}>
                Strength: {fmt(tr?.strength)}%
              </p>
            </div>

            {/* Momentum */}
            <div className="card" style={{ marginBottom: 0 }}>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', textTransform: 'uppercase',
                letterSpacing: '0.05em', marginBottom: 4 }}>Momentum (10d)</p>
              <h2 style={{ margin: 0, fontSize: '1.4rem',
                color: (ta?.momentum?.current || 0) >= 0 ? '#00e68a' : '#ff4757' }}>
                {(ta?.momentum?.current || 0) >= 0 ? '+' : ''}{fmt(ta?.momentum?.current)}%
              </h2>
            </div>
          </div>

          {/* Tab bar */}
          <div style={{ display: 'flex', gap: '0.25rem', padding: 4, background: 'var(--bg-tertiary)',
            borderRadius: 'var(--radius-md)', marginBottom: '1.25rem', width: 'fit-content' }}>
            {[
              { id: 'indicators', label: 'Indicators',    Icon: FiActivity },
              { id: 'patterns',   label: 'Patterns',      Icon: FiLayers   },
              { id: 'trend',      label: 'Trend',         Icon: FiBarChart2 },
            ].map(t => (
              <button key={t.id} onClick={() => setTab(t.id)}
                style={{ display: 'flex', alignItems: 'center', gap: 6, border: 'none',
                  borderRadius: 'var(--radius-sm)', cursor: 'pointer', padding: '6px 14px',
                  fontWeight: 600, fontSize: '0.82rem',
                  background: tab === t.id ? 'var(--cyan)' : 'transparent',
                  color: tab === t.id ? 'var(--bg-primary)' : 'var(--text-secondary)' }}>
                <t.Icon size={13} /> {t.label}
              </button>
            ))}
          </div>

          {/* ── INDICATORS TAB ── */}
          {tab === 'indicators' && ind && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>

              {/* RSI */}
              <Card title="RSI (14)" icon={FiActivity} accent="#00e68a">
                <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: 4,
                  color: ind.rsi_14 < 30 ? '#00e68a' : ind.rsi_14 > 70 ? '#ff4757' : 'var(--text-primary)' }}>
                  {fmt(ind.rsi_14)}
                </div>
                <Gauge value={ind.rsi_14 || 50} low={30} high={70} />
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.78rem', marginTop: 8 }}>
                  {ind.rsi_14 < 30 ? '📉 Oversold — potential buy zone'
                    : ind.rsi_14 > 70 ? '📈 Overbought — potential sell zone'
                    : '↔ Neutral range (30–70)'}
                </p>
              </Card>

              {/* MACD */}
              <Card title="MACD (12/26/9)" icon={FiActivity} accent="#00d4ff">
                <StatRow label="MACD Line"   value={fmt(ind.macd?.line,      4)} />
                <StatRow label="Signal Line" value={fmt(ind.macd?.signal,    4)} />
                <StatRow label="Histogram"   value={fmt(ind.macd?.histogram, 4)}
                  color={(ind.macd?.histogram || 0) >= 0 ? '#00e68a' : '#ff4757'} />
                <div style={{ marginTop: 10 }}>
                  <SignalBadge signal={(ind.macd?.line > ind.macd?.signal) ? 'bullish' : 'bearish'} />
                </div>
              </Card>

              {/* Bollinger Bands */}
              <Card title="Bollinger Bands (20)" icon={FiBarChart2} accent="#a855f7">
                <StatRow label="Upper Band"  value={fmtPrice(ind.bollinger_bands?.upper)} />
                <StatRow label="Middle Band" value={fmtPrice(ind.bollinger_bands?.middle)} />
                <StatRow label="Lower Band"  value={fmtPrice(ind.bollinger_bands?.lower)} />
                <StatRow label="Price"       value={fmtPrice(ind.current_price)} />
                {ind.bollinger_bands?.upper && ind.bollinger_bands?.lower && (
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.78rem', marginTop: 8 }}>
                    Band width: {fmtPrice(ind.bollinger_bands.upper - ind.bollinger_bands.lower)}
                  </p>
                )}
              </Card>

              {/* Moving Averages */}
              <Card title="Moving Averages" icon={FiTrendingUp} accent="#ffc107">
                <StatRow label="SMA 20"  value={fmtPrice(ind.sma_20)} />
                <StatRow label="SMA 50"  value={fmtPrice(ind.sma_50)} />
                <StatRow label="SMA 200" value={fmtPrice(ind.sma_200) || '(need more data)'} />
                <StatRow label="EMA 12"  value={fmtPrice(ind.ema_12)} />
                <StatRow label="EMA 26"  value={fmtPrice(ind.ema_26)} />
              </Card>

              {/* Stochastic */}
              <Card title="Stochastic (14)" icon={FiActivity} accent="#ff4757">
                <div style={{ fontSize: '1.6rem', fontWeight: 700, marginBottom: 4 }}>
                  K: {fmt(ind.stochastic?.k)}
                </div>
                <Gauge value={ind.stochastic?.k || 50} low={20} high={80} />
                <StatRow label="D Line" value={fmt(ind.stochastic?.d)} />
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.78rem', marginTop: 8 }}>
                  {(ind.stochastic?.k || 50) < 20 ? 'Oversold'
                    : (ind.stochastic?.k || 50) > 80 ? 'Overbought' : 'Neutral'}
                </p>
              </Card>

              {/* Volatility */}
              <Card title="Volatility & Trend" icon={FiBarChart2} accent="#00e68a">
                <StatRow label="ATR (14)"  value={fmt(ind.atr_14, 2)} />
                <StatRow label="ADX (14)"  value={ind.adx_14 ? fmt(ind.adx_14) : '(need more data)'}
                  color={ind.adx_14 > 25 ? '#00e68a' : '#ffc107'} />
                <StatRow label="ROC (12)"  value={ind.roc_12 ? `${fmt(ind.roc_12)}%` : '—'}
                  color={(ind.roc_12 || 0) >= 0 ? '#00e68a' : '#ff4757'} />
                {ind.adx_14 && (
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.78rem', marginTop: 8 }}>
                    {ind.adx_14 > 25 ? '💪 Strong trend detected' : '↔ Weak / no trend'}
                  </p>
                )}
              </Card>

              {/* Buy/Sell signals */}
              {ind.signals && (
                <Card title="Active Signals" icon={FiLayers} accent="#00e68a">
                  {ind.signals.buy_signals?.length > 0 && (
                    <>
                      <p style={{ color: '#00e68a', fontSize: '0.78rem', fontWeight: 600,
                        marginBottom: 4, textTransform: 'uppercase' }}>Buy Signals</p>
                      {ind.signals.buy_signals.map(s => (
                        <div key={s} style={{ fontSize: '0.82rem', padding: '3px 0',
                          color: '#00e68a' }}>✓ {s.replace(/_/g, ' ')}</div>
                      ))}
                    </>
                  )}
                  {ind.signals.sell_signals?.length > 0 && (
                    <>
                      <p style={{ color: '#ff4757', fontSize: '0.78rem', fontWeight: 600,
                        marginTop: 8, marginBottom: 4, textTransform: 'uppercase' }}>Sell Signals</p>
                      {ind.signals.sell_signals.map(s => (
                        <div key={s} style={{ fontSize: '0.82rem', padding: '3px 0',
                          color: '#ff4757' }}>✗ {s.replace(/_/g, ' ')}</div>
                      ))}
                    </>
                  )}
                  {ind.signals.neutral?.length > 0 && (
                    <>
                      <p style={{ color: '#ffc107', fontSize: '0.78rem', fontWeight: 600,
                        marginTop: 8, marginBottom: 4, textTransform: 'uppercase' }}>Context</p>
                      {ind.signals.neutral.map(s => (
                        <div key={s} style={{ fontSize: '0.82rem', padding: '3px 0',
                          color: '#ffc107' }}>→ {s.replace(/_/g, ' ')}</div>
                      ))}
                    </>
                  )}
                </Card>
              )}
            </div>
          )}

          {/* ── PATTERNS TAB ── */}
          {tab === 'patterns' && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>

              {/* Candlestick patterns */}
              <Card title="Recent Candlestick Patterns" icon={FiLayers} accent="#a855f7">
                {pats.length === 0 ? (
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                    No strong patterns detected in recent candles.
                  </p>
                ) : pats.map((p, i) => (
                  <PatternPill key={i} pattern={p.pattern} signal={p.signal} />
                ))}
              </Card>

              {/* Support / Resistance */}
              <Card title="Support & Resistance Levels" icon={FiBarChart2} accent="#00d4ff">
                <p style={{ color: '#ff4757', fontSize: '0.75rem', fontWeight: 700,
                  textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
                  Resistance
                </p>
                {(sr?.resistance || []).length === 0
                  ? <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>—</p>
                  : (sr.resistance || []).map((lvl, i) => (
                      <StatRow key={i} label={`R${i + 1}`} value={fmtPrice(lvl)}
                        color="#ff4757" />
                    ))}
                <p style={{ color: '#00e68a', fontSize: '0.75rem', fontWeight: 700,
                  textTransform: 'uppercase', letterSpacing: '0.05em', margin: '12px 0 6px' }}>
                  Support
                </p>
                {(sr?.support || []).length === 0
                  ? <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>—</p>
                  : (sr.support || []).map((lvl, i) => (
                      <StatRow key={i} label={`S${i + 1}`} value={fmtPrice(lvl)}
                        color="#00e68a" />
                    ))}
              </Card>
            </div>
          )}

          {/* ── TREND TAB ── */}
          {tab === 'trend' && ta && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>

              <Card title="Trend Direction" icon={FiTrendingUp} accent="#00d4ff">
                <div style={{ marginBottom: 8 }}>
                  <SignalBadge signal={ta.trend?.direction || 'neutral'} />
                </div>
                <StatRow label="Strength"   value={ta.trend?.strength} />
                <StatRow label="Short MA"   value={fmtPrice(ta.trend?.short_ma)} />
                <StatRow label="Long MA"    value={fmtPrice(ta.trend?.long_ma)} />
                <StatRow label="Data pts"   value={ta.data_points} />
              </Card>

              <Card title="Price Action" icon={FiBarChart2} accent="#ffc107">
                <StatRow label="Current"    value={fmtPrice(ta.price_action?.current)} />
                <StatRow label="Period High" value={fmtPrice(ta.price_action?.high)} />
                <StatRow label="Period Low"  value={fmtPrice(ta.price_action?.low)} />
                <StatRow label="Range"       value={fmtPrice(ta.stats?.range)} />
                <StatRow label="Avg Price"   value={fmtPrice(ta.stats?.mean)} />
              </Card>

              <Card title="Volatility Analysis" icon={FiActivity} accent="#a855f7">
                <StatRow label="Recent Vol"  value={`${fmt(ta.volatility?.recent, 4)}%`} />
                <StatRow label="Early Vol"   value={`${fmt(ta.volatility?.early, 4)}%`} />
                <StatRow label="Trend"       value={ta.volatility?.trend}
                  color={ta.volatility?.trend === 'increasing' ? '#ff4757' : '#00e68a'} />
              </Card>

              <Card title="Momentum" icon={FiTrendingUp} accent="#00e68a">
                <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: 4,
                  color: (ta.momentum?.current || 0) >= 0 ? '#00e68a' : '#ff4757' }}>
                  {(ta.momentum?.current || 0) >= 0 ? '+' : ''}{fmt(ta.momentum?.current)}%
                </div>
                <StatRow label="Interpretation" value={ta.momentum?.interpretation}
                  color={ta.momentum?.interpretation === 'bullish' ? '#00e68a' : '#ff4757'} />
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.78rem', marginTop: 8 }}>
                  10-period rate of change
                </p>
              </Card>

              {/* Recent reversals */}
              {(ta.price_action?.reversals || []).length > 0 && (
                <Card title="Recent Reversals" icon={FiLayers} accent="#ff4757">
                  {ta.price_action.reversals.map((r, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between',
                      padding: '5px 0', borderBottom: '1px solid rgba(255,255,255,0.04)',
                      fontSize: '0.82rem' }}>
                      <span style={{ textTransform: 'capitalize', color: 'var(--text-secondary)' }}>
                        {r.type}
                      </span>
                      <span style={{ color: r.potential === 'bullish' ? '#00e68a' : '#ff4757', fontWeight: 600 }}>
                        {fmtPrice(r.price)} · {r.potential}
                      </span>
                    </div>
                  ))}
                </Card>
              )}

              {/* Significant breaks */}
              {(ta.price_action?.breaks || []).length > 0 && (
                <Card title="Significant Price Breaks" icon={FiActivity} accent="#ffc107">
                  {ta.price_action.breaks.map((b, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between',
                      padding: '5px 0', borderBottom: '1px solid rgba(255,255,255,0.04)',
                      fontSize: '0.82rem' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>{fmtPrice(b.price)}</span>
                      <span style={{ color: b.direction === 'up' ? '#00e68a' : '#ff4757', fontWeight: 600 }}>
                        {b.direction === 'up' ? '▲' : '▼'} {fmt(b.change_percent)}%
                      </span>
                    </div>
                  ))}
                </Card>
              )}
            </div>
          )}
        </>
      )}

      {!loading && !data && !error && (
        <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-secondary)' }}>
          Select a symbol to begin analysis.
        </div>
      )}
    </div>
  );
}
