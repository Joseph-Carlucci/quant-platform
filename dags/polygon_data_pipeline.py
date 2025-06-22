from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
import pandas as pd
import numpy as np
import requests
import psycopg2
from sqlalchemy import create_engine, text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default arguments for the DAG
default_args = {
    'owner': 'quant-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'polygon_data_pipeline',
    default_args=default_args,
    description='Polygon.io data ingestion pipeline for MVP',
    schedule_interval=timedelta(hours=6),  # Run 4 times per day
    catchup=False,
    tags=['polygon', 'market-data', 'mvp'],
)

# Database connection string
DB_CONN = 'postgresql://quant_user:quant_password@postgres:5432/quant_data'

# Sample tickers for MVP (you can modify this list)
MVP_TICKERS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META', 'SPY']

def get_polygon_api_key():
    """
    Get Polygon.io API key from multiple sources (in order of preference):
    1. Airflow Connection (most secure)
    2. Environment variable 
    3. Airflow Variable (fallback)
    
    For Airflow Connection: Admin -> Connections
    - Conn Id: polygon_api
    - Conn Type: HTTP
    - Password: your_api_key
    
    For Environment Variable: POLYGON_API_KEY
    For Airflow Variable: polygon_api_key
    """
    # Try Airflow Connection first (most secure)
    try:
        from airflow.hooks.base import BaseHook
        conn = BaseHook.get_connection('polygon_api')
        if conn.password:
            return conn.password
    except Exception:
        pass
    
    # Try environment variable second
    import os
    api_key = os.getenv('POLYGON_API_KEY')
    if api_key:
        return api_key
    
    # Fall back to Airflow Variable
    try:
        api_key = Variable.get("polygon_api_key")
        if not api_key:
            raise ValueError("Polygon API key is empty")
        return api_key
    except Exception as e:
        logger.error(f"Failed to get Polygon API key: {e}")
        logger.info("Please set up the API key using one of these methods:")
        logger.info("1. Airflow Connection (RECOMMENDED): Admin -> Connections")
        logger.info("   - Conn Id: polygon_api")
        logger.info("   - Conn Type: HTTP") 
        logger.info("   - Password: your_api_key")
        logger.info("2. Environment Variable: POLYGON_API_KEY")
        logger.info("3. Airflow Variable: polygon_api_key")
        logger.info("Get your free API key at: https://polygon.io/")
        raise

