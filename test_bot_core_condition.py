#!/usr/bin/env python3
"""
Test the bot_core condition that's preventing LLM tool execution
"""
import asyncio
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

async def test_bot_core_condition():
    """Test what's happening with the bot_core condition"""
    print("🔍 Testing bot_core condition that's preventing LLM tool execution...")
    
    # This test would need to connect to the running container
    # For now, let's check the logs more carefully
    
    # Check if Elena is using basic vs full AI response
    import subprocess
    
    # Look for the specific log messages that would indicate which path was taken
    try:
        result = subprocess.run([
            'docker', 'logs', 'whisperengine-elena-bot', 
            '--since', '2024-09-18T22:50:00'
        ], capture_output=True, text=True, timeout=30)
        
        logs = result.stdout
        
        print("🔍 Checking for AI response generation logs...")
        
        # Look for full vs basic AI response indicators
        if "_generate_full_ai_response" in logs:
            print("✅ Found _generate_full_ai_response calls")
        else:
            print("❌ NO _generate_full_ai_response calls found")
            
        if "_generate_basic_ai_response" in logs:
            print("⚠️ Found _generate_basic_ai_response calls - this is the fallback path!")
        else:
            print("✅ No basic AI response fallback")
            
        if "bot_core" in logs and "memory_manager" in logs:
            print("🔍 Found bot_core and memory_manager references")
        else:
            print("❌ Missing bot_core or memory_manager references")
            
        # Count how many times each method appears
        full_count = logs.count("_generate_full_ai_response")
        basic_count = logs.count("_generate_basic_ai_response")
        
        print(f"📊 Full AI response calls: {full_count}")
        print(f"📊 Basic AI response calls: {basic_count}")
        
        if basic_count > 0 and full_count == 0:
            print("🚨 ISSUE FOUND: Elena is falling back to basic AI response instead of using full AI with tools!")
            print("   This means either:")
            print("   1. self.bot_core is None")
            print("   2. self.bot_core.memory_manager doesn't exist") 
            print("   3. hasattr(self.bot_core, 'memory_manager') is returning False")
            
    except Exception as e:
        print(f"❌ Error checking logs: {e}")

if __name__ == "__main__":
    asyncio.run(test_bot_core_condition())