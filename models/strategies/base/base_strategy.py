from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class SignalType(Enum):
    BUY = 1
    SELL = -1
    HOLD = 0

@dataclass
class Signal:
    timestamp: pd.Timestamp
    symbol: str
    signal_type: SignalType
    strength: float = 1.0  # Signal strength (0-1)
    price: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Position:
    symbol: str
    quantity: float
    entry_price: float
    entry_time: pd.Timestamp
    current_price: float
    unrealized_pnl: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    This class defines the interface that all strategies must implement.
    It provides common functionality like parameter management, data handling,
    and signal generation framework.
    """
    
    def __init__(self, name: str, parameters: Optional[Dict[str, Any]] = None):
        self.name = name
        self.parameters = parameters or {}
        self.positions: Dict[str, Position] = {}
        self.signals: List[Signal] = []
        self.data: Optional[pd.DataFrame] = None
        self.features: Optional[pd.DataFrame] = None
        self.initialized = False
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """Update strategy parameters."""
        self.parameters.update(parameters)
        self.logger.info(f"Updated parameters: {parameters}")
        
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get a parameter value with optional default."""
        return self.parameters.get(key, default)
        
    def set_data(self, data: pd.DataFrame) -> None:
        """Set the market data for the strategy."""
        self.data = data
        self.logger.info(f"Data set with shape: {data.shape}")
        
    def set_features(self, features: pd.DataFrame) -> None:
        """Set the feature data for the strategy."""
        self.features = features
        self.logger.info(f"Features set with shape: {features.shape}")
        
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the strategy.
        
        This method is called once before the strategy starts running.
        Use it to set up any required state, validate parameters, etc.
        """
        pass
        
    @abstractmethod
    def generate_signals(self, current_time: pd.Timestamp, 
                        current_data: pd.Series) -> List[Signal]:
        """
        Generate trading signals based on current market data.
        
        Args:
            current_time: Current timestamp
            current_data: Current market data (OHLCV, etc.)
            
        Returns:
            List of Signal objects
        """
        pass
        
    def on_signal(self, signal: Signal) -> None:
        """
        Handle a generated signal.
        
        This method is called after a signal is generated but before
        it's sent to the risk management system.
        
        Args:
            signal: The generated signal
        """
        self.signals.append(signal)
        self.logger.info(f"Signal generated: {signal}")
        
    def on_position_opened(self, position: Position) -> None:
        """
        Handle position opening.
        
        Args:
            position: The opened position
        """
        self.positions[position.symbol] = position
        self.logger.info(f"Position opened: {position}")
        
    def on_position_closed(self, position: Position, realized_pnl: float) -> None:
        """
        Handle position closing.
        
        Args:
            position: The closed position
            realized_pnl: Realized profit/loss
        """
        if position.symbol in self.positions:
            del self.positions[position.symbol]
        self.logger.info(f"Position closed: {position}, PnL: {realized_pnl}")
        
    def update_positions(self, current_prices: Dict[str, float]) -> None:
        """
        Update unrealized PnL for open positions.
        
        Args:
            current_prices: Dictionary of symbol -> current price
        """
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                position.current_price = current_prices[symbol]
                position.unrealized_pnl = (
                    (position.current_price - position.entry_price) * 
                    position.quantity
                )
                
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total portfolio value.
        
        Args:
            current_prices: Dictionary of symbol -> current price
            
        Returns:
            Total portfolio value
        """
        total_value = 0.0
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                total_value += position.quantity * current_prices[symbol]
        return total_value
        
    def get_position_size(self, symbol: str) -> float:
        """
        Get current position size for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position size (positive for long, negative for short)
        """
        if symbol in self.positions:
            return self.positions[symbol].quantity
        return 0.0
        
    def is_long(self, symbol: str) -> bool:
        """Check if we have a long position in the symbol."""
        return self.get_position_size(symbol) > 0
        
    def is_short(self, symbol: str) -> bool:
        """Check if we have a short position in the symbol."""
        return self.get_position_size(symbol) < 0
        
    def is_flat(self, symbol: str) -> bool:
        """Check if we have no position in the symbol."""
        return self.get_position_size(symbol) == 0
        
    def validate_parameters(self) -> bool:
        """
        Validate strategy parameters.
        
        Returns:
            True if parameters are valid, False otherwise
        """
        return True
        
    def get_required_features(self) -> List[str]:
        """
        Get list of required features for this strategy.
        
        Returns:
            List of feature names
        """
        return []
        
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get strategy information and statistics.
        
        Returns:
            Dictionary with strategy info
        """
        return {
            'name': self.name,
            'parameters': self.parameters,
            'total_signals': len(self.signals),
            'open_positions': len(self.positions),
            'initialized': self.initialized
        }
        
    def reset(self) -> None:
        """Reset strategy state (useful for backtesting multiple runs)."""
        self.positions.clear()
        self.signals.clear()
        self.initialized = False
        self.logger.info("Strategy state reset")
        
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
        
    def __repr__(self) -> str:
        return self.__str__()