import React, { useState, useEffect, useCallback } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  PointElement, LineElement, Tooltip, Legend, Filler
} from 'chart.js';
import api from '../services/api';
import {
  FiTrendingUp, FiTrendingDown, FiMinus,
  FiRefreshCw, FiCpu, FiActivity, FiBarChart2
} from 'react-icons/fi';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler);

// ── Helpers ───────────────────────────────────────────────────────────────

const fmt = (v, d = 2) => v != null ? Number(v).toFixed(d) : '—';
const fmtPrice = v =>
  v != null ? '$' + Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—';

const SignalBadge = ({ type }) => {
  const map = {
    buy:  { bg: 'rgba(0,230,138,0.15)', color: '#00e68a', icon: '▲', label: 'BUY'  },
    sell: { bg: 'rgba(255,71,87,0.15)',  color: '#ff4757', icon: '▼', label: 'SELL' },
    hold: { bg: 'rgba(255,193,7,0.15)',  color: '#ffc107', icon: '◼', label: 'HOLD' },
  };
  const s = map[type?.toLowerCase()] || map.hold;
  return (
    <span style={{ padding: '4px 12px', borderRadius: 6, fontSize: '0.82rem',
      fontWeight: 700, background: s.bg, color: s.color }}>
      {s.icon} {s.label}
    </span>
  );
};

