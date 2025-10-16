#!/usr/bin/env python3
"""
WhisperEngine Migration Validator

This script validates the completeness and correctness of Alembic migrations.
Run this before deploying to ensure migration chain integrity.

Usage:
    python scripts/validate_migrations.py
    
    # With detailed output
    python scripts/validate_migrations.py --verbose
    
    # Fix common issues
    python scripts/validate_migrations.py --fix
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse


class MigrationValidator:
    """Validates Alembic migration chain integrity."""
    
    def __init__(self, migrations_dir: Path, verbose: bool = False):
        self.migrations_dir = migrations_dir
        self.verbose = verbose
        self.migrations: Dict[str, Dict] = {}
        self.issues: List[str] = []
        self.warnings: List[str] = []
        
    def load_migrations(self) -> None:
        """Load all migration files and extract metadata."""
        for file in sorted(self.migrations_dir.glob('*.py')):
            if file.name == '__init__.py':
                continue
                
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract revision and down_revision
            rev_match = re.search(r"revision[:\s]*=?\s*['\"]([^'\"]+)['\"]", content)
            down_match = re.search(
                r"down_revision[:\s]*=?\s*(?:Union\[str, None\]\s*=\s*)?['\"]?([^'\"]+|None)['\"]?",
                content
            )
            
            if rev_match:
                revision = rev_match.group(1)
                down_revision = down_match.group(1) if down_match and down_match.group(1) != 'None' else None
                
                # Extract description from docstring
                doc_match = re.search(r'"""([^"]+)"""', content)
                description = doc_match.group(1).strip().split('\n')[0] if doc_match else "No description"
                
                self.migrations[revision] = {
                    'file': file.name,
                    'down_revision': down_revision,
                    'description': description,
                    'path': file
                }
                
        if self.verbose:
            print(f"📦 Loaded {len(self.migrations)} migrations")
    
    def check_init_file(self) -> bool:
        """Check if __init__.py exists in migrations directory."""
        init_file = self.migrations_dir / '__init__.py'
        if not init_file.exists():
            self.issues.append("❌ Missing __init__.py in alembic/versions/")
            return False
        
        if self.verbose:
            print("✅ __init__.py exists")
        return True
    
    def check_compiled_files(self) -> Tuple[List[Path], List[Path]]:
        """Check for stale .pyc files."""
        pyc_files = list(self.migrations_dir.glob('*.pyc'))
        pycache_files = list(self.migrations_dir.glob('__pycache__/*'))
        
        if pyc_files or pycache_files:
            total = len(pyc_files) + len(pycache_files)
            self.warnings.append(f"⚠️  Found {total} .pyc files (can cause stale migration issues)")
            if self.verbose:
                print(f"⚠️  {total} compiled Python files found")
        else:
            if self.verbose:
                print("✅ No stale .pyc files")
        
        return pyc_files, pycache_files
    
    def check_duplicate_revisions(self) -> bool:
        """Check for duplicate revision IDs."""
        seen = {}
        duplicates = []
        
        for rev_id, migration in self.migrations.items():
            if rev_id in seen:
                duplicates.append((rev_id, migration['file'], seen[rev_id]))
            else:
                seen[rev_id] = migration['file']
        
        if duplicates:
            for rev_id, file1, file2 in duplicates:
                self.issues.append(f"❌ DUPLICATE revision ID: {rev_id} in {file1} and {file2}")
            return False
        
        if self.verbose:
            print(f"✅ All {len(self.migrations)} revision IDs are unique")
        return True
    
    def check_broken_chain(self) -> Tuple[Optional[str], List[str], Dict[str, List[str]]]:
        """Check for broken migration chain and branches."""
        from collections import defaultdict
        
        down_revisions = defaultdict(list)
        base_revision = None
        
        for rev_id, migration in self.migrations.items():
            down_rev = migration['down_revision']
            if down_rev is None:
                base_revision = rev_id
            else:
                down_revisions[down_rev].append(rev_id)
        
        # Check for branches (multiple migrations with same down_revision)
        branches = {dr: revs for dr, revs in down_revisions.items() if len(revs) > 1}
        
        if branches:
            for down_rev, branch_revs in branches.items():
                self.issues.append(
                    f"❌ BRANCH: Multiple migrations depend on '{down_rev}': {branch_revs}"
                )
        else:
            if self.verbose:
                print("✅ No branching detected (linear migration chain)")
        
        # Check for orphaned migrations
        all_rev_ids = set(self.migrations.keys())
        referenced_rev_ids = set()
        
        for migration in self.migrations.values():
            if migration['down_revision']:
                referenced_rev_ids.add(migration['down_revision'])
        
        # Orphans are migrations that are not referenced and are not the base
        orphaned = all_rev_ids - referenced_rev_ids - {base_revision} if base_revision else all_rev_ids - referenced_rev_ids
        
        if orphaned:
            for orphan in orphaned:
                migration = self.migrations[orphan]
                self.issues.append(
                    f"❌ ORPHANED migration: {orphan} (down_revision={migration['down_revision']}) in {migration['file']}"
                )
        else:
            if self.verbose:
                print("✅ No orphaned migrations")
        
        return base_revision, list(orphaned), branches
    
    def check_missing_references(self) -> List[str]:
        """Check for references to non-existent migrations."""
        all_rev_ids = set(self.migrations.keys())
        missing_refs = []
        
        for rev_id, migration in self.migrations.items():
            down_rev = migration['down_revision']
            if down_rev and down_rev not in all_rev_ids:
                missing_refs.append(down_rev)
                self.issues.append(
                    f"❌ BROKEN LINK: {rev_id} references non-existent down_revision '{down_rev}'"
                )
        
        if not missing_refs and self.verbose:
            print("✅ All down_revision references are valid")
        
        return missing_refs
    
    def build_chain(self) -> List[Tuple[str, str]]:
        """Build the complete migration chain from base to head."""
        # Find base (migration with down_revision = None)
        base = None
        for rev_id, migration in self.migrations.items():
            if migration['down_revision'] is None:
                base = rev_id
                break
        
        if not base:
            return []
        
        # Build chain
        chain = [(base, self.migrations[base]['file'])]
        current = base
        visited = {base}
        
        while True:
            # Find next migration (where down_revision == current)
            next_migrations = [
                rev_id for rev_id, migration in self.migrations.items()
                if migration['down_revision'] == current and rev_id not in visited
            ]
            
            if not next_migrations:
                break
            
            if len(next_migrations) > 1:
                # Branch detected - this is handled by check_broken_chain
                break
            
            next_rev = next_migrations[0]
            chain.append((next_rev, self.migrations[next_rev]['file']))
            visited.add(next_rev)
            current = next_rev
        
        return chain
    
    def print_summary(self, chain: List[Tuple[str, str]]) -> bool:
        """Print validation summary."""
        print("\n📊 Summary:")
        print(f"   Total migrations: {len(self.migrations)}")
        print(f"   Chain length: {len(chain)}")
        print(f"   Warnings: {len(self.warnings)}")
        print(f"   Critical issues: {len(self.issues)}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if self.issues:
            print(f"\n❌ CRITICAL ISSUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"   {issue}")
            return False
        
        print("\n✅ ALL CHECKS PASSED - Migrations are complete and valid!")
        return True
    
    def print_chain(self, chain: List[Tuple[str, str]]) -> None:
        """Print the migration chain."""
        if not chain:
            print("\n⚠️  Unable to build migration chain")
            return
        
        print(f"\n🔗 Migration Chain ({len(chain)} migrations):")
        print("=" * 80)
        for i, (rev, _) in enumerate(chain, 1):
            desc = self.migrations[rev]['description'][:60]
            print(f"{i:2d}. {rev:30s} → {desc}")
    
    def fix_compiled_files(self, pyc_files: List[Path], pycache_files: List[Path]) -> None:
        """Remove compiled Python files."""
        removed = 0
        for file in pyc_files + pycache_files:
            try:
                file.unlink()
                removed += 1
                if self.verbose:
                    print(f"   Removed: {file}")
            except OSError as e:
                print(f"   ⚠️  Could not remove {file}: {e}")
        
        if removed > 0:
            print(f"✅ Removed {removed} compiled files")
    
    def validate(self, fix: bool = False) -> bool:
        """Run all validation checks."""
        print("\n📋 MIGRATION COMPLETENESS ANALYSIS")
        print("=" * 80)
        
        self.load_migrations()
        
        # Check 1: __init__.py
        self.check_init_file()
        
        # Check 2: Compiled files
        pyc_files, pycache_files = self.check_compiled_files()
        if fix and (pyc_files or pycache_files):
            print("\n🔧 Fixing compiled files...")
            self.fix_compiled_files(pyc_files, pycache_files)
        
        # Check 3: Duplicate revisions
        self.check_duplicate_revisions()
        
        # Check 4: Broken chain and branches
        self.check_broken_chain()
        
        # Check 5: Missing references
        self.check_missing_references()
        
        # Build and print chain
        chain = self.build_chain()
        if self.verbose:
            self.print_chain(chain)
        
        # Print summary
        valid = self.print_summary(chain)
        
        return valid


def main():
    parser = argparse.ArgumentParser(
        description="Validate WhisperEngine Alembic migration chain integrity"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed output'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Attempt to fix common issues (remove .pyc files)'
    )
    parser.add_argument(
        '--migrations-dir',
        type=Path,
        default=Path('alembic/versions'),
        help='Path to migrations directory (default: alembic/versions)'
    )
    
    args = parser.parse_args()
    
    if not args.migrations_dir.exists():
        print(f"❌ Migrations directory not found: {args.migrations_dir}")
        print("   Run this script from the WhisperEngine root directory")
        sys.exit(1)
    
    validator = MigrationValidator(args.migrations_dir, args.verbose)
    valid = validator.validate(fix=args.fix)
    
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
