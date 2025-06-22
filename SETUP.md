# Quantitative Research Platform Setup Guide

This comprehensive guide will help you set up the quantitative research platform with Docker, PostgreSQL, Apache Airflow, and Polygon.io data integration. The platform is production-ready and has been tested with unlimited API calls.

## Prerequisites

- **Docker and Docker Compose** (v20+ recommended)
- **Polygon.io API key** - [Get free key](https://polygon.io/) (unlimited plan recommended for production)
- **4GB+ RAM** available for containers
- **Ports available**: 8080 (Airflow), 5432 (PostgreSQL), 5050 (pgAdmin), 6379 (Redis)

## Quick Start

### 1. Clone and Configure

```bash
# Clone the repository
git clone <your-repo-url>
cd quant-platform

# Create environment file from template
cp env.example .env

# Edit .env with your actual API key
nano .env
```

**Required in `.env` file:**
```bash
# Polygon.io API Configuration
POLYGON_API_KEY=your_actual_api_key_here

# Optional: Override default database passwords
# POSTGRES_PASSWORD=your_secure_password
# PGADMIN_DEFAULT_PASSWORD=your_admin_password
```

### 2. Launch the Platform

```bash
# Start all services in detached mode
docker-compose up -d

# Check all services are running
docker-compose ps

# Expected output: All services should show "Up" status
# - quant-postgres (healthy)
# - quant-airflow (running)
# - quant-redis (running)  
# - quant-pgadmin (running)
```

### 3. Verify Installation

```bash
# Check Airflow is responding
curl http://localhost:8080/health

# View service logs if needed
docker-compose logs airflow
docker-compose logs postgres
```

### 4. Access Web Interfaces

- **Airflow Web UI**: http://localhost:8080
  - Username: `admin`
  - Password: `admin`

- **pgAdmin**: http://localhost:5050
  - Email: `admin@admin.com`
  - Password: `admin`

- **PostgreSQL Direct**: `localhost:5432`
  - Username: `quant_user`
  - Password: `quant_password`
  - Database: `quant_data`

## Running Your First Data Pipeline

### 1. Enable the DAG

1. Open Airflow UI at http://localhost:8080
2. Log in with `admin/admin`
3. Find `polygon_data_pipeline` in the DAGs list
4. Click the toggle switch to **enable** the DAG
5. Click **Trigger DAG** to run it manually

### 2. Monitor Execution

- Watch the **Graph View** to see task progress
- Check **Logs** for each task to see detailed output
- **Grid View** shows historical runs and success/failure status

### 3. Expected Results

After successful execution, you should see:
- ✅ `create_tables`: Database schema created
- ✅ `fetch_previous_close`: Latest prices for 8 tickers collected
- ✅ `fetch_ticker_details`: Company information stored
- ✅ `fetch_daily_aggregates`: Historical data retrieved

## Data Pipeline Details

### What Gets Collected

**For these tickers**: AAPL, GOOGL, MSFT, TSLA, AMZN, NVDA, META, SPY

**Data types**:
1. **Previous Close Data**: Latest closing prices with OHLCV
2. **Company Details**: Market cap, employee count, descriptions
3. **Daily Aggregates**: Historical OHLCV data for analysis
4. **Ticker Metadata**: Exchange, currency, and classification info

### Database Schema

```sql
-- All data stored in 'quant_data' database under 'market_data' schema

market_data.previous_close:
- ticker, date, close_price, open_price, high_price, low_price
- volume, pre_market, after_hours, created_at

market_data.ticker_details:
- ticker, name, market, locale, primary_exchange, type
- currency_name, market_cap, share_class_outstanding
- weighted_shares_outstanding, description, homepage_url
- total_employees, updated_at

market_data.daily_aggregates:
- ticker, date, open_price, high_price, low_price, close_price
- volume, vwap, timestamp_utc, transactions, created_at
```

### Scheduling

- **Default**: Runs every 6 hours automatically
- **Manual**: Can trigger anytime via Airflow UI
- **Customizable**: Edit `schedule_interval` in DAG file

## Database Access and Queries

### Via pgAdmin Web Interface

1. Open http://localhost:5050
2. Login with `admin@admin.com/admin`  
3. **Add New Server**:
   - **General Tab**:
     - Name: `Quant Database`
   - **Connection Tab**:
     - Host name/address: `postgres`
     - Port: `5432`
     - Maintenance database: `quant_data`
     - Username: `quant_user`
     - Password: `quant_password`

### Sample Queries

```sql
-- View latest stock prices
SELECT ticker, close_price, volume, date 
FROM market_data.previous_close 
ORDER BY date DESC, ticker;

-- Top companies by market cap
SELECT ticker, name, market_cap, total_employees 
FROM market_data.ticker_details 
WHERE market_cap IS NOT NULL
ORDER BY market_cap DESC;

-- AAPL price history (last 30 days)
SELECT date, close_price, volume, 
       (close_price - LAG(close_price) OVER (ORDER BY date)) / LAG(close_price) OVER (ORDER BY date) * 100 as daily_return
FROM market_data.daily_aggregates 
WHERE ticker = 'AAPL'
ORDER BY date DESC
LIMIT 30;

-- Data freshness check
SELECT 
    'previous_close' as table_name,
    COUNT(*) as records,
    MAX(created_at) as last_updated
FROM market_data.previous_close
UNION ALL
SELECT 
    'ticker_details' as table_name,
    COUNT(*) as records,
    MAX(updated_at) as last_updated  
FROM market_data.ticker_details;
```

## Customization

### Adding More Tickers

Edit `dags/polygon_data_pipeline.py`:

```python
# Find this line and add your tickers
MVP_TICKERS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META', 'SPY', 'QQQ', 'IWM']
```

### Changing Update Frequency

```python
# In DAG definition, modify schedule_interval
dag = DAG(
    'polygon_data_pipeline',
    schedule_interval=timedelta(hours=1),  # Run every hour
    # or use cron: schedule_interval='0 9,12,15,18 * * 1-5'  # Weekdays only
)
```

### API Key Configuration Options

The platform supports multiple ways to provide your API key (in order of preference):

1. **Environment Variable** (Recommended):
   ```bash
   # In .env file
   POLYGON_API_KEY=your_key_here
   ```

2. **Airflow Connection**:
   - Go to Admin → Connections in Airflow UI
   - Add connection with ID: `polygon_api`
   - Type: `HTTP`
   - Password: `your_api_key`

3. **Airflow Variable** (Fallback):
   - Go to Admin → Variables
   - Key: `polygon_api_key`
   - Value: `your_api_key`

## Troubleshooting

### Common Issues and Solutions

#### DAG Not Showing Up
```bash
# Check DAG syntax
docker exec quant-airflow python /opt/airflow/dags/polygon_data_pipeline.py

# Check Airflow logs
docker-compose logs airflow --tail 50

# Restart Airflow
docker-compose restart airflow
```

#### API Rate Limiting (429 Errors)
- **Free Tier**: 5 requests/minute limit
- **Solution**: Upgrade to unlimited plan or reduce frequency
- **Check**: Current usage at polygon.io dashboard

#### Database Connection Issues
```bash
# Check PostgreSQL health
docker-compose logs postgres

# Test connection
docker exec quant-postgres psql -U quant_user -d quant_data -c "\dt market_data.*"

# Reset database (if needed)
docker-compose down
docker volume rm quant-platform_postgres_data
docker-compose up -d
```

#### Memory Issues
```bash
# Check container resources
docker stats

# Increase Docker memory allocation to 4GB+
# Docker Desktop → Settings → Resources → Memory
```

### Log Locations

```bash
# Airflow logs
docker-compose logs airflow

# PostgreSQL logs  
docker-compose logs postgres

# Individual task logs available in Airflow UI → Logs section
```

## Production Deployment

### Security Hardening

1. **Change Default Passwords**:
   ```yaml
   # In docker-compose.yml
   environment:
     - POSTGRES_PASSWORD=your_secure_password
     - PGADMIN_DEFAULT_PASSWORD=your_admin_password
     - AIRFLOW_ADMIN_PASSWORD=your_airflow_password
   ```

2. **Use Environment Variables**:
   ```bash
   # For production, set these in your environment
   export POLYGON_API_KEY=your_production_key
   export POSTGRES_PASSWORD=secure_password
   ```

3. **Network Security**:
   - Restrict port access with firewall rules
   - Use HTTPS/SSL certificates
   - Consider VPN access for admin interfaces

### EC2 Deployment

```bash
# Launch EC2 instance (t3.medium+ recommended)
# Install Docker and Docker Compose

# Set environment variables
echo "POLYGON_API_KEY=your_key" >> .env

# Deploy
docker-compose up -d

# Set up monitoring
docker-compose exec airflow airflow config list | grep sql_alchemy_conn
```

### AWS Parameter Store Integration

The platform supports AWS Parameter Store for secure API key management:

```bash
# Store API key in AWS Parameter Store
aws ssm put-parameter \
  --name "/quant-platform/polygon-api-key" \
  --value "your_api_key" \
  --type "SecureString"

# Platform will automatically detect and use this
```

## Performance Optimization

### For Large-Scale Operations

1. **Increase Tickers**: Platform tested with 100+ tickers
2. **Parallel Processing**: Modify `max_active_runs` in DAG
3. **Database Tuning**: Adjust PostgreSQL settings for your workload
4. **Resource Scaling**: Use larger EC2 instances or multiple containers

### Monitoring

```bash
# Resource usage
docker stats

# Database performance  
docker exec quant-postgres psql -U quant_user -d quant_data -c "
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'market_data';"
```

## Next Steps

1. **Data Analysis**: Connect Jupyter notebooks to PostgreSQL
2. **Visualization**: Build dashboards with Grafana or Plotly
3. **Strategy Development**: Implement backtesting frameworks
4. **Real-time Data**: Add WebSocket feeds for live updates
5. **Machine Learning**: Create prediction models using collected data

## Support

For issues and questions:
1. Check logs first: `docker-compose logs [service_name]`
2. Review Airflow task logs in the UI
3. Verify API key and quotas at polygon.io
4. Check system resources and Docker allocations

---

**Your quantitative research platform is now ready for serious market analysis!** 📈🚀 