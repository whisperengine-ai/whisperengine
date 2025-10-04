#!/usr/bin/env python3
"""
Test the workflow system directly with Dotty's configuration.
This simulates what happens when a user sends "I'll have a whiskey" to test
the platform-agnostic workflow detection in MessageProcessor.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.roleplay.workflow_manager import WorkflowManager
from src.roleplay.transaction_manager import create_transaction_manager
from src.llm.llm_protocol import create_llm_client
from src.core.message_processor import MessageContext
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_workflow_detection():
    """Test workflow detection with Dotty's configuration."""
    
    print("🎯 Testing Workflow System with Dotty Configuration")
    print("=" * 60)
    
    try:
        # 1. Load environment from .env.dotty
        from dotenv import load_dotenv
        load_dotenv(".env.dotty")
        
        print(f"✅ Loaded environment - Character: {os.getenv('CDL_DEFAULT_CHARACTER')}")
        print(f"✅ Bot name: {os.getenv('DISCORD_BOT_NAME')}")
        
        # 2. Create LLM client (dependency for workflow manager)
        llm_client = create_llm_client()
        print("✅ LLM client created")
        
        # 3. Create transaction manager (mock for testing)
        class MockTransactionManager:
            async def create_transaction(self, user_id, bot_name, workflow_name, context_data, transaction_type=None, state="pending"):
                transaction_id = f"tx_{workflow_name}_{user_id[:8]}"
                print(f"🔄 Created transaction: {transaction_id}")
                print(f"   - User: {user_id}")
                print(f"   - Workflow: {workflow_name}")
                print(f"   - Context: {context_data}")
                print(f"   - Type: {transaction_type}")
                print(f"   - State: {state}")
                return transaction_id
            
            async def get_pending_transaction(self, user_id, bot_name, workflow_name):
                return None  # No pending transactions for test
            
            async def check_pending_transaction(self, user_id, bot_name):
                return None  # No pending transactions for test
        
        transaction_manager = MockTransactionManager()
        print("✅ Mock transaction manager created")
        
        # 4. Create workflow manager
        workflow_manager = WorkflowManager(
            transaction_manager=transaction_manager,
            llm_client=llm_client
        )
        print("✅ Workflow manager created")
        
        # 5. Load workflows for Dotty
        character_file = os.getenv('CDL_DEFAULT_CHARACTER')
        if not character_file:
            print("❌ No character file specified in environment")
            return
            
        success = await workflow_manager.load_workflows_for_character(character_file)
        if success:
            print(f"✅ Loaded workflows for character: {character_file}")
        else:
            print(f"❌ Failed to load workflows for character: {character_file}")
            return
        
        # 6. Test message processing
        test_messages = [
            "I'll have a whiskey",
            "Give me a beer", 
            "Can I get some wine?",
            "Can you make me something with chocolate and strawberries?",  # Custom drink
            "Here you go",  # Payment
            "Never mind"    # Cancellation
        ]
        
        user_id = "test_user_12345"
        bot_name = os.getenv("DISCORD_BOT_NAME", "dotty").lower()
        
        print(f"\n🧪 Testing Messages (user: {user_id}, bot: {bot_name})")
        print("-" * 60)
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n{i}. Testing: '{message}'")
            
            # Detect intent
            trigger_result = await workflow_manager.detect_intent(
                message=message,
                user_id=user_id,
                bot_name=bot_name
            )
            
            if trigger_result:
                print(f"   ✅ DETECTED: {trigger_result.workflow_name} (confidence: {trigger_result.match_confidence:.2f})")
                print(f"   📋 Context: {trigger_result.extracted_context}")
                
                # Execute workflow action
                workflow_result = await workflow_manager.execute_workflow_action(
                    trigger_result=trigger_result,
                    user_id=user_id,
                    bot_name=bot_name,
                    message=message
                )
                
                print(f"   🎯 ACTION: {workflow_result.get('action')}")
                print(f"   📝 PROMPT INJECTION: {workflow_result.get('prompt_injection', 'None')[:100]}...")
                
                if workflow_result.get('transaction_id'):
                    print(f"   🆔 TRANSACTION: {workflow_result['transaction_id']}")
                    
            else:
                print(f"   ❌ No workflow detected")
        
        print(f"\n🎉 Workflow system test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow_detection())