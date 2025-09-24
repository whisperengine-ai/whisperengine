#!/usr/bin/env python3
"""
Check if the Universal Chat Orchestrator path decision is logged anywhere
"""
import subprocess
import sys

def check_orchestrator_decision():
    """Check logs for Universal Chat Orchestrator path decisions"""
    
    print("🔍 Checking Universal Chat Orchestrator decision logs...")
    
    try:
        # Get recent logs
        result = subprocess.run([
            'docker', 'logs', 'whisperengine-elena-bot', 
            '--since', '2024-09-18T22:50:00'
        ], capture_output=True, text=True, check=False)
        
        logs = result.stdout
        
        # Look for the specific condition checks
        patterns = [
            "bot_core",
            "memory_manager", 
            "_generate_full_ai_response",
            "_generate_basic_ai_response",
            "hasattr",
            "Check if we have access",
            "full WhisperEngine AI framework"
        ]
        
        print("🔍 Looking for Universal Chat decision patterns...")
        
        for pattern in patterns:
            matches = [line for line in logs.split('\n') if pattern.lower() in line.lower()]
            if matches:
                print(f"\n✅ Pattern '{pattern}' found:")
                for match in matches[-3:]:  # Show last 3 matches
                    print(f"   {match}")
            else:
                print(f"❌ Pattern '{pattern}' not found")
                
        # Check specifically for the bot_core condition
        print("\n🔍 Looking for bot_core condition evaluation...")
        bot_core_lines = [line for line in logs.split('\n') if 'bot_core' in line.lower()]
        memory_manager_lines = [line for line in logs.split('\n') if 'memory_manager' in line.lower()]
        
        print(f"Bot_core mentions: {len(bot_core_lines)}")
        print(f"Memory_manager mentions: {len(memory_manager_lines)}")
        
        if not bot_core_lines and not memory_manager_lines:
            print("🚨 ISSUE: No logging around bot_core condition - this means the path decision is silent!")
            print("   The Universal Chat Orchestrator is making a decision without logging it.")
            
        # Check for any error patterns
        error_patterns = ['error', 'exception', 'failed', 'fallback']
        print("\n🔍 Checking for error patterns...")
        for pattern in error_patterns:
            error_matches = [line for line in logs.split('\n') if pattern.lower() in line.lower() and '22:' in line]
            if error_matches:
                print(f"⚠️ Found {pattern} in recent logs:")
                for match in error_matches[-2:]:
                    print(f"   {match}")
        
    except Exception as e:
        print(f"❌ Error checking logs: {e}")

if __name__ == "__main__":
    check_orchestrator_decision()