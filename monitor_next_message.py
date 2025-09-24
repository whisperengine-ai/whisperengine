#!/usr/bin/env python3
"""
Monitor Elena's next message to see if web search works
"""
import subprocess
import time

def monitor_next_message():
    """Monitor Elena for web search functionality"""
    
    print("🔍 Elena is ready with all fixes applied:")
    print("   ✅ JSON parsing fix")
    print("   ✅ Two-phase LLM calling") 
    print("   ✅ Correct method name (generate_chat_completion)")
    print()
    print("📱 Send Elena a web search message in Discord:")
    print("   💭 'What's the latest news about AI?'")
    print("   💭 'Can you search for recent developments in machine learning?'")
    print("   💭 '!search_news AI breakthroughs'")
    print()
    print("📋 Monitoring for the next message...")
    
    # Get current timestamp to only monitor new messages
    start_time = time.time()
    last_log_check = start_time
    
    while time.time() - start_time < 300:  # Monitor for 5 minutes
        try:
            # Get recent logs
            since_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(last_log_check))
            
            result = subprocess.run([
                'docker', 'logs', 'whisperengine-elena-bot',
                '--since', since_time
            ], capture_output=True, text=True, check=False)
            
            logs = result.stdout
            
            if logs.strip():
                print("📨 New activity detected!")
                
                # Key success indicators
                if "🔍 Web search needed detected" in logs:
                    print("✅ SUCCESS: Web search detection working!")
                
                if "🔄 Making second LLM call" in logs:
                    print("🎉 SUCCESS: Second LLM call initiated!")
                
                if "✅ Second LLM call generated" in logs:
                    print("🎉 SUCCESS: Second LLM call completed!")
                    
                if "🌐 Added web search indicator" in logs:
                    print("🎉 SUCCESS: Web search emoji added!")
                
                if "Generated response of" in logs:
                    # Look for response size
                    lines = logs.split('\n')
                    for line in lines:
                        if "Generated response of" in line:
                            if "4 characters" in line:
                                print("❌ Still generating 'None' responses (4 chars)")
                            else:
                                print("✅ Generated proper response!")
                                print(f"   📏 {line.split('Generated response of')[1].split(' ')[1]} characters")
                
                # Check for errors
                if "Second LLM call failed" in logs:
                    print("❌ Second LLM call failed - checking error...")
                    error_lines = [line for line in logs.split('\n') if 'ERROR' in line and 'Second LLM call failed' in line]
                    for error in error_lines:
                        print(f"   🔍 Error: {error}")
                
                last_log_check = time.time()
            
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            break
    
    print("\n⏰ Monitoring complete!")
    print("   If you see SUCCESS messages above, web search is working!")
    print("   If not, there may be additional issues to debug.")

if __name__ == "__main__":
    monitor_next_message()