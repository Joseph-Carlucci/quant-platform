import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from typing import List, Optional, Dict, Any, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataLoader:
    """
    Data loading utility for the trading platform.
    
    Provides methods to load market data from the PostgreSQL database
    and prepare it for strategy backtesting and analysis.
    """
    
    def __init__(self, db_connection: str):
        """
        Initialize DataLoader.
        
        Args:
            db_connection: Database connection string
        """
        self.db_connection = db_connection
        self.engine = create_engine(db_connection)
        
    def load_daily_data(self, 
                       symbols: List[str],
                       start_date: Optional[str] = None,
                       end_date: Optional[str] = None,
                       columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Load daily market data for specified symbols.
        
        Args:
            symbols: List of trading symbols
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            columns: Specific columns to load (defaults to all)
            
        Returns:
            DataFrame with daily market data
        """
        # Default columns
        if columns is None:
            columns = ['ticker', 'date', 'open_price', 'high_price', 'low_price', 
                      'close_price', 'volume', 'vwap']
                      
        # Build query
        query = f"""
        SELECT {', '.join(columns)}
        FROM market_data.daily_aggregates
        WHERE ticker = ANY(%(symbols)s)
        """
        
        params = {'symbols': symbols}
        
        if start_date:
            query += " AND date >= %(start_date)s"
            params['start_date'] = start_date
            
        if end_date:
            query += " AND date <= %(end_date)s"
            params['end_date'] = end_date
            
        query += " ORDER BY ticker, date"
        
        try:
            df = pd.read_sql_query(text(query), self.engine, params=params)
            df['date'] = pd.to_datetime(df['date'])
            
            logger.info(f"Loaded {len(df)} daily records for {len(symbols)} symbols")
            return df
            
        except Exception as e:
            logger.error(f"Error loading daily data: {e}")
            raise
            
    def load_previous_close(self, 
                           symbols: List[str],
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Load previous close data for specified symbols.
        
        Args:
            symbols: List of trading symbols
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            
        Returns:
            DataFrame with previous close data
        """
        query = """
        SELECT ticker, date, close_price, open_price, high_price, 
               low_price, volume, pre_market, after_hours
        FROM market_data.previous_close
        WHERE ticker = ANY(%(symbols)s)
        """
        
        params = {'symbols': symbols}
        
        if start_date:
            query += " AND date >= %(start_date)s"
            params['start_date'] = start_date
            
        if end_date:
            query += " AND date <= %(end_date)s"
            params['end_date'] = end_date
            
        query += " ORDER BY ticker, date"
        
        try:
            df = pd.read_sql_query(text(query), self.engine, params=params)
            df['date'] = pd.to_datetime(df['date'])
            
            logger.info(f"Loaded {len(df)} previous close records")
            return df
            
        except Exception as e:
            logger.error(f"Error loading previous close data: {e}")
            raise
            
    def load_ticker_details(self, symbols: List[str]) -> pd.DataFrame:
        """
        Load ticker details for specified symbols.
        
        Args:
            symbols: List of trading symbols
            
        Returns:
            DataFrame with ticker details
        """
        query = """
        SELECT ticker, name, market, locale, primary_exchange, type,
               currency_name, market_cap, share_class_outstanding,
               weighted_shares_outstanding, description, homepage_url,
               total_employees
        FROM market_data.ticker_details
        WHERE ticker = ANY(%(symbols)s)
        """
        
        try:
            df = pd.read_sql_query(text(query), self.engine, params={'symbols': symbols})
            logger.info(f"Loaded details for {len(df)} tickers")
            return df
            
        except Exception as e:
            logger.error(f"Error loading ticker details: {e}")
            raise
            
    def get_available_symbols(self) -> List[str]:
        """
        Get list of available symbols in the database.
        
        Returns:
            List of available symbols
        """
        query = """
        SELECT DISTINCT ticker
        FROM market_data.daily_aggregates
        ORDER BY ticker
        """
        
        try:
            df = pd.read_sql_query(text(query), self.engine)
            symbols = df['ticker'].tolist()
            logger.info(f"Found {len(symbols)} available symbols")
            return symbols
            
        except Exception as e:
            logger.error(f"Error getting available symbols: {e}")
            raise
            
    def get_date_range(self, symbol: Optional[str] = None) -> Tuple[str, str]:
        """
        Get the date range of available data.
        
        Args:
            symbol: Optional symbol to get date range for (defaults to all)
            
        Returns:
            Tuple of (start_date, end_date) as strings
        """
        query = """
        SELECT MIN(date) as start_date, MAX(date) as end_date
        FROM market_data.daily_aggregates
        """
        
        params = {}
        if symbol:
            query += " WHERE ticker = %(symbol)s"
            params['symbol'] = symbol
            
        try:
            df = pd.read_sql_query(text(query), self.engine, params=params)
            start_date = df['start_date'].iloc[0].strftime('%Y-%m-%d')
            end_date = df['end_date'].iloc[0].strftime('%Y-%m-%d')
            
            logger.info(f"Date range: {start_date} to {end_date}")
            return start_date, end_date
            
        except Exception as e:
            logger.error(f"Error getting date range: {e}")
            raise
            
    def prepare_backtest_data(self,
                             symbols: List[str],
                             start_date: Optional[str] = None,
                             end_date: Optional[str] = None,
                             pivot: bool = True) -> pd.DataFrame:
        """
        Prepare data for backtesting.
        
        Args:
            symbols: List of trading symbols
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            pivot: Whether to pivot data (symbols as columns)
            
        Returns:
            DataFrame prepared for backtesting
        """
        # Load daily data
        df = self.load_daily_data(symbols, start_date, end_date)
        
        if df.empty:
            logger.warning("No data loaded for backtesting")
            return df
            
        # Clean data
        df = self._clean_data(df)
        
        if pivot:
            # Pivot data to have symbols as columns
            price_data = df.pivot_table(
                index='date',
                columns='ticker',
                values=['open_price', 'high_price', 'low_price', 'close_price', 'volume'],
                aggfunc='first'
            )
            
            # Flatten column names
            price_data.columns = [f"{col[1]}_{col[0]}" for col in price_data.columns]
            price_data = price_data.reset_index()
            
            return price_data
        else:
            return df
            
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean market data.
        
        Args:
            df: Raw market data DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        # Remove rows with missing critical data
        critical_columns = ['open_price', 'high_price', 'low_price', 'close_price']
        df = df.dropna(subset=critical_columns)
        
        # Remove rows with zero or negative prices
        for col in critical_columns:
            df = df[df[col] > 0]
            
        # Remove rows with invalid OHLC relationships
        df = df[
            (df['high_price'] >= df['low_price']) &
            (df['high_price'] >= df['open_price']) &
            (df['high_price'] >= df['close_price']) &
            (df['low_price'] <= df['open_price']) &
            (df['low_price'] <= df['close_price'])
        ]
        
        # Fill missing volume with 0
        df['volume'] = df['volume'].fillna(0)
        
        # Sort by date
        df = df.sort_values(['ticker', 'date']).reset_index(drop=True)
        
        logger.info(f"Data cleaned: {len(df)} records remaining")
        return df
        
    def get_statistics(self, symbols: List[str] = None) -> Dict[str, Any]:
        """
        Get data statistics.
        
        Args:
            symbols: Optional list of symbols (defaults to all)
            
        Returns:
            Dictionary with statistics
        """
        if symbols is None:
            symbols = self.get_available_symbols()
            
        stats = {}
        
        try:
            # Get date range
            start_date, end_date = self.get_date_range()
            stats['date_range'] = {'start': start_date, 'end': end_date}
            
            # Get record counts per symbol
            query = """
            SELECT ticker, COUNT(*) as record_count
            FROM market_data.daily_aggregates
            WHERE ticker = ANY(%(symbols)s)
            GROUP BY ticker
            ORDER BY ticker
            """
            
            df = pd.read_sql_query(text(query), self.engine, params={'symbols': symbols})
            stats['record_counts'] = dict(zip(df['ticker'], df['record_count']))
            
            # Get total records
            stats['total_records'] = df['record_count'].sum()
            stats['symbols_count'] = len(df)
            
            logger.info(f"Statistics: {stats['total_records']} records for {stats['symbols_count']} symbols")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise