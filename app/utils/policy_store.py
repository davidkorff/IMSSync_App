import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

logger = logging.getLogger(__name__)

class PolicyStore:
    """Simple file-based storage for policy mappings"""
    
    def __init__(self, storage_path: str = "data/policies.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """Load data from file"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading policy data: {e}")
                return {}
        return {}
    
    def _save_data(self):
        """Save data to file"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self._data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving policy data: {e}")
    
    def store_policy(self, policy_number: str, policy_guid: UUID, 
                    transaction_id: str, additional_data: Dict[str, Any] = None):
        """Store policy mapping"""
        self._data[policy_number] = {
            "policy_guid": str(policy_guid),
            "transaction_id": transaction_id,
            "created_at": datetime.now().isoformat(),
            "additional_data": additional_data or {}
        }
        self._save_data()
        logger.info(f"Stored policy mapping: {policy_number} -> {policy_guid}")
    
    def get_policy_guid(self, policy_number: str) -> Optional[UUID]:
        """Get policy GUID by policy number"""
        if policy_number in self._data:
            return UUID(self._data[policy_number]["policy_guid"])
        return None
    
    def get_policy_info(self, policy_number: str) -> Optional[Dict[str, Any]]:
        """Get full policy information"""
        return self._data.get(policy_number)

# Global instance
policy_store = PolicyStore()