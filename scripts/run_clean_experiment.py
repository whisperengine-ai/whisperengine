#!/usr/bin/env python3
"""
Automated execution of clean Dotty × NotTaylor experimental matrix.
Addresses limitations from initial cross-model research with controlled design.

Usage:
    python scripts/run_clean_experiment.py --all
    python scripts/run_clean_experiment.py --test T1-A
    python scripts/run_clean_experiment.py --phase 1  # Just Mistral+Mistral tests
"""

import argparse
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


# ============================================================================
# EXPERIMENT CONFIGURATION
# ============================================================================

EXPERIMENT_DIR = Path("experiments/clean_experiment_oct2025")
RAW_CONVERSATIONS_DIR = EXPERIMENT_DIR / "raw_conversations"
METRICS_DIR = EXPERIMENT_DIR / "metrics"
ANALYSIS_DIR = EXPERIMENT_DIR / "analysis"

# Test matrix definition
TEST_MATRIX = {
    "T1-A": {"dotty": "mistral", "nottaylor": "mistral", "phase": 1, "rep": 1},
    "T1-B": {"dotty": "mistral", "nottaylor": "mistral", "phase": 1, "rep": 2},
    "T1-C": {"dotty": "mistral", "nottaylor": "mistral", "phase": 1, "rep": 3},
    "T2-A": {"dotty": "claude", "nottaylor": "claude", "phase": 2, "rep": 1},
    "T2-B": {"dotty": "claude", "nottaylor": "claude", "phase": 2, "rep": 2},
    "T2-C": {"dotty": "claude", "nottaylor": "claude", "phase": 2, "rep": 3},
    "T3-A": {"dotty": "mistral", "nottaylor": "claude", "phase": 3, "rep": 1},
    "T3-B": {"dotty": "mistral", "nottaylor": "claude", "phase": 3, "rep": 2},
    "T3-C": {"dotty": "mistral", "nottaylor": "claude", "phase": 3, "rep": 3},
    "T4-A": {"dotty": "claude", "nottaylor": "mistral", "phase": 4, "rep": 1},
    "T4-B": {"dotty": "claude", "nottaylor": "mistral", "phase": 4, "rep": 2},
    "T4-C": {"dotty": "claude", "nottaylor": "mistral", "phase": 4, "rep": 3},
}

# Model configurations (all at temperature 0.8)
MODEL_CONFIGS = {
    "mistral": {
        "model": "mistralai/mistral-medium-3.1",
        "temperature": "0.8",
    },
    "claude": {
        "model": "anthropic/claude-3.7-sonnet",
        "temperature": "0.8",
    },
}

# Bot configurations
BOTS = {
    "dotty": {
        "env_file": ".env.dotty",
        "port": 9098,
        "collection": "whisperengine_memory_dotty",
    },
    "nottaylor": {
        "env_file": ".env.nottaylor",
        "port": 9100,
        "collection": "whisperengine_memory_nottaylor",
    },
}

# Experiment parameters
TURNS = 10  # Reduced from 20 to limit escalation
TIMEOUT = 90
CONTINUATION = True


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def log(message: str, level: str = "INFO"):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


def run_command(cmd: List[str], cwd: str = None, check: bool = True, stream: bool = False) -> subprocess.CompletedProcess:
    """Run shell command and return result."""
    log(f"Running: {' '.join(cmd)}")
    
    if stream:
        # Stream output in real-time
        result = subprocess.run(cmd, cwd=cwd, check=False, text=True)
        return result
    else:
        # Capture output
        result = subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)
        if result.returncode != 0:
            log(f"Command failed: {result.stderr}", "ERROR")
        return result


