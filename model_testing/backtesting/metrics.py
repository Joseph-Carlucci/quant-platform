import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """
    Calculate performance metrics for backtesting results.
    
    Provides standard financial metrics like Sharpe ratio, maximum drawdown,
    volatility, and other key performance indicators.
    """
    
    def __init__(self, portfolio_history: pd.DataFrame, risk_free_rate: float = 0.02):
        """
        Initialize performance metrics calculator.
        
        Args:
            portfolio_history: DataFrame with portfolio value over time
            risk_free_rate: Annual risk-free rate for Sharpe ratio calculation
        """
        self.portfolio_history = portfolio_history.copy()
        self.risk_free_rate = risk_free_rate
        
        # Ensure timestamp is datetime
        if 'timestamp' in portfolio_history.columns:
            self.portfolio_history['timestamp'] = pd.to_datetime(portfolio_history['timestamp'])
            self.portfolio_history = self.portfolio_history.sort_values('timestamp')
            
        # Calculate returns
        self._calculate_returns()
        
    def _calculate_returns(self):
        """Calculate daily returns from portfolio values."""
        if 'total_value' not in self.portfolio_history.columns:
            raise ValueError("Portfolio history must contain 'total_value' column")
            
        self.portfolio_history['daily_return'] = self.portfolio_history['total_value'].pct_change()
        self.portfolio_history['cumulative_return'] = (
            1 + self.portfolio_history['daily_return']
        ).cumprod() - 1
        
    def total_return(self) -> float:
        """Calculate total return over the entire period."""
        if len(self.portfolio_history) < 2:
            return 0.0
            
        initial_value = self.portfolio_history['total_value'].iloc[0]
        final_value = self.portfolio_history['total_value'].iloc[-1]
        
        return (final_value - initial_value) / initial_value
        
    def annualized_return(self) -> float:
        """Calculate annualized return."""
        if len(self.portfolio_history) < 2:
            return 0.0
            
        total_ret = self.total_return()
        
        # Calculate number of years
        start_date = self.portfolio_history['timestamp'].iloc[0]
        end_date = self.portfolio_history['timestamp'].iloc[-1]
        years = (end_date - start_date).days / 365.25
        
        if years <= 0:
            return 0.0
            
        return (1 + total_ret) ** (1 / years) - 1
        
    def volatility(self, annualized: bool = True) -> float:
        """
        Calculate volatility (standard deviation of returns).
        
        Args:
            annualized: Whether to annualize the volatility
        """
        if len(self.portfolio_history) < 2:
            return 0.0
            
        daily_returns = self.portfolio_history['daily_return'].dropna()
        daily_vol = daily_returns.std()
        
        if annualized:
            return daily_vol * np.sqrt(252)  # Assuming 252 trading days per year
        else:
            return daily_vol
            
    def sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio."""
        if len(self.portfolio_history) < 2:
            return 0.0
            
        annual_return = self.annualized_return()
        annual_vol = self.volatility(annualized=True)
        
        if annual_vol == 0:
            return 0.0
            
        return (annual_return - self.risk_free_rate) / annual_vol
        
    def sortino_ratio(self, target_return: float = 0.0) -> float:
        """
        Calculate Sortino ratio (downside deviation version of Sharpe).
        
        Args:
            target_return: Target return threshold
        """
        if len(self.portfolio_history) < 2:
            return 0.0
            
        daily_returns = self.portfolio_history['daily_return'].dropna()
        annual_return = self.annualized_return()
        
        # Calculate downside deviation
        downside_returns = daily_returns[daily_returns < target_return / 252]
        if len(downside_returns) == 0:
            return np.inf
            
        downside_deviation = downside_returns.std() * np.sqrt(252)
        
        if downside_deviation == 0:
            return 0.0
            
        return (annual_return - self.risk_free_rate) / downside_deviation
        
    def max_drawdown(self) -> float:
        """Calculate maximum drawdown."""
        if len(self.portfolio_history) < 2:
            return 0.0
            
        portfolio_values = self.portfolio_history['total_value']
        
        # Calculate rolling maximum
        rolling_max = portfolio_values.expanding().max()
        
        # Calculate drawdown
        drawdown = (portfolio_values - rolling_max) / rolling_max
        
        return abs(drawdown.min())
        
    def calmar_ratio(self) -> float:
        """Calculate Calmar ratio (annual return / max drawdown)."""
        annual_ret = self.annualized_return()
        max_dd = self.max_drawdown()
        
        if max_dd == 0:
            return np.inf if annual_ret > 0 else 0.0
            
        return annual_ret / max_dd
        
    def value_at_risk(self, confidence_level: float = 0.05) -> float:
        """
        Calculate Value at Risk (VaR).
        
        Args:
            confidence_level: Confidence level (e.g., 0.05 for 95% VaR)
        """
        if len(self.portfolio_history) < 2:
            return 0.0
            
        daily_returns = self.portfolio_history['daily_return'].dropna()
        return daily_returns.quantile(confidence_level)
        
    def conditional_value_at_risk(self, confidence_level: float = 0.05) -> float:
        """
        Calculate Conditional Value at Risk (CVaR or Expected Shortfall).
        
        Args:
            confidence_level: Confidence level (e.g., 0.05 for 95% CVaR)
        """
        if len(self.portfolio_history) < 2:
            return 0.0
            
        daily_returns = self.portfolio_history['daily_return'].dropna()
        var = self.value_at_risk(confidence_level)
        
        # Expected value of returns below VaR threshold
        tail_returns = daily_returns[daily_returns <= var]
        
        return tail_returns.mean() if len(tail_returns) > 0 else 0.0
        
    def beta(self, benchmark_returns: pd.Series) -> float:
        """
        Calculate beta relative to a benchmark.
        
        Args:
            benchmark_returns: Series of benchmark returns
        """
        if len(self.portfolio_history) < 2:
            return 0.0
            
        portfolio_returns = self.portfolio_history['daily_return'].dropna()
        
        # Align returns by index/date
        aligned_data = pd.DataFrame({
            'portfolio': portfolio_returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        if len(aligned_data) < 2:
            return 0.0
            
        covariance = aligned_data['portfolio'].cov(aligned_data['benchmark'])
        benchmark_variance = aligned_data['benchmark'].var()
        
        if benchmark_variance == 0:
            return 0.0
            
        return covariance / benchmark_variance
        
    def alpha(self, benchmark_returns: pd.Series) -> float:
        """
        Calculate alpha relative to a benchmark.
        
        Args:
            benchmark_returns: Series of benchmark returns
        """
        portfolio_return = self.annualized_return()
        beta = self.beta(benchmark_returns)
        
        # Calculate benchmark return
        benchmark_return = (1 + benchmark_returns).prod() ** (252 / len(benchmark_returns)) - 1
        
        return portfolio_return - (self.risk_free_rate + beta * (benchmark_return - self.risk_free_rate))
        
    def information_ratio(self, benchmark_returns: pd.Series) -> float:
        """
        Calculate information ratio.
        
        Args:
            benchmark_returns: Series of benchmark returns
        """
        if len(self.portfolio_history) < 2:
            return 0.0
            
        portfolio_returns = self.portfolio_history['daily_return'].dropna()
        
        # Align returns
        aligned_data = pd.DataFrame({
            'portfolio': portfolio_returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        if len(aligned_data) < 2:
            return 0.0
            
        excess_returns = aligned_data['portfolio'] - aligned_data['benchmark']
        tracking_error = excess_returns.std() * np.sqrt(252)
        
        if tracking_error == 0:
            return 0.0
            
        return excess_returns.mean() * 252 / tracking_error
        
    def winning_percentage(self) -> float:
        """Calculate percentage of winning trades/periods."""
        if len(self.portfolio_history) < 2:
            return 0.0
            
        daily_returns = self.portfolio_history['daily_return'].dropna()
        winning_days = (daily_returns > 0).sum()
        
        return winning_days / len(daily_returns) * 100
        
    def average_win(self) -> float:
        """Calculate average winning day return."""
        if len(self.portfolio_history) < 2:
            return 0.0
            
        daily_returns = self.portfolio_history['daily_return'].dropna()
        winning_returns = daily_returns[daily_returns > 0]
        
        return winning_returns.mean() if len(winning_returns) > 0 else 0.0
        
    def average_loss(self) -> float:
        """Calculate average losing day return."""
        if len(self.portfolio_history) < 2:
            return 0.0
            
        daily_returns = self.portfolio_history['daily_return'].dropna()
        losing_returns = daily_returns[daily_returns < 0]
        
        return losing_returns.mean() if len(losing_returns) > 0 else 0.0
        
    def profit_factor(self) -> float:
        """Calculate profit factor (total wins / total losses)."""
        avg_win = self.average_win()
        avg_loss = abs(self.average_loss())
        
        if avg_loss == 0:
            return np.inf if avg_win > 0 else 0.0
            
        win_pct = self.winning_percentage() / 100
        loss_pct = 1 - win_pct
        
        if loss_pct == 0:
            return np.inf
            
        return (avg_win * win_pct) / (avg_loss * loss_pct)
        
    def get_all_metrics(self) -> Dict[str, float]:
        """Get all performance metrics as a dictionary."""
        metrics = {
            'total_return': self.total_return(),
            'annualized_return': self.annualized_return(),
            'volatility': self.volatility(),
            'sharpe_ratio': self.sharpe_ratio(),
            'sortino_ratio': self.sortino_ratio(),
            'max_drawdown': self.max_drawdown(),
            'calmar_ratio': self.calmar_ratio(),
            'value_at_risk_5pct': self.value_at_risk(0.05),
            'conditional_var_5pct': self.conditional_value_at_risk(0.05),
            'winning_percentage': self.winning_percentage(),
            'average_win': self.average_win(),
            'average_loss': self.average_loss(),
            'profit_factor': self.profit_factor()
        }
        
        return metrics
        
    def print_summary(self):
        """Print a summary of all performance metrics."""
        metrics = self.get_all_metrics()
        
        print("\n" + "="*50)
        print("PERFORMANCE SUMMARY")
        print("="*50)
        
        print(f"Total Return:        {metrics['total_return']:.2%}")
        print(f"Annualized Return:   {metrics['annualized_return']:.2%}")
        print(f"Volatility:          {metrics['volatility']:.2%}")
        print(f"Sharpe Ratio:        {metrics['sharpe_ratio']:.3f}")
        print(f"Sortino Ratio:       {metrics['sortino_ratio']:.3f}")
        print(f"Max Drawdown:        {metrics['max_drawdown']:.2%}")
        print(f"Calmar Ratio:        {metrics['calmar_ratio']:.3f}")
        print(f"VaR (5%):           {metrics['value_at_risk_5pct']:.2%}")
        print(f"CVaR (5%):          {metrics['conditional_var_5pct']:.2%}")
        print(f"Winning %:           {metrics['winning_percentage']:.1f}%")
        print(f"Average Win:         {metrics['average_win']:.2%}")
        print(f"Average Loss:        {metrics['average_loss']:.2%}")
        print(f"Profit Factor:       {metrics['profit_factor']:.2f}")
        print("="*50)