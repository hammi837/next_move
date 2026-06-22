import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 15000, // 15s — fail fast, don't hang indefinitely
  headers: {
    'Content-Type': 'application/json',
  },
});

export const dashboardService = {
  getSummary: async () => {
    try {
      const response = await api.get('/dashboard/summary');
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard summary:', error);
      throw error;
    }
  },
  getMarketOverview: async () => {
    try {
      const response = await api.get('/dashboard/market-overview');
      return response.data;
    } catch (error) {
      console.error('Error fetching market overview:', error);
      throw error;
    }
  },
  getRecentData: async (symbol, limit = 50) => {
    try {
      const response = await api.get(`/dashboard/recent-data/${symbol}?limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching recent data for ${symbol}:`, error);
      throw error;
    }
  }
};

export const goldService = {
  getCurrent: async () => {
    try {
      const response = await api.get('/gold/current');
      return response.data;
    } catch (error) {
      console.error('Error fetching current gold price:', error);
      throw error;
    }
  },
  getHistory: async (days = 7, interval = '1d') => {
    try {
      const response = await api.get(`/gold/history?days=${days}&interval=${interval}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching gold history:', error);
      throw error;
    }
  },
  getStats: async (days = 30) => {
    try {
      const response = await api.get(`/gold/stats?days=${days}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching gold stats:', error);
      throw error;
    }
  }
};

export const stocksService = {
  getOverview: async () => {
    try {
      const response = await api.get('/stocks/overview');
      return response.data;
    } catch (error) {
      console.error('Error fetching stocks overview:', error);
      throw error;
    }
  },
  getCurrent: async (symbol) => {
    try {
      const response = await api.get(`/stocks/current/${symbol}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching current price for ${symbol}:`, error);
      throw error;
    }
  },
  getHistory: async (symbol, days = 30, interval = '1d') => {
    try {
      const response = await api.get(`/stocks/history/${symbol}?days=${days}&interval=${interval}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching history for ${symbol}:`, error);
      throw error;
    }
  }
};

export const indicatorsService = {
  getSummary: async (symbol, days = 90) => {
    const response = await api.get(`/indicators/${symbol}/summary?days=${days}`);
    return response.data;
  },
  getIndicators: async (symbol, days = 120) => {
    const response = await api.get(`/indicators/${symbol}/indicators?days=${days}`);
    return response.data;
  },
  getRSI: async (symbol) => {
    const response = await api.get(`/indicators/${symbol}/rsi`);
    return response.data;
  },
  getMACD: async (symbol) => {
    const response = await api.get(`/indicators/${symbol}/macd`);
    return response.data;
  },
  getPatterns: async (symbol) => {
    const response = await api.get(`/indicators/${symbol}/patterns/candlestick`);
    return response.data;
  },
  getTrendAnalysis: async (symbol, days = 90) => {
    const response = await api.get(`/indicators/${symbol}/trend-analysis?days=${days}`);
    return response.data;
  },
};

export default api;