def create_experiment_dirs():
    """Create experiment directory structure."""
    for directory in [RAW_CONVERSATIONS_DIR, METRICS_DIR, ANALYSIS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
        log(f"Created directory: {directory}")


def backup_env_files():
    """Backup current bot environment files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for bot_name, bot_config in BOTS.items():
        env_file = Path(bot_config["env_file"])
        if env_file.exists():
            backup_file = env_file.parent / f"{env_file.name}.backup_{timestamp}"
            backup_file.write_text(env_file.read_text())
            log(f"Backed up {env_file} to {backup_file}")


def update_env_file(bot_name: str, model_type: str):
    """Update bot environment file with model configuration."""
    env_file = Path(BOTS[bot_name]["env_file"])
    model_config = MODEL_CONFIGS[model_type]
    
    if not env_file.exists():
        log(f"Environment file {env_file} not found!", "ERROR")
        return False
    
    # Read current env file
    lines = env_file.read_text().splitlines()
    updated_lines = []
    
    model_updated = False
    temp_updated = False
    tool_calling_updated = False
    
    for line in lines:
        if line.startswith("LLM_CHAT_MODEL="):
            updated_lines.append(f'LLM_CHAT_MODEL={model_config["model"]}')
            model_updated = True
        elif line.startswith("TEMPERATURE="):
            updated_lines.append(f'TEMPERATURE={model_config["temperature"]}')
            temp_updated = True
        elif line.startswith("ENABLE_LLM_TOOL_CALLING="):
            updated_lines.append('ENABLE_LLM_TOOL_CALLING=false')
            tool_calling_updated = True
        else:
            updated_lines.append(line)
    
    # Add missing variables if not found
    if not model_updated:
        updated_lines.append(f'LLM_CHAT_MODEL={model_config["model"]}')
    if not temp_updated:
        updated_lines.append(f'TEMPERATURE={model_config["temperature"]}')
    if not tool_calling_updated:
        updated_lines.append('ENABLE_LLM_TOOL_CALLING=false')
    
    # Write updated file
    env_file.write_text("\n".join(updated_lines) + "\n")
    log(f"Updated {env_file}: {model_config['model']} @ temp {model_config['temperature']} (tool calling disabled)")
    return True


def clear_bot_memory(bot_name: str):
    """Clear and recreate bot's Qdrant collection for fresh slate."""
    collection_name = BOTS[bot_name]["collection"]
    
    try:
        client = QdrantClient(host="localhost", port=6334)
        
        # Delete existing collection
        try:
            client.delete_collection(collection_name)
            log(f"Deleted collection: {collection_name}")
        except Exception as e:
            log(f"Collection {collection_name} didn't exist: {e}", "WARN")
        
        # Recreate with same schema
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "content": VectorParams(size=384, distance=Distance.COSINE),
                "emotion": VectorParams(size=384, distance=Distance.COSINE),
                "semantic": VectorParams(size=384, distance=Distance.COSINE),
            }
        )
        log(f"Recreated collection: {collection_name} (fresh slate)")
        return True
        
    except Exception as e:
        log(f"Failed to clear memory for {bot_name}: {e}", "ERROR")
        return False


def stop_bot(bot_name: str):
    """Stop specific bot container."""
    log(f"Stopping {bot_name}...")
    run_command(["./multi-bot.sh", "stop-bot", bot_name], check=False)
    time.sleep(2)


def start_bot(bot_name: str):
    """Start specific bot container."""
    log(f"Starting {bot_name}...")
    run_command(["./multi-bot.sh", "bot", bot_name])
    time.sleep(5)  # Wait for container to be ready


def check_bot_health(bot_name: str) -> bool:
    """Check if bot is healthy and responding."""
    port = BOTS[bot_name]["port"]
    import requests
    
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        if response.status_code == 200:
            log(f"{bot_name} is healthy")
            return True
        else:
            log(f"{bot_name} health check failed: {response.status_code}", "WARN")
            return False
    except Exception as e:
        log(f"{bot_name} health check error: {e}", "ERROR")
        return False


def run_conversation(test_id: str, dotty_model: str, nottaylor_model: str) -> bool:
    """Execute bot conversation for specific test."""
    log(f"Running conversation: {test_id}")
    log(f"  Dotty: {dotty_model} @ 0.8")
    log(f"  NotTaylor: {nottaylor_model} @ 0.8")
    log(f"  Turns: {TURNS}, Timeout: {TIMEOUT}s")
    
    cmd = [
        "python", "scripts/bot_bridge_conversation.py",
        "dotty", "nottaylor",
        "--turns", str(TURNS),
        "--timeout", str(TIMEOUT),
    ]
    
    if CONTINUATION:
        cmd.append("--continuation")
    
    result = run_command(cmd, check=False, stream=True)
    
    if result.returncode == 0:
        log(f"✅ Conversation {test_id} completed successfully")
        return True
    else:
        log(f"❌ Conversation {test_id} failed", "ERROR")
        return False


def save_test_metadata(test_id: str, config: Dict):
    """Save test configuration and metadata."""
    metadata = {
        "test_id": test_id,
        "timestamp": datetime.now().isoformat(),
        "configuration": {
            "dotty_model": MODEL_CONFIGS[config["dotty"]]["model"],
            "dotty_temperature": MODEL_CONFIGS[config["dotty"]]["temperature"],
            "nottaylor_model": MODEL_CONFIGS[config["nottaylor"]]["model"],
            "nottaylor_temperature": MODEL_CONFIGS[config["nottaylor"]]["temperature"],
        },
        "parameters": {
            "turns": TURNS,
            "timeout": TIMEOUT,
            "continuation": CONTINUATION,
            "memory_state": "fresh",
        },
        "phase": config["phase"],
        "replication": config["rep"],
    }
    
    metadata_file = METRICS_DIR / f"{test_id}_metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2))
    log(f"Saved metadata: {metadata_file}")


# ============================================================================
# MAIN EXECUTION FUNCTIONS
# ============================================================================

