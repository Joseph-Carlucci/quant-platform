"""
Technical Indicators Transformer

Transforms raw OHLCV market data into technical analysis indicators.
This replaces the complex "feature store" with a simple, focused transformer.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from .base_transformer import BaseTransformer

logger = logging.getLogger(__name__)


class TechnicalIndicators(BaseTransformer):
    """
    Transform OHLCV market data into technical indicators.
    
    Takes raw market data and produces common technical analysis indicators
    like RSI, MACD, Bollinger Bands, moving averages, etc.
    """
    
    def __init__(self, periods: Optional[Dict[str, int]] = None):
        """
        Initialize technical indicators transformer.
        
        Args:
            periods: Dictionary of periods for various indicators
        """
        self.periods = periods if periods is not None else {
            'rsi': 14,
            'sma_short': 20,
            'sma_long': 50,
            'ema_fast': 12,
            'ema_slow': 26,
            'bb': 20,
            'atr': 14,
            'adx': 14,
            'volume_sma': 20
        }
        super().__init__({'periods': self.periods})
    
    def get_required_columns(self) -> List[str]:
        """Return required input columns."""
        return ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
    
    def transform(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """
        Transform OHLCV data into technical indicators.
        
        Args:
            market_data: DataFrame with columns [symbol, date, open, high, low, close, volume]
            
        Returns:
            DataFrame with technical indicators
        """
        results = []
        
        for symbol in market_data['symbol'].unique():
            symbol_data = market_data[market_data['symbol'] == symbol].copy()
            symbol_data = symbol_data.sort_values(['date']).reset_index(drop=True)
            
            # Calculate all indicators for this symbol
            indicators = self._calculate_indicators(symbol_data)
            results.append(indicators)
        
        if results:
            return pd.concat(results, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def _calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators for a single symbol."""
        
        # Create base result DataFrame
        result = pd.DataFrame({
            'symbol': data['symbol'],
            'date': data['date']
        })
        
        # Price data as Series
        high = pd.Series(data['high'].values, index=data.index)
        low = pd.Series(data['low'].values, index=data.index)
        close = pd.Series(data['close'].values, index=data.index)
        volume = pd.Series(data['volume'].values, index=data.index)
        
        # === Moving Averages ===
        result['sma_20'] = close.rolling(self.periods['sma_short']).mean()
        result['sma_50'] = close.rolling(self.periods['sma_long']).mean()
        result['ema_12'] = close.ewm(span=self.periods['ema_fast']).mean()
        result['ema_26'] = close.ewm(span=self.periods['ema_slow']).mean()
        
        # === RSI ===
        result['rsi_14'] = self._calculate_rsi(close, self.periods['rsi'])
        
        # === MACD ===
        macd_line = result['ema_12'] - result['ema_26']
        macd_signal = macd_line.ewm(span=9).mean()
        result['macd'] = macd_line
        result['macd_signal'] = macd_signal
        result['macd_histogram'] = macd_line - macd_signal
        
        # === Bollinger Bands ===
        bb_period = self.periods['bb']
        bb_middle = close.rolling(bb_period).mean()
        bb_std = close.rolling(bb_period).std()
        result['bb_upper'] = bb_middle + (bb_std * 2)
        result['bb_middle'] = bb_middle
        result['bb_lower'] = bb_middle - (bb_std * 2)
        
        # Bollinger Band position (0 = at lower band, 1 = at upper band)
        bb_range = result['bb_upper'] - result['bb_lower']
        result['bb_position'] = np.where(bb_range > 0, 
                                       (close - result['bb_lower']) / bb_range, 
                                       0.5)
        result['bb_width'] = bb_range / bb_middle
        
        # === Volume Indicators ===
        result['volume_sma_20'] = volume.rolling(self.periods['volume_sma']).mean()
        result['volume_ratio'] = volume / result['volume_sma_20']
        
        # === Volatility Indicators ===
        result['atr_14'] = self._calculate_atr(data, self.periods['atr'])
        
        # === Trend Indicators ===
        result['adx_14'] = self._calculate_adx(data, self.periods['adx'])
        
        return result
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high = pd.Series(data['high'].values, index=data.index)
        low = pd.Series(data['low'].values, index=data.index)
        close = pd.Series(data['close'].values, index=data.index)
        
        tr1 = high - low
        tr2 = np.abs(high - close.shift())
        tr3 = np.abs(low - close.shift())
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return true_range.rolling(period).mean()
    
    def _calculate_adx(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average Directional Index."""
        high = pd.Series(data['high'].values, index=data.index)
        low = pd.Series(data['low'].values, index=data.index)
        
        # Calculate Directional Movement
        up_move = high - high.shift()
        down_move = low.shift() - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # Convert to Series
        plus_dm_series = pd.Series(plus_dm, index=data.index)
        minus_dm_series = pd.Series(minus_dm, index=data.index)
        
        # Calculate True Range for this calculation
        atr_series = self._calculate_atr(data, 1)  # 1-period TR
        
        # Smooth the values
        plus_dm_smooth = plus_dm_series.rolling(period).mean()
        minus_dm_smooth = minus_dm_series.rolling(period).mean()
        tr_smooth = atr_series.rolling(period).mean()
        
        # Calculate Directional Indicators
        plus_di = 100 * (plus_dm_smooth / tr_smooth)
        minus_di = 100 * (minus_dm_smooth / tr_smooth)
        
        # Calculate ADX
        di_diff = np.abs(plus_di - minus_di)
        di_sum = plus_di + minus_di
        dx = 100 * (di_diff / di_sum)
        return dx.rolling(period).mean()
    
    def get_output_schema(self) -> Dict[str, str]:
        """Return the schema of transformed data."""
        return {
            'symbol': 'VARCHAR(10)',
            'date': 'DATE',
            # Moving averages
            'sma_20': 'DECIMAL(12,4)',
            'sma_50': 'DECIMAL(12,4)',
            'ema_12': 'DECIMAL(12,4)',
            'ema_26': 'DECIMAL(12,4)',
            # RSI
            'rsi_14': 'DECIMAL(8,4)',
            # MACD
            'macd': 'DECIMAL(10,6)',
            'macd_signal': 'DECIMAL(10,6)',
            'macd_histogram': 'DECIMAL(10,6)',
            # Bollinger Bands
            'bb_upper': 'DECIMAL(12,4)',
            'bb_middle': 'DECIMAL(12,4)',
            'bb_lower': 'DECIMAL(12,4)',
            'bb_position': 'DECIMAL(6,4)',
            'bb_width': 'DECIMAL(8,4)',
            # Volume
            'volume_sma_20': 'BIGINT',
            'volume_ratio': 'DECIMAL(8,4)',
            # Volatility
            'atr_14': 'DECIMAL(8,4)',
            # Trend
            'adx_14': 'DECIMAL(6,2)'
        }


class FundamentalRatios(BaseTransformer):
    """
    Transform fundamental data into financial ratios.
    
    Future implementation for fundamental analysis.
    """
    
    def get_required_columns(self) -> List[str]:
        return ['symbol', 'date', 'revenue', 'net_income', 'total_assets']
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transform fundamental data into ratios."""
        # Placeholder implementation
        return pd.DataFrame()
    
    def get_output_schema(self) -> Dict[str, str]:
        return {
            'symbol': 'VARCHAR(10)',
            'date': 'DATE',
            'pe_ratio': 'DECIMAL(8,2)',
            'pb_ratio': 'DECIMAL(8,2)',
            'roe': 'DECIMAL(8,4)',
            'debt_to_equity': 'DECIMAL(8,4)'
        }


class SentimentScores(BaseTransformer):
    """
    Transform news/social data into sentiment scores.
    
    Future implementation for sentiment analysis.
    """
    
    def get_required_columns(self) -> List[str]:
        return ['symbol', 'date', 'news_text']
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transform text data into sentiment scores."""
        # Placeholder implementation
        return pd.DataFrame()
    
    def get_output_schema(self) -> Dict[str, str]:
        return {
            'symbol': 'VARCHAR(10)',
            'date': 'DATE',
            'news_sentiment_score': 'DECIMAL(6,4)',
            'social_sentiment_score': 'DECIMAL(6,4)'
        }