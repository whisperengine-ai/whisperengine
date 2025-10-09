#!/usr/bin/env python3
"""
Synthetic Testing Launcher

Simple launcher script for running synthetic conversations and feeding metrics to InfluxDB.
Integrates with WhisperEngine's existing InfluxDB temporal intelligence infrastructure.

Usage:
    python synthetic_testing_launcher.py --bots elena,marcus,ryan,dream,gabriel,sophia,jake,dotty,aetheris,aethys --duration 24

Author: WhisperEngine AI Team  
Created: October 8, 2025
Purpose: Unified synthetic testing with InfluxDB integration
"""

import argparse
import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict

# Import our synthetic modules
from synthetic_conversation_generator import SyntheticConversationGenerator
from synthetic_validation_metrics import SyntheticDataValidator
from synthetic_influxdb_integration import SyntheticMetricsCollector, SyntheticTestMetrics

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SyntheticTestingOrchestrator:
    """Orchestrates synthetic testing and InfluxDB metric collection"""
    
    def __init__(self, bot_endpoints: Dict[str, str], test_duration_hours: float = 24.0):
        self.bot_endpoints = bot_endpoints
        self.test_duration_hours = test_duration_hours
        self.generator = SyntheticConversationGenerator(bot_endpoints)
        self.validator = SyntheticDataValidator()
        self.metrics_collector = SyntheticMetricsCollector()
        self.start_time = datetime.now()
        
    async def run_synthetic_testing(self):
        """Run continuous synthetic testing with InfluxDB integration"""
        logger.info("🚀 Starting synthetic testing orchestrator")
        logger.info("Test duration: %.1f hours", self.test_duration_hours)
        logger.info("Bot endpoints: %s", list(self.bot_endpoints.keys()))
        
        await self.generator.start_session()
        
        try:
            end_time = self.start_time + timedelta(hours=self.test_duration_hours)
            conversation_count = 0
            last_metrics_update = self.start_time
            
            while datetime.now() < end_time:
                # Generate synthetic conversation
                conversation_generated = await self._generate_single_conversation()
                if conversation_generated:
                    conversation_count += 1
                
                # Update InfluxDB metrics every hour
                if datetime.now() - last_metrics_update >= timedelta(hours=1):
                    await self._update_influxdb_metrics(conversation_count)
                    last_metrics_update = datetime.now()
                
                # Wait before next conversation (realistic pacing)
                wait_time = 30 + (conversation_count % 180)  # 30s to 3.5min
                await asyncio.sleep(wait_time)
            
            # Final metrics update
            await self._update_influxdb_metrics(conversation_count, final=True)
            
        except KeyboardInterrupt:
            logger.info("🛑 Synthetic testing interrupted by user")
        finally:
            await self.generator.close_session()
            self.metrics_collector.close()
        
        logger.info("✅ Synthetic testing completed: %d conversations generated", conversation_count)
    
    async def _generate_single_conversation(self) -> bool:
        """Generate a single synthetic conversation"""
        try:
            # Import here to avoid circular imports
            from synthetic_conversation_generator import ConversationType, random
            
            user = random.choice(self.generator.synthetic_users)
            bot_name = random.choice(list(self.bot_endpoints.keys()))
            conversation_type = random.choice(list(ConversationType))
            
            conversation_log = await self.generator.generate_conversation(user, bot_name, conversation_type)
            return len(conversation_log) > 0
            
        except (ValueError, ConnectionError, RuntimeError) as e:
            logger.error("Failed to generate conversation: %s", e)
            return False
    
    async def _update_influxdb_metrics(self, conversation_count: int, final: bool = False):
        """Update InfluxDB with latest synthetic testing metrics"""
        try:
            # Reload conversation data
            self.validator.load_conversation_data()
            
            if not self.validator.conversations:
                logger.warning("No conversations available for metrics calculation")
                return
            
            # Calculate comprehensive metrics
            memory_metrics = self.validator.validate_memory_effectiveness()
            emotion_metrics = self.validator.validate_emotion_detection()
            cdl_metrics = self.validator.validate_cdl_personality_consistency()
            relationship_metrics = self.validator.validate_relationship_progression()
            cross_pollination_metrics = self.validator.validate_cross_pollination_accuracy()
            enhanced_api_metrics = self.validator.validate_enhanced_api_metadata()  # NEW: Enhanced API validation
            quality_score = self.validator.calculate_conversation_quality_score()
            
            # Memory Intelligence Convergence validation (NEW)
            memory_intelligence_metrics = self.validator.validate_memory_intelligence_convergence()
            coordinator_metrics = self.validator.validate_unified_character_intelligence_coordinator()
            semantic_naming_metrics = self.validator.validate_semantic_naming_compliance()
            
            # Create synthetic test metrics (enhanced with Memory Intelligence Convergence)
            elapsed_hours = (datetime.now() - self.start_time).total_seconds() / 3600
            test_metrics = SyntheticTestMetrics(
                memory_recall_accuracy=memory_metrics['overall_accuracy'],
                emotion_detection_precision=emotion_metrics['emotion_consistency_score'],
                cdl_personality_consistency=cdl_metrics['overall_consistency'],
                relationship_progression_score=relationship_metrics['overall_progression_score'],
                cross_pollination_accuracy=cross_pollination_metrics['fact_sharing_accuracy'],
                conversation_quality_score=quality_score,
                conversations_analyzed=len(self.validator.conversations),
                unique_synthetic_users=len(set(conv['user']['user_id'] for conv in self.validator.conversations)),
                test_duration_hours=elapsed_hours,
                expanded_taxonomy_usage=emotion_metrics['expanded_taxonomy_usage'],
                # Memory Intelligence Convergence metrics (PHASE 1-4)
                character_vector_episodic_intelligence_score=memory_intelligence_metrics['character_vector_episodic_intelligence_score'],
                temporal_evolution_intelligence_score=memory_intelligence_metrics['temporal_evolution_intelligence_score'],
                unified_coordinator_response_quality=coordinator_metrics['unified_coordinator_response_quality'],
                intelligence_system_coordination_score=coordinator_metrics['intelligence_system_coordination_score'],
                semantic_naming_compliance=semantic_naming_metrics['semantic_naming_compliance']
            )
            
            # Record to InfluxDB
            test_type = "final_report" if final else "hourly_update"
            success = await self.metrics_collector.record_synthetic_test_metrics(test_metrics, test_type)
            
            if success:
                logger.info("📊 InfluxDB metrics updated: quality=%.2f, conversations=%d", 
                           quality_score, len(self.validator.conversations))
            else:
                logger.warning("Failed to update InfluxDB metrics")
            
            # Record conversation rate
            conversations_per_hour = conversation_count / max(0.1, elapsed_hours)
            bot_distribution = {}
            for conv in self.validator.conversations:
                bot_name = conv['bot_name']
                bot_distribution[bot_name] = bot_distribution.get(bot_name, 0) + 1
            
            await self.metrics_collector.record_synthetic_conversation_rate(
                conversations_per_hour, 
                test_metrics.unique_synthetic_users,
                bot_distribution
            )
            
            # Record expanded taxonomy usage
            await self.metrics_collector.record_expanded_taxonomy_usage(
                emotion_metrics['emotions_detected'],
                emotion_metrics['expanded_taxonomy_usage']
            )
            
        except (ValueError, ConnectionError, RuntimeError) as e:
            logger.error("Failed to update InfluxDB metrics: %s", e)


