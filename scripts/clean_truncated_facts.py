#!/usr/bin/env python3
"""
Clean truncated/malformed facts from PostgreSQL.

Removes facts that are clearly incomplete or corrupted from LLM extraction:
- Ends with 'at', 'be', 'and'
- Contains incomplete phrases like 'might be', 'who collapse', 'access codes'
- Very short entity names
"""

import logging
import subprocess
import sys
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# SQL query to find truncated facts
FIND_TRUNCATED_QUERY = """
SELECT ufr.id, entity_name, relationship_type 
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
WHERE 
  -- Ends with problematic tokens
  entity_name ILIKE '% at' OR
  entity_name ILIKE '% be' OR
  entity_name ILIKE '% and' OR
  -- Contains incomplete phrases
  entity_name ILIKE '%might be%' OR
  entity_name ILIKE '%who collapse%' OR
  entity_name ILIKE '%access codes%' OR
  entity_name ILIKE '%you are actually%' OR
  entity_name ILIKE '%they''re%' OR
  -- Very short entity names
  LENGTH(TRIM(entity_name)) < 3
ORDER BY ufr.updated_at DESC;
"""

# SQL query to delete truncated facts
DELETE_TRUNCATED_QUERY = """
DELETE FROM user_fact_relationships 
WHERE entity_id IN (
  SELECT fe.id FROM fact_entities fe
  WHERE 
    entity_name ILIKE '% at' OR
    entity_name ILIKE '% be' OR
    entity_name ILIKE '% and' OR
    entity_name ILIKE '%might be%' OR
    entity_name ILIKE '%who collapse%' OR
    entity_name ILIKE '%access codes%' OR
    entity_name ILIKE '%you are actually%' OR
    entity_name ILIKE '%they''re%' OR
    LENGTH(TRIM(entity_name)) < 3
);
"""


def run_psql_command(query: str, output_format: Optional[str] = None) -> str:
    """Run a psql command and return output."""
    cmd = ['docker', 'exec', 'postgres', 'psql', '-U', 'whisperengine', '-d', 'whisperengine']
    
    if output_format == 'json':
        cmd.extend(['-c', query, '--json'])
    else:
        cmd.extend(['-c', query])
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    
    if result.returncode != 0:
        logger.error("psql command failed: %s", result.stderr)
        return ""
    
    return result.stdout


def find_truncated_facts() -> int:
    """Find and display truncated facts."""
    logger.info("🔍 Scanning for truncated/malformed facts...")
    
    output = run_psql_command(FIND_TRUNCATED_QUERY)
    
    if not output or 'rows' not in output.lower():
        logger.info("✓ No truncated facts found!")
        return 0
    
    lines = output.strip().split('\n')
    # Filter out header and footer lines
    data_lines = [l for l in lines if l and not l.startswith('(') and not l.startswith('-')]
    
    if not data_lines or len(data_lines) == 0:
        logger.info("✓ No truncated facts found!")
        return 0
    
    logger.info("Found %d truncated/malformed facts:", len(data_lines))
    for line in data_lines[:20]:
        logger.info("  %s", line)
    
    if len(data_lines) > 20:
        logger.info("  ... and %d more", len(data_lines) - 20)
    
    return len(data_lines)


def delete_truncated_facts(dry_run: bool = True) -> int:
    """Delete truncated facts from the database."""
    
    if dry_run:
        count = find_truncated_facts()
        if count > 0:
            logger.info("[DRY RUN] Would delete %d truncated facts", count)
            logger.info("Run with --execute flag to actually delete")
        return 0
    else:
        logger.info("🗑️ Deleting truncated facts...")
        output = run_psql_command(DELETE_TRUNCATED_QUERY)
        
        # Parse the output to get count
        if 'DELETE' in output:
            parts = output.split()
            if len(parts) >= 1:
                try:
                    count = int(parts[-1])
                    logger.info("✓ Successfully deleted %d truncated facts", count)
                    return count
                except ValueError:
                    pass
        
        logger.info("✓ Truncated facts cleaned up")
        return 0


def main() -> None:
    """Main entry point."""
    dry_run = '--execute' not in sys.argv
    
    if dry_run:
        find_truncated_facts()
    else:
        delete_truncated_facts(dry_run=False)


if __name__ == "__main__":
    main()
