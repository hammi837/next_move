import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
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
  getHistory: async (days = 7) => {
    try {
      const response = await api.get(`/gold/history?days=${days}`);
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
  getHistory: async (symbol, days = 30) => {
    try {
      const response = await api.get(`/stocks/history/${symbol}?days=${days}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching history for ${symbol}:`, error);
      throw error;
    }
  }
};

export default api;
