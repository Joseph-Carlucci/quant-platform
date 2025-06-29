-- Quantitative Research Platform Database Initialization
-- This script sets up all required databases and schemas

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

-- Technical Features Table
CREATE TABLE IF NOT EXISTS technical_features (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    features JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);

-- Models Table
CREATE TABLE IF NOT EXISTS models (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL UNIQUE,
    strategy_type VARCHAR(50) NOT NULL,
    parameters JSONB,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Signals Table
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES models(id),
    symbol VARCHAR(10) NOT NULL,
    signal_type VARCHAR(10) NOT NULL, -- 'buy', 'sell', 'hold'
    confidence DECIMAL(3,2),
    signal_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model Performance Table
CREATE TABLE IF NOT EXISTS model_performance (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES models(id),
    evaluation_date DATE NOT NULL,
    total_return DECIMAL(8,4),
    sharpe_ratio DECIMAL(6,4),
    max_drawdown DECIMAL(6,4),
    win_rate DECIMAL(5,4),
    total_trades INTEGER,
    evaluation_period_days INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_id, evaluation_date)
);

-- Trading Universe Table
CREATE TABLE IF NOT EXISTS trading_universe (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    sector VARCHAR(50),
    market_cap_category VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    added_date DATE DEFAULT CURRENT_DATE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_date ON market_data(symbol, date);
CREATE INDEX IF NOT EXISTS idx_technical_features_symbol_date ON technical_features(symbol, date);
CREATE INDEX IF NOT EXISTS idx_signals_model_symbol_date ON signals(model_id, symbol, signal_date);
CREATE INDEX IF NOT EXISTS idx_model_performance_model_date ON model_performance(model_id, evaluation_date);

-- Insert initial trading universe
INSERT INTO trading_universe (symbol, sector, market_cap_category) VALUES
    ('AAPL', 'Technology', 'Large Cap'),
    ('MSFT', 'Technology', 'Large Cap'),
    ('GOOGL', 'Technology', 'Large Cap'),
    ('AMZN', 'Consumer Discretionary', 'Large Cap'),
    ('NVDA', 'Technology', 'Large Cap'),
    ('META', 'Technology', 'Large Cap'),
    ('TSLA', 'Consumer Discretionary', 'Large Cap'),
    ('NFLX', 'Communication Services', 'Large Cap')
ON CONFLICT (symbol) DO NOTHING;

-- Grant permissions on all tables to quant_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO quant_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO quant_user;