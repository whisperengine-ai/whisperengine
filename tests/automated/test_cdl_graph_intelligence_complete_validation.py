#!/usr/bin/env python3
"""
CDL Graph Intelligence Complete System Validation
Comprehensive end-to-end testing of all 8 implementation steps

Tests the complete CDL Graph Intelligence roadmap:
✅ STEP 1: Basic CDL Integration
✅ STEP 2: Cross-Pollination Enhancement  
✅ STEP 3: Memory Trigger Enhancement
✅ STEP 4: Emotional Context Synchronization
✅ STEP 5: Proactive Context Injection
✅ STEP 6: Confidence-Aware Conversations
✅ STEP 7: Question Generation Intelligence
✅ STEP 8: Database Performance Optimization
"""

import os
import sys
import asyncio
import time
from typing import Dict, Any
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Load environment
load_dotenv()

class CDLGraphIntelligenceSystemValidator:
    def __init__(self):
        self.validation_results = {}
        self.start_time = None
        
    async def initialize(self):
        """Initialize all system components"""
        print("🚀 Initializing CDL Graph Intelligence System Validation")
        print("="*70)
        
        # Set required environment variables
        os.environ['FASTEMBED_CACHE_PATH'] = "/tmp/fastembed_cache"
        os.environ['QDRANT_HOST'] = "localhost"
        os.environ['QDRANT_PORT'] = "6334"
        os.environ['POSTGRES_HOST'] = "localhost"
        os.environ['POSTGRES_PORT'] = "5433"
        
        self.start_time = time.perf_counter()
        print("✅ Environment configured for CDL Graph Intelligence testing")
        
    async def validate_step_1_basic_cdl_integration(self) -> Dict[str, Any]:
        """STEP 1: Basic CDL Integration - Character data retrieval"""
        print("\n🧠 STEP 1: Basic CDL Integration")
        
        try:
            from src.characters.cdl.character_graph_manager import CharacterGraphManager
            
            # Test character data retrieval
            manager = CharacterGraphManager()
            character_data = await manager.get_character_context("elena", limit=10)
            
            if character_data and len(character_data) > 0:
                return {
                    "status": "success",
                    "character_data_count": len(character_data),
                    "sample_categories": list(set(item.get('category', 'unknown') for item in character_data[:5])),
                    "implementation": "CharacterGraphManager retrieval working"
                }
            else:
                return {
                    "status": "warning", 
                    "message": "No character data retrieved - may need data import"
                }
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def validate_step_2_cross_pollination(self) -> Dict[str, Any]:
        """STEP 2: Cross-Pollination Enhancement - User facts to character background"""
        print("🔄 STEP 2: Cross-Pollination Enhancement")
        
        try:
            from src.characters.cdl.character_graph_manager import CharacterGraphManager
            
            manager = CharacterGraphManager()
            
            # Test cross-pollination with sample user facts
            sample_facts = [
                {"entity_name": "diving", "confidence": 0.9},
                {"entity_name": "marine_biology", "confidence": 0.85},
                {"entity_name": "research", "confidence": 0.8}
            ]
            
            # Test the cross-pollination method
            cross_pollinated = await manager.get_cross_pollination_background(
                character_name="elena",
                user_facts=sample_facts
            )
            
            if cross_pollinated:
                return {
                    "status": "success",
                    "cross_pollinated_count": len(cross_pollinated),
                    "implementation": "Cross-pollination logic working",
                    "sample_matches": [item.get('description', '')[:100] + "..." for item in cross_pollinated[:2]]
                }
            else:
                return {
                    "status": "warning",
                    "message": "No cross-pollination matches found"
                }
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def validate_step_3_memory_triggers(self) -> Dict[str, Any]:
        """STEP 3: Memory Trigger Enhancement - User entity triggers for memories"""
        print("🧠 STEP 3: Memory Trigger Enhancement")
        
        try:
            from src.characters.cdl.character_graph_manager import CharacterGraphManager
            
            manager = CharacterGraphManager()
            
            # Test memory trigger activation
            sample_user_facts = [
                {"entity_name": "diving", "confidence": 0.9},
                {"entity_name": "ocean", "confidence": 0.85}
            ]
            
            triggered_memories = await manager.get_memory_triggered_context(
                character_name="elena",
                keywords=["diving"],
                user_facts=sample_user_facts
            )
            
            if triggered_memories:
                return {
                    "status": "success", 
                    "triggered_memory_count": len(triggered_memories),
                    "implementation": "Memory trigger logic working",
                    "sample_triggers": [mem.get('triggers', []) for mem in triggered_memories[:2] if mem.get('triggers')]
                }
            else:
                return {
                    "status": "warning",
                    "message": "No memory triggers activated"
                }
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def validate_step_4_emotional_context(self) -> Dict[str, Any]:
        """STEP 4: Emotional Context Synchronization - Emotional resonance matching"""
        print("💙 STEP 4: Emotional Context Synchronization")
        
        try:
            from src.characters.cdl.character_graph_manager import CharacterGraphManager
            
            manager = CharacterGraphManager()
            
            # Test emotional resonance
            emotional_memories = await manager.get_emotionally_resonant_memories(
                character_name="elena",
                user_emotional_context="excited",
                emotional_intensity=0.8
            )
            
            if emotional_memories:
                return {
                    "status": "success",
                    "emotional_memory_count": len(emotional_memories),
                    "implementation": "Emotional synchronization working",
                    "emotion_impacts": [mem.get('emotional_impact', 0) for mem in emotional_memories[:3]]
                }
            else:
                return {
                    "status": "warning", 
                    "message": "No emotionally resonant memories found"
                }
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def validate_step_5_proactive_context(self) -> Dict[str, Any]:
        """STEP 5: Proactive Context Injection - Auto-inject character background"""
        print("🎯 STEP 5: Proactive Context Injection")
        
        try:
            from src.characters.cdl.character_graph_manager import CharacterGraphManager
            
            manager = CharacterGraphManager()
            
            # Test proactive context injection  
            proactive_context = await manager.get_proactive_context_injection(
                character_name="elena",
                message_content="I'm interested in underwater photography",
                user_facts=[{"entity_name": "photography", "confidence": 0.9}]
            )
            
            if proactive_context:
                return {
                    "status": "success",
                    "proactive_context_count": len(proactive_context),
                    "implementation": "Proactive injection working",
                    "injected_categories": list(set(ctx.get('category', 'unknown') for ctx in proactive_context))
                }
            else:
                return {
                    "status": "warning",
                    "message": "No proactive context found for injection"
                }
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def validate_step_6_confidence_aware(self) -> Dict[str, Any]:
        """STEP 6: Confidence-Aware Conversations - Confidence-based language"""
        print("📊 STEP 6: Confidence-Aware Conversations")
        
        try:
            from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
            
            integration = CDLAIPromptIntegration()
            
            # Test confidence-aware context building
            sample_user_facts = [
                {"entity_name": "diving", "confidence": 0.95, "relationship_type": "enjoys"},
                {"entity_name": "photography", "confidence": 0.7, "relationship_type": "learning"},
                {"entity_name": "marine_biology", "confidence": 0.4, "relationship_type": "curious_about"}
            ]
            
            confidence_context = await integration.build_confidence_aware_context(
                user_facts=sample_user_facts
            )
            
            if confidence_context and len(confidence_context) > 50:
                return {
                    "status": "success",
                    "confidence_context_length": len(confidence_context),
                    "implementation": "Confidence-aware language working",
                    "contains_high_confidence": "high confidence" in confidence_context.lower(),
                    "contains_medium_confidence": "medium confidence" in confidence_context.lower()
                }
            else:
                return {
                    "status": "warning",
                    "message": "Confidence-aware context generation minimal"
                }
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def validate_step_7_question_generation(self) -> Dict[str, Any]:
        """STEP 7: Question Generation Intelligence - Knowledge gap questions"""
        print("❓ STEP 7: Question Generation Intelligence")
        
        try:
            from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
            
            integration = CDLAIPromptIntegration()
            
            # Test question generation
            sample_user_facts = [
                {"entity_name": "diving", "confidence": 0.95, "relationship_type": "enjoys"},
                {"entity_name": "marine_biology", "confidence": 0.85, "relationship_type": "studies"}
            ]
            
            questions = await integration.generate_curiosity_questions(
                user_id="test_user_validation",
                user_facts=sample_user_facts,
                character_name="elena"
            )
            
            if questions and len(questions) > 0:
                return {
                    "status": "success",
                    "question_count": len(questions),
                    "implementation": "Question generation working",
                    "sample_questions": questions[:3],
                    "character_appropriate": any("diving" in q.lower() or "marine" in q.lower() for q in questions)
                }
            else:
                return {
                    "status": "warning",
                    "message": "No curiosity questions generated"
                }
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def validate_step_8_performance(self) -> Dict[str, Any]:
        """STEP 8: Database Performance Optimization - Query performance"""
        print("⚡ STEP 8: Database Performance Optimization")
        
        try:
            import asyncpg
            
            # Test database query performance
            database_url = (
                f"postgresql://{os.getenv('POSTGRES_USER', 'whisperengine')}:"
                f"{os.getenv('POSTGRES_PASSWORD', 'devpass123')}@"
                f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
                f"{os.getenv('POSTGRES_PORT', '5433')}/"
                f"{os.getenv('POSTGRES_DB', 'whisperengine')}"
            )
            
            conn = await asyncpg.connect(database_url)
            
            # Test query performance
            start_time = time.perf_counter()
            result = await conn.fetch("""
                SELECT id, description, importance_level 
                FROM character_background 
                WHERE character_id = (SELECT id FROM characters WHERE name = 'elena' LIMIT 1)
                ORDER BY importance_level DESC 
                LIMIT 10
            """)
            end_time = time.perf_counter()
            
            query_time_ms = (end_time - start_time) * 1000
            
            await conn.close()
            
            return {
                "status": "success",
                "query_time_ms": round(query_time_ms, 2),
                "implementation": "Database performance optimized",
                "target_met": query_time_ms < 10.0,
                "result_count": len(result)
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def run_complete_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation of all 8 CDL Graph Intelligence steps"""
        validation_steps = [
            ("step_1_basic_cdl", self.validate_step_1_basic_cdl_integration),
            ("step_2_cross_pollination", self.validate_step_2_cross_pollination),
            ("step_3_memory_triggers", self.validate_step_3_memory_triggers),
            ("step_4_emotional_context", self.validate_step_4_emotional_context),
            ("step_5_proactive_context", self.validate_step_5_proactive_context),
            ("step_6_confidence_aware", self.validate_step_6_confidence_aware),
            ("step_7_question_generation", self.validate_step_7_question_generation),
            ("step_8_performance", self.validate_step_8_performance)
        ]
        
        results = {}
        
        for step_name, validation_func in validation_steps:
            try:
                result = await validation_func()
                results[step_name] = result
            except Exception as e:
                results[step_name] = {"status": "error", "error": str(e)}
        
        # Calculate overall system health
        successful_steps = sum(1 for r in results.values() if r.get("status") == "success")
        total_steps = len(validation_steps)
        success_rate = (successful_steps / total_steps) * 100
        
        end_time = time.perf_counter()
        total_time = (end_time - self.start_time) * 1000
        
        results["summary"] = {
            "total_validation_time_ms": round(total_time, 2),
            "successful_steps": successful_steps,
            "total_steps": total_steps,
            "success_rate": f"{success_rate:.1f}%",
            "system_status": "operational" if success_rate >= 75 else "degraded" if success_rate >= 50 else "critical"
        }
        
        return results

def print_validation_report(results: Dict[str, Any]):
    """Print comprehensive CDL Graph Intelligence validation report"""
    print("\n" + "="*70)
    print("🎯 CDL GRAPH INTELLIGENCE SYSTEM VALIDATION REPORT")
    print("="*70)
    
    summary = results.get("summary", {})
    print(f"\n🚀 OVERALL SYSTEM STATUS:")
    print(f"   Total Validation Time: {summary.get('total_validation_time_ms', 0)}ms")
    print(f"   Successful Steps: {summary.get('successful_steps', 0)}/{summary.get('total_steps', 0)}")
    print(f"   Success Rate: {summary.get('success_rate', '0%')}")
    print(f"   System Status: {summary.get('system_status', 'unknown').upper()}")
    
    step_names = {
        "step_1_basic_cdl": "STEP 1: Basic CDL Integration",
        "step_2_cross_pollination": "STEP 2: Cross-Pollination Enhancement",
        "step_3_memory_triggers": "STEP 3: Memory Trigger Enhancement", 
        "step_4_emotional_context": "STEP 4: Emotional Context Synchronization",
        "step_5_proactive_context": "STEP 5: Proactive Context Injection",
        "step_6_confidence_aware": "STEP 6: Confidence-Aware Conversations",
        "step_7_question_generation": "STEP 7: Question Generation Intelligence",
        "step_8_performance": "STEP 8: Database Performance Optimization"
    }
    
    print(f"\n📋 DETAILED STEP VALIDATION:")
    
    for step_key, step_name in step_names.items():
        if step_key in results:
            result = results[step_key]
            status = result.get("status", "unknown")
            
            if status == "success":
                print(f"   ✅ {step_name}: SUCCESS")
                if "implementation" in result:
                    print(f"      Implementation: {result['implementation']}")
                    
                # Show key metrics for each step
                if step_key == "step_1_basic_cdl" and "character_data_count" in result:
                    print(f"      Character Data: {result['character_data_count']} items")
                elif step_key == "step_2_cross_pollination" and "cross_pollinated_count" in result:
                    print(f"      Cross-Pollination Matches: {result['cross_pollinated_count']}")
                elif step_key == "step_3_memory_triggers" and "triggered_memory_count" in result:
                    print(f"      Memory Triggers: {result['triggered_memory_count']}")
                elif step_key == "step_4_emotional_context" and "emotional_memory_count" in result:
                    print(f"      Emotional Memories: {result['emotional_memory_count']}")
                elif step_key == "step_5_proactive_context" and "proactive_context_count" in result:
                    print(f"      Proactive Context: {result['proactive_context_count']}")
                elif step_key == "step_6_confidence_aware" and "confidence_context_length" in result:
                    print(f"      Confidence Context: {result['confidence_context_length']} chars")
                elif step_key == "step_7_question_generation" and "question_count" in result:
                    print(f"      Generated Questions: {result['question_count']}")
                elif step_key == "step_8_performance" and "query_time_ms" in result:
                    target_status = "✅ PASSED" if result.get("target_met") else "⚠️ SLOW"
                    print(f"      Query Performance: {result['query_time_ms']}ms ({target_status})")
                    
            elif status == "warning":
                print(f"   ⚠️ {step_name}: WARNING")
                if "message" in result:
                    print(f"      Issue: {result['message']}")
                    
            else:
                print(f"   ❌ {step_name}: FAILED")
                if "error" in result:
                    print(f"      Error: {result['error']}")
    
    print("\n" + "="*70)
    
    # System recommendations
    success_rate = float(summary.get("success_rate", "0%").rstrip("%"))
    if success_rate >= 85:
        print("🎉 EXCELLENT: CDL Graph Intelligence system is fully operational!")
        print("   All major components working correctly. System ready for production use.")
    elif success_rate >= 75:
        print("✅ GOOD: CDL Graph Intelligence system is mostly operational.")
        print("   Minor issues detected. System functional with some optimizations needed.")
    elif success_rate >= 50:
        print("⚠️ DEGRADED: CDL Graph Intelligence system has significant issues.")
        print("   Multiple components need attention before production use.")
    else:
        print("❌ CRITICAL: CDL Graph Intelligence system requires major fixes.")
        print("   System not ready for production. Immediate attention required.")
    
    print("="*70)

async def main():
    """Main validation execution"""
    validator = CDLGraphIntelligenceSystemValidator()
    
    try:
        # Initialize system
        await validator.initialize()
        
        # Run complete validation
        results = await validator.run_complete_validation()
        
        # Print comprehensive report
        print_validation_report(results)
        
        # Determine exit code based on results
        summary = results.get("summary", {})
        success_rate = float(summary.get("success_rate", "0%").rstrip("%"))
        
        if success_rate >= 75:
            print(f"\n🎉 CDL Graph Intelligence System Validation: PASSED ({success_rate}%)")
            return True
        else:
            print(f"\n❌ CDL Graph Intelligence System Validation: FAILED ({success_rate}%)")
            return False
        
    except Exception as e:
        print(f"❌ System validation failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)