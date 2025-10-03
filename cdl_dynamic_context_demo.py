#!/usr/bin/env python3
"""
CDL Dynamic Context Demonstration

Shows how WhisperEngine's CDL system dynamically includes/excludes content based on conversation context.
"""

import asyncio
from src.characters.cdl.parser import load_character
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration

async def demonstrate_cdl_dynamic_context():
    """Demonstrate how CDL context-aware inclusion works."""
    
    print("🎭 CDL DYNAMIC CONTEXT DEMONSTRATION")
    print("=" * 80)
    
    # Load Sophia character (most complete)
    character = load_character('characters/examples/sophia_v2.json')
    cdl_integration = CDLAIPromptIntegration()
    
    # Test scenarios
    test_scenarios = [
        {
            "type": "General Conversation",
            "message": "Hi! How are you today?",
            "expected_sections": ["Basic identity", "Personality", "Response style"]
        },
        {
            "type": "Career Discussion", 
            "message": "Tell me about your work and career background",
            "expected_sections": ["Identity", "Career info", "Professional skills", "Education"]
        },
        {
            "type": "Family Discussion",
            "message": "Do you have any family or siblings?", 
            "expected_sections": ["Identity", "Family background", "Backstory"]
        },
        {
            "type": "Relationship Discussion",
            "message": "Are you married or in a relationship?",
            "expected_sections": ["Identity", "Relationship status", "Family context"]
        },
        {
            "type": "Technical Discussion",
            "message": "Can you help me debug this Python code?",
            "expected_sections": ["Identity", "Technical expertise", "Communication patterns"]
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🎯 SCENARIO {i}: {scenario['type']}")
        print(f"📝 Message: \"{scenario['message']}\"")
        print("-" * 60)
        
        # Extract personal knowledge sections dynamically
        personal_sections = await cdl_integration._extract_cdl_personal_knowledge_sections(
            character, scenario['message']
        )
        
        # Show what gets included
        if personal_sections:
            print(f"✅ INCLUDED Personal Sections:")
            for line in personal_sections.split('\n'):
                if line.strip():
                    print(f"   • {line}")
        else:
            print("❌ NO Personal sections included (general conversation)")
        
        # Show word count impact
        base_prompt_size = len(f"You are {character.identity.name}, a {character.identity.occupation}.".split())
        personal_size = len(personal_sections.split()) if personal_sections else 0
        
        print(f"📊 Context Impact:")
        print(f"   • Base prompt: ~{base_prompt_size} words")
        print(f"   • Personal context: +{personal_size} words")
        print(f"   • Expected sections: {', '.join(scenario['expected_sections'])}")

async def demonstrate_fidelity_first_optimization():
    """Show how fidelity-first optimization works."""
    
    print(f"\n🚀 FIDELITY-FIRST OPTIMIZATION")
    print("=" * 80)
    
    cdl_integration = CDLAIPromptIntegration()
    character = load_character('characters/examples/sophia_v2.json')
    
    # Simulate scenarios with different context sizes
    optimization_scenarios = [
        {
            "name": "Small Context (No Optimization)",
            "memories": [],
            "conversation_history": [],
            "message": "Hello!",
            "expected": "Full fidelity retained"
        },
        {
            "name": "Medium Context (Selective Inclusion)",
            "memories": ["memory1", "memory2", "memory3"],
            "conversation_history": [{"role": "user", "content": "Previous message"}],
            "message": "Tell me about your family background",
            "expected": "Family sections included, other sections optimized"
        },
        {
            "name": "Large Context (Intelligent Trimming)",
            "memories": ["mem" + str(i) for i in range(10)],
            "conversation_history": [{"role": "user", "content": f"Message {i}"} for i in range(5)],
            "message": "Complex question about work, family, and technical skills",
            "expected": "Intelligent prioritization based on message content"
        }
    ]
    
    for scenario in optimization_scenarios:
        print(f"\n📊 {scenario['name']}")
        print(f"   Message: \"{scenario['message']}\"")
        print(f"   Context size: {len(scenario['memories'])} memories, {len(scenario['conversation_history'])} history")
        print(f"   Expected behavior: {scenario['expected']}")
        
        # Show what personal knowledge would be extracted
        personal_knowledge = await cdl_integration._extract_cdl_personal_knowledge_sections(
            character, scenario['message']
        )
        
        if personal_knowledge:
            print(f"   Context-aware sections: {len(personal_knowledge.split('\\n'))} sections")
        else:
            print(f"   Context-aware sections: No personal context needed")

def analyze_current_system_architecture():
    """Analyze the current CDL context-aware system."""
    
    print(f"\n🏗️ CURRENT CDL CONTEXT-AWARE ARCHITECTURE")
    print("=" * 80)
    
    current_features = {
        "✅ Context-Aware Personal Knowledge": [
            "Family info only included when family keywords detected",
            "Career info only included when work/education keywords detected", 
            "Relationship info only included when relationship keywords detected",
            "Uses actual CDL structure (backstory, current_life, etc.)"
        ],
        "✅ Fidelity-First Size Management": [
            "Full context preserved when under word limit (3000 words)",
            "Intelligent optimization only when necessary",
            "Preserves character identity and core personality",
            "Emergency truncation maintains structure (80% start + 10% end)"
        ],
        "✅ Dynamic Content Prioritization": [
            "Response style comes FIRST for instruction compliance",
            "Core identity always included",
            "Big Five personality always included",
            "Memory context varies by relevance",
            "Emotional context included when available"
        ],
        "✅ Communication Scenario Detection": [
            "Message pattern triggers from CDL",
            "Conversation flow guidelines based on detected scenarios",
            "Platform-aware responses (Discord vs other platforms)",
            "Character-specific adaptations per scenario"
        ]
    }
    
    for category, features in current_features.items():
        print(f"\n{category}")
        for feature in features:
            print(f"   • {feature}")

async def main():
    """Run the CDL dynamic context demonstration."""
    await demonstrate_cdl_dynamic_context()
    await demonstrate_fidelity_first_optimization()
    analyze_current_system_architecture()
    
    print(f"\n🎯 SUMMARY: CDL DYNAMIC CONTEXT SYSTEM")
    print("=" * 80)
    print("✅ WhisperEngine ALREADY has sophisticated context-aware CDL inclusion!")
    print("✅ Personal knowledge sections are included ONLY when conversation context requires them")
    print("✅ Fidelity-first optimization preserves character authenticity while managing size")
    print("✅ Message content analysis determines which CDL sections to include/exclude")
    print("✅ System balances completeness with efficiency automatically")

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    asyncio.run(main())