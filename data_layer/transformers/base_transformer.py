"""
Base Transformer Class

Provides the abstract interface for all data transformers in the quantitative platform.
All transformers must inherit from this base class to ensure consistent interfaces.
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class BaseTransformer(ABC):
    """
    Abstract base class for all data transformers.
    
    A transformer takes raw data as input and produces analysis-ready data as output.
    This could be technical indicators, fundamental ratios, sentiment scores, etc.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the transformer with optional configuration.
        
        Args:
            config: Dictionary containing transformer-specific configuration
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        
    @abstractmethod
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transform raw data into analysis-ready format.
        
        Args:
            data: Input DataFrame with raw data
            
        Returns:
            DataFrame with transformed data
            
        Raises:
            ValueError: If input data doesn't meet requirements
        """
        pass
    
    @abstractmethod
    def get_output_schema(self) -> Dict[str, str]:
        """
        Return the schema of the transformed data.
        
        Returns:
            Dictionary mapping column names to SQL data types
        """
        pass
    
    def get_required_columns(self) -> List[str]:
        """
        Return the list of required input columns.
        
        Returns:
            List of required column names
        """
        return []
    
    def validate_input(self, data: pd.DataFrame) -> bool:
        """
        Validate that input data meets requirements.
        
        Args:
            data: Input DataFrame to validate
            
        Returns:
            True if data is valid
            
        Raises:
            ValueError: If data doesn't meet requirements
        """
        # Check required columns exist
        required_cols = self.get_required_columns()
        missing_cols = set(required_cols) - set(data.columns)
        
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Check for empty data
        if data.empty:
            raise ValueError("Input data is empty")
        
        logger.debug(f"{self.name}: Input validation passed")
        return True
    
    def validate_output(self, data: pd.DataFrame) -> bool:
        """
        Validate that output data meets quality standards.
        
        Args:
            data: Output DataFrame to validate
            
        Returns:
            True if data passes quality checks
        """
        if data.empty:
            logger.warning(f"{self.name}: Output data is empty")
            return False
        
        # Check for excessive missing values
        for col in data.columns:
            if data[col].dtype in ['float64', 'int64']:
                missing_pct = data[col].isna().mean()
                if missing_pct > 0.5:  # More than 50% missing
                    logger.warning(f"{self.name}: Column '{col}' has {missing_pct:.1%} missing values")
        
        logger.debug(f"{self.name}: Output validation passed")
        return True
    
    def transform_safe(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transform data with validation and error handling.
        
        Args:
            data: Input DataFrame
            
        Returns:
            Transformed DataFrame
        """
        try:
            # Validate input
            self.validate_input(data)
            
            # Perform transformation
            logger.info(f"{self.name}: Starting transformation of {len(data)} rows")
            result = self.transform(data)
            
            # Validate output
            self.validate_output(result)
            
            logger.info(f"{self.name}: Transformation complete, output has {len(result)} rows")
            return result
            
        except Exception as e:
            logger.error(f"{self.name}: Transformation failed: {e}")
            raise
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Return metadata about this transformer.
        
        Returns:
            Dictionary with transformer metadata
        """
        return {
            'name': self.name,
            'config': self.config,
            'required_columns': self.get_required_columns(),
            'output_schema': self.get_output_schema()
        }


class TransformationPipeline:
    """
    A pipeline that chains multiple transformers together.
    """
    
    def __init__(self, transformers: List[BaseTransformer]):
        """
        Initialize pipeline with list of transformers.
        
        Args:
            transformers: List of transformer instances to chain
        """
        self.transformers = transformers
        
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Apply all transformers in sequence.
        
        Args:
            data: Input DataFrame
            
        Returns:
            DataFrame after all transformations
        """
        result = data.copy()
        
        for transformer in self.transformers:
            logger.info(f"Pipeline: Applying {transformer.name}")
            result = transformer.transform_safe(result)
            
        return result
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Return metadata about the entire pipeline.
        
        Returns:
            Dictionary with pipeline metadata
        """
        return {
            'transformers': [t.get_metadata() for t in self.transformers],
            'total_transformers': len(self.transformers)
        } 