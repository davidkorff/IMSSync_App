"""
Polling Service
Coordinates database polling from various sources and feeds into the standard pipeline
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from ..sources.triton.pull_adapter import TritonPullAdapter
from ..core.transaction_processor import processor

logger = logging.getLogger(__name__)


class PollingService:
    """
    Service that polls external data sources and feeds transactions into the pipeline
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        self.adapters = {}
        
        # Initialize adapters based on config
        if config.get('triton', {}).get('enabled'):
            triton_config = config['triton']
            self.adapters['triton'] = TritonPullAdapter(triton_config['database'])
    
    async def start(self):
        """Start the polling service"""
        if self.running:
            logger.warning("Polling service is already running")
            return
        
        self.running = True
        logger.info("Starting polling service")
        
        # Start polling tasks for each enabled source
        tasks = []
        
        if 'triton' in self.adapters:
            triton_interval = self.config['triton'].get('polling_interval', 300)  # 5 minutes default
            tasks.append(self._poll_source('triton', triton_interval))
        
        if tasks:
            await asyncio.gather(*tasks)
        else:
            logger.warning("No polling sources configured")
    
    async def stop(self):
        """Stop the polling service"""
        self.running = False
        logger.info("Stopping polling service")
        
        # Disconnect adapters
        for adapter in self.adapters.values():
            if hasattr(adapter, 'disconnect'):
                await adapter.disconnect()
    
    async def _poll_source(self, source_name: str, interval: int):
        """Poll a specific source at regular intervals"""
        logger.info(f"Starting {source_name} polling (interval: {interval}s)")
        
        adapter = self.adapters[source_name]
        
        while self.running:
            try:
                await self._poll_once(source_name, adapter)
                
                # Wait for next polling interval
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                logger.info(f"Polling cancelled for {source_name}")
                break
            except Exception as e:
                logger.error(f"Error polling {source_name}: {e}")
                # Wait before retrying on error
                await asyncio.sleep(min(interval, 60))
    
    async def _poll_once(self, source_name: str, adapter):
        """Perform one polling cycle for a source"""
        try:
            logger.debug(f"Polling {source_name} for new transactions")
            
            # Get pending transactions
            transactions = await adapter.get_pending_transactions(limit=10)
            
            if not transactions:
                logger.debug(f"No pending transactions from {source_name}")
                return
            
            logger.info(f"Found {len(transactions)} pending transactions from {source_name}")
            
            # Process each transaction
            for transaction in transactions:
                try:
                    result = await processor.process_transaction(transaction, "ims")
                    
                    if result['status'] == 'completed':
                        logger.info(
                            f"Successfully processed {transaction.source_transaction_id} "
                            f"from {source_name}"
                        )
                    else:
                        logger.error(
                            f"Failed to process {transaction.source_transaction_id} "
                            f"from {source_name}: {result['message']}"
                        )
                        
                except Exception as e:
                    logger.error(
                        f"Exception processing transaction {transaction.source_transaction_id} "
                        f"from {source_name}: {e}"
                    )
            
        except Exception as e:
            logger.error(f"Error in polling cycle for {source_name}: {e}")
            raise
    
    async def poll_now(self, source_name: str = None) -> Dict[str, Any]:
        """
        Trigger immediate polling for testing/manual execution
        
        Args:
            source_name: Specific source to poll, or None for all sources
            
        Returns:
            Results of polling operation
        """
        results = {}
        
        sources_to_poll = [source_name] if source_name else list(self.adapters.keys())
        
        for source in sources_to_poll:
            if source not in self.adapters:
                results[source] = {"error": f"Unknown source: {source}"}
                continue
            
            try:
                adapter = self.adapters[source]
                transactions = await adapter.get_pending_transactions(limit=10)
                
                results[source] = {
                    "transactions_found": len(transactions),
                    "processed": 0,
                    "failed": 0,
                    "errors": []
                }
                
                # Process transactions
                for transaction in transactions:
                    try:
                        result = await processor.process_transaction(transaction, "ims")
                        
                        if result['status'] == 'completed':
                            results[source]["processed"] += 1
                        else:
                            results[source]["failed"] += 1
                            results[source]["errors"].append({
                                "transaction_id": transaction.source_transaction_id,
                                "error": result['message']
                            })
                            
                    except Exception as e:
                        results[source]["failed"] += 1
                        results[source]["errors"].append({
                            "transaction_id": transaction.source_transaction_id,
                            "error": str(e)
                        })
                
            except Exception as e:
                results[source] = {"error": str(e)}
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of polling service"""
        return {
            "running": self.running,
            "sources_configured": list(self.adapters.keys()),
            "config": self.config
        }


# Global polling service instance
polling_service = None


def get_polling_service(config: Dict[str, Any] = None) -> PollingService:
    """Get or create the global polling service instance"""
    global polling_service
    
    if polling_service is None and config is not None:
        polling_service = PollingService(config)
    
    return polling_service