def create_market_data_tables():
    """Create necessary tables if they don't exist"""
    engine = create_engine(DB_CONN)
    
    # Daily aggregates table
    daily_aggs_sql = """
    CREATE TABLE IF NOT EXISTS market_data.daily_aggregates (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(10) NOT NULL,
        date DATE NOT NULL,
        open_price DECIMAL(10,2),
        high_price DECIMAL(10,2),
        low_price DECIMAL(10,2),
        close_price DECIMAL(10,2),
        volume BIGINT,
        vwap DECIMAL(10,4),
        timestamp_utc BIGINT,
        transactions INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(ticker, date)
    );
    """
    
    # Previous close table
    prev_close_sql = """
    CREATE TABLE IF NOT EXISTS market_data.previous_close (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(10) NOT NULL,
        date DATE NOT NULL,
        close_price DECIMAL(10,2),
        open_price DECIMAL(10,2),
        high_price DECIMAL(10,2),
        low_price DECIMAL(10,2),
        volume BIGINT,
        pre_market DECIMAL(10,2),
        after_hours DECIMAL(10,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(ticker, date)
    );
    """
    
    # Ticker details table
    ticker_details_sql = """
    CREATE TABLE IF NOT EXISTS market_data.ticker_details (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(10) NOT NULL UNIQUE,
        name VARCHAR(255),
        market VARCHAR(50),
        locale VARCHAR(10),
        primary_exchange VARCHAR(10),
        type VARCHAR(20),
        currency_name VARCHAR(50),
        market_cap BIGINT,
        share_class_outstanding BIGINT,
        weighted_shares_outstanding BIGINT,
        description TEXT,
        homepage_url VARCHAR(255),
        total_employees INTEGER,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    with engine.begin() as conn:
        conn.execute(text(daily_aggs_sql))
        conn.execute(text(prev_close_sql))
        conn.execute(text(ticker_details_sql))
    
    logger.info("Market data tables created successfully")

def fetch_previous_close_data(**context):
    """Fetch previous close data for MVP tickers"""
    api_key = get_polygon_api_key()
    
    all_data = []
    
    for ticker in MVP_TICKERS:
        try:
            url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/prev"
            params = {
                'adjusted': 'true',
                'apikey': api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('results'):
                result = data['results'][0]
                
                # Convert timestamp to date
                from datetime import datetime
                date = datetime.fromtimestamp(result['t'] / 1000).date()
                
                record = {
                    'ticker': ticker,
                    'date': date,
                    'close_price': result.get('c'),
                    'open_price': result.get('o'),
                    'high_price': result.get('h'),
                    'low_price': result.get('l'),
                    'volume': result.get('v'),
                    'pre_market': None,  # Not available in this endpoint
                    'after_hours': None  # Not available in this endpoint
                }
                
                all_data.append(record)
                logger.info(f"Fetched previous close for {ticker}: ${result.get('c')}")
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            continue
    
    # Store data in database
    if all_data:
        df = pd.DataFrame(all_data)
        
        # Clean the data: replace NaN values with None and handle data types
        df = df.replace({pd.NA: None, pd.NaT: None})
        df = df.where(pd.notnull(df), None)
        
        engine = create_engine(DB_CONN)
        
        # Use individual upsert statements to handle duplicates properly
        with engine.begin() as conn:
            for _, row in df.iterrows():
                upsert_sql = text("""
                INSERT INTO market_data.previous_close 
                (ticker, date, close_price, open_price, high_price, low_price, volume, pre_market, after_hours)
                VALUES (:ticker, :date, :close_price, :open_price, :high_price, :low_price, :volume, :pre_market, :after_hours)
                ON CONFLICT (ticker, date) 
                DO UPDATE SET 
                    close_price = EXCLUDED.close_price,
                    open_price = EXCLUDED.open_price,
                    high_price = EXCLUDED.high_price,
                    low_price = EXCLUDED.low_price,
                    volume = EXCLUDED.volume,
                    pre_market = EXCLUDED.pre_market,
                    after_hours = EXCLUDED.after_hours,
                    created_at = CURRENT_TIMESTAMP;
                """)
                
                conn.execute(upsert_sql, {
                    'ticker': row['ticker'],
                    'date': row['date'],
                    'close_price': row['close_price'],
                    'open_price': row['open_price'],
                    'high_price': row['high_price'],
                    'low_price': row['low_price'],
                    'volume': row['volume'],
                    'pre_market': row['pre_market'],
                    'after_hours': row['after_hours']
                })
        
        logger.info(f"Stored/updated {len(all_data)} previous close records")
    
    return len(all_data)

def fetch_daily_aggregates(**context):
    """Fetch daily aggregates for the last few days"""
    api_key = get_polygon_api_key()
    
    # Get date range (last 5 business days)
    from datetime import datetime, timedelta
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)  # Get a week's worth to ensure we have business days
    
    all_data = []
    
    for ticker in MVP_TICKERS:
        try:
            url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
            params = {
                'adjusted': 'true',
                'sort': 'asc',
                'apikey': api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('results'):
                for result in data['results']:
                    # Convert timestamp to date
                    date = datetime.fromtimestamp(result['t'] / 1000).date()
                    
                    record = {
                        'ticker': ticker,
                        'date': date,
                        'open_price': result.get('o'),
                        'high_price': result.get('h'),
                        'low_price': result.get('l'),
                        'close_price': result.get('c'),
                        'volume': result.get('v'),
                        'vwap': result.get('vw'),
                        'timestamp_utc': result.get('t'),
                        'transactions': result.get('n')
                    }
                    
                    all_data.append(record)
                
                logger.info(f"Fetched {len(data['results'])} daily records for {ticker}")
            
        except Exception as e:
            logger.error(f"Error fetching daily aggregates for {ticker}: {e}")
            continue
    
    # Store data in database
    if all_data:
        df = pd.DataFrame(all_data)
        
        # Clean the data: replace NaN values with None and handle data types
        df = df.replace({pd.NA: None, pd.NaT: None})
        df = df.where(pd.notnull(df), None)
        
        engine = create_engine(DB_CONN)
        
        # Handle duplicates by updating existing records
        df.to_sql('daily_aggregates', engine, schema='market_data', 
                 if_exists='append', index=False, method='multi')
        
        logger.info(f"Stored {len(all_data)} daily aggregate records")
    
    return len(all_data)

def fetch_ticker_details(**context):
    """Fetch ticker details for MVP tickers"""
    api_key = get_polygon_api_key()
    
    all_data = []
    
    for ticker in MVP_TICKERS:
        try:
            url = f"https://api.polygon.io/v3/reference/tickers/{ticker}"
            params = {'apikey': api_key}
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('results'):
                result = data['results']
                
                record = {
                    'ticker': ticker,
                    'name': result.get('name'),
                    'market': result.get('market'),
                    'locale': result.get('locale'),
                    'primary_exchange': result.get('primary_exchange'),
                    'type': result.get('type'),
                    'currency_name': result.get('currency_name'),
                    'market_cap': result.get('market_cap'),
                    'share_class_outstanding': result.get('share_class_shares_outstanding'),
                    'weighted_shares_outstanding': result.get('weighted_shares_outstanding'),
                    'description': result.get('description'),
                    'homepage_url': result.get('homepage_url'),
                    'total_employees': result.get('total_employees')
                }
                
                all_data.append(record)
                logger.info(f"Fetched details for {ticker}: {result.get('name')}")
            
        except Exception as e:
            logger.error(f"Error fetching details for {ticker}: {e}")
            continue
    
    # Store data in database
    if all_data:
        df = pd.DataFrame(all_data)
        
        # Clean the data: replace NaN values with None and handle data types
        df = df.replace({pd.NA: None, pd.NaT: None})
        df = df.where(pd.notnull(df), None)
        
        # Additional cleaning for numeric fields that might have NaN
        numeric_cols = ['market_cap', 'share_class_outstanding', 'weighted_shares_outstanding', 'total_employees']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].replace([np.inf, -np.inf, np.nan], None)
        
        engine = create_engine(DB_CONN)
        
        # Use individual upsert statements to handle duplicates properly
        with engine.begin() as conn:
            for _, row in df.iterrows():
                upsert_sql = text("""
                INSERT INTO market_data.ticker_details 
                (ticker, name, market, locale, primary_exchange, type, currency_name, market_cap, 
                 share_class_outstanding, weighted_shares_outstanding, description, homepage_url, total_employees)
                VALUES (:ticker, :name, :market, :locale, :primary_exchange, :type, :currency_name, :market_cap,
                        :share_class_outstanding, :weighted_shares_outstanding, :description, :homepage_url, :total_employees)
                ON CONFLICT (ticker) 
                DO UPDATE SET 
                    name = EXCLUDED.name,
                    market = EXCLUDED.market,
                    locale = EXCLUDED.locale,
                    primary_exchange = EXCLUDED.primary_exchange,
                    type = EXCLUDED.type,
                    currency_name = EXCLUDED.currency_name,
                    market_cap = EXCLUDED.market_cap,
                    share_class_outstanding = EXCLUDED.share_class_outstanding,
                    weighted_shares_outstanding = EXCLUDED.weighted_shares_outstanding,
                    description = EXCLUDED.description,
                    homepage_url = EXCLUDED.homepage_url,
                    total_employees = EXCLUDED.total_employees,
                    updated_at = CURRENT_TIMESTAMP;
                """)
                
                conn.execute(upsert_sql, {
                    'ticker': row['ticker'],
                    'name': row['name'],
                    'market': row['market'],
                    'locale': row['locale'],
                    'primary_exchange': row['primary_exchange'],
                    'type': row['type'],
                    'currency_name': row['currency_name'],
                    'market_cap': row['market_cap'],
                    'share_class_outstanding': row['share_class_outstanding'],
                    'weighted_shares_outstanding': row['weighted_shares_outstanding'],
                    'description': row['description'],
                    'homepage_url': row['homepage_url'],
                    'total_employees': row['total_employees']
                })
        
        logger.info(f"Stored/updated {len(all_data)} ticker detail records")
    
    return len(all_data)

# Define tasks
create_tables_task = PythonOperator(
    task_id='create_tables',
    python_callable=create_market_data_tables,
    dag=dag,
)

fetch_previous_close_task = PythonOperator(
    task_id='fetch_previous_close',
    python_callable=fetch_previous_close_data,
    dag=dag,
)

fetch_daily_aggs_task = PythonOperator(
    task_id='fetch_daily_aggregates', 
    python_callable=fetch_daily_aggregates,
    dag=dag,
)

fetch_ticker_details_task = PythonOperator(
    task_id='fetch_ticker_details',
    python_callable=fetch_ticker_details,
    dag=dag,
)

# Define task dependencies
create_tables_task >> [fetch_previous_close_task, fetch_daily_aggs_task, fetch_ticker_details_task] 