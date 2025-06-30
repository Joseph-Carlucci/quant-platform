-- Unified Quantitative Research Platform Database Schema
-- This script provides a single source of truth for both dev and prod environments
-- Last updated: 2025-06-30

-- Set postgres superuser password from environment variable
-- Note: This will be executed via psql with environment variable substitution

-- Create databases if they don't exist
SELECT 'CREATE DATABASE airflow' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow');
SELECT 'CREATE DATABASE quant_data' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'quant_data');

-- Create airflow user if it doesn't exist
DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'airflow') THEN
      CREATE USER airflow WITH PASSWORD 'airflow';
   END IF;
END
$do$;

-- Create quant_user if it doesn't exist
DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'quant_user') THEN
      CREATE USER quant_user WITH PASSWORD 'quant_password';
   END IF;
END
$do$;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
GRANT ALL PRIVILEGES ON DATABASE quant_data TO quant_user;
GRANT ALL PRIVILEGES ON DATABASE quant_data TO postgres;

-- Connect to quant_data database to create tables
\c quant_data;

-- Market Data Tables
CREATE TABLE IF NOT EXISTS market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open_price DECIMAL(10,4),
    high_price DECIMAL(10,4),
    low_price DECIMAL(10,4),
    close_price DECIMAL(10,4),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);

-- UPDATED: Technical Indicators Table (replacing technical_features)
-- This table now uses individual columns instead of JSONB for better performance and clarity
CREATE TABLE IF NOT EXISTS technical_indicators (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    -- RSI indicators
    rsi_14 DECIMAL(6,3),
    -- Moving averages
    sma_20 DECIMAL(10,4),
    sma_50 DECIMAL(10,4),
    ema_12 DECIMAL(10,4),
    ema_26 DECIMAL(10,4),
    -- MACD indicators
    macd_line DECIMAL(10,6),
    macd_signal DECIMAL(10,6),
    macd_histogram DECIMAL(10,6),
    -- Bollinger Bands
    bb_upper DECIMAL(10,4),
    bb_lower DECIMAL(10,4),
    bb_middle DECIMAL(10,4),
    -- Volume indicators
    volume_ratio DECIMAL(6,3),
    -- Momentum indicators
    momentum_5 DECIMAL(8,4),
    momentum_10 DECIMAL(8,4),
    -- Volatility
    volatility_20 DECIMAL(8,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);

-- UPDATED: Models Table with corrected column names
CREATE TABLE IF NOT EXISTS models (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL UNIQUE,
    model_version VARCHAR(20) DEFAULT '1.0.0',
    model_type VARCHAR(50) NOT NULL,  -- Changed from strategy_type
    strategy_class VARCHAR(200),
    parameters JSONB,
    description TEXT,
    created_by VARCHAR(100),
    is_active BOOLEAN DEFAULT true,   -- Changed from status VARCHAR to is_active BOOLEAN
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- UPDATED: Signals Table with corrected column names
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    model_run_id INTEGER,
    model_id INTEGER REFERENCES models(id),
    ticker VARCHAR(10) NOT NULL,      -- Changed from symbol to ticker
    signal_date DATE NOT NULL,
    signal_time TIMESTAMP,
    signal_type INTEGER NOT NULL,     -- Changed to INTEGER: 1 = buy, -1 = sell, 0 = hold
    signal_strength DECIMAL(4,3),
    target_price DECIMAL(10,4),
    stop_loss DECIMAL(10,4),
    confidence_score DECIMAL(4,3),    -- Changed from confidence to confidence_score
    signal_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- UPDATED: Model Performance Table with additional fields
CREATE TABLE IF NOT EXISTS model_performance (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES models(id),
    run_date DATE NOT NULL,
    evaluation_date DATE NOT NULL,
    total_return DECIMAL(8,4),
    avg_return DECIMAL(8,4),
    win_rate DECIMAL(5,4),
    avg_win DECIMAL(8,4),
    avg_loss DECIMAL(8,4),
    volatility DECIMAL(8,4),
    sharpe_ratio DECIMAL(6,4),
    max_drawdown DECIMAL(6,4),
    profit_factor DECIMAL(8,4),
    prediction_accuracy DECIMAL(5,4),
    total_trades INTEGER,
    evaluation_period_days INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_id, run_date)
);

-- Model Runs Table (for tracking individual model executions)
CREATE TABLE IF NOT EXISTS model_runs (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES models(id),
    run_date DATE NOT NULL,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    universe_size INTEGER,
    signals_generated INTEGER DEFAULT 0,
    error_message TEXT,
    execution_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance Reports Table
CREATE TABLE IF NOT EXISTS performance_reports (
    id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL UNIQUE,
    total_models INTEGER,
    avg_return_all_models DECIMAL(8,4),
    best_model_id INTEGER,
    worst_model_id INTEGER,
    report_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trading Universe Table
CREATE TABLE IF NOT EXISTS trading_universe (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    sector VARCHAR(50),
    market_cap BIGINT,
    market_cap_category VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    added_date DATE DEFAULT CURRENT_DATE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_date ON market_data(symbol, date);
CREATE INDEX IF NOT EXISTS idx_technical_indicators_symbol_date ON technical_indicators(symbol, date);
CREATE INDEX IF NOT EXISTS idx_signals_model_ticker_date ON signals(model_id, ticker, signal_date);
CREATE INDEX IF NOT EXISTS idx_signals_ticker_date ON signals(ticker, signal_date);
CREATE INDEX IF NOT EXISTS idx_model_performance_model_date ON model_performance(model_id, evaluation_date);
CREATE INDEX IF NOT EXISTS idx_model_runs_model_date ON model_runs(model_id, run_date);
CREATE INDEX IF NOT EXISTS idx_models_active ON models(is_active);
CREATE INDEX IF NOT EXISTS idx_trading_universe_active ON trading_universe(is_active);

-- Insert initial trading universe
INSERT INTO trading_universe (symbol, sector, market_cap_category) VALUES
    ('AAPL', 'Technology', 'Large Cap'),
    ('MSFT', 'Technology', 'Large Cap'),
    ('GOOGL', 'Technology', 'Large Cap'),
    ('AMZN', 'Consumer Discretionary', 'Large Cap'),
    ('NVDA', 'Technology', 'Large Cap'),
    ('META', 'Technology', 'Large Cap'),
    ('TSLA', 'Consumer Discretionary', 'Large Cap'),
    ('NFLX', 'Communication Services', 'Large Cap'),
    ('ADBE', 'Technology', 'Large Cap'),
    ('CRM', 'Technology', 'Large Cap'),
    ('ORCL', 'Technology', 'Large Cap'),
    ('AMD', 'Technology', 'Large Cap'),
    ('INTC', 'Technology', 'Large Cap'),
    ('QCOM', 'Technology', 'Large Cap'),
    ('BKNG', 'Consumer Discretionary', 'Large Cap'),
    ('CMCSA', 'Communication Services', 'Large Cap'),
    ('AVGO', 'Technology', 'Large Cap'),
    ('TXN', 'Technology', 'Large Cap'),
    ('HON', 'Industrials', 'Large Cap'),
    ('UNP', 'Industrials', 'Large Cap')
ON CONFLICT (symbol) DO NOTHING;

-- Grant permissions on all tables to quant_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO quant_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO quant_user;

-- Migration: Drop old technical_features table if it exists and data has been migrated
-- Uncomment this line after verifying the migration is complete:
-- DROP TABLE IF EXISTS technical_features;