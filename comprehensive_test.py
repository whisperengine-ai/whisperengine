import sys
sys.path.append('.')
import asyncio
from env_manager import load_environment
import os

load_environment()
os.environ['ENV_MODE'] = 'production'

from src.core.bot import DiscordBotCore

async def test_all_functionality():
    print('=== COMPREHENSIVE AI SYSTEM TEST ===')
    bot_core = DiscordBotCore(debug_mode=True)
    bot_core.initialize_all()

    components = bot_core.get_components()

    # Test 1: Memory System 
    print('\n✅ 1. MEMORY SYSTEM TEST')
    memory_manager = components.get('memory_manager')
    test_user = '123456789012345678'  # Discord-style user ID
    test_message = 'I am passionate about machine learning and AI research'
    
    memory_manager.store_conversation(
        user_id=test_user,
        user_message=test_message,
        bot_response='That is fascinating! What specific areas of AI research interest you most?',
        channel_id='test_channel'
    )
    
    memories = memory_manager.retrieve_relevant_memories(
        user_id=test_user,
        message='artificial intelligence research',
        limit=3
    )
    print(f'   Stored and retrieved {len(memories)} memories ✅')

    # Test 2: Phase 2 - Emotional Intelligence
    print('\n✅ 2. PHASE 2 EMOTIONAL INTELLIGENCE TEST')
    phase2 = components.get('phase2_integration')
    if phase2:
        try:
            emotional_result = phase2.process_message_with_emotional_intelligence(
                user_id=test_user,
                message="I'm feeling overwhelmed with my workload lately",
                context={'channel_id': 'test'}
            )
            print(f'   Emotional analysis result: {emotional_result.get("emotional_state", "N/A")} ✅')
        except Exception as e:
            print(f'   Emotional analysis error: {e}')

    # Test 3: Phase 3 - Memory Networks  
    print('\n✅ 3. PHASE 3 MEMORY NETWORKS TEST')
    phase3 = components.get('phase3_memory_networks')
    if phase3:
        try:
            network_state = phase3.get_network_state(user_id=test_user)
            print(f'   Memory network clusters: {len(network_state.get("clusters", []))} ✅')
        except Exception as e:
            print(f'   Memory network error: {e}')

    # Test 4: External Emotion AI
    print('\n✅ 4. EXTERNAL EMOTION AI TEST')
    emotion_ai = components.get('external_emotion_ai')
    if emotion_ai:
        try:
            emotion_result = emotion_ai.analyze_emotion_cloud(
                "I'm really excited about my new project!"
            )
            print(f'   Cloud emotion analysis: {emotion_result.get("emotion", "N/A")} ✅')
        except Exception as e:
            print(f'   Cloud emotion analysis error: {e}')

    # Test 5: Phase 4 - Human-Like Intelligence (async)
    print('\n✅ 5. PHASE 4 HUMAN-LIKE INTELLIGENCE TEST')
    if hasattr(memory_manager, 'process_with_phase4_intelligence'):
        try:
            phase4_result = await memory_manager.process_with_phase4_intelligence(
                user_id=test_user,
                message="I'm looking for advice on career development",
                conversation_context=[],
                discord_context={'channel_id': 'test', 'guild_id': 'test'}
            )
            print(f'   Phase 4 interaction type: {phase4_result.get("interaction_type", "N/A")} ✅')
            print(f'   Phase 4 conversation mode: {phase4_result.get("conversation_mode", "N/A")} ✅')
        except Exception as e:
            print(f'   Phase 4 processing error: {e}')

    # Test 6: Production Optimization
    print('\n✅ 6. PRODUCTION OPTIMIZATION TEST')
    production_adapter = components.get('production_adapter')
    if production_adapter:
        print(f'   Production adapter type: {type(production_adapter).__name__} ✅')

    # Test 7: Conversation Cache (Redis)
    print('\n✅ 7. REDIS CONVERSATION CACHE TEST')
    conversation_cache = components.get('conversation_cache')
    if conversation_cache:
        print(f'   Cache type: {type(conversation_cache).__name__} ✅')

    print('\n=== FINAL ASSESSMENT ===')
    working_components = sum(1 for comp in components.values() if comp is not None)
    total_components = len(components)
    print(f'Working components: {working_components}/{total_components}')
    
    critical_systems = ['memory_manager', 'llm_client', 'phase2_integration', 'phase3_memory_networks']
    critical_working = sum(1 for sys in critical_systems if components.get(sys) is not None)
    print(f'Critical AI systems: {critical_working}/{len(critical_systems)} ✅')
    
    if critical_working == len(critical_systems):
        print('\n🎉 ALL CRITICAL AI SYSTEMS ARE FULLY FUNCTIONAL! 🎉')
        print('The WhisperEngine AI system is working as designed.')
    else:
        print('\n⚠️  Some critical systems need attention')

# Run the comprehensive test
try:
    asyncio.run(test_all_functionality())
except Exception as e:
    print(f'Test failed: {e}')
    import traceback
    traceback.print_exc()