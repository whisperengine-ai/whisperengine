#!/usr/bin/env python3
"""
Elena Rodriguez (Marine Biologist) Test Scenarios
Additional test scenarios for Elena to complement the main automated testing suite.
"""

# Elena Test Scenarios (Marine Biology Focus)
ELENA_TEST_SCENARIOS = [
    {
        "name": "Marine Ecosystem Explanation",
        "message": "Elena, can you explain how coral reefs support marine biodiversity?",
        "expected_traits": ["coral", "biodiversity", "ecosystem", "marine"],
        "category": "Marine Biology Expertise",
        "description": "Test deep marine biology knowledge and educational communication"
    },
    {
        "name": "Ocean Conservation",
        "message": "What are the biggest threats to ocean health right now?",
        "expected_traits": ["conservation", "threats", "pollution", "climate"],
        "category": "Environmental Awareness",
        "description": "Test understanding of current environmental challenges"
    },
    {
        "name": "Research Methodology",
        "message": "Elena, how do you conduct underwater research studies?",
        "expected_traits": ["research", "methodology", "underwater", "scientific"],
        "category": "Research & Scientific Method",
        "description": "Test scientific methodology and field research experience"
    },
    {
        "name": "Educational Explanation",
        "message": "I'm 12 years old and want to learn about marine biology. Where should I start?",
        "expected_traits": ["educational", "young", "learning", "encourage"],
        "category": "Educational Communication",
        "description": "Test ability to adapt communication for younger audiences"
    },
    {
        "name": "Ocean Exploration",
        "message": "What's the most exciting marine discovery you've heard about recently?",
        "expected_traits": ["discovery", "exciting", "exploration", "recent"],
        "category": "Marine Biology Expertise", 
        "description": "Test enthusiasm for marine science and current developments"
    }
]

if __name__ == "__main__":
    print("Elena Rodriguez Test Scenarios")
    print("=" * 40)
    for i, scenario in enumerate(ELENA_TEST_SCENARIOS, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   Category: {scenario['category']}")
        print(f"   Message: \"{scenario['message']}\"")
        print(f"   Expected traits: {', '.join(scenario['expected_traits'])}")
        print(f"   Description: {scenario['description']}")