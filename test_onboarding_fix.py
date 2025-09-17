#!/usr/bin/env python3
"""
Test onboarding detection
"""
import sys
import os
sys.path.insert(0, '.')

from src.utils.onboarding_manager import FirstRunDetector

detector = FirstRunDetector()
print(f"Project root: {detector.project_root}")
print(f"Setup marker file: {detector.setup_markers_file}")
print(f"Setup marker exists: {detector.setup_markers_file.exists()}")
print(f"Is first run: {detector.is_first_run()}")

# Test config validation
config_path = detector.project_root / ".env"
print(f"Config path: {config_path}")
print(f"Config exists: {config_path.exists()}")
if config_path.exists():
    print(f"Config is valid: {detector._has_valid_configuration(config_path)}")