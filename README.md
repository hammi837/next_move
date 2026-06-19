# 🚀 Next Move — Trading Analysis & Prediction Platform

A full-stack AI-powered platform for analyzing historical trading trends (stocks, gold, commodities), identifying patterns, predicting future price movements, and delivering actionable insights for traders and investors.

---

## 📁 Project Structure

```
next_move/
├── BE/          → Python FastAPI backend (API, ML models, data pipelines)
├── FE/          → React + Vite frontend (dashboard, charts, real-time UI)
└── README.md    → This file
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Vite, Chart.js, React Router, Zustand, Framer Motion |
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| **Database** | PostgreSQL 15, Redis 7 |
| **ML/AI** | TensorFlow/Keras (LSTM), XGBoost, Facebook Prophet, scikit-learn |
| **Data Sources** | Yahoo Finance, Alpha Vantage, NewsAPI, FRED |
| **DevOps** | Docker, Docker Compose |

## 🔥 Key Features

### 📊 Data Collection
- Real-time market data via Yahoo Finance & Alpha Vantage APIs
- Historical OHLCV data for stocks, gold, and commodities
- Technical indicators: Moving Averages, RSI, MACD, Bollinger Bands

### 📈 Analysis Engine
- Technical analysis with 20+ indicators
- Pattern recognition (candlestick patterns, chart patterns)
- Support/resistance level detection
- Trend identification (bullish/bearish/neutral)

### 🤖 Prediction Module
- LSTM neural networks for time-series forecasting
- XGBoost gradient boosting for tabular predictions
- Facebook Prophet for trend decomposition
- Ensemble model combining all predictors
- Backtesting framework for model validation

### 🖥️ Dashboard
- Interactive candlestick & line charts
- Real-time price tracking with WebSocket
- Prediction confidence visualizations
- Alert management system
- Premium dark theme with glassmorphism design

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker (optional, recommended)

### Option 1: Docker (Recommended)
```bash
cd BE
docker-compose up -d
```

### Option 2: Manual Setup

#### Backend
```bash
cd BE
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # Edit with your settings
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd FE
npm install
cp .env.example .env          # Edit with your settings
npm run dev
```

### Access
- **Frontend Dashboard**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📅 Development Phases

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 0 | Project scaffolding & structure | ✅ Complete |
| Phase 1 | Data collection pipeline & basic dashboard | 🔜 Next |
| Phase 2 | Technical analysis & pattern recognition | ⏳ Planned |
| Phase 3 | ML model development & predictions | ⏳ Planned |
| Phase 4 | Alerts, auth, advanced visualizations | ⏳ Planned |

## 📊 Supported Markets

| Market | Key Indicators |
|--------|---------------|
| **Stocks** | Price movement, volume, P/E ratios, sector trends |
| **Gold** | Price trends, geopolitical events, USD strength, inflation |
| **Commodities** | Supply/demand, seasonal patterns, futures curves |
| **General** | VIX volatility, market sentiment, support/resistance |

## 📄 License

This project is proprietary. All rights reserved.
