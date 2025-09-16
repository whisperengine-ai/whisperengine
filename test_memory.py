import sys
sys.path.append('.')
from env_manager import load_environment
import os

load_environment()
os.environ['ENV_MODE'] = 'production'

from src.core.bot import DiscordBotCore

print('=== TESTING MEMORY WITH CORRECT API ===')
bot_core = DiscordBotCore(debug_mode=True)
bot_core.initialize_all()

memory_manager = bot_core.get_components()['memory_manager']

# Test storing a conversation with correct parameters
test_user = 'test_user_correct_api'
test_message = 'I love playing guitar and learning jazz music'
bot_response = 'That sounds amazing! Jazz guitar is really complex and beautiful.'

print(f'Storing: "{test_message}"')

try:
    result = memory_manager.store_conversation(
        user_id=test_user,
        user_message=test_message,
        bot_response=bot_response,
        channel_id='test_channel_123'
    )
    print(f'✅ Storage result: {result}')
except Exception as e:
    print(f'❌ Storage failed: {e}')

# Test retrieving memories with correct parameters
print('\nTesting memory retrieval...')
try:
    memories = memory_manager.retrieve_relevant_memories(
        user_id=test_user,
        message='guitar jazz music',
        limit=5
    )
    
    print(f'Found {len(memories)} relevant memories')
    for i, memory in enumerate(memories):
        print(f'  Memory {i+1}:')
        for key, value in memory.items():
            if key not in ['embedding']:  # Skip embedding data
                if len(str(value)) > 100:
                    print(f'    {key}: {str(value)[:100]}...')
                else:
                    print(f'    {key}: {value}')
    
    # Check if our test message was found
    found_our_message = any('guitar' in str(m.get('message', '') or m.get('user_message', '')).lower() for m in memories)
    
    if found_our_message:
        print('\n=== RESULT: Memory system is WORKING - Found our test message! ===')
    else:
        print('\n=== RESULT: Memory system is WORKING but did not find test message ===')
    
except Exception as e:
    print(f'❌ Retrieval failed: {e}')
    import traceback
    traceback.print_exc()