"""
IMS Producer Service

This service handles all producer-related operations in IMS including:
- Finding producers
- Managing producer contacts
- Managing producer locations
- Producer clearance operations
"""

import logging
from typing import Dict, Any, Optional, List

from app.services.ims.base_service import BaseIMSService

logger = logging.getLogger(__name__)


class IMSProducerService(BaseIMSService):
    """Service for managing producers in IMS"""
    
    def search_producer(self, search_string: str, start_with: bool = False) -> List[Dict[str, Any]]:
        """
        Search for producers by name or other criteria
        
        Args:
            search_string: The search string
            start_with: Whether to search from beginning of name only
            
        Returns:
            List of producer location dictionaries
        """
        self._log_operation("search_producer", {"search_string": search_string})
        
        body_content = f"""
        <ProducerSearch xmlns="http://tempuri.org/IMSWebServices/ProducerFunctions">
            <searchString>{search_string}</searchString>
            <startWith>{"true" if start_with else "false"}</startWith>
        </ProducerSearch>
        """
        
        try:
            response = self.soap_client._make_soap_request(
                self.soap_client.producer_functions_url,
                "http://tempuri.org/IMSWebServices/ProducerFunctions/ProducerSearch",
                body_content
            )
            
            if response and 'soap:Body' in response:
                search_response = response['soap:Body'].get('ProducerSearchResponse', {})
                search_result = search_response.get('ProducerSearchResult', {})
                
                if search_result:
                    producer_locations = search_result.get('ProducerLocation', [])
                    
                    # Convert to list if single item
                    if not isinstance(producer_locations, list):
                        producer_locations = [producer_locations]
                    
                    logger.info(f"Found {len(producer_locations)} producer locations")
                    return producer_locations
            
            return []
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "search_producer")
                # Retry once
                return self.search_producer(search_string, start_with)
            raise
    
    def get_producer_by_name(self, producer_name: str) -> Optional[str]:
        """
        Get producer location GUID by name with fuzzy matching
        
        Args:
            producer_name: The producer's name
            
        Returns:
            Producer location GUID if found, None otherwise
        """
        if not producer_name:
            return None
        
        logger.info(f"Searching for producer: {producer_name}")
        
        # Try multiple search strategies
        search_strategies = [
            producer_name,  # Exact name
            producer_name.split()[0] if ' ' in producer_name else producer_name,  # First word
            producer_name.replace(" Agency", "").replace(" Insurance", ""),  # Remove common suffixes
        ]
        
        all_results = []
        for search_term in search_strategies:
            results = self.search_producer(search_term, start_with=False)
            all_results.extend(results)
        
        # Remove duplicates
        unique_results = []
        seen_guids = set()
        for result in all_results:
            guid = result.get('ProducerLocationGuid')
            if guid and guid not in seen_guids:
                seen_guids.add(guid)
                unique_results.append(result)
        
        # Score results
        scored_results = []
        for location in unique_results:
            score = self._calculate_producer_match_score(producer_name, location)
            scored_results.append((location, score))
        
        # Sort by score
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        if scored_results:
            best_match, best_score = scored_results[0]
            
            # Log top matches
            logger.info(f"Top producer matches for '{producer_name}':")
            for i, (loc, score) in enumerate(scored_results[:3]):
                logger.info(f"  {i+1}. {loc.get('ProducerName')} - Score: {score:.2f}")
            
            # Accept match if score is high enough
            if best_score >= 0.8:
                logger.info(f"Accepting producer match: {best_match.get('ProducerName')}")
                return best_match.get('ProducerLocationGuid')
            elif best_score >= 0.6:
                logger.warning(f"Partial match for producer '{producer_name}': {best_match.get('ProducerName')} (score: {best_score:.2f})")
                return best_match.get('ProducerLocationGuid')
        
        logger.warning(f"No suitable producer found for: {producer_name}")
        return None
    
    def _calculate_producer_match_score(self, search_name: str, producer: Dict[str, Any]) -> float:
        """Calculate match score for a producer"""
        producer_name = producer.get('ProducerName', '')
        
        if not producer_name:
            return 0.0
        
        # Normalize names
        search_norm = search_name.upper().strip()
        producer_norm = producer_name.upper().strip()
        
        # Exact match
        if search_norm == producer_norm:
            return 1.0
        
        # One contains the other
        if search_norm in producer_norm or producer_norm in search_norm:
            return 0.9
        
        # Calculate word overlap
        search_words = set(search_norm.split())
        producer_words = set(producer_norm.split())
        
        if search_words and producer_words:
            overlap = len(search_words.intersection(producer_words))
            total = len(search_words.union(producer_words))
            word_score = overlap / total if total > 0 else 0
            
            # Boost score if key words match
            key_words = search_words.intersection(producer_words)
            if key_words and len(key_words) >= len(search_words) * 0.5:
                word_score = min(word_score * 1.5, 0.95)
            
            return word_score
        
        # Use string similarity as fallback
        from difflib import SequenceMatcher
        return SequenceMatcher(None, search_norm, producer_norm).ratio() * 0.8
    
    def get_producer_info(self, producer_guid: str) -> Dict[str, Any]:
        """
        Get detailed information about a producer
        
        Args:
            producer_guid: The producer's GUID
            
        Returns:
            Dictionary containing producer information
        """
        self._log_operation("get_producer_info", {"producer_guid": producer_guid})
        
        body_content = f"""
        <GetProducerInfo xmlns="http://tempuri.org/IMSWebServices/ProducerFunctions">
            <producerGuid>{producer_guid}</producerGuid>
        </GetProducerInfo>
        """
        
        try:
            response = self.soap_client._make_soap_request(
                self.soap_client.producer_functions_url,
                "http://tempuri.org/IMSWebServices/ProducerFunctions/GetProducerInfo",
                body_content
            )
            
            if response and 'soap:Body' in response:
                info_response = response['soap:Body'].get('GetProducerInfoResponse', {})
                producer_info = info_response.get('GetProducerInfoResult', {})
                
                if producer_info:
                    logger.info(f"Retrieved info for producer {producer_guid}")
                    return producer_info
            
            return {}
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "get_producer_info")
                # Retry once
                return self.get_producer_info(producer_guid)
            raise
    
    def get_producer_contact_info(self, contact_guid: str) -> Dict[str, Any]:
        """
        Get information about a specific producer contact
        
        Args:
            contact_guid: The contact's GUID
            
        Returns:
            Dictionary containing contact information
        """
        self._log_operation("get_producer_contact_info", {"contact_guid": contact_guid})
        
        body_content = f"""
        <GetProducerContactInfo xmlns="http://tempuri.org/IMSWebServices/ProducerFunctions">
            <contactGuid>{contact_guid}</contactGuid>
        </GetProducerContactInfo>
        """
        
        try:
            response = self.soap_client._make_soap_request(
                self.soap_client.producer_functions_url,
                "http://tempuri.org/IMSWebServices/ProducerFunctions/GetProducerContactInfo",
                body_content
            )
            
            if response and 'soap:Body' in response:
                contact_response = response['soap:Body'].get('GetProducerContactInfoResponse', {})
                contact_info = contact_response.get('GetProducerContactInfoResult', {})
                
                if contact_info:
                    logger.info(f"Retrieved info for producer contact {contact_guid}")
                    return contact_info
            
            return {}
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "get_producer_contact_info")
                # Retry once
                return self.get_producer_contact_info(contact_guid)
            raise
    
    def get_default_producer_guid(self, source: Optional[str] = None) -> str:
        """
        Get the default producer GUID for a source system
        
        Args:
            source: The source system name (e.g., 'triton', 'xuber')
            
        Returns:
            The default producer GUID
        """
        default_guid = "00000000-0000-0000-0000-000000000000"
        
        if source:
            source_config = self._get_source_config(source)
            producer_guid = source_config.get("default_producer_guid", default_guid)
            
            logger.info(f"Using producer GUID for source {source}: {producer_guid}")
            return producer_guid
        
        return default_guid
    
    def add_producer_contact(self, producer_location_guid: str, 
                           contact_data: Dict[str, Any]) -> str:
        """
        Add a contact to a producer location
        
        Args:
            producer_location_guid: The producer location's GUID
            contact_data: Dictionary containing contact information
            
        Returns:
            The new contact GUID
        """
        self._log_operation("add_producer_contact", {
            "producer_location_guid": producer_location_guid,
            "contact_name": f"{contact_data.get('first_name')} {contact_data.get('last_name')}"
        })
        
        body_content = f"""
        <AddProducerContact xmlns="http://tempuri.org/IMSWebServices/ProducerFunctions">
            <producerLocationGuid>{producer_location_guid}</producerLocationGuid>
            <contact>
                <FirstName>{contact_data.get('first_name', '')}</FirstName>
                <LastName>{contact_data.get('last_name', '')}</LastName>
                <Email>{contact_data.get('email', '')}</Email>
                <Phone>{contact_data.get('phone', '')}</Phone>
                <Title>{contact_data.get('title', '')}</Title>
                <IsPrimary>{contact_data.get('is_primary', True)}</IsPrimary>
            </contact>
        </AddProducerContact>
        """
        
        try:
            response = self.soap_client._make_soap_request(
                self.soap_client.producer_functions_url,
                "http://tempuri.org/IMSWebServices/ProducerFunctions/AddProducerContact",
                body_content
            )
            
            if response and 'soap:Body' in response:
                add_response = response['soap:Body'].get('AddProducerContactResponse', {})
                contact_guid = add_response.get('AddProducerContactResult')
                
                if contact_guid:
                    logger.info(f"Added producer contact: {contact_guid}")
                    return contact_guid
            
            raise ValueError("Failed to add producer contact: No GUID returned")
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "add_producer_contact")
                # Retry once
                return self.add_producer_contact(producer_location_guid, contact_data)
            raise
    
    def get_producer_underwriter(self, producer_location_guid: str) -> Optional[str]:
        """
        Get the underwriter assigned to a producer location
        
        Args:
            producer_location_guid: The producer location's GUID
            
        Returns:
            The underwriter GUID if found, None otherwise
        """
        self._log_operation("get_producer_underwriter", {
            "producer_location_guid": producer_location_guid
        })
        
        body_content = f"""
        <GetProducerUnderwriter xmlns="http://tempuri.org/IMSWebServices/ProducerFunctions">
            <producerLocationGuid>{producer_location_guid}</producerLocationGuid>
        </GetProducerUnderwriter>
        """
        
        try:
            response = self.soap_client._make_soap_request(
                self.soap_client.producer_functions_url,
                "http://tempuri.org/IMSWebServices/ProducerFunctions/GetProducerUnderwriter",
                body_content
            )
            
            if response and 'soap:Body' in response:
                uw_response = response['soap:Body'].get('GetProducerUnderwriterResponse', {})
                underwriter_guid = uw_response.get('GetProducerUnderwriterResult')
                
                if underwriter_guid and underwriter_guid != "00000000-0000-0000-0000-000000000000":
                    logger.info(f"Found underwriter {underwriter_guid} for producer {producer_location_guid}")
                    return underwriter_guid
            
            logger.info(f"No underwriter found for producer {producer_location_guid}")
            return None
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "get_producer_underwriter")
                # Retry once
                return self.get_producer_underwriter(producer_location_guid)
            raise
    
    def find_underwriter_by_name(self, underwriter_name: str) -> Optional[str]:
        """
        Find underwriter GUID by name
        
        Args:
            underwriter_name: The underwriter's name
            
        Returns:
            Underwriter GUID if found, None otherwise
        """
        if not underwriter_name:
            return None
        
        self._log_operation("find_underwriter_by_name", {"name": underwriter_name})
        
        # Query to find underwriter
        query = """
        SELECT TOP 10 UserGUID, FirstName, LastName, Email, Active
        FROM Users
        WHERE Active = 1
          AND IsUnderwriter = 1
          AND (FirstName + ' ' + LastName LIKE @Name
               OR LastName LIKE @Name
               OR Email LIKE @Email)
        ORDER BY LastName, FirstName
        """
        
        params = {
            "Name": f"%{underwriter_name}%",
            "Email": f"%{underwriter_name}%"
        }
        
        try:
            result = self.soap_client.execute_data_set(query, params)
            
            if result and 'Tables' in result:
                tables = result.get('Tables', {})
                if tables and len(tables) > 0:
                    rows = tables[0].get('Rows', [])
                    
                    # Score results
                    scored_results = []
                    for row in rows:
                        full_name = f"{row.get('FirstName', '')} {row.get('LastName', '')}".strip()
                        score = self._calculate_name_match_score(underwriter_name, full_name)
                        scored_results.append((row, score))
                    
                    # Sort by score
                    scored_results.sort(key=lambda x: x[1], reverse=True)
                    
                    if scored_results:
                        best_match, best_score = scored_results[0]
                        
                        if best_score >= 0.7:
                            underwriter_guid = best_match.get('UserGUID')
                            full_name = f"{best_match.get('FirstName', '')} {best_match.get('LastName', '')}".strip()
                            logger.info(f"Found underwriter: {full_name} ({underwriter_guid})")
                            return underwriter_guid
            
            logger.warning(f"No underwriter found for: {underwriter_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding underwriter: {str(e)}")
            return None
    
    def _calculate_name_match_score(self, search_name: str, actual_name: str) -> float:
        """Calculate match score between two names"""
        if not search_name or not actual_name:
            return 0.0
        
        # Normalize
        search_norm = search_name.upper().strip()
        actual_norm = actual_name.upper().strip()
        
        # Exact match
        if search_norm == actual_norm:
            return 1.0
        
        # Last name only match
        search_parts = search_norm.split()
        actual_parts = actual_norm.split()
        
        if search_parts and actual_parts:
            # Check if last names match
            if search_parts[-1] == actual_parts[-1]:
                return 0.85
            
            # Check if any part matches
            for s_part in search_parts:
                if s_part in actual_parts:
                    return 0.7
        
        # Use string similarity
        from difflib import SequenceMatcher
        return SequenceMatcher(None, search_norm, actual_norm).ratio() * 0.6