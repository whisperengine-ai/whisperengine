#!/usr/bin/env python3
"""
Comprehensive CDL (Character Definition Language) validation and error testing system.
Tests for parsing errors, missing fields, malformed structures, and validation issues.
"""

import asyncio
import json
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional
from src.characters.cdl.parser import load_character
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration

class CDLValidationTester:
    def __init__(self):
        self.test_results = []
        
    def log_result(self, test_name: str, status: str, message: str, details: Optional[str] = None):
        """Log test results for summary."""
        self.test_results.append({
            'test': test_name,
            'status': status,
            'message': message,
            'details': details
        })
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")

    async def test_cdl_file_parsing(self, file_path: Path) -> Dict[str, Any]:
        """Test parsing of a single CDL file."""
        test_name = f"Parse {file_path.name}"
        
        try:
            # Test 1: JSON syntax validation
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            # Test 2: CDL parser validation
            character = load_character(file_path)
            
            # Test 3: Required fields validation
            required_fields = ['identity', 'personality', 'communication']
            missing_fields = []
            
            if not hasattr(character, 'identity') or not character.identity:
                missing_fields.append('identity')
            if not hasattr(character, 'personality') or not character.personality:
                missing_fields.append('personality')
            if not hasattr(character, 'communication') or not character.communication:
                missing_fields.append('communication')
                
            if missing_fields:
                self.log_result(test_name, "FAIL", f"Missing required fields: {missing_fields}")
                return {'status': 'FAIL', 'error': f"Missing fields: {missing_fields}"}
            
            # Test 4: Identity validation
            if not character.identity.name:
                self.log_result(test_name, "FAIL", "Missing character name in identity")
                return {'status': 'FAIL', 'error': 'Missing character name'}
                
            # Test 5: Communication validation
            if not character.communication.typical_responses:
                self.log_result(test_name, "WARN", "No typical_responses defined")
                
            self.log_result(test_name, "PASS", f"Successfully parsed {character.identity.name}")
            return {
                'status': 'PASS',
                'character_name': character.identity.name,
                'has_typical_responses': bool(character.communication.typical_responses),
                'response_scenarios': list(character.communication.typical_responses.keys()) if character.communication.typical_responses else []
            }
            
        except json.JSONDecodeError as e:
            self.log_result(test_name, "FAIL", f"JSON syntax error: {e}", str(e))
            return {'status': 'FAIL', 'error': f'JSON syntax: {e}'}
        except Exception as e:
            self.log_result(test_name, "FAIL", f"Parsing error: {e}", traceback.format_exc())
            return {'status': 'FAIL', 'error': f'Parser error: {e}'}

    async def test_cdl_integration(self, file_path: Path) -> Dict[str, Any]:
        """Test CDL integration with AI prompt system."""
        test_name = f"Integration {file_path.name}"
        
        try:
            cdl_integration = CDLAIPromptIntegration()
            
            # Test with various message types
            test_messages = [
                "Hello there",  # Greeting
                "You're beautiful",  # Compliment
                "I find you attractive",  # Romantic interest
                "Help me with advice"  # Advice request
            ]
            
            integration_results = {}
            
            for message in test_messages:
                try:
                    prompt = await cdl_integration.create_character_aware_prompt(
                        character_file=str(file_path),
                        user_id="test_user",
                        message_content=message,
                        pipeline_result=None
                    )
                    
                    # Check if character name appears in prompt
                    character = load_character(file_path)
                    character_name_in_prompt = character.identity.name in prompt
                    has_scenario_guidance = "SCENARIO-SPECIFIC RESPONSES:" in prompt
                    
                    integration_results[message] = {
                        'prompt_generated': True,
                        'character_name_present': character_name_in_prompt,
                        'scenario_guidance': has_scenario_guidance,
                        'prompt_length': len(prompt)
                    }
                    
                except Exception as e:
                    integration_results[message] = {
                        'prompt_generated': False,
                        'error': str(e)
                    }
            
            # Check overall integration success
            successful_integrations = sum(1 for result in integration_results.values() 
                                        if result.get('prompt_generated', False))
            
            if successful_integrations == len(test_messages):
                self.log_result(test_name, "PASS", f"All {len(test_messages)} integrations successful")
                return {'status': 'PASS', 'results': integration_results}
            else:
                self.log_result(test_name, "WARN", f"{successful_integrations}/{len(test_messages)} integrations successful")
                return {'status': 'WARN', 'results': integration_results}
                
        except Exception as e:
            self.log_result(test_name, "FAIL", f"Integration test failed: {e}", traceback.format_exc())
            return {'status': 'FAIL', 'error': str(e)}

    async def test_malformed_cdl_handling(self):
        """Test handling of various malformed CDL files."""
        print(f"\n📋 Testing Malformed CDL Handling")
        print("-" * 50)
        
        # Create temporary malformed CDL files for testing
        test_cases = [
            {
                'name': 'invalid_json.json',
                'content': '{"character": {"identity": {"name": "Test"}, "missing_quote": }',  # Invalid JSON
                'expected_error': 'JSON syntax'
            },
            {
                'name': 'missing_identity.json',
                'content': '{"character": {"personality": {}, "communication": {}}}',  # Missing identity
                'expected_error': 'Missing identity'
            },
            {
                'name': 'empty_character.json',
                'content': '{"character": {}}',  # Empty character
                'expected_error': 'Missing required fields'
            },
            {
                'name': 'invalid_structure.json',
                'content': '{"not_character": {"identity": {"name": "Test"}}}',  # Wrong structure
                'expected_error': 'Missing character'
            }
        ]
        
        temp_dir = Path("temp_test_cdl")
        temp_dir.mkdir(exist_ok=True)
        
        try:
            for test_case in test_cases:
                temp_file = temp_dir / test_case['name']
                
                try:
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        f.write(test_case['content'])
                    
                    # Test parsing this malformed file
                    result = await self.test_cdl_file_parsing(temp_file)
                    
                    if result['status'] == 'FAIL':
                        self.log_result(f"Malformed {test_case['name']}", "PASS", 
                                      f"Correctly detected error: {result.get('error', 'Unknown')}")
                    else:
                        self.log_result(f"Malformed {test_case['name']}", "FAIL", 
                                      "Should have failed but didn't")
                        
                except Exception as e:
                    self.log_result(f"Malformed {test_case['name']}", "PASS", 
                                  f"Correctly caught exception: {e}")
                finally:
                    # Clean up temp file
                    if temp_file.exists():
                        temp_file.unlink()
        finally:
            # Clean up temp directory
            if temp_dir.exists():
                temp_dir.rmdir()

    async def run_comprehensive_cdl_tests(self):
        """Run comprehensive CDL validation tests."""
        print("🔍 CDL Validation and Error Testing System")
        print("=" * 60)
        
        # Test 1: Find and test all CDL files
        characters_dir = Path("characters/examples")
        if not characters_dir.exists():
            print("❌ Characters directory not found!")
            return
            
        cdl_files = list(characters_dir.glob("*.json"))
        if not cdl_files:
            print("❌ No CDL files found!")
            return
            
        print(f"📁 Found {len(cdl_files)} CDL files to test")
        print("-" * 50)
        
        # Test each CDL file
        for cdl_file in cdl_files:
            print(f"\n🧪 Testing: {cdl_file.name}")
            print("-" * 30)
            
            # Test parsing
            parse_result = await self.test_cdl_file_parsing(cdl_file)
            
            # Test integration (only if parsing succeeded)
            if parse_result['status'] == 'PASS':
                await self.test_cdl_integration(cdl_file)
        
        # Test malformed CDL handling
        await self.test_malformed_cdl_handling()
        
        # Print summary
        await self.print_test_summary()

    async def print_test_summary(self):
        """Print comprehensive test summary."""
        print(f"\n📊 Test Summary")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        warned = len([r for r in self.test_results if r['status'] == 'WARN'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"⚠️  Warnings: {warned}")
        print(f"❌ Failed: {failed}")
        
        if failed > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"   • {result['test']}: {result['message']}")
        
        if warned > 0:
            print(f"\n⚠️  Warnings:")
            for result in self.test_results:
                if result['status'] == 'WARN':
                    print(f"   • {result['test']}: {result['message']}")
        
        success_rate = (passed / total_tests) * 100 if total_tests > 0 else 0
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 Excellent CDL validation results!")
        elif success_rate >= 75:
            print("👍 Good CDL validation - some improvements needed")
        else:
            print("⚠️  CDL validation needs attention")

async def main():
    """Run CDL validation tests."""
    tester = CDLValidationTester()
    await tester.run_comprehensive_cdl_tests()

if __name__ == "__main__":
    asyncio.run(main())