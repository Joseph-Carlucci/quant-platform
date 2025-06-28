import os
import json
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class BacktestConfig:
    initial_capital: float = 100000.0
    commission: float = 0.001
    slippage: float = 0.0005
    min_commission: float = 1.0
    
@dataclass
class RiskConfig:
    max_position_size: float = 0.1
    stop_loss_pct: float = 0.02
    max_drawdown: float = 0.15
    max_leverage: float = 1.0
    position_sizing_method: str = "fixed_fractional"
    
@dataclass
class DataConfig:
    db_connection: str = "postgresql://quant_user:quant_password@postgres:5432/quant_data"
    data_frequency: str = "daily"
    lookback_period: int = 252  # 1 year of daily data
    
@dataclass
class ExecutionConfig:
    broker: str = "simulation"
    execution_delay: float = 0.0  # seconds
    market_impact: float = 0.0001
    
class Config:
    """
    Configuration management system for the trading platform.
    
    Supports loading configuration from:
    - JSON files
    - YAML files
    - Environment variables
    - Direct dictionary input
    """
    
    def __init__(self, config_file: Optional[str] = None):
        # Default configurations
        self.backtest = BacktestConfig()
        self.risk = RiskConfig()
        self.data = DataConfig()
        self.execution = ExecutionConfig()
        self.custom: Dict[str, Any] = {}
        
        # Load from file if provided
        if config_file:
            self.load_from_file(config_file)
            
        # Override with environment variables
        self._load_from_env()
        
    def load_from_file(self, config_file: str) -> None:
        """
        Load configuration from a file.
        
        Args:
            config_file: Path to configuration file (JSON or YAML)
        """
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
            
        with open(config_file, 'r') as f:
            if config_file.endswith('.json'):
                config_data = json.load(f)
            elif config_file.endswith(('.yaml', '.yml')):
                config_data = yaml.safe_load(f)
            else:
                raise ValueError("Configuration file must be JSON or YAML")
                
        self.load_from_dict(config_data)
        logger.info(f"Configuration loaded from {config_file}")
        
    def load_from_dict(self, config_data: Dict[str, Any]) -> None:
        """
        Load configuration from a dictionary.
        
        Args:
            config_data: Configuration dictionary
        """
        # Update backtest configuration
        if 'backtest' in config_data:
            backtest_data = config_data['backtest']
            for key, value in backtest_data.items():
                if hasattr(self.backtest, key):
                    setattr(self.backtest, key, value)
                    
        # Update risk configuration
        if 'risk' in config_data:
            risk_data = config_data['risk']
            for key, value in risk_data.items():
                if hasattr(self.risk, key):
                    setattr(self.risk, key, value)
                    
        # Update data configuration
        if 'data' in config_data:
            data_config = config_data['data']
            for key, value in data_config.items():
                if hasattr(self.data, key):
                    setattr(self.data, key, value)
                    
        # Update execution configuration
        if 'execution' in config_data:
            execution_data = config_data['execution']
            for key, value in execution_data.items():
                if hasattr(self.execution, key):
                    setattr(self.execution, key, value)
                    
        # Store any custom configuration
        for key, value in config_data.items():
            if key not in ['backtest', 'risk', 'data', 'execution']:
                self.custom[key] = value
                
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Backtest configuration
        if os.getenv('BACKTEST_INITIAL_CAPITAL'):
            self.backtest.initial_capital = float(os.getenv('BACKTEST_INITIAL_CAPITAL'))
        if os.getenv('BACKTEST_COMMISSION'):
            self.backtest.commission = float(os.getenv('BACKTEST_COMMISSION'))
        if os.getenv('BACKTEST_SLIPPAGE'):
            self.backtest.slippage = float(os.getenv('BACKTEST_SLIPPAGE'))
            
        # Risk configuration
        if os.getenv('RISK_MAX_POSITION_SIZE'):
            self.risk.max_position_size = float(os.getenv('RISK_MAX_POSITION_SIZE'))
        if os.getenv('RISK_STOP_LOSS_PCT'):
            self.risk.stop_loss_pct = float(os.getenv('RISK_STOP_LOSS_PCT'))
        if os.getenv('RISK_MAX_DRAWDOWN'):
            self.risk.max_drawdown = float(os.getenv('RISK_MAX_DRAWDOWN'))
            
        # Data configuration
        if os.getenv('DATA_DB_CONNECTION'):
            self.data.db_connection = os.getenv('DATA_DB_CONNECTION')
        if os.getenv('DATA_FREQUENCY'):
            self.data.data_frequency = os.getenv('DATA_FREQUENCY')
            
    def save_to_file(self, config_file: str) -> None:
        """
        Save configuration to a file.
        
        Args:
            config_file: Path to save configuration file
        """
        config_data = self.to_dict()
        
        with open(config_file, 'w') as f:
            if config_file.endswith('.json'):
                json.dump(config_data, f, indent=2)
            elif config_file.endswith(('.yaml', '.yml')):
                yaml.dump(config_data, f, default_flow_style=False)
            else:
                raise ValueError("Configuration file must be JSON or YAML")
                
        logger.info(f"Configuration saved to {config_file}")
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Configuration as dictionary
        """
        return {
            'backtest': asdict(self.backtest),
            'risk': asdict(self.risk),
            'data': asdict(self.data),
            'execution': asdict(self.execution),
            **self.custom
        }
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'risk.max_position_size')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        
        if len(keys) == 1:
            # Top-level key
            if hasattr(self, keys[0]):
                return getattr(self, keys[0])
            else:
                return self.custom.get(keys[0], default)
        elif len(keys) == 2:
            # Nested key
            section, attr = keys
            if hasattr(self, section):
                section_obj = getattr(self, section)
                if hasattr(section_obj, attr):
                    return getattr(section_obj, attr)
            return default
        else:
            # Deeper nesting not supported
            return default
            
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        
        if len(keys) == 1:
            # Top-level key
            if hasattr(self, keys[0]):
                setattr(self, keys[0], value)
            else:
                self.custom[keys[0]] = value
        elif len(keys) == 2:
            # Nested key
            section, attr = keys
            if hasattr(self, section):
                section_obj = getattr(self, section)
                if hasattr(section_obj, attr):
                    setattr(section_obj, attr, value)
            else:
                # Create nested structure in custom
                if section not in self.custom:
                    self.custom[section] = {}
                self.custom[section][attr] = value
                
    def validate(self) -> bool:
        """
        Validate configuration values.
        
        Returns:
            True if configuration is valid
        """
        errors = []
        
        # Validate backtest configuration
        if self.backtest.initial_capital <= 0:
            errors.append("Initial capital must be positive")
        if self.backtest.commission < 0:
            errors.append("Commission cannot be negative")
        if self.backtest.slippage < 0:
            errors.append("Slippage cannot be negative")
            
        # Validate risk configuration
        if not 0 < self.risk.max_position_size <= 1:
            errors.append("Max position size must be between 0 and 1")
        if self.risk.stop_loss_pct < 0:
            errors.append("Stop loss percentage cannot be negative")
        if not 0 < self.risk.max_drawdown <= 1:
            errors.append("Max drawdown must be between 0 and 1")
            
        if errors:
            for error in errors:
                logger.error(f"Configuration validation error: {error}")
            return False
            
        return True
        
    def __str__(self) -> str:
        return f"Config(backtest={self.backtest}, risk={self.risk}, data={self.data})"