"""
CSV Data Gatherer - Data gatherer for CSV files
"""
import csv
import os
from typing import List, Dict, Any
from datetime import datetime
import re
from decimal import Decimal

from data_gatherers.base_gatherer import BaseDataGatherer
from ims_data_model import (
    PolicyData, 
    InsuredParty, 
    PolicyParty, 
    PolicyLimit,
    PolicyDeductible,
    PolicyCommission
)


class CSVDataGatherer(BaseDataGatherer):
    """Data gatherer for CSV files"""
    
    def __init__(self, file_path: str, config: Dict[str, Any] = None):
        """
        Initialize the CSV data gatherer
        
        Args:
            file_path: Path to the CSV file
            config: Configuration for the gatherer
        """
        super().__init__('csv', config)
        self.file_path = file_path
        self.file = None
        
    def connect(self) -> bool:
        """
        Connect to the CSV file
        
        Returns:
            bool: True if file exists, False otherwise
        """
        if not os.path.exists(self.file_path):
            self.logger.error(f"CSV file not found: {self.file_path}")
            return False
            
        self.logger.info(f"Connected to CSV file: {self.file_path}")
        return True
    
    def disconnect(self) -> None:
        """Disconnect from the CSV file"""
        self.file = None
        self.logger.info("Disconnected from CSV file")
    
    def get_policies(self, filters: Dict[str, Any] = None) -> List[PolicyData]:
        """
        Get policies from the CSV file based on optional filters
        
        Args:
            filters: Optional filters to apply when retrieving policies
            
        Returns:
            List[PolicyData]: List of policies in the common data model format
        """
        policies = []
        
        try:
            with open(self.file_path, 'r') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Apply filters if specified
                    if filters and not self._apply_filters(row, filters):
                        continue
                    
                    try:
                        policy = self._map_row_to_policy(row)
                        policies.append(policy)
                    except Exception as e:
                        self.logger.error(f"Error mapping row to policy: {e}")
                        continue
                
        except Exception as e:
            self.logger.error(f"Error reading CSV file: {e}")
            
        self.logger.info(f"Retrieved {len(policies)} policies from CSV file")
        return policies
    
    def _apply_filters(self, row: Dict[str, str], filters: Dict[str, Any]) -> bool:
        """
        Apply filters to a row
        
        Args:
            row: CSV row
            filters: Filters to apply
            
        Returns:
            bool: True if row passes filters, False otherwise
        """
        for field, value in filters.items():
            if field not in row or row[field] != value:
                return False
        return True
    
    def _map_row_to_policy(self, row: Dict[str, str]) -> PolicyData:
        """
        Map a CSV row to a PolicyData object
        
        Args:
            row: CSV row
            
        Returns:
            PolicyData: Policy data object
        """
        # Extract and clean premium
        premium = self._parse_currency(row.get('Gross Premium', '0'))
        
        # Parse limits
        limits = []
        limit_str = row.get('Limit', '')
        if limit_str:
            limit_parts = limit_str.split('/')
            if len(limit_parts) == 2:
                limits.append(PolicyLimit(
                    type='Occurrence',
                    amount=self._clean_currency(limit_parts[0]),
                    aggregate=self._clean_currency(limit_parts[1])
                ))
            else:
                limits.append(PolicyLimit(
                    type='Occurrence',
                    amount=self._clean_currency(limit_str)
                ))
        
        # Parse deductibles
        deductibles = []
        deductible_str = row.get('Deductible', '')
        if deductible_str:
            deductibles.append(PolicyDeductible(
                type='Standard',
                amount=self._clean_currency(deductible_str)
            ))
        
        # Create commission data
        commission = PolicyCommission(
            producer_percentage=self._parse_decimal(row.get('Commission Percent', '0')),
            terms_of_payment=1  # Default
        )
        
        # Map the row to a PolicyData object
        return PolicyData(
            policy_number=row.get('Policy Number/Certificate Ref.', ''),
            program=row.get('Program', ''),
            line_of_business=row.get('Class of Business', ''),
            
            effective_date=self._parse_date(row.get('Effective Date', '')),
            expiration_date=self._parse_date(row.get('Expiration Date', '')),
            bound_date=self._parse_date(row.get('Bound Date', '')),
            
            insured=InsuredParty(
                name=row.get('Insured', ''),
                state=row.get('Insured State', ''),
                zip_code=row.get('Insured Zip', '')
            ),
            
            producer=PolicyParty(
                name=row.get('Producer', '')
            ),
            
            underwriter=PolicyParty(
                name=row.get('Underwriter', '')
            ),
            
            limits=limits,
            deductibles=deductibles,
            commission=commission,
            
            premium=premium,
            
            additional_info={
                'umr': row.get('Unique Market Reference (UMR)', ''),
                'agreement_no': row.get('Agreement No', ''),
                'section_no': row.get('Section No', ''),
                'broker': row.get('Parent Broker/Customer/Agency', ''),
                'transaction_type': row.get('Transaction Type', '')
            }
        )
    
    def _parse_date(self, date_str: str):
        """Parse date string to datetime.date object"""
        if not date_str:
            return None
            
        try:
            return datetime.strptime(date_str, '%m/%d/%Y').date()
        except ValueError:
            self.logger.warning(f"Invalid date format: {date_str}")
            return None
    
    def _parse_currency(self, currency_str: str) -> float:
        """Parse currency string to float"""
        if not currency_str:
            return 0.0
            
        try:
            # Remove currency symbols, commas, etc.
            clean_str = re.sub(r'[^\d.]', '', currency_str)
            return float(clean_str)
        except ValueError:
            self.logger.warning(f"Invalid currency format: {currency_str}")
            return 0.0
    
    def _clean_currency(self, currency_str: str) -> str:
        """Clean currency string for storage in the data model"""
        # Just return the string with dollar signs and commas removed
        return currency_str.strip().replace('$', '').replace(',', '')
            
    def _parse_decimal(self, decimal_str: str) -> float:
        """Parse decimal string to float"""
        if not decimal_str:
            return 0.0
            
        try:
            return float(decimal_str)
        except ValueError:
            self.logger.warning(f"Invalid decimal format: {decimal_str}")
            return 0.0 