"""
Producer Matcher - Service for matching producers between source systems and IMS
"""
import os
import json
import logging
import csv
import re
from typing import Dict, Any, List, Optional, Tuple
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz


class ProducerMatcher:
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the producer matcher
        
        Args:
            config_path: Path to the configuration file (optional)
        """
        self.logger = self._setup_logger()
        self.mappings = {}
        self.ims_producers = {}
        self.match_threshold = 80  # Default threshold for fuzzy matching
        
        # Load configuration if provided
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
            
        # Load mappings if they exist
        self.mapping_file = "producer_mappings.json"
        self._load_mappings()
        
    def _setup_logger(self):
        """Set up logging for the producer matcher"""
        logger = logging.getLogger('producer_matcher')
        logger.setLevel(logging.INFO)
        
        # Create handlers if they don't exist
        if not logger.handlers:
            # Create handlers
            file_handler = logging.FileHandler('producer_matcher.log')
            console_handler = logging.StreamHandler()
            
            # Create formatters and add to handlers
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # Add handlers to the logger
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def _load_config(self, config_path: str):
        """Load configuration from a file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            # Set configuration values
            self.match_threshold = config.get('match_threshold', self.match_threshold)
            self.mapping_file = config.get('mapping_file', self.mapping_file)
            
            self.logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
    
    def _load_mappings(self):
        """Load producer mappings from a file if it exists"""
        if os.path.exists(self.mapping_file):
            try:
                with open(self.mapping_file, 'r') as f:
                    self.mappings = json.load(f)
                self.logger.info(f"Loaded {len(self.mappings)} producer mappings from {self.mapping_file}")
            except Exception as e:
                self.logger.error(f"Error loading producer mappings: {e}")
                self.mappings = {}
    
    def _save_mappings(self):
        """Save producer mappings to a file"""
        try:
            with open(self.mapping_file, 'w') as f:
                json.dump(self.mappings, f, indent=2)
            self.logger.info(f"Saved {len(self.mappings)} producer mappings to {self.mapping_file}")
        except Exception as e:
            self.logger.error(f"Error saving producer mappings: {e}")
    
    def load_ims_producers(self, producers: List[Dict[str, Any]]):
        """
        Load IMS producers
        
        Args:
            producers: List of IMS producers, each with at least 'guid' and 'name' keys
        """
        self.ims_producers = {producer['name'].lower(): producer for producer in producers}
        self.logger.info(f"Loaded {len(self.ims_producers)} IMS producers")
    
    def load_ims_producers_from_csv(self, csv_path: str):
        """
        Load IMS producers from a CSV file
        
        Args:
            csv_path: Path to the CSV file containing IMS producers
            
        The CSV file should have at least 'guid' and 'name' columns
        """
        producers = []
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    producers.append({
                        'guid': row.get('guid'),
                        'name': row.get('name')
                    })
            
            self.load_ims_producers(producers)
            self.logger.info(f"Loaded {len(producers)} IMS producers from {csv_path}")
        except Exception as e:
            self.logger.error(f"Error loading IMS producers from CSV: {e}")
    
    def add_mapping(self, source_producer: str, source_system: str, ims_producer_guid: str):
        """
        Add a mapping between a source producer and an IMS producer
        
        Args:
            source_producer: Name of the producer in the source system
            source_system: Name of the source system (e.g., 'tritan')
            ims_producer_guid: GUID of the producer in IMS
        """
        key = self._format_key(source_producer, source_system)
        self.mappings[key] = ims_producer_guid
        self._save_mappings()
        self.logger.info(f"Added mapping: {key} -> {ims_producer_guid}")
    
    def get_mapping(self, source_producer: str, source_system: str) -> Optional[str]:
        """
        Get the IMS producer GUID for a source producer
        
        Args:
            source_producer: Name of the producer in the source system
            source_system: Name of the source system (e.g., 'tritan')
            
        Returns:
            Optional[str]: GUID of the producer in IMS, or None if not found
        """
        key = self._format_key(source_producer, source_system)
        return self.mappings.get(key)
    
    def _format_key(self, producer_name: str, source_system: str) -> str:
        """Format a key for the mappings dictionary"""
        return f"{source_system}:{producer_name.lower()}"
    
    def _normalize_name(self, name: str) -> str:
        """Normalize a producer name for matching"""
        # Convert to lowercase
        name = name.lower()
        
        # Remove common words and punctuation
        name = re.sub(r'\s+(insurance|agency|brokerage|inc|llc|ltd|broker|brokers)\b', '', name)
        name = re.sub(r'[^\w\s]', '', name)
        
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def find_ims_producer(self, source_producer: str, source_system: str) -> Tuple[Optional[str], float]:
        """
        Find the best matching IMS producer for a source producer
        
        Args:
            source_producer: Name of the producer in the source system
            source_system: Name of the source system (e.g., 'tritan')
            
        Returns:
            Tuple[Optional[str], float]: GUID of the best matching producer in IMS and the match score,
                                          or (None, 0.0) if no match found
        """
        # Check for an existing mapping
        existing_guid = self.get_mapping(source_producer, source_system)
        if existing_guid:
            return existing_guid, 100.0
        
        # Normalize the source producer name
        normalized_source = self._normalize_name(source_producer)
        
        # Find the best match
        best_match = None
        best_score = 0.0
        
        for ims_name, ims_producer in self.ims_producers.items():
            normalized_ims = self._normalize_name(ims_name)
            
            # Calculate similarity score
            score = fuzz.ratio(normalized_source, normalized_ims)
            
            if score > best_score:
                best_score = score
                best_match = ims_producer
        
        # Return the match if it's above the threshold
        if best_match and best_score >= self.match_threshold:
            return best_match['guid'], best_score
        
        return None, 0.0
    
    def interactive_match(self, source_producer: str, source_system: str) -> Optional[str]:
        """
        Interactively match a source producer to an IMS producer
        
        Args:
            source_producer: Name of the producer in the source system
            source_system: Name of the source system (e.g., 'tritan')
            
        Returns:
            Optional[str]: GUID of the matched producer in IMS, or None if not matched
        """
        # Check for an existing mapping
        existing_guid = self.get_mapping(source_producer, source_system)
        if existing_guid:
            return existing_guid
        
        # Find potential matches
        normalized_source = self._normalize_name(source_producer)
        matches = []
        
        for ims_name, ims_producer in self.ims_producers.items():
            normalized_ims = self._normalize_name(ims_name)
            score = fuzz.ratio(normalized_source, normalized_ims)
            
            if score >= self.match_threshold:
                matches.append((ims_producer, score))
        
        # Sort matches by score
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Display matches for selection
        print(f"\nMatching producer: {source_producer} ({source_system})")
        
        if not matches:
            print("No matches found")
            return None
        
        print("Potential matches:")
        for i, (match, score) in enumerate(matches[:10], 1):
            print(f"{i}. {match['name']} (Score: {score:.1f})")
        
        print("0. None of the above")
        
        # Get user selection
        try:
            selection = int(input("Select a match (0-10): "))
            
            if selection > 0 and selection <= len(matches[:10]):
                selected_match = matches[selection - 1][0]
                
                # Add mapping
                self.add_mapping(source_producer, source_system, selected_match['guid'])
                
                return selected_match['guid']
            
        except (ValueError, IndexError):
            pass
        
        return None
    
    def batch_match_producers(self, source_producers: List[Dict[str, str]], source_system: str,
                            interactive: bool = False) -> Dict[str, str]:
        """
        Match a batch of source producers to IMS producers
        
        Args:
            source_producers: List of source producers, each with at least a 'name' key
            source_system: Name of the source system (e.g., 'tritan')
            interactive: Whether to prompt for user input on uncertain matches
            
        Returns:
            Dict[str, str]: Dictionary mapping source producer names to IMS producer GUIDs
        """
        results = {}
        
        for producer in source_producers:
            source_name = producer['name']
            
            if interactive:
                # Interactive matching
                guid = self.interactive_match(source_name, source_system)
            else:
                # Automatic matching
                guid, score = self.find_ims_producer(source_name, source_system)
                
                if guid:
                    # Add to mappings if it's a good match
                    if score >= 90:
                        self.add_mapping(source_name, source_system, guid)
                    
                    self.logger.info(f"Matched {source_name} to {guid} with score {score:.1f}")
            
            if guid:
                results[source_name] = guid
        
        return results


# Example usage
if __name__ == "__main__":
    # Create a producer matcher
    matcher = ProducerMatcher()
    
    # Load sample IMS producers
    ims_producers = [
        {"guid": "00000000-0000-0000-0000-000000000001", "name": "ABC Insurance Agency"},
        {"guid": "00000000-0000-0000-0000-000000000002", "name": "XYZ Brokers Inc."},
        {"guid": "00000000-0000-0000-0000-000000000003", "name": "John Smith Insurance"}
    ]
    matcher.load_ims_producers(ims_producers)
    
    # Sample source producers
    source_producers = [
        {"name": "ABC Insurance"},
        {"name": "XYZ Insurance Brokers"},
        {"name": "Smith, John - Insurance Agency"}
    ]
    
    # Match producers
    matches = matcher.batch_match_producers(source_producers, "tritan", interactive=True)
    
    # Print results
    print("\nMatching Results:")
    for source_name, ims_guid in matches.items():
        ims_name = next((p["name"] for p in ims_producers if p["guid"] == ims_guid), "Unknown")
        print(f"{source_name} -> {ims_name} ({ims_guid})") 