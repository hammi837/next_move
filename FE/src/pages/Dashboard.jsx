import React, { useState, useEffect, useMemo } from 'react';
import { dashboardService, goldService, stocksService } from '../services/api';
import PriceChart from '../components/charts/PriceChart';
import { FiRefreshCw, FiTrendingUp, FiTrendingDown, FiMinus } from 'react-icons/fi';

const MarketCard = ({ data, onClick }) => {
  if (!data) return null;

  const { symbol, current_price, change_percent_24h } = data;
  
  const formattedPrice = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(current_price || 0);

  let statusClass = 'neutral';
  let TrendIcon = FiMinus;
  
  if (change_percent_24h > 0) {
    statusClass = 'positive';
    TrendIcon = FiTrendingUp;
  } else if (change_percent_24h < 0) {
    statusClass = 'negative';
    TrendIcon = FiTrendingDown;
  }

  const formattedChange = change_percent_24h !== undefined && change_percent_24h !== null 
    ? `${change_percent_24h > 0 ? '+' : ''}${change_percent_24h.toFixed(2)}%`
    : '0.00%';

  return (
    <div className="card market-card" onClick={onClick}>
      <div className="card-header">
        <div>
          <h3 className="symbol">{symbol}</h3>
          <p className="company">Market Data</p>
        </div>
        <div className={`change ${statusClass}`}>
          <TrendIcon /> {formattedChange}
        </div>
      </div>
      
      <div>
        <h2 className="price gradient-text">{formattedPrice}</h2>
      </div>
    </div>
  );
};

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSymbol, setSelectedSymbol] = useState('GOLD');
  const [chartData, setChartData] = useState([]);
  const [chartLoading, setChartLoading] = useState(false);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await dashboardService.getSummary();
      setSummary(data);
    } catch (err) {
      setError('Failed to load dashboard data. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const [timeframe, setTimeframe] = useState(7);
  const [interval, setInterval] = useState('1d');

  const [chartError, setChartError] = useState(false);

  const fetchChartData = async (symbol, days, ivl) => {
    try {
      setChartLoading(true);
      setChartError(false);
      let data = [];
      if (symbol === 'GOLD') {
        data = await goldService.getHistory(days, ivl);
      } else {
        data = await stocksService.getHistory(symbol, days, ivl);
      }
      setChartData(data);
    } catch (err) {
      console.error('Failed to fetch chart data:', err);
      setChartError(true);
    } finally {
      setChartLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  useEffect(() => {
    fetchChartData(selectedSymbol, timeframe, interval);
  }, [selectedSymbol, timeframe, interval]);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <h2 className="gradient-text">Loading Market Data...</h2>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <h3>Error</h3>
        <p>{error}</p>
        <button onClick={fetchDashboard} className="btn mt-4">
          <FiRefreshCw /> Retry
        </button>
      </div>
    );
  }

  const allMarkets = [
    ...(summary?.gold ? [summary.gold] : []),
    ...(summary?.stocks || []),
    ...(summary?.commodities || [])
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>Market Overview</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Real-time trading trends and analytics</p>
        </div>
        <button onClick={fetchDashboard} className="btn" style={{ background: 'var(--glass-bg)', color: 'var(--text-primary)' }}>
          <FiRefreshCw /> Refresh
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-lg)', marginBottom: '2rem' }}>
        {allMarkets.map((market, index) => (
          <MarketCard key={market.symbol || index} data={market} onClick={() => setSelectedSymbol(market.symbol)} />
        ))}
      </div>

      <div className="card">
        {/* ── Google-style header ── */}
        {(() => {
          const price = chartData.length ? chartData[chartData.length - 1]?.close : null;
          const open  = chartData.length ? chartData[0]?.open : null;
          const high  = chartData.length ? Math.max(...chartData.map(d => d.high).filter(Boolean)) : null;
          const low   = chartData.length ? Math.min(...chartData.map(d => d.low).filter(Boolean)) : null;
          const prevClose = chartData.length > 1 ? chartData[0]?.close : null;
          const vol   = chartData.length ? chartData.reduce((s, d) => s + (d.volume || 0), 0) : null;
          const change = price && prevClose ? price - prevClose : null;
          const changePct = change && prevClose ? (change / prevClose) * 100 : null;
          const isUp = changePct >= 0;
          const fmt = (v) => v != null ? `$${Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—';
          const fmtVol = (v) => v ? Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 }) : '—';
          const tfLabel = [
            { label: '1D', days: 1, interval: '30m' },
            { label: '5D', days: 5, interval: '1h'  },
            { label: '1W', days: 7, interval: '1d'  },
            { label: '1M', days: 30, interval: '1d' },
            { label: '3M', days: 90, interval: '1d' },
          ].find(t => t.days === timeframe && t.interval === interval)?.label || '';

          return (
            <>
              {/* Title row */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '0.5rem' }}>
                <div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.2rem' }}>{selectedSymbol} · {tfLabel}</p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                    <h2 style={{ fontSize: '2rem', fontWeight: 700, margin: 0 }} className="gradient-text">
                      {fmt(price)}
                    </h2>
                    {changePct != null && (
                      <span style={{
                        display: 'inline-flex', alignItems: 'center', gap: '4px',
                        padding: '3px 10px', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 600,
                        background: isUp ? 'rgba(0,230,138,0.12)' : 'rgba(255,80,80,0.12)',
                        color: isUp ? '#00e68a' : '#ff5050',
                      }}>
                        {isUp ? <FiTrendingUp size={13}/> : <FiTrendingDown size={13}/>}
                        {isUp ? '+' : ''}{changePct.toFixed(2)}% {tfLabel === '1D' ? 'today' : `past ${tfLabel}`}
                      </span>
                    )}
                  </div>
                </div>

                {/* Symbol + timeframe controls */}
                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', gap: '0.25rem' }}>
                    {['GOLD', 'AAPL', 'MSFT', 'TSLA'].map(sym => (
                      <button key={sym} onClick={() => setSelectedSymbol(sym)} className="btn"
                        style={{ background: selectedSymbol === sym ? 'var(--cyan)' : 'var(--glass-bg)', color: selectedSymbol === sym ? 'var(--bg-primary)' : 'var(--text-primary)', padding: '4px 10px', fontSize: '0.8rem' }}>
                        {sym}
                      </button>
                    ))}
                  </div>
                  <div style={{ display: 'flex', gap: '2px', padding: '3px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)' }}>
                    {[
                      { label: '1D', days: 1,  interval: '30m' },
                      { label: '5D', days: 5,  interval: '1h'  },
                      { label: '1W', days: 7,  interval: '1d'  },
                      { label: '1M', days: 30, interval: '1d'  },
                      { label: '3M', days: 90, interval: '1d'  },
                    ].map(tf => {
                      const active = timeframe === tf.days && interval === tf.interval;
                      return (
                        <button key={tf.label}
                          onClick={() => { setTimeframe(tf.days); setInterval(tf.interval); }}
                          style={{ border: 'none', borderRadius: 'var(--radius-sm)', fontWeight: 600, cursor: 'pointer',
                            background: active ? 'var(--cyan)' : 'transparent',
                            color: active ? 'var(--bg-primary)' : 'var(--text-secondary)',
                            padding: '4px 11px', fontSize: '0.8rem' }}>
                          {tf.label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Chart */}
              {chartLoading ? (
                <div style={{ height: '300px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', gap: '1rem' }}>
                  <div style={{ width: '100%', display: 'flex', alignItems: 'flex-end', gap: '6px', height: '180px', padding: '0 8px' }}>
                    {[60,80,50,90,70,85,65,95,75,88,55,78].map((h, i) => (
                      <div key={i} style={{ flex: 1, height: `${h}%`, borderRadius: '3px 3px 0 0',
                        background: 'linear-gradient(180deg, rgba(0,230,138,0.15) 0%, rgba(0,230,138,0.05) 100%)',
                        animation: `pulse 1.4s ease-in-out ${i * 0.08}s infinite` }} />
                    ))}
                  </div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Fetching {selectedSymbol} data...</p>
                  <style>{`@keyframes pulse { 0%,100%{opacity:.4} 50%{opacity:1} }`}</style>
                </div>
              ) : chartError ? (
                <div style={{ height: '300px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', gap: '1rem' }}>
                  <p style={{ color: 'var(--text-secondary)' }}>Failed to load {selectedSymbol} chart data.</p>
                  <button onClick={() => fetchChartData(selectedSymbol, timeframe, interval)} className="btn"
                    style={{ background: 'var(--glass-bg)', color: 'var(--text-primary)' }}>
                    <FiRefreshCw /> Retry
                  </button>
                </div>
              ) : (
                <div style={{ height: '360px', marginBottom: '1.25rem' }}>
                  <PriceChart data={chartData} symbol={selectedSymbol} interval={interval} />
                </div>
              )}

              {/* ── Stats bar (Open / High / Low / Prev Close / Vol) ── */}
              {!chartLoading && !chartError && chartData.length > 0 && (
                <div style={{
                  display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                  gap: '0', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '1rem', marginTop: '0.25rem'
                }}>
                  {[
                    { label: 'Open',       value: fmt(open) },
                    { label: 'High',       value: fmt(high) },
                    { label: 'Low',        value: fmt(low) },
                    { label: 'Prev Close', value: fmt(prevClose) },
                    { label: 'Vol',        value: fmtVol(vol) },
                    { label: 'Change',     value: change != null ? `${isUp ? '+' : ''}${fmt(change)}` : '—',
                      color: isUp ? '#00e68a' : '#ff5050' },
                  ].map(stat => (
                    <div key={stat.label} style={{ padding: '0.5rem 0.75rem', borderRight: '1px solid rgba(255,255,255,0.04)' }}>
                      <p style={{ color: 'var(--text-secondary)', fontSize: '0.72rem', marginBottom: '0.2rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        {stat.label}
                      </p>
                      <p style={{ fontWeight: 600, fontSize: '0.9rem', color: stat.color || 'var(--text-primary)', margin: 0 }}>
                        {stat.value}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </>
          );
        })()}
      </div>
    </div>
  );
}
