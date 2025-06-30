"""
End-to-End Performance Testing DAG
This DAG demonstrates the complete performance testing workflow:
1. Identify all active trading models
2. Calculate performance metrics for each model
3. Update model performance history
4. Generate performance reports and alerts
5. Rank models by performance

This serves as a blueprint for team development within the layered architecture.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import psycopg2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default arguments for the DAG
default_args = {
    'owner': 'quant-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'end_to_end_performance_testing',
    default_args=default_args,
    description='Performance testing and evaluation for all trading models',
    schedule_interval='0 18 * * 1-5',  # Daily at 6 PM on weekdays
    catchup=False,
    tags=['end-to-end', 'performance', 'models', 'example'],
)

def get_database_connection():
    """Create database connection for performance testing."""
    return create_engine(
        'postgresql://quant_user:quant_password@postgres:5432/quant_data'
    )

def get_active_models(**context):
    """
    Retrieve all active trading models for performance evaluation.
    
    Returns list of model metadata including recent signal statistics.
    """
    try:
        engine = get_database_connection()
        
        # Get models with recent signal activity
        query = """
        SELECT DISTINCT
            s.model_id,
            m.model_name,
            m.model_type as model_type,
            'v1.0' as version,
            COUNT(s.id) as recent_signals,
            MAX(s.created_at) as last_signal_time,
            AVG(s.confidence_score) as avg_confidence
        FROM signals s
        JOIN models m ON s.model_id = m.id
        WHERE s.created_at >= CURRENT_DATE - INTERVAL '30 days'
        AND s.model_id IS NOT NULL
        AND m.is_active = true
        GROUP BY s.model_id, m.model_name, m.model_type
        HAVING COUNT(s.id) >= 5  -- Minimum signals for meaningful analysis
        ORDER BY last_signal_time DESC
        """
        
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        
        # Convert to records and handle datetime serialization
        models = df.to_dict('records')
        
        # Convert Timestamps to strings for JSON serialization
        for model in models:
            for key, value in model.items():
                if hasattr(value, 'isoformat'):  # Check if it's a datetime-like object
                    model[key] = value.isoformat()
                elif pd.isna(value):  # Handle NaN values
                    model[key] = None
        
        logger.info(f"Found {len(models)} active models for performance testing")
        
        # Store in XCom for downstream tasks
        context['task_instance'].xcom_push(key='active_models', value=models)
        
        return models
        
    except Exception as e:
        logger.error(f"Error retrieving active models: {str(e)}")
        raise

def calculate_model_performance(model_id: str, **context):
    """
    Calculate comprehensive performance metrics for a specific model.
    
    Args:
        model_id: Unique identifier for the trading model
    """
    try:
        engine = get_database_connection()
        
        # Get model signals with actual returns
        signals_query = """
        SELECT 
            s.id as signal_id,
            s.ticker,
            s.signal_type,
            1.0 as signal_strength,
            NULL as price_target,
            NULL as stop_loss,
            s.confidence_score as confidence_score,
            s.created_at as signal_time,
            NULL as expected_return,
            
            -- Get actual price data for performance calculation
            md_entry.close_price as entry_price,
            md_exit.close_price as exit_price,
            md_exit.date as exit_date
            
        FROM signals s
        LEFT JOIN market_data md_entry ON (
            s.ticker = md_entry.symbol 
            AND s.signal_date = md_entry.date
        )
        LEFT JOIN market_data md_exit ON (
            s.ticker = md_exit.symbol 
            AND md_exit.date = s.signal_date + INTERVAL '5 days'  -- 5-day holding period
        )
        WHERE s.model_id = %(model_id)s
        AND s.created_at >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY s.created_at DESC
        """
        
        with engine.connect() as conn:
            df = pd.read_sql(signals_query, conn, params={'model_id': model_id})
        
        if df.empty:
            logger.warning(f"No signals found for model {model_id}")
            return None
        
        # Calculate performance metrics
        metrics = {}
        
        # Basic return calculations
        df['actual_return'] = (df['exit_price'] - df['entry_price']) / df['entry_price']
        df['actual_return'] = df['actual_return'].fillna(0)  # Handle missing data
        
        # Adjust returns based on signal type
        df.loc[df['signal_type'] == 'SELL', 'actual_return'] *= -1
        
        # Core performance metrics
        metrics['total_signals'] = len(df)
        metrics['total_return'] = df['actual_return'].sum()
        metrics['avg_return'] = df['actual_return'].mean()
        metrics['win_rate'] = (df['actual_return'] > 0).mean()
        metrics['avg_win'] = df[df['actual_return'] > 0]['actual_return'].mean()
        metrics['avg_loss'] = df[df['actual_return'] < 0]['actual_return'].mean()
        
        # Risk metrics
        metrics['volatility'] = df['actual_return'].std()
        metrics['sharpe_ratio'] = metrics['avg_return'] / metrics['volatility'] if metrics['volatility'] > 0 else 0
        metrics['max_drawdown'] = (df['actual_return'].cumsum() - df['actual_return'].cumsum().cummax()).min()
        
        # Advanced metrics
        metrics['profit_factor'] = abs(df[df['actual_return'] > 0]['actual_return'].sum() / 
                                      df[df['actual_return'] < 0]['actual_return'].sum()) if df[df['actual_return'] < 0]['actual_return'].sum() != 0 else np.inf
        
        # Prediction accuracy (compare expected vs actual returns)
        df['prediction_error'] = abs(df['expected_return'] - df['actual_return'])
        metrics['avg_prediction_error'] = df['prediction_error'].mean()
        metrics['prediction_accuracy'] = 1 - (metrics['avg_prediction_error'] / abs(df['actual_return']).mean()) if abs(df['actual_return']).mean() > 0 else 0
        
        # Confidence-weighted metrics
        df['confidence_weighted_return'] = df['actual_return'] * df['confidence_score']
        metrics['confidence_weighted_avg_return'] = df['confidence_weighted_return'].mean()
        
        # Store performance data
        performance_data = {
            'model_id': model_id,
            'evaluation_date': datetime.now().date(),
            'metrics': metrics,
            'detailed_signals': df[['signal_id', 'ticker', 'actual_return', 'confidence_score']].to_dict('records')
        }
        
        # Save to database
        insert_query = """
        INSERT INTO model_performance (
            model_id, run_date, evaluation_date, total_return,
            avg_return, win_rate, volatility, sharpe_ratio,
            max_drawdown, profit_factor, prediction_accuracy
        ) VALUES (
            :model_id, :run_date, :evaluation_date, :total_return,
            :avg_return, :win_rate, :volatility, :sharpe_ratio,
            :max_drawdown, :profit_factor, :prediction_accuracy
        )
        ON CONFLICT (model_id, run_date) 
        DO UPDATE SET
            evaluation_date = EXCLUDED.evaluation_date,
            total_return = EXCLUDED.total_return,
            avg_return = EXCLUDED.avg_return,
            win_rate = EXCLUDED.win_rate,
            volatility = EXCLUDED.volatility,
            sharpe_ratio = EXCLUDED.sharpe_ratio,
            max_drawdown = EXCLUDED.max_drawdown,
            profit_factor = EXCLUDED.profit_factor,
            prediction_accuracy = EXCLUDED.prediction_accuracy,
            updated_at = CURRENT_TIMESTAMP
        """
        
        params = {
            'model_id': model_id,
            'run_date': datetime.now().date(),
            'evaluation_date': datetime.now().date(),
            'total_return': float(metrics['total_return']),
            'avg_return': float(metrics['avg_return']),
            'win_rate': float(metrics['win_rate']),
            'volatility': float(metrics['volatility']),
            'sharpe_ratio': float(metrics['sharpe_ratio']),
            'max_drawdown': float(metrics['max_drawdown']),
            'profit_factor': float(metrics['profit_factor']) if metrics['profit_factor'] != np.inf else 999.9999,
            'prediction_accuracy': float(metrics['prediction_accuracy'])
        }
        
        with engine.connect() as conn:
            conn.execute(text(insert_query), params)
        
        logger.info(f"Performance calculated for model {model_id}: {metrics['avg_return']:.4f} avg return, {metrics['win_rate']:.2f} win rate")
        
        return performance_data
        
    except Exception as e:
        logger.error(f"Error calculating performance for model {model_id}: {str(e)}")
        raise

def generate_performance_report(**context):
    """
    Generate comprehensive performance report comparing all models.
    """
    try:
        engine = get_database_connection()
        
        # Get latest performance data for all models
        query = """
        SELECT 
            mp.*,
            m.model_name,
            m.model_type as model_type,
            'v1.0' as version,
            ROW_NUMBER() OVER (PARTITION BY mp.model_id ORDER BY mp.evaluation_date DESC) as rn
        FROM model_performance mp
        JOIN models m ON mp.model_id = m.id
        WHERE mp.evaluation_date >= CURRENT_DATE - INTERVAL '7 days'
        AND m.is_active = true
        """
        
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        
        # Filter to latest evaluation for each model
        df = df[df['rn'] == 1].drop('rn', axis=1)
        
        if df.empty:
            logger.warning("No recent performance data found")
            return
        
        # Generate rankings
        df['overall_score'] = (
            df['sharpe_ratio'] * 0.3 +
            df['avg_return'] * 0.25 +
            df['win_rate'] * 0.2 +
            df['prediction_accuracy'] * 0.15 +
            (1 / (1 + abs(df['max_drawdown']))) * 0.1  # Lower drawdown is better
        )
        
        df_ranked = df.sort_values('overall_score', ascending=False).reset_index(drop=True)
        df_ranked['rank'] = df_ranked.index + 1
        
        # Generate summary statistics
        summary = {
            'total_models': len(df_ranked),
            'avg_return_all_models': float(df_ranked['avg_return'].mean()),
            'best_model': {
                'model_id': str(df_ranked.iloc[0]['model_id']),
                'model_name': str(df_ranked.iloc[0]['model_name']),
                'overall_score': float(df_ranked.iloc[0]['overall_score']),
                'avg_return': float(df_ranked.iloc[0]['avg_return']),
                'sharpe_ratio': float(df_ranked.iloc[0]['sharpe_ratio'])
            },
            'worst_model': {
                'model_id': str(df_ranked.iloc[-1]['model_id']),
                'model_name': str(df_ranked.iloc[-1]['model_name']),
                'overall_score': float(df_ranked.iloc[-1]['overall_score']),
                'avg_return': float(df_ranked.iloc[-1]['avg_return'])
            }
        }
        
        # Store performance report with proper serialization
        model_rankings = df_ranked[['rank', 'model_id', 'model_name', 'overall_score', 'avg_return', 'sharpe_ratio', 'win_rate']].to_dict('records')
        
        # Convert all numeric values to native Python types for JSON serialization
        for ranking in model_rankings:
            for key, value in ranking.items():
                if pd.isna(value):
                    ranking[key] = None
                elif hasattr(value, 'item'):  # numpy scalar
                    ranking[key] = value.item()
                elif isinstance(value, (pd.Timestamp, datetime)):
                    ranking[key] = value.isoformat()
        
        report_data = {
            'report_date': datetime.now().date().isoformat(),
            'model_rankings': model_rankings,
            'summary': summary
        }
        
        # Save report to database
        insert_report = """
        INSERT INTO performance_reports (
            report_date, total_models, avg_return_all_models,
            best_model_id, worst_model_id, report_data
        ) VALUES (
            :report_date, :total_models, :avg_return_all_models,
            :best_model_id, :worst_model_id, :report_data
        )
        ON CONFLICT (report_date)
        DO UPDATE SET
            total_models = EXCLUDED.total_models,
            avg_return_all_models = EXCLUDED.avg_return_all_models,
            best_model_id = EXCLUDED.best_model_id,
            worst_model_id = EXCLUDED.worst_model_id,
            report_data = EXCLUDED.report_data,
            updated_at = CURRENT_TIMESTAMP
        """
        
        # Clean NaN values from report_data before JSON serialization
        def clean_nan_values(obj):
            if isinstance(obj, dict):
                return {k: clean_nan_values(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_nan_values(v) for v in obj]
            elif isinstance(obj, float) and (obj != obj):  # NaN check
                return None
            else:
                return obj
        
        clean_report_data = clean_nan_values(report_data)
        
        params = {
            'report_date': datetime.now().date(),
            'total_models': summary['total_models'],
            'avg_return_all_models': float(summary['avg_return_all_models']),
            'best_model_id': summary['best_model']['model_id'],
            'worst_model_id': summary['worst_model']['model_id'],
            'report_data': json.dumps(clean_report_data, default=str)
        }
        
        with engine.connect() as conn:
            conn.execute(text(insert_report), params)
        
        logger.info(f"Performance report generated: {summary['total_models']} models, best: {summary['best_model']['model_name']}")
        
        return report_data
        
    except Exception as e:
        logger.error(f"Error generating performance report: {str(e)}")
        raise

def update_model_rankings(**context):
    """
    Update model rankings and trigger alerts for underperforming models.
    """
    try:
        engine = get_database_connection()
        
        # Get current rankings
        query = """
        SELECT model_id, overall_score, total_return
        FROM (
            SELECT 
                mp.model_id,
                mp.total_return,
                (COALESCE(mp.sharpe_ratio, 0) * 0.4 + COALESCE(mp.total_return, 0) * 0.3 + COALESCE(mp.win_rate, 0) * 0.3 + 
                 (1 / (1 + ABS(COALESCE(mp.max_drawdown, 0)))) * 0.1) as overall_score,
                ROW_NUMBER() OVER (PARTITION BY mp.model_id ORDER BY mp.evaluation_date DESC) as rn
            FROM model_performance mp
            WHERE mp.evaluation_date >= CURRENT_DATE - INTERVAL '7 days'
        ) ranked
        WHERE rn = 1
        ORDER BY overall_score DESC
        """
        
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        
        # Identify models that need attention
        underperforming_models = df[df['total_return'] < -0.02]  # Less than -2% total return
        top_performers = df.head(3)
        
        # Update model status in database
        for idx, model in df.iterrows():
            status = 'active'
            if model['model_id'] in underperforming_models['model_id'].values:
                status = 'underperforming'
            elif model['model_id'] in top_performers['model_id'].values:
                status = 'top_performer'
            
            # Update model status (this would go to a model_status table)
            logger.info(f"Model {model['model_id']}: {status} (score: {model['overall_score']:.4f})")
        
        # Log alerts for underperforming models
        if len(underperforming_models) > 0:
            logger.warning(f"ALERT: {len(underperforming_models)} models are underperforming")
            for _, model in underperforming_models.iterrows():
                logger.warning(f"Underperforming model: {model['model_id']} (return: {model['avg_return']:.4f})")
        
        return {
            'total_models': len(df),
            'underperforming_count': len(underperforming_models),
            'top_performers': top_performers['model_id'].tolist()
        }
        
    except Exception as e:
        logger.error(f"Error updating model rankings: {str(e)}")
        raise

# Task definitions
start_task = DummyOperator(
    task_id='start_performance_testing',
    dag=dag,
)

get_models_task = PythonOperator(
    task_id='get_active_models',
    python_callable=get_active_models,
    dag=dag,
)

# This would be a dynamic task that processes each model
# For simplicity, we'll create a single task that processes all models
calculate_all_performance_task = PythonOperator(
    task_id='calculate_all_model_performance',
    python_callable=lambda **context: [
        calculate_model_performance(model['model_id'], **context)
        for model in context['task_instance'].xcom_pull(task_ids='get_active_models', key='active_models')
    ],
    dag=dag,
)

generate_report_task = PythonOperator(
    task_id='generate_performance_report',
    python_callable=generate_performance_report,
    dag=dag,
)

update_rankings_task = PythonOperator(
    task_id='update_model_rankings',
    python_callable=update_model_rankings,
    dag=dag,
)

end_task = DummyOperator(
    task_id='end_performance_testing',
    dag=dag,
)

# Task dependencies
start_task >> get_models_task >> calculate_all_performance_task >> generate_report_task >> update_rankings_task >> end_task 