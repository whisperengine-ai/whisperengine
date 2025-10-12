#!/usr/bin/env python3
"""
WhisperEngine Database Migration Manager

This script provides a simple interface for managing Alembic database migrations.
It wraps common Alembic commands with WhisperEngine-specific configuration.

Usage:
    python scripts/migrations/migrate.py status              # Show current migration status
    python scripts/migrations/migrate.py history             # Show migration history
    python scripts/migrations/migrate.py create "description" # Create new migration
    python scripts/migrations/migrate.py upgrade             # Apply all pending migrations
    python scripts/migrations/migrate.py upgrade +1          # Apply next migration
    python scripts/migrations/migrate.py downgrade -1        # Rollback last migration
    python scripts/migrations/migrate.py current             # Show current revision
"""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


def run_alembic_command(args: list[str]) -> int:
    """Execute an Alembic command with proper environment."""
    # Ensure we're in the project root
    os.chdir(project_root)
    
    # Build command
    cmd = ["alembic"] + args
    
    # Show what we're running
    print(f"🔧 Running: {' '.join(cmd)}")
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Show database connection info (without password)
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5433")
    db_name = os.getenv("POSTGRES_DB", "whisperengine")
    print(f"🗄️  Database: {db_name} at {db_host}:{db_port}\n")
    
    # Execute
    result = subprocess.run(cmd, env=os.environ.copy())
    return result.returncode


def show_status():
    """Show current migration status."""
    print("=" * 60)
    print("Current Migration Status")
    print("=" * 60)
    return run_alembic_command(["current", "--verbose"])


def show_history():
    """Show migration history."""
    print("=" * 60)
    print("Migration History")
    print("=" * 60)
    return run_alembic_command(["history", "--verbose"])


def create_migration(description: str):
    """Create a new migration file."""
    if not description:
        print("❌ Error: Migration description required")
        print("Usage: migrate.py create 'Add user preferences table'")
        return 1
    
    print("=" * 60)
    print(f"Creating new migration: {description}")
    print("=" * 60)
    
    # Generate migration file
    return run_alembic_command(["revision", "-m", description])


def upgrade_migrations(target: str = "head"):
    """Apply migrations up to target revision."""
    print("=" * 60)
    print(f"Upgrading database to: {target}")
    print("=" * 60)
    return run_alembic_command(["upgrade", target])


def downgrade_migrations(target: str = "-1"):
    """Downgrade database to target revision."""
    print("=" * 60)
    print(f"⚠️  Downgrading database to: {target}")
    print("=" * 60)
    
    # Confirm downgrade
    response = input("Are you sure you want to downgrade? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Downgrade cancelled")
        return 0
    
    return run_alembic_command(["downgrade", target])


def stamp_database(revision: str = "head"):
    """Mark database as being at a specific revision without running migrations."""
    print("=" * 60)
    print(f"Stamping database with revision: {revision}")
    print("=" * 60)
    print("⚠️  WARNING: This marks the database as migrated without running SQL!")
    print("Only use this for initializing an existing database.")
    
    response = input("Are you sure? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Stamp cancelled")
        return 0
    
    return run_alembic_command(["stamp", revision])


def show_help():
    """Show help message."""
    print(__doc__)
    return 0


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        return show_help()
    
    command = sys.argv[1].lower()
    
    if command in ["help", "-h", "--help"]:
        return show_help()
    
    elif command == "status":
        return show_status()
    
    elif command == "current":
        return run_alembic_command(["current", "--verbose"])
    
    elif command == "history":
        return show_history()
    
    elif command == "create":
        if len(sys.argv) < 3:
            print("❌ Error: Migration description required")
            print("Usage: migrate.py create 'Add user preferences table'")
            return 1
        description = " ".join(sys.argv[2:])
        return create_migration(description)
    
    elif command == "upgrade":
        target = sys.argv[2] if len(sys.argv) > 2 else "head"
        return upgrade_migrations(target)
    
    elif command == "downgrade":
        target = sys.argv[2] if len(sys.argv) > 2 else "-1"
        return downgrade_migrations(target)
    
    elif command == "stamp":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        return stamp_database(revision)
    
    else:
        print(f"❌ Error: Unknown command '{command}'")
        return show_help()


if __name__ == "__main__":
    sys.exit(main())
