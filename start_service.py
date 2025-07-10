#!/usr/bin/env python3
"""
Start the IMS integration service
Handles port conflicts and provides clear feedback
"""

import os
import sys
import subprocess
import socket
import signal

def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('', port))
            return False
        except:
            return True

def find_free_port(start_port=8000):
    """Find a free port starting from start_port"""
    port = start_port
    while port < 9000:
        if not is_port_in_use(port):
            return port
        port += 1
    return None

def main():
    """Start the service"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Start IMS integration service')
    parser.add_argument('--port', type=int, default=8000,
                       help='Port to run on (default: 8000)')
    parser.add_argument('--host', default='0.0.0.0',
                       help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--reload', action='store_true',
                       help='Enable auto-reload on code changes')
    
    args = parser.parse_args()
    
    # Check if port is in use
    if is_port_in_use(args.port):
        print(f"❌ Port {args.port} is already in use!")
        free_port = find_free_port(args.port + 1)
        if free_port:
            print(f"💡 Try using port {free_port} instead:")
            print(f"   python start_service.py --port {free_port}")
        else:
            print("❌ No free ports found between 8000-9000")
        
        # Try to find what's using the port
        try:
            result = subprocess.run(['lsof', '-i', f':{args.port}'], 
                                  capture_output=True, text=True)
            if result.stdout:
                print(f"\n📋 Port {args.port} is being used by:")
                print(result.stdout)
        except:
            pass
        
        return 1
    
    print("=" * 60)
    print("🚀 STARTING IMS INTEGRATION SERVICE")
    print("=" * 60)
    print(f"📍 URL: http://localhost:{args.port}")
    print(f"📁 API Docs: http://localhost:{args.port}/docs")
    print(f"🔄 Auto-reload: {'Enabled' if args.reload else 'Disabled'}")
    print("\n✋ Press Ctrl+C to stop the service")
    print("=" * 60)
    
    # Build the uvicorn command
    cmd = [
        sys.executable, '-m', 'uvicorn',
        'app.main:app',
        '--host', args.host,
        '--port', str(args.port)
    ]
    
    if args.reload:
        cmd.append('--reload')
    
    # Add some color to the logs
    cmd.extend(['--log-config', 'logging.yaml']) if os.path.exists('logging.yaml') else None
    
    try:
        # Run the service
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\n✅ Service stopped successfully")
        return 0
    except Exception as e:
        print(f"\n❌ Error starting service: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())