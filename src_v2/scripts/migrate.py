import os
import sys
from alembic.config import Config
from alembic import command
from loguru import logger

def run_migrations():
    """
    Runs Alembic migrations programmatically.
    """
    logger.info("Running database migrations...")
    try:
        # Point to our new alembic_v2.ini
        alembic_cfg = Config("alembic_v2.ini")
        
        # Run the upgrade command
        command.upgrade(alembic_cfg, "head")
        
        logger.info("Database migrations completed successfully.")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        # We might want to exit if migrations fail, or just warn
        # sys.exit(1)

if __name__ == "__main__":
    run_migrations()
