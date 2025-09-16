#!/usr/bin/env python3
"""
Build-time Model Downloader for WhisperEngine
Downloads all required models during the build process for offline bundling
"""

import os
import subprocess
import sys
from pathlib import Path


def run_model_download():
    """Run the model download script as part of build process"""

    # Ensure we're in the right directory
    if not Path("download_models.py").exists():
        sys.exit(1)

    # Set environment variables for offline mode
    env = os.environ.copy()
    env.update(
        {
            "HF_DATASETS_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "SENTENCE_TRANSFORMERS_HOME": "./models/.cache",
        }
    )

    try:
        # Download models first
        result = subprocess.run(
            [sys.executable, "download_models.py"], capture_output=True, text=True, env=env
        )

        if result.returncode != 0:
            sys.exit(1)

        # Now run the actual build
        build_command = sys.argv[1:] if len(sys.argv) > 1 else ["pyinstaller", "whisperengine.spec"]

        result = subprocess.run(build_command, env=env)

        if result.returncode == 0:
            pass
        else:
            sys.exit(1)

    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    run_model_download()
