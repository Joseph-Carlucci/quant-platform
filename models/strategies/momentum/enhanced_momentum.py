"""
Enhanced Momentum Strategy for End-to-End Example

This strategy demonstrates:
- Integration with the database and data layer
- Advanced technical analysis combining multiple indicators
- Risk management and position sizing
- Signal generation with confidence scoring
- Production-ready strategy design patterns
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from models.strategies.base import BaseStrategy, Signal, SignalType
from data_layer.features import TechnicalIndicators

logger = logging.getLogger(__name__)

class EnhancedMomentumStrategy(BaseStrategy):
    """
    Enhanced momentum strategy that combines multiple technical indicators
    for robust signal generation.
    
    Strategy Logic:
    - Primary: Moving average crossover (SMA 10 vs SMA 20)
    - Confirmation: RSI not in extreme zones (30-70)
    - Volume confirmation: Above 20-day average
    - Momentum confirmation: Positive 5-day momentum
    - Risk management: Volatility-based position sizing
    
    Parameters:
        short_ma_period: Short-term moving average period (default: 10)
        long_ma_period: Long-term moving average period (default: 20)
        rsi_period: RSI calculation period (default: 14)
        rsi_lower: RSI lower threshold (default: 30)
        rsi_upper: RSI upper threshold (default: 70)
        volume_ma_period: Volume moving average period (default: 20)
        momentum_period: Momentum lookback period (default: 5)
        min_volume_ratio: Minimum volume ratio for signal (default: 1.2)
        volatility_lookback: Volatility calculation period (default: 20)
        max_position_size: Maximum position size percentage (default: 0.05)
    """
    
    def __init__(self, name: str = "EnhancedMomentum", parameters: Dict[str, Any] = None):
        default_params = {
            'short_ma_period': 10,
            'long_ma_period': 20,
            'rsi_period': 14,
            'rsi_lower': 30,
            'rsi_upper': 70,
            'volume_ma_period': 20,
            'momentum_period': 5,
            'min_volume_ratio': 1.2,
            'volatility_lookback': 20,
            'max_position_size': 0.05,
            'min_confidence': 0.3,
        }
        
        if parameters:
            default_params.update(parameters)
            
        super().__init__(name, default_params)
        
        # Strategy state for tracking indicators
        self.indicator_cache: Dict[str, Dict[str, float]] = {}
        
    def initialize(self) -> None:
        """Initialize the enhanced momentum strategy."""
        self.logger.info("Initializing EnhancedMomentumStrategy")
        
        if not self.validate_parameters():
            raise ValueError("Invalid strategy parameters")
            
        self.initialized = True
        self.logger.info("EnhancedMomentumStrategy initialized successfully")
        
    def validate_parameters(self) -> bool:
        """Validate strategy parameters."""
        params_to_check = [
            ('short_ma_period', lambda x: x > 0),
            ('long_ma_period', lambda x: x > 0),
            ('rsi_period', lambda x: x > 0),
            ('rsi_lower', lambda x: 0 <= x <= 100),
            ('rsi_upper', lambda x: 0 <= x <= 100),
            ('volume_ma_period', lambda x: x > 0),
            ('momentum_period', lambda x: x > 0),
            ('min_volume_ratio', lambda x: x > 0),
            ('volatility_lookback', lambda x: x > 0),
            ('max_position_size', lambda x: 0 < x <= 1),
            ('min_confidence', lambda x: 0 <= x <= 1),
        ]
        
        for param_name, validator in params_to_check:
            value = self.get_parameter(param_name)
            if not validator(value):
                self.logger.error(f"Invalid parameter {param_name}: {value}")
                return False
                
        # Check that short MA < long MA
        if self.get_parameter('short_ma_period') >= self.get_parameter('long_ma_period'):
            self.logger.error("Short MA period must be less than long MA period")
            return False
            
        # Check RSI thresholds
        if self.get_parameter('rsi_lower') >= self.get_parameter('rsi_upper'):
            self.logger.error("RSI lower threshold must be less than upper threshold")
            return False
            
        return True
        
    def get_required_features(self) -> List[str]:
        """Get list of required features for this strategy."""
        return [
            f"sma_{self.get_parameter('short_ma_period')}",
            f"sma_{self.get_parameter('long_ma_period')}",
            f"rsi_{self.get_parameter('rsi_period')}",
            f"volume_ma_{self.get_parameter('volume_ma_period')}",
            f"momentum_{self.get_parameter('momentum_period')}d",
            f"volatility_{self.get_parameter('volatility_lookback')}d",
            "volume_ratio",
        ]
        
    def generate_signals_from_features(self, 
                                     symbol: str, 
                                     current_date: str,
                                     features: Dict[str, float],
                                     market_data: Dict[str, float]) -> List[Signal]:
        """
        Generate signals using pre-calculated features from the database.
        
        This method demonstrates production-ready signal generation using
        features stored in the database by the data ingestion pipeline.
        
        Args:
            symbol: Trading symbol
            current_date: Current date (YYYY-MM-DD)
            features: Dictionary of feature values
            market_data: Current market data (OHLCV)
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        try:
            current_price = market_data.get('close_price')
            if current_price is None:
                self.logger.warning(f"No current price for {symbol}")
                return signals
            
            # Extract required features
            short_ma = features.get(f'sma_{self.get_parameter("short_ma_period")}')
            long_ma = features.get(f'sma_{self.get_parameter("long_ma_period")}')
            rsi = features.get(f'rsi_{self.get_parameter("rsi_period")}')
            volume_ratio = features.get('volume_ratio')
            momentum = features.get(f'momentum_{self.get_parameter("momentum_period")}d')
            volatility = features.get(f'volatility_{self.get_parameter("volatility_lookback")}d')
            
            # Check if we have all required features
            required_features = [short_ma, long_ma, rsi, volume_ratio, momentum]
            if any(feature is None for feature in required_features):
                self.logger.debug(f"Missing features for {symbol}, skipping signal generation")
                return signals
            
            # Get previous indicators for crossover detection
            prev_indicators = self.indicator_cache.get(symbol, {})
            prev_short_ma = prev_indicators.get('short_ma')
            prev_long_ma = prev_indicators.get('long_ma')
            
            # Update current indicators
            self.indicator_cache[symbol] = {
                'short_ma': short_ma,
                'long_ma': long_ma,
                'rsi': rsi,
                'volume_ratio': volume_ratio,
                'momentum': momentum,
                'volatility': volatility
            }
            
            # Generate signals if we have previous data
            if prev_short_ma is not None and prev_long_ma is not None:
                signal = self._evaluate_signal_conditions(
                    symbol=symbol,
                    current_date=current_date,
                    current_price=current_price,
                    short_ma=short_ma,
                    long_ma=long_ma,
                    prev_short_ma=prev_short_ma,
                    prev_long_ma=prev_long_ma,
                    rsi=rsi,
                    volume_ratio=volume_ratio,
                    momentum=momentum,
                    volatility=volatility
                )
                
                if signal:
                    signals.append(signal)
                    
        except Exception as e:
            self.logger.error(f"Error generating signals for {symbol}: {e}")
            
        return signals
    
    def _evaluate_signal_conditions(self,
                                  symbol: str,
                                  current_date: str,
                                  current_price: float,
                                  short_ma: float,
                                  long_ma: float,
                                  prev_short_ma: float,
                                  prev_long_ma: float,
                                  rsi: float,
                                  volume_ratio: float,
                                  momentum: float,
                                  volatility: Optional[float]) -> Optional[Signal]:
        """Evaluate all signal conditions and generate signal if criteria are met."""
        
        # Primary condition: Moving average crossover
        bullish_crossover = (prev_short_ma <= prev_long_ma and short_ma > long_ma)
        bearish_crossover = (prev_short_ma >= prev_long_ma and short_ma < long_ma)
        
        if not (bullish_crossover or bearish_crossover):
            return None
            
        # Confirmation conditions
        confirmations = {}
        confidence_factors = []
        
        # 1. RSI confirmation (not in extreme zones)
        rsi_lower = self.get_parameter('rsi_lower')
        rsi_upper = self.get_parameter('rsi_upper')
        rsi_confirmed = rsi_lower <= rsi <= rsi_upper
        confirmations['rsi'] = rsi_confirmed
        
        if rsi_confirmed:
            # Higher confidence when RSI is closer to neutral (50)
            rsi_confidence = 1.0 - abs(rsi - 50) / 50
            confidence_factors.append(rsi_confidence)
        else:
            confidence_factors.append(0.2)  # Low confidence for extreme RSI
            
        # 2. Volume confirmation
        min_volume_ratio = self.get_parameter('min_volume_ratio')
        volume_confirmed = volume_ratio >= min_volume_ratio
        confirmations['volume'] = volume_confirmed
        
        if volume_confirmed:
            # Higher confidence for higher volume
            volume_confidence = min(volume_ratio / 2.0, 1.0)
            confidence_factors.append(volume_confidence)
        else:
            confidence_factors.append(0.3)  # Lower confidence for low volume
            
        # 3. Momentum confirmation
        momentum_confirmed = (bullish_crossover and momentum > 0) or (bearish_crossover and momentum < 0)
        confirmations['momentum'] = momentum_confirmed
        
        if momentum_confirmed:
            # Higher confidence for stronger momentum
            momentum_confidence = min(abs(momentum) * 10, 1.0)
            confidence_factors.append(momentum_confidence)
        else:
            confidence_factors.append(0.4)  # Lower confidence for conflicting momentum
            
        # 4. Volatility consideration (for position sizing, not signal generation)
        volatility_factor = 1.0
        if volatility is not None and volatility > 0:
            # Lower confidence in highly volatile environments
            volatility_factor = max(0.3, 1.0 - (volatility - 0.2) / 0.3) if volatility > 0.2 else 1.0
            confidence_factors.append(volatility_factor)
        
        # Calculate overall confidence
        overall_confidence = np.mean(confidence_factors) if confidence_factors else 0.5
        
        # Apply confirmation requirements
        min_confirmations_required = 2  # At least 2 out of 3 confirmations
        confirmations_count = sum(confirmations.values())
        
        if confirmations_count < min_confirmations_required:
            self.logger.debug(f"Insufficient confirmations for {symbol}: {confirmations}")
            return None
            
        # Check minimum confidence threshold
        min_confidence = self.get_parameter('min_confidence')
        if overall_confidence < min_confidence:
            self.logger.debug(f"Confidence too low for {symbol}: {overall_confidence:.3f}")
            return None
            
        # Determine signal type
        signal_type = SignalType.BUY if bullish_crossover else SignalType.SELL
        
        # Calculate position size based on volatility
        position_size = self._calculate_position_size(volatility, overall_confidence)
        
        # Create signal
        signal = Signal(
            timestamp=pd.Timestamp(current_date),
            symbol=symbol,
            signal_type=signal_type,
            strength=overall_confidence,
            price=current_price,
            metadata={
                'strategy': self.name,
                'short_ma': short_ma,
                'long_ma': long_ma,
                'rsi': rsi,
                'volume_ratio': volume_ratio,
                'momentum': momentum,
                'volatility': volatility,
                'confirmations': confirmations,
                'confirmations_count': confirmations_count,
                'position_size': position_size,
                'crossover_type': 'bullish' if bullish_crossover else 'bearish'
            }
        )
        
        self.logger.info(f"{signal_type.name} signal generated for {symbol} "
                        f"at ${current_price:.2f} (confidence: {overall_confidence:.3f})")
        
        return signal
    
    def _calculate_position_size(self, volatility: Optional[float], confidence: float) -> float:
        """Calculate position size based on volatility and confidence."""
        max_position = self.get_parameter('max_position_size')
        
        # Base position size adjusted by confidence
        base_position = max_position * confidence
        
        # Adjust for volatility (lower position size for higher volatility)
        if volatility is not None and volatility > 0:
            # Scale down position for high volatility (>30% annualized)
            volatility_adjustment = max(0.3, 1.0 - (volatility - 0.3) / 0.5) if volatility > 0.3 else 1.0
            base_position *= volatility_adjustment
            
        return min(base_position, max_position)
    
    def generate_signals(self, current_time: pd.Timestamp, current_data: pd.Series) -> List[Signal]:
        """
        Legacy interface for compatibility with backtesting engine.
        In production, use generate_signals_from_features instead.
        """
        self.logger.warning("Using legacy signal generation interface. "
                           "Consider using generate_signals_from_features for production.")
        
        # For compatibility, try to generate basic signals
        symbol = current_data.name
        if symbol is None:
            return []
            
        try:
            current_price = current_data.get('close', current_data.get('close_price'))
            if pd.isna(current_price):
                return []
                
            # Basic moving average crossover without full feature set
            # This is a simplified version for backtesting compatibility
            short_window = self.get_parameter('short_ma_period')
            long_window = self.get_parameter('long_ma_period')
            
            # Note: In a real implementation, you'd calculate MAs from historical data
            # This is just a placeholder for demonstration
            return []
            
        except Exception as e:
            self.logger.error(f"Error in legacy signal generation for {symbol}: {e}")
            return []
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get comprehensive strategy information and current state."""
        base_info = super().get_strategy_info()
        
        enhanced_info = {
            'strategy_type': 'enhanced_momentum',
            'primary_signals': 'moving_average_crossover',
            'confirmations': ['rsi', 'volume', 'momentum'],
            'risk_management': 'volatility_based_position_sizing',
            'parameters': self.parameters,
            'tracked_symbols': len(self.indicator_cache),
            'current_indicators': dict(self.indicator_cache) if len(self.indicator_cache) <= 5 else f"{len(self.indicator_cache)} symbols tracked"
        }
        
        base_info.update(enhanced_info)
        return base_info
    
    def reset(self) -> None:
        """Reset strategy state."""
        super().reset()
        self.indicator_cache.clear()
        self.logger.info("Enhanced momentum strategy state reset")
        
    def get_performance_attribution(self) -> Dict[str, Any]:
        """Get performance attribution factors for analysis."""
        return {
            'primary_factor': 'momentum',
            'secondary_factors': ['rsi_confirmation', 'volume_confirmation', 'momentum_confirmation'],
            'risk_factors': ['volatility_adjustment', 'confidence_filtering'],
            'signal_filters': {
                'min_confirmations': 2,
                'min_confidence': self.get_parameter('min_confidence'),
                'rsi_range': [self.get_parameter('rsi_lower'), self.get_parameter('rsi_upper')],
                'min_volume_ratio': self.get_parameter('min_volume_ratio')
            }
        }