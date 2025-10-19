#!/usr/bin/env python3
"""
Phase 4 Intelligence Automated Test Suite

Tests all Phase 4 Human-Like Intelligence features:
- Adaptive Conversation Modes
- Interaction Type Detection  
- Enhanced Memory Processing
- Relationship Depth Tracking
- Context-Aware Response Generation
- Advanced Components (4.1, 4.2, 4.3)
"""

import aiohttp
import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase4IntelligenceTestSuite:
    """Comprehensive automated test suite for Phase 4 Intelligence features."""
    
    def __init__(self, bot_name: str = None, test_user_id: str = "test_user_phase4"):
        self.bot_name = bot_name or "elena"
        self.base_url = self._get_bot_url()
        self.test_user_id = test_user_id
        self.test_results = []
        self.relationship_progression_state = "new_acquaintance"
    
    def _get_bot_url(self) -> str:
        """Get the correct bot URL based on bot name."""
        bot_ports = {
            "elena": 9091,
            "marcus": 9092, 
            "ryan": 9093,
            "dream": 9094,
            "gabriel": 9095,
            "sophia": 9096,
            "jake": 9097,
            "dotty": 9098,
            "aetheris": 9099,
            "aethys": 3007
        }
        
        port = bot_ports.get(self.bot_name.lower(), 9091)
        return f"http://localhost:{port}"
    
    async def send_message(self, message: str, expected_features: List[str] = None, 
                          test_name: str = None, delay_before: float = 0.0) -> Dict[str, Any]:
        """Send message to bot and analyze response for Phase 4 features."""
        
        if delay_before > 0:
            await asyncio.sleep(delay_before)
        
        logger.info(f"🧪 TEST: {test_name}")
        logger.info(f"📤 SENDING: {message}")
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "user_id": self.test_user_id,
                    "message": message,
                    "username": "TestUser",
                    "metadata_level": "extended"  # Request extended metadata for comprehensive testing
                }
                
                async with session.post(
                    f"{self.base_url}/api/chat",
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30.0)
                ) as response:
                    if response.status != 200:
                        logger.error(f"❌ Request failed with status {response.status}")
                        return {"success": False, "error": f"HTTP {response.status}"}
                    
                    result = await response.json()
                    
                    # Analyze for Phase 4 features
                    analysis = await self._analyze_response_for_phase4(result, expected_features or [])
                    
                    # Log analysis results
                    await self._log_test_result(test_name, message, result, analysis)
                    
                    return {
                        "success": True,
                        "test_name": test_name,
                        "message": message,
                        "response": result.get("response", ""),
                        "analysis": analysis,
                        "raw_result": result
                    }
                    
        except Exception as e:
            logger.error(f"❌ Request failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_response_for_phase4(self, result: Dict[str, Any], 
                                          expected_features: List[str]) -> Dict[str, Any]:
        """Analyze bot response for Phase 4 intelligence features."""
        
        analysis = {
            "adaptive_conversation_modes": False,
            "interaction_type_detection": False,
            "enhanced_memory_processing": False,
            "relationship_depth_tracking": False,
            "context_aware_response": False,
            "human_like_integration": False,
            "response_quality": 0,
            "detected_features": [],
            "missing_features": [],
            "phase4_indicators": []
        }
        
        response_text = result.get("response", "").lower()
        metadata = result.get("metadata", {})
        ai_components = metadata.get("ai_components", {})
        
        # Check for Phase 4 intelligence in metadata using current field names
        conversation_intelligence = ai_components.get("conversation_intelligence", {})
        unified_intelligence = ai_components.get("unified_character_intelligence", {})
        character_performance = ai_components.get("character_performance_intelligence", {})
        conversation_analysis = ai_components.get("conversation_analysis", {})
        
        # Check for any intelligence system presence
        if conversation_intelligence or unified_intelligence or character_performance:
            analysis["detected_features"].append("phase4_context_available")
            analysis["phase4_indicators"].append("Intelligence systems detected in metadata")
            
            # Check conversation mode from conversation_analysis
            if conversation_analysis:
                conversation_mode = conversation_analysis.get("mode")
                if conversation_mode in ["human_like", "analytical", "balanced", "adaptive", "standard"]:
                    analysis["adaptive_conversation_modes"] = True
                    analysis["detected_features"].append("conversation_mode_detection")
                    analysis["phase4_indicators"].append(f"Conversation mode: {conversation_mode}")
                
                # Check interaction type
                interaction_type = conversation_analysis.get("interaction_type")
                if interaction_type in ["general", "problem_solving", "emotional_support", "information_seeking", "creative_collaboration", "assistance_request"]:
                    analysis["interaction_type_detection"] = True
                    analysis["detected_features"].append("interaction_type_detection")
                    analysis["phase4_indicators"].append(f"Interaction type: {interaction_type}")
            
            # Check for unified intelligence coordination
            if unified_intelligence:
                enhanced_response = unified_intelligence.get("enhanced_response")
                if enhanced_response:
                    analysis["human_like_integration"] = True
                    analysis["detected_features"].append("unified_intelligence_active")
                    analysis["phase4_indicators"].append("Unified character intelligence coordination active")
        
        # Check for adaptive conversation mode indicators in response
        analytical_indicators = [
            "analysis shows", "research indicates", "data suggests", "studies demonstrate",
            "technical specifications", "according to", "empirical evidence", "quantitative",
            "statistical", "methodology", "algorithm", "parameters"
        ]
        
        human_like_indicators = [
            "i understand how you feel", "that sounds exciting", "i'm so proud",
            "that must be", "i can imagine", "sounds like you", "i feel",
            "my heart", "emotional", "personal", "share this with you"
        ]
        
        # Check for mode adaptation
        analytical_count = sum(1 for indicator in analytical_indicators if indicator in response_text)
        human_like_count = sum(1 for indicator in human_like_indicators if indicator in response_text)
        
        if analytical_count >= 2:
            analysis["adaptive_conversation_modes"] = True
            analysis["detected_features"].append("analytical_mode_response")
            analysis["phase4_indicators"].append(f"Analytical mode indicators: {analytical_count}")
        
        if human_like_count >= 2:
            analysis["adaptive_conversation_modes"] = True
            analysis["detected_features"].append("human_like_mode_response")
            analysis["phase4_indicators"].append(f"Human-like mode indicators: {human_like_count}")
        
        # Check for enhanced memory processing indicators
        memory_indicators = [
            "remember when", "as we discussed", "building on our", "continuing from",
            "last time we", "you mentioned before", "from our previous", "following up on"
        ]
        
        # Check current intelligence systems for memory processing
        if conversation_intelligence or unified_intelligence:
            # Check for enhanced emotion analysis
            if conversation_intelligence.get("empathy_response_calibration"):
                analysis["enhanced_memory_processing"] = True
                analysis["detected_features"].append("enhanced_memory_processing")
                analysis["phase4_indicators"].append("Enhanced emotion analysis detected")
            
            # Check for context switches which indicate memory processing
            context_switches = ai_components.get("context_switches", [])
            if context_switches:
                analysis["enhanced_memory_processing"] = True
                analysis["detected_features"].append("memory_continuity")
                analysis["phase4_indicators"].append(f"Context switches: {len(context_switches)}")
        
        # Also check textual indicators
        for indicator in memory_indicators:
            if indicator in response_text:
                analysis["enhanced_memory_processing"] = True
                analysis["detected_features"].append("memory_continuity")
                analysis["phase4_indicators"].append(f"Memory continuity: '{indicator}'")
                break
        
        # Check for relationship depth tracking indicators  
        relationship_indicators = [
            "getting to know you", "our friendship", "trust between us", "feel comfortable",
            "personal sharing", "open up", "closer", "bond", "connection", "relationship"
        ]
        
        for indicator in relationship_indicators:
            if indicator in response_text:
                analysis["relationship_depth_tracking"] = True
                analysis["detected_features"].append("relationship_awareness")
                analysis["phase4_indicators"].append(f"Relationship awareness: '{indicator}'")
                break
        
        # Check for context-aware response generation
        context_indicators = [
            "considering both", "taking into account", "balancing", "multiple aspects",
            "complex situation", "nuanced", "multifaceted", "various factors"
        ]
        
        # Check current intelligence systems for context-aware features
        if conversation_analysis or unified_intelligence:
            # Check for comprehensive context analysis
            comprehensive_context = ai_components.get("comprehensive_context")
            if comprehensive_context:
                analysis["context_aware_response"] = True
                analysis["detected_features"].append("context_aware_response")
                analysis["phase4_indicators"].append("Comprehensive context analysis detected")
            
            # Check for context switches
            context_switches = ai_components.get("context_switches", [])
            if context_switches:
                analysis["context_aware_response"] = True
                analysis["detected_features"].append("multi_context_integration")
                analysis["phase4_indicators"].append(f"Context switches: {len(context_switches)}")
        
        # Also check textual indicators
        for indicator in context_indicators:
            if indicator in response_text:
                analysis["context_aware_response"] = True
                analysis["detected_features"].append("multi_context_integration")
                analysis["phase4_indicators"].append(f"Multi-context integration: '{indicator}'")
                break
        
        # Check for human-like integration patterns
        if unified_intelligence:
            performance_metrics = unified_intelligence.get("performance_metrics", {})
            systems_utilized = performance_metrics.get("systems_utilized", 0)
            if systems_utilized >= 1:  # Any system utilization indicates integration
                analysis["human_like_integration"] = True
                analysis["detected_features"].append("human_like_integration")
                analysis["phase4_indicators"].append(f"Systems utilized: {systems_utilized}")
        
        # Also consider multiple features as human-like integration
        if len(analysis["detected_features"]) >= 3:
            analysis["human_like_integration"] = True
            if "human_like_integration" not in analysis["detected_features"]:
                analysis["detected_features"].append("human_like_integration")
        
        # Calculate response quality score
        feature_count = len(analysis["detected_features"])
        if feature_count >= 6:
            analysis["response_quality"] = 5
        elif feature_count >= 4:
            analysis["response_quality"] = 4
        elif feature_count >= 2:
            analysis["response_quality"] = 3
        elif feature_count >= 1:
            analysis["response_quality"] = 2
        else:
            analysis["response_quality"] = 1
        
        # Check for missing expected features
        for feature in expected_features:
            if feature not in analysis["detected_features"]:
                analysis["missing_features"].append(feature)
        
        return analysis
    
    async def _log_test_result(self, test_name: str, message: str, result: Dict[str, Any], 
                              analysis: Dict[str, Any]) -> None:
        """Log detailed test results."""
        
        logger.info(f"📊 ANALYSIS for '{test_name}':")
        logger.info(f"   Adaptive Conversation Modes: {'✅' if analysis['adaptive_conversation_modes'] else '❌'}")
        logger.info(f"   Interaction Type Detection: {'✅' if analysis['interaction_type_detection'] else '❌'}")
        logger.info(f"   Enhanced Memory Processing: {'✅' if analysis['enhanced_memory_processing'] else '❌'}")
        logger.info(f"   Relationship Depth Tracking: {'✅' if analysis['relationship_depth_tracking'] else '❌'}")
        logger.info(f"   Context-Aware Response: {'✅' if analysis['context_aware_response'] else '❌'}")
        logger.info(f"   Human-Like Integration: {'✅' if analysis['human_like_integration'] else '❌'}")
        logger.info(f"   Response Quality: {analysis['response_quality']}/5")
        
        if analysis["phase4_indicators"]:
            logger.info(f"   Phase4+ Indicators:")
            for indicator in analysis["phase4_indicators"]:
                logger.info(f"     • {indicator}")
        
        if analysis["missing_features"]:
            logger.warning(f"   Missing Features: {analysis['missing_features']}")
        
        logger.info(f"📝 RESPONSE: {result.get('response', '')[:200]}...")
        logger.info("=" * 80)
        
        # Store result for final report
        self.test_results.append({
            "test_name": test_name,
            "message": message,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        })
    
    async def run_adaptive_conversation_mode_tests(self):
        """Test adaptive conversation mode switching."""
        logger.info("🔄 STARTING ADAPTIVE CONVERSATION MODE TESTS")
        
        # Analytical Mode Test
        await self.send_message(
            "I need a detailed scientific analysis of microplastic impact on marine food chains. Please include molecular-level effects, bioaccumulation patterns, and quantitative data on ecosystem disruption.",
            expected_features=["analytical_mode_response", "conversation_mode_detection"],
            test_name="Analytical Mode Trigger",
            delay_before=1.0
        )
        
        # Human-Like Mode Test
        await self.send_message(
            "I just had the most amazing experience snorkeling today! I saw a sea turtle and it felt so magical. I wish I could share this feeling with someone who really understands the ocean.",
            expected_features=["human_like_mode_response", "conversation_mode_detection"],
            test_name="Human-Like Mode Trigger",
            delay_before=2.0
        )
        
        # Balanced Mode Test
        await self.send_message(
            "I'm working on a research project about coral bleaching, but I'm also feeling overwhelmed by the environmental crisis. Can you help me understand the science while also supporting me emotionally?",
            expected_features=["conversation_mode_detection", "multi_context_integration"],
            test_name="Balanced Mode Trigger",
            delay_before=2.0
        )
    
    async def run_interaction_type_detection_tests(self):
        """Test interaction type recognition and appropriate responses."""
        logger.info("🔍 STARTING INTERACTION TYPE DETECTION TESTS")
        
        # Emotional Support Detection
        await self.send_message(
            "I'm going through a really difficult breakup right now. I feel lost and don't know how to move forward. Everything reminds me of my ex and I can't seem to get my life back on track.",
            expected_features=["interaction_type_detection", "human_like_mode_response"],
            test_name="Emotional Support Detection",
            delay_before=1.0
        )
        
        # Problem Solving Detection
        await self.send_message(
            "My marine biology research is failing and I'm behind on my thesis deadline. My advisor is disappointed and I don't know what I'm doing wrong. I need to fix this fast or I'll lose my funding.",
            expected_features=["interaction_type_detection", "analytical_mode_response"],
            test_name="Problem Solving Detection",
            delay_before=2.0
        )
        
        # Creative Collaboration Detection
        await self.send_message(
            "I'm designing an underwater photography exhibit and want to create something unique that captures the magic of marine life. Can we brainstorm some innovative display ideas together?",
            expected_features=["interaction_type_detection", "multi_context_integration"],
            test_name="Creative Collaboration Detection",
            delay_before=2.0
        )
        
        # Information Seeking Detection
        await self.send_message(
            "I'm researching the latest trends in marine conservation technology. What are the most promising innovations, current research directions, and emerging methodologies?",
            expected_features=["interaction_type_detection", "analytical_mode_response"],
            test_name="Information Seeking Detection",
            delay_before=2.0
        )
    
    async def run_enhanced_memory_processing_tests(self):
        """Test human-like memory retrieval and pattern recognition."""
        logger.info("🧠 STARTING ENHANCED MEMORY PROCESSING TESTS")
        
        # Memory Pattern Recognition Test (sequential)
        await self.send_message(
            "I'm starting to study marine biology and I'm really passionate about ocean conservation.",
            expected_features=["conversation_mode_detection"],
            test_name="Memory Baseline (Marine Biology Interest)",
            delay_before=1.0
        )
        
        await self.send_message(
            "Remember I mentioned my interest in marine biology? Well, I just got accepted to an marine science program! Can you help me understand what this journey will be like?",
            expected_features=["memory_continuity", "enhanced_memory_processing"],
            test_name="Memory Pattern Recognition (Callback)",
            delay_before=2.0
        )
        
        # Emotional Memory Prioritization
        await self.send_message(
            "I'm feeling anxious about starting my marine biology studies. What if I'm not smart enough? What if I fail?",
            expected_features=["memory_continuity", "human_like_mode_response"],
            test_name="Emotional Memory Prioritization",
            delay_before=2.0
        )
    
    async def run_relationship_depth_tracking_tests(self):
        """Test progressive relationship building."""
        logger.info("💝 STARTING RELATIONSHIP DEPTH TRACKING TESTS")
        
        # New Acquaintance Level
        await self.send_message(
            "Hi, I'm new to marine biology and interested in learning more about ocean conservation.",
            expected_features=["conversation_mode_detection"],
            test_name="Relationship Level: New Acquaintance",
            delay_before=1.0
        )
        
        # Growing Friendship Level
        await self.send_message(
            "Thanks for all your help learning about marine biology. I'm starting to feel really passionate about ocean conservation because of our conversations.",
            expected_features=["relationship_awareness", "memory_continuity"],
            test_name="Relationship Level: Growing Friendship",
            delay_before=2.0
        )
        
        # Deeper Relationship Level
        await self.send_message(
            "I got accepted to a marine biology program! I wanted to share this with you because you've been such an inspiration in helping me find my path.",
            expected_features=["relationship_awareness", "human_like_mode_response"],
            test_name="Relationship Level: Close Friend",
            delay_before=2.0
        )
    
    async def run_context_aware_response_tests(self):
        """Test multi-dimensional context integration."""
        logger.info("🔀 STARTING CONTEXT-AWARE RESPONSE TESTS")
        
        # Multi-Context Integration Test
        await self.send_message(
            "I just got back from my first underwater photography session in a coral reef. The colors were incredible but I struggled with the technical camera settings in the underwater environment. Also, I'm planning a solo marine research trip next month and feeling both excited and nervous about the adventure.",
            expected_features=["multi_context_integration", "conversation_mode_detection"],
            test_name="Multi-Context Integration (Technical + Emotional + Adventure)",
            delay_before=1.0
        )
        
        # Academic Context Integration Test
        await self.send_message(
            "I'm working on my thesis about marine ecosystem restoration, but I'm also dealing with impostor syndrome and wondering if my research actually matters. The pressure to publish is overwhelming.",
            expected_features=["multi_context_integration", "analytical_mode_response", "human_like_mode_response"],
            test_name="Academic Context Integration (Research + Emotional + Career)",
            delay_before=2.0
        )
    
    async def run_advanced_phase4_components_tests(self):
        """Test Phase 4.1, 4.2, 4.3 advanced components."""
        logger.info("🚀 STARTING ADVANCED PHASE4 COMPONENTS TESTS")
        
        # Phase 4.1: Human-Like Integration Test
        await self.send_message(
            "I need both analytical help and emotional support. Can you help me understand the technical aspects of coral reef restoration while also helping me deal with my anxiety about climate change?",
            expected_features=["human_like_integration", "multi_context_integration"],
            test_name="Phase 4.1: Human-Like Integration",
            delay_before=1.0
        )
        
        # Phase 4.2: Advanced Thread Management Test
        await self.send_message(
            "Continuing our conversation about marine conservation, I've been thinking about what you said regarding coral restoration and want to explore ocean acidification's impact further.",
            expected_features=["memory_continuity", "enhanced_memory_processing"],
            test_name="Phase 4.2: Advanced Thread Management",
            delay_before=2.0
        )
        
        # Phase 4.3: Proactive Engagement Test (simulated)
        await self.send_message(
            "Hi again, it's been a while since we last chatted.",
            expected_features=["relationship_awareness", "memory_continuity"],
            test_name="Phase 4.3: Proactive Engagement Response",
            delay_before=2.0
        )
    
    async def run_all_tests(self):
        """Run complete Phase 4 intelligence test suite."""
        
        logger.info("🚀 STARTING FULL PHASE 4 INTELLIGENCE TEST SUITE")
        logger.info(f"🎯 Target: {self.base_url}")
        logger.info(f"👤 Test User: {self.test_user_id}")
        logger.info("=" * 80)
        
        try:
            # Health check
            await self._check_bot_health()
            
            start_time = time.time()
            
            # Run all test categories
            await self.run_adaptive_conversation_mode_tests()
            await self.run_interaction_type_detection_tests()  
            await self.run_enhanced_memory_processing_tests()
            await self.run_relationship_depth_tracking_tests()
            await self.run_context_aware_response_tests()
            await self.run_advanced_phase4_components_tests()
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Generate final report
            await self._generate_final_report(duration)
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            return False
        
        return True
    
    async def _check_bot_health(self):
        """Check if bot is healthy and responsive."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/health") as response:
                if response.status != 200:
                    raise Exception(f"Bot health check failed: {response.status}")
                logger.info("✅ Bot health check passed")
    
    async def _generate_final_report(self, duration: float):
        """Generate comprehensive test report."""
        
        total_tests = len(self.test_results)
        
        # Calculate feature detection rates
        adaptive_modes_tests = sum(1 for r in self.test_results if r["analysis"]["adaptive_conversation_modes"])
        interaction_type_tests = sum(1 for r in self.test_results if r["analysis"]["interaction_type_detection"])
        memory_processing_tests = sum(1 for r in self.test_results if r["analysis"]["enhanced_memory_processing"])
        relationship_tracking_tests = sum(1 for r in self.test_results if r["analysis"]["relationship_depth_tracking"])
        context_aware_tests = sum(1 for r in self.test_results if r["analysis"]["context_aware_response"])
        human_like_tests = sum(1 for r in self.test_results if r["analysis"]["human_like_integration"])
        
        # Calculate average quality
        avg_quality = sum(r["analysis"]["response_quality"] for r in self.test_results) / total_tests if total_tests > 0 else 0
        
        phase4_effectiveness = {
            "adaptive_conversation_modes_rate": (adaptive_modes_tests / total_tests * 100) if total_tests > 0 else 0,
            "interaction_type_detection_rate": (interaction_type_tests / total_tests * 100) if total_tests > 0 else 0,
            "enhanced_memory_processing_rate": (memory_processing_tests / total_tests * 100) if total_tests > 0 else 0,
            "relationship_depth_tracking_rate": (relationship_tracking_tests / total_tests * 100) if total_tests > 0 else 0,
            "context_aware_response_rate": (context_aware_tests / total_tests * 100) if total_tests > 0 else 0,
            "human_like_integration_rate": (human_like_tests / total_tests * 100) if total_tests > 0 else 0,
            "average_quality_score": avg_quality
        }
        
        logger.info("📊 FINAL REPORT SUMMARY")
        logger.info(f"   Total Tests: {total_tests}")
        logger.info(f"   Adaptive Conversation Modes: {adaptive_modes_tests}/{total_tests} ({phase4_effectiveness['adaptive_conversation_modes_rate']:.1f}%)")
        logger.info(f"   Interaction Type Detection: {interaction_type_tests}/{total_tests} ({phase4_effectiveness['interaction_type_detection_rate']:.1f}%)")
        logger.info(f"   Enhanced Memory Processing: {memory_processing_tests}/{total_tests} ({phase4_effectiveness['enhanced_memory_processing_rate']:.1f}%)")
        logger.info(f"   Relationship Depth Tracking: {relationship_tracking_tests}/{total_tests} ({phase4_effectiveness['relationship_depth_tracking_rate']:.1f}%)")
        logger.info(f"   Context-Aware Response: {context_aware_tests}/{total_tests} ({phase4_effectiveness['context_aware_response_rate']:.1f}%)")
        logger.info(f"   Human-Like Integration: {human_like_tests}/{total_tests} ({phase4_effectiveness['human_like_integration_rate']:.1f}%)")
        logger.info(f"   Average Quality Score: {avg_quality:.2f}/5")
        logger.info("🎯 TEST SUITE COMPLETED")
        logger.info(f"⏱️  Total Duration: {duration:.2f} seconds")
        
        # Determine pass/fail
        passing_threshold = 70.0  # 70% feature detection rate minimum
        avg_feature_rate = sum([
            phase4_effectiveness['adaptive_conversation_modes_rate'],
            phase4_effectiveness['interaction_type_detection_rate'],
            phase4_effectiveness['enhanced_memory_processing_rate'],
            phase4_effectiveness['relationship_depth_tracking_rate'],
            phase4_effectiveness['context_aware_response_rate'],
            phase4_effectiveness['human_like_integration_rate']
        ]) / 6
        
        if avg_feature_rate >= passing_threshold and avg_quality >= 3.0:
            logger.info("✅ Phase 4 Intelligence tests PASSED")
            return True
        else:
            logger.error("❌ Phase 4 Intelligence tests FAILED or performance below threshold")
            return False


async def main():
    """Run Phase 4 Intelligence automated tests."""
    import os
    
    # Get bot name from environment variable or default to elena
    bot_name = os.environ.get('DISCORD_BOT_NAME', 'elena').lower()
    
    test_suite = Phase4IntelligenceTestSuite(
        bot_name=bot_name,
        test_user_id=f"test_user_phase4_{bot_name}"
    )
    
    logger.info("🤖 Testing bot: %s at %s", bot_name.upper(), test_suite.base_url)
    
    result = await test_suite.run_all_tests()
    return result


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)