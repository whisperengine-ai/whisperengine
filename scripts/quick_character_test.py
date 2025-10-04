#!/usr/bin/env python3
"""
Quick Character Test Runner
Simplified version of automated character tests for daily validation.
"""

import asyncio
import aiohttp
import time
from typing import Tuple

class QuickCharacterTest:
    """Quick test runner for basic character validation."""
    
    def __init__(self):
        # Only test bots that have the new external chat API
        self.bots = {
            "elena": {"port": 9091, "emoji": "🌊", "test": "Tell me about marine conservation"},
            "dotty": {"port": 9098, "emoji": "🍸", "test": "What drinks do you serve at the Lim speakeasy?"}
        }
        
        # Other bots don't have chat API yet (will be added as they're updated)
        self.bots_without_api = {
            "marcus": {"port": 9092, "emoji": "🤖"},
            "ryan": {"port": 9093, "emoji": "🎮"},
            "dream": {"port": 9094, "emoji": "🌙"},
            "gabriel": {"port": 9095, "emoji": "🎩"},
            "sophia": {"port": 9096, "emoji": "💼"},
            "jake": {"port": 9097, "emoji": "📸"},
            "aethys": {"port": 3007, "emoji": "✨"}
        }

    async def quick_test_bot(self, bot_name: str) -> Tuple[bool, str, float]:
        """Quick test of a single bot."""
        if bot_name not in self.bots:
            return False, f"Unknown bot: {bot_name}", 0.0
            
        bot = self.bots[bot_name]
        start_time = time.time()
        
        try:
            # Health check
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:{bot['port']}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status != 200:
                        return False, "Health check failed", time.time() - start_time
                
                # Quick chat test
                payload = {"message": bot["test"], "user_id": f"quick_test_{int(time.time())}"}
                async with session.post(f"http://localhost:{bot['port']}/api/chat", json=payload, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    execution_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            return True, f"Response received ({len(data.get('response', ''))} chars)", execution_time
                        else:
                            return False, f"API error: {data.get('error', 'Unknown')}", execution_time
                    else:
                        return False, f"HTTP {response.status}", execution_time
                        
        except asyncio.TimeoutError:
            return False, "Timeout", time.time() - start_time
        except (aiohttp.ClientError, OSError) as e:
            return False, str(e), time.time() - start_time

    async def test_all_bots(self):
        """Test all bots quickly."""
        print("🤖 Quick Character Test Runner")
        print("=" * 40)
        print(f"Testing bots with external chat API: {', '.join(self.bots.keys())}")
        print(f"Bots without API yet: {', '.join(self.bots_without_api.keys())}")
        print("-" * 40)
        
        results = {}
        tasks = []
        
        # Run all tests concurrently for speed
        for bot_name in self.bots.keys():
            tasks.append(self.quick_test_bot(bot_name))
            
        test_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, bot_name in enumerate(self.bots.keys()):
            bot = self.bots[bot_name]
            
            result = test_results[i]
            if isinstance(result, BaseException):
                success, message, timing = False, str(result), 0.0
            elif isinstance(result, tuple) and len(result) == 3:
                success, message, timing = result
            else:
                success, message, timing = False, "Invalid response format", 0.0
            
            status = "✅" if success else "❌"
            print(f"{status} {bot['emoji']} {bot_name:<8} - {message:<30} ({timing:.2f}s)")
            results[bot_name] = success
            
        print("-" * 40)
        passed = sum(results.values())
        total = len(results)
        available_total = len(self.bots) + len(self.bots_without_api)
        print(f"Result: {passed}/{total} bots with API responding ({(passed/total)*100:.0f}%)")
        print(f"Overall: {passed}/{available_total} total bots have working chat API ({(passed/available_total)*100:.0f}%)")
        
        return results

async def main():
    """Main entry point."""
    tester = QuickCharacterTest()
    await tester.test_all_bots()

if __name__ == "__main__":
    asyncio.run(main())