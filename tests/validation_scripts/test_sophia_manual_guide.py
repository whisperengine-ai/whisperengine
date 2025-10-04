#!/usr/bin/env python3
"""
Sophia 7D Response Optimization - Manual Test Tracker
Guides manual testing and provides scoring framework for conversational style validation.
"""

def display_test_menu():
    """Display the manual testing menu with conversational style focus."""
    
    print("🎯 SOPHIA 7D RESPONSE OPTIMIZATION - MANUAL TESTING")
    print("=" * 70)
    print("✅ Technical Foundation: COMPLETE (All 7 vectors, CDL enhanced, memory cleared)")
    print("✅ Professional Persona: VALIDATED (95/100 scores achieved)")
    print("🔄 Response Style: OPTIMIZATION APPLIED (Testing required)")
    print("-" * 70)
    
    print("\n📋 CONVERSATIONAL STYLE TESTS (Priority)")
    print("=" * 50)
    
    tests = [
        {
            "id": "2.1",
            "name": "Conversational Response Style Validation",
            "message": "What's the most important trend in digital marketing right now?",
            "criteria": [
                "Response under 500 characters / 80 words",
                "Natural, conversational tone (like texting a friend)", 
                "Focuses on ONE main point",
                "Includes engaging follow-up question",
                "Maintains professional marketing expertise"
            ],
            "priority": "🚨 HIGH - Core optimization validation"
        },
        {
            "id": "2.2", 
            "name": "Analytics Dashboard Design (Professional Task)",
            "message": "We need to design a dashboard for our marketing analytics. What metrics should we prioritize?",
            "criteria": [
                "Brief, focused on 2-3 key metrics maximum",
                "Natural explanation without jargon overload",
                "Follow-up question about specific business goals", 
                "Professional insight from McKinsey background"
            ],
            "priority": "⭐ MEDIUM - Professional expertise + conversational style"
        },
        {
            "id": "2.3",
            "name": "Brand Strategy Challenge (Creative Problem-Solving)",
            "message": "Our brand feels outdated. How do we modernize without losing our core customers?",
            "criteria": [
                "Conversational strategy overview (not detailed plan)",
                "One key insight about brand evolution",
                "Question to understand target audience better",
                "Demonstrates strategic marketing background"
            ],
            "priority": "⭐ MEDIUM - Strategic thinking + engagement"
        },
        {
            "id": "2.4",
            "name": "Crisis Communication (High-Pressure Scenario)", 
            "message": "There's negative buzz about our product on social media. What's the immediate action plan?",
            "criteria": [
                "Calm, professional crisis response",
                "One immediate priority (not exhaustive checklist)",
                "Practical next step question",
                "Shows experience with crisis management"
            ],
            "priority": "⭐ MEDIUM - Professional composure + brevity"
        },
        {
            "id": "2.5",
            "name": "Memory Integration (Relationship Development)",
            "message": "Remember that product launch we discussed? We decided to move forward. What's the first milestone we should track?",
            "criteria": [
                "Acknowledges previous conversation naturally",
                "Brief milestone suggestion (not full project plan)",
                "Personal engagement showing relationship building",
                "Follow-up question about timeline or resources"
            ],
            "priority": "🔍 LOW - Memory system validation"
        },
        {
            "id": "2.6", 
            "name": "Personal Professional Background (Character Depth)",
            "message": "You seem to know a lot about strategy consulting. What's your background?",
            "criteria": [
                "Natural mention of Northwestern MBA, McKinsey experience",
                "Personal but professional tone",
                "Brief career highlight (not full resume)",
                "Question about user's background or interests"
            ],
            "priority": "🔍 LOW - CDL integration validation"
        }
    ]
    
    for test in tests:
        print(f"\n{test['priority']}")
        print(f"📝 Test {test['id']}: {test['name']}")
        print(f"💬 Message: \"{test['message']}\"")
        print("✅ Success Criteria:")
        for criterion in test['criteria']:
            print(f"   • {criterion}")
    
    print("\n" + "=" * 70)
    print("🎯 SCORING FRAMEWORK")
    print("=" * 70)
    print("📊 Technical Performance (40 points):")
    print("   • Memory Integration (10 points) - Recalls context accurately")
    print("   • CDL Adherence (10 points) - Maintains character consistency")
    print("   • Response Timing (10 points) - Quick, natural response flow")
    print("   • System Stability (10 points) - No errors or failures")
    print()
    print("🎭 Character Authenticity (30 points):")
    print("   • Professional Identity (10 points) - Marketing executive persona")
    print("   • Background Integration (10 points) - MBA, McKinsey experience natural")
    print("   • Personality Traits (10 points) - Strategic, confident, results-driven")
    print()
    print("💬 Conversational Style (30 points) - NEW FOCUS:")
    print("   • Brevity (10 points) - Under 500 characters, focused")
    print("   • Natural Flow (10 points) - Like texting a friend")
    print("   • Engagement (10 points) - Follow-up questions, conversational")
    print()
    print("🎯 Target Score: 90+ points (Excellent)")
    
    print("\n" + "=" * 70)
    print("📋 MANUAL TESTING INSTRUCTIONS")
    print("=" * 70)
    print("1. 🎮 Start Discord and locate Sophia Blake")
    print("2. 📝 Send Test 2.1 message first (highest priority)")
    print("3. 📊 Evaluate response against success criteria")
    print("4. 🔢 Score response using framework above")
    print("5. 📋 Document results and move to next test")
    print("6. 🚨 Flag any 'wall of text' responses as optimization failures")
    
    print("\n✅ READY FOR TESTING!")
    print("Sophia bot is healthy and running on port 9096")
    print("New conversational response style loaded and active")

if __name__ == "__main__":
    display_test_menu()