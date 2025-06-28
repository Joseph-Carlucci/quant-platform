import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from collections import deque, defaultdict
import logging
from datetime import datetime, timedelta
import queue

from models.strategies.base import BaseStrategy, SignalType
from infrastructure.utils import DataLoader, Config
from .events import (
    Event, EventType, MarketEvent, SignalEvent, OrderEvent, FillEvent,
    OrderType, OrderDirection
)
from .metrics import PerformanceMetrics

logger = logging.getLogger(__name__)

class Portfolio:
    """
    Portfolio management for backtesting.
    
    Tracks positions, cash, and portfolio value over time.
    """
    
    def __init__(self, initial_capital: float, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        
        # Current state
        self.cash = initial_capital
        self.positions: Dict[str, float] = defaultdict(float)
        self.portfolio_value = initial_capital
        
        # History tracking
        self.history: List[Dict[str, Any]] = []
        
    def update_market_value(self, current_prices: Dict[str, float], timestamp: pd.Timestamp):
        """Update portfolio value based on current market prices."""
        # Calculate position values
        position_value = 0.0
        for symbol, quantity in self.positions.items():
            if symbol in current_prices and quantity != 0:
                position_value += quantity * current_prices[symbol]
                
        self.portfolio_value = self.cash + position_value
        
        # Record history
        self.history.append({
            'timestamp': timestamp,
            'cash': self.cash,
            'position_value': position_value,
            'total_value': self.portfolio_value,
            'positions': dict(self.positions)
        })
        
    def execute_fill(self, fill: FillEvent):
        """Execute a fill and update portfolio."""
        if fill.direction == OrderDirection.BUY:
            # Buy: decrease cash, increase position
            cost = fill.quantity * fill.fill_price + fill.commission
            self.cash -= cost
            self.positions[fill.symbol] += fill.quantity
        else:
            # Sell: increase cash, decrease position
            proceeds = fill.quantity * fill.fill_price - fill.commission
            self.cash += proceeds
            self.positions[fill.symbol] -= fill.quantity
            
        logger.debug(f"Fill executed: {fill.symbol} {fill.direction.value} "
                    f"{fill.quantity} @ {fill.fill_price}")
                    
    def can_afford(self, order: OrderEvent, current_price: float) -> bool:
        """Check if portfolio can afford the order."""
        if order.direction == OrderDirection.BUY:
            cost = order.quantity * current_price * (1 + self.commission)
            return self.cash >= cost
        else:
            # For sell orders, check if we have enough position
            return self.positions[order.symbol] >= order.quantity
            
    def get_position(self, symbol: str) -> float:
        """Get current position size for symbol."""
        return self.positions.get(symbol, 0.0)
        
    def get_portfolio_df(self) -> pd.DataFrame:
        """Get portfolio history as DataFrame."""
        return pd.DataFrame(self.history)

class ExecutionHandler:
    """
    Handles order execution with realistic fills, commission, and slippage.
    """
    
    def __init__(self, commission: float = 0.001, slippage: float = 0.0005):
        self.commission = commission
        self.slippage = slippage
        
    def execute_order(self, order: OrderEvent, market_data: MarketEvent) -> Optional[FillEvent]:
        """
        Execute an order and return a fill event.
        
        Args:
            order: Order to execute
            market_data: Current market data
            
        Returns:
            FillEvent if successful, None otherwise
        """
        # Get current price
        current_price = market_data.get_price(order.symbol, "close")
        if current_price is None:
            logger.warning(f"No price data for {order.symbol}")
            return None
            
        # Apply slippage
        if order.direction == OrderDirection.BUY:
            fill_price = current_price * (1 + self.slippage)
        else:
            fill_price = current_price * (1 - self.slippage)
            
        # Calculate commission
        commission = max(
            abs(order.quantity * fill_price) * self.commission,
            1.0  # Minimum commission
        )
        
        # Create fill event
        fill = FillEvent(
            timestamp=market_data.timestamp,
            symbol=order.symbol,
            quantity=order.quantity,
            direction=order.direction,
            fill_price=fill_price,
            commission=commission,
            slippage=self.slippage
        )
        
        return fill

class BacktestEngine:
    """
    Event-driven backtesting engine.
    
    Coordinates data, strategies, portfolio management, and execution
    to provide realistic backtesting capabilities.
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        
        # Core components
        self.data_loader = DataLoader(self.config.data.db_connection)
        self.portfolio = Portfolio(
            initial_capital=self.config.backtest.initial_capital,
            commission=self.config.backtest.commission
        )
        self.execution_handler = ExecutionHandler(
            commission=self.config.backtest.commission,
            slippage=self.config.backtest.slippage
        )
        
        # Event queue
        self.events = queue.Queue()
        
        # Data and state
        self.market_data: Optional[pd.DataFrame] = None
        self.current_time: Optional[pd.Timestamp] = None
        self.symbols: List[str] = []
        
        # Results
        self.results: Optional[Dict[str, Any]] = None
        
    def load_data(self, 
                  symbols: List[str],
                  start_date: str,
                  end_date: str) -> None:
        """
        Load market data for backtesting.
        
        Args:
            symbols: List of symbols to trade
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        self.symbols = symbols
        self.market_data = self.data_loader.prepare_backtest_data(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            pivot=False
        )
        
        if self.market_data.empty:
            raise ValueError("No market data loaded")
            
        logger.info(f"Loaded {len(self.market_data)} data points for backtesting")
        
    def run(self,
            strategy: BaseStrategy,
            symbols: List[str],
            start_date: str,
            end_date: str) -> Dict[str, Any]:
        """
        Run a backtest.
        
        Args:
            strategy: Trading strategy to test
            symbols: List of symbols to trade
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Dictionary with backtest results
        """
        logger.info(f"Starting backtest: {strategy.name}")
        logger.info(f"Symbols: {symbols}")
        logger.info(f"Period: {start_date} to {end_date}")
        
        # Load data
        self.load_data(symbols, start_date, end_date)
        
        # Initialize strategy
        strategy.set_data(self.market_data)
        strategy.initialize()
        
        # Group data by date for event-driven processing
        daily_data = self.market_data.groupby('date')
        
        # Main backtest loop
        for date, day_data in daily_data:
            self.current_time = date
            
            # Create market event
            market_data = {}
            for _, row in day_data.iterrows():
                symbol = row['ticker']
                market_data[symbol] = {
                    'open': row['open_price'],
                    'high': row['high_price'], 
                    'low': row['low_price'],
                    'close': row['close_price'],
                    'volume': row['volume']
                }
                
            market_event = MarketEvent(timestamp=date, data=market_data)
            self.events.put(market_event)
            
            # Process events
            self._process_events(strategy)
            
            # Update portfolio value
            current_prices = {symbol: data['close'] for symbol, data in market_data.items()}
            self.portfolio.update_market_value(current_prices, date)
            
        # Calculate results
        self.results = self._calculate_results(strategy)
        
        logger.info(f"Backtest completed. Final portfolio value: "
                   f"${self.portfolio.portfolio_value:,.2f}")
        
        return self.results
        
    def _process_events(self, strategy: BaseStrategy):
        """Process all events in the queue."""
        while not self.events.empty():
            try:
                event = self.events.get(False)
            except queue.Empty:
                break
                
            if event.type == EventType.MARKET:
                self._handle_market_event(event, strategy)
            elif event.type == EventType.SIGNAL:
                self._handle_signal_event(event)
            elif event.type == EventType.ORDER:
                self._handle_order_event(event)
            elif event.type == EventType.FILL:
                self._handle_fill_event(event, strategy)
                
    def _handle_market_event(self, event: MarketEvent, strategy: BaseStrategy):
        """Handle market data event."""
        # Generate signals from strategy
        for symbol in event.get_symbols():
            current_data = pd.Series(event.data[symbol])
            current_data.name = symbol
            
            signals = strategy.generate_signals(event.timestamp, current_data)
            
            # Convert strategy signals to signal events
            for signal in signals:
                signal_event = SignalEvent(
                    timestamp=event.timestamp,
                    symbol=signal.symbol,
                    signal_type=signal.signal_type.value,
                    strength=signal.strength,
                    price=signal.price,
                    metadata=signal.metadata
                )
                self.events.put(signal_event)
                
    def _handle_signal_event(self, event: SignalEvent):
        """Convert signal to order."""
        # Simple position sizing (fixed percentage of portfolio)
        position_size = self.config.risk.max_position_size
        target_value = self.portfolio.portfolio_value * position_size
        
        # Get current price
        current_price = event.price or 100.0  # Fallback price
        target_quantity = target_value / current_price
        
        # Determine order direction and quantity
        current_position = self.portfolio.get_position(event.symbol)
        
        if event.signal_type == 1:  # Buy signal
            if current_position <= 0:
                # Go long
                quantity = target_quantity
                direction = OrderDirection.BUY
            else:
                return  # Already long
        elif event.signal_type == -1:  # Sell signal
            if current_position >= 0:
                # Go short or close long
                quantity = target_quantity if current_position == 0 else current_position
                direction = OrderDirection.SELL
            else:
                return  # Already short
        else:
            return  # Hold signal
            
        # Create order
        order = OrderEvent(
            timestamp=event.timestamp,
            symbol=event.symbol,
            order_type=OrderType.MARKET,
            quantity=quantity,
            direction=direction
        )
        
        self.events.put(order)
        
    def _handle_order_event(self, event: OrderEvent):
        """Execute order."""
        # Get current market data
        market_event = None
        temp_events = []
        
        # Find the most recent market event
        while not self.events.empty():
            try:
                temp_event = self.events.get(False)
                temp_events.append(temp_event)
                if temp_event.type == EventType.MARKET:
                    market_event = temp_event
                    break
            except queue.Empty:
                break
                
        # Put events back
        for temp_event in temp_events:
            self.events.put(temp_event)
            
        if market_event is None:
            logger.warning("No market data available for order execution")
            return
            
        # Check if portfolio can afford the order
        current_price = market_event.get_price(event.symbol, "close")
        if current_price is None or not self.portfolio.can_afford(event, current_price):
            logger.warning(f"Cannot afford order: {event.symbol} {event.direction.value}")
            return
            
        # Execute order
        fill = self.execution_handler.execute_order(event, market_event)
        if fill:
            self.events.put(fill)
            
    def _handle_fill_event(self, event: FillEvent, strategy: BaseStrategy):
        """Handle fill event."""
        self.portfolio.execute_fill(event)
        
        # Notify strategy
        if event.direction == OrderDirection.BUY:
            from models.strategies.base import Position
            position = Position(
                symbol=event.symbol,
                quantity=event.quantity,
                entry_price=event.fill_price,
                entry_time=event.timestamp,
                current_price=event.fill_price
            )
            strategy.on_position_opened(position)
        else:
            # Position closing logic would go here
            pass
            
    def _calculate_results(self, strategy: BaseStrategy) -> Dict[str, Any]:
        """Calculate backtest results and performance metrics."""
        portfolio_df = self.portfolio.get_portfolio_df()
        
        if portfolio_df.empty:
            return {}
            
        # Calculate performance metrics
        metrics = PerformanceMetrics(portfolio_df)
        
        results = {
            'strategy_name': strategy.name,
            'start_date': portfolio_df['timestamp'].min(),
            'end_date': portfolio_df['timestamp'].max(),
            'initial_capital': self.config.backtest.initial_capital,
            'final_value': self.portfolio.portfolio_value,
            'total_return': metrics.total_return(),
            'annualized_return': metrics.annualized_return(),
            'sharpe_ratio': metrics.sharpe_ratio(),
            'max_drawdown': metrics.max_drawdown(),
            'volatility': metrics.volatility(),
            'calmar_ratio': metrics.calmar_ratio(),
            'total_trades': len(strategy.signals),
            'portfolio_history': portfolio_df,
            'positions': dict(self.portfolio.positions),
            'signals': strategy.signals
        }
        
        return results
        
    def get_results(self) -> Optional[Dict[str, Any]]:
        """Get backtest results."""
        return self.results