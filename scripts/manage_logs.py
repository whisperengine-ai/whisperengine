#!/usr/bin/env python3
"""
Log Management Script for Discord Bot
Provides utilities for log cleanup, archival, and maintenance.
Part of DevOps best practices implementation.
"""

import os
import sys
import gzip
import shutil
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
import logging


def setup_script_logging():
    """Setup logging for this script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def get_log_files(log_dir: Path, pattern: str = "*.log*") -> List[Path]:
    """Get all log files matching pattern"""
    return list(log_dir.glob(pattern))


def compress_log_file(log_file: Path) -> Optional[Path]:
    """Compress a log file using gzip"""
    logger = logging.getLogger(__name__)
    
    if log_file.suffix == '.gz':
        logger.info(f"File {log_file} is already compressed")
        return log_file
    
    compressed_file = log_file.with_suffix(log_file.suffix + '.gz')
    
    try:
        with open(log_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove original file after successful compression
        log_file.unlink()
        logger.info(f"Compressed {log_file} -> {compressed_file}")
        return compressed_file
        
    except Exception as e:
        logger.error(f"Failed to compress {log_file}: {e}")
        if compressed_file.exists():
            compressed_file.unlink()
        return None


def archive_old_logs(log_dir: Path, days_old: int = 7, compress: bool = True) -> int:
    """Archive logs older than specified days"""
    logger = logging.getLogger(__name__)
    archived_count = 0
    
    archive_dir = log_dir / "archived"
    archive_dir.mkdir(exist_ok=True)
    
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    for log_file in get_log_files(log_dir):
        if log_file.parent == archive_dir:
            continue  # Skip already archived files
            
        # Check file modification time
        file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
        
        if file_time < cutoff_date:
            archive_path = archive_dir / log_file.name
            
            try:
                if compress and not log_file.name.endswith('.gz'):
                    # Move to archive dir first, then compress
                    temp_path = archive_dir / log_file.name
                    shutil.move(str(log_file), str(temp_path))
                    compress_log_file(temp_path)
                else:
                    shutil.move(str(log_file), str(archive_path))
                
                logger.info(f"Archived {log_file.name}")
                archived_count += 1
                
            except Exception as e:
                logger.error(f"Failed to archive {log_file}: {e}")
    
    return archived_count


def cleanup_old_logs(log_dir: Path, days_to_keep: int = 30) -> int:
    """Delete logs older than specified days"""
    logger = logging.getLogger(__name__)
    deleted_count = 0
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    # Clean up both main log dir and archived logs
    for search_dir in [log_dir, log_dir / "archived"]:
        if not search_dir.exists():
            continue
            
        for log_file in get_log_files(search_dir):
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            
            if file_time < cutoff_date:
                try:
                    log_file.unlink()
                    logger.info(f"Deleted old log: {log_file.name}")
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete {log_file}: {e}")
    
    return deleted_count


def get_log_stats(log_dir: Path) -> dict:
    """Get statistics about log files"""
    stats = {
        'total_files': 0,
        'total_size_mb': 0.0,
        'compressed_files': 0,
        'archived_files': 0,
        'recent_files': 0  # Files from last 24 hours
    }
    
    recent_cutoff = datetime.now() - timedelta(hours=24)
    
    for log_file in get_log_files(log_dir):
        stats['total_files'] += 1
        stats['total_size_mb'] += log_file.stat().st_size / (1024 * 1024)
        
        if log_file.suffix == '.gz':
            stats['compressed_files'] += 1
        
        if 'archived' in str(log_file):
            stats['archived_files'] += 1
        
        file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
        if file_time > recent_cutoff:
            stats['recent_files'] += 1
    
    stats['total_size_mb'] = round(stats['total_size_mb'], 2)
    return stats


def main():
    parser = argparse.ArgumentParser(description='Discord Bot Log Management')
    parser.add_argument('--log-dir', default='logs', help='Log directory path')
    parser.add_argument('--action', choices=['stats', 'archive', 'cleanup', 'compress'], 
                       required=True, help='Action to perform')
    parser.add_argument('--days-old', type=int, default=7, 
                       help='Days old for archiving (default: 7)')
    parser.add_argument('--days-to-keep', type=int, default=30, 
                       help='Days to keep logs before deletion (default: 30)')
    parser.add_argument('--compress', action='store_true', 
                       help='Compress logs when archiving')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without doing it')
    
    args = parser.parse_args()
    
    logger = setup_script_logging()
    log_dir = Path(args.log_dir)
    
    if not log_dir.exists():
        logger.error(f"Log directory {log_dir} does not exist")
        sys.exit(1)
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
    
    try:
        if args.action == 'stats':
            stats = get_log_stats(log_dir)
            print(f"\n📊 Log Statistics for {log_dir}:")
            print(f"  Total files: {stats['total_files']}")
            print(f"  Total size: {stats['total_size_mb']} MB")
            print(f"  Compressed files: {stats['compressed_files']}")
            print(f"  Archived files: {stats['archived_files']}")
            print(f"  Recent files (24h): {stats['recent_files']}")
            
        elif args.action == 'archive':
            if not args.dry_run:
                count = archive_old_logs(log_dir, args.days_old, args.compress)
                logger.info(f"Archived {count} log files")
            else:
                logger.info(f"Would archive logs older than {args.days_old} days")
                
        elif args.action == 'cleanup':
            if not args.dry_run:
                count = cleanup_old_logs(log_dir, args.days_to_keep)
                logger.info(f"Deleted {count} old log files")
            else:
                logger.info(f"Would delete logs older than {args.days_to_keep} days")
                
        elif args.action == 'compress':
            compressed_count = 0
            for log_file in get_log_files(log_dir, "*.log"):
                if not args.dry_run:
                    if compress_log_file(log_file):
                        compressed_count += 1
                else:
                    logger.info(f"Would compress: {log_file}")
                    compressed_count += 1
            
            if not args.dry_run:
                logger.info(f"Compressed {compressed_count} log files")
            else:
                logger.info(f"Would compress {compressed_count} log files")
    
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
