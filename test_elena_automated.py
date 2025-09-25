#!/usr/bin/env python3
"""
Elena Automated Personality & Emotional Intelligence Test
Tests the core features that matter: personality and emotional flow
Runs locally with localhost configs to avoid container dependency
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add src to path
sys.path.append('src')

# Set up localhost environment for local testing
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5433'  # Multi-bot port
os.environ['REDIS_HOST'] = 'localhost'
os.environ['REDIS_PORT'] = '6380'     # Multi-bot port
os.environ['QDRANT_HOST'] = 'localhost'
os.environ['QDRANT_PORT'] = '6334'    # Multi-bot port


class ElenaTestSuite:
    """Automated test suite for Elena's personality and functionality"""
    
    def __init__(self):
        self.test_results = {}
        self.container_name = "whisperengine-elena-bot"
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    async def run_full_test_suite(self) -> Dict:
        """Run complete Elena test suite"""
        self.logger.info("🧪 ELENA AUTOMATED TEST SUITE")
        self.logger.info(f"📅 {datetime.now().isoformat()}")
        self.logger.info("="*60)
        
        # Test categories in order of dependency
        test_categories = [
            ("infrastructure", self.test_infrastructure),
            ("character_system", self.test_character_system), 
            ("container_health", self.test_container_health),
            ("personality_integration", self.test_personality_integration),
            ("conversation_flow", self.test_conversation_flow),
            ("memory_persistence", self.test_memory_persistence),
            ("regression_detection", self.test_regression_detection)
        ]
        
        overall_success = True
        
        for category_name, test_function in test_categories:
            self.logger.info(f"\n🔍 TESTING: {category_name.upper().replace('_', ' ')}")
            
            try:
                success, results = await test_function()
                self.test_results[category_name] = {
                    "success": success,
                    "results": results,
                    "timestamp": datetime.now().isoformat()
                }
                
                status = "✅ PASS" if success else "❌ FAIL"
                self.logger.info(f"{status} {category_name}")
                
                if not success:
                    overall_success = False
                    self.logger.error(f"Failed tests in {category_name}: {results.get('failures', [])}")
                    
            except Exception as e:
                self.logger.error(f"❌ ERROR in {category_name}: {e}")
                self.test_results[category_name] = {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                overall_success = False
        
        # Generate comprehensive report
        await self.generate_test_report(overall_success)
        return self.test_results
    
    async def test_infrastructure(self) -> Tuple[bool, Dict]:
        """Test basic infrastructure requirements"""
        results = {"tests": [], "failures": []}
        
        # Test 1: Character file exists and is valid
        elena_file = "characters/examples/elena-rodriguez.json"
        if os.path.exists(elena_file):
            try:
                with open(elena_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Validate structure
                required_fields = ["identity", "personality", "communication_style"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    results["failures"].append(f"Missing character fields: {missing_fields}")
                else:
                    results["tests"].append("character_file_structure")
            except Exception as e:
                results["failures"].append(f"Character file invalid: {e}")
        else:
            results["failures"].append(f"Character file missing: {elena_file}")
        
        # Test 2: Docker environment accessible
        try:
            result = subprocess.run(
                ["docker", "ps"], 
                capture_output=True, 
                text=True, 
                check=True, 
                timeout=10
            )
            results["tests"].append("docker_accessible")
        except Exception as e:
            results["failures"].append(f"Docker not accessible: {e}")
        
        # Test 3: Multi-bot script exists
        if os.path.exists("./multi-bot.sh"):
            results["tests"].append("multi_bot_script_exists")
        else:
            results["failures"].append("Multi-bot script missing")
        
        success = len(results["failures"]) == 0
        return success, results
    
    async def test_character_system(self) -> Tuple[bool, Dict]:
        """Test CDL character system integrity"""
        results = {"tests": [], "failures": [], "personality_traits": {}}
        
        elena_file = "characters/examples/elena-rodriguez.json"
        
        try:
            with open(elena_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Test personality traits
            content = json.dumps(data, indent=2)
            
            personality_checks = {
                "spanish_language": ["español", "Spanish", "bilingual", "¡"],
                "marine_biology": ["marine", "ocean", "biologist", "La Jolla"],
                "warmth_personality": ["warm", "enthusiastic", "passionate"],
                "emoji_usage": ["emoji", "expressive", "visual"]
            }
            
            for trait, indicators in personality_checks.items():
                found = [ind for ind in indicators if ind.lower() in content.lower()]
                results["personality_traits"][trait] = {
                    "found_indicators": found,
                    "indicator_count": len(found),
                    "present": len(found) > 0
                }
                
                if len(found) > 0:
                    results["tests"].append(f"personality_{trait}")
                else:
                    results["failures"].append(f"Missing personality trait: {trait}")
            
            # Test character identity
            if "identity" in data:
                identity = data["identity"]
                if identity.get("name") == "Elena Rodriguez":
                    results["tests"].append("character_identity")
                else:
                    results["failures"].append("Incorrect character name")
            
        except Exception as e:
            results["failures"].append(f"Character system test failed: {e}")
        
        success = len(results["failures"]) == 0
        return success, results
    
    async def test_container_health(self) -> Tuple[bool, Dict]:
        """Test Elena container health and initialization"""
        results = {"tests": [], "failures": [], "container_info": {}}
        
        try:
            # Check if container is running
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={self.container_name}", "--format", "{{.Status}}"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            
            if result.stdout.strip():
                status = result.stdout.strip()
                results["container_info"]["status"] = status
                
                if "Up" in status and "healthy" in status:
                    results["tests"].append("container_running_healthy")
                elif "Up" in status:
                    results["tests"].append("container_running")
                    results["failures"].append("Container not healthy")
                else:
                    results["failures"].append(f"Container not running: {status}")
            else:
                results["failures"].append("Elena container not found")
            
            # Test container logs for initialization success
            log_result = subprocess.run(
                ["docker", "logs", self.container_name, "--tail", "50"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if log_result.returncode == 0:
                logs = log_result.stdout
                
                # Check for critical initialization markers
                init_checks = {
                    "discord_ready": ["bot initialization complete", "Discord bot ready"],
                    "cdl_system": ["CDL", "Character Definition Language", "character system initialized"],
                    "memory_system": ["memory", "vector", "qdrant"],
                    "llm_integration": ["LLM", "OpenRouter", "client configured"]
                }
                
                for check_name, patterns in init_checks.items():
                    if any(pattern.lower() in logs.lower() for pattern in patterns):
                        results["tests"].append(f"init_{check_name}")
                    else:
                        results["failures"].append(f"Initialization check failed: {check_name}")
                
                # Check for critical errors
                error_patterns = ["ERROR", "Exception", "Failed", "rate limit"]
                errors_found = []
                for pattern in error_patterns:
                    if pattern.lower() in logs.lower():
                        errors_found.append(pattern)
                
                if errors_found:
                    results["failures"].append(f"Errors in logs: {errors_found}")
                else:
                    results["tests"].append("no_critical_errors")
                    
            else:
                results["failures"].append("Could not retrieve container logs")
        
        except Exception as e:
            results["failures"].append(f"Container health check failed: {e}")
        
        success = len(results["failures"]) == 0
        return success, results
    
    async def test_personality_integration(self) -> Tuple[bool, Dict]:
        """Test Elena's personality integration in logs"""
        results = {"tests": [], "failures": [], "personality_evidence": {}}
        
        try:
            # Get recent logs to look for personality evidence
            log_result = subprocess.run(
                ["docker", "logs", self.container_name, "--tail", "100"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if log_result.returncode == 0:
                logs = log_result.stdout
                
                # Look for personality evidence in actual bot messages
                personality_evidence = {
                    "spanish_phrases": [r"¡[^!]*!", r"qué", r"Sí", r"mi amigo", r"español"],
                    "marine_references": [r"ocean", r"marine", r"sea", r"bubble bath", r"water"],
                    "warm_personality": [r"wonderful", r"missed you", r"dulce", r"alegría", r"perfecto"],
                    "elena_identity": [r"Elena Rodriguez", r"marine biologist"],
                    "emojis": [r"🌊", r"😊", r"💙", r"☀️", r"🔬"]
                }
                
                total_evidence = 0
                for category, patterns in personality_evidence.items():
                    matches = []
                    for pattern in patterns:
                        import re
                        found = re.findall(pattern, logs, re.IGNORECASE)
                        matches.extend(found)
                    
                    unique_matches = list(set(matches))
                    results["personality_evidence"][category] = {
                        "matches": unique_matches,
                        "count": len(unique_matches)
                    }
                    
                    if unique_matches:
                        results["tests"].append(f"personality_{category}")
                        total_evidence += len(unique_matches)
                    else:
                        results["failures"].append(f"No evidence of {category}")
                
                # Overall personality integration test
                if total_evidence >= 3:  # At least 3 pieces of personality evidence
                    results["tests"].append("personality_integration_active")
                else:
                    results["failures"].append("Insufficient personality evidence in logs")
                    
            else:
                results["failures"].append("Could not retrieve logs for personality analysis")
        
        except Exception as e:
            results["failures"].append(f"Personality integration test failed: {e}")
        
        success = len(results["failures"]) == 0
        return success, results
    
    async def test_conversation_flow(self) -> Tuple[bool, Dict]:
        """Test conversation flow indicators"""
        results = {"tests": [], "failures": [], "conversation_metrics": {}}
        
        try:
            # Look for conversation flow evidence in logs
            log_result = subprocess.run(
                ["docker", "logs", self.container_name, "--tail", "200"],
                capture_output=True,
                text=True,
                timeout=20
            )
            
            if log_result.returncode == 0:
                logs = log_result.stdout
                
                # Count conversation indicators
                conversation_indicators = {
                    "message_processing": ["on_message called", "processing message"],
                    "response_generation": ["generating response", "response sent"],
                    "cdl_integration": ["CDL", "character-aware prompt"],
                    "memory_retrieval": ["retrieving memories", "memory retrieval"],
                    "cache_usage": ["cache", "caching"]
                }
                
                conversation_active = False
                for indicator_type, patterns in conversation_indicators.items():
                    count = sum(logs.lower().count(pattern.lower()) for pattern in patterns)
                    results["conversation_metrics"][indicator_type] = count
                    
                    if count > 0:
                        results["tests"].append(f"conversation_{indicator_type}")
                        conversation_active = True
                
                if conversation_active:
                    results["tests"].append("conversation_flow_active")
                else:
                    results["failures"].append("No evidence of active conversation flow")
            
        except Exception as e:
            results["failures"].append(f"Conversation flow test failed: {e}")
        
        success = len(results["failures"]) == 0
        return success, results
    
    async def test_memory_persistence(self) -> Tuple[bool, Dict]:
        """Test memory system functionality"""
        results = {"tests": [], "failures": []}
        
        # This would require more sophisticated testing
        # For now, check for memory-related log entries
        try:
            log_result = subprocess.run(
                ["docker", "logs", self.container_name, "--tail", "100"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if log_result.returncode == 0:
                logs = log_result.stdout
                
                memory_indicators = ["memory", "store", "retrieve", "qdrant", "vector"]
                memory_evidence = sum(logs.lower().count(ind.lower()) for ind in memory_indicators)
                
                if memory_evidence > 0:
                    results["tests"].append("memory_system_active")
                else:
                    results["failures"].append("No memory system activity detected")
        
        except Exception as e:
            results["failures"].append(f"Memory persistence test failed: {e}")
        
        success = len(results["failures"]) == 0
        return success, results
    
    async def test_regression_detection(self) -> Tuple[bool, Dict]:
        """Test for known regression patterns"""
        results = {"tests": [], "failures": [], "regressions": []}
        
        try:
            log_result = subprocess.run(
                ["docker", "logs", self.container_name, "--tail", "200"],
                capture_output=True,
                text=True,
                timeout=20
            )
            
            if log_result.returncode == 0:
                logs = log_result.stdout
                
                # Known regression patterns
                regression_patterns = {
                    "none_responses": ["None", "response is None"],
                    "generic_responses": ["I'm sorry, I encountered an error"],
                    "missing_character": ["character file not found", "CDL not available"],
                    "rate_limiting": ["rate limited", "429"],
                    "connection_errors": ["connection failed", "timeout"]
                }
                
                for regression_name, patterns in regression_patterns.items():
                    if any(pattern.lower() in logs.lower() for pattern in patterns):
                        results["regressions"].append(regression_name)
                        results["failures"].append(f"Regression detected: {regression_name}")
                
                if not results["regressions"]:
                    results["tests"].append("no_known_regressions")
        
        except Exception as e:
            results["failures"].append(f"Regression detection failed: {e}")
        
        success = len(results["failures"]) == 0
        return success, results
    
    async def generate_test_report(self, overall_success: bool):
        """Generate comprehensive test report"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📋 ELENA AUTOMATED TEST REPORT")
        self.logger.info("="*60)
        
        total_tests = 0
        total_failures = 0
        
        for category, data in self.test_results.items():
            if "results" in data:
                tests_count = len(data["results"].get("tests", []))
                failures_count = len(data["results"].get("failures", []))
                total_tests += tests_count
                total_failures += failures_count
                
                status = "✅" if data["success"] else "❌"
                self.logger.info(f"\n{status} {category.upper()}: {tests_count} passed, {failures_count} failed")
                
                if failures_count > 0:
                    for failure in data["results"]["failures"]:
                        self.logger.warning(f"  ❌ {failure}")
        
        success_rate = ((total_tests) / (total_tests + total_failures) * 100) if (total_tests + total_failures) > 0 else 0
        
        self.logger.info(f"\n🎯 OVERALL RESULT: {total_tests} tests passed, {total_failures} failures")
        self.logger.info(f"📊 SUCCESS RATE: {success_rate:.1f}%")
        
        if overall_success:
            self.logger.info("🎉 ALL TESTS PASSED - Elena is ready for development!")
        else:
            self.logger.error("🚨 TESTS FAILED - Address issues before making changes!")
        
        # Save detailed report
        report_file = f"elena_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        self.logger.info(f"\n📄 Detailed report saved: {report_file}")


async def main():
    """Run Elena automated test suite"""
    test_suite = ElenaTestSuite()
    results = await test_suite.run_full_test_suite()
    
    # Return appropriate exit code
    overall_success = all(result.get("success", False) for result in results.values())
    return 0 if overall_success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)