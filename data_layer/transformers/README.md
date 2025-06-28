# Data Transformers

The transformers directory contains components for transforming raw market data into analysis-ready datasets for trading models.

## Current Structure

```
data_layer/transformers/
├── __init__.py
├── README.md
├── base_transformer.py     # Abstract base class (future)
└── technical.py           # Technical indicators (future)
```

## Current Implementation

Currently, data transformation is handled directly within the Airflow DAGs. The end-to-end data ingestion DAG calculates technical indicators inline and stores them in JSON format in the feature store.

**Current Indicators:**
- RSI (Relative Strength Index)
- Moving averages (SMA)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Volume indicators

## Storage Approach

Features are stored in JSON format in the feature store table for flexibility:

```sql
CREATE TABLE feature_store (
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    feature_set VARCHAR(50) NOT NULL,
    features JSONB NOT NULL,
    PRIMARY KEY (symbol, date, feature_set)
);
```

## Future Capabilities

When expanded, this directory will provide:
- Abstract base transformer class for consistent interfaces
- Dedicated technical indicators transformer
- Fundamental ratios calculator
- Sentiment analysis transformers
- Typed database schemas for specific indicator types

## Current Usage

Technical indicators are calculated in:
- `dags/end_to_end_data_ingestion.py` - Direct calculation and JSON storage
- Enhanced momentum strategy - Feature consumption from JSON

## Benefits of Current Approach

- Simple and focused on current needs
- Flexible JSON storage for any indicator structure
- Direct integration with Airflow DAGs
- Easy to extend with new indicators

The transformers directory is prepared for future expansion while maintaining simplicity in the current implementation.