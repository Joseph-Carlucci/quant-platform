# Models Layer

The models layer contains trading strategies and the framework for building quantitative trading algorithms.

## Current Implementation

The layer provides:
- Base strategy framework with abstract classes
- Enhanced momentum strategy as a complete example
- Standardized signal types and generation

## Structure

```
models/
├── strategies/
│   ├── base/                  # Base classes and signal types
│   └── momentum/              # Enhanced momentum strategy example
└── README.md                  # This file
```

## Enhanced Momentum Strategy

The platform includes a complete momentum strategy in `strategies/momentum/enhanced_momentum.py`:

**Key Features:**
- Multi-factor confirmation using moving averages, RSI, volume, and momentum
- Volatility-based position sizing
- Confidence scoring based on multiple factors
- Production-ready error handling

**Strategy Logic:**
1. Primary signal from moving average crossover (10-day vs 20-day SMA)
2. Confirmation filters: RSI between 30-70, volume above average, momentum alignment
3. Position sizing based on volatility and confidence
4. Risk management with stop losses and size limits

## Adding New Strategies

To create a new strategy:

1. **Create Strategy Class**: Inherit from `BaseStrategy` in `strategies/base/`
2. **Implement Required Methods**: `initialize()`, `generate_signals()`, `get_required_features()`
3. **Register in DAG**: Add to model registry in `dags/end_to_end_model_execution.py`

**Example Registration:**
```python
{
    'model_name': 'my_strategy_v1',
    'strategy_class': 'models.strategies.my_module.MyStrategy',
    'parameters': {'param1': 20, 'param2': 0.05},
    'is_active': True
}
```

## Integration

Strategies integrate with:
- Feature store for technical indicators
- Model registry for parameter management
- Performance testing for evaluation
- Database for signal storage

## Testing

Test strategies using:
- End-to-end performance testing DAG
- Backtesting framework in `model_testing/`
- Performance metrics monitoring