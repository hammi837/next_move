import React, { useState, useEffect } from 'react';
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

  const [timeframe, setTimeframe] = useState(30);

  const fetchChartData = async (symbol, days) => {
    try {
      setChartLoading(true);
      let data = [];
      if (symbol === 'GOLD') {
        data = await goldService.getHistory(days);
      } else {
        data = await stocksService.getHistory(symbol, days);
      }
      setChartData(data);
    } catch (err) {
      console.error('Failed to fetch chart data:', err);
    } finally {
      setChartLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  useEffect(() => {
    fetchChartData(selectedSymbol, timeframe);
  }, [selectedSymbol, timeframe]);

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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
          <h2>{selectedSymbol} Price History</h2>
          
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', gap: '0.5rem', padding: '4px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)' }}>
              {[ {label: '1W', days: 7}, {label: '1M', days: 30}, {label: '3M', days: 90} ].map(tf => (
                <button
                  key={tf.label}
                  onClick={() => setTimeframe(tf.days)}
                  style={{ 
                    border: 'none',
                    borderRadius: 'var(--radius-sm)',
                    fontWeight: 600,
                    cursor: 'pointer',
                    background: timeframe === tf.days ? 'var(--glass-bg-active)' : 'transparent',
                    color: timeframe === tf.days ? 'var(--cyan)' : 'var(--text-secondary)',
                    padding: '4px 12px'
                  }}
                >
                  {tf.label}
                </button>
              ))}
            </div>

            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {['GOLD', 'AAPL', 'MSFT', 'TSLA'].map(sym => (
                <button
                  key={sym}
                  onClick={() => setSelectedSymbol(sym)}
                  className="btn"
                  style={{ 
                    background: selectedSymbol === sym ? 'var(--cyan)' : 'var(--glass-bg)',
                    color: selectedSymbol === sym ? 'var(--bg-primary)' : 'var(--text-primary)',
                    padding: '4px 12px'
                  }}
                >
                  {sym}
                </button>
              ))}
            </div>
          </div>
        </div>

        {chartLoading ? (
          <div style={{ height: '300px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            Loading Chart...
          </div>
        ) : (
          <div style={{ height: '400px' }}>
            <PriceChart data={chartData} symbol={selectedSymbol} />
          </div>
        )}
      </div>
    </div>
  );
}
