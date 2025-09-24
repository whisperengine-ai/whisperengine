#!/usr/bin/env python3
"""
Test the web search fix by monitoring Elena's logs for the next message
"""
import subprocess
import time
import sys

def test_web_search_fix():
    """Monitor Elena for web search functionality"""
    
    print("🔍 Elena web search fix has been applied!")
    print("🚀 The issue was: LLM tool arguments were JSON strings, not parsed dictionaries")
    print("✅ Fix applied: Added JSON parsing in _process_tool_calls method")
    print()
    print("📱 Now send Elena a message in Discord to test:")
    print("   💭 'What's the latest news about AI?'")
    print("   💭 'Can you search for recent developments in machine learning?'")
    print("   💭 Or use commands: !search_news AI developments")
    print()
    print("🔍 Expected behavior:")
    print("   ✅ Elena should detect web search keywords")
    print("   ✅ No more 'str object has no attribute get' error")
    print("   ✅ Web search should execute successfully")
    print("   ✅ Response should include 🌐 emoji prefix")
    print("   ✅ Response should contain current information from web search")
    print()
    print("📋 Monitoring Elena's logs for the next 2 minutes...")
    
    start_time = time.time()
    last_check = 0
    
    while time.time() - start_time < 120:  # 2 minutes
        try:
            # Get logs from last 30 seconds to see new activity
            since_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - 30))
            
            result = subprocess.run([
                'docker', 'logs', 'whisperengine-elena-bot',
                '--since', since_time
            ], capture_output=True, text=True, check=False)
            
            logs = result.stdout
            
            if logs.strip():
                current_time = int(time.time())
                if current_time > last_check + 5:  # Only log every 5 seconds to avoid spam
                    
                    # Check for key success indicators
                    if "🔍 Web search needed detected" in logs:
                        print("✅ WEB SEARCH DETECTED!")
                    
                    if "'str' object has no attribute 'get'" in logs:
                        print("❌ STILL HAS ERROR - the fix didn't work")
                    
                    if "🔍 Executing web search tool" in logs:
                        print("✅ WEB SEARCH EXECUTING!")
                    
                    if "🌐 Added web search indicator" in logs:
                        print("🎉 SUCCESS: Web search worked and added 🌐 emoji!")
                    
                    if "search_current_events" in logs and "success" in logs.lower():
                        print("✅ search_current_events tool executed successfully!")
                    
                    if "Generated response of" in logs:
                        print("📝 Elena generated a response")
                        
                    last_check = current_time
            
            time.sleep(3)
            
        except Exception as e:
            print(f"❌ Error monitoring: {e}")
            break
    
    print("\n⏰ Monitoring complete!")
    print("   If you saw '✅ SUCCESS' messages above, the web search is working!")
    print("   If not, try sending another web search message to Elena.")

if __name__ == "__main__":
    test_web_search_fix()