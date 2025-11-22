import sys
import os
sys.path.append(os.getcwd())

try:
    from src_v2.discord.bot import WhisperBot
    from src_v2.memory.session import session_manager
    from src_v2.memory.manager import memory_manager
    from src_v2.memory.summarizer import SummaryManager
    print("Imports successful")
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)
