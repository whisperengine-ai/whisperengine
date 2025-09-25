#!/usr/bin/env python3
"""
Elena Feature Verification Script
Tests all claimed features of Elena Rodriguez to verify actual vs expected functionality
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append('src')

from env_manager import load_environment

# Test categories
TESTS = {
    "character_system": [
        "CDL character file exists",
        "Character parser can load Elena",
        "Spanish phrases are defined",
        "Marine biology personality traits exist",
        "Emoji preferences are configured"
    ],
    "memory_system": [
        "Vector memory is operational", 
        "Can store conversations",
        "Can retrieve relevant memories",
        "Emotion context is captured",
        "User preferences are remembered"
    ],
    "llm_integration": [
        "LLM client is configured",
        "OpenAI/OpenRouter connection works",
        "CDL prompt integration functions",
        "Response generation completes",
        "Character personality shows in responses"
    ],
    "discord_integration": [
        "Bot is connected to Discord",
        "Can receive DMs",
        "Can send responses", 
        "Rate limiting is handled",
        "Message caching works"
    ]
}

class ElenaFeatureVerifier:
    def __init__(self):
        self.results = {}
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    async def run_all_tests(self):
        """Run comprehensive feature verification"""
        self.logger.info("🔍 Starting Elena Feature Verification")
        self.logger.info(f"📅 Test Date: {datetime.now().isoformat()}")
        
        # Load environment
        load_environment()
        
        for category, tests in TESTS.items():
            self.logger.info(f"\n📋 Testing Category: {category.upper()}")
            self.results[category] = {}
            
            for test in tests:
                try:
                    result = await self._run_test(category, test)
                    self.results[category][test] = result
                    status = "✅ PASS" if result["passed"] else "❌ FAIL"
                    self.logger.info(f"  {status}: {test}")
                    if not result["passed"]:
                        self.logger.warning(f"    Reason: {result.get('error', 'Unknown')}")
                except Exception as e:
                    self.results[category][test] = {
                        "passed": False,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    self.logger.error(f"  ❌ ERROR: {test} - {e}")
        
        # Generate report
        await self._generate_report()
    
    async def _run_test(self, category, test_name):
        """Run individual test"""
        result = {
            "passed": False,
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if category == "character_system":
                result = await self._test_character_system(test_name)
            elif category == "memory_system":
                result = await self._test_memory_system(test_name)
            elif category == "llm_integration":
                result = await self._test_llm_integration(test_name)
            elif category == "discord_integration":
                result = await self._test_discord_integration(test_name)
                
        except Exception as e:
            result["error"] = str(e)
            
        result["timestamp"] = datetime.now().isoformat()
        return result
    
    async def _test_character_system(self, test_name):
        """Test character system features"""
        result = {"passed": False, "details": {}}
        
        if test_name == "CDL character file exists":
            elena_file = "characters/examples/elena-rodriguez.json"
            if os.path.exists(elena_file):
                with open(elena_file, 'r') as f:
                    data = json.load(f)
                result["passed"] = True
                result["details"] = {
                    "file_path": elena_file,
                    "file_size": os.path.getsize(elena_file),
                    "has_identity": "identity" in data,
                    "has_personality": "personality" in data,
                    "character_name": data.get("identity", {}).get("name", "Unknown")
                }
            else:
                result["error"] = f"Character file not found: {elena_file}"
                
        elif test_name == "Character parser can load Elena":
            try:
                from src.characters.cdl.parser import load_character
                character = load_character("characters/examples/elena-rodriguez.json")
                result["passed"] = True
                result["details"] = {
                    "character_loaded": character is not None,
                    "name": character.identity.name if character else "None",
                    "occupation": getattr(character.identity, 'occupation', 'Unknown') if character else "None"
                }
            except Exception as e:
                result["error"] = f"Character loading failed: {e}"
                
        elif test_name == "Spanish phrases are defined":
            elena_file = "characters/examples/elena-rodriguez.json"
            if os.path.exists(elena_file):
                with open(elena_file, 'r') as f:
                    content = f.read()
                spanish_phrases = ["¡", "español", "Spanish", "bilingual", "Sí"]
                found_phrases = [phrase for phrase in spanish_phrases if phrase in content]
                result["passed"] = len(found_phrases) > 0
                result["details"] = {
                    "found_spanish_indicators": found_phrases,
                    "content_sample": content[:200] + "..." if len(content) > 200 else content
                }
            else:
                result["error"] = "Character file not found"
        
        # Add more character tests...
        
        return result
    
    async def _test_memory_system(self, test_name):
        """Test memory system features"""
        result = {"passed": False, "details": {}}
        
        if test_name == "Vector memory is operational":
            try:
                from src.memory.memory_protocol import create_memory_manager
                memory_manager = create_memory_manager(memory_type="vector")
                result["passed"] = memory_manager is not None
                result["details"] = {
                    "memory_type": type(memory_manager).__name__,
                    "has_store_method": hasattr(memory_manager, 'store_conversation'),
                    "has_retrieve_method": hasattr(memory_manager, 'retrieve_relevant_memories')
                }
            except Exception as e:
                result["error"] = f"Memory manager creation failed: {e}"
        
        # Add more memory tests...
        
        return result
    
    async def _test_llm_integration(self, test_name):
        """Test LLM integration features"""
        result = {"passed": False, "details": {}}
        
        if test_name == "LLM client is configured":
            try:
                from src.llm.llm_protocol import create_llm_client
                llm_client = create_llm_client(llm_client_type="openrouter")
                result["passed"] = llm_client is not None
                result["details"] = {
                    "client_type": type(llm_client).__name__,
                    "has_generate_method": hasattr(llm_client, 'generate_response'),
                    "api_key_configured": bool(os.getenv("OPENROUTER_API_KEY"))
                }
            except Exception as e:
                result["error"] = f"LLM client creation failed: {e}"
        
        # Add more LLM tests...
        
        return result
    
    async def _test_discord_integration(self, test_name):
        """Test Discord integration features"""
        result = {"passed": False, "details": {}}
        
        if test_name == "Bot is connected to Discord":
            # This would require actual Discord connection testing
            # For now, just check configuration
            discord_token = os.getenv("DISCORD_BOT_TOKEN")
            bot_name = os.getenv("DISCORD_BOT_NAME")
            result["passed"] = bool(discord_token and bot_name)
            result["details"] = {
                "token_configured": bool(discord_token),
                "bot_name": bot_name,
                "character_file_env": os.getenv("CHARACTER_FILE_PATH")
            }
            if not result["passed"]:
                result["error"] = "Discord token or bot name not configured"
        
        # Add more Discord tests...
        
        return result
    
    async def _generate_report(self):
        """Generate comprehensive test report"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📊 ELENA FEATURE VERIFICATION REPORT")
        self.logger.info("="*60)
        
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.results.items():
            category_passed = sum(1 for test in tests.values() if test["passed"])
            category_total = len(tests)
            total_tests += category_total
            passed_tests += category_passed
            
            self.logger.info(f"\n📋 {category.upper()}: {category_passed}/{category_total}")
            
            for test_name, result in tests.items():
                status = "✅" if result["passed"] else "❌"
                self.logger.info(f"  {status} {test_name}")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        self.logger.info(f"\n🎯 OVERALL: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        
        # Save detailed report
        report_file = f"elena_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        self.logger.info(f"📄 Detailed report saved to: {report_file}")
        
        # Recommendations
        self.logger.info("\n💡 RECOMMENDATIONS:")
        if success_rate == 100:
            self.logger.info("  🎉 All tests passed! Elena is fully operational.")
        elif success_rate >= 80:
            self.logger.info("  ✨ Most features working. Address failing tests before changes.")
        elif success_rate >= 60:
            self.logger.info("  ⚠️  Some core features failing. Investigate before deployment.")
        else:
            self.logger.info("  🚨 Major issues detected. Full system review needed.")

async def main():
    """Main verification function"""
    verifier = ElenaFeatureVerifier()
    await verifier.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())