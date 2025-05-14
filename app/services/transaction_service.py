import logging
import uuid
import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
import xml.etree.ElementTree as ET
from lxml import etree
import xmltodict

from app.models.transaction_models import (
    Transaction, TransactionStatus, TransactionResponse, 
    IMSProcessingStatus, TransactionSearchParams, TransactionType
)
from app.services.ims_workflow_service import IMSWorkflowService
from app.core.config import settings

logger = logging.getLogger(__name__)

class TransactionService:
    def __init__(self, environment=None):
        self.environment = environment or settings.DEFAULT_ENVIRONMENT
        
        # Initialize the IMS workflow service
        self.ims_workflow_service = IMSWorkflowService(self.environment)
        
        # Initialize the database connection
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "transactions.db")
        self._init_db()
        
        # Cache for in-memory transactions
        self.transactions: Dict[str, Transaction] = {}
        
    def _init_db(self):
        """Initialize the SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    external_id TEXT,
                    type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    raw_data TEXT NOT NULL,
                    processed_data TEXT,
                    received_at TEXT NOT NULL,
                    processed_at TEXT,
                    error_message TEXT,
                    ims_status TEXT,
                    ims_data TEXT
                )
            """)
            
            # Create transaction_logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transaction_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    message TEXT NOT NULL,
                    FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id)
                )
            """)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def create_transaction(self, transaction_type: str, source: str, data: Union[Dict[str, Any], str], 
                          external_id: Optional[str] = None) -> Transaction:
        """
        Create a new transaction from incoming data
        """
        transaction_id = str(uuid.uuid4())
        
        transaction = Transaction(
            transaction_id=transaction_id,
            external_id=external_id,
            type=transaction_type,
            source=source,
            status=TransactionStatus.RECEIVED,
            raw_data=data
        )
        
        # Store transaction in memory
        self.transactions[transaction_id] = transaction
        
        # Store transaction in database
        self._save_transaction(transaction)
        
        logger.info(f"Created new transaction: {transaction_id} from source: {source}")
        
        # Log data format and size
        if isinstance(data, dict):
            logger.info(f"Transaction {transaction_id} data is a dictionary with {len(data)} keys")
        elif isinstance(data, str):
            logger.info(f"Transaction {transaction_id} data is a string of length {len(data)}")
        else:
            logger.info(f"Transaction {transaction_id} data is of type {type(data)}")
        
        return transaction
    
    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """
        Retrieve a transaction by ID
        """
        # Check in-memory cache first
        if transaction_id in self.transactions:
            return self.transactions[transaction_id]
        
        # If not in memory, try to load from database
        return self._load_transaction(transaction_id)
    
    def update_transaction_status(self, transaction_id: str, status: TransactionStatus, 
                                 error_message: Optional[str] = None) -> Optional[Transaction]:
        """
        Update the status of a transaction
        """
        transaction = self.get_transaction(transaction_id)
        if not transaction:
            logger.error(f"Transaction not found: {transaction_id}")
            return None
            
        transaction.update_status(status, error_message)
            
        # Update transaction in database
        self._save_transaction(transaction)
        
        logger.info(f"Updated transaction {transaction_id} status to {status}")
        return transaction
    
    def process_transaction(self, transaction_id: str) -> TransactionResponse:
        """
        Process a transaction by ID
        """
        transaction = self.get_transaction(transaction_id)
        if not transaction:
            logger.error(f"Transaction not found: {transaction_id}")
            return TransactionResponse(
                transaction_id=transaction_id,
                status=TransactionStatus.FAILED,
                message=f"Transaction not found: {transaction_id}"
            )
        
        try:
            # Update status to processing
            self.update_transaction_status(transaction_id, TransactionStatus.PROCESSING)
            
            # Parse the incoming data
            processed_data = self._parse_data(transaction.raw_data)
            transaction.parsed_data = processed_data
            
            # Process the transaction with IMS workflow
            logger.info(f"Starting IMS workflow for transaction {transaction_id}")
            transaction = self.ims_workflow_service.process_transaction(transaction)
            
            # Save the transaction with updated status
            self._save_transaction(transaction)
            
            # Prepare response message
            if transaction.status == TransactionStatus.COMPLETED:
                message = f"Transaction processed successfully: {transaction.ims_processing.policy.policy_number if transaction.ims_processing.policy else 'No policy created'}"
            else:
                message = f"Transaction processing failed: {transaction.error_message or 'Unknown error'}"
            
            return TransactionResponse(
                transaction_id=transaction_id,
                status=transaction.status,
                ims_status=transaction.ims_processing.status,
                message=message
            )
            
        except Exception as e:
            import traceback
            logger.error(f"Error processing transaction {transaction_id}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            self.update_transaction_status(transaction_id, TransactionStatus.FAILED, str(e))
            
            return TransactionResponse(
                transaction_id=transaction_id,
                status=TransactionStatus.FAILED,
                ims_status=IMSProcessingStatus.ERROR if transaction.ims_processing else None,
                message=f"Error processing transaction: {str(e)}"
            )
    
    def _parse_data(self, data: Union[Dict[str, Any], str]) -> Dict[str, Any]:
        """
        Parse the raw transaction data, handling both JSON and XML
        """
        if isinstance(data, dict):
            # Already parsed JSON
            logger.info(f"Data is already a parsed dictionary, no parsing needed")
            return data
            
        if isinstance(data, str):
            # Check if it's XML
            if data.strip().startswith('<'):
                try:
                    # Try to parse as XML
                    logger.info(f"Parsing data as XML, first 100 chars: {data[:100]}...")
                    result = xmltodict.parse(data)
                    logger.info(f"Successfully parsed XML into dictionary with {len(result)} root elements")
                    return result
                except Exception as e:
                    logger.error(f"Error parsing XML: {str(e)}")
                    logger.error(f"First 200 chars of problematic XML: {data[:200]}")
                    raise ValueError(f"Invalid XML data: {str(e)}")
            else:
                # Try to parse as JSON
                try:
                    logger.info(f"Parsing data as JSON, first 100 chars: {data[:100]}...")
                    result = json.loads(data)
                    logger.info(f"Successfully parsed JSON into dictionary with {len(result) if isinstance(result, dict) else 'non-dict type'} elements")
                    return result
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON: {str(e)}")
                    logger.error(f"First 200 chars of problematic JSON: {data[:200]}")
                    raise ValueError(f"Invalid JSON data: {str(e)}")
        
        logger.error(f"Unsupported data format: {type(data)}")
        raise ValueError(f"Unsupported data format: {type(data)}")
    
    def search_transactions(self, params: TransactionSearchParams) -> List[Transaction]:
        """
        Search for transactions based on parameters
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT transaction_id FROM transactions WHERE 1=1"
            query_params = []
            
            if params.source:
                query += " AND source = ?"
                query_params.append(params.source)
                
            if params.status:
                query += " AND status = ?"
                query_params.append(params.status.value)
                
            if params.external_id:
                query += " AND external_id = ?"
                query_params.append(params.external_id)
                
            if params.start_date:
                query += " AND received_at >= ?"
                query_params.append(params.start_date.isoformat())
                
            if params.end_date:
                query += " AND received_at <= ?"
                query_params.append(params.end_date.isoformat())
            
            query += " ORDER BY received_at DESC LIMIT ? OFFSET ?"
            query_params.extend([params.limit, params.offset])
            
            cursor.execute(query, query_params)
            transaction_ids = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            # Load transactions
            return [self.get_transaction(transaction_id) for transaction_id in transaction_ids if transaction_id]
            
        except Exception as e:
            logger.error(f"Error searching transactions: {str(e)}")
            return []
            
    def _save_transaction(self, transaction: Transaction) -> None:
        """
        Save a transaction to the database
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if transaction already exists
            cursor.execute("SELECT 1 FROM transactions WHERE transaction_id = ?", (transaction.transaction_id,))
            exists = cursor.fetchone() is not None
            
            # Serialize IMS processing data
            ims_data = None
            if transaction.ims_processing:
                ims_data = json.dumps(transaction.ims_processing.dict(), default=str)
            
            # Serialize processed data
            processed_data = None
            if transaction.processed_data:
                processed_data = json.dumps(transaction.processed_data, default=str)
                
            if exists:
                # Update existing transaction
                cursor.execute("""
                    UPDATE transactions 
                    SET status = ?, processed_data = ?, processed_at = ?, error_message = ?, 
                        ims_status = ?, ims_data = ?
                    WHERE transaction_id = ?
                """, (
                    transaction.status.value,
                    processed_data,
                    transaction.processed_at.isoformat() if transaction.processed_at else None,
                    transaction.error_message,
                    transaction.ims_processing.status.value if transaction.ims_processing else None,
                    ims_data,
                    transaction.transaction_id
                ))
            else:
                # Insert new transaction
                cursor.execute("""
                    INSERT INTO transactions (
                        transaction_id, external_id, type, source, status, raw_data,
                        processed_data, received_at, processed_at, error_message,
                        ims_status, ims_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction.transaction_id,
                    transaction.external_id,
                    transaction.type.value,
                    transaction.source,
                    transaction.status.value,
                    json.dumps(transaction.raw_data, default=str) if isinstance(transaction.raw_data, dict) else transaction.raw_data,
                    processed_data,
                    transaction.received_at.isoformat(),
                    transaction.processed_at.isoformat() if transaction.processed_at else None,
                    transaction.error_message,
                    transaction.ims_processing.status.value if transaction.ims_processing else None,
                    ims_data
                ))
            
            # Save transaction logs if there are any
            if transaction.ims_processing and transaction.ims_processing.processing_logs:
                for log_message in transaction.ims_processing.processing_logs:
                    cursor.execute("""
                        INSERT INTO transaction_logs (transaction_id, timestamp, message)
                        VALUES (?, ?, ?)
                    """, (
                        transaction.transaction_id,
                        datetime.now().isoformat(),
                        log_message
                    ))
                    
                # Clear logs after saving
                transaction.ims_processing.processing_logs = []
                
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving transaction: {str(e)}")
            raise
            
    def _load_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """
        Load a transaction from the database
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT transaction_id, external_id, type, source, status, raw_data,
                    processed_data, received_at, processed_at, error_message,
                    ims_status, ims_data
                FROM transactions
                WHERE transaction_id = ?
            """, (transaction_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            # Parse raw data
            raw_data = row[5]
            try:
                raw_data = json.loads(raw_data)
            except json.JSONDecodeError:
                pass  # Keep as string if it's not valid JSON
                
            # Parse processed data
            processed_data = row[6]
            if processed_data:
                try:
                    processed_data = json.loads(processed_data)
                except json.JSONDecodeError:
                    processed_data = None
            
            # Create transaction object
            transaction = Transaction(
                transaction_id=row[0],
                external_id=row[1],
                type=row[2],
                source=row[3],
                status=TransactionStatus(row[4]),
                raw_data=raw_data,
                processed_data=processed_data,
                received_at=datetime.fromisoformat(row[7]),
                processed_at=datetime.fromisoformat(row[8]) if row[8] else None,
                error_message=row[9]
            )
            
            # Parse IMS processing data if available
            if row[11]:
                try:
                    ims_data = json.loads(row[11])
                    transaction.ims_processing = ims_data
                except json.JSONDecodeError:
                    pass
            
            # Load transaction logs
            cursor.execute("""
                SELECT timestamp, message
                FROM transaction_logs
                WHERE transaction_id = ?
                ORDER BY log_id
            """, (transaction_id,))
            
            logs = cursor.fetchall()
            for log in logs:
                transaction.ims_processing.processing_logs.append(f"[{log[0]}] {log[1]}")
                
            conn.close()
            
            # Add to in-memory cache
            self.transactions[transaction_id] = transaction
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error loading transaction {transaction_id}: {str(e)}")
            return None