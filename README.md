# Quantitative Research Platform 📈

A modular, production-ready quantitative research platform built with clean layered architecture. This platform demonstrates the complete end-to-end workflow from data ingestion to model execution to performance testing.

## 🚀 Features

- **Layered Architecture**: Clean separation between data, models, and orchestration layers
- **End-to-End Example**: Complete workflow from data ingestion to performance testing
- **Production Ready**: Docker containerized with comprehensive error handling and monitoring
- **Modular Design**: Easy to extend with new strategies and data sources
- **Performance Analytics**: Automated model evaluation and ranking system
- **Web UI Management**: Airflow interface for monitoring and data pipeline management

## 🏗️ Architecture Overview

The platform follows a clean layered architecture:

### **Data Layer** (`data_layer/`)
- Market data ingestion from Polygon.io
- Technical indicator calculation
- Feature engineering and storage
- Data validation and quality checks

### **Models Layer** (`models/`)
- Trading strategy implementations
- Enhanced momentum strategy (example)
- Base strategy framework for extensibility

### **Orchestration Layer** (`dags/`)
- End-to-end data ingestion pipeline
- Model execution and signal generation
- Performance testing and evaluation

### **Infrastructure Layer** (`infrastructure/`)
- Common utilities and configuration
- Database schema management
- Logging and monitoring foundations

## 🛠️ Tech Stack

- **Orchestration**: Apache Airflow
- **Database**: PostgreSQL 13
- **Data Processing**: Python, Pandas, SQLAlchemy
- **API Integration**: Polygon.io REST API
- **Containerization**: Docker & Docker Compose
- **Database Access**: Direct PostgreSQL connection via port-forwarding

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
- **PostgreSQL**: Use `./connect-prod.sh` then connect to localhost:15432

### 4. Run End-to-End Example
1. Open Airflow UI at http://localhost:8080
2. Enable the three end-to-end DAGs:
   - `end_to_end_data_ingestion`
   - `end_to_end_model_execution` 
   - `end_to_end_performance_testing`
3. Trigger the data ingestion DAG first to populate data

## 📈 End-to-End Workflow

```
Data Ingestion → Model Execution → Performance Testing
       ↓               ↓                ↓
  Market Data    Trading Signals   Model Rankings
  Features       Risk Metrics      Performance Reports
  Quality        Confidence        Alert Generation
  Validation     Scoring           Trend Analysis
```

### Pipeline Components:
1. **Data Ingestion**: Fetch market data, calculate features, validate quality
2. **Model Execution**: Run trading strategies, generate signals, track performance
3. **Performance Testing**: Evaluate models, rank performance, generate reports

## 🗄️ Database Schema

```sql
-- Core data tables
market_data              -- Daily OHLCV data from external sources
trading_universe         -- Active tradeable symbols with metadata
feature_store            -- JSON-based feature storage for models

-- Model framework
models                   -- Model registry with configurations  
model_runs               -- Execution tracking and status
signals                  -- Model-generated trading signals

-- Performance framework
model_performance        -- Comprehensive performance metrics
performance_reports      -- Daily comparative analysis and rankings
```

## 🔧 Configuration Options

### API Key Setup:
Set `POLYGON_API_KEY` in `.env` file (required for data ingestion)

### Customization:
- **Add Symbols**: Modify `UNIVERSE_SYMBOLS` in `dags/end_to_end_data_ingestion.py`
- **Add Strategies**: Create new strategy classes in `models/strategies/`
- **Extend Features**: Add calculations in data ingestion DAG
- **Custom Metrics**: Modify performance testing DAG

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
-- Latest trading signals
SELECT s.*, m.model_name 
FROM signals s 
JOIN models m ON s.model_id = m.id
ORDER BY s.created_at DESC LIMIT 10;

-- Model performance comparison
SELECT mp.*, m.model_name
FROM model_performance mp
JOIN models m ON mp.model_id = m.id
ORDER BY mp.sharpe_ratio DESC;

-- Market data with features
SELECT md.symbol, md.date, md.close_price, fs.features
FROM market_data md
JOIN feature_store fs ON md.symbol = fs.symbol AND md.date = fs.date
WHERE md.date >= CURRENT_DATE - INTERVAL '7 days';
```

## 🔍 Monitoring & Troubleshooting

### Check Service Health:
```bash
docker-compose ps
docker-compose logs airflow
docker-compose logs postgres
```

### Common Issues:
- **DAG not appearing**: Check syntax with `docker exec quant-airflow python /opt/airflow/dags/<dag_name>.py`
- **API rate limits**: Upgrade Polygon.io plan or adjust schedule intervals
- **Database errors**: Check PostgreSQL logs and verify schema is applied
- **Model execution failures**: Ensure market data exists for execution date

## 🎯 Next Steps

1. **Add New Strategies**: Implement mean reversion, ML-based models
2. **Expand Data Sources**: Alternative data, news sentiment, economic indicators
3. **Real-time Processing**: WebSocket integration for live signals
4. **Advanced Analytics**: Risk attribution, portfolio optimization
5. **Backtesting Framework**: Historical strategy validation
6. **Production Trading**: Broker integration for live execution

## 📚 Documentation

- **[Architecture Guide](ARCHITECTURE.md)**: Detailed system architecture
- **[End-to-End Example](END_TO_END_EXAMPLE.md)**: Complete workflow walkthrough
- **[Quick Start Guide](QUICK_START.md)**: Fast setup instructions

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