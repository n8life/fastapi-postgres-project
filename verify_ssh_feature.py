#!/usr/bin/env python3
"""
SSH Database Connection Feature Verification Script

This script verifies that the SSH database connection feature is properly implemented
and ready for use with actual SSH credentials.
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """Check that required dependencies are installed."""
    try:
        import sshtunnel
        import paramiko
        print("✅ SSH dependencies installed successfully")
        print(f"   - sshtunnel: {sshtunnel.__version__}")
        print(f"   - paramiko: {paramiko.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def check_ssh_tunnel_module():
    """Check that the SSH tunnel module is properly implemented."""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from app.ssh_tunnel import SSHTunnelManager
        
        # Verify the class has required methods
        manager = SSHTunnelManager()
        required_methods = ['create_tunnel', 'close_tunnel', 'is_active', 'get_connection_string']
        
        for method in required_methods:
            if not hasattr(manager, method):
                print(f"❌ Missing method: {method}")
                return False
                
        print("✅ SSH tunnel module properly implemented")
        print("   - SSHTunnelManager class available")
        print("   - All required methods present")
        return True
    except Exception as e:
        print(f"❌ SSH tunnel module error: {e}")
        return False

def check_database_integration():
    """Check that database manager supports SSH connections."""
    try:
        from app.database import DatabaseManager
        
        # Create manager instance and check SSH support
        manager = DatabaseManager()
        
        # Check that SSH-related attributes exist
        if not hasattr(manager, 'ssh_tunnel'):
            print("❌ DatabaseManager missing ssh_tunnel attribute")
            return False
            
        if not hasattr(manager, 'use_ssh'):
            print("❌ DatabaseManager missing use_ssh attribute")
            return False
            
        print("✅ Database manager SSH integration properly implemented")
        print("   - SSH tunnel attribute available")
        print("   - SSH connection mode detection available")
        return True
    except Exception as e:
        print(f"❌ Database integration error: {e}")
        return False

def check_environment_variables():
    """Check SSH environment variable configuration."""
    ssh_vars = [
        'USE_SSH_CONNECTION',
        'SSH_HOST', 
        'SSH_USER',
        'SSH_KEY_PATH',
        'SSH_POSTGRES_HOST',
        'SSH_POSTGRES_PORT', 
        'SSH_POSTGRES_USER',
        'SSH_POSTGRES_PASSWORD',
        'SSH_POSTGRES_DB'
    ]
    
    print("📋 SSH Environment Variables Configuration:")
    for var in ssh_vars:
        value = os.getenv(var, 'Not set')
        if var in ['SSH_POSTGRES_PASSWORD']:
            value = '***' if value != 'Not set' else 'Not set'
        print(f"   - {var}: {value}")
    
    return True

def check_docker_files():
    """Check that Docker configuration supports SSH."""
    docker_files = [
        'Dockerfile',
        'docker-compose.ssh.yml'
    ]
    
    missing_files = []
    for file in docker_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing Docker files: {missing_files}")
        return False
    
    # Check Dockerfile contains openssh-client
    dockerfile_content = Path('Dockerfile').read_text()
    if 'openssh-client' not in dockerfile_content:
        print("❌ Dockerfile missing openssh-client installation")
        return False
        
    print("✅ Docker configuration supports SSH")
    print("   - Dockerfile includes openssh-client")
    print("   - docker-compose.ssh.yml available")
    return True

def main():
    """Run all verification checks."""
    print("🔍 Verifying SSH Database Connection Feature Implementation\n")
    
    checks = [
        ("Dependencies", check_dependencies),
        ("SSH Tunnel Module", check_ssh_tunnel_module), 
        ("Database Integration", check_database_integration),
        ("Environment Variables", check_environment_variables),
        ("Docker Configuration", check_docker_files)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        results.append(check_func())
    
    print("\n" + "="*60)
    if all(results):
        print("🎉 SSH Database Connection Feature: FULLY IMPLEMENTED")
        print("\nNext steps:")
        print("1. Set SSH environment variables with actual credentials")
        print("2. Test with: docker-compose -f docker-compose.yml -f docker-compose.ssh.yml up")
        print("3. Verify SSH connection works with your PostgreSQL server")
    else:
        print("⚠️  SSH Database Connection Feature: ISSUES DETECTED")
        print("Please review the failed checks above")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)