"""
Data Ingestion Module

This module provides standardized interfaces for ingesting data from various external sources
into the quantitative trading platform.

Key Components:
- polygon_client: Polygon.io API integration
- base_ingestion: Base classes for data source adapters
"""

try:
    from .polygon_client import PolygonClient
    from .base_ingestion import BaseDataSource
    __all__ = ['PolygonClient', 'BaseDataSource']
except ImportError:
    # Handle import errors gracefully
    __all__ = [] 