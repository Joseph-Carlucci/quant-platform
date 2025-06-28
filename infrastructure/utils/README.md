# Utils Directory

## Purpose & Design Philosophy

The `utils/` directory provides **foundational infrastructure** and common utilities that support all other components of the trading platform. This directory embodies the **DRY principle** (Don't Repeat Yourself) by centralizing shared functionality and ensuring consistent behavior across the entire system.

## Design Principles

### 1. **Centralized Common Functionality**
- Single source of truth for configuration management
- Standardized data loading and database interactions
- Unified logging and error handling patterns

### 2. **Platform Independence**
- Abstract away environment-specific details
- Support multiple deployment scenarios (local, cloud, containers)
- Flexible configuration sources (files, environment, databases)

### 3. **Developer Experience**
- Simple, intuitive APIs for common tasks
- Comprehensive error messages and debugging support
- Minimal boilerplate code for routine operations

### 4. **Production Readiness**
- Robust error handling and recovery
- Performance optimization for data operations
- Security best practices for sensitive operations

## Directory Structure

```
utils/
├── config.py         # Configuration management system
├── data_loader.py    # Database and data loading utilities
├── logger.py         # Logging setup and management
├── performance.py    # Performance calculation helpers (future)
└── __init__.py      # Public API exports
```

## Core Components

### **Configuration Management (`config.py`)**
**Purpose**: Centralized, hierarchical configuration system supporting multiple sources and environments.

**Design Philosophy**: Configuration should be **explicit, flexible, and environment-aware**. Support development, testing, and production scenarios without code changes.

**Key Features**:
- **Multiple Sources**: YAML/JSON files, environment variables, direct input
- **Hierarchical Structure**: Nested configuration with dot-notation access
- **Type Safety**: Dataclass-based configuration with validation
- **Environment Overrides**: Production values override development defaults

**Configuration Categories**:
```python
@dataclass
class BacktestConfig:
    initial_capital: float = 100000.0
    commission: float = 0.001
    slippage: float = 0.0005

@dataclass  
class RiskConfig:
    max_position_size: float = 0.1
    stop_loss_pct: float = 0.02
    max_drawdown: float = 0.15

@dataclass
class DataConfig:
    db_connection: str = "postgresql://..."
    data_frequency: str = "daily"
    lookback_period: int = 252
```

### **Data Loading (`data_loader.py`)**
**Purpose**: Standardized interface for loading market data from the PostgreSQL database with optimization and error handling.

**Design Philosophy**: **Efficiency and reliability** - provide fast, robust data access with intelligent caching and error recovery.

**Key Capabilities**:
- **Multiple Data Types**: Daily aggregates, previous close, ticker details
- **Flexible Queries**: Date ranges, symbol filtering, column selection
- **Data Cleaning**: Automated data validation and cleaning
- **Performance Optimization**: Efficient SQL queries and result caching
- **Error Handling**: Graceful degradation and retry logic

### **Logging (`logger.py`)**
**Purpose**: Centralized logging configuration providing consistent log formatting, levels, and output destinations.

**Design Philosophy**: **Visibility and debugging** - provide comprehensive logging that aids development and production monitoring without overwhelming users.

**Features**:
- **Multiple Outputs**: Console and file logging
- **Configurable Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Custom Formatting**: Timestamp, module, level, message
- **Third-party Integration**: Proper log levels for external libraries

## Configuration System Deep Dive

### **Configuration Hierarchy**
```
Environment Variables (highest priority)
    ↓
Configuration Files (YAML/JSON)
    ↓
Default Values (lowest priority)
```

### **Usage Patterns**

#### **Basic Configuration**
```python
# Use defaults
config = Config()
print(config.backtest.initial_capital)  # 100000.0

# Load from file
config = Config('production.yaml')

# Override specific values
config.set('backtest.commission', 0.0005)
```

#### **Environment Integration**
```bash
# Set environment variables
export BACKTEST_INITIAL_CAPITAL=50000
export RISK_MAX_POSITION_SIZE=0.05
export DATA_DB_CONNECTION="postgresql://prod-user:pass@prod-db:5432/quant"
```

```python
# Automatically picks up environment variables
config = Config()
print(config.backtest.initial_capital)  # 50000 (from environment)
```

#### **Configuration Files**
```yaml
# config.yaml
backtest:
  initial_capital: 100000
  commission: 0.001
  
risk:
  max_position_size: 0.1
  stop_loss_pct: 0.02
  
data:
  db_connection: "postgresql://localhost:5432/quant_data"
  
# Custom sections
strategies:
  momentum:
    default_window: 20
  
logging:
  level: "INFO"
  file: "trading.log"
```

### **Validation and Type Safety**
```python
def validate(self) -> bool:
    """Validate configuration values."""
    errors = []
    
    if self.backtest.initial_capital <= 0:
        errors.append("Initial capital must be positive")
    if not 0 < self.risk.max_position_size <= 1:
        errors.append("Max position size must be between 0 and 1")
    
    return len(errors) == 0
```

## Data Loading System Deep Dive

### **Database Integration**
```python
class DataLoader:
    def __init__(self, db_connection: str):
        self.engine = create_engine(db_connection)
        
    def load_daily_data(self, symbols, start_date, end_date):
        """Load daily OHLCV data with optimized queries."""
        # Efficient SQL with proper indexing
        # Data validation and cleaning
        # Error handling and retry logic
```

### **Data Pipeline Operations**

#### **Raw Data Loading**
```python
# Load basic OHLCV data
data = data_loader.load_daily_data(
    symbols=['AAPL', 'GOOGL'],
    start_date='2023-01-01',
    end_date='2023-12-31'
)
```

#### **Prepared Backtest Data**
```python
# Load and prepare data for backtesting
backtest_data = data_loader.prepare_backtest_data(
    symbols=['AAPL', 'GOOGL'],
    start_date='2023-01-01',
    end_date='2023-12-31',
    pivot=True  # Symbols as columns for vectorized operations
)
```

#### **Metadata and Statistics**
```python
# Get available symbols and date ranges
symbols = data_loader.get_available_symbols()
start_date, end_date = data_loader.get_date_range()

# Get data quality statistics
stats = data_loader.get_statistics(['AAPL', 'GOOGL'])
```

### **Data Cleaning Pipeline**
```python
def _clean_data(self, df):
    """Comprehensive data cleaning."""
    # Remove missing critical data
    df = df.dropna(subset=['open_price', 'high_price', 'low_price', 'close_price'])
    
    # Remove invalid prices
    df = df[df['close_price'] > 0]
    
    # Validate OHLC relationships
    df = df[
        (df['high_price'] >= df['low_price']) &
        (df['high_price'] >= df['close_price']) &
        (df['low_price'] <= df['close_price'])
    ]
    
    # Handle volume data
    df['volume'] = df['volume'].fillna(0)
    
    return df
```

## Logging System Architecture

### **Hierarchical Logger Setup**
```python
def setup_logging(level="INFO", log_file=None, format_string=None):
    """Configure platform-wide logging."""
    
    # Root logger configuration
    root_logger = logging.getLogger()
    
    # Console handler for development
    console_handler = logging.StreamHandler(sys.stdout)
    
    # File handler for production
    if log_file:
        file_handler = logging.FileHandler(log_file)
    
    # Third-party library log levels
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
```

### **Module-Specific Loggers**
```python
# Each module gets its own logger
logger = logging.getLogger(__name__)

# Usage patterns
logger.info("Strategy initialized successfully")
logger.warning("Missing data for symbol AAPL on 2023-05-15")
logger.error("Database connection failed", exc_info=True)
logger.debug("Signal generated: BUY AAPL at $150.25")
```

### **Production Logging Best Practices**
```python
# Structured logging for production monitoring
logger.info("Backtest completed", extra={
    'strategy': 'SimpleMomentum',
    'symbols': ['AAPL', 'GOOGL'],
    'total_return': 0.1234,
    'sharpe_ratio': 1.45,
    'duration_seconds': 23.5
})

# Performance monitoring
logger.info("Data loading performance", extra={
    'operation': 'load_daily_data',
    'symbols_count': 10,
    'records_loaded': 25000,
    'duration_ms': 1250
})
```

## Integration Patterns

### **Configuration-Driven Components**
```python
# Components accept configuration objects
class BacktestEngine:
    def __init__(self, config: Config):
        self.config = config
        self.initial_capital = config.backtest.initial_capital
        self.commission = config.backtest.commission
        
# Strategy configuration
class MyStrategy(BaseStrategy):
    def __init__(self, config: Config):
        super().__init__()
        self.lookback = config.get('strategies.momentum.lookback', 20)
```

### **Data Loading Integration**
```python
# Strategies use data loader for historical data
class Strategy:
    def initialize(self):
        data_loader = DataLoader(self.config.data.db_connection)
        self.historical_data = data_loader.load_daily_data(
            symbols=self.symbols,
            start_date=self.config.get('backtest.start_date'),
            end_date=self.config.get('backtest.end_date')
        )
```

### **Logging Integration**
```python
# All components use centralized logging
def main():
    # Setup logging first
    setup_logging(level="INFO", log_file="trading.log")
    
    # All subsequent logging uses configured handlers
    logger = logging.getLogger(__name__)
    logger.info("Trading platform starting")
```

## Performance Utilities (Future)

### **Timing and Profiling**
```python
# Performance monitoring decorators
@time_it
def expensive_computation():
    # Function timing logged automatically
    pass

@profile_memory
def memory_intensive_function():
    # Memory usage tracked and logged
    pass
```

### **Caching Utilities**
```python
# Intelligent caching for expensive operations
@cache_result(ttl_seconds=3600)
def load_features(symbol, start_date, end_date):
    # Results cached with automatic expiration
    pass
```

## Security and Best Practices

### **Sensitive Data Handling**
```python
# Never log sensitive information
def connect_to_database(connection_string):
    # Log connection attempt without credentials
    logger.info("Connecting to database", extra={
        'host': extract_host(connection_string),
        'database': extract_database(connection_string)
        # Never log username/password
    })
```

### **Configuration Security**
```python
# Use environment variables for production secrets
config = Config()
config.data.db_connection = os.getenv('DATABASE_URL')  # From environment
config.api.polygon_key = os.getenv('POLYGON_API_KEY')   # Never in code
```

### **Error Handling Patterns**
```python
def robust_operation():
    try:
        # Risky operation
        result = perform_operation()
        return result
    except SpecificException as e:
        logger.error("Specific error occurred", exc_info=True)
        # Graceful degradation
        return fallback_value()
    except Exception as e:
        logger.critical("Unexpected error", exc_info=True)
        # Re-raise for handling at higher level
        raise
```

## Testing Support

### **Test Configuration**
```python
# Separate configuration for testing
test_config = Config()
test_config.data.db_connection = "sqlite:///test.db"
test_config.backtest.initial_capital = 10000
test_config.logging.level = "DEBUG"
```

### **Mock Data Loading**
```python
# Support for test data injection
class TestDataLoader(DataLoader):
    def __init__(self, mock_data):
        self.mock_data = mock_data
        
    def load_daily_data(self, symbols, start_date, end_date):
        return self.mock_data[symbols]
```

This utilities framework provides the solid foundation that enables all other components to focus on their core responsibilities while maintaining consistency, reliability, and ease of use across the platform.