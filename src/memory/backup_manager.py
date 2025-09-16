"""
Backup and recovery system for ChromaDB HTTP service data
"""

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

from src.memory.chromadb_http_manager import ChromaDBHTTPManager
from src.memory.memory_manager import UserMemoryManager
from src.utils.exceptions import MemoryError

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages backup and recovery operations for ChromaDB HTTP service data"""

    def __init__(
        self,
        backup_path: str | None = None,
        chromadb_host: str | None = None,
        chromadb_port: int | None = None,
    ):
        # Load backup path from environment variables
        if backup_path is None:
            backup_path = os.getenv("BACKUP_PATH", "./backups")

        self.backup_path = Path(backup_path)
        self.backup_path.mkdir(exist_ok=True)

        # ChromaDB HTTP connection details
        self.chromadb_host = chromadb_host or os.getenv("CHROMADB_HOST", "localhost")
        self.chromadb_port = chromadb_port or int(os.getenv("CHROMADB_PORT", "8000"))

        # Load backup configuration from environment
        self.auto_backup_enabled = os.getenv("AUTO_BACKUP_ENABLED", "true").lower() == "true"
        self.backup_interval_hours = int(os.getenv("AUTO_BACKUP_INTERVAL_HOURS", "24"))
        self.backup_retention_count = int(os.getenv("BACKUP_RETENTION_COUNT", "5"))

        # Log relative path to avoid exposing full system paths
        relative_backup_path = os.path.relpath(backup_path)
        logger.info(
            f"BackupManager initialized: chromadb_http={self.chromadb_host}:{self.chromadb_port}, backups={relative_backup_path}"
        )
        logger.info(
            f"Auto backup: enabled={self.auto_backup_enabled}, interval={self.backup_interval_hours}h, retention={self.backup_retention_count}"
        )

    async def create_backup(self, include_metadata: bool = True) -> str:
        """
        Create a backup of the ChromaDB HTTP service data

        Args:
            include_metadata: Whether to include metadata export

        Returns:
            Path to the created backup
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"chromadb_backup_{timestamp}"
            backup_dir = self.backup_path / backup_name

            # Create backup directory
            backup_dir.mkdir(exist_ok=True)

            # Initialize ChromaDB HTTP manager
            chromadb_manager = ChromaDBHTTPManager(host=self.chromadb_host, port=self.chromadb_port)
            await chromadb_manager.initialize()

            # Export data via HTTP API
            await self._export_http_data(backup_dir, chromadb_manager)

            # Export metadata if requested
            if include_metadata:
                await self._export_metadata(backup_dir, chromadb_manager)

            # Create backup info file
            backup_info = {
                "timestamp": timestamp,
                "chromadb_host": self.chromadb_host,
                "chromadb_port": self.chromadb_port,
                "backup_size": self._get_directory_size(backup_dir),
                "include_metadata": include_metadata,
                "backup_type": "http_api",
            }

            with open(backup_dir / "backup_info.json", "w") as f:
                json.dump(backup_info, f, indent=2)

            logger.info(f"Backup created successfully: {backup_dir}")
            return str(backup_dir)

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise MemoryError(f"Backup creation failed: {e}")

    def restore_backup(self, backup_path: str, confirm: bool = False) -> bool:
        """
        Restore ChromaDB data from a backup

        Args:
            backup_path: Path to the backup directory
            confirm: Whether to proceed without confirmation

        Returns:
            True if restoration was successful
        """
        try:
            backup_dir = Path(backup_path)
            if not backup_dir.exists():
                raise MemoryError(f"Backup directory does not exist: {backup_path}")

            # Check backup validity
            backup_info_file = backup_dir / "backup_info.json"
            if not backup_info_file.exists():
                raise MemoryError("Invalid backup: missing backup_info.json")

            # Load backup info
            with open(backup_info_file) as f:
                backup_info = json.load(f)

            logger.info(f"Restoring backup from {backup_info['timestamp']}")

            # Create backup of current data before restore
            if self.chromadb_path.exists() and not confirm:
                current_backup = self.create_backup()
                logger.info(f"Created safety backup at {current_backup}")

            # Remove current ChromaDB data
            if self.chromadb_path.exists():
                shutil.rmtree(self.chromadb_path)
                logger.info("Removed existing ChromaDB data")

            # Restore backup
            backup_chromadb = backup_dir / "chromadb_data"
            if backup_chromadb.exists():
                shutil.copytree(backup_chromadb, self.chromadb_path)
                logger.info("Restored ChromaDB data from backup")
            else:
                raise MemoryError("Backup does not contain ChromaDB data")

            logger.info("Backup restoration completed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            raise MemoryError(f"Backup restoration failed: {e}")

    def list_backups(self) -> list[dict]:
        """List all available backups with their metadata"""
        backups = []

        try:
            for backup_dir in self.backup_path.iterdir():
                if backup_dir.is_dir() and backup_dir.name.startswith("chromadb_backup_"):
                    backup_info_file = backup_dir / "backup_info.json"

                    if backup_info_file.exists():
                        try:
                            with open(backup_info_file) as f:
                                backup_info = json.load(f)

                            backup_info["path"] = str(backup_dir)
                            backup_info["size_mb"] = backup_info.get("backup_size", 0) / (
                                1024 * 1024
                            )
                            backups.append(backup_info)

                        except Exception as e:
                            logger.warning(f"Could not read backup info for {backup_dir}: {e}")

            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        except Exception as e:
            logger.error(f"Error listing backups: {e}")

        return backups

    def cleanup_old_backups(self, keep_count: int = 5) -> int:
        """
        Remove old backups, keeping only the specified number

        Args:
            keep_count: Number of backups to keep

        Returns:
            Number of backups removed
        """
        try:
            backups = self.list_backups()

            if len(backups) <= keep_count:
                logger.info(f"Only {len(backups)} backups exist, no cleanup needed")
                return 0

            # Remove old backups
            removed_count = 0
            for backup in backups[keep_count:]:
                backup_path = Path(backup["path"])
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                    logger.info(f"Removed old backup: {backup_path}")
                    removed_count += 1

            logger.info(f"Cleanup completed: removed {removed_count} old backups")
            return removed_count

        except Exception as e:
            logger.error(f"Error during backup cleanup: {e}")
            return 0

    def _export_metadata(self, backup_dir: Path):
        """Export ChromaDB metadata to JSON format"""
        try:
            memory_manager = UserMemoryManager(str(self.chromadb_path))

            # Get all data from collection
            results = memory_manager.collection.get(limit=10000)  # Large limit to get all data

            metadata_export = {
                "export_timestamp": datetime.now().isoformat(),
                "collection_name": memory_manager.collection.name,
                "total_documents": len(results.get("documents", [])),
                "documents": results.get("documents", []),
                "metadatas": results.get("metadatas", []),
                "ids": results.get("ids", []),
            }

            with open(backup_dir / "metadata_export.json", "w") as f:
                json.dump(metadata_export, f, indent=2)

            logger.info(f"Exported {metadata_export['total_documents']} documents to metadata file")

        except Exception as e:
            logger.warning(f"Could not export metadata: {e}")

    def _get_directory_size(self, path: Path) -> int:
        """Get the total size of a directory in bytes"""
        total_size = 0
        try:
            for dirpath, _dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception as e:
            logger.warning(f"Could not calculate directory size: {e}")

        return total_size

    def create_consistent_backup(self, wait_for_operations=True):
        """Create backup after ensuring data consistency"""
        if wait_for_operations:
            logger.info("Waiting for active operations to complete before backup...")
            # Signal all managers to complete operations
            # This would be coordinated with other managers in a real implementation
            import time

            time.sleep(2)  # Give operations time to complete

        return self.create_backup(include_metadata=True)

    def verify_backup(self, backup_path: str) -> dict:
        """
        Verify the integrity of a backup

        Args:
            backup_path: Path to the backup directory

        Returns:
            Dictionary with verification results
        """
        verification_result = {"valid": False, "errors": [], "warnings": [], "info": {}}

        try:
            backup_dir = Path(backup_path)

            # Check if backup directory exists
            if not backup_dir.exists():
                verification_result["errors"].append("Backup directory does not exist")
                return verification_result

            # Check for backup info file
            backup_info_file = backup_dir / "backup_info.json"
            if not backup_info_file.exists():
                verification_result["errors"].append("Missing backup_info.json")
            else:
                try:
                    with open(backup_info_file) as f:
                        backup_info = json.load(f)
                    verification_result["info"]["backup_info"] = backup_info
                except Exception as e:
                    verification_result["errors"].append(f"Could not read backup_info.json: {e}")

            # Check for ChromaDB data
            chromadb_dir = backup_dir / "chromadb_data"
            if not chromadb_dir.exists():
                verification_result["errors"].append("Missing chromadb_data directory")
            else:
                # Check for essential ChromaDB files
                essential_files = ["chroma.sqlite3"]
                for file in essential_files:
                    if not (chromadb_dir / file).exists():
                        verification_result["warnings"].append(f"Missing ChromaDB file: {file}")

            # Check for metadata export
            metadata_file = backup_dir / "metadata_export.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                    verification_result["info"]["metadata_count"] = metadata.get(
                        "total_documents", 0
                    )
                except Exception as e:
                    verification_result["warnings"].append(f"Could not read metadata export: {e}")

            # Calculate backup size
            verification_result["info"]["size_bytes"] = self._get_directory_size(backup_dir)
            verification_result["info"]["size_mb"] = verification_result["info"]["size_bytes"] / (
                1024 * 1024
            )

            # Set validity
            verification_result["valid"] = len(verification_result["errors"]) == 0

        except Exception as e:
            verification_result["errors"].append(f"Verification failed: {e}")

        return verification_result
