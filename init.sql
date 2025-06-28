-- Database Initialization Script for Quant Platform
-- This script creates the necessary databases and users for the quantitative trading platform

-- Create Airflow database and user
CREATE DATABASE airflow;
CREATE USER airflow WITH PASSWORD 'airflow';
GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;

-- Connect to airflow database and grant schema permissions
\c airflow;
GRANT ALL ON SCHEMA public TO airflow;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO airflow;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO airflow;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO airflow;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO airflow;

-- Back to main database for other setup
\c postgres;

-- Create Quant Data database and user
CREATE DATABASE quant_data;
CREATE USER quant_user WITH PASSWORD 'quant_password';
GRANT ALL PRIVILEGES ON DATABASE quant_data TO quant_user;

-- Connect to quant_data database to create initial schema
\c quant_data;

-- Grant permissions to quant_user on all current and future objects
GRANT ALL ON SCHEMA public TO quant_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO quant_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO quant_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO quant_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO quant_user;

-- Create core tables for the end-to-end example

-- Market data from external sources (Polygon API)
CREATE TABLE IF NOT EXISTS market_data (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open_price DECIMAL(12,4) NOT NULL,
    high_price DECIMAL(12,4) NOT NULL,
    low_price DECIMAL(12,4) NOT NULL,
    close_price DECIMAL(12,4) NOT NULL,
    volume BIGINT NOT NULL,
    vwap DECIMAL(12,4),
    transactions INTEGER,
    data_source VARCHAR(50) DEFAULT 'polygon',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(symbol, date)
);

-- Trading universe - actively traded symbols
CREATE TABLE IF NOT EXISTS trading_universe (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    company_name VARCHAR(255),
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap_category VARCHAR(20), -- 'large', 'mid', 'small', 'micro'
    is_active BOOLEAN DEFAULT true,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Feature store for model inputs (flexible JSON-based storage)
CREATE TABLE IF NOT EXISTS feature_store (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    feature_set VARCHAR(50) NOT NULL,  -- e.g., 'technical_v1', 'momentum_v1'
    features JSONB NOT NULL,           -- Flexible feature storage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(symbol, date, feature_set)
);

-- Model registry
CREATE TABLE IF NOT EXISTS models (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL UNIQUE,
    model_version VARCHAR(20) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    strategy_class VARCHAR(200) NOT NULL,  -- Full Python class path
    parameters JSONB,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model execution runs
CREATE TABLE IF NOT EXISTS model_runs (
    id BIGSERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES models(id),
    run_date DATE NOT NULL,
    execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'running', -- 'running', 'completed', 'failed'
    signals_generated INTEGER DEFAULT 0,
    error_message TEXT,
    execution_duration_seconds INTEGER,
    metadata JSONB,
    
    UNIQUE(model_id, run_date)
);

-- Trading signals from models
CREATE TABLE IF NOT EXISTS signals (
    id BIGSERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES models(id),
    symbol VARCHAR(10) NOT NULL,
    signal_date DATE NOT NULL,
    signal_type VARCHAR(10) NOT NULL, -- 'BUY', 'SELL', 'HOLD'
    strength DECIMAL(5,4) NOT NULL,   -- Signal strength 0.0 to 1.0
    price DECIMAL(12,4),              -- Target/reference price
    confidence DECIMAL(5,4),          -- Model confidence 0.0 to 1.0
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT signals_signal_type_check CHECK (signal_type IN ('BUY', 'SELL', 'HOLD')),
    CONSTRAINT signals_strength_check CHECK (strength >= 0.0 AND strength <= 1.0),
    CONSTRAINT signals_confidence_check CHECK (confidence >= 0.0 AND confidence <= 1.0)
);

-- Model performance metrics
CREATE TABLE IF NOT EXISTS model_performance (
    id BIGSERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES models(id),
    evaluation_date DATE NOT NULL,
    evaluation_period_start DATE NOT NULL,
    evaluation_period_end DATE NOT NULL,
    
    -- Performance metrics
    total_return DECIMAL(10,6),
    sharpe_ratio DECIMAL(8,4),
    max_drawdown DECIMAL(8,4),
    win_rate DECIMAL(6,4),
    avg_win DECIMAL(10,6),
    avg_loss DECIMAL(10,6),
    profit_factor DECIMAL(8,4),
    
    -- Risk metrics
    volatility DECIMAL(8,4),
    downside_deviation DECIMAL(8,4),
    var_95 DECIMAL(10,6),
    
    -- Trade statistics
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    
    -- Metadata
    benchmark_comparison JSONB,
    additional_metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(model_id, evaluation_date)
);

-- Performance reports
CREATE TABLE IF NOT EXISTS performance_reports (
    id SERIAL PRIMARY KEY,
    report_name VARCHAR(100) NOT NULL,
    report_date DATE NOT NULL,
    report_type VARCHAR(50) NOT NULL, -- 'daily', 'weekly', 'monthly'
    
    -- Summary statistics
    models_evaluated INTEGER,
    best_performing_model_id INTEGER REFERENCES models(id),
    worst_performing_model_id INTEGER REFERENCES models(id),
    
    -- Report content
    summary_statistics JSONB,
    model_rankings JSONB,
    performance_analysis JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(report_name, report_date)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_date ON market_data(symbol, date);
CREATE INDEX IF NOT EXISTS idx_market_data_date ON market_data(date);
CREATE INDEX IF NOT EXISTS idx_feature_store_symbol_date ON feature_store(symbol, date);
CREATE INDEX IF NOT EXISTS idx_feature_store_feature_set ON feature_store(feature_set);
CREATE INDEX IF NOT EXISTS idx_signals_model_symbol_date ON signals(model_id, symbol, signal_date);
CREATE INDEX IF NOT EXISTS idx_signals_date ON signals(signal_date);
CREATE INDEX IF NOT EXISTS idx_model_performance_model_date ON model_performance(model_id, evaluation_date);
CREATE INDEX IF NOT EXISTS idx_model_runs_model_date ON model_runs(model_id, run_date);