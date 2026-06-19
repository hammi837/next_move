// Format currency with symbol and decimal places
export const formatCurrency = (value, currency = 'USD', decimals = 2) => {
  if (value == null || isNaN(value)) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

// Format percentage with sign
export const formatPercentage = (value, decimals = 2) => {
  if (value == null || isNaN(value)) return '—';
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)}%`;
};

// Format large numbers (1K, 1M, 1B)
export const formatLargeNumber = (value) => {
  if (value == null || isNaN(value)) return '—';
  const abs = Math.abs(value);
  if (abs >= 1e12) return `${(value / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
  return value.toLocaleString();
};

// Format volume
export const formatVolume = (value) => {
  if (value == null || isNaN(value)) return '—';
  if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
  if (value >= 1e3) return `${(value / 1e3).toFixed(0)}K`;
  return value.toString();
};

// Format date
export const formatDate = (date, format = 'short') => {
  if (!date) return '—';
  const d = new Date(date);
  if (isNaN(d.getTime())) return '—';

  const options = {
    short: { month: 'short', day: 'numeric' },
    medium: { month: 'short', day: 'numeric', year: 'numeric' },
    long: { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' },
    time: { hour: '2-digit', minute: '2-digit' },
    datetime: { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' },
    full: { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' },
  };

  return d.toLocaleDateString('en-US', options[format] || options.short);
};

// Relative time (e.g., "2 hours ago")
export const formatRelativeTime = (date) => {
  if (!date) return '—';
  const d = new Date(date);
  const now = new Date();
  const diffMs = now - d;
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(date, 'short');
};

// Format price change
export const formatChange = (value, isPercentage = false) => {
  if (value == null || isNaN(value)) return { text: '—', isPositive: true };
  const isPositive = value >= 0;
  const sign = isPositive ? '+' : '';
  const text = isPercentage
    ? `${sign}${value.toFixed(2)}%`
    : `${sign}${formatCurrency(value)}`;
  return { text, isPositive };
};

// Clamp a number between min and max
export const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

// Generate random ID
export const generateId = () => Math.random().toString(36).substr(2, 9);
