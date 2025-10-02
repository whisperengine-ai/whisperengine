import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)

async def test_context_switch():
    try:
        # Import required modules
        from src.intelligence.context_switch_detector import ContextSwitchDetector
        from src.memory.memory_protocol import create_memory_manager
        
        # Create vector memory manager
        print("Creating memory manager...")
        memory_manager = create_memory_manager(memory_type="vector")
        print(f"Memory manager created: {type(memory_manager)}")
        
        # Print available methods on memory_manager
        print("Available methods on memory_manager:")
        for method in dir(memory_manager):
            if not method.startswith('_'):
                print(f"  - {method}")
        
        # Check if detect_contradictions exists
        has_detect_contradictions = hasattr(memory_manager, 'detect_contradictions')
        print(f"memory_manager has detect_contradictions: {has_detect_contradictions}")
        
        # Initialize detector with vector store
        print("\nInitializing detector with vector store...")
        detector = ContextSwitchDetector(vector_memory_store=memory_manager)
        print("Detector initialized with vector store")
        
        # Print context switch detector details
        print("\nContext switch detector details:")
        print(f"  Has vector store: {detector.vector_store is not None}")
        if detector.vector_store:
            print(f"  Vector store type: {type(detector.vector_store)}")
            print(f"  Has detect_contradictions: {hasattr(detector.vector_store, 'detect_contradictions')}")
        
        # Test message with clear topic shift
        test_message = "I've been researching ocean acidification and its impact on coral reefs. By the way, could you recommend a good Italian restaurant in Seattle?"
        
        print(f"\nTesting with message: '{test_message}'")
        
        # Extract topics manually
        from src.intelligence.context_switch_detector import ContextSwitchDetector
        first_part = test_message.split(". By the way")[0]
        second_part = "By the way" + test_message.split("By the way")[1]
        print(f"First topic part: '{first_part}'")
        print(f"Second topic part: '{second_part}'")
        
        # Run detection
        switches = await detector.detect_context_switches('test_user', test_message)
        
        # Print results
        print(f"\nDetected switches: {len(switches)}")
        for i, switch in enumerate(switches):
            print(f"Switch {i+1}:")
            print(f"  Type: {switch.switch_type}")
            print(f"  Strength: {switch.strength}")
            print(f"  Description: {switch.description}")
            print(f"  Confidence: {switch.confidence_score}")
            print(f"  Adaptation Strategy: {switch.adaptation_strategy}")
            
    except Exception as e:
        print(f"Error testing context switch detection: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_context_switch())