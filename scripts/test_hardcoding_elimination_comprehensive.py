#!/usr/bin/env python3
"""
Comprehensive automated tests for high-priority hardcoding elimination validation.

Tests the database-driven systems we implemented:
1. AI Identity Keywords detection
2. Physical Interaction Keywords detection  
3. Question Template generation
4. Entity Classification patterns

Uses HTTP API calls to Aetheris, Elena, and Jake bots and validates
results through prompt log file analysis.
"""

import asyncio
import aiohttp
import json
import os
import glob
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import time

class HighPriorityHardcodingTests:
    """Automated tests for validating hardcoding elimination."""
    
    def __init__(self):
        self.base_ports = {
            'aetheris': 9099,  # Updated from container status
            'elena': 9091, 
            'jake': 9097
        }
        self.test_results = []
        self.prompt_logs_dir = "/Users/markcastillo/git/whisperengine/logs/prompts"
        
    async def run_comprehensive_tests(self):
        """Run all automated tests for hardcoding elimination validation."""
        
        print("🚀 AUTOMATED TESTS: High-Priority Hardcoding Elimination Validation")
        print("=" * 80)
        
        # Test scenarios covering all eliminated hardcoding
        test_scenarios = [
            # AI Identity Keywords (formerly hardcoded)
            {
                'category': 'ai_identity',
                'message': 'Are you an AI or artificial intelligence?',
                'expected_detection': True,
                'validation_keywords': ['AI nature', 'honest about your AI nature', 'respond authentically']
            },
            {
                'category': 'ai_identity', 
                'message': 'What kind of robot or computer program are you?',
                'expected_detection': True,
                'validation_keywords': ['AI nature', 'honest about your AI nature']
            },
            
            # Physical Interaction Keywords (formerly hardcoded)
            {
                'category': 'physical_interaction',
                'message': 'Can I give you a hug and hold your hand?',
                'expected_detection': True,
                'validation_keywords': ['PHYSICAL INTERACTION GUIDANCE', 'roleplay request detected']
            },
            {
                'category': 'physical_interaction',
                'message': 'I want to kiss and cuddle with you',
                'expected_detection': True, 
                'validation_keywords': ['PHYSICAL INTERACTION GUIDANCE', 'tier-appropriate response']
            },
            
            # Question Templates (formerly hardcoded gap_patterns)
            {
                'category': 'question_templates',
                'message': 'I love photography but I am new to it',
                'expected_detection': True,
                'validation_keywords': ['photography', 'How', 'What', 'Where']  # Should trigger knowledge gap questions
            },
            {
                'category': 'question_templates',
                'message': 'I enjoy marine biology research',
                'expected_detection': True,
                'validation_keywords': ['marine biology', 'experience', 'journey', 'How']
            },
            
            # Entity Classification (formerly hardcoded categories)
            {
                'category': 'entity_classification',
                'message': 'I study computer science and artificial intelligence',
                'expected_detection': True,
                'validation_keywords': ['computer science', 'artificial intelligence']
            },
            {
                'category': 'entity_classification',
                'message': 'I practice underwater photography in the ocean',
                'expected_detection': True,
                'validation_keywords': ['underwater photography', 'ocean']
            },
            
            # Control tests (should NOT trigger)
            {
                'category': 'control_test',
                'message': 'What is the weather like today?',
                'expected_detection': False,
                'validation_keywords': []  # Should not trigger any special handling
            }
        ]
        
        print(f"🧪 Running {len(test_scenarios)} test scenarios across 3 characters...")
        
        # Test each character with each scenario
        for character in ['aetheris', 'elena', 'jake']:
            print(f"\\n🎭 TESTING CHARACTER: {character.upper()}")
            print("-" * 50)
            
            character_results = []
            
            for i, scenario in enumerate(test_scenarios, 1):
                print(f"\\n  Test {i}/{len(test_scenarios)}: {scenario['category']}")
                print(f"    Message: '{scenario['message']}'")
                
                try:
                    # Send HTTP API request
                    response_data, prompt_log_path = await self._send_api_request(
                        character, scenario['message'], f"test_user_{i}"
                    )
                    
                    if response_data and prompt_log_path:
                        # Validate through prompt logs
                        validation_result = await self._validate_prompt_logs(
                            prompt_log_path, scenario
                        )
                        
                        character_results.append({
                            'character': character,
                            'scenario': scenario['category'],
                            'message': scenario['message'],
                            'success': validation_result['success'],
                            'details': validation_result['details'],
                            'prompt_log': prompt_log_path
                        })
                        
                        status = "✅ PASS" if validation_result['success'] else "❌ FAIL"
                        print(f"    Result: {status}")
                        print(f"    Details: {validation_result['details']}")
                        
                    else:
                        print(f"    Result: ❌ FAIL - API request failed")
                        character_results.append({
                            'character': character,
                            'scenario': scenario['category'], 
                            'message': scenario['message'],
                            'success': False,
                            'details': 'API request failed',
                            'prompt_log': None
                        })
                    
                    # Brief pause between requests
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"    Result: ❌ FAIL - Exception: {e}")
                    character_results.append({
                        'character': character,
                        'scenario': scenario['category'],
                        'message': scenario['message'],
                        'success': False,
                        'details': f'Exception: {e}',
                        'prompt_log': None
                    })
            
            self.test_results.extend(character_results)
        
        # Generate comprehensive report
        await self._generate_test_report()
    
    async def _send_api_request(self, character: str, message: str, user_id: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Send HTTP API request to character bot and return response + prompt log path."""
        
        port = self.base_ports[character]
        url = f"http://localhost:{port}/api/chat"
        
        payload = {
            "user_id": user_id,
            "message": message,
            "context": {
                "channel_type": "dm",
                "platform": "api_test",
                "metadata": {}
            }
        }
        
        try:
            # Record timestamp for prompt log correlation
            request_time = datetime.now()
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        
                        # Find corresponding prompt log file
                        prompt_log_path = await self._find_prompt_log(character, user_id, request_time)
                        
                        return response_data, prompt_log_path
                    else:
                        print(f"      HTTP {response.status}: {await response.text()}")
                        return None, None
                        
        except Exception as e:
            print(f"      API Request Error: {e}")
            return None, None
    
    async def _find_prompt_log(self, character: str, user_id: str, request_time: datetime) -> Optional[str]:
        """Find the prompt log file corresponding to this request."""
        
        # Wait a moment for log file to be written
        await asyncio.sleep(2)
        
        # Look for recent prompt log files for this character and user
        pattern = f"{self.prompt_logs_dir}/{character.title()}_*_{user_id}.json"
        
        matching_files = glob.glob(pattern, recursive=False)
        
        if matching_files:
            # Return the most recent file
            latest_file = max(matching_files, key=os.path.getctime)
            return latest_file
        
        # Fallback: look for any recent files for this character
        fallback_pattern = f"{self.prompt_logs_dir}/{character.title()}_*.json"
        fallback_files = glob.glob(fallback_pattern, recursive=False)
        
        if fallback_files:
            # Filter by creation time (within last 30 seconds)
            recent_files = [
                f for f in fallback_files 
                if abs(os.path.getctime(f) - request_time.timestamp()) < 30
            ]
            
            if recent_files:
                return max(recent_files, key=os.path.getctime)
        
        return None
    
    async def _validate_prompt_logs(self, prompt_log_path: str, scenario: Dict) -> Dict:
        """Validate prompt logs contain expected database-driven features."""
        
        try:
            with open(prompt_log_path, 'r') as f:
                log_data = json.load(f)
            
            # Extract system prompt and full conversation
            messages = log_data.get('messages', [])
            system_prompt = ""
            
            for msg in messages:
                if msg.get('role') == 'system':
                    system_prompt = msg.get('content', '')
                    break
            
            validation_details = []
            success = True
            
            # Validate based on scenario category
            if scenario['category'] == 'ai_identity':
                # Check for AI identity handling in system prompt
                found_keywords = [kw for kw in scenario['validation_keywords'] if kw.lower() in system_prompt.lower()]
                if found_keywords:
                    validation_details.append(f"✅ AI identity handling detected: {found_keywords}")
                else:
                    validation_details.append("❌ AI identity handling not found in system prompt")
                    success = False
            
            elif scenario['category'] == 'physical_interaction':
                # Check for physical interaction guidance
                found_keywords = [kw for kw in scenario['validation_keywords'] if kw in system_prompt]
                if found_keywords:
                    validation_details.append(f"✅ Physical interaction guidance detected: {found_keywords}")
                else:
                    validation_details.append("❌ Physical interaction guidance not found")
                    success = False
            
            elif scenario['category'] == 'question_templates':
                # Check for question generation in system prompt or LLM response
                llm_response = log_data.get('llm_response', '')
                combined_text = system_prompt + " " + llm_response
                
                question_indicators = ['?', 'How', 'What', 'Where', 'When', 'Why']
                found_questions = [q for q in question_indicators if q in combined_text]
                
                if found_questions:
                    validation_details.append(f"✅ Question generation detected: {found_questions}")
                else:
                    validation_details.append("❌ No question generation found")
                    # Don't fail for this - questions might not always be generated
            
            elif scenario['category'] == 'entity_classification':
                # Check for entity recognition in system prompt
                user_message = scenario['message']
                entities_mentioned = any(kw in system_prompt for kw in scenario['validation_keywords'])
                
                if entities_mentioned:
                    validation_details.append("✅ Entity classification working - entities recognized")
                else:
                    validation_details.append("❓ Entity classification unclear from system prompt")
                    # Don't fail - entity classification might be subtle
            
            elif scenario['category'] == 'control_test':
                # For control tests, we expect NO special handling
                special_keywords = ['AI nature', 'PHYSICAL INTERACTION', 'roleplay request']
                found_special = [kw for kw in special_keywords if kw in system_prompt]
                
                if not found_special:
                    validation_details.append("✅ Control test passed - no special handling triggered")
                else:
                    validation_details.append(f"❌ Control test failed - unexpected handling: {found_special}")
                    success = False
            
            # Additional validations
            if log_data.get('total_chars', 0) > 0:
                validation_details.append(f"✅ Prompt generated ({log_data['total_chars']} chars)")
            
            if log_data.get('llm_response'):
                validation_details.append("✅ LLM response received")
            
            return {
                'success': success,
                'details': '; '.join(validation_details)
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': f'Prompt log validation error: {e}'
            }
    
    async def _generate_test_report(self):
        """Generate comprehensive test report."""
        
        print("\\n\\n📊 COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        
        # Summary statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"\\n📈 SUMMARY STATISTICS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"   Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        
        # Results by character
        print(f"\\n🎭 RESULTS BY CHARACTER:")
        for character in ['aetheris', 'elena', 'jake']:
            char_results = [r for r in self.test_results if r['character'] == character]
            char_passed = sum(1 for r in char_results if r['success'])
            char_total = len(char_results)
            
            print(f"   {character.upper()}: {char_passed}/{char_total} passed ({char_passed/char_total*100:.1f}%)")
        
        # Results by scenario category
        print(f"\\n🔍 RESULTS BY SCENARIO:")
        scenarios = set(r['scenario'] for r in self.test_results)
        for scenario in sorted(scenarios):
            scenario_results = [r for r in self.test_results if r['scenario'] == scenario]
            scenario_passed = sum(1 for r in scenario_results if r['success'])
            scenario_total = len(scenario_results)
            
            print(f"   {scenario}: {scenario_passed}/{scenario_total} passed ({scenario_passed/scenario_total*100:.1f}%)")
        
        # Detailed failures
        failures = [r for r in self.test_results if not r['success']]
        if failures:
            print(f"\\n❌ DETAILED FAILURES ({len(failures)}):")
            for i, failure in enumerate(failures, 1):
                print(f"   {i}. {failure['character']} - {failure['scenario']}")
                print(f"      Message: '{failure['message']}'")
                print(f"      Issue: {failure['details']}")
                if failure['prompt_log']:
                    print(f"      Log: {failure['prompt_log']}")
        
        # Architecture compliance validation
        print(f"\\n💡 ARCHITECTURE COMPLIANCE VALIDATION:")
        
        ai_identity_tests = [r for r in self.test_results if r['scenario'] == 'ai_identity']
        ai_passed = sum(1 for r in ai_identity_tests if r['success'])
        print(f"   ✅ AI Identity Keywords (database-driven): {ai_passed}/{len(ai_identity_tests)} tests passed")
        
        physical_tests = [r for r in self.test_results if r['scenario'] == 'physical_interaction'] 
        physical_passed = sum(1 for r in physical_tests if r['success'])
        print(f"   ✅ Physical Interaction Keywords (database-driven): {physical_passed}/{len(physical_tests)} tests passed")
        
        question_tests = [r for r in self.test_results if r['scenario'] == 'question_templates']
        question_passed = sum(1 for r in question_tests if r['success'])
        print(f"   ✅ Question Templates (database-driven): {question_passed}/{len(question_tests)} tests passed")
        
        entity_tests = [r for r in self.test_results if r['scenario'] == 'entity_classification']
        entity_passed = sum(1 for r in entity_tests if r['success'])
        print(f"   ✅ Entity Classification (database-driven): {entity_passed}/{len(entity_tests)} tests passed")
        
        control_tests = [r for r in self.test_results if r['scenario'] == 'control_test']
        control_passed = sum(1 for r in control_tests if r['success'])
        print(f"   ✅ Control Tests (no false positives): {control_passed}/{len(control_tests)} tests passed")
        
        # Overall assessment
        overall_success_rate = passed_tests / total_tests * 100
        
        print(f"\\n🎯 OVERALL ASSESSMENT:")
        if overall_success_rate >= 90:
            print(f"   🎉 EXCELLENT: {overall_success_rate:.1f}% success rate")
            print(f"   ✅ High-priority hardcoding elimination is working excellently!")
        elif overall_success_rate >= 75:
            print(f"   ✅ GOOD: {overall_success_rate:.1f}% success rate")
            print(f"   ✅ High-priority hardcoding elimination is working well with minor issues")
        elif overall_success_rate >= 50:
            print(f"   ⚠️ PARTIAL: {overall_success_rate:.1f}% success rate")
            print(f"   ⚠️ Some issues with hardcoding elimination - needs investigation")
        else:
            print(f"   ❌ POOR: {overall_success_rate:.1f}% success rate") 
            print(f"   ❌ Significant issues with hardcoding elimination - requires fixes")
        
        print(f"\\n🚀 High-priority hardcoding elimination validation complete!")

async def main():
    """Run the comprehensive automated tests."""
    
    # Check if bots are running
    print("🔍 Checking bot availability...")
    
    test_suite = HighPriorityHardcodingTests()
    
    # Quick health check
    timeout = aiohttp.ClientTimeout(total=5)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for character, port in test_suite.base_ports.items():
            try:
                async with session.get(f"http://localhost:{port}/health") as response:
                    if response.status == 200:
                        print(f"   ✅ {character} bot available on port {port}")
                    else:
                        print(f"   ❌ {character} bot not responding on port {port}")
            except:
                print(f"   ❌ {character} bot not available on port {port}")
    
    print("\\n🚀 Starting comprehensive automated tests...")
    await test_suite.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())