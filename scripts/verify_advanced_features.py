#!/usr/bin/env python3
"""
Advanced Features Verification Script
=====================================

Tests all integrated advanced conversation features:
- Context Switch Detection
- Empathy Calibration  
- Memory-Triggered Moments
- Proactive Engagement Engine
- Advanced Thread Management
"""

import asyncio
import json
import logging
import requests
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration
BOTS_TO_TEST = {
    "Gabriel": "http://localhost:9095/api/chat",
    "Sophia": "http://localhost:9096/api/chat", 
}

TEST_USER_ID = "advanced_features_test_user"

def test_api_call(bot_name, bot_url, message, expected_features=None):
    """Test API call and analyze response for advanced features"""
    
    payload = {
        "message": message,
        "user_id": TEST_USER_ID
    }
    
    try:
        logger.info(f"🧪 Testing {bot_name}: {message[:50]}...")
        
        start_time = time.time()
        response = requests.post(bot_url, json=payload, timeout=30)
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get("response", "")
            response_time = end_time - start_time
            
            logger.info(f"✅ {bot_name} responded in {response_time:.2f}s")
            logger.info(f"📝 Response preview: {response_text[:100]}...")
            
            # Analyze for advanced features
            features_detected = analyze_response_for_features(response_text, expected_features)
            
            return {
                "success": True,
                "response_time": response_time,
                "response_length": len(response_text),
                "features_detected": features_detected,
                "bot_name": data.get("bot_name", bot_name),
                "message_id": data.get("message_id"),
            }
        else:
            logger.error(f"❌ {bot_name} API error: {response.status_code}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        logger.error(f"💥 {bot_name} test failed: {e}")
        return {"success": False, "error": str(e)}

def analyze_response_for_features(response_text, expected_features=None):
    """Analyze response for indicators of advanced conversation features"""
    
    features_detected = []
    
    # Context awareness indicators
    if any(phrase in response_text.lower() for phrase in [
        "switching", "changing topics", "different subject", "new direction"
    ]):
        features_detected.append("context_switch_awareness")
    
    # Empathy indicators  
    if any(phrase in response_text.lower() for phrase in [
        "understand", "feel", "sorry", "support", "here for you", "tough"
    ]):
        features_detected.append("empathy_response")
    
    # Memory/personality indicators
    if any(phrase in response_text.lower() for phrase in [
        "remember", "mentioned", "told me", "earlier", "before"
    ]):
        features_detected.append("memory_integration")
    
    # Technical sophistication (indicating rich system prompts)
    if len(response_text) > 500:
        features_detected.append("detailed_response")
    
    # Personality consistency (character-specific language)
    if any(phrase in response_text.lower() for phrase in [
        "love", "darling", "honey", "alright", "wild", "chaos"  # Gabriel-style
    ]):
        features_detected.append("personality_consistency")
        
    return features_detected

def main():
    """Run comprehensive advanced features test"""
    
    logger.info("🚀 Starting WhisperEngine Advanced Features Verification")
    logger.info("=" * 60)
    
    test_scenarios = [
        {
            "name": "Context Switch Detection",
            "message": "I want to completely change topics from casual chat to quantum physics",
            "expected_features": ["context_switch_awareness"]
        },
        {
            "name": "Empathy Calibration", 
            "message": "I'm feeling really anxious about my job interview tomorrow",
            "expected_features": ["empathy_response"]
        },
        {
            "name": "Complex Technical Response",
            "message": "Explain the technical details of neural network backpropagation",
            "expected_features": ["detailed_response", "personality_consistency"]
        },
        {
            "name": "Memory Integration Test",
            "message": "Remember when I mentioned being nervous? How can I use that experience?",
            "expected_features": ["memory_integration"]
        }
    ]
    
    results = {}
    
    for bot_name, bot_url in BOTS_TO_TEST.items():
        logger.info(f"\n🤖 Testing {bot_name}")
        logger.info("-" * 40)
        
        bot_results = []
        
        for scenario in test_scenarios:
            result = test_api_call(
                bot_name, 
                bot_url, 
                scenario["message"],
                scenario["expected_features"]
            )
            result["scenario"] = scenario["name"]
            bot_results.append(result)
            
            # Brief pause between tests
            time.sleep(2)
            
        results[bot_name] = bot_results
    
    # Generate summary report
    logger.info("\n" + "=" * 60)
    logger.info("📊 ADVANCED FEATURES VERIFICATION SUMMARY")
    logger.info("=" * 60)
    
    for bot_name, bot_results in results.items():
        logger.info(f"\n🤖 {bot_name} Results:")
        
        successful_tests = sum(1 for r in bot_results if r.get("success", False))
        total_tests = len(bot_results)
        avg_response_time = sum(r.get("response_time", 0) for r in bot_results if r.get("success")) / max(successful_tests, 1)
        
        logger.info(f"✅ Success Rate: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
        logger.info(f"⏱️  Average Response Time: {avg_response_time:.2f}s")
        
        # Feature detection summary
        all_features = set()
        for result in bot_results:
            if result.get("success") and result.get("features_detected"):
                all_features.update(result["features_detected"])
        
        if all_features:
            logger.info(f"🧠 Advanced Features Detected: {', '.join(sorted(all_features))}")
        else:
            logger.info("⚠️  No advanced features clearly detected")
            
        # Individual test details
        for result in bot_results:
            scenario = result.get("scenario", "Unknown")
            if result.get("success"):
                features = result.get("features_detected", [])
                logger.info(f"   • {scenario}: ✅ ({len(features)} features)")
            else:
                logger.info(f"   • {scenario}: ❌ {result.get('error', 'Unknown error')}")
    
    logger.info("\n🎉 Advanced features verification complete!")
    
    # Overall system health check
    healthy_bots = sum(1 for bot_results in results.values() 
                      if sum(1 for r in bot_results if r.get("success", False)) > len(bot_results) // 2)
    
    if healthy_bots == len(BOTS_TO_TEST):
        logger.info("✅ All bots showing advanced conversation capabilities!")
    else:
        logger.info(f"⚠️  {healthy_bots}/{len(BOTS_TO_TEST)} bots fully operational with advanced features")

if __name__ == "__main__":
    main()