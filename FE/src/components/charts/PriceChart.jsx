import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// Custom plugin for neon ECG glow
const neonGlowPlugin = {
  id: 'neonGlow',
  beforeDatasetsDraw: (chart) => {
    const ctx = chart.ctx;
    ctx.save();
    ctx.shadowColor = '#00e68a'; // Emerald glow
    ctx.shadowBlur = 15;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 0;
  },
  afterDatasetsDraw: (chart) => {
    chart.ctx.restore();
  }
};

const PriceChart = ({ data, symbol, interval = '1d' }) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-800 bg-opacity-50 rounded-xl border border-gray-700">
        <p className="text-gray-400">No data available for {symbol}</p>
      </div>
    );
  }

  const isIntraday = interval !== '1d';

  // Format x-axis labels based on interval
  const formatLabel = (ts) => {
    const date = new Date(ts);
    if (interval === '1d') {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
    if (interval === '1h' || interval === '30m') {
      // 5D or 1D: show day + time
      const day = date.toLocaleDateString('en-US', { weekday: 'short' });
      const time = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
      return interval === '30m' ? time : `${day} ${time}`;
    }
    // default
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
  };

  // Format data for Chart.js
  const chartData = {
    labels: data.map(d => formatLabel(d.timestamp)),
    datasets: [
      {
        label: `${symbol} Price`,
        data: data.map(d => d.close),
        borderColor: '#00e68a', // Emerald line (ECG style)
        backgroundColor: 'rgba(0, 230, 138, 0.05)',
        borderWidth: 2.5,
        pointRadius: 0, // No points, pure line
        pointHoverRadius: 6,
        pointBackgroundColor: '#00e68a',
        fill: true,
        tension: 0, // Sharp jagged edges for ECG look
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(10, 14, 26, 0.95)',
        titleColor: '#fff',
        bodyColor: '#00e68a',
        borderColor: 'rgba(0, 230, 138, 0.2)',
        borderWidth: 1,
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(context.parsed.y);
            }
            return label;
          }
        }
      }
    },
    scales: {
      x: {
        grid: {
          display: true,
          color: 'rgba(0, 230, 138, 0.05)', // ECG paper grid
          drawBorder: true,
          borderColor: 'rgba(0, 230, 138, 0.2)',
        },
        ticks: {
          color: '#5a6478',
          maxTicksLimit: isIntraday ? 10 : 7,
          font: { family: "'JetBrains Mono', monospace" }
        }
      },
      y: {
        grid: {
          display: true,
          color: 'rgba(0, 230, 138, 0.05)', // ECG paper grid
          drawBorder: true,
          borderColor: 'rgba(0, 230, 138, 0.2)',
        },
        ticks: {
          color: '#5a6478',
          font: { family: "'JetBrains Mono', monospace" },
          callback: function(value) {
            return '$' + value;
          }
        }
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    }
  };

  return (
    <div className="w-full h-full min-h-[300px]" style={{ position: 'relative' }}>
      <Line data={chartData} options={options} plugins={[neonGlowPlugin]} />
      {/* Subtle overlay to enhance the ECG monitor effect */}
      <div style={{
        position: 'absolute',
        top: 0, left: 0, right: 0, bottom: 0,
        background: 'linear-gradient(rgba(10, 14, 26, 0) 50%, rgba(0, 230, 138, 0.02) 100%)',
        pointerEvents: 'none'
      }}></div>
    </div>
  );
};

export default PriceChart;
