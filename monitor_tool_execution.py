#!/usr/bin/env python3
"""
Monitor Elena's logs for LLM tool execution to verify the fix worked
"""
import subprocess
import time
import sys

def monitor_tool_execution():
    """Monitor Elena's logs for LLM tool execution"""
    print("🔍 Monitoring Elena's logs for LLM tool execution...")
    print("💬 Send Elena a message like 'What's the latest news on AI?' in Discord to test")
    print("🕐 Monitoring for 2 minutes...")
    
    start_time = time.time()
    last_log_time = None
    
    while time.time() - start_time < 120:  # Monitor for 2 minutes
        try:
            # Get logs from last 30 seconds to avoid duplicates
            since_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - 30))
            
            result = subprocess.run([
                'docker', 'logs', 'whisperengine-elena-bot', 
                '--since', since_time
            ], capture_output=True, text=True, check=False)
            
            logs = result.stdout
            
            # Look for key indicators
            patterns = [
                "🔧 LLM TOOL CALLING: Using Phase 1 & 2 tools",
                "_generate_full_ai_response",
                "🔧 LLM TOOLS: Calling execute_llm_with_tools",
                "✅ LLM TOOLS: Generated response using sophisticated tools",
                "🌐",  # Web search emoji prefix
                "web search",
                "DuckDuckGo",
                "search results"
            ]
            
            # Check for new logs
            current_logs = logs.strip()
            if current_logs and current_logs != last_log_time:
                for pattern in patterns:
                    if pattern.lower() in logs.lower():
                        print(f"✅ DETECTED: {pattern}")
                        if pattern in ["🔧 LLM TOOL CALLING", "_generate_full_ai_response"]:
                            print("🎉 SUCCESS: Elena is now using the full AI system with tools!")
                        elif pattern == "🌐":
                            print("🎉 SUCCESS: Web search emoji prefix detected!")
                        elif pattern in ["web search", "DuckDuckGo"]:
                            print("🎉 SUCCESS: Web search functionality is working!")
                            
                last_log_time = current_logs
            
            # Check for any conversation activity
            if "message from" in logs.lower() or "generate" in logs.lower():
                print(f"📨 Activity detected at {time.strftime('%H:%M:%S')}")
            
            time.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            print(f"❌ Error monitoring logs: {e}")
            time.sleep(5)
    
    print("⏰ Monitoring complete. If you saw 'SUCCESS' messages above, the fix worked!")
    print("   If not, try sending Elena a message with web search keywords like:")
    print("   - 'What's the latest news on AI?'")
    print("   - 'Can you find recent information about...'")
    print("   - 'What are the current trends in...'")

if __name__ == "__main__":
    monitor_tool_execution()