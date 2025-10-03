#!/usr/bin/env python3
"""
Test script to verify Dotty's CDL response_style is correctly read by the AI integration system
"""

import os
import sys
sys.path.append('.')

# Set environment for Dotty
os.environ['CDL_DEFAULT_CHARACTER'] = 'characters/examples/dotty.json'

# Test CDL Manager
print("🧪 Testing CDL Manager...")
from src.characters.cdl.manager import get_response_style, get_conversation_flow_guidelines

guidelines = get_conversation_flow_guidelines()
print(f"Conversation guidelines found: {bool(guidelines)}")

response_style = get_response_style()
print(f"Response style found: {bool(response_style)}")

if response_style:
    print(f"✅ Response style keys: {list(response_style.keys())}")
    core_principles = response_style.get('core_principles', [])
    print(f"✅ Core principles count: {len(core_principles)}")
    if core_principles:
        print(f"✅ First core principle: {core_principles[0][:60]}...")
    
    char_adaptations = response_style.get('character_specific_adaptations', [])
    print(f"✅ Character adaptations count: {len(char_adaptations)}")
    if char_adaptations:
        print(f"✅ First adaptation: {char_adaptations[0][:60]}...")

print("\n🎭 Testing CDL AI Integration...")
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration

cdl_integration = CDLAIPromptIntegration()
try:
    # Test the integration system
    test_prompt = cdl_integration._extract_cdl_response_style(None, "TestUser")
    print(f"CDL AI Integration response style extraction: {bool(test_prompt)}")
    if test_prompt:
        if "ALWAYS respond as Dotty" in test_prompt:
            print("✅ Found Dotty character identity instructions!")
        if "signature memory-infused cocktails" in test_prompt:
            print("✅ Found signature drinks instructions!")
        if "Echo Sour" in test_prompt:
            print("✅ Found specific drink names!")
    
except Exception as e:
    print(f"CDL AI Integration test failed: {e}")

print("\n🎯 SUMMARY:")
print(f"CDL Manager working: {bool(response_style)}")
print(f"Character instructions accessible: {'ALWAYS respond as Dotty' in str(response_style)}")
print(f"Signature drinks accessible: {'Echo Sour' in str(response_style)}")

if response_style and 'ALWAYS respond as Dotty' in str(response_style):
    print("🎉 SUCCESS: Dotty's character instructions are now accessible to the AI system!")
else:
    print("❌ ISSUE: Character instructions still not accessible")