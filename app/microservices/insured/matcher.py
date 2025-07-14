"""
Insured matching logic for fuzzy matching
"""

import re
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher


class InsuredMatcher:
    """
    Helper class for matching insureds using fuzzy logic
    """
    
    def __init__(self):
        self.name_weight = 0.5
        self.address_weight = 0.3
        self.tax_id_weight = 0.2
        self.match_threshold = 0.8
    
    def find_best_match(self, criteria: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find the best matching insured from candidates
        
        Args:
            criteria: Search criteria
            candidates: List of candidate insureds
            
        Returns:
            Best matching insured or None
        """
        if not candidates:
            return None
        
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            score = self.calculate_match_score(criteria, candidate)
            if score > best_score and score >= self.match_threshold:
                best_score = score
                best_match = candidate
        
        return best_match
    
    def calculate_match_score(self, criteria: Dict[str, Any], candidate: Dict[str, Any]) -> float:
        """
        Calculate match score between criteria and candidate
        
        Args:
            criteria: Search criteria
            candidate: Candidate insured
            
        Returns:
            Match score between 0 and 1
        """
        score = 0.0
        total_weight = 0.0
        
        # Name matching
        if criteria.get('name') and candidate.get('name'):
            name_score = self._fuzzy_match(
                self._normalize_name(criteria['name']),
                self._normalize_name(candidate['name'])
            )
            score += name_score * self.name_weight
            total_weight += self.name_weight
        
        # Tax ID matching (exact match only)
        if criteria.get('tax_id') and candidate.get('tax_id'):
            tax_id_score = 1.0 if criteria['tax_id'] == candidate['tax_id'] else 0.0
            score += tax_id_score * self.tax_id_weight
            total_weight += self.tax_id_weight
        
        # Address matching
        if criteria.get('address') and candidate.get('address'):
            address_score = self._fuzzy_match(
                self._normalize_address(criteria['address']),
                self._normalize_address(candidate['address'])
            )
            score += address_score * self.address_weight
            total_weight += self.address_weight
        
        # Normalize score
        if total_weight > 0:
            return score / total_weight
        
        return 0.0
    
    def _fuzzy_match(self, str1: str, str2: str) -> float:
        """
        Calculate fuzzy match score between two strings
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Match score between 0 and 1
        """
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize company name for matching
        
        Args:
            name: Company name
            
        Returns:
            Normalized name
        """
        # Remove common suffixes
        suffixes = [
            r'\s+LLC$', r'\s+L\.L\.C\.$', r'\s+INC$', r'\s+Inc\.$',
            r'\s+CORP$', r'\s+Corp\.$', r'\s+Corporation$',
            r'\s+LTD$', r'\s+Ltd\.$', r'\s+Limited$',
            r'\s+LP$', r'\s+L\.P\.$', r'\s+LLP$',
            r'\s+PLLC$', r'\s+P\.L\.L\.C\.$',
            r'\s+PC$', r'\s+P\.C\.$'
        ]
        
        normalized = name
        for suffix in suffixes:
            normalized = re.sub(suffix, '', normalized, flags=re.IGNORECASE)
        
        # Remove extra spaces and punctuation
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = ' '.join(normalized.split())
        
        return normalized.strip()
    
    def _normalize_address(self, address: str) -> str:
        """
        Normalize address for matching
        
        Args:
            address: Address string
            
        Returns:
            Normalized address
        """
        # Common abbreviations
        replacements = {
            r'\bSTREET\b': 'ST',
            r'\bSTR\b': 'ST',
            r'\bAVENUE\b': 'AVE',
            r'\bAV\b': 'AVE',
            r'\bROAD\b': 'RD',
            r'\bDRIVE\b': 'DR',
            r'\bLANE\b': 'LN',
            r'\bBOULEVARD\b': 'BLVD',
            r'\bPARKWAY\b': 'PKWY',
            r'\bNORTH\b': 'N',
            r'\bSOUTH\b': 'S',
            r'\bEAST\b': 'E',
            r'\bWEST\b': 'W',
            r'\bSUITE\b': 'STE',
            r'\bAPARTMENT\b': 'APT',
            r'\bAPT\b': 'APT',
            r'\bFLOOR\b': 'FL',
            r'\bBUILDING\b': 'BLDG'
        }
        
        normalized = address.upper()
        
        for pattern, replacement in replacements.items():
            normalized = re.sub(pattern, replacement, normalized)
        
        # Remove extra spaces and punctuation
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = ' '.join(normalized.split())
        
        return normalized.strip()