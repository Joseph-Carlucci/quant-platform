"""
End-to-End Data Ingestion DAG

This DAG demonstrates the complete data ingestion workflow:
1. Fetch market data from Polygon API
2. Calculate technical indicators and features
3. Update trading universe
4. Prepare data for model consumption

This serves as a blueprint for team development within the layered architecture.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

import pandas as pd
import numpy as np
import requests
import logging
from pathlib import Path
import sys
import json
import random
import os
from sqlalchemy import create_engine, text

# Add project root to path for imports
sys.path.append('/opt/airflow/dags/quant-platform')

logger = logging.getLogger(__name__)

# DAG Configuration
DAG_ID = "end_to_end_data_ingestion"
SCHEDULE_INTERVAL = "0 18 * * 1-5"  # 6 PM weekdays (after market close)
START_DATE = datetime(2024, 1, 1)

# Configuration
POSTGRES_CONN_STRING = "postgresql://quant_user:quant_password@postgres:5432/quant_data"
UNIVERSE_SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX", "ADBE", "CRM",
    "ORCL", "AMD", "INTC", "QCOM", "BKNG", "CMCSA", "AVGO", "TXN", "HON", "UNP"
]

default_args = {
    'owner': 'quant-team',
    'depends_on_past': False,
    'start_date': START_DATE,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'max_active_runs': 1,
}

def fetch_market_data(**context) -> Dict[str, Any]:
    """
    Fetch market data from Polygon API for the trading universe.
    
    This function demonstrates:
    - External API integration
    - Error handling and retry logic
    - Data quality validation
    - Database integration using the data layer
    """
    logger.info(f"Context type: {type(context)}, Context: {context}")
    execution_date = context.get('ds', '2025-06-27')
    logger.info(f"Fetching market data for {execution_date}")
    
    # Get database connection
    logger.info(f"Using connection string: {POSTGRES_CONN_STRING}")
    engine = create_engine(POSTGRES_CONN_STRING)
    
    # Test connection
    with engine.connect() as test_conn:
        result = test_conn.execute(text("SELECT current_database(), current_user"))
        db_name, db_user = result.fetchone()
        logger.info(f"Connected to database: {db_name} as user: {db_user}")
        
        # Check if technical_indicators table exists
        table_check = test_conn.execute(text("SELECT EXISTS(SELECT FROM information_schema.tables WHERE table_name='technical_indicators')"))
        table_exists = table_check.fetchone()[0]
        logger.info(f"technical_indicators table exists: {table_exists}")
    
    # Get API key from environment variable
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        logger.error("POLYGON_API_KEY not found in environment variables. Please set it in your .env file.")
        raise ValueError("Missing POLYGON_API_KEY environment variable")
    
    # Prepare data for batch insert
    market_data_records = []
    failed_symbols = []
    
    for symbol in UNIVERSE_SYMBOLS:
        try:
            # Fetch data from Polygon API
            url = f"https://api.polygon.io/v1/open-close/{symbol}/{execution_date}"
            params = {"apikey": api_key}
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"API response for {symbol}: {data}")
            
            # Validate data quality
            if isinstance(data, dict) and data.get('status') == 'OK' and all(key in data for key in ['open', 'high', 'low', 'close', 'volume']):
                market_data_records.append({
                    'symbol': symbol,
                    'date': execution_date,
                    'open_price': float(data['open']),
                    'high_price': float(data['high']),
                    'low_price': float(data['low']),
                    'close_price': float(data['close']),
                    'volume': int(data['volume'])
                })
                logger.info(f"Successfully fetched data for {symbol}")
            else:
                logger.warning(f"Invalid data received for {symbol}: {data}")
                failed_symbols.append(symbol)
                
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            failed_symbols.append(symbol)
    
    # Batch insert market data
    if market_data_records:
        with engine.begin() as conn:
            for value in market_data_records:
                conn.execute(
                    text("INSERT INTO market_data (symbol, date, open_price, high_price, low_price, close_price, volume) VALUES (:symbol, :date, :open_price, :high_price, :low_price, :close_price, :volume) ON CONFLICT (symbol, date) DO UPDATE SET open_price = EXCLUDED.open_price, high_price = EXCLUDED.high_price, low_price = EXCLUDED.low_price, close_price = EXCLUDED.close_price, volume = EXCLUDED.volume"),
                    {
                        'symbol': value['symbol'], 
                        'date': value['date'], 
                        'open_price': value['open_price'], 
                        'high_price': value['high_price'], 
                        'low_price': value['low_price'], 
                        'close_price': value['close_price'], 
                        'volume': value['volume']
                    }
                )
        logger.info(f"Inserted {len(market_data_records)} market data records")
    
    # Update task metrics
    return {
        'total_symbols': len(UNIVERSE_SYMBOLS),
        'successful_symbols': len(market_data_records),
        'failed_symbols': len(failed_symbols),
        'failed_symbol_list': failed_symbols,
        'execution_date': execution_date
    }

def calculate_technical_indicators(**context) -> Dict[str, Any]:
    """
    Calculate technical indicators and features using the data layer.
    
    This function demonstrates:
    - Usage of the data_layer.features module
    - Bulk feature calculation and storage
    - Integration with the layered architecture
    """
    execution_date = context['ds']
    logger.info(f"Calculating technical features for {execution_date}")
    
    logger.info(f"Using connection string: {POSTGRES_CONN_STRING}")
    engine = create_engine(POSTGRES_CONN_STRING)
    
    # Test connection
    with engine.connect() as test_conn:
        result = test_conn.execute(text("SELECT current_database(), current_user"))
        db_name, db_user = result.fetchone()
        logger.info(f"Connected to database: {db_name} as user: {db_user}")
        
        # Check if technical_indicators table exists
        table_check = test_conn.execute(text("SELECT EXISTS(SELECT FROM information_schema.tables WHERE table_name='technical_indicators')"))
        table_exists = table_check.fetchone()[0]
        logger.info(f"technical_indicators table exists: {table_exists}")
    
    # Get recent market data for feature calculation (last 60 days)
    lookback_date = (datetime.strptime(execution_date, '%Y-%m-%d') - timedelta(days=60)).strftime('%Y-%m-%d')
    
    market_data_sql = """
    SELECT symbol, date, open_price, high_price, low_price, close_price, volume
    FROM market_data 
    WHERE date >= %(lookback_date)s AND date <= %(execution_date)s
    ORDER BY symbol, date
    """
    
    with engine.connect() as conn:
        df = pd.read_sql(market_data_sql, conn, params={'lookback_date': lookback_date, 'execution_date': execution_date})
    
    if df.empty:
        logger.warning("No market data found for feature calculation")
        return {'features_calculated': 0}
    
    all_features = []
    
    # Calculate features for each symbol
    for symbol in df['symbol'].unique():
        symbol_data = df[df['symbol'] == symbol].copy()
        symbol_data = symbol_data.sort_values('date')
        
        if len(symbol_data) < 20:  # Need minimum data for features
            logger.warning(f"Insufficient data for {symbol}, skipping feature calculation")
            continue
        
        try:
            # Calculate various technical indicators
            # RSI
            delta = symbol_data['close_price'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Moving averages
            sma_10 = symbol_data['close_price'].rolling(window=10).mean()
            sma_20 = symbol_data['close_price'].rolling(window=20).mean()
            sma_50 = symbol_data['close_price'].rolling(window=50).mean()
            ema_12 = symbol_data['close_price'].ewm(span=12).mean()
            ema_26 = symbol_data['close_price'].ewm(span=26).mean()
            
            # MACD
            macd = ema_12 - ema_26
            macd_signal = macd.ewm(span=9).mean()
            macd_histogram = macd - macd_signal
            
            # Bollinger Bands
            bb_middle = symbol_data['close_price'].rolling(window=20).mean()
            bb_std = symbol_data['close_price'].rolling(window=20).std()
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            
            # Volume indicators
            volume_ma_20 = symbol_data['volume'].rolling(window=20).mean()
            volume_ratio = symbol_data['volume'] / volume_ma_20
            
            # Price momentum
            momentum_5 = symbol_data['close_price'] / symbol_data['close_price'].shift(5) - 1
            momentum_10 = symbol_data['close_price'] / symbol_data['close_price'].shift(10) - 1
            
            # Volatility
            returns = symbol_data['close_price'].pct_change()
            volatility_20 = returns.rolling(window=20).std() * np.sqrt(252)
            
            # Store features in feature store
            latest_date = symbol_data['date'].max().strftime('%Y-%m-%d')
            if latest_date == execution_date:
                features_data = {
                    'rsi_14': float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None,
                    'sma_20': float(sma_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else None,
                    'sma_50': float(sma_50.iloc[-1]) if not pd.isna(sma_50.iloc[-1]) else None,
                    'ema_12': float(ema_12.iloc[-1]) if not pd.isna(ema_12.iloc[-1]) else None,
                    'ema_26': float(ema_26.iloc[-1]) if not pd.isna(ema_26.iloc[-1]) else None,
                    'macd': float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else None,
                    'macd_signal': float(macd_signal.iloc[-1]) if not pd.isna(macd_signal.iloc[-1]) else None,
                    'bb_upper': float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else None,
                    'bb_lower': float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else None,
                    'volume_ratio': float(volume_ratio.iloc[-1]) if not pd.isna(volume_ratio.iloc[-1]) else None
                }
                
                all_features.append({
                    'symbol': symbol,
                    'date': execution_date,
                    'feature_set': 'technical_v1',
                    'features': features_data
                })
        
        except Exception as e:
            logger.error(f"Error calculating features for {symbol}: {e}")
    
    # Batch insert features
    if all_features:
        with engine.begin() as conn:
            for feature in all_features:
                features_data = feature['features']
                conn.execute(
                    text("""INSERT INTO technical_indicators (symbol, date, rsi_14, sma_20, sma_50, ema_12, ema_26, macd_line, macd_signal, bb_upper, bb_lower, volume_ratio) 
                         VALUES (:symbol, :date, :rsi_14, :sma_20, :sma_50, :ema_12, :ema_26, :macd, :macd_signal, :bb_upper, :bb_lower, :volume_ratio) 
                         ON CONFLICT (symbol, date) DO UPDATE SET 
                         rsi_14 = EXCLUDED.rsi_14, sma_20 = EXCLUDED.sma_20, sma_50 = EXCLUDED.sma_50, 
                         ema_12 = EXCLUDED.ema_12, ema_26 = EXCLUDED.ema_26, macd_line = EXCLUDED.macd_line, 
                         macd_signal = EXCLUDED.macd_signal, bb_upper = EXCLUDED.bb_upper, bb_lower = EXCLUDED.bb_lower, 
                         volume_ratio = EXCLUDED.volume_ratio, updated_at = CURRENT_TIMESTAMP"""),
                    {
                        'symbol': feature['symbol'], 
                        'date': feature['date'], 
                        'rsi_14': features_data.get('rsi_14'),
                        'sma_20': features_data.get('sma_20'),
                        'sma_50': features_data.get('sma_50'),
                        'ema_12': features_data.get('ema_12'),
                        'ema_26': features_data.get('ema_26'),
                        'macd': features_data.get('macd'),
                        'macd_signal': features_data.get('macd_signal'),
                        'bb_upper': features_data.get('bb_upper'),
                        'bb_lower': features_data.get('bb_lower'),
                        'volume_ratio': features_data.get('volume_ratio')
                    }
                )
        logger.info(f"Inserted {len(all_features)} feature records")
    
    return {
        'features_calculated': len(all_features),
        'symbols_processed': len(df['symbol'].unique()),
        'execution_date': execution_date
    }

def update_trading_universe(**context) -> Dict[str, Any]:
    """
    Update the trading universe with current symbols and metadata.
    
    This function demonstrates:
    - Universe management
    - Metadata storage
    - Data quality checks
    """
    logger.info("Updating trading universe")
    
    engine = create_engine(POSTGRES_CONN_STRING)
    
    # Define universe with metadata
    universe_data = [
        {'symbol': 'AAPL', 'company_name': 'Apple Inc.', 'sector': 'Technology'},
        {'symbol': 'MSFT', 'company_name': 'Microsoft Corporation', 'sector': 'Technology'},
        {'symbol': 'GOOGL', 'company_name': 'Alphabet Inc.', 'sector': 'Technology'},
        {'symbol': 'AMZN', 'company_name': 'Amazon.com Inc.', 'sector': 'Consumer Discretionary'},
        {'symbol': 'NVDA', 'company_name': 'NVIDIA Corporation', 'sector': 'Technology'},
        {'symbol': 'META', 'company_name': 'Meta Platforms Inc.', 'sector': 'Technology'},
        {'symbol': 'TSLA', 'company_name': 'Tesla Inc.', 'sector': 'Consumer Discretionary'},
        {'symbol': 'NFLX', 'company_name': 'Netflix Inc.', 'sector': 'Communication Services'},
        {'symbol': 'ADBE', 'company_name': 'Adobe Inc.', 'sector': 'Technology'},
        {'symbol': 'CRM', 'company_name': 'Salesforce Inc.', 'sector': 'Technology'},
    ]
    
    # Insert or update universe
    with engine.begin() as conn:
        for u in universe_data:
            conn.execute(
                text("INSERT INTO trading_universe (symbol, sector, is_active) VALUES (:symbol, :sector, :is_active) ON CONFLICT (symbol) DO UPDATE SET sector = EXCLUDED.sector, is_active = EXCLUDED.is_active, last_updated = CURRENT_TIMESTAMP"),
                {
                    'symbol': u['symbol'], 
                    'sector': u['sector'], 
                    'is_active': True
                }
            )
    logger.info(f"Updated universe with {len(universe_data)} symbols")
    
    return {
        'universe_size': len(universe_data),
        'symbols': [u['symbol'] for u in universe_data]
    }

def validate_data_quality(**context) -> Dict[str, Any]:
    """
    Perform data quality checks on ingested data.
    
    This function demonstrates:
    - Data quality validation
    - Alerting for data issues
    - Quality metrics collection
    """
    execution_date = context['ds']
    logger.info(f"Validating data quality for {execution_date}")
    
    engine = create_engine(POSTGRES_CONN_STRING)
    
    quality_checks = {}
    
    # Check 1: Market data completeness
    market_data_count_sql = """
    SELECT COUNT(*) as count 
    FROM market_data 
    WHERE date = %(execution_date)s
    """
    with engine.connect() as conn:
        result = pd.read_sql(market_data_count_sql, conn, params={'execution_date': execution_date})
        market_data_count = result.iloc[0]['count']
    expected_count = len(UNIVERSE_SYMBOLS)
    
    quality_checks['market_data_completeness'] = {
        'expected': expected_count,
        'actual': market_data_count,
        'percentage': (market_data_count / expected_count) * 100 if expected_count > 0 else 0,
        'status': 'pass' if market_data_count >= expected_count * 0.8 else 'fail'
    }
    
    # Check 2: Features completeness
    features_count_sql = """
    SELECT COUNT(DISTINCT symbol) as count 
    FROM technical_indicators 
    WHERE date = %(execution_date)s
    """
    with engine.connect() as conn:
        result = pd.read_sql(features_count_sql, conn, params={'execution_date': execution_date})
        features_count = result.iloc[0]['count']
    
    quality_checks['features_completeness'] = {
        'expected': expected_count,
        'actual': features_count,
        'percentage': (features_count / expected_count) * 100 if expected_count > 0 else 0,
        'status': 'pass' if features_count >= expected_count * 0.8 else 'fail'
    }
    
    # Check 3: Data freshness
    latest_data_sql = """
    SELECT MAX(date) as latest_date 
    FROM market_data
    """
    with engine.connect() as conn:
        result = pd.read_sql(latest_data_sql, conn)
        latest_date = result['latest_date'].iloc[0]
    days_since_latest = (datetime.strptime(execution_date, '%Y-%m-%d').date() - latest_date).days if latest_date else 999
    
    quality_checks['data_freshness'] = {
        'latest_date': str(latest_date) if latest_date else None,
        'days_since_latest': days_since_latest,
        'status': 'pass' if days_since_latest <= 1 else 'fail'
    }
    
    # Overall quality score
    passed_checks = sum(1 for check in quality_checks.values() if check['status'] == 'pass')
    total_checks = len(quality_checks)
    overall_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
    
    logger.info(f"Data quality validation completed. Overall score: {overall_score:.1f}%")
    
    # Alert if quality is poor
    if overall_score < 80:
        logger.error(f"Data quality below threshold: {overall_score:.1f}%")
        # In production, this would trigger alerts to the team
    
    return {
        'overall_score': overall_score,
        'quality_checks': quality_checks,
        'execution_date': execution_date
    }

# Create the DAG
dag = DAG(
    DAG_ID,
    default_args=default_args,
    description='End-to-end data ingestion pipeline demonstrating layered architecture usage',
    schedule_interval=SCHEDULE_INTERVAL,
    max_active_runs=1,
    catchup=False,
    tags=['end-to-end', 'data-ingestion', 'example'],
)

# Task 1: Initialize database schema (commented out since schema is already initialized)
# init_schema = PostgresOperator(
#     task_id='init_database_schema',
#     postgres_conn_id=POSTGRES_CONN_ID,
#     sql='/opt/airflow/dags/quant-platform/data_layer/storage/schema.sql',
#     dag=dag,
# )

# Task 2: Update trading universe
update_universe = PythonOperator(
    task_id='update_trading_universe',
    python_callable=update_trading_universe,
    dag=dag,
)

# Task 3: Fetch market data
fetch_data = PythonOperator(
    task_id='fetch_market_data',
    python_callable=fetch_market_data,
    dag=dag,
)

# Task 4: Calculate technical features
calculate_features = PythonOperator(
    task_id='calculate_technical_indicators',
    python_callable=calculate_technical_indicators,
    dag=dag,
)

# Task 5: Validate data quality
validate_quality = PythonOperator(
    task_id='validate_data_quality',
    python_callable=validate_data_quality,
    dag=dag,
)

# Task 6: Data ingestion summary
data_summary = BashOperator(
    task_id='data_ingestion_summary',
    bash_command="""
    echo "Data ingestion completed for {{ ds }}"
    echo "Pipeline demonstrates:"
    echo "- External API integration (Polygon)"
    echo "- Technical indicator calculation"
    echo "- Database operations using layered architecture"
    echo "- Data quality validation"
    echo "- Error handling and monitoring"
    """,
    dag=dag,
)

# Define task dependencies
# init_schema >> update_universe >> fetch_data >> calculate_features >> validate_quality >> data_summary
update_universe >> fetch_data >> calculate_features >> validate_quality >> data_summary