#!/usr/bin/env python3
"""
Safe server startup script for JiyashCreation Django project
"""
import os
import sys
import subprocess
import webbrowser
import time

def check_port_available(port):
    """Check if a port is available"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False

def main():
    """Main startup function"""
    print("🚀 Starting JiyashCreation Django Server")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("❌ Error: manage.py not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Find an available port
    ports_to_try = [8000, 8001, 8002, 8003, 8004]
    available_port = None
    
    for port in ports_to_try:
        if check_port_available(port):
            available_port = port
            break
    
    if not available_port:
        print("❌ Error: No available ports found. Please check if other servers are running.")
        sys.exit(1)
    
    print(f"✅ Using port {available_port}")
    
    # Run basic checks
    print("🔄 Running system checks...")
    try:
        result = subprocess.run(['python', 'manage.py', 'check'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print("❌ System check failed:")
            print(result.stderr)
            sys.exit(1)
        print("✅ System checks passed")
    except Exception as e:
        print(f"⚠️  Warning: Could not run system check: {e}")
    
    # Start the server
    server_url = f"http://127.0.0.1:{available_port}/"
    print(f"🌐 Starting server at {server_url}")
    print("📋 Available URLs:")
    print(f"   • Homepage: {server_url}")
    print(f"   • Admin: {server_url}admin/")
    print(f"   • Shop: {server_url}shop-all/")
    print("\n💡 Tips:")
    print("   • Use Ctrl+C to stop the server")
    print("   • Use HTTP (not HTTPS) for development")
    print("   • Clear browser cache if you see HTTPS errors")
    print("=" * 50)
    
    try:
        # Start the Django development server
        subprocess.run([
            'python', 'manage.py', 'runserver', 
            f'127.0.0.1:{available_port}', '--noreload'
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure .env file exists with proper SECRET_KEY")
        print("2. Run: python manage.py migrate")
        print("3. Check if another server is running on the port")
        print("4. Try: python manage.py runserver 127.0.0.1:8002")

if __name__ == "__main__":
    main()
