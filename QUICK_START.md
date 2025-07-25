# Quick Start Guide

Get up and running with the quant platform's end-to-end example in minutes.

## Prerequisites

- Docker and Docker Compose installed
- Polygon.io API key ([Get free key](https://polygon.io/))

## 🚀 Start the Platform

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd quant-platform

# Set up environment
cp env.example .env
# Edit .env and add: POLYGON_API_KEY=your_actual_api_key_here
```

### 2. Launch Local Services
```bash
# Start local development environment
docker compose up -d

# Verify services are running
docker compose ps
```

### 3. Access Local Web Interfaces
- **Airflow**: http://localhost:8080 (credentials from .env file)
- **pgAdmin**: http://localhost:5050 (credentials from .env file)

### 4. Connect to Production (Optional)
```bash
# Connect to production services
./connect-prod.sh

# When done, disconnect
./disconnect-prod.sh
```

**Production Access:**
- **Airflow**: http://localhost:8081 (credentials from GitHub secrets)
- **pgAdmin**: http://localhost:5051 (credentials from GitHub secrets)

## 🔄 Run the End-to-End Example

### 1. Enable DAGs
In Airflow UI (http://localhost:8080):
1. Enable `end_to_end_data_ingestion`
2. Enable `end_to_end_model_execution` 
3. Enable `end_to_end_performance_testing`

### 2. Trigger First Run
```bash
# Method 1: Via Airflow UI
# Click "Trigger DAG" on end_to_end_data_ingestion

# Method 2: Via CLI
docker exec quant-airflow airflow dags trigger end_to_end_data_ingestion
```

### 3. Monitor Progress
Watch the DAGs run in sequence:
1. **Data Ingestion** (5-10 minutes) - Fetches market data, calculates features
2. **Model Execution** (2-5 minutes) - Runs momentum strategy, generates signals  
3. **Performance Testing** (1-2 minutes) - Evaluates performance, creates reports

## 📊 View Results

### Database Queries (via pgAdmin)
```sql
-- View latest trading signals
SELECT s.*, m.model_name 
FROM signals s 
JOIN models m ON s.model_id = m.id
ORDER BY s.created_at DESC LIMIT 10;

-- Check model performance  
SELECT mp.*, m.model_name
FROM model_performance mp
JOIN models m ON mp.model_id = m.id
ORDER BY mp.sharpe_ratio DESC;

-- See market data
SELECT symbol, date, close_price, volume
FROM market_data 
ORDER BY date DESC, symbol LIMIT 20;
```

### Check Data Quality
```sql
-- Data freshness
SELECT MAX(date) as latest_data FROM market_data;

-- Signal generation health
SELECT m.model_name, COUNT(s.*) as signals_today
FROM models m
LEFT JOIN signals s ON m.id = s.model_id 
    AND DATE(s.created_at) = CURRENT_DATE
GROUP BY m.id, m.model_name;
```

## 🛠️ Understanding the Architecture

### Data Flow
```
Polygon API → Data Ingestion → Feature Store → Model Execution → Performance Testing
     ↓             ↓              ↓              ↓                ↓
Market Data    Technical      Enhanced       Trading         Model Rankings
   OHLCV       Indicators     Momentum       Signals         & Reports
               (RSI, MACD)    Strategy    (Buy/Sell/Hold)
```

### Key Components
- **Enhanced Momentum Strategy**: Multi-factor momentum with RSI, volume, and volatility confirmation
- **Feature Store**: JSON-based storage for calculated technical indicators
- **Performance Framework**: Automated evaluation with Sharpe ratio, drawdown, win rate

## 🔧 Customization

### Add New Symbols
Edit `dags/end_to_end_data_ingestion.py`:
```python
UNIVERSE_SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX",
    "YOUR_SYMBOL_HERE"  # Add your symbol
]
```

### Modify Strategy Parameters
Edit `dags/end_to_end_model_execution.py`:
```python
'parameters': {
    'short_ma_period': 10,     # Faster signals: 5, Slower: 15
    'long_ma_period': 20,      # Faster signals: 15, Slower: 30
    'rsi_lower': 30,           # More signals: 35, Fewer: 25
    'rsi_upper': 70,           # More signals: 65, Fewer: 75
    'min_confidence': 0.4,     # Higher threshold: 0.6, Lower: 0.3
}
```

## 🔒 Security Configuration

### Default Credentials (IMPORTANT!)

**SECURITY WARNING**: Never commit credentials to version control!

For local development, the platform uses basic defaults. For production deployments, you MUST set secure credentials via environment variables.

### Override Credentials

**For production deployments, always override these defaults!** Create a `.env` file:

```bash
cp env.example .env
```

Then edit `.env` to set your own secure credentials:

```bash
# Your secure Airflow admin credentials
AIRFLOW_ADMIN_USERNAME=your_username
AIRFLOW_ADMIN_PASSWORD=your_secure_password
AIRFLOW_ADMIN_EMAIL=admin@yourcompany.com

# Your secure pgAdmin credentials  
PGADMIN_EMAIL=admin@yourcompany.com
PGADMIN_PASSWORD=your_secure_pgadmin_password
```

### Kubernetes Deployment Security

For Kubernetes deployments, the platform uses `ClusterIP` service type for internal access only. To access Airflow:

```bash
# Port forward to access Airflow securely
kubectl port-forward -n quant-platform service/airflow 8080:8080

# Then access via http://localhost:8080
```

## 🐛 Common Issues

### DAG Not Appearing
```bash
# Check DAG syntax
docker exec quant-airflow python /opt/airflow/dags/end_to_end_data_ingestion.py
```

### No Market Data
- Verify `POLYGON_API_KEY` is set in `.env`
- Check API rate limits (free tier has limits)
- Ensure internet connectivity

### Database Connection Errors
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Verify database is running
docker exec quant-postgres psql -U quant_user -d quant_data -c "SELECT 1;"
```

## 📈 Next Steps

### 1. Explore the Strategy
Review `models/strategies/momentum/enhanced_momentum.py` to understand:
- Multi-factor signal generation
- Risk management and position sizing
- Confidence scoring methodology

### 2. Extend the Platform
- **Add new strategies**: Create classes inheriting from `BaseStrategy`
- **More data sources**: Economic indicators, news sentiment
- **Advanced features**: Machine learning models, portfolio optimization

### 3. Production Deployment
- Use `k8s/` configs for Kubernetes deployment
- Set up CI/CD with `.github/workflows/`
- Configure monitoring and alerting

## 🛑 Stopping Services

```bash
# Stop local development
docker compose down

# Stop production connections
./disconnect-prod.sh
```

## 📚 Documentation

- **[Development Workflow](DEV_WORKFLOW.md)**: Complete development guide
- **[Production Access](PRODUCTION_ACCESS.md)**: Secure production access
- **[Architecture Guide](ARCHITECTURE.md)**: Detailed system design
- **[End-to-End Example](END_TO_END_EXAMPLE.md)**: Complete workflow explanation
- **[GitHub Secrets Setup](GITHUB_SECRETS_SETUP.md)**: CI/CD security configuration

---

**Ready to build your own quant strategies?** 🚀

The end-to-end example provides a complete foundation demonstrating data ingestion, model execution, and performance testing within a clean, modular architecture.