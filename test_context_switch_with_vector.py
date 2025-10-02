import asyncio
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, 
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
        
        # Initialize detector with vector store
        print("Initializing detector with vector store...")
        detector = ContextSwitchDetector(vector_memory_store=memory_manager)
        print("Detector initialized with vector store")
        
        # Test message with clear topic shift
        test_message = "I've been researching ocean acidification and its impact on coral reefs. By the way, could you recommend a good Italian restaurant in Seattle?"
        
        print(f"Testing with message: '{test_message}'")
        
        # Run detection
        switches = await detector.detect_context_switches('test_user', test_message)
        
        # Print results
        print(f"Detected switches: {len(switches)}")
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