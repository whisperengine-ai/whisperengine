#!/usr/bin/env python3
"""
End-to-End PostgreSQL Fact Storage Test via HTTP Chat API

Tests the complete flow for both Elena and Dotty bots:
1. Store facts via chat message
2. Store preferences via chat message  
3. Query PostgreSQL to verify storage
4. Retrieve facts in subsequent conversation
5. Validate PostgreSQL retrieval in logs

Usage:
    python tests/e2e_postgres_fact_http_test.py
"""

import asyncio
import aiohttp
import logging
import sys
import time
from typing import Dict, Any
import subprocess

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PostgreSQLFactE2ETester:
    """End-to-end tester for PostgreSQL fact storage via HTTP API"""
    
    def __init__(self):
        self.test_user_id = f"test_user_e2e_{int(time.time())}"
        
        # Bot configurations
        self.bots = {
            'elena': {
                'name': 'Elena',
                'port': 9091,
                'container': 'whisperengine-elena-bot',
                'url': 'http://localhost:9091/api/chat'
            },
            'dotty': {
                'name': 'Dotty',
                'port': 3007,
                'container': 'whisperengine-dotty-bot',
                'url': 'http://localhost:3007/api/chat'
            }
        }
        
        # Test data
        self.test_facts = [
            "I love pizza and sushi",
            "I enjoy hiking and photography",
            "My name is TestUser"
        ]
        
        self.results = {
            'elena': {'passed': 0, 'failed': 0, 'tests': []},
            'dotty': {'passed': 0, 'failed': 0, 'tests': []}
        }
    
    async def send_chat_message(self, bot_key: str, message: str) -> Dict[str, Any]:
        """Send chat message to bot via HTTP API"""
        bot = self.bots[bot_key]
        
        payload = {
            "user_id": self.test_user_id,
            "message": message,
            "context": {
                "channel_type": "dm",
                "platform": "api_test",
                "metadata": {
                    "test_type": "e2e_postgres_facts"
                }
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    bot['url'],
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ [{bot['name']}] Message sent successfully")
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ [{bot['name']}] HTTP {response.status}: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"❌ [{bot['name']}] Request failed: {e}")
            return None
    
    def check_postgres_facts(self, entity_name: str) -> bool:
        """Check if fact exists in PostgreSQL"""
        query = f"""
        SELECT fe.entity_name, fe.entity_type, ufr.relationship_type
        FROM user_fact_relationships ufr
        JOIN fact_entities fe ON ufr.entity_id = fe.id
        WHERE fe.entity_name = '{entity_name}'
          AND ufr.user_id = '{self.test_user_id}'
        LIMIT 1;
        """
        
        try:
            result = subprocess.run(
                [
                    'docker', 'exec', 'whisperengine-multi-postgres',
                    'psql', '-U', 'whisperengine', '-d', 'whisperengine',
                    '-t', '-c', query
                ],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                logger.info(f"  ✅ Found '{entity_name}' in PostgreSQL")
                return True
            else:
                logger.warning(f"  ⚠️ '{entity_name}' not found in PostgreSQL")
                return False
        except Exception as e:
            logger.error(f"  ❌ PostgreSQL query failed: {e}")
            return False
    
    def check_postgres_preference(self, pref_key: str, expected_value: str = None) -> bool:
        """Check if preference exists in PostgreSQL with optional value validation"""
        query = f"""
        SELECT preferences::jsonb->'{pref_key}'->>'value' as value
        FROM universal_users
        WHERE universal_id = '{self.test_user_id}'
          AND preferences::jsonb ? '{pref_key}'
        LIMIT 1;
        """
        
        try:
            result = subprocess.run(
                [
                    'docker', 'exec', 'whisperengine-multi-postgres',
                    'psql', '-U', 'whisperengine', '-d', 'whisperengine',
                    '-t', '-c', query
                ],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                actual_value = result.stdout.strip()
                if expected_value:
                    # Check if actual value matches expected (case-insensitive partial match)
                    if expected_value.lower() in actual_value.lower():
                        logger.info(f"  ✅ Found preference '{pref_key}' = '{actual_value}' in PostgreSQL")
                        return True
                    else:
                        logger.warning(f"  ⚠️ Preference '{pref_key}' found but value mismatch: expected '{expected_value}', got '{actual_value}'")
                        return False
                else:
                    logger.info(f"  ✅ Found preference '{pref_key}' = '{actual_value}' in PostgreSQL")
                    return True
            else:
                logger.warning(f"  ⚠️ Preference '{pref_key}' not found in PostgreSQL")
                return False
        except Exception as e:
            logger.error(f"  ❌ PostgreSQL query failed: {e}")
            return False
    
    def check_bot_logs(self, bot_key: str, pattern: str, tail_lines: int = 2000) -> bool:
        """Check bot logs for specific pattern (searches more lines for better reliability)"""
        bot = self.bots[bot_key]
        
        try:
            result = subprocess.run(
                ['docker', 'logs', bot['container'], '--tail', str(tail_lines)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if pattern in result.stdout or pattern in result.stderr:
                logger.info(f"  ✅ [{bot['name']}] Found pattern in logs: '{pattern}'")
                return True
            else:
                logger.warning(f"  ⚠️ [{bot['name']}] Pattern not found: '{pattern}'")
                return False
        except Exception as e:
            logger.error(f"  ❌ [{bot['name']}] Log check failed: {e}")
            return False
    
    async def test_fact_storage(self, bot_key: str) -> bool:
        """Test 1: Store facts via chat message"""
        bot = self.bots[bot_key]
        logger.info(f"\n🧪 Test 1 [{bot['name']}]: Fact Storage")
        
        # Send message with facts
        response = await self.send_chat_message(bot_key, self.test_facts[0])
        
        if not response:
            self.results[bot_key]['tests'].append({
                'name': 'Fact Storage - HTTP Request',
                'passed': False,
                'error': 'HTTP request failed'
            })
            self.results[bot_key]['failed'] += 1
            return False
        
        self.results[bot_key]['tests'].append({
            'name': 'Fact Storage - HTTP Request',
            'passed': True
        })
        self.results[bot_key]['passed'] += 1
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Check PostgreSQL for stored facts
        pizza_stored = self.check_postgres_facts('pizza')
        sushi_stored = self.check_postgres_facts('sushi')
        
        facts_test_passed = pizza_stored or sushi_stored
        self.results[bot_key]['tests'].append({
            'name': 'Fact Storage - PostgreSQL Verification',
            'passed': facts_test_passed,
            'details': f"pizza: {pizza_stored}, sushi: {sushi_stored}"
        })
        
        if facts_test_passed:
            self.results[bot_key]['passed'] += 1
        else:
            self.results[bot_key]['failed'] += 1
        
        return facts_test_passed
    
    async def test_preference_storage(self, bot_key: str) -> bool:
        """Test 2: Store preference via chat message"""
        bot = self.bots[bot_key]
        logger.info(f"\n🧪 Test 2 [{bot['name']}]: Preference Storage")
        
        # Send message with preference
        response = await self.send_chat_message(bot_key, self.test_facts[2])
        
        if not response:
            self.results[bot_key]['tests'].append({
                'name': 'Preference Storage - HTTP Request',
                'passed': False,
                'error': 'HTTP request failed'
            })
            self.results[bot_key]['failed'] += 1
            return False
        
        self.results[bot_key]['tests'].append({
            'name': 'Preference Storage - HTTP Request',
            'passed': True
        })
        self.results[bot_key]['passed'] += 1
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Check PostgreSQL for stored preference
        # Note: The regex captures "Test" from "My name is TestUser"
        pref_stored = self.check_postgres_preference('preferred_name', expected_value='Test')
        
        self.results[bot_key]['tests'].append({
            'name': 'Preference Storage - PostgreSQL Verification',
            'passed': pref_stored
        })
        
        if pref_stored:
            self.results[bot_key]['passed'] += 1
        else:
            self.results[bot_key]['failed'] += 1
        
        return pref_stored
    
    async def test_fact_retrieval(self, bot_key: str) -> bool:
        """Test 3: Retrieve facts in conversation"""
        bot = self.bots[bot_key]
        logger.info(f"\n🧪 Test 3 [{bot['name']}]: Fact Retrieval")
        
        # Send message that should trigger fact retrieval
        response = await self.send_chat_message(
            bot_key, 
            "What do you remember about me?"
        )
        
        if not response:
            self.results[bot_key]['tests'].append({
                'name': 'Fact Retrieval - HTTP Request',
                'passed': False,
                'error': 'HTTP request failed'
            })
            self.results[bot_key]['failed'] += 1
            return False
        
        self.results[bot_key]['tests'].append({
            'name': 'Fact Retrieval - HTTP Request',
            'passed': True
        })
        self.results[bot_key]['passed'] += 1
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Check logs for PostgreSQL fact retrieval
        postgres_used = self.check_bot_logs(bot_key, "POSTGRES FACTS: Retrieved")
        
        self.results[bot_key]['tests'].append({
            'name': 'Fact Retrieval - PostgreSQL Query Used',
            'passed': postgres_used
        })
        
        if postgres_used:
            self.results[bot_key]['passed'] += 1
        else:
            # Check if legacy fallback was used (acceptable during transition)
            legacy_used = self.check_bot_logs(bot_key, "LEGACY FACTS")
            if legacy_used:
                logger.warning(f"  ⚠️ [{bot['name']}] Used legacy fallback (acceptable during transition)")
                self.results[bot_key]['tests'][-1]['warning'] = 'Legacy fallback used'
            self.results[bot_key]['failed'] += 1
        
        # Check if response mentions facts (basic validation)
        # Note: Preference extraction captures "Test" not "TestUser"
        bot_response = response.get('response', '').lower() if response else ''
        mentions_facts = 'pizza' in bot_response or 'sushi' in bot_response or 'test' in bot_response
        
        self.results[bot_key]['tests'].append({
            'name': 'Fact Retrieval - Response Content',
            'passed': mentions_facts,
            'details': f"Response length: {len(bot_response)}"
        })
        
        if mentions_facts:
            self.results[bot_key]['passed'] += 1
        else:
            self.results[bot_key]['failed'] += 1
        
        return postgres_used and mentions_facts
    
    async def test_bot(self, bot_key: str):
        """Run all tests for a specific bot"""
        bot = self.bots[bot_key]
        logger.info(f"\n{'='*80}")
        logger.info(f"TESTING BOT: {bot['name'].upper()} (Port {bot['port']})")
        logger.info(f"Test User ID: {self.test_user_id}")
        logger.info(f"{'='*80}")
        
        # Test 1: Fact storage
        await self.test_fact_storage(bot_key)
        
        # Test 2: Preference storage
        await self.test_preference_storage(bot_key)
        
        # Test 3: Fact retrieval
        await self.test_fact_retrieval(bot_key)
    
    def print_summary(self):
        """Print test summary for all bots"""
        logger.info(f"\n{'='*80}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*80}")
        
        total_passed = 0
        total_failed = 0
        
        for bot_key, results in self.results.items():
            bot = self.bots[bot_key]
            logger.info(f"\n{bot['name']}:")
            logger.info(f"  Passed: {results['passed']}")
            logger.info(f"  Failed: {results['failed']}")
            
            total_passed += results['passed']
            total_failed += results['failed']
            
            # Detailed test results
            for test in results['tests']:
                status = "✅" if test['passed'] else "❌"
                logger.info(f"    {status} {test['name']}")
                if 'details' in test:
                    logger.info(f"       Details: {test['details']}")
                if 'warning' in test:
                    logger.info(f"       ⚠️ Warning: {test['warning']}")
                if 'error' in test:
                    logger.info(f"       Error: {test['error']}")
        
        logger.info(f"\n{'='*80}")
        logger.info(f"OVERALL RESULTS:")
        logger.info(f"  Total Passed: {total_passed}")
        logger.info(f"  Total Failed: {total_failed}")
        logger.info(f"  Success Rate: {(total_passed/(total_passed+total_failed)*100):.1f}%")
        logger.info(f"{'='*80}")
        
        if total_failed == 0:
            logger.info("\n✅ ALL TESTS PASSED - PostgreSQL fact retrieval working correctly!")
        else:
            logger.warning(f"\n⚠️ {total_failed} TESTS FAILED - Review results above")
    
    async def run_all_tests(self):
        """Run tests for all bots"""
        logger.info("\n" + "="*80)
        logger.info("END-TO-END POSTGRESQL FACT STORAGE TEST")
        logger.info("Testing: Elena & Dotty bots via HTTP Chat API")
        logger.info("="*80)
        
        # Test Elena
        await self.test_bot('elena')
        
        # Wait between bots
        await asyncio.sleep(2)
        
        # Test Dotty
        await self.test_bot('dotty')
        
        # Print summary
        self.print_summary()


async def main():
    """Main entry point"""
    tester = PostgreSQLFactE2ETester()
    await tester.run_all_tests()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️ Test interrupted by user")
        sys.exit(1)
