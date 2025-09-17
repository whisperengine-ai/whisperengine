#!/usr/bin/env python3
"""
Lightweight migration runner for WhisperEngine

Features:
- Applies SQL migration files in numeric order from migrations/
- Tracks applied versions & checksums in schema_versions table
- Safe re-run (idempotent)
- Fails fast on checksum mismatch (ensures immutable history)

Usage:
  python scripts/db/run_migrations.py            # Apply all pending
  python scripts/db/run_migrations.py --status   # Show current status
  python scripts/db/run_migrations.py --fake 0002  # Mark a version applied without running

Environment variables used:
  POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD

Optional:
  RUN_DB_MIGRATIONS_ON_START=true  (can be checked in app startup)
"""

import os
import sys
import hashlib
import argparse
import psycopg2
from pathlib import Path
from datetime import datetime

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "migrations"


def log(msg: str):
    print(f"[migrate] {msg}")


def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "whisper_engine"),
            user=os.getenv("POSTGRES_USER", "bot_user"),
            password=os.getenv("POSTGRES_PASSWORD", "securepassword123"),
        )
        conn.autocommit = False
        return conn
    except Exception as e:
        log(f"ERROR: Could not connect to database: {e}")
        sys.exit(2)


def ensure_schema_versions_table(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_versions (
                component VARCHAR(100) NOT NULL DEFAULT 'core',
                version INT NOT NULL,
                checksum VARCHAR(128) NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                PRIMARY KEY (component, version)
            )
            """
        )
        conn.commit()


def load_applied_versions(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT version, checksum FROM schema_versions WHERE component='core' ORDER BY version")
        rows = cur.fetchall()
    return {int(v): c for v, c in rows}


def compute_checksum(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def parse_version(filename: str) -> int:
    # Expect filenames like 0001_baseline.sql
    prefix = filename.split("_")[0]
    try:
        return int(prefix)
    except ValueError:
        raise ValueError(f"Invalid migration filename (expected numeric prefix): {filename}")


def list_migrations():
    if not MIGRATIONS_DIR.exists():
        return []
    return sorted([p for p in MIGRATIONS_DIR.iterdir() if p.name.endswith('.sql')])


def apply_migration(conn, version: int, path: Path, checksum: str, fake: bool = False):
    description = path.name
    if fake:
        log(f"FAKE applying {path.name} (record only)")
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO schema_versions (component, version, checksum, description)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (component, version) DO NOTHING
                """,
                ("core", version, checksum, description),
            )
            conn.commit()
        return

    sql = path.read_text(encoding="utf-8")
    log(f"Applying migration {path.name}")
    with conn.cursor() as cur:
        try:
            cur.execute(sql)
            cur.execute(
                """
                INSERT INTO schema_versions (component, version, checksum, description)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (component, version) DO NOTHING
                """,
                ("core", version, checksum, description),
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            log(f"ERROR applying {path.name}: {e}")
            sys.exit(1)


def show_status(applied: dict[int, str], migrations: list[Path]):
    log("Migration Status:")
    if not migrations:
        log("No migrations found.")
        return
    for m in migrations:
        v = parse_version(m.name)
        checksum = compute_checksum(m)
        if v in applied:
            status = "APPLIED" if applied[v] == checksum else "CHECKSUM MISMATCH"  # drift detection
        else:
            status = "PENDING"
        log(f" {v:04d} | {m.name:30} | {status}")
    log("")


def main():
    parser = argparse.ArgumentParser(description="WhisperEngine migration runner")
    parser.add_argument("--status", action="store_true", help="Show migration status only")
    parser.add_argument("--fake", metavar="VERSION", help="Mark a migration version as applied without executing")
    args = parser.parse_args()

    migrations = list_migrations()
    conn = get_db_connection()
    ensure_schema_versions_table(conn)
    applied = load_applied_versions(conn)

    if args.status:
        show_status(applied, migrations)
        return

    if args.fake:
        try:
            fake_version = int(args.fake)
        except ValueError:
            log("--fake requires an integer version")
            sys.exit(1)
        # Find migration file
        match = [m for m in migrations if parse_version(m.name) == fake_version]
        if not match:
            log(f"No migration file found for version {fake_version}")
            sys.exit(1)
        checksum = compute_checksum(match[0])
        apply_migration(conn, fake_version, match[0], checksum, fake=True)
        log("Fake apply complete")
        return

    # Apply pending migrations
    pending = []
    for m in migrations:
        v = parse_version(m.name)
        checksum = compute_checksum(m)
        if v in applied:
            if applied[v] != checksum:
                log(f"FATAL: Checksum mismatch for version {v}. Refusing to continue.")
                log("       Fix by either: a) restoring original file, b) bumping version with new migration, or c) manual intervention.")
                sys.exit(1)
            continue
        pending.append((v, m, checksum))

    if not pending:
        log("No pending migrations. Database is up to date.")
        return

    for version, path, checksum in pending:
        apply_migration(conn, version, path, checksum)

    log("All pending migrations applied successfully.")


if __name__ == "__main__":
    main()
