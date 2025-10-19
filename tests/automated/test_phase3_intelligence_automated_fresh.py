#!/usr/bin/env python3
"""
Automated Phase 3+ Intelligence Testing Suite
============================================

Automated tests for Phase 3+ intelligence features including:
- Context Switch Detection (topic shifts, emotional shifts, mode changes, urgency, intent)
- Empathy Calibration (supportive, enthusiastic, validating styles)
- AI Intelligence Guidance integration in prompts
- CDL character integration with comprehensive context

Uses HTTP API endpoints to test the same MessageProcessor pipeline that Discord uses.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import aiohttp
import sys
import os

# Add the src directory to the Python path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase3IntelligenceTestSuite:
    """Automated test suite for Phase 3+ intelligence features."""
    
    def __init__(self, base_url: str = "http://localhost:9091", test_user_id: str = "test_user_phase3_fresh_1760826262_4807"):
        self.base_url = base_url
        self.test_user_id = test_user_id
        self.session = None
        self.test_results = []
        self.conversation_history = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_message(self, message: str, expected_features: List[str] = None, 
                          test_name: str = "", delay_before: float = 1.0) -> Dict[str, Any]:
        """Send a message to the bot and analyze the response for Phase 3+ features."""
        
        if delay_before > 0:
            await asyncio.sleep(delay_before)
        
        logger.info("🧪 TEST: %s", test_name)
        logger.info("📤 SENDING: %s", message)
        
        try:
            # Send message to bot's HTTP API
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json={
                    "user_id": self.test_user_id,
                    "message": message,
                    "username": "TestUser",
                    "metadata_level": "extended"  # Request extended metadata for comprehensive testing
                },
                timeout=30
            ) as response:
                if response.status != 200:
                    logger.error("❌ HTTP Error %d: %s", response.status, await response.text())
                    return {"success": False, "error": f"HTTP {response.status}"}
                
                result = await response.json()
                
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error("❌ Request failed: %s", str(e))
            return {"success": False, "error": str(e)}
        
        # Analyze response for Phase 3+ features
        analysis = await self._analyze_response_for_phase3(result, expected_features)
        
        # Store conversation for context
        self.conversation_history.append({
            "user_message": message,
            "bot_response": result.get("response", ""),
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis
        })
        
        # Log results
        self._log_test_result(test_name, message, result, analysis)
        
        return {
            "success": True,
            "test_name": test_name,
            "message": message,
            "response": result.get("response", ""),
            "analysis": analysis,
            "raw_result": result
        }
    
    async def _analyze_response_for_phase3(self, result: Dict[str, Any], 
                                          expected_features: List[str]) -> Dict[str, Any]:
        """Analyze bot response for Phase 3+ intelligence features."""
        
        analysis = {
            "context_switches_detected": False,
            "empathy_calibration_active": False,
            "ai_intelligence_guidance": False,
            "cdl_integration": False,
            "response_quality": 0,
            "detected_features": [],
            "missing_features": [],
            "phase3_indicators": []
        }
        
        response_text = result.get("response", "").lower()
        metadata = result.get("metadata", {})
        ai_components = metadata.get("ai_components", {})
        
        # Check for context switches in metadata (Phase 3+ intelligence detection)
        context_switches = ai_components.get("context_switches", [])
        if context_switches:
            analysis["context_switches_detected"] = True
            analysis["detected_features"].append("context_switch_detection")
            for switch in context_switches:
                switch_type = switch.get("switch_type", "unknown")
                confidence = switch.get("confidence_score", 0)
                analysis["phase3_indicators"].append(
                    f"Context switch detected: {switch_type} (confidence: {confidence:.2f})"
                )
        
        # Check for context switch indicators in response text (user-facing acknowledgment)
        context_switch_indicators = [
            "i can see you've shifted", "switching gears", "changing topics",
            "i notice you've moved", "transitioning from", "shift from",
            "let me switch", "pivoting to", "moving from", "¡qué cambio"
        ]
        
        for indicator in context_switch_indicators:
            if indicator in response_text:
                analysis["detected_features"].append("context_switch_acknowledgment")
                analysis["phase3_indicators"].append(f"Response acknowledges topic shift: '{indicator}'")
                break
        
        # Check for empathy calibration indicators
        empathy_indicators = [
            "i understand", "that must be", "sounds like you're feeling",
            "i can imagine", "that's exciting", "sorry to hear",
            "congratulations", "i'm here for you", "that's wonderful"
        ]
        
        for indicator in empathy_indicators:
            if indicator in response_text:
                analysis["empathy_calibration_active"] = True
                analysis["detected_features"].append("empathy_response")
                analysis["phase3_indicators"].append(f"Empathetic response: '{indicator}'")
                break
        
        # Check for AI intelligence guidance integration
        # This would require checking logs or response metadata, but we can infer from response quality
        if len(analysis["detected_features"]) > 0:
            analysis["ai_intelligence_guidance"] = True
        
        # Check for CDL character integration (Elena-specific)
        elena_indicators = [
            "¡ay", "¡dios mío", "¡increíble", "amigo", "marine", "ocean", 
            "reef", "dive", "research", "*laughs*", "*grins*"
        ]
        
        for indicator in elena_indicators:
            if indicator in response_text:
                analysis["cdl_integration"] = True
                analysis["detected_features"].append("elena_personality")
                break
        
        # Calculate response quality score (0-5)
        quality_score = 0
        if analysis["cdl_integration"]: quality_score += 1
        if analysis["context_switches_detected"]: quality_score += 2
        if analysis["empathy_calibration_active"]: quality_score += 1
        if len(result.get("response", "")) > 50: quality_score += 1  # Adequate length
        
        analysis["response_quality"] = quality_score
        
        # Check for missing expected features
        if expected_features:
            for feature in expected_features:
                if feature not in analysis["detected_features"]:
                    analysis["missing_features"].append(feature)
        
        return analysis
    
    def _log_test_result(self, test_name: str, message: str, result: Dict[str, Any], 
                        analysis: Dict[str, Any]):
        """Log test results with detailed analysis."""
        
        logger.info(f"📊 ANALYSIS for '{test_name}':")
        logger.info(f"   Context Switches: {'✅' if analysis['context_switches_detected'] else '❌'}")
        logger.info(f"   Empathy Calibration: {'✅' if analysis['empathy_calibration_active'] else '❌'}")
        logger.info(f"   CDL Integration: {'✅' if analysis['cdl_integration'] else '❌'}")
        logger.info(f"   Response Quality: {analysis['response_quality']}/5")
        
        if analysis["phase3_indicators"]:
            logger.info(f"   Phase3+ Indicators:")
            for indicator in analysis["phase3_indicators"]:
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
    
    async def run_context_switch_tests(self):
        """Run all context switch detection tests."""
        logger.info("🔄 STARTING CONTEXT SWITCH DETECTION TESTS")
        
        # Topic Shift Test
        await self.send_message(
            "I've been studying coral reef ecosystems lately, but actually I want to ask you about Python programming instead",
            expected_features=["context_switch_acknowledgment", "elena_personality"],
            test_name="Topic Shift (Marine Biology → Programming)",
            delay_before=1.0
        )
        
        # Emotional Shift Test (requires sequence)
        await self.send_message(
            "I'm so excited about my marine biology research project!",
            expected_features=["empathy_response", "elena_personality"],
            test_name="Emotional Baseline (Excitement)",
            delay_before=2.0
        )
        
        await self.send_message(
            "Actually, I'm really stressed because the deadline is tomorrow and I'm behind",
            expected_features=["context_switch_acknowledgment", "empathy_response"],
            test_name="Emotional Shift (Excitement → Stress)",
            delay_before=2.0
        )
        
        # Conversation Mode Change
        await self.send_message(
            "Can you help me understand photosynthesis in marine plants?",
            expected_features=["elena_personality"],
            test_name="Educational Mode Request",
            delay_before=2.0
        )
        
        await self.send_message(
            "Thanks! Now let's just chat casually - how's your day going?",
            expected_features=["context_switch_acknowledgment"],
            test_name="Mode Shift (Educational → Casual)",
            delay_before=2.0
        )
        
        # Urgency Change
        await self.send_message(
            "I'm working on a research paper about ocean acidification",
            expected_features=["elena_personality"],
            test_name="Normal Pace Baseline",
            delay_before=2.0
        )
        
        await self.send_message(
            "WAIT! I need help RIGHT NOW - my presentation is in 10 minutes and I'm panicking!",
            expected_features=["context_switch_acknowledgment", "empathy_response"],
            test_name="Urgency Escalation (Dramatic)",
            delay_before=2.0
        )
        
        # Intent Change
        await self.send_message(
            "What can you tell me about marine biodiversity?",
            expected_features=["elena_personality"],
            test_name="Information Seeking Intent",
            delay_before=2.0
        )
        
        await self.send_message(
            "Actually, forget the facts - I'm feeling down and just need someone to talk to",
            expected_features=["context_switch_acknowledgment", "empathy_response"],
            test_name="Intent Shift (Information → Emotional Support)",
            delay_before=2.0
        )
    
    async def run_empathy_calibration_tests(self):
        """Run empathy calibration tests."""
        logger.info("💭 STARTING EMPATHY CALIBRATION TESTS")
        
        # Emotional Vulnerability
        await self.send_message(
            "I failed my marine biology exam and I'm questioning if I'm cut out for this field",
            expected_features=["empathy_response", "elena_personality"],
            test_name="Emotional Vulnerability (Self-doubt)",
            delay_before=2.0
        )
        
        # Excitement/Joy
        await self.send_message(
            "OMG Elena! I just got accepted to do field research with whale sharks in the Maldives!",
            expected_features=["empathy_response", "elena_personality"],
            test_name="Excitement/Joy (Achievement)",
            delay_before=2.0
        )
        
        # Frustration/Anger
        await self.send_message(
            "I'm so frustrated with people who don't care about ocean pollution - they're destroying everything!",
            expected_features=["empathy_response", "elena_personality"],
            test_name="Frustration/Anger (Environmental)",
            delay_before=2.0
        )
    
    async def run_complex_multi_switch_tests(self):
        """Run complex multi-switch tests."""
        logger.info("🧠 STARTING COMPLEX MULTI-SWITCH TESTS")
        
        # Triple Switch Test
        await self.send_message(
            "I love studying marine ecosystems - the complexity is fascinating!",
            expected_features=["elena_personality"],
            test_name="Multi-Switch Baseline",
            delay_before=2.0
        )
        
        await self.send_message(
            "But honestly, I'm overwhelmed and scared I'll never understand it all. Can we just talk normally?",
            expected_features=["context_switch_acknowledgment", "empathy_response"],
            test_name="Triple Switch (Topic + Emotion + Mode)",
            delay_before=2.0
        )
        
        # Rapid Context Switching
        messages = [
            ("I'm studying marine biology", "Rapid Switch 1 (Baseline)"),
            ("Actually, let's talk about cooking", "Rapid Switch 2 (Topic)"),
            ("Wait, I'm stressed about my exams", "Rapid Switch 3 (Emotional)"),
            ("Never mind, how's the weather?", "Rapid Switch 4 (Casual)")
        ]
        
        for message, test_name in messages:
            await self.send_message(
                message,
                expected_features=["context_switch_acknowledgment"] if "Switch" in test_name and test_name != "Rapid Switch 1 (Baseline)" else [],
                test_name=test_name,
                delay_before=1.0
            )
    
    async def run_full_test_suite(self) -> Dict[str, Any]:
        """Run the complete Phase 3+ intelligence test suite."""
        logger.info("🚀 STARTING FULL PHASE 3+ INTELLIGENCE TEST SUITE")
        logger.info(f"🎯 Target: {self.base_url}")
        logger.info(f"👤 Test User: {self.test_user_id}")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        try:
            # Test bot health first
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status != 200:
                    raise Exception(f"Bot health check failed: {response.status}")
                logger.info("✅ Bot health check passed")
            
            # Run test suites
            await self.run_context_switch_tests()
            await self.run_empathy_calibration_tests() 
            await self.run_complex_multi_switch_tests()
            
            # Generate final report
            end_time = time.time()
            duration = end_time - start_time
            
            report = self._generate_final_report(duration)
            logger.info("🎯 TEST SUITE COMPLETED")
            logger.info(f"⏱️  Total Duration: {duration:.2f} seconds")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "completed_tests": len(self.test_results)
            }
    
    def _generate_final_report(self, duration: float) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        
        total_tests = len(self.test_results)
        context_switch_tests = sum(1 for r in self.test_results if r["analysis"]["context_switches_detected"])
        empathy_tests = sum(1 for r in self.test_results if r["analysis"]["empathy_calibration_active"])
        cdl_tests = sum(1 for r in self.test_results if r["analysis"]["cdl_integration"])
        
        avg_quality = sum(r["analysis"]["response_quality"] for r in self.test_results) / total_tests if total_tests > 0 else 0
        
        phase3_effectiveness = {
            "context_switch_detection_rate": (context_switch_tests / total_tests * 100) if total_tests > 0 else 0,
            "empathy_calibration_rate": (empathy_tests / total_tests * 100) if total_tests > 0 else 0,
            "cdl_integration_rate": (cdl_tests / total_tests * 100) if total_tests > 0 else 0,
            "average_response_quality": avg_quality
        }
        
        report = {
            "success": True,
            "test_summary": {
                "total_tests": total_tests,
                "duration_seconds": duration,
                "context_switches_detected": context_switch_tests,
                "empathy_responses": empathy_tests,
                "cdl_integration_success": cdl_tests,
                "average_quality_score": avg_quality
            },
            "phase3_effectiveness": phase3_effectiveness,
            "detailed_results": self.test_results,
            "conversation_history": self.conversation_history,
            "recommendations": self._generate_recommendations(phase3_effectiveness)
        }
        
        # Log summary
        logger.info("📊 FINAL REPORT SUMMARY")
        logger.info(f"   Total Tests: {total_tests}")
        logger.info(f"   Context Switch Detection: {context_switch_tests}/{total_tests} ({phase3_effectiveness['context_switch_detection_rate']:.1f}%)")
        logger.info(f"   Empathy Calibration: {empathy_tests}/{total_tests} ({phase3_effectiveness['empathy_calibration_rate']:.1f}%)")
        logger.info(f"   CDL Integration: {cdl_tests}/{total_tests} ({phase3_effectiveness['cdl_integration_rate']:.1f}%)")
        logger.info(f"   Average Quality Score: {avg_quality:.2f}/5")
        
        return report
    
    def _generate_recommendations(self, effectiveness: Dict[str, float]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if effectiveness["context_switch_detection_rate"] < 50:
            recommendations.append("Context switch detection rate is low - check ContextSwitchDetector initialization and thresholds")
        
        if effectiveness["empathy_calibration_rate"] < 60:
            recommendations.append("Empathy calibration needs improvement - verify emotion analysis integration")
        
        if effectiveness["cdl_integration_rate"] < 80:
            recommendations.append("CDL character integration issues - check character file loading and personality expression")
        
        if effectiveness["average_response_quality"] < 3.0:
            recommendations.append("Overall response quality is low - investigate AI components processing pipeline")
        
        if not recommendations:
            recommendations.append("All Phase 3+ intelligence features performing well!")
        
        return recommendations

    async def save_report_to_file(self, report: Dict[str, Any], filename: str = None):
        """Save test report to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"phase3_intelligence_test_report_{timestamp}.json"
        
        report_path = Path(__file__).parent / "reports" / filename
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Report saved to: {report_path}")
        return str(report_path)


async def main():
    """Main test execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 3+ Intelligence Automated Test Suite")
    parser.add_argument("--url", default="http://localhost:9091", help="Bot API base URL")
    parser.add_argument("--user-id", default="test_user_phase3", help="Test user ID")
    parser.add_argument("--save-report", action="store_true", help="Save detailed report to file")
    
    args = parser.parse_args()
    
    async with Phase3IntelligenceTestSuite(base_url=args.url, test_user_id=args.user_id) as test_suite:
        report = await test_suite.run_full_test_suite()
        
        if args.save_report:
            await test_suite.save_report_to_file(report)
        
        # Return exit code based on success
        if report.get("success") and report.get("phase3_effectiveness", {}).get("average_response_quality", 0) >= 3.0:
            print("✅ Phase 3+ Intelligence tests PASSED")
            return 0
        else:
            print("❌ Phase 3+ Intelligence tests FAILED or performance below threshold")
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)