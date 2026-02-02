"""
Configuration module for TLGeo2QGIS plugin.

This module provides centralized configuration management including:
- Database connection settings
- API endpoints
- Plugin constants
- Environment variable loading
"""

from .database import DatabaseConfig, TableNames, FieldNames, QueryTemplates

__all__ = [
    'DatabaseConfig',
    'TableNames',
    'FieldNames',
    'QueryTemplates'
]
