#!/usr/bin/env python3
"""
Initialize Graphiti database with required indices and constraints
This fixes the missing name_embedding property issue
"""

import asyncio
import os
from pathlib import Path

# Add backend to path to import graphiti
import sys
sys.path.append(str(Path(__file__).parent.parent / "backend"))

try:
    from graphiti_core import Graphiti
    GRAPHITI_AVAILABLE = True
except ImportError:
    print("❌ graphiti_core not available. Run: cd backend && uv add 'graphiti-core[all]'")
    GRAPHITI_AVAILABLE = False


async def initialize_database():
    """Initialize Graphiti database with proper indices and constraints"""
    
    if not GRAPHITI_AVAILABLE:
        return False
    
    # Get connection details from environment
    neo4j_uri = os.getenv('NEO4J_URI')
    neo4j_user = os.getenv('NEO4J_USER')
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    
    if not all([neo4j_uri, neo4j_user, neo4j_password]):
        print("❌ Missing Neo4j connection details in environment")
        print("Required: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
        return False
    
    print("🔧 Initializing Graphiti database...")
    print(f"🔗 Connecting to: {neo4j_uri}")
    print(f"👤 User: {neo4j_user}")
    
    try:
        # Create Graphiti client
        client = Graphiti(
            uri=neo4j_uri,
            user=neo4j_user,
            password=neo4j_password
        )
        
        print("📡 Testing connection...")
        # Test connection by trying to build indices
        await client.build_indices_and_constraints()
        
        print("✅ Database initialization completed successfully!")
        print("📊 Created indices and constraints for:")
        print("   • Entity nodes with name_embedding vectors")
        print("   • Episode nodes")
        print("   • Relationship constraints")
        print("   • Vector similarity indices")
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    # Load environment variables
    from pathlib import Path
    import subprocess
    
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        print(f"📁 Loading environment from: {env_file}")
        # Source .env file
        result = subprocess.run(
            f"set -a; source {env_file}; set +a; env", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if '=' in line and not line.startswith('_'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    success = asyncio.run(initialize_database())
    print("\n" + "="*50)
    if success:
        print("🎉 Database ready! You can now run your Graphiti tests.")
    else:
        print("❌ Initialization failed. Check the error messages above.")
    
    exit(0 if success else 1)