const StatCell = ({ label, value, color }) => (
  <div style={{ textAlign: 'center', padding: '0.75rem',
    border: '1px solid rgba(255,255,255,0.06)', borderRadius: 8 }}>
    <div style={{ color: 'var(--text-secondary)', fontSize: '0.72rem',
      textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>{label}</div>
    <div style={{ fontWeight: 700, fontSize: '1rem', color: color || 'var(--text-primary)' }}>{value}</div>
  </div>
);

const Card = ({ title, icon: Icon, children, accent = '#00d4ff' }) => (
  <div className="card" style={{ marginBottom: 0 }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: '1rem',
      paddingBottom: '0.75rem', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
      {Icon && <Icon size={15} color={accent} />}
      <h3 style={{ margin: 0, fontSize: '0.92rem', fontWeight: 600 }}>{title}</h3>
    </div>
    {children}
  </div>
);

// ── Forecast chart ────────────────────────────────────────────────────────

const ForecastChart = ({ forecast }) => {
  if (!forecast?.predictions?.length) return null;

  const labels  = forecast.dates || forecast.predictions.map((_, i) => `Day ${i + 1}`);
  const values  = forecast.predictions;
  const confs   = forecast.confidences || values.map(() => 0.7);

  const data = {
    labels,
    datasets: [
      {
        label:           'Predicted Price',
        data:            values,
        borderColor:     '#00d4ff',
        backgroundColor: 'rgba(0,212,255,0.08)',
        borderWidth:     2.5,
        pointRadius:     4,
        pointBackgroundColor: '#00d4ff',
        fill:  true,
        tension: 0.35,
      },
      {
        label:           'Confidence',
        data:            confs.map(c => c * Math.max(...values)),
        borderColor:     'rgba(255,193,7,0.4)',
        backgroundColor: 'transparent',
        borderWidth:     1,
        borderDash:      [4, 4],
        pointRadius:     0,
        fill:  false,
        tension: 0.35,
        yAxisID: 'y2',
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: true, labels: { color: '#8b95a8', boxWidth: 12 } },
      tooltip: {
        backgroundColor: 'rgba(10,14,26,0.95)',
        titleColor: '#fff',
        bodyColor:  '#00d4ff',
        callbacks: {
          label: ctx => {
            if (ctx.datasetIndex === 0) return `Price: ${fmtPrice(ctx.parsed.y)}`;
            return `Conf: ${fmt(confs[ctx.dataIndex] * 100, 0)}%`;
          },
        },
      },
    },
    scales: {
      x:  { ticks: { color: '#5a6478' }, grid: { color: 'rgba(255,255,255,0.04)' } },
      y:  { ticks: { color: '#5a6478', callback: v => `$${v.toLocaleString()}` },
            grid: { color: 'rgba(255,255,255,0.04)' } },
      y2: { display: false },
    },
  };

  return (
    <div style={{ height: 280 }}>
      <Line data={data} options={options} />
    </div>
  );
};

// ── Main page ─────────────────────────────────────────────────────────────

const SYMBOLS = ['GOLD', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'AMZN'];

export default function Predictions() {
  const [symbol,    setSymbol]    = useState('GOLD');
  const [forecast,  setForecast]  = useState(null);
  const [signal,    setSignal]    = useState(null);
  const [backtest,  setBacktest]  = useState(null);
  const [perf,      setPerf]      = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [training,  setTraining]  = useState(false);
  const [btLoading, setBtLoading] = useState(false);
  const [error,     setError]     = useState(null);

  const fetchAll = useCallback(async (sym) => {
    setLoading(true);
    setError(null);
    setForecast(null);
    setSignal(null);
    setPerf(null);

    try {
      // Signal always works (no model required)
      const sigRes = await api.get(`/predictions/${sym}/trading-signal`);
      setSignal(sigRes.data);
    } catch (e) {
      console.error('Signal error', e);
    }

    try {
      const statusRes = await api.get('/predictions/models/status');
      setModelInfo(statusRes.data.models);
    } catch (e) { /* ignore */ }

    try {
      if (modelInfo?.[sym]) {
        const [fRes, pRes] = await Promise.all([
          api.get(`/predictions/${sym}/predict?days=7`),
          api.get(`/predictions/${sym}/model-performance`),
        ]);
        setForecast(fRes.data);
        setPerf(pRes.data);
      }
    } catch (e) {
      console.error('Forecast error', e);
    }

    setLoading(false);
  }, [modelInfo]);

  // Fetch signal & model status on mount / symbol change
  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const statusRes = await api.get('/predictions/models/status');
        const models    = statusRes.data.models;
        setModelInfo(models);

        const sigRes = await api.get(`/predictions/${symbol}/trading-signal`);
        setSignal(sigRes.data);

        if (models?.[symbol]) {
          const [fRes, pRes] = await Promise.all([
            api.get(`/predictions/${symbol}/predict?days=7`),
            api.get(`/predictions/${symbol}/model-performance`),
          ]);
          setForecast(fRes.data);
          setPerf(pRes.data);
        } else {
          setForecast(null);
          setPerf(null);
        }
      } catch (e) {
        setError('Failed to load prediction data.');
        console.error(e);
      } finally {
        setLoading(false);
      }
    })();
  }, [symbol]);

  const trainModel = async () => {
    setTraining(true);
    setError(null);
    try {
      await api.post(`/predictions/${symbol}/train-model?epochs=100`);
      // Refresh after training
      const [fRes, pRes, statusRes] = await Promise.all([
        api.get(`/predictions/${symbol}/predict?days=7`),
        api.get(`/predictions/${symbol}/model-performance`),
        api.get('/predictions/models/status'),
      ]);
      setForecast(fRes.data);
      setPerf(pRes.data);
      setModelInfo(statusRes.data.models);
    } catch (e) {
      setError('Training failed. Make sure there is enough price history in the DB (60+ rows).');
    } finally {
      setTraining(false);
    }
  };

  const runBacktest = async () => {
    setBtLoading(true);
    setBacktest(null);
    try {
      const res = await api.post(
        `/predictions/${symbol}/backtest?initial_capital=10000&days=90`
      );
      setBacktest(res.data.backtest_results);
    } catch (e) {
      setError('Backtest failed.');
    } finally {
      setBtLoading(false);
    }
  };

  const hasModel = modelInfo?.[symbol] === true;

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between',
        alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1>ML Predictions</h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: 2 }}>
            Ensemble model · Trading signals · Backtesting
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
                  color:      symbol === s ? 'var(--bg-primary)' : 'var(--text-secondary)' }}>
                {s}
              </button>
            ))}
          </div>
          <button onClick={trainModel} disabled={training}
            style={{ display: 'flex', alignItems: 'center', gap: 6,
              border: 'none', borderRadius: 'var(--radius-md)', padding: '7px 14px',
              background: training ? 'rgba(0,212,255,0.1)' : 'var(--cyan)',
              color: training ? 'var(--cyan)' : 'var(--bg-primary)',
              fontWeight: 700, cursor: training ? 'not-allowed' : 'pointer' }}>
            <FiCpu size={13} /> {training ? 'Training…' : `Train ${symbol}`}
          </button>
        </div>
      </div>

      {error && (
        <div className="card" style={{ color: '#ff4757', marginBottom: '1rem', fontSize: '0.88rem' }}>
          {error}
        </div>
      )}

      {/* Model status banner */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
        {SYMBOLS.map(s => (
          <span key={s} style={{ padding: '3px 10px', borderRadius: 6, fontSize: '0.75rem',
            fontWeight: 600,
            background: modelInfo?.[s] ? 'rgba(0,230,138,0.12)' : 'rgba(255,255,255,0.05)',
            color:      modelInfo?.[s] ? '#00e68a' : '#5a6478' }}>
            {modelInfo?.[s] ? '✓' : '○'} {s}
          </span>
        ))}
      </div>

      {loading && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
          <h3 className="gradient-text">Loading {symbol}…</h3>
        </div>
      )}

      {!loading && (
        <>
          {/* Top row — signal + model metrics */}
          <div style={{ display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '1rem', marginBottom: '1.25rem' }}>

            {/* Trading signal */}
            <Card title="Trading Signal" icon={FiActivity} accent="#00d4ff">
              {signal ? (
                <>
                  <div style={{ marginBottom: 8 }}>
                    <SignalBadge type={signal.trading_signal?.signal_type} />
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)',
                    display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <span>Strength: <b style={{ color: 'var(--text-primary)' }}>
                      {fmt(signal.trading_signal?.strength)}</b></span>
                    <span>Confidence: <b style={{ color: 'var(--text-primary)' }}>
                      {fmt((signal.trading_signal?.confidence || 0) * 100, 0)}%</b></span>
                    <span>ML Score: <b style={{ color: 'var(--text-primary)' }}>
                      {fmt(signal.trading_signal?.ml_score)}</b></span>
                  </div>
                  {(signal.trading_signal?.reasons || []).map((r, i) => (
                    <div key={i} style={{ fontSize: '0.75rem', color: 'var(--text-secondary)',
                      marginTop: 4 }}>→ {r}</div>
                  ))}
                </>
              ) : <p style={{ color: 'var(--text-secondary)' }}>Loading…</p>}
            </Card>

            {/* Model performance */}
            <Card title="Model Metrics" icon={FiBarChart2} accent="#a855f7">
              {hasModel && perf ? (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                  <StatCell label="R²"    value={fmt(perf.model_metrics?.metrics?.r2, 3)} />
                  <StatCell label="RMSE"  value={fmt(perf.model_metrics?.metrics?.rmse, 4)} />
                  <StatCell label="MAE"   value={fmt(perf.model_metrics?.metrics?.mae, 4)} />
                  <StatCell label="Dir. Acc."
                    value={`${fmt(perf.model_metrics?.metrics?.directional_accuracy, 1)}%`}
                    color={perf.model_metrics?.metrics?.directional_accuracy > 55 ? '#00e68a' : '#ffc107'} />
                </div>
              ) : (
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                  {hasModel ? 'Loading metrics…' : `No model yet. Click "Train ${symbol}".`}
                </p>
              )}
            </Card>

            {/* Backtest button & summary */}
            <Card title="Backtest (90 days)" icon={FiTrendingUp} accent="#ffc107">
              <button onClick={runBacktest} disabled={btLoading}
                style={{ border: 'none', borderRadius: 6, padding: '7px 16px',
                  background: btLoading ? 'rgba(255,193,7,0.1)' : 'rgba(255,193,7,0.15)',
                  color: '#ffc107', fontWeight: 700, cursor: btLoading ? 'wait' : 'pointer',
                  marginBottom: 10, width: '100%' }}>
                {btLoading ? 'Running…' : '▶ Run Backtest'}
              </button>
              {backtest && !backtest.error && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                  <StatCell label="Return"
                    value={`${fmt(backtest.total_return_percent)}%`}
                    color={backtest.total_return_percent >= 0 ? '#00e68a' : '#ff4757'} />
                  <StatCell label="Win Rate" value={`${fmt(backtest.win_rate)}%`} />
                  <StatCell label="Trades"   value={backtest.total_trades} />
                  <StatCell label="Sharpe"   value={fmt(backtest.sharpe_ratio)} />
                  <StatCell label="Max DD"
                    value={`${fmt(backtest.max_drawdown)}%`} color="#ff4757" />
                  <StatCell label="Profit F" value={fmt(backtest.profit_factor)} />
                </div>
              )}
              {backtest?.error && (
                <p style={{ color: '#ff4757', fontSize: '0.82rem' }}>{backtest.note || backtest.error}</p>
              )}
            </Card>
          </div>

          {/* Forecast chart */}
          {hasModel ? (
            <div className="card" style={{ marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between',
                alignItems: 'center', marginBottom: '1rem' }}>
                <h2 style={{ margin: 0, fontSize: '1.05rem' }}>
                  7-Day Price Forecast — {symbol}
                </h2>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Ensemble model (Ridge + GBR)
                </span>
              </div>

              {forecast ? (
                <>
                  <ForecastChart forecast={forecast} />
                  {/* Day-by-day table */}
                  <div style={{ display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
                    gap: '0.5rem', marginTop: '1.25rem' }}>
                    {forecast.predictions.map((p, i) => (
                      <div key={i} style={{ textAlign: 'center', padding: '0.6rem',
                        background: 'var(--bg-tertiary)', borderRadius: 8 }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)',
                          marginBottom: 3 }}>
                          {forecast.dates?.[i] || `Day ${i + 1}`}
                        </div>
                        <div style={{ fontWeight: 700, color: 'var(--cyan)', fontSize: '0.9rem' }}>
                          {fmtPrice(p)}
                        </div>
                        <div style={{ fontSize: '0.68rem', color: '#ffc107', marginTop: 2 }}>
                          {fmt((forecast.confidences?.[i] || 0.7) * 100, 0)}% conf
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p style={{ color: 'var(--text-secondary)' }}>Loading forecast…</p>
              )}
            </div>
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
              <FiCpu size={40} color="var(--text-tertiary)" />
              <h3 style={{ margin: '1rem 0 0.5rem', color: 'var(--text-secondary)' }}>
                No model trained for {symbol}
              </h3>
              <p style={{ color: 'var(--text-tertiary)', marginBottom: '1.5rem', fontSize: '0.88rem' }}>
                Click "Train {symbol}" above to train an ensemble model.<br />
                Requires 60+ rows of price history in the database.
              </p>
              <button onClick={trainModel} disabled={training}
                style={{ border: 'none', borderRadius: 8, padding: '10px 24px',
                  background: 'var(--cyan)', color: 'var(--bg-primary)',
                  fontWeight: 700, cursor: training ? 'not-allowed' : 'pointer',
                  fontSize: '0.9rem' }}>
                <FiCpu size={14} style={{ marginRight: 6 }} />
                {training ? 'Training…' : `Train ${symbol} Model`}
              </button>
            </div>
          )}

          {/* Recent trades from last backtest */}
          {backtest?.trades?.length > 0 && (
            <div className="card">
              <h3 style={{ marginBottom: '1rem', fontSize: '0.95rem' }}>
                Recent Backtest Trades
              </h3>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                  <thead>
                    <tr style={{ color: 'var(--text-secondary)', textAlign: 'left' }}>
                      {['#', 'Entry', 'Exit', 'PnL', 'PnL %'].map(h => (
                        <th key={h} style={{ padding: '6px 10px',
                          borderBottom: '1px solid rgba(255,255,255,0.06)' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {backtest.trades.slice(-10).map((t, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                        <td style={{ padding: '5px 10px', color: 'var(--text-secondary)' }}>{i + 1}</td>
                        <td style={{ padding: '5px 10px' }}>{fmtPrice(t.entry)}</td>
                        <td style={{ padding: '5px 10px' }}>{fmtPrice(t.exit)}</td>
                        <td style={{ padding: '5px 10px',
                          color: t.pnl >= 0 ? '#00e68a' : '#ff4757' }}>
                          {t.pnl >= 0 ? '+' : ''}{fmt(t.pnl, 4)}
                        </td>
                        <td style={{ padding: '5px 10px',
                          color: t.pnl_pct >= 0 ? '#00e68a' : '#ff4757' }}>
                          {t.pnl_pct >= 0 ? '+' : ''}{fmt(t.pnl_pct)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
