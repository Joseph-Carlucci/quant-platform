# Quantitative Research Platform 📈

A production-ready quantitative research platform built with Apache Airflow, PostgreSQL, and real-time market data from Polygon.io. This platform automatically collects, processes, and stores market data for analysis and strategy development.

## 🚀 Features

- **Real-time Market Data**: Integration with Polygon.io API (unlimited calls supported)
- **Automated Data Pipeline**: Runs every 6 hours via Apache Airflow
- **Robust Data Storage**: PostgreSQL with proper schema and upsert capabilities
- **Production Ready**: Docker containerized with proper error handling and logging
- **Web UI Management**: Airflow and pgAdmin interfaces for monitoring and data exploration
- **Scalable Architecture**: Ready for cloud deployment (EC2, etc.)

## 📊 Data Sources

Currently ingests data for: **AAPL, GOOGL, MSFT, TSLA, AMZN, NVDA, META, SPY**

### Data Types Collected:
- **Previous Close Prices**: Latest closing prices with OHLCV data
- **Company Details**: Market cap, employee count, descriptions, and metadata
- **Daily Aggregates**: Historical OHLCV data with volume and VWAP
- **Ticker Information**: Exchange details, currency, and market classification

## 🛠️ Tech Stack

- **Orchestration**: Apache Airflow
- **Database**: PostgreSQL 13
- **Data Processing**: Python, Pandas, SQLAlchemy
- **API Integration**: Polygon.io REST API
- **Containerization**: Docker & Docker Compose
- **Admin Interface**: pgAdmin 4

## ⚡ Quick Start

### Prerequisites
- Docker and Docker Compose
- Polygon.io API key ([Get free key](https://polygon.io/))

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd quant-platform

# Create environment file
cp env.example .env

# Edit .env with your API key
nano .env  # Add: POLYGON_API_KEY=your_actual_api_key_here
```

### 2. Launch Platform
```bash
# Start all services
docker-compose up -d

# Check services are running
docker-compose ps
```

### 3. Access Services
- **Airflow Web UI**: http://localhost:8080 (admin/admin)
- **pgAdmin**: http://localhost:5050 (admin@admin.com/admin)
- **PostgreSQL**: localhost:5432 (quant_user/quant_password)

### 4. Run Data Pipeline
1. Open Airflow UI at http://localhost:8080
2. Enable the `polygon_data_pipeline` DAG
3. Trigger a manual run to test

## 📈 Data Pipeline Architecture

```
Polygon.io API → Airflow DAG → Data Processing → PostgreSQL
                      ↓
           Error Handling & Retry Logic
                      ↓
              Upsert (No Duplicates)
```

### Pipeline Tasks:
1. **create_tables**: Sets up database schema
2. **fetch_previous_close**: Gets latest market prices
3. **fetch_ticker_details**: Collects company information  
4. **fetch_daily_aggregates**: Retrieves historical data

## 🗄️ Database Schema

```sql
-- Market data is stored in organized tables:
market_data.previous_close      -- Latest prices and volumes
market_data.ticker_details      -- Company fundamentals
market_data.daily_aggregates    -- Historical OHLCV data
```

## 🔧 Configuration Options

### API Key Setup (Multiple Methods):
1. **Environment Variable** (Recommended): Set `POLYGON_API_KEY` in `.env`
2. **Airflow Connection**: Admin → Connections → polygon_api
3. **Airflow Variable**: Admin → Variables → polygon_api_key

### Customization:
- **Add Tickers**: Modify `MVP_TICKERS` in `dags/polygon_data_pipeline.py`
- **Change Schedule**: Adjust `schedule_interval` in DAG definition
- **Database Settings**: Update connection strings in `docker-compose.yml`

## 🚀 Production Deployment

### For EC2 Deployment:
```bash
# Set API key via environment variable
export POLYGON_API_KEY=your_key_here

# Or use AWS Parameter Store (supported)
aws ssm put-parameter --name "/quant-platform/polygon-api-key" --value "your_key" --type "SecureString"
```

### Security Checklist:
- [ ] Change default passwords in `docker-compose.yml`
- [ ] Use environment variables for all secrets
- [ ] Set up SSL/TLS certificates
- [ ] Configure backup strategies
- [ ] Monitor resource usage

## 📊 Sample Queries

```sql
-- Latest stock prices
SELECT ticker, close_price, volume, date 
FROM market_data.previous_close 
ORDER BY date DESC;

-- Company market caps
SELECT ticker, name, market_cap, total_employees 
FROM market_data.ticker_details 
WHERE market_cap IS NOT NULL
ORDER BY market_cap DESC;

-- Price trends
SELECT ticker, date, close_price, volume
FROM market_data.daily_aggregates 
WHERE ticker = 'AAPL'
ORDER BY date DESC
LIMIT 30;
```

## 🔍 Monitoring & Troubleshooting

### Check Service Health:
```bash
docker-compose ps
docker-compose logs airflow
docker-compose logs postgres
```

### Common Issues:
- **DAG not appearing**: Check syntax with `docker exec quant-airflow python /opt/airflow/dags/polygon_data_pipeline.py`
- **API rate limits**: Upgrade Polygon.io plan or adjust schedule
- **Database errors**: Check PostgreSQL logs and connection settings

## 🎯 Next Steps

1. **Add Analytics**: Build Jupyter notebooks for data analysis
2. **Expand Data Sources**: Integrate Alpha Vantage, Yahoo Finance, etc.
3. **Create Strategies**: Implement backtesting frameworks
4. **Scale Infrastructure**: Move to cloud services (AWS RDS, ECS, etc.)
5. **Add Real-time Feeds**: WebSocket integration for live data
6. **Build Dashboards**: Create visualization interfaces

## 📝 License

[Your chosen license]

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

**Ready to start your quantitative research journey?** 🚀

*This platform provides the foundation for building sophisticated trading strategies and market analysis tools.*