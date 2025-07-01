#!/usr/bin/env python3
"""
Test connection and create ims_transaction_logs table
"""

def test_and_create():
    """Test connection and create table if successful"""
    try:
        import mysql.connector
        
        config = {
            'host': 'localhost',
            'port': 13307,
            'database': 'greenhill_db',
            'user': 'greenhill',
            'password': '62OEqb9sjR4ZX5vBMdB521hx6W2A',
            'autocommit': False
        }
        
        print("Testing connection to localhost:13307...")
        connection = mysql.connector.connect(**config)
        print("✅ Connection successful!")
        
        cursor = connection.cursor()
        
        # Check if table already exists
        cursor.execute("SHOW TABLES LIKE 'ims_transaction_logs'")
        exists = cursor.fetchone()
        
        if exists:
            print("ℹ️ Table 'ims_transaction_logs' already exists")
            cursor.execute("SELECT COUNT(*) FROM ims_transaction_logs")
            count = cursor.fetchone()[0]
            print(f"   Current records: {count}")
            return True
        
        print("Creating ims_transaction_logs table...")
        
        # Create table SQL
        create_table_sql = """
        CREATE TABLE ims_transaction_logs (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            transaction_type VARCHAR(50) NOT NULL,
            resource_type VARCHAR(50) NOT NULL,
            resource_id BIGINT NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            attempt_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_attempt_at TIMESTAMP NULL,
            completed_at TIMESTAMP NULL,
            request_data JSON,
            response_data JSON,
            error_message TEXT,
            ims_policy_number VARCHAR(255),
            external_transaction_id VARCHAR(255),
            
            INDEX idx_status (status),
            INDEX idx_resource (resource_type, resource_id),
            INDEX idx_created_at (created_at),
            INDEX idx_transaction_type (transaction_type)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        cursor.execute(create_table_sql)
        connection.commit()
        print("✅ Table created successfully!")
        
        # Check table structure
        cursor.execute("DESCRIBE ims_transaction_logs")
        columns = cursor.fetchall()
        print(f"\nTable structure ({len(columns)} columns):")
        for col in columns:
            print(f"  {col[0]} - {col[1]}")
        
        # Add test transactions for the same opportunities we tested
        print("\nAdding test transactions for opportunities that worked in integration test...")
        test_data = [
            ('binding', 'opportunity', 315, 'GAH-01002-150513'),
            ('binding', 'opportunity', 381, 'GAH-01002-150526'), 
            ('binding', 'opportunity', 393, 'GAH-01001-150520')
        ]
        
        for tx_type, res_type, res_id, policy_num in test_data:
            cursor.execute("""
                INSERT INTO ims_transaction_logs 
                (transaction_type, resource_type, resource_id, status, external_transaction_id)
                VALUES (%s, %s, %s, 'pending', %s)
            """, (tx_type, res_type, res_id, f"test_{policy_num}"))
        
        connection.commit()
        print(f"✅ Added {len(test_data)} test transactions")
        
        # Verify 
        cursor.execute("SELECT id, transaction_type, resource_id, status, external_transaction_id FROM ims_transaction_logs")
        rows = cursor.fetchall()
        print(f"\nAdded transactions:")
        for row in rows:
            print(f"  ID {row[0]}: {row[1]} for opportunity {row[2]} - {row[3]} ({row[4]})")
        
        cursor.close()
        connection.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ MySQL Error: {str(e)}")
        if "10061" in str(e):
            print("\n💡 This usually means the port forwarding is not active.")
            print("   Make sure you have this running in another terminal:")
            print("   aws ssm start-session --target $INSTANCE_ID --document-name AWS-StartPortForwardingSessionToRemoteHost --parameters host=triton-dev.ctfcgagzmyca.us-east-1.rds.amazonaws.com,portNumber=3306,localPortNumber=13307 --profile ryansg --no-verify-ssl")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_and_create()
    
    if success:
        print("\n" + "="*70)
        print("🎉 IMS TRANSACTION LOGS TABLE READY!")
        print("="*70)
        print("Next steps:")
        print("1. The integration can now track all IMS transactions")
        print("2. Run integration tests and monitor the table")
        print("3. Check status: SELECT * FROM ims_transaction_logs;")
        print("="*70)