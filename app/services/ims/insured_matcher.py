"""
Enhanced insured matching logic

This module provides sophisticated matching algorithms to find existing insureds
in IMS before creating duplicates.
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from difflib import SequenceMatcher
from app.services.ims.base_service import BaseIMSService

logger = logging.getLogger(__name__)


class InsuredMatcher:
    """Advanced matching logic for finding existing insureds"""
    
    # Common business entity suffixes to normalize
    BUSINESS_SUFFIXES = [
        "LLC", "L.L.C.", "LIMITED LIABILITY COMPANY",
        "INC", "INC.", "INCORPORATED", 
        "CORP", "CORP.", "CORPORATION",
        "CO", "CO.", "COMPANY",
        "LTD", "LTD.", "LIMITED",
        "LP", "L.P.", "LIMITED PARTNERSHIP",
        "LLP", "L.L.P.", "LIMITED LIABILITY PARTNERSHIP",
        "PA", "P.A.", "PROFESSIONAL ASSOCIATION",
        "PC", "P.C.", "PROFESSIONAL CORPORATION",
        "PLLC", "P.L.L.C.", "PROFESSIONAL LIMITED LIABILITY COMPANY"
    ]
    
    # Common name variations
    NAME_VARIATIONS = {
        "&": ["AND"],
        "AND": ["&"],
        "ASSOC": ["ASSOCIATES", "ASSOCIATION"],
        "ASSOCIATES": ["ASSOC"],
        "ASSOCIATION": ["ASSOC"],
        "INTL": ["INTERNATIONAL"],
        "INTERNATIONAL": ["INTL"],
        "MGMT": ["MANAGEMENT"],
        "MANAGEMENT": ["MGMT"],
        "SVCS": ["SERVICES"],
        "SERVICES": ["SVCS"],
        "GRP": ["GROUP"],
        "GROUP": ["GRP"],
        "DIST": ["DISTRIBUTION", "DISTRIBUTORS"],
        "DISTRIBUTION": ["DIST"],
        "MFG": ["MANUFACTURING"],
        "MANUFACTURING": ["MFG"]
    }
    
    def __init__(self, insured_service: BaseIMSService):
        self.insured_service = insured_service
    
    def find_best_match(self, search_criteria: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find the best matching insured using multiple criteria
        
        Args:
            search_criteria: Dictionary containing search fields like name, tax_id, address, etc.
            
        Returns:
            Best matching insured or None if no good match found
        """
        insured_name = search_criteria.get("name", "")
        tax_id = search_criteria.get("tax_id")
        
        if not insured_name:
            logger.warning("No insured name provided for matching")
            return None
        
        # Step 1: Try exact tax ID match if provided
        if tax_id and self._is_valid_tax_id(tax_id):
            logger.info(f"Searching for insured by tax ID: {tax_id}")
            exact_match = self._find_by_tax_id(tax_id)
            if exact_match:
                logger.info(f"Found exact tax ID match: {exact_match.get('InsuredName')}")
                return exact_match
        
        # Step 2: Search by name variations
        logger.info(f"Searching for insured by name: {insured_name}")
        candidates = self._find_candidates_by_name(insured_name, search_criteria)
        
        if not candidates:
            logger.info("No candidates found")
            return None
        
        # Step 3: Score and rank candidates
        scored_candidates = []
        for candidate in candidates:
            score = self._calculate_match_score(search_criteria, candidate)
            scored_candidates.append((candidate, score))
        
        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Step 4: Return best match if score is high enough
        best_candidate, best_score = scored_candidates[0]
        
        # Log top matches for debugging
        logger.info(f"Top {min(3, len(scored_candidates))} matches:")
        for i, (candidate, score) in enumerate(scored_candidates[:3]):
            logger.info(f"  {i+1}. {candidate.get('InsuredName')} - Score: {score:.2f}")
        
        # Threshold for accepting a match
        if best_score >= 0.85:  # 85% confidence
            logger.info(f"Accepting match: {best_candidate.get('InsuredName')} (Score: {best_score:.2f})")
            return best_candidate
        elif best_score >= 0.70 and tax_id and self._tax_ids_match(tax_id, best_candidate.get('TaxID')):
            # Lower threshold if tax IDs match
            logger.info(f"Accepting match with tax ID confirmation: {best_candidate.get('InsuredName')} (Score: {best_score:.2f})")
            return best_candidate
        else:
            logger.info(f"Best match score {best_score:.2f} below threshold - creating new insured")
            return None
    
    def _find_by_tax_id(self, tax_id: str) -> Optional[Dict[str, Any]]:
        """Find insured by exact tax ID match"""
        normalized_tax_id = self._normalize_tax_id(tax_id)
        
        # Execute query to find by tax ID
        query = """
        SELECT InsuredGUID, InsuredName, TaxID, BusinessTypeID, 
               Address1, City, State, ZipCode, Active
        FROM Insureds 
        WHERE REPLACE(REPLACE(TaxID, '-', ''), ' ', '') = @TaxID
          AND Active = 1
        """
        
        try:
            result = self.insured_service.soap_client.execute_data_set(
                query, 
                {"TaxID": normalized_tax_id}
            )
            
            if result and 'Tables' in result:
                tables = result.get('Tables', {})
                if tables and len(tables) > 0:
                    rows = tables[0].get('Rows', [])
                    if rows and len(rows) > 0:
                        return rows[0]
        except Exception as e:
            logger.error(f"Error searching by tax ID: {str(e)}")
        
        return None
    
    def _find_candidates_by_name(self, name: str, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find potential candidates by name and location"""
        candidates = []
        
        # Generate name variations
        name_variations = self._generate_name_variations(name)
        
        # Search for each variation
        for variant in name_variations[:5]:  # Limit to top 5 variations
            try:
                # Use the SOAP client's find method
                results = self._search_insureds(
                    variant, 
                    search_criteria.get("city", ""),
                    search_criteria.get("state", ""),
                    search_criteria.get("zip_code", "")
                )
                
                # Add unique results to candidates
                for result in results:
                    if not any(c.get('InsuredGUID') == result.get('InsuredGUID') for c in candidates):
                        candidates.append(result)
                
            except Exception as e:
                logger.error(f"Error searching for name variant '{variant}': {str(e)}")
        
        return candidates
    
    def _search_insureds(self, name: str, city: str = "", state: str = "", zip_code: str = "") -> List[Dict[str, Any]]:
        """Search for insureds using SOAP service"""
        # This would use the actual SOAP search - for now, using a query
        query = """
        SELECT TOP 20 InsuredGUID, InsuredName, TaxID, BusinessTypeID,
               Address1, City, State, ZipCode, Active
        FROM Insureds
        WHERE Active = 1
          AND InsuredName LIKE @Name
        """
        
        params = {"Name": f"%{name}%"}
        
        # Add location filters if provided
        if state:
            query += " AND State = @State"
            params["State"] = state
        
        if city:
            query += " AND City LIKE @City"
            params["City"] = f"%{city}%"
            
        if zip_code:
            query += " AND ZipCode LIKE @Zip"
            params["Zip"] = f"{zip_code[:5]}%"
        
        query += " ORDER BY InsuredName"
        
        try:
            result = self.insured_service.soap_client.execute_data_set(query, params)
            
            if result and 'Tables' in result:
                tables = result.get('Tables', {})
                if tables and len(tables) > 0:
                    return tables[0].get('Rows', [])
        except Exception as e:
            logger.error(f"Error executing search query: {str(e)}")
        
        return []
    
    def _calculate_match_score(self, search_criteria: Dict[str, Any], candidate: Dict[str, Any]) -> float:
        """
        Calculate a match score between 0 and 1
        
        Scoring weights:
        - Name similarity: 40%
        - Tax ID match: 30%
        - Address match: 20%
        - State match: 10%
        """
        score = 0.0
        
        # Name similarity (40%)
        search_name = search_criteria.get("name", "")
        candidate_name = candidate.get("InsuredName", "")
        if search_name and candidate_name:
            name_score = self._calculate_name_similarity(search_name, candidate_name)
            score += name_score * 0.4
        
        # Tax ID match (30%)
        search_tax_id = search_criteria.get("tax_id")
        candidate_tax_id = candidate.get("TaxID")
        if search_tax_id and candidate_tax_id:
            if self._tax_ids_match(search_tax_id, candidate_tax_id):
                score += 0.3
            elif self._tax_ids_partial_match(search_tax_id, candidate_tax_id):
                score += 0.15  # Partial credit for partial match
        
        # Address match (20%)
        search_address = search_criteria.get("address", "")
        candidate_address = candidate.get("Address1", "")
        if search_address and candidate_address:
            address_score = self._calculate_address_similarity(search_address, candidate_address)
            score += address_score * 0.2
        
        # State match (10%)
        search_state = search_criteria.get("state", "")
        candidate_state = candidate.get("State", "")
        if search_state and candidate_state:
            if search_state.upper() == candidate_state.upper():
                score += 0.1
        
        return score
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two business names"""
        # Normalize both names
        norm1 = self._normalize_business_name(name1)
        norm2 = self._normalize_business_name(name2)
        
        # If normalized names are identical, perfect match
        if norm1 == norm2:
            return 1.0
        
        # Calculate base similarity
        base_similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Check if one name contains the other (subsidiary check)
        if norm1 in norm2 or norm2 in norm1:
            base_similarity = max(base_similarity, 0.85)
        
        # Check word overlap
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        if words1 and words2:
            overlap = len(words1.intersection(words2))
            total = len(words1.union(words2))
            word_similarity = overlap / total if total > 0 else 0
            base_similarity = max(base_similarity, word_similarity * 0.9)
        
        return base_similarity
    
    def _calculate_address_similarity(self, addr1: str, addr2: str) -> float:
        """Calculate similarity between two addresses"""
        # Normalize addresses
        norm1 = self._normalize_address(addr1)
        norm2 = self._normalize_address(addr2)
        
        # If normalized addresses are identical, perfect match
        if norm1 == norm2:
            return 1.0
        
        # Extract street numbers
        num1 = re.match(r'^(\d+)', norm1)
        num2 = re.match(r'^(\d+)', norm2)
        
        # If street numbers don't match, low similarity
        if num1 and num2 and num1.group(1) != num2.group(1):
            return 0.2
        
        # Calculate similarity
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def _normalize_business_name(self, name: str) -> str:
        """Normalize a business name for comparison"""
        if not name:
            return ""
        
        # Convert to uppercase
        normalized = name.upper()
        
        # Remove special characters except spaces and hyphens
        normalized = re.sub(r'[^\w\s-]', ' ', normalized)
        
        # Remove common suffixes
        for suffix in self.BUSINESS_SUFFIXES:
            # Add word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(suffix) + r'\b'
            normalized = re.sub(pattern, '', normalized)
        
        # Replace multiple spaces with single space
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove leading/trailing spaces
        normalized = normalized.strip()
        
        return normalized
    
    def _normalize_address(self, address: str) -> str:
        """Normalize an address for comparison"""
        if not address:
            return ""
        
        # Convert to uppercase
        normalized = address.upper()
        
        # Common address abbreviations
        replacements = {
            r'\bSTREET\b': 'ST',
            r'\bAVENUE\b': 'AVE',
            r'\bROAD\b': 'RD',
            r'\bDRIVE\b': 'DR',
            r'\bLANE\b': 'LN',
            r'\bBOULEVARD\b': 'BLVD',
            r'\bSUITE\b': 'STE',
            r'\bAPARTMENT\b': 'APT',
            r'\bNORTH\b': 'N',
            r'\bSOUTH\b': 'S',
            r'\bEAST\b': 'E',
            r'\bWEST\b': 'W'
        }
        
        for pattern, replacement in replacements.items():
            normalized = re.sub(pattern, replacement, normalized)
        
        # Remove special characters
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Replace multiple spaces with single space
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized.strip()
    
    def _normalize_tax_id(self, tax_id: str) -> str:
        """Normalize a tax ID for comparison"""
        if not tax_id:
            return ""
        
        # Remove all non-numeric characters
        return re.sub(r'[^\d]', '', tax_id)
    
    def _is_valid_tax_id(self, tax_id: str) -> bool:
        """Check if a tax ID appears valid"""
        normalized = self._normalize_tax_id(tax_id)
        
        # Check for valid length (9 for SSN/EIN)
        if len(normalized) == 9:
            return True
        
        # Could add more validation here
        return False
    
    def _tax_ids_match(self, tax_id1: str, tax_id2: str) -> bool:
        """Check if two tax IDs match"""
        if not tax_id1 or not tax_id2:
            return False
        
        return self._normalize_tax_id(tax_id1) == self._normalize_tax_id(tax_id2)
    
    def _tax_ids_partial_match(self, tax_id1: str, tax_id2: str) -> bool:
        """Check if tax IDs partially match (last 4 digits)"""
        if not tax_id1 or not tax_id2:
            return False
        
        norm1 = self._normalize_tax_id(tax_id1)
        norm2 = self._normalize_tax_id(tax_id2)
        
        # Check if last 4 digits match
        if len(norm1) >= 4 and len(norm2) >= 4:
            return norm1[-4:] == norm2[-4:]
        
        return False
    
    def _generate_name_variations(self, name: str) -> List[str]:
        """Generate variations of a business name for searching"""
        variations = [name]
        
        # Add normalized version
        normalized = self._normalize_business_name(name)
        if normalized != name:
            variations.append(normalized)
        
        # Add version without suffixes
        for suffix in self.BUSINESS_SUFFIXES:
            if suffix in name.upper():
                without_suffix = re.sub(r'\b' + re.escape(suffix) + r'\b', '', name, flags=re.IGNORECASE)
                without_suffix = re.sub(r'\s+', ' ', without_suffix).strip()
                if without_suffix and without_suffix not in variations:
                    variations.append(without_suffix)
        
        # Add common variations
        name_upper = name.upper()
        for original, replacements in self.NAME_VARIATIONS.items():
            if original in name_upper:
                for replacement in replacements:
                    variant = re.sub(r'\b' + re.escape(original) + r'\b', 
                                   replacement, name, flags=re.IGNORECASE)
                    if variant not in variations:
                        variations.append(variant)
        
        return variations