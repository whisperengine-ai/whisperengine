#!/usr/bin/env python3
"""
Docker-based ChatGPT import script
Runs the import in an isolated container environment
"""

import subprocess
import argparse
import sys
from pathlib import Path


def run_docker_import(conversations_file: str, user_id: int, verbose: bool = False):
    """Run import using Docker container"""
    
    # Validate file exists
    file_path = Path(conversations_file).resolve()
    if not file_path.exists():
        print(f"❌ Error: File {conversations_file} not found")
        return 1
        
    # Build Docker command
    cmd = [
        'docker', 'run', '--rm',
        '-v', f'{file_path.parent}:/import_data',
        '-v', f'{Path.cwd()}/.env:/app/.env:ro',  # Mount env file
        '--network', 'host',  # For database access
        'whisperengine:latest',
        'python', 'scripts/chatgpt_import/import_chatgpt.py',
        '--file', f'/import_data/{file_path.name}',
        '--user-id', str(user_id)
    ]
    
    if verbose:
        cmd.append('--verbose')
        
    print(f"🐳 Running Docker import...")
    print(f"📁 File: {file_path}")
    print(f"👤 User ID: {user_id}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker import failed:")
        print(e.stderr)
        return 1
    except FileNotFoundError:
        print("❌ Docker not found. Please install Docker to use this import method.")
        return 1


def main():
    parser = argparse.ArgumentParser(description='Import ChatGPT conversations using Docker')
    parser.add_argument('--file', '-f', required=True, help='Path to conversations.json file')
    parser.add_argument('--user-id', '-u', type=int, required=True, help='Discord user ID')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    return run_docker_import(args.file, args.user_id, args.verbose)


if __name__ == '__main__':
    sys.exit(main())