"""
IMS Lookup Service - Handles mappings between text identifiers and IMS GUIDs
"""
import os
import json
import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

class IMSLookupService:
    def __init__(self, ims_integration):
        """Initialize the lookup service with a reference to the IMS integration"""
        self.ims = ims_integration
        self.logger = self.ims.logger
        self.cache = {
            'insureds': {},
            'producers': {},
            'underwriters': {},
            'locations': {},
            'lines': {},
            'programs': {}
        }
        self.cache_file = f"ims_guid_cache_{self.ims.env}.json"
        self._load_cache()
        
    def _load_cache(self):
        """Load the GUID cache from file if it exists"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    loaded_cache = json.load(f)
                    # Update our cache with the loaded data
                    for category, items in loaded_cache.items():
                        if category in self.cache:
                            self.cache[category].update(items)
                self.logger.info(f"Loaded GUID cache from {self.cache_file}")
            except Exception as e:
                self.logger.error(f"Error loading GUID cache: {e}")
    
    def _save_cache(self):
        """Save the GUID cache to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            self.logger.info(f"Saved GUID cache to {self.cache_file}")
        except Exception as e:
            self.logger.error(f"Error saving GUID cache: {e}")
    
    def lookup_insured(self, insured_name):
        """Look up an insured GUID by name"""
        if insured_name in self.cache['insureds']:
            return self.cache['insureds'][insured_name]
        
        # TODO: Implement API call to search for insured by name
        # This would likely use the ContactFunctions.asmx service
        
        # For now, use a placeholder GUID
        guid = "00000000-0000-0000-0000-000000000000"
        
        # Cache the result
        self.cache['insureds'][insured_name] = guid
        self._save_cache()
        
        return guid
    
    def lookup_producer(self, producer_name):
        """Look up a producer GUID by name"""
        if producer_name in self.cache['producers']:
            return self.cache['producers'][producer_name]
        
        # TODO: Implement API call to search for producer by name
        # This would likely use the ContactFunctions.asmx service
        
        # For now, use a placeholder GUID
        guid = "00000000-0000-0000-0000-000000000000"
        
        # Cache the result
        self.cache['producers'][producer_name] = guid
        self._save_cache()
        
        return guid
    
    def lookup_underwriter(self, underwriter_name):
        """Look up an underwriter GUID by name"""
        if underwriter_name in self.cache['underwriters']:
            return self.cache['underwriters'][underwriter_name]
        
        # TODO: Implement API call to search for underwriter by name
        # This would likely use the ContactFunctions.asmx service
        
        # For now, use a placeholder GUID
        guid = "00000000-0000-0000-0000-000000000000"
        
        # Cache the result
        self.cache['underwriters'][underwriter_name] = guid
        self._save_cache()
        
        return guid
    
    def lookup_location(self, location_name, location_type='producer'):
        """Look up a location GUID by name and type"""
        key = f"{location_type}:{location_name}"
        if key in self.cache['locations']:
            return self.cache['locations'][key]
        
        # TODO: Implement API call to search for location by name and type
        # This would likely use the LocationFunctions.asmx service
        
        # For now, use a placeholder GUID
        guid = "00000000-0000-0000-0000-000000000000"
        
        # Cache the result
        self.cache['locations'][key] = guid
        self._save_cache()
        
        return guid
    
    def lookup_line(self, line_name):
        """Look up a line of business GUID by name"""
        if line_name in self.cache['lines']:
            return self.cache['lines'][line_name]
        
        # TODO: Implement API call to search for line by name
        # This would likely use a LineFunctions.asmx service or similar
        
        # For now, use a placeholder GUID
        guid = "00000000-0000-0000-0000-000000000000"
        
        # Cache the result
        self.cache['lines'][line_name] = guid
        self._save_cache()
        
        return guid
    
    def lookup_program(self, program_name):
        """Look up a program GUID by name"""
        if program_name in self.cache['programs']:
            return self.cache['programs'][program_name]
        
        # TODO: Implement API call to search for program by name
        # This would likely use a ProgramFunctions.asmx service or similar
        
        # For now, use a placeholder GUID
        guid = "00000000-0000-0000-0000-000000000000"
        
        # Cache the result
        self.cache['programs'][program_name] = guid
        self._save_cache()
        
        return guid
    
    def lookup_all_for_policy(self, policy_data):
        """
        Look up all needed GUIDs for a policy
        
        Returns a dictionary of GUIDs keyed by entity type
        """
        guids = {
            'insured': self.lookup_insured(policy_data['insured_name']),
            'producer': self.lookup_producer(policy_data['producer']),
            'underwriter': self.lookup_underwriter(policy_data['underwriter']),
            'line': self.lookup_line(policy_data['class_of_business']),
            'program': self.lookup_program(policy_data['program']),
            'producer_location': self.lookup_location(policy_data['producer'], 'producer'),
            'company_location': '00000000-0000-0000-0000-000000000000'  # Placeholder
        }
        
        return guids 