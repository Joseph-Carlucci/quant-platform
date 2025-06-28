# Data Layer

The data layer handles market data ingestion, feature calculation, and storage for the quantitative trading platform.

## Architecture

```
Polygon API → Data Ingestion → Feature Calculation → Database Storage → Trading Models
```

The data layer provides:
- Data ingestion from external APIs (Polygon.io)
- Technical indicator calculation
- Flexible JSON-based feature storage
- Direct integration with Airflow DAGs

## Structure

```
data_layer/
├── README.md                    # This file
├── ingestion/                   # Data source connections
│   ├── base_ingestion.py       # Abstract base for data sources
│   └── polygon_client.py       # Polygon.io API client
└── transformers/               # Data transformation logic
    ├── base_transformer.py    # Abstract base for transformers
    └── technical.py           # Technical indicators calculator
```

## Current Implementation

**Data Sources:**
- Polygon.io API for market data (OHLCV)
- Configurable via `POLYGON_API_KEY` environment variable

**Technical Indicators:**
- RSI (Relative Strength Index)
- Moving averages (SMA, EMA)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Volume indicators

**Storage:**
- PostgreSQL database with JSONB feature storage
- Flexible schema supporting any indicator structure
- Efficient querying for model execution

## Usage in End-to-End Example

The data layer is used directly in `dags/end_to_end_data_ingestion.py`:

1. **Fetch market data** from Polygon API for trading universe symbols
2. **Calculate technical indicators** using rolling window calculations
3. **Store features** in JSON format in the feature store
4. **Provide data** to model execution and performance testing DAGs

## Configuration

Set environment variables:
```bash
POLYGON_API_KEY=your_polygon_api_key
```

Database connection handled by DAGs:
```python
POSTGRES_CONN_STRING = "postgresql://quant_user:quant_password@postgres:5432/quant_data"
```

## Key Benefits

- Simple integration with Airflow DAGs
- Flexible JSON storage for any feature structure
- Easy to extend with new data sources
- Production-ready error handling and logging

The data layer provides essential market data and features for the end-to-end example while maintaining simplicity and focus.