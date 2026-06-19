import React from 'react';
import { motion } from 'framer-motion';
import { FiTrendingUp, FiTrendingDown, FiMinus } from 'react-icons/fi';

const MarketCard = ({ data }) => {
  if (!data) return null;

  const { symbol, current_price, change_percent_24h } = data;
  
  // Format the price based on typical values for stocks/gold
  const formattedPrice = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(current_price || 0);

  let statusClass = 'text-warning'; // Default neutral
  let TrendIcon = FiMinus;
  
  if (change_percent_24h > 0) {
    statusClass = 'text-success';
    TrendIcon = FiTrendingUp;
  } else if (change_percent_24h < 0) {
    statusClass = 'text-danger';
    TrendIcon = FiTrendingDown;
  }

  const formattedChange = change_percent_24h !== undefined && change_percent_24h !== null 
    ? `${change_percent_24h > 0 ? '+' : ''}${change_percent_24h.toFixed(2)}%`
    : '0.00%';

  return (
    <motion.div 
      className="glass-card p-6 rounded-xl hover-glow transition-all duration-300 cursor-pointer"
      whileHover={{ y: -5, scale: 1.02 }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-200">{symbol}</h3>
          <p className="text-sm text-gray-400 mt-1">Market Data</p>
        </div>
        <div className={`p-2 rounded-full bg-opacity-10 ${statusClass.replace('text-', 'bg-')}`}>
          <TrendIcon className={`w-5 h-5 ${statusClass}`} />
        </div>
      </div>
      
      <div className="mt-4">
        <h2 className="text-3xl font-bold text-white gradient-text-primary tracking-tight">
          {formattedPrice}
        </h2>
        <div className="flex items-center mt-2 space-x-2">
          <span className={`font-medium ${statusClass} flex items-center`}>
            {formattedChange}
          </span>
          <span className="text-gray-500 text-sm">past 24h</span>
        </div>
      </div>
    </motion.div>
  );
};

export default MarketCard;
