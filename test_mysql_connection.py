#!/usr/bin/env python3
"""
Test MySQL connection to Triton database via SSM tunnel
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test the MySQL connection"""
    try:
        import mysql.connector
        
        config = {
            'host': os.getenv('TRITON_MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('TRITON_MYSQL_PORT', '13306')),
            'database': os.getenv('TRITON_MYSQL_DATABASE', 'triton_staging'),
            'user': os.getenv('TRITON_MYSQL_USER'),
            'password': os.getenv('TRITON_MYSQL_PASSWORD'),
            'autocommit': False
        }
        
        print("Testing MySQL connection with config:")
        print(f"Host: {config['host']}")
        print(f"Port: {config['port']}")
        print(f"Database: {config['database']}")
        print(f"User: {config['user']}")
        print()
        
        # Test connection
        print("Connecting to MySQL...")
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():
            print("✅ Successfully connected to MySQL!")
            
            # Test basic query
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            db_name = cursor.fetchone()
            print(f"Current database: {db_name[0]}")
            
            # Show tables
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            print(f"Found {len(tables)} tables:")
            for table in tables[:10]:  # Show first 10 tables
                print(f"  - {table[0]}")
            if len(tables) > 10:
                print(f"  ... and {len(tables) - 10} more")
            
            # Check for key tables
            table_names = [table[0] for table in tables]
            key_tables = ['opportunities', 'accounts', 'producers', 'quotes', 'ims_transaction_logs']
            
            print("\nChecking for key tables:")
            for table in key_tables:
                if table in table_names:
                    print(f"  ✅ {table}")
                else:
                    print(f"  ❌ {table} (missing)")
            
            cursor.close()
            connection.close()
            print("\n✅ Connection test completed successfully!")
            return True
            
    except ImportError:
        print("❌ mysql-connector-python not installed")
        print("Install with: pip install mysql-connector-python")
        return False
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)