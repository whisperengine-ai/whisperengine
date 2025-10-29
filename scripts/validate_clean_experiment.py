#!/usr/bin/env python3
"""
Pre-flight validation for clean experiment execution.
Checks all prerequisites before starting automation.
"""

import sys
from pathlib import Path
import subprocess
import requests
from qdrant_client import QdrantClient


def check_mark(passed: bool) -> str:
    return "✅" if passed else "❌"


def check_infrastructure():
    """Check if required infrastructure is running."""
    print("\n🔍 Checking Infrastructure...")
    
    checks = {
        "postgres": False,
        "qdrant": False,
    }
    
    # Check docker containers
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}"],
        capture_output=True, text=True
    )
    
    containers = result.stdout.splitlines()
    checks["postgres"] = any("postgres" in c for c in containers)
    checks["qdrant"] = any("qdrant" in c for c in containers)
    
    print(f"  {check_mark(checks['postgres'])} PostgreSQL")
    print(f"  {check_mark(checks['qdrant'])} Qdrant")
    
    return all(checks.values())


def check_bot_health():
    """Check if bots are accessible (don't need to be running yet)."""
    print("\n🤖 Checking Bot Ports...")
    
    ports = {
        "dotty": 9098,
        "nottaylor": 9100,
    }
    
    checks = {}
    for bot, port in ports.items():
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            checks[bot] = response.status_code == 200
        except:
            checks[bot] = None  # Bot might not be running yet (OK)
        
        status = "🟢 Running" if checks[bot] else "⚪ Not running (will start during test)"
        print(f"  {bot}: {status}")
    
    return True  # Bots don't need to be running yet


def check_qdrant_connection():
    """Check Qdrant connection and collections."""
    print("\n🗄️  Checking Qdrant Connection...")
    
    try:
        client = QdrantClient(host="localhost", port=6334)
        collections = client.get_collections().collections
        
        print(f"  ✅ Connected to Qdrant")
        print(f"  📊 Found {len(collections)} collections")
        
        # Check for bot collections
        collection_names = [c.name for c in collections]
        dotty_exists = "whisperengine_memory_dotty" in collection_names
        nottaylor_exists = "whisperengine_memory_nottaylor" in collection_names
        
        print(f"  {check_mark(dotty_exists)} whisperengine_memory_dotty")
        print(f"  {check_mark(nottaylor_exists)} whisperengine_memory_nottaylor")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Qdrant connection failed: {e}")
        return False


def check_env_files():
    """Check if bot environment files exist."""
    print("\n📄 Checking Environment Files...")
    
    files = {
        ".env.dotty": Path(".env.dotty"),
        ".env.nottaylor": Path(".env.nottaylor"),
    }
    
    checks = {}
    for name, path in files.items():
        checks[name] = path.exists()
        print(f"  {check_mark(checks[name])} {name}")
        
        if checks[name]:
            # Check for required keys
            content = path.read_text()
            has_model = "LLM_CHAT_MODEL" in content
            has_temp = "TEMPERATURE" in content
            
            if has_model and has_temp:
                print(f"     ✓ Has required variables")
            else:
                print(f"     ⚠️  Missing variables (will be added)")
    
    return all(checks.values())


def check_scripts():
    """Check if required scripts exist."""
    print("\n📜 Checking Scripts...")
    
    scripts = {
        "run_clean_experiment.py": Path("scripts/run_clean_experiment.py"),
        "bot_bridge_conversation.py": Path("scripts/bot_bridge_conversation.py"),
        "convert_bot_conversations_to_markdown.py": Path("scripts/convert_bot_conversations_to_markdown.py"),
        "analyze_clean_experiment.py": Path("scripts/analyze_clean_experiment.py"),
    }
    
    checks = {}
    for name, path in scripts.items():
        checks[name] = path.exists()
        print(f"  {check_mark(checks[name])} {name}")
    
    return all(checks.values())


def check_directories():
    """Check if required directories exist (will create if needed)."""
    print("\n📁 Checking Directories...")
    
    dirs = {
        "experiments/clean_experiment_oct2025": Path("experiments/clean_experiment_oct2025"),
        "logs/bot_conversations": Path("logs/bot_conversations"),
        "docs/bot_conversations": Path("docs/bot_conversations"),
    }
    
    for name, path in dirs.items():
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ Created {name}")
        else:
            print(f"  ✅ {name}")
    
    return True


def check_python_packages():
    """Check if required Python packages are installed."""
    print("\n📦 Checking Python Packages...")
    
    packages = ["qdrant_client", "requests", "pandas"]
    
    checks = {}
    for package in packages:
        try:
            __import__(package)
            checks[package] = True
        except ImportError:
            checks[package] = False
        
        print(f"  {check_mark(checks[package])} {package}")
    
    if not all(checks.values()):
        print("\n  💡 Install missing packages: pip install qdrant-client requests pandas")
    
    return all(checks.values())


def main():
    print("=" * 70)
    print("Clean Experiment Pre-Flight Validation")
    print("=" * 70)
    
    results = {
        "Infrastructure": check_infrastructure(),
        "Bot Ports": check_bot_health(),
        "Qdrant": check_qdrant_connection(),
        "Environment Files": check_env_files(),
        "Scripts": check_scripts(),
        "Directories": check_directories(),
        "Python Packages": check_python_packages(),
    }
    
    print("\n" + "=" * 70)
    print("Validation Summary")
    print("=" * 70)
    
    for check, passed in results.items():
        print(f"  {check_mark(passed)} {check}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 70)
    
    if all_passed:
        print("✅ All checks passed! Ready to run experiment.")
        print("\nRun: ./scripts/run_clean_experiment.sh")
        sys.exit(0)
    else:
        print("⚠️  Some checks failed. Please fix issues before running experiment.")
        print("\nTo start infrastructure: ./multi-bot.sh infra")
        sys.exit(1)


if __name__ == "__main__":
    main()