def execute_single_test(test_id: str) -> bool:
    """Execute a single test from the matrix."""
    if test_id not in TEST_MATRIX:
        log(f"Invalid test ID: {test_id}", "ERROR")
        return False
    
    config = TEST_MATRIX[test_id]
    log(f"\n{'='*70}")
    log(f"EXECUTING TEST: {test_id}")
    log(f"  Phase: {config['phase']}, Replication: {config['rep']}")
    log(f"  Dotty: {config['dotty']}, NotTaylor: {config['nottaylor']}")
    log(f"{'='*70}\n")
    
    # Step 1: Clear memory for fresh slate
    log("Step 1: Clearing bot memories...")
    if not clear_bot_memory("dotty"):
        return False
    if not clear_bot_memory("nottaylor"):
        return False
    
    # Step 2: Stop bots
    log("Step 2: Stopping bots...")
    stop_bot("dotty")
    stop_bot("nottaylor")
    
    # Step 3: Update configurations
    log("Step 3: Updating bot configurations...")
    if not update_env_file("dotty", config["dotty"]):
        return False
    if not update_env_file("nottaylor", config["nottaylor"]):
        return False
    
    # Step 4: Start bots
    log("Step 4: Starting bots...")
    start_bot("dotty")
    start_bot("nottaylor")
    
    # Step 5: Wait for bots to be ready
    log("Step 5: Waiting for bots to be healthy...")
    time.sleep(10)  # Initial wait
    
    max_retries = 6
    for i in range(max_retries):
        if check_bot_health("dotty") and check_bot_health("nottaylor"):
            break
        if i < max_retries - 1:
            log(f"Bots not ready yet, waiting... (attempt {i+1}/{max_retries})")
            time.sleep(5)
    else:
        log("Bots failed to become healthy", "ERROR")
        return False
    
    # Step 6: Run conversation
    log("Step 6: Running conversation...")
    success = run_conversation(test_id, config["dotty"], config["nottaylor"])
    
    # Step 7: Save metadata
    if success:
        log("Step 7: Saving test metadata...")
        save_test_metadata(test_id, config)
    
    return success


def execute_phase(phase: int) -> Tuple[int, int]:
    """Execute all tests in a specific phase."""
    tests = [test_id for test_id, config in TEST_MATRIX.items() if config["phase"] == phase]
    
    log(f"\n{'='*70}")
    log(f"EXECUTING PHASE {phase}: {len(tests)} tests")
    log(f"Tests: {', '.join(tests)}")
    log(f"{'='*70}\n")
    
    successes = 0
    failures = 0
    
    for test_id in tests:
        if execute_single_test(test_id):
            successes += 1
        else:
            failures += 1
            log(f"Test {test_id} failed, continuing to next test...", "WARN")
    
    return successes, failures


def execute_all_tests() -> Tuple[int, int]:
    """Execute all 12 tests in the matrix."""
    log(f"\n{'='*70}")
    log(f"EXECUTING COMPLETE TEST MATRIX: {len(TEST_MATRIX)} tests")
    log(f"{'='*70}\n")
    
    successes = 0
    failures = 0
    
    # Execute by phase for logical grouping
    for phase in [1, 2, 3, 4]:
        phase_successes, phase_failures = execute_phase(phase)
        successes += phase_successes
        failures += phase_failures
    
    return successes, failures


def print_summary(successes: int, failures: int, start_time: datetime):
    """Print execution summary."""
    duration = datetime.now() - start_time
    total = successes + failures
    
    print(f"\n{'='*70}")
    print(f"EXPERIMENT EXECUTION SUMMARY")
    print(f"{'='*70}")
    print(f"Total Tests: {total}")
    print(f"✅ Successful: {successes} ({successes/total*100:.1f}%)")
    print(f"❌ Failed: {failures} ({failures/total*100:.1f}%)")
    print(f"Duration: {duration}")
    print(f"{'='*70}\n")
    
    if failures == 0:
        print("🎉 All tests completed successfully!")
    else:
        print(f"⚠️  {failures} test(s) failed. Check logs for details.")


def list_tests():
    """List all available tests."""
    print("\n" + "="*70)
    print("AVAILABLE TESTS")
    print("="*70)
    
    for phase in [1, 2, 3, 4]:
        tests = [(tid, cfg) for tid, cfg in TEST_MATRIX.items() if cfg["phase"] == phase]
        print(f"\nPhase {phase}:")
        for test_id, config in tests:
            print(f"  {test_id}: Dotty={config['dotty']}, NotTaylor={config['nottaylor']} (Rep {config['rep']})")
    
    print("\n" + "="*70 + "\n")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Automate clean Dotty × NotTaylor experimental matrix execution"
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Execute all 12 tests")
    group.add_argument("--phase", type=int, choices=[1, 2, 3, 4], help="Execute all tests in a phase")
    group.add_argument("--test", type=str, help="Execute a single test (e.g., T1-A)")
    group.add_argument("--list", action="store_true", help="List all available tests")
    
    parser.add_argument("--skip-backup", action="store_true", help="Skip backing up env files")
    
    args = parser.parse_args()
    
    # List tests and exit
    if args.list:
        list_tests()
        return
    
    # Setup
    log("Starting clean experiment automation")
    start_time = datetime.now()
    
    create_experiment_dirs()
    
    if not args.skip_backup:
        backup_env_files()
    
    # Execute based on mode
    if args.all:
        successes, failures = execute_all_tests()
    elif args.phase:
        successes, failures = execute_phase(args.phase)
    elif args.test:
        success = execute_single_test(args.test)
        successes = 1 if success else 0
        failures = 0 if success else 1
    
    # Summary
    print_summary(successes, failures, start_time)


if __name__ == "__main__":
    main()