async def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(description="WhisperEngine Synthetic Testing")
    parser.add_argument("--bots", default="elena,marcus,ryan,dream,gabriel,sophia,jake,dotty,aetheris,aethys", 
                       help="Comma-separated list of bots to test")
    parser.add_argument("--duration", type=float, default=24.0,
                       help="Test duration in hours")
    parser.add_argument("--validate-only", action="store_true",
                       help="Only run validation on existing data")
    
    args = parser.parse_args()
    
    # Parse bot list
    bot_names = [name.strip() for name in args.bots.split(",")]
    
    # Bot endpoints from environment variables (Docker-friendly) with localhost fallback
    default_endpoints = {
        "elena": os.getenv("ELENA_ENDPOINT", "http://localhost:9091"),
        "marcus": os.getenv("MARCUS_ENDPOINT", "http://localhost:9092"), 
        "ryan": os.getenv("RYAN_ENDPOINT", "http://localhost:9093"),
        "dream": os.getenv("DREAM_ENDPOINT", "http://localhost:9094"),
        "gabriel": os.getenv("GABRIEL_ENDPOINT", "http://localhost:9095"),
        "sophia": os.getenv("SOPHIA_ENDPOINT", "http://localhost:9096"),
        "jake": os.getenv("JAKE_ENDPOINT", "http://localhost:9097"),
        "dotty": os.getenv("DOTTY_ENDPOINT", "http://localhost:9098"),
        "aetheris": os.getenv("AETHERIS_ENDPOINT", "http://localhost:9099"),
        "aethys": os.getenv("AETHYS_ENDPOINT", "http://localhost:3007")
    }
    
    # Build endpoint dict for requested bots
    bot_endpoints = {name: default_endpoints[name] for name in bot_names if name in default_endpoints}
    
    if not bot_endpoints:
        logger.error("No valid bot endpoints found for: %s", bot_names)
        return
    
    logger.info("Starting synthetic testing for bots: %s", list(bot_endpoints.keys()))
    
    if args.validate_only:
        # Just run validation and update InfluxDB
        validator = SyntheticDataValidator()
        metrics_collector = SyntheticMetricsCollector()
        
        # Generate validation report
        report = validator.generate_comprehensive_report()
        
        # Push to InfluxDB
        test_metrics = SyntheticTestMetrics(
            memory_recall_accuracy=report.memory_recall_accuracy,
            emotion_detection_precision=report.emotion_detection_precision,
            cdl_personality_consistency=report.cdl_personality_consistency,
            relationship_progression_score=report.relationship_progression_score,
            cross_pollination_accuracy=report.cross_pollination_accuracy,
            conversation_quality_score=report.conversation_quality_score,
            conversations_analyzed=report.total_conversations,
            unique_synthetic_users=report.unique_users,
            test_duration_hours=report.test_duration_hours,
            expanded_taxonomy_usage=0.0  # Would need to calculate this
        )
        
        success = await metrics_collector.record_synthetic_test_metrics(test_metrics, "validation_report")
        if success:
            logger.info("✅ Validation metrics pushed to InfluxDB")
        else:
            logger.error("❌ Failed to push validation metrics to InfluxDB")
        
        metrics_collector.close()
    else:
        # Run full synthetic testing
        orchestrator = SyntheticTestingOrchestrator(bot_endpoints, args.duration)
        await orchestrator.run_synthetic_testing()


if __name__ == "__main__":
    asyncio.run(main())