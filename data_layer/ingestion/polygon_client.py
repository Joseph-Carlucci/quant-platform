"""
Polygon.io API Client

This module provides a clean interface for interacting with the Polygon.io API
for market data ingestion in the quantitative trading platform.
"""

import os
import requests
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
import logging
import time

from .base_ingestion import BaseDataSource, APIConnectionError, DataQualityError

logger = logging.getLogger(__name__)


class PolygonClient(BaseDataSource):
    """
    Polygon.io API client for market data ingestion.
    
    This client provides methods to fetch various types of market data from Polygon.io
    with proper error handling, rate limiting, and data validation.
    """
    
    BASE_URL = "https://api.polygon.io"
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Polygon client.
        
        Args:
            api_key: Polygon.io API key. If None, will try to get from environment
            **kwargs: Additional configuration options
        """
        # Get API key from multiple sources
        if not api_key:
            api_key = self._get_api_key()
        
        super().__init__(api_key=api_key, **kwargs)
        
        # Configure rate limiting
        self.rate_limit_delay = kwargs.get('rate_limit_delay', 0.1)  # seconds between requests
        self.max_retries = kwargs.get('max_retries', 3)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuantPlatform/1.0'
        })
    
    def _get_api_key(self) -> str:
        """
        Get Polygon.io API key from multiple sources in order of preference:
        1. Environment variable POLYGON_API_KEY
        2. Airflow Variable polygon_api_key (if available)
        3. Airflow Connection polygon_api (if available)
        
        Returns:
            API key string
            
        Raises:
            ValueError: If no API key found
        """
        # Try environment variable first
        api_key = os.getenv('POLYGON_API_KEY')
        if api_key:
            return api_key
        
        # Try Airflow Variable (if running in Airflow context)
        try:
            from airflow.models import Variable
            api_key = Variable.get("polygon_api_key", default_var=None)
            if api_key:
                return api_key
        except ImportError:
            pass  # Not running in Airflow context
        except Exception:
            pass  # Variable doesn't exist
        
        # Try Airflow Connection (if running in Airflow context)
        try:
            from airflow.hooks.base import BaseHook
            conn = BaseHook.get_connection('polygon_api')
            if conn.password:
                return conn.password
        except ImportError:
            pass  # Not running in Airflow context
        except Exception:
            pass  # Connection doesn't exist
        
        raise ValueError(
            "Polygon API key not found. Please set one of:\n"
            "1. Environment variable: POLYGON_API_KEY\n"
            "2. Airflow Variable: polygon_api_key\n"
            "3. Airflow Connection: polygon_api\n"
            "Get your free API key at: https://polygon.io/"
        )
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make an API request with error handling and rate limiting.
        
        Args:
            endpoint: API endpoint (e.g., '/v2/aggs/ticker/AAPL/prev')
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            APIConnectionError: If request fails after retries
        """
        if params is None:
            params = {}
        
        params['apikey'] = self.api_key
        url = f"{self.BASE_URL}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                # Rate limiting
                time.sleep(self.rate_limit_delay)
                
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # Check Polygon-specific error responses
                if data.get('status') == 'ERROR':
                    error_msg = data.get('error', 'Unknown Polygon API error')
                    raise APIConnectionError(f"Polygon API error: {error_msg}")
                
                return data
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise APIConnectionError(f"Failed after {self.max_retries} attempts: {e}")
                
                # Exponential backoff
                wait_time = 2 ** attempt
                time.sleep(wait_time)
    
    def fetch_market_data(self, 
                         symbols: List[str], 
                         start_date: date, 
                         end_date: date,
                         **kwargs) -> pd.DataFrame:
        """
        Fetch historical market data for given symbols and date range.
        
        Args:
            symbols: List of ticker symbols
            start_date: Start date for data range
            end_date: End date for data range
            **kwargs: Additional parameters (adjusted, multiplier, timespan)
            
        Returns:
            DataFrame with market data
        """
        symbols = self.validate_symbols(symbols)
        all_data = []
        
        for symbol in symbols:
            try:
                data = self._fetch_symbol_aggregates(symbol, start_date, end_date, **kwargs)
                all_data.extend(data)
            except Exception as e:
                self.logger.error(f"Failed to fetch data for {symbol}: {e}")
                continue
        
        if not all_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_data)
        return self.standardize_dataframe(df)
    
    def _fetch_symbol_aggregates(self, 
                                symbol: str, 
                                start_date: date, 
                                end_date: date,
                                **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch daily aggregates for a single symbol.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date
            end_date: End date
            **kwargs: Additional parameters
            
        Returns:
            List of daily aggregate records
        """
        multiplier = kwargs.get('multiplier', 1)
        timespan = kwargs.get('timespan', 'day')
        adjusted = kwargs.get('adjusted', True)
        
        endpoint = f"/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{start_date}/{end_date}"
        params = {
            'adjusted': str(adjusted).lower(),
            'sort': 'asc',
            'limit': 50000
        }
        
        response = self._make_request(endpoint, params)
        
        if response.get('status') != 'OK':
            self.logger.warning(f"No data returned for {symbol}")
            return []
        
        results = response.get('results', [])
        
        # Convert to standardized format
        records = []
        for result in results:
            records.append({
                'symbol': symbol,
                'date': datetime.fromtimestamp(result['t'] / 1000).date(),
                'open_price': result.get('o'),
                'high_price': result.get('h'),
                'low_price': result.get('l'),
                'close_price': result.get('c'),
                'volume': result.get('v'),
                'vwap': result.get('vw'),
                'transactions': result.get('n'),
                'timestamp_utc': result.get('t')
            })
        
        return records
    
    def fetch_previous_close(self, symbols: List[str]) -> pd.DataFrame:
        """
        Fetch previous trading day's close data for given symbols.
        
        Args:
            symbols: List of ticker symbols
            
        Returns:
            DataFrame with previous close data
        """
        symbols = self.validate_symbols(symbols)
        all_data = []
        
        for symbol in symbols:
            try:
                endpoint = f"/v2/aggs/ticker/{symbol}/prev"
                params = {'adjusted': 'true'}
                
                response = self._make_request(endpoint, params)
                
                if response.get('status') == 'OK' and response.get('results'):
                    result = response['results'][0]
                    
                    record = {
                        'symbol': symbol,
                        'date': datetime.fromtimestamp(result['t'] / 1000).date(),
                        'open_price': result.get('o'),
                        'high_price': result.get('h'),
                        'low_price': result.get('l'),
                        'close_price': result.get('c'),
                        'volume': result.get('v'),
                        'vwap': result.get('vw'),
                        'transactions': result.get('n')
                    }
                    
                    all_data.append(record)
                    self.logger.info(f"Fetched previous close for {symbol}: ${result.get('c')}")
                
            except Exception as e:
                self.logger.error(f"Failed to fetch previous close for {symbol}: {e}")
                continue
        
        if not all_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_data)
        return self.standardize_dataframe(df)
    
    def fetch_ticker_details(self, symbols: List[str]) -> pd.DataFrame:
        """
        Fetch detailed information about ticker symbols.
        
        Args:
            symbols: List of ticker symbols
            
        Returns:
            DataFrame with ticker details
        """
        symbols = self.validate_symbols(symbols)
        all_data = []
        
        for symbol in symbols:
            try:
                endpoint = f"/v3/reference/tickers/{symbol}"
                response = self._make_request(endpoint)
                
                if response.get('status') == 'OK' and response.get('results'):
                    result = response['results']
                    
                    record = {
                        'symbol': symbol,
                        'name': result.get('name'),
                        'market': result.get('market'),
                        'locale': result.get('locale'),
                        'primary_exchange': result.get('primary_exchange'),
                        'type': result.get('type'),
                        'currency_name': result.get('currency_name'),
                        'market_cap': result.get('market_cap'),
                        'share_class_outstanding': result.get('share_class_shares_outstanding'),
                        'weighted_shares_outstanding': result.get('weighted_shares_outstanding'),
                        'description': result.get('description'),
                        'homepage_url': result.get('homepage_url'),
                        'total_employees': result.get('total_employees')
                    }
                    
                    all_data.append(record)
                    self.logger.info(f"Fetched details for {symbol}")
                
            except Exception as e:
                self.logger.error(f"Failed to fetch details for {symbol}: {e}")
                continue
        
        return pd.DataFrame(all_data) if all_data else pd.DataFrame()
    
    def standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize DataFrame to common column names and formats.
        
        Args:
            df: Raw DataFrame from Polygon API
            
        Returns:
            Standardized DataFrame
        """
        if df.empty:
            return df
        
        # Ensure date column is properly typed
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date
        
        # Round price columns to appropriate decimal places
        price_columns = ['open_price', 'high_price', 'low_price', 'close_price', 'vwap']
        for col in price_columns:
            if col in df.columns:
                df[col] = df[col].round(4)
        
        # Sort by symbol and date
        if 'symbol' in df.columns and 'date' in df.columns:
            df = df.sort_values(['symbol', 'date'])
        
        return df.reset_index(drop=True) 