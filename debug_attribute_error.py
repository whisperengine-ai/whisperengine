#!/usr/bin/env python3
"""
Quick test to see exact error location
"""
import os
import sys
import traceback

# Add src to path
sys.path.insert(0, 'src')

# Set environment
os.environ['ENV_MODE'] = 'development'

from src.memory.memory_manager import UserMemoryManager

try:
    print("Creating UserMemoryManager...")
    manager = UserMemoryManager('test_user_123')
    
    print(f"use_external_embeddings: {manager.use_external_embeddings}")
    print(f"add_documents_with_embeddings: {manager.add_documents_with_embeddings}")
    
    # This should fail
    print("Attempting to call add_documents_with_embeddings...")
    manager.add_documents_with_embeddings()
    
except Exception as e:
    print(f"Error: {e}")
    print("Traceback:")
    traceback.print_exc()