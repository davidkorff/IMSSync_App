"""
Base Data Gatherer - Abstract base class for all source-specific data gatherers
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging
from ims_data_model import PolicyData


class BaseDataGatherer(ABC):
    """Abstract base class for all source-specific data gatherers"""
    
    def __init__(self, source_name: str, config: Dict[str, Any] = None):
        """
        Initialize the data gatherer
        
        Args:
            source_name: Name of the source system
            config: Configuration for the gatherer
        """
        self.source_name = source_name
        self.config = config or {}
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for the gatherer"""
        logger = logging.getLogger(f'gatherer.{self.source_name}')
        logger.setLevel(logging.INFO)
        
        # Create handlers if they don't exist
        if not logger.handlers:
            # Create handlers
            file_handler = logging.FileHandler(f'{self.source_name}_gatherer.log')
            console_handler = logging.StreamHandler()
            
            # Create formatters and add to handlers
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # Add handlers to the logger
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the source system
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_policies(self, filters: Dict[str, Any] = None) -> List[PolicyData]:
        """
        Get policies from the source system based on optional filters
        
        Args:
            filters: Optional filters to apply when retrieving policies
            
        Returns:
            List[PolicyData]: List of policies in the common data model format
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the source system"""
        pass
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect() 