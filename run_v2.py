import asyncio
import sys
import os
from pathlib import Path

# Ensure the current directory is in the python path
sys.path.append(os.getcwd())

def setup_environment():
    """
    Sets up the environment variables before importing the main application.
    This allows selecting the bot/character via command line argument.
    """
    # Suppress HuggingFace Tokenizers warning
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    # Check if a bot name was provided as an argument
    if len(sys.argv) > 1:
        bot_name = sys.argv[1]
        print(f"🤖 Setting DISCORD_BOT_NAME to '{bot_name}' from command line argument.")
        os.environ["DISCORD_BOT_NAME"] = bot_name
    
    # Check if DISCORD_BOT_NAME is set
    if not os.getenv("DISCORD_BOT_NAME"):
        # Check if .env exists and has DISCORD_BOT_NAME
        env_path = Path(".env")
        has_bot_name_in_env = False
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("DISCORD_BOT_NAME="):
                        has_bot_name_in_env = True
                        break
        
        if not has_bot_name_in_env:
            print("⚠️  WARNING: DISCORD_BOT_NAME is not set in environment or .env file.")
            print("   Usage: python run_v2.py <bot_name>")
            print("   Example: python run_v2.py elena")
            
            # List available bot configs
            env_files = list(Path(".").glob(".env.*"))
            if env_files:
                print("\n   Available bot configurations:")
                for f in env_files:
                    if f.name != ".env.example" and f.name != ".env.template":
                        print(f"   - {f.name.replace('.env.', '')}")
            print("")

# Setup environment BEFORE importing src_v2.main
setup_environment()

from src_v2.main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Critical error: {e}", file=sys.stderr)
        sys.exit(1)
