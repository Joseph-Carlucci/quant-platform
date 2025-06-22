-- PostgreSQL Database Initialization Script for Quant Platform
-- This script creates all necessary databases, users, and schemas

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

-- Create schemas for different data types
CREATE SCHEMA IF NOT EXISTS market_data;
CREATE SCHEMA IF NOT EXISTS fundamental_data;
CREATE SCHEMA IF NOT EXISTS alternative_data;
CREATE SCHEMA IF NOT EXISTS models;
CREATE SCHEMA IF NOT EXISTS backtests;

-- Grant permissions to quant_user on all schemas
GRANT ALL ON SCHEMA market_data TO quant_user;
GRANT ALL ON SCHEMA fundamental_data TO quant_user;
GRANT ALL ON SCHEMA alternative_data TO quant_user;
GRANT ALL ON SCHEMA models TO quant_user;
GRANT ALL ON SCHEMA backtests TO quant_user;

-- Grant permissions on all objects in schemas
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA market_data TO quant_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA market_data TO quant_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA fundamental_data TO quant_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA fundamental_data TO quant_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA alternative_data TO quant_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA alternative_data TO quant_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA models TO quant_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA models TO quant_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA backtests TO quant_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA backtests TO quant_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA market_data GRANT ALL ON TABLES TO quant_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA market_data GRANT ALL ON SEQUENCES TO quant_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA fundamental_data GRANT ALL ON TABLES TO quant_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA fundamental_data GRANT ALL ON SEQUENCES TO quant_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA alternative_data GRANT ALL ON TABLES TO quant_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA alternative_data GRANT ALL ON SEQUENCES TO quant_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA models GRANT ALL ON TABLES TO quant_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA models GRANT ALL ON SEQUENCES TO quant_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA backtests GRANT ALL ON TABLES TO quant_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA backtests GRANT ALL ON SEQUENCES TO quant_user; 