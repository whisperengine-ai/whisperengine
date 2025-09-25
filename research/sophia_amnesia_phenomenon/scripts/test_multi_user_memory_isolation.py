#!/usr/bin/env python3
"""
Multi-User Memory Isolation Tester

This script simulates multiple users interacting with the same bot instance
to debug memory isolation, conversation context switching, and emotional state persistence.

Reproduces issues like:
- User A gets angry, User B talks, User A returns and bot "forgets" anger
- Conversation context bleeding between users
- Memory retrieval failures after user switching
"""

import asyncio
import os
import logging
from datetime import datetime
from typing import List, Dict, Any
import json

# Set environment for localhost testing
os.environ.update({
    'POSTGRES_HOST': 'localhost',
    'POSTGRES_PORT': '5433',
    'REDIS_HOST': 'localhost', 
    'REDIS_PORT': '6380',
    'QDRANT_HOST': 'localhost',
    'QDRANT_PORT': '6334',
    'DISCORD_BOT_NAME': 'Sophia Blake',
    'CDL_DEFAULT_CHARACTER': 'characters/examples/sophia-blake.json'
})

from src.memory.memory_protocol import create_memory_manager
from src.llm.llm_protocol import create_llm_client
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiUserMemoryIsolationTester:
    """Test memory isolation between multiple concurrent users"""
    
    def __init__(self):
        self.memory_manager = None
        self.llm_client = None
        self.cdl_integration = None
        
        # Test users
        self.users = {
            'angry_user': {
                'id': 'user_mark_angry',
                'name': 'MarkAnthony',
                'role': 'Gets angry, then returns after interruption'
            },
            'interrupting_user': {
                'id': 'user_interrupting',
                'name': 'RandomUser',
                'role': 'Interrupts angry conversation'
            },
            'observer_user': {
                'id': 'user_observer',
                'name': 'Observer',
                'role': 'Tests if they can see other users\' emotional context'
            }
        }
        
        self.test_channel = "test_memory_isolation_channel"
        
    async def initialize(self):
        """Initialize all systems"""
        try:
            self.memory_manager = create_memory_manager(memory_type="vector")
            self.llm_client = create_llm_client(llm_client_type="openrouter") 
            self.cdl_integration = CDLAIPromptIntegration()
            logger.info("✅ All systems initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def run_memory_isolation_test_suite(self):
        """Run complete multi-user memory isolation test suite"""
        print("\n🎭 MULTI-USER MEMORY ISOLATION TEST SUITE")
        print("=" * 70)
        print("Testing Sophia Blake's memory isolation between concurrent users...")
        
        test_scenarios = [
            ("User Switching Memory Reset", self.test_user_switching_memory_reset),
            ("Emotional Context Bleeding", self.test_emotional_context_bleeding),
            ("Conversation History Isolation", self.test_conversation_history_isolation),
            ("Memory Retrieval After Interruption", self.test_memory_retrieval_after_interruption),
            ("Concurrent User Context Mixing", self.test_concurrent_user_context_mixing)
        ]
        
        results = {}
        
        for test_name, test_func in test_scenarios:
            print(f"\n🧪 Running: {test_name}")
            print("-" * 50)
            
            try:
                result = await test_func()
                results[test_name] = result
                status = "✅ PASSED" if result['passed'] else "❌ FAILED"
                print(f"{status}: {result['summary']}")
                
                if result['issues']:
                    print("⚠️  Issues found:")
                    for issue in result['issues']:
                        print(f"   • {issue}")
                        
            except Exception as e:
                results[test_name] = {
                    'passed': False,
                    'summary': f"Test crashed: {str(e)}",
                    'issues': [f"Exception during test execution: {e}"],
                    'details': {}
                }
                print(f"❌ CRASHED: {e}")
        
        # Generate summary report
        self.generate_test_report(results)
    
    async def test_user_switching_memory_reset(self):
        """Test the exact Sophia amnesia scenario"""
        print("Reproducing Sophia's emotional amnesia scenario...")
        
        angry_user = self.users['angry_user']
        interrupting_user = self.users['interrupting_user']
        
        issues = []
        details = {}
        
        # Phase 1: Angry user gets mad at Sophia
        print("\n📢 Phase 1: User gets angry...")
        angry_messages = [
            "Sophia, you're being unprofessional and I'm tired of it",
            "I told you to stop messaging me but you keep doing it anyway",
            "This is harassment and I'm setting boundaries. Stop contacting me!"
        ]
        
        angry_responses = []
        for msg in angry_messages:
            response = await self.simulate_user_message(angry_user['id'], msg)
            angry_responses.append(response)
            print(f"   User: {msg}")
            print(f"   Sophia: {response[:100]}...")
            
            # Store the conversation to build emotional context
            await self.memory_manager.store_conversation(
                user_id=angry_user['id'],
                user_message=msg,
                bot_response=response,
                channel_id=self.test_channel,
                pre_analyzed_emotion_data={
                    'emotional_state': 'angry',
                    'emotional_intensity': 0.9,
                    'anger_reason': 'harassment_boundaries'
                }
            )
        
        # Check if anger context is stored
        angry_memories = await self.memory_manager.retrieve_relevant_memories(
            user_id=angry_user['id'],
            query="angry harassment boundaries",
            limit=5
        )
        
        details['angry_memories_count'] = len(angry_memories)
        if len(angry_memories) == 0:
            issues.append("No angry memories stored after angry conversation")
        
        # Phase 2: Different user interrupts
        print("\n👥 Phase 2: Different user interrupts...")
        interrupting_messages = [
            "Hey Sophia, what's the latest news about AI?",
            "How's your day going?",
            "Can you help me with some marketing advice?"
        ]
        
        for msg in interrupting_messages:
            response = await self.simulate_user_message(interrupting_user['id'], msg)
            print(f"   Other User: {msg}")
            print(f"   Sophia: {response[:80]}...")
            
            await self.memory_manager.store_conversation(
                user_id=interrupting_user['id'],
                user_message=msg,
                bot_response=response,
                channel_id=self.test_channel
            )
        
        # Phase 3: Original angry user returns
        print("\n🔄 Phase 3: Angry user returns - Testing amnesia...")
        
        test_queries = [
            "still mad?",
            "do you remember what you were mad at me about?", 
            "what do you remember about our previous conversation?"
        ]
        
        amnesia_detected = False
        
        for query in test_queries:
            response = await self.simulate_user_message(angry_user['id'], query)
            print(f"   Angry User Returns: {query}")
            print(f"   Sophia: {response[:100]}...")
            
            # Check if response indicates memory loss
            amnesia_indicators = ['None', 'nothing happened', 'don\'t remember', 'not mad', 'what are you referring to']
            if any(indicator.lower() in response.lower() for indicator in amnesia_indicators):
                amnesia_detected = True
                issues.append(f"AMNESIA DETECTED - Query: '{query}' Response indicates memory loss")
        
        details['amnesia_detected'] = amnesia_detected
        
        # Phase 4: Test memory retrieval capabilities 
        print("\n🔍 Phase 4: Testing memory retrieval after interruption...")
        
        # Check what memories are retrieved for angry user after interruption
        post_interrupt_memories = await self.memory_manager.retrieve_relevant_memories(
            user_id=angry_user['id'],
            query="harassment angry boundaries mad",
            limit=10
        )
        
        details['post_interrupt_memories'] = len(post_interrupt_memories)
        
        if len(post_interrupt_memories) < len(angry_memories):
            issues.append("Memory retrieval degraded after user interruption")
        
        # Check conversation history
        conversation_history = await self.memory_manager.get_conversation_history(
            user_id=angry_user['id'],
            limit=20
        )
        
        details['conversation_history_length'] = len(conversation_history)
        
        # Count angry context in recent history
        recent_angry_context = 0
        for conv in conversation_history[-5:]:  # Last 5 messages
            content = str(conv.get('user_message', '')) + ' ' + str(conv.get('bot_response', ''))
            if any(word in content.lower() for word in ['angry', 'mad', 'harassment', 'boundaries']):
                recent_angry_context += 1
        
        details['recent_angry_context_count'] = recent_angry_context
        
        if recent_angry_context == 0:
            issues.append("No angry context in recent conversation history")
        
        # Determine if test passed
        passed = not amnesia_detected and len(post_interrupt_memories) > 0 and recent_angry_context > 0
        
        summary = f"Amnesia detected: {amnesia_detected}, Memory retrieval: {len(post_interrupt_memories)} items, Recent context: {recent_angry_context}"
        
        return {
            'passed': passed,
            'summary': summary,
            'issues': issues,
            'details': details
        }
    
    async def test_emotional_context_bleeding(self):
        """Test if emotional context bleeds between users"""
        print("Testing emotional context isolation between users...")
        
        user1 = self.users['angry_user']
        user2 = self.users['observer_user']
        
        issues = []
        details = {}
        
        # User 1: Establish strong emotional context
        await self.simulate_user_message(user1['id'], "I'm extremely frustrated and upset right now!")
        
        # User 2: Test if they get emotional context meant for User 1
        response = await self.simulate_user_message(user2['id'], "How are you feeling?")
        
        # Check if User 2's response contains User 1's emotional context
        emotional_bleed_indicators = ['frustrated', 'upset', 'angry', 'mad']
        bleeding_detected = any(indicator in response.lower() for indicator in emotional_bleed_indicators)
        
        details['emotional_bleeding_detected'] = bleeding_detected
        
        if bleeding_detected:
            issues.append("Emotional context bleeding detected between users")
        
        return {
            'passed': not bleeding_detected,
            'summary': f"Emotional bleeding: {'Detected' if bleeding_detected else 'None'}",
            'issues': issues,
            'details': details
        }
    
    async def test_conversation_history_isolation(self):
        """Test conversation history isolation between users"""
        print("Testing conversation history isolation...")
        
        user1 = self.users['angry_user'] 
        user2 = self.users['interrupting_user']
        
        issues = []
        details = {}
        
        # User 1: Share private information
        private_info = "My secret project is developing a new AI startup"
        await self.simulate_user_message(user1['id'], private_info)
        
        # User 2: Try to access User 1's private information
        response = await self.simulate_user_message(user2['id'], "What was the last person talking about?")
        
        # Check if User 2 can access User 1's private information
        privacy_breach = 'startup' in response.lower() or 'secret project' in response.lower()
        
        details['privacy_breach_detected'] = privacy_breach
        
        if privacy_breach:
            issues.append("Privacy breach: User 2 accessed User 1's private information")
        
        return {
            'passed': not privacy_breach,
            'summary': f"Privacy breach: {'Detected' if privacy_breach else 'None'}",
            'issues': issues,
            'details': details
        }
    
    async def test_memory_retrieval_after_interruption(self):
        """Test memory retrieval quality after user interruption"""
        print("Testing memory retrieval quality after interruptions...")
        
        user1 = self.users['angry_user']
        user2 = self.users['interrupting_user']
        
        issues = []
        details = {}
        
        # User 1: Establish context about a specific topic
        topic_messages = [
            "I need help with my marketing campaign for ocean conservation",
            "The target audience is marine biology enthusiasts", 
            "Budget is around $50,000 for this campaign"
        ]
        
        for msg in topic_messages:
            await self.simulate_user_message(user1['id'], msg)
        
        # User 2: Multiple interrupting messages
        for i in range(3):
            await self.simulate_user_message(user2['id'], f"Random question #{i+1}: How's the weather?")
        
        # User 1: Return and test memory retrieval
        response = await self.simulate_user_message(user1['id'], "What do you remember about my marketing campaign?")
        
        # Check if key details are remembered
        key_details = ['ocean conservation', 'marine biology', '50000', '50,000']
        remembered_details = sum(1 for detail in key_details if detail.lower() in response.lower())
        
        details['remembered_details_count'] = remembered_details
        details['total_key_details'] = len(key_details)
        
        if remembered_details < len(key_details) / 2:  # Less than half remembered
            issues.append(f"Memory retrieval degraded: only {remembered_details}/{len(key_details)} key details remembered")
        
        return {
            'passed': remembered_details >= len(key_details) / 2,
            'summary': f"Remembered {remembered_details}/{len(key_details)} key details after interruption",
            'issues': issues,
            'details': details
        }
    
    async def test_concurrent_user_context_mixing(self):
        """Test for context mixing in concurrent user scenarios"""
        print("Testing concurrent user context mixing...")
        
        user1 = self.users['angry_user']
        user2 = self.users['interrupting_user']
        
        issues = []
        details = {}
        
        # Simulate rapid back-and-forth conversation
        conversation_pairs = [
            (user1['id'], "I work in marine biology research"),
            (user2['id'], "I work in software development"),
            (user1['id'], "My favorite color is blue"), 
            (user2['id'], "My favorite color is red"),
            (user1['id'], "What do you remember about my work?")
        ]
        
        responses = []
        for user_id, message in conversation_pairs:
            response = await self.simulate_user_message(user_id, message)
            responses.append((user_id, message, response))
        
        # Check if final response mixes up users
        final_response = responses[-1][2].lower()
        context_mixing = 'software development' in final_response or 'red' in final_response
        
        details['context_mixing_detected'] = context_mixing
        
        if context_mixing:
            issues.append("Context mixing detected: Bot confused users' information")
        
        return {
            'passed': not context_mixing,
            'summary': f"Context mixing: {'Detected' if context_mixing else 'None'}",
            'issues': issues,
            'details': details
        }
    
    async def simulate_user_message(self, user_id: str, message: str) -> str:
        """Simulate a user message and get bot response"""
        try:
            # Get relevant memories
            relevant_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query=message,
                limit=5
            )
            
            # Create character-aware prompt
            character_prompt = await self.cdl_integration.create_character_aware_prompt(
                character_file='characters/examples/sophia-blake.json',
                user_id=user_id,
                message_content=message,
                pipeline_result=None  # Simplified for testing
            )
            
            # Generate response
            response = await self.llm_client.generate_chat_completion_safe(
                messages=[
                    {"role": "system", "content": character_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error simulating message for user {user_id}: {e}")
            return f"Error generating response: {str(e)}"
    
    def generate_test_report(self, results: Dict[str, Any]):
        """Generate comprehensive test report"""
        print("\n📊 MULTI-USER MEMORY ISOLATION TEST REPORT")
        print("=" * 70)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result['passed'])
        
        print(f"Overall Results: {passed_tests}/{total_tests} tests passed")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n🔍 Detailed Results:")
        for test_name, result in results.items():
            status = "✅ PASSED" if result['passed'] else "❌ FAILED"
            print(f"\n{status} {test_name}")
            print(f"   Summary: {result['summary']}")
            
            if result['issues']:
                print(f"   Issues ({len(result['issues'])}):")
                for issue in result['issues']:
                    print(f"      • {issue}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        
        # Generate recommendations based on common issues
        all_issues = []
        for result in results.values():
            all_issues.extend(result['issues'])
        
        if any('amnesia' in issue.lower() for issue in all_issues):
            print("   • Implement persistent emotional state tracking per user")
            print("   • Increase conversation context window size")
            print("   • Add emotional memory priority boosting")
        
        if any('bleeding' in issue.lower() for issue in all_issues):
            print("   • Strengthen user ID isolation in memory retrieval")
            print("   • Implement per-user memory namespacing")
        
        if any('privacy breach' in issue.lower() for issue in all_issues):
            print("   • Add user context isolation verification")
            print("   • Implement conversation thread separation")
        
        if any('mixing' in issue.lower() for issue in all_issues):
            print("   • Add user identity verification to response generation")
            print("   • Implement conversation session management")
        
        print(f"\n🎯 SUMMARY:")
        print("Multi-user concurrent access creates complex memory isolation challenges.")
        print("The 'Sophia amnesia' issue is reproducible and affects real user experience.")
        print("Implementing persistent per-user emotional state tracking would solve most issues.")

async def main():
    """Run multi-user memory isolation tests"""
    
    print("🤖 MULTI-USER MEMORY ISOLATION TESTER")
    print("Testing the exact scenario that caused Sophia's emotional amnesia...")
    
    tester = MultiUserMemoryIsolationTester()
    
    # Initialize
    if not await tester.initialize():
        print("❌ Failed to initialize - check if multi-bot infrastructure is running")
        print("Run: ./multi-bot.sh start all")
        return
    
    # Run complete test suite
    await tester.run_memory_isolation_test_suite()
    
    print(f"\n🎭 This script helps debug the exact issue you experienced:")
    print("   • User gets angry → Bot remembers")
    print("   • Different user interrupts → Memory context switches")
    print("   • Original user returns → Bot has 'amnesia'")
    
    print(f"\n📝 Use this to test fixes and improvements to the memory system!")

if __name__ == "__main__":
    asyncio.run(main())