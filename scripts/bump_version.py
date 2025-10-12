#!/usr/bin/env python3
"""
WhisperEngine Version Management Script

Automatically bumps version numbers across all files and creates git tags.

Usage:
    python scripts/bump_version.py patch    # 1.0.8 → 1.0.9
    python scripts/bump_version.py minor    # 1.0.8 → 1.1.0
    python scripts/bump_version.py major    # 1.0.8 → 2.0.0
    python scripts/bump_version.py 1.2.3    # Set specific version

Features:
    - Updates pyproject.toml
    - Updates src/__init__.py
    - Creates git commit
    - Creates git tag
    - Optionally pushes to origin
"""

import re
import sys
import subprocess
from pathlib import Path
from typing import Tuple, Optional

# Project root directory
ROOT_DIR = Path(__file__).parent.parent

# Files that contain version numbers
VERSION_FILES = {
    "pyproject.toml": r'version = "([0-9]+\.[0-9]+\.[0-9]+)"',
    "src/__init__.py": r'__version__ = "([0-9]+\.[0-9]+\.[0-9]+)"',
    "VERSION": r'^([0-9]+\.[0-9]+\.[0-9]+)$',
}


class VersionManager:
    """Manages version bumping across multiple files"""
    
    def __init__(self):
        self.current_version = self._get_current_version()
        print(f"📌 Current version: {self.current_version}")
    
    def _get_current_version(self) -> str:
        """Get current version from pyproject.toml"""
        pyproject_path = ROOT_DIR / "pyproject.toml"
        content = pyproject_path.read_text()
        match = re.search(VERSION_FILES["pyproject.toml"], content)
        if not match:
            raise ValueError("Could not find version in pyproject.toml")
        return match.group(1)
    
    def _parse_version(self, version: str) -> Tuple[int, int, int]:
        """Parse version string into (major, minor, patch) tuple"""
        parts = version.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version}")
        return tuple(map(int, parts))
    
    def bump(self, bump_type: str) -> str:
        """
        Bump version based on type
        
        Args:
            bump_type: 'major', 'minor', 'patch', or specific version like '1.2.3'
        
        Returns:
            New version string
        """
        major, minor, patch = self._parse_version(self.current_version)
        
        if bump_type == "major":
            new_version = f"{major + 1}.0.0"
        elif bump_type == "minor":
            new_version = f"{major}.{minor + 1}.0"
        elif bump_type == "patch":
            new_version = f"{major}.{minor}.{patch + 1}"
        else:
            # Assume it's a specific version
            try:
                self._parse_version(bump_type)  # Validate format
                new_version = bump_type
            except ValueError:
                raise ValueError(f"Invalid bump type: {bump_type}. Use 'major', 'minor', 'patch', or specific version like '1.2.3'")
        
        return new_version
    
    def update_files(self, new_version: str) -> None:
        """Update version in all tracked files"""
        print(f"\n🔄 Updating version {self.current_version} → {new_version}")
        
        for file_path, pattern in VERSION_FILES.items():
            full_path = ROOT_DIR / file_path
            if not full_path.exists():
                print(f"⚠️  File not found: {file_path}")
                continue
            
            content = full_path.read_text()
            new_content = re.sub(
                pattern,
                lambda m: m.group(0).replace(m.group(1), new_version),
                content
            )
            
            if content != new_content:
                full_path.write_text(new_content)
                print(f"✅ Updated {file_path}")
            else:
                print(f"⚠️  No changes needed in {file_path}")
    
    def git_commit_and_tag(self, new_version: str, push: bool = False) -> None:
        """Create git commit and tag for version bump"""
        print(f"\n📝 Creating git commit and tag...")
        
        # Stage version files
        files_to_stage = [str(ROOT_DIR / f) for f in VERSION_FILES.keys()]
        subprocess.run(["git", "add"] + files_to_stage, check=True)
        
        # Create commit
        commit_message = f"chore: bump version {self.current_version} → {new_version}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        print(f"✅ Created commit: {commit_message}")
        
        # Create annotated tag
        tag_name = f"v{new_version}"
        tag_message = f"WhisperEngine {tag_name}\n\nRelease of version {new_version}"
        subprocess.run(["git", "tag", "-a", tag_name, "-m", tag_message], check=True)
        print(f"✅ Created tag: {tag_name}")
        
        # Push if requested
        if push:
            branch = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            
            print(f"\n🚀 Pushing to origin...")
            subprocess.run(["git", "push", "origin", branch], check=True)
            subprocess.run(["git", "push", "origin", tag_name], check=True)
            print(f"✅ Pushed branch and tag to origin")
        else:
            print(f"\n💡 To push changes later, run:")
            print(f"   git push origin $(git branch --show-current)")
            print(f"   git push origin {tag_name}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("❌ Error: Version bump type required")
        print("\nUsage:")
        print("  python scripts/bump_version.py patch    # 1.0.8 → 1.0.9")
        print("  python scripts/bump_version.py minor    # 1.0.8 → 1.1.0")
        print("  python scripts/bump_version.py major    # 1.0.8 → 2.0.0")
        print("  python scripts/bump_version.py 1.2.3    # Set specific version")
        print("\nOptions:")
        print("  --push    Automatically push commit and tag to origin")
        sys.exit(1)
    
    bump_type = sys.argv[1]
    push = "--push" in sys.argv
    
    # Check git status
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )
    if result.stdout.strip() and "--force" not in sys.argv:
        print("❌ Error: Working directory is not clean")
        print("   Commit or stash changes before bumping version")
        print("   Or use --force to bypass this check")
        sys.exit(1)
    
    try:
        manager = VersionManager()
        new_version = manager.bump(bump_type)
        
        # Confirm
        print(f"\n📦 Version bump summary:")
        print(f"   Current: {manager.current_version}")
        print(f"   New:     {new_version}")
        print(f"   Push:    {'Yes' if push else 'No (manual push required)'}")
        
        response = input("\n❓ Proceed with version bump? [y/N]: ")
        if response.lower() != 'y':
            print("❌ Version bump cancelled")
            sys.exit(0)
        
        # Execute
        manager.update_files(new_version)
        manager.git_commit_and_tag(new_version, push=push)
        
        print(f"\n✅ Version bump complete!")
        print(f"\n📋 Next steps:")
        print(f"   1. Review changes: git show")
        print(f"   2. Build Docker: ./push-to-dockerhub.sh whisperengine v{new_version}")
        print(f"   3. Create GitHub release: https://github.com/whisperengine-ai/whisperengine/releases/new")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
