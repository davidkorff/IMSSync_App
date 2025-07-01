#!/usr/bin/env python3
"""
Test connection to triton-dev database
Provides alternative methods if mysql-connector-python isn't available
"""

def test_triton_dev_connection():
    """Test connection to triton-dev database"""
    
    print("Testing Triton-Dev Database Connection")
    print("="*50)
    
    # Database details
    host = "triton-dev.ctfcgagzmyca.us-east-1.rds.amazonaws.com"
    port = 3306
    database = "greenhill_db"
    user = "greenhill"
    password = "62OEqb9sjR4ZX5vBMdB521hx6W2A"
    
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Database: {database}")
    print(f"User: {user}")
    print()
    
    # Method 1: Try mysql-connector-python
    try:
        import mysql.connector
        print("✅ mysql.connector available - testing connection...")
        
        config = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password,
            'autocommit': False,
            'connect_timeout': 10
        }
        
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor(dictionary=True)
        
        # Test basic query
        cursor.execute("SELECT COUNT(*) as count FROM opportunities WHERE status = 'bound'")
        result = cursor.fetchone()
        
        print(f"✅ Connection successful!")
        print(f"   Found {result['count']} bound opportunities")
        
        # Test recent data
        cursor.execute("""
            SELECT COUNT(*) as recent_count 
            FROM opportunities 
            WHERE status = 'bound' 
            AND bound_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """)
        recent = cursor.fetchone()
        
        print(f"   Found {recent['recent_count']} bound in last 30 days")
        
        cursor.close()
        connection.close()
        
        return True
        
    except ImportError:
        print("❌ mysql.connector not available")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Method 2: Check network connectivity
    print("\n📡 Testing network connectivity...")
    try:
        import socket
        
        # Test if we can reach the host on port 3306
        sock = socket.create_connection((host, port), timeout=10)
        sock.close()
        print(f"✅ Network connection to {host}:{port} successful")
        
    except Exception as e:
        print(f"❌ Network connection failed: {e}")
        print("   This might be a VPC/security group issue")
        return False
    
    # Method 3: Provide manual verification steps
    print("\n🔧 Manual Verification Options:")
    print("1. Ensure your IP is whitelisted in RDS security group")
    print("2. Verify VPC configuration allows external access")
    print("3. Check if RDS instance is publicly accessible")
    print("4. Test with mysql client:")
    print(f"   mysql -h {host} -P {port} -u {user} -p{password} {database}")
    
    return False

if __name__ == "__main__":
    test_triton_dev_connection()