// API Endpoints
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/auth/login',
    REGISTER: '/api/auth/register',
    REFRESH: '/api/auth/refresh',
    PROFILE: '/api/auth/profile',
  },
  MARKET: {
    QUOTES: '/api/market/quotes',
    HISTORY: '/api/market/history',
    SEARCH: '/api/market/search',
    MOVERS: '/api/market/movers',
    SECTORS: '/api/market/sectors',
  },
  ANALYSIS: {
    TECHNICAL: '/api/analysis/technical',
    PATTERNS: '/api/analysis/patterns',
    SUPPORT_RESISTANCE: '/api/analysis/support-resistance',
    INDICATORS: '/api/analysis/indicators',
    SENTIMENT: '/api/analysis/sentiment',
  },
  PREDICTIONS: {
    LIST: '/api/predictions',
    CREATE: '/api/predictions/create',
    BACKTEST: '/api/predictions/backtest',
    MODELS: '/api/predictions/models',
  },
  ALERTS: {
    LIST: '/api/alerts',
    CREATE: '/api/alerts/create',
    UPDATE: '/api/alerts/update',
    DELETE: '/api/alerts/delete',
    HISTORY: '/api/alerts/history',
  },
};

// Chart Colors
export const CHART_COLORS = {
  cyan: '#00d4ff',
  cyanAlpha: 'rgba(0, 212, 255, 0.15)',
  emerald: '#00e68a',
  emeraldAlpha: 'rgba(0, 230, 138, 0.15)',
  red: '#ff4757',
  redAlpha: 'rgba(255, 71, 87, 0.15)',
  amber: '#ffc107',
  amberAlpha: 'rgba(255, 193, 7, 0.15)',
  purple: '#a855f7',
  purpleAlpha: 'rgba(168, 85, 247, 0.15)',
  white: '#f0f2f5',
  whiteAlpha: 'rgba(240, 242, 245, 0.1)',
  grid: 'rgba(255, 255, 255, 0.04)',
  gridBorder: 'rgba(255, 255, 255, 0.08)',
  candleUp: '#00e68a',
  candleDown: '#ff4757',
  volume: 'rgba(0, 212, 255, 0.3)',
};

// Default Symbols
export const DEFAULT_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'GOLD'];

// Time Ranges
export const TIME_RANGES = [
  { label: '1D', value: '1d', days: 1 },
  { label: '1W', value: '1w', days: 7 },
  { label: '1M', value: '1m', days: 30 },
  { label: '3M', value: '3m', days: 90 },
  { label: '6M', value: '6m', days: 180 },
  { label: '1Y', value: '1y', days: 365 },
  { label: 'ALL', value: 'all', days: null },
];

// Chart Time Intervals
export const CHART_INTERVALS = [
  { label: '1m', value: '1min' },
  { label: '5m', value: '5min' },
  { label: '15m', value: '15min' },
  { label: '1H', value: '1hour' },
  { label: '4H', value: '4hour' },
  { label: '1D', value: '1day' },
  { label: '1W', value: '1week' },
];

// Technical Indicators
export const INDICATORS = {
  RSI: { name: 'RSI', color: CHART_COLORS.cyan, overbought: 70, oversold: 30 },
  MACD: { name: 'MACD', color: CHART_COLORS.emerald, signalColor: CHART_COLORS.red },
  SMA_20: { name: 'SMA 20', color: CHART_COLORS.amber },
  SMA_50: { name: 'SMA 50', color: CHART_COLORS.purple },
  EMA_12: { name: 'EMA 12', color: CHART_COLORS.cyan },
  BOLLINGER: { name: 'Bollinger Bands', color: CHART_COLORS.whiteAlpha },
};

// Alert Types
export const ALERT_TYPES = {
  PRICE_ABOVE: { label: 'Price Above', icon: '📈' },
  PRICE_BELOW: { label: 'Price Below', icon: '📉' },
  PERCENT_CHANGE: { label: '% Change', icon: '📊' },
  VOLUME_SPIKE: { label: 'Volume Spike', icon: '🔊' },
  PATTERN: { label: 'Pattern Detected', icon: '🔍' },
  PREDICTION: { label: 'Prediction Alert', icon: '🤖' },
};

// Prediction Models
export const PREDICTION_MODELS = [
  { id: 'lstm', name: 'LSTM Neural Network', accuracy: 0.847 },
  { id: 'transformer', name: 'Transformer Model', accuracy: 0.891 },
  { id: 'ensemble', name: 'Ensemble (Best)', accuracy: 0.912 },
  { id: 'xgboost', name: 'XGBoost', accuracy: 0.823 },
];

// Navigation Items
export const NAV_ITEMS = [
  { path: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
  { path: '/market-analysis', label: 'Market Analysis', icon: 'analysis' },
  { path: '/predictions', label: 'Predictions', icon: 'predictions' },
  { path: '/alerts', label: 'Alerts', icon: 'alerts' },
  { path: '/settings', label: 'Settings', icon: 'settings' },
];
