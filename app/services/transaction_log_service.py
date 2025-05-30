"""
Transaction Log Service
Handles logging of all IMS transactions to the ims_transaction_logs table
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
import mysql.connector
from mysql.connector import Error

logger = logging.getLogger(__name__)


class TransactionLogService:
    """
    Service for managing ims_transaction_logs entries
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.connection = None
        
    def _get_connection(self):
        """Get database connection"""
        if not self.connection or not self.connection.is_connected():
            self.connection = mysql.connector.connect(**self.db_config)
        return self.connection
    
    def create_transaction_log(
        self,
        transaction_type: str,
        resource_type: str,
        resource_id: int,
        external_transaction_id: str,
        request_data: Dict[str, Any]
    ) -> Optional[int]:
        """
        Create a new transaction log entry
        
        Returns:
            The ID of the created log entry
        """
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            
            query = """
                INSERT INTO ims_transaction_logs 
                (transaction_type, resource_type, resource_id, 
                 external_transaction_id, status, request_data, created_at)
                VALUES (%s, %s, %s, %s, 'pending', %s, %s)
            """
            
            values = (
                transaction_type,
                resource_type,
                resource_id,
                external_transaction_id,
                json.dumps(request_data),
                datetime.now()
            )
            
            cursor.execute(query, values)
            connection.commit()
            
            log_id = cursor.lastrowid
            logger.info(
                f"Created transaction log {log_id} for {transaction_type} "
                f"{resource_type} {resource_id}"
            )
            
            cursor.close()
            return log_id
            
        except Error as e:
            logger.error(f"Error creating transaction log: {e}")
            return None
    
    def update_transaction_log(
        self,
        log_id: int,
        status: str,
        response_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        ims_policy_number: Optional[str] = None
    ):
        """Update an existing transaction log entry"""
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            
            # Build update query
            update_fields = ["status = %s", "last_attempt_at = %s"]
            values = [status, datetime.now()]
            
            if response_data:
                update_fields.append("response_data = %s")
                values.append(json.dumps(response_data))
            
            if error_message:
                update_fields.append("error_message = %s")
                values.append(error_message)
            
            if ims_policy_number:
                update_fields.append("ims_policy_number = %s")
                values.append(ims_policy_number)
            
            if status == 'completed':
                update_fields.append("completed_at = %s")
                values.append(datetime.now())
            
            # Increment attempt count
            update_fields.append("attempt_count = attempt_count + 1")
            
            # Add log_id to values
            values.append(log_id)
            
            query = f"""
                UPDATE ims_transaction_logs 
                SET {', '.join(update_fields)}
                WHERE id = %s
            """
            
            cursor.execute(query, values)
            connection.commit()
            
            logger.info(f"Updated transaction log {log_id} to status: {status}")
            cursor.close()
            
        except Error as e:
            logger.error(f"Error updating transaction log {log_id}: {e}")
    
    def get_pending_transactions(self, limit: int = 10) -> list:
        """Get pending transactions that need processing"""
        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT * FROM ims_transaction_logs 
                WHERE status IN ('pending', 'retry')
                AND (attempt_count < 3 OR attempt_count IS NULL)
                ORDER BY created_at ASC
                LIMIT %s
            """
            
            cursor.execute(query, (limit,))
            results = cursor.fetchall()
            
            cursor.close()
            return results
            
        except Error as e:
            logger.error(f"Error getting pending transactions: {e}")
            return []
    
    def check_already_processed(
        self,
        resource_type: str,
        resource_id: int,
        transaction_type: str
    ) -> bool:
        """Check if a transaction has already been processed successfully"""
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            
            query = """
                SELECT COUNT(*) FROM ims_transaction_logs 
                WHERE resource_type = %s 
                AND resource_id = %s 
                AND transaction_type = %s
                AND status = 'completed'
            """
            
            cursor.execute(query, (resource_type, resource_id, transaction_type))
            count = cursor.fetchone()[0]
            
            cursor.close()
            return count > 0
            
        except Error as e:
            logger.error(f"Error checking if already processed: {e}")
            return False
    
    def get_transaction_history(
        self,
        resource_type: str,
        resource_id: int
    ) -> list:
        """Get all transaction history for a specific resource"""
        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT * FROM ims_transaction_logs 
                WHERE resource_type = %s AND resource_id = %s
                ORDER BY created_at DESC
            """
            
            cursor.execute(query, (resource_type, resource_id))
            results = cursor.fetchall()
            
            cursor.close()
            return results
            
        except Error as e:
            logger.error(f"Error getting transaction history: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Closed transaction log database connection")