#!/usr/bin/env python3
"""
Test Alembic Migration System Setup

Quick validation that Alembic is properly configured.
Run this after setting up the migration system.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Change to project root for proper path resolution
os.chdir(project_root)

from dotenv import load_dotenv
load_dotenv()

def test_alembic_imports():
    """Test that Alembic can be imported."""
    try:
        import alembic
        from alembic.config import Config
        from alembic import command
        print("✅ Alembic imports successful")
        return True
    except ImportError as e:
        print(f"❌ Alembic import failed: {e}")
        print("   Run: pip install -r requirements-core.txt")
        return False

def test_alembic_config():
    """Test that alembic.ini exists and is valid."""
    config_path = project_root / "alembic.ini"
    if not config_path.exists():
        print(f"❌ alembic.ini not found at {config_path}")
        return False
    
    try:
        from alembic.config import Config
        cfg = Config(str(config_path))
        print(f"✅ alembic.ini found and valid")
        return True
    except Exception as e:
        print(f"❌ alembic.ini is invalid: {e}")
        return False

def test_env_py():
    """Test that alembic/env.py exists."""
    env_path = project_root / "alembic" / "env.py"
    if not env_path.exists():
        print(f"❌ alembic/env.py not found at {env_path}")
        return False
    print("✅ alembic/env.py found")
    return True

def test_versions_dir():
    """Test that alembic/versions directory exists."""
    versions_path = project_root / "alembic" / "versions"
    if not versions_path.exists():
        print(f"❌ alembic/versions/ not found at {versions_path}")
        return False
    
    migrations = list(versions_path.glob("*.py"))
    migrations = [m for m in migrations if m.name != "__init__.py"]
    print(f"✅ alembic/versions/ found with {len(migrations)} migration(s)")
    return True

def test_database_connection():
    """Test that database connection info is available."""
    db_host = os.getenv("POSTGRES_HOST")
    db_port = os.getenv("POSTGRES_PORT")
    db_name = os.getenv("POSTGRES_DB")
    
    if not all([db_host, db_port, db_name]):
        print("⚠️  Database environment variables not set")
        print("   This is OK if not running migrations yet")
        return True
    
    print(f"✅ Database config: {db_name} at {db_host}:{db_port}")
    return True

def test_migration_script():
    """Test that migration management script exists."""
    script_path = project_root / "scripts" / "migrations" / "migrate.py"
    if not script_path.exists():
        print(f"❌ migrate.py not found at {script_path}")
        return False
    
    if not os.access(script_path, os.X_OK):
        print(f"⚠️  migrate.py is not executable (run: chmod +x {script_path})")
    
    print("✅ Migration management script found")
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("Alembic Migration System Validation")
    print("=" * 60)
    print()
    
    tests = [
        test_alembic_imports,
        test_alembic_config,
        test_env_py,
        test_versions_dir,
        test_migration_script,
        test_database_connection,
    ]
    
    results = [test() for test in tests]
    
    print()
    print("=" * 60)
    if all(results):
        print("✅ All checks passed! Migration system is ready.")
        print()
        print("Next steps:")
        print("  1. For v1.0.6 deployments: ./scripts/migrations/db-migrate.sh stamp head")
        print("  2. For fresh installs: ./scripts/migrations/db-migrate.sh upgrade")
        print("  3. Check status: ./scripts/migrations/db-migrate.sh status")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
