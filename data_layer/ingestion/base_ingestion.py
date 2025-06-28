"""
Base classes for data ingestion adapters.

This module provides abstract base classes that all data source adapters should inherit from
to ensure consistent interfaces across different data providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class BaseDataSource(ABC):
    """
    Abstract base class for all data source adapters.
    
    This class defines the standard interface that all data sources must implement
    to ensure consistent behavior across different providers (Polygon, Yahoo Finance, etc.)
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the data source adapter.
        
        Args:
            api_key: API key for authenticated endpoints
            **kwargs: Additional configuration parameters
        """
        self.api_key = api_key
        self.config = kwargs
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def fetch_market_data(self, 
                         symbols: List[str], 
                         start_date: date, 
                         end_date: date,
                         **kwargs) -> pd.DataFrame:
        """
        Fetch historical market data for given symbols and date range.
        
        Args:
            symbols: List of ticker symbols to fetch
            start_date: Start date for data range
            end_date: End date for data range
            **kwargs: Additional parameters specific to the data source
            
        Returns:
            DataFrame with standardized columns:
            - symbol: str
            - date: date
            - open_price: float
            - high_price: float
            - low_price: float
            - close_price: float
            - volume: int
            - adjusted_close: float (optional)
            - vwap: float (optional)
        """
        pass
    
    @abstractmethod
    def fetch_previous_close(self, symbols: List[str]) -> pd.DataFrame:
        """
        Fetch previous trading day's close data for given symbols.
        
        Args:
            symbols: List of ticker symbols
            
        Returns:
            DataFrame with previous close data
        """
        pass
    
    def validate_symbols(self, symbols: List[str]) -> List[str]:
        """
        Validate that symbols are properly formatted and supported.
        
        Args:
            symbols: List of symbols to validate
            
        Returns:
            List of valid symbols
        """
        valid_symbols = []
        for symbol in symbols:
            if self._is_valid_symbol(symbol):
                valid_symbols.append(symbol.upper())
            else:
                self.logger.warning(f"Invalid symbol skipped: {symbol}")
        
        return valid_symbols
    
    def _is_valid_symbol(self, symbol: str) -> bool:
        """
        Check if a symbol is valid (basic validation).
        
        Args:
            symbol: Symbol to validate
            
        Returns:
            True if symbol appears valid
        """
        if not symbol or not isinstance(symbol, str):
            return False
        
        # Basic validation - alphanumeric and reasonable length
        return symbol.replace('.', '').replace('-', '').isalnum() and 1 <= len(symbol) <= 10
    
    def standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize DataFrame to common column names and formats.
        
        Args:
            df: Raw DataFrame from data source
            
        Returns:
            Standardized DataFrame
        """
        # This should be implemented by each subclass according to their data format
        return df
    
    def handle_rate_limiting(self, retry_count: int = 0, max_retries: int = 3):
        """
        Handle rate limiting and retry logic.
        
        Args:
            retry_count: Current retry attempt
            max_retries: Maximum number of retries
        """
        if retry_count >= max_retries:
            raise Exception(f"Max retries ({max_retries}) exceeded")
        
        # Exponential backoff
        import time
        wait_time = 2 ** retry_count
        self.logger.info(f"Rate limited. Waiting {wait_time} seconds before retry {retry_count + 1}")
        time.sleep(wait_time)


class DataQualityError(Exception):
    """Exception raised when data quality issues are detected."""
    pass


class APIConnectionError(Exception):
    """Exception raised when API connection fails."""
    pass


class DataValidationMixin:
    """
    Mixin class providing common data validation methods.
    """
    
    def validate_price_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate price data for common issues.
        
        Args:
            df: DataFrame with price data
            
        Returns:
            Validated DataFrame
            
        Raises:
            DataQualityError: If critical data quality issues found
        """
        if df.empty:
            raise DataQualityError("Empty DataFrame provided")
        
        required_cols = ['symbol', 'date', 'close_price']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise DataQualityError(f"Missing required columns: {missing_cols}")
        
        # Check for negative prices
        price_cols = [col for col in df.columns if 'price' in col.lower()]
        for col in price_cols:
            if (df[col] < 0).any():
                self.logger.warning(f"Negative prices found in column {col}")
        
        # Check for missing data
        null_percentage = df.isnull().sum() / len(df)
        high_null_cols = null_percentage[null_percentage > 0.1].index.tolist()
        if high_null_cols:
            self.logger.warning(f"High null percentage in columns: {high_null_cols}")
        
        return df 