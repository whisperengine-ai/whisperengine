import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)

async def test_context_switch():
    try:
        from src.intelligence.context_switch_detector import ContextSwitchDetector
        
        # Initialize detector
        detector = ContextSwitchDetector()
        print("Detector initialized")
        
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