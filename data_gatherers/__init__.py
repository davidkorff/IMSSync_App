"""
Data Gatherers Package - Collection of source-specific data gatherers
"""
from typing import Dict, Any, Type, Optional
import importlib
import os

from data_gatherers.base_gatherer import BaseDataGatherer
from data_gatherers.csv_gatherer import CSVDataGatherer
from data_gatherers.tritan_gatherer import TritanDataGatherer

# Register all available gatherers
GATHERERS = {
    'csv': CSVDataGatherer,
    'tritan': TritanDataGatherer,
    # Add more gatherers as they are implemented
}

def get_gatherer(source_type: str, **kwargs) -> Optional[BaseDataGatherer]:
    """
    Get a data gatherer instance for the specified source type
    
    Args:
        source_type: Type of source system
        **kwargs: Additional arguments to pass to the gatherer constructor
        
    Returns:
        BaseDataGatherer: Data gatherer instance, or None if not found
    """
    gatherer_class = GATHERERS.get(source_type.lower())
    
    if gatherer_class is None:
        return None
        
    return gatherer_class(**kwargs)

def list_gatherers() -> Dict[str, Type[BaseDataGatherer]]:
    """
    List all available gatherers
    
    Returns:
        Dict[str, Type[BaseDataGatherer]]: Dictionary of gatherer types and classes
    """
    return GATHERERS 