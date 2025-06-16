# 💸 Pennywise: Intelligent Stock Analytics Platform

![Pennywise Banner](https://user-images.githubusercontent.com/your-banner.png)

---

## 🚀 Overview

**Pennywise** is a comprehensive, AI-powered stock analytics platform designed for retail investors, analysts, and enthusiasts. It combines advanced technical and fundamental analysis, real-time data, and beautiful visualizations to help you make smarter investment decisions.

---

## ✨ Features

- **📈 Technical Analysis:**  
  - Automated support & resistance detection  
  - Candlestick pattern recognition (single & double)  
  - Channel and trendline generation  
  - RSI, OBV, and more indicators

- **💹 Fundamental Analysis:**  
  - Quarterly & annual financial parsing  
  - Key ratios and peer comparison  
  - ROIC, equity, and capital structure insights

- **🔍 Data Integration:**  
  - Real-time price updates via [yfinance](https://github.com/ranaroussi/yfinance)  
  - Multi-exchange support (.NS, .BS fallback)

- **🖥️ Modern Frontend:**  
  - Built with React & Material UI  
  - Interactive charts and dashboards  
  - Peer comparison and detailed stock views

- **⚡ FastAPI Backend:**  
  - Robust REST API  
  - SQLAlchemy ORM for database management  
  - Modular, scalable architecture

---

## 🏗️ Project Structure

```
Pennywise/
├── Backend/
│   ├── Database/
│   ├── Routers/
│   ├── Stock/
│   └── main.py
├── Frontend/
│   ├── src/
│   └── package.json
├── README.md
└── requirements.txt
```

---

## 🛠️ Tech Stack

- **Frontend:** React, Material UI, Chart.js
- **Backend:** FastAPI, SQLAlchemy, yfinance, BeautifulSoup
- **Database:** PostgreSQL / SQLite
- **ML/Analytics:** NumPy, Pandas, scikit-learn

---

## 🚦 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/pennywise.git
cd pennywise
```

### 2. Backend Setup

```bash
cd Backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. Frontend Setup

```bash
cd Frontend
npm install
npm start
```

---

## 📊 Screenshots

| Dashboard | Peer Comparison | Candlestick Patterns |
|-----------|-----------------|---------------------|
| ![Dashboard](https://user-images.githubusercontent.com/your-dashboard.png) | ![Peer](https://user-images.githubusercontent.com/your-peer.png) | ![Candlestick](https://user-images.githubusercontent.com/your-candle.png) |

---

## 🤝 Contributing

We welcome contributions! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

MIT License © [Your Name](https://github.com/yourusername)

---

> _“The stock market is filled with individuals who know the price of everything, but the value of nothing.”_  
> — Philip Fisher

---
