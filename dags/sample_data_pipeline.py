from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

# Default arguments for the DAG
default_args = {
    'owner': 'quant-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'sample_data_pipeline',
    default_args=default_args,
    description='Sample data ingestion pipeline for quant research',
    schedule_interval=timedelta(hours=1),
    catchup=False,
    tags=['sample', 'data-ingestion'],
)

def check_database_connection():
    """Test connection to the quant database"""
    try:
        engine = create_engine('postgresql://quant_user:quant_password@postgres:5432/quant_data')
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("Database connection successful!")
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise

def sample_data_fetch():
    """Sample function to demonstrate data fetching"""
    # This is where you would fetch data from APIs like Alpha Vantage, Yahoo Finance, etc.
    print("Fetching sample market data...")
    
    # Sample data creation (replace with actual API calls)
    sample_data = {
        'timestamp': [datetime.now()],
        'symbol': ['AAPL'],
        'price': [150.00],
        'volume': [1000000]
    }
    
    df = pd.DataFrame(sample_data)
    print(f"Fetched {len(df)} records")
    return df.to_json()

def store_market_data(**context):
    """Store fetched data in the database"""
    # Get data from previous task
    data_json = context['task_instance'].xcom_pull(task_ids='fetch_data')
    df = pd.read_json(data_json)
    
    # Store in database
    engine = create_engine('postgresql://quant_user:quant_password@postgres:5432/quant_data')
    df.to_sql('sample_prices', engine, schema='market_data', if_exists='append', index=False)
    print(f"Stored {len(df)} records in market_data.sample_prices")

# Define tasks
check_db_task = PythonOperator(
    task_id='check_database',
    python_callable=check_database_connection,
    dag=dag,
)

fetch_data_task = PythonOperator(
    task_id='fetch_data',
    python_callable=sample_data_fetch,
    dag=dag,
)

store_data_task = PythonOperator(
    task_id='store_data',
    python_callable=store_market_data,
    dag=dag,
)

# Define task dependencies
check_db_task >> fetch_data_task >> store_data_task 