#!/usr/bin/env python3
"""
Monitor Elena for two-phase LLM calling fix
"""
import subprocess
import time

def monitor_two_phase_fix():
    """Monitor Elena for the two-phase LLM fix"""
    
    print("🔍 Elena two-phase LLM fix has been applied!")
    print("🚀 The issue was: LLM was not making a second call with tool results")
    print("✅ Fix applied: Added second LLM call after tool execution")
    print()
    print("📱 Send Elena a web search message in Discord:")
    print("   💭 'What's the latest news about AI?'")
    print("   💭 'Can you search for recent developments in machine learning?'")
    print()
    print("🔍 Expected behavior:")
    print("   ✅ First LLM call makes tool calls")
    print("   ✅ Tools execute and return results")
    print("   ✅ Second LLM call processes results into response")
    print("   ✅ Elena responds with comprehensive information and 🌐 emoji")
    print()
    print("📋 Monitoring Elena's logs...")
    
    last_log_time = 0
    
    for _ in range(24):  # Monitor for 2 minutes (5 second intervals)
        try:
            since_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - 30))
            
            result = subprocess.run([
                'docker', 'logs', 'whisperengine-elena-bot',
                '--since', since_time
            ], capture_output=True, text=True, check=False)
            
            logs = result.stdout
            
            if logs.strip():
                current_time = int(time.time())
                if current_time > last_log_time + 3:
                    
                    # Check for key indicators
                    if "🔍 Web search needed detected" in logs:
                        print("✅ WEB SEARCH DETECTED!")
                    
                    if "🔄 Making second LLM call" in logs:
                        print("🎉 SUCCESS: Second LLM call initiated!")
                    
                    if "tool results" in logs:
                        print("✅ Tool results being processed")
                    
                    if "✅ Second LLM call generated" in logs:
                        print("🎉 SUCCESS: Second LLM call generated response!")
                    
                    if "🌐 Added web search indicator" in logs:
                        print("🎉 SUCCESS: Web search emoji added!")
                    
                    if "Generated response of" in logs and "4 characters" not in logs:
                        print("📝 Elena generated a proper response!")
                        
                    last_log_time = current_time
            
            time.sleep(5)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            break
    
    print("\n⏰ Monitoring complete!")

if __name__ == "__main__":
    monitor_two_phase_fix()