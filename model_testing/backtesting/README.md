# Backtesting Directory

## Purpose & Design Philosophy

The `backtesting/` directory implements a sophisticated, event-driven backtesting engine designed to provide **realistic simulation** of trading strategies. Unlike simple vectorized backtesting, this system simulates the actual sequence of market events, orders, and fills that would occur in live trading.

## Design Principles

### 1. **Event-Driven Architecture**
- Mimics real-world trading where events happen sequentially
- Prevents look-ahead bias by processing data chronologically
- Enables realistic order execution simulation

### 2. **Realism Over Speed**
- Accurate modeling of transaction costs, slippage, and market impact
- Portfolio-level constraints and realistic position management
- Proper handling of partial fills and order types

### 3. **Extensibility**
- Modular components that can be customized or replaced
- Support for different broker models and execution algorithms
- Easy integration with risk management and portfolio optimization

### 4. **Comprehensive Analytics**
- Beyond simple returns - includes risk metrics, drawdown analysis
- Performance attribution and trade-level analytics
- Comparison tools for strategy evaluation

## Directory Structure

```
backtesting/
├── engine.py           # Core backtesting engine and orchestration
├── events.py          # Event system (Market, Signal, Order, Fill)
├── metrics.py         # Performance metrics and analytics
├── visualization.py   # Results visualization (future)
└── __init__.py        # Public API exports
```

## Core Components

### **BacktestEngine (`engine.py`)**
**Purpose**: The main orchestrator that coordinates all components of the backtesting system.

**Key Responsibilities**:
- Data management and event generation
- Strategy execution and signal processing
- Portfolio management and position tracking
- Order execution and fill simulation
- Results calculation and aggregation

**Design Philosophy**: Act as the "market simulator" - create a realistic trading environment where strategies can be tested under conditions that mirror live trading.

### **Event System (`events.py`)**
**Purpose**: Implements the event-driven architecture with different event types representing real trading activities.

**Event Types**:
- `MarketEvent`: New market data (OHLCV) arrives
- `SignalEvent`: Strategy generates a trading signal
- `OrderEvent`: Signal converted to executable order
- `FillEvent`: Order executed and position updated

**Design Philosophy**: Model the exact sequence of events that occur in live trading, ensuring strategies can only use information available at that point in time.

### **Performance Metrics (`metrics.py`)**
**Purpose**: Comprehensive suite of financial performance metrics for strategy evaluation.

**Key Metrics**:
- **Return Metrics**: Total, annualized, risk-adjusted returns
- **Risk Metrics**: Volatility, VaR, maximum drawdown, beta
- **Efficiency Ratios**: Sharpe, Sortino, Calmar, Information ratios
- **Trading Metrics**: Win rate, profit factor, average win/loss

**Design Philosophy**: Provide institutional-grade performance analysis that enables thorough strategy evaluation and comparison.

## Event-Driven Flow

### **1. Market Data Processing**
```
Market Data → MarketEvent → Strategy.generate_signals()
```
- New OHLCV data creates a `MarketEvent`
- Event contains all symbols' data for current timestamp
- Strategy processes data and generates signals

### **2. Signal Processing**
```
Strategy Signals → SignalEvent → Position Sizing → OrderEvent
```
- Strategy signals converted to `SignalEvent` objects
- Risk management applies position sizing rules
- Executable orders created based on portfolio constraints

### **3. Order Execution**
```
OrderEvent → ExecutionHandler → FillEvent → Portfolio Update
```
- Orders sent to execution handler (simulated broker)
- Realistic fills generated with slippage and commission
- Portfolio positions and cash updated

### **4. Performance Tracking**
```
FillEvent → Portfolio History → Performance Metrics
```
- Each transaction updates portfolio value
- Historical track record maintained
- Metrics calculated on completed trades and portfolio evolution

## Backtesting Engine Architecture

### **Portfolio Management**
```python
class Portfolio:
    def __init__(self, initial_capital, commission):
        self.cash = initial_capital
        self.positions = {}  # symbol -> quantity
        self.history = []    # track portfolio over time
    
    def execute_fill(self, fill_event):
        # Update cash and positions based on trade
        
    def update_market_value(self, current_prices):
        # Calculate current portfolio value
```

**Design Intention**: Maintain realistic portfolio accounting with proper cash management, position tracking, and mark-to-market valuation.

### **Execution Handler**
```python
class ExecutionHandler:
    def execute_order(self, order, market_data):
        # Apply slippage based on order direction
        # Calculate commission based on trade size
        # Return realistic fill event
```

**Design Intention**: Simulate realistic broker execution including transaction costs, timing delays, and market impact.

### **Event Queue Processing**
```python
def _process_events(self, strategy):
    while not self.events.empty():
        event = self.events.get()
        if event.type == EventType.MARKET:
            self._handle_market_event(event, strategy)
        elif event.type == EventType.SIGNAL:
            self._handle_signal_event(event)
        # ... handle other event types
```

**Design Intention**: Process events in strict chronological order to prevent look-ahead bias and maintain realism.

## Configuration & Customization

### **Backtest Configuration**
```python
config = Config()
config.backtest.initial_capital = 100000
config.backtest.commission = 0.001      # 0.1% per trade
config.backtest.slippage = 0.0005       # 0.05% slippage
config.backtest.min_commission = 1.0    # $1 minimum
```

### **Execution Parameters**
- **Commission Models**: Percentage, per-share, tiered structures
- **Slippage Models**: Fixed percentage, volume-based, volatility-adjusted
- **Market Impact**: Linear, square-root, or custom models
- **Order Types**: Market, limit, stop orders (future enhancement)

## Performance Analytics Deep Dive

### **Risk-Adjusted Returns**
- **Sharpe Ratio**: Return per unit of total risk
- **Sortino Ratio**: Return per unit of downside risk
- **Calmar Ratio**: Return per unit of maximum drawdown

### **Drawdown Analysis**
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Drawdown Duration**: Time to recover from drawdowns
- **Underwater Curve**: Visualization of drawdown periods

### **Portfolio Analytics**
- **Beta**: Sensitivity to market movements
- **Alpha**: Excess return after adjusting for market risk
- **Information Ratio**: Active return per unit of tracking error

### **Trade-Level Metrics**
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profits to gross losses
- **Average Win/Loss**: Mean profit per winning/losing trade

## Usage Patterns

### **Basic Backtesting**
```python
# Simple strategy backtest
engine = BacktestEngine(config)
results = engine.run(
    strategy=MyStrategy(),
    symbols=['AAPL', 'GOOGL'],
    start_date='2023-01-01',
    end_date='2023-12-31'
)

print(f"Sharpe Ratio: {results['sharpe_ratio']:.3f}")
print(f"Max Drawdown: {results['max_drawdown']:.2%}")
```

### **Parameter Optimization**
```python
# Test multiple parameter combinations
param_grid = {
    'short_window': [5, 10, 15],
    'long_window': [20, 30, 40]
}

best_params = optimize_parameters(
    strategy_class=MomentumStrategy,
    param_grid=param_grid,
    symbols=['AAPL'],
    optimization_metric='sharpe_ratio'
)
```

### **Walk-Forward Analysis**
```python
# Test strategy robustness over time
results = walk_forward_analysis(
    strategy=MyStrategy(),
    symbols=['AAPL'],
    start_date='2020-01-01',
    end_date='2023-12-31',
    train_period='365D',
    test_period='90D'
)
```

## Integration with Other Components

### **Strategy Integration**
- Strategies implement standard interface for signal generation
- Engine handles all event processing and position management
- Clean separation between strategy logic and execution mechanics

### **Feature Engineering Integration**
- Automatic feature calculation based on strategy requirements
- Efficient data pipeline with feature caching
- Support for custom indicators and alternative data

### **Risk Management Integration**
- Position sizing rules applied automatically
- Portfolio-level constraints enforced
- Dynamic risk adjustments based on market conditions

## Best Practices

### **1. Realistic Assumptions**
- Use conservative estimates for transaction costs
- Include realistic slippage based on asset liquidity
- Consider market impact for larger orders
- Account for bid-ask spreads in execution

### **2. Bias Prevention**
- Never use future information in signal generation
- Implement proper data alignment and timing
- Account for corporate actions and data adjustments
- Use point-in-time data when available

### **3. Robustness Testing**
- Test across multiple time periods and market regimes
- Validate performance out-of-sample
- Check sensitivity to parameter changes
- Stress test under extreme market conditions

### **4. Performance Analysis**
- Look beyond simple returns to risk-adjusted metrics
- Analyze drawdown characteristics and recovery times
- Examine trade-level statistics for insights
- Compare performance to relevant benchmarks

## Future Enhancements

### **Advanced Order Types**
- Limit orders with partial fill modeling
- Stop-loss and take-profit orders
- Iceberg orders for large positions
- Custom execution algorithms (TWAP, VWAP)

### **Market Microstructure**
- Level II order book simulation
- Bid-ask spread modeling
- Volume-based market impact
- Intraday execution patterns

### **Multi-Asset Support**
- Cross-asset strategies (stocks, bonds, commodities)
- Currency hedging for international assets
- Correlation-based risk management
- Asset-specific transaction cost models

### **Advanced Analytics**
- Performance attribution by factor exposure
- Regime-specific performance analysis
- Transaction cost analysis (TCA)
- Risk decomposition and stress testing

This backtesting framework provides the foundation for rigorous strategy development and validation, ensuring that strategies tested here have a higher probability of success in live trading environments.