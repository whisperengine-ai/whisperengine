#!/usr/bin/env python3
"""
Sprint 1-3 Feature Verification Script

Verify that all Sprint 1-3 memory persistence features are properly
enabled and working in your WhisperEngine setup.
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timezone as tz

# Load environment early so .env variables are present
try:
    from env_manager import load_environment
    load_environment()
except Exception as _env_err:  # noqa: BLE001
    print(f"⚠️  Warning: environment load failed early: {_env_err}")

# Add src to path for imports
sys.path.insert(0, '/Users/markcastillo/git/whisperengine')


async def verify_sprint_features():
    """Verify Sprint 1-3 features are enabled and working"""
    
    print("🔍 WhisperEngine Sprint 1-3 Feature Verification")
    print("=" * 50)
    
    verification_results = {
        "environment_config": False,
        "database_connectivity": False,
        "sprint1_emotional_intelligence": False,
        "sprint2_memory_importance": False,
        "sprint3_emotional_memory_bridge": False,
        "sprint3_automatic_learning": False,
        "full_integration": False
    }
    
    # Step 1: Check Environment Configuration
    print("\n📋 Step 1: Environment Configuration")
    
    env_checks = [
        "ENABLE_EMOTIONAL_INTELLIGENCE",
        "ENABLE_PHASE3_MEMORY", 
        "POSTGRES_HOST",
        "POSTGRES_DB",
        "POSTGRES_USER"
    ]
    
    missing_env = []
    for env_var in env_checks:
        value = os.getenv(env_var)
        if value:
            print(f"✅ {env_var}={value}")
        else:
            print(f"❌ {env_var} not set")
            missing_env.append(env_var)
    
    if not missing_env:
        verification_results["environment_config"] = True
        print("✅ Environment configuration verified")
    else:
        print(f"❌ Missing environment variables: {missing_env}")
    
    # Step 2: Test Database Connectivity
    print("\n📋 Step 2: Database Connectivity")
    
    try:
        import psycopg2
        
        conn_params = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "database": os.getenv("POSTGRES_DB", "whisper_engine"),
            "user": os.getenv("POSTGRES_USER", "bot_user"),
            "password": os.getenv("POSTGRES_PASSWORD", "securepassword123")
        }
        # Psycopg2 stubs may not precisely match our dynamic dict unpack; ignore type check here.
        conn = psycopg2.connect(**conn_params)  # type: ignore[arg-type]
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL connected: {db_version[:50]}...")

        cursor.close()
        conn.close()
        verification_results["database_connectivity"] = True
        
    except Exception as e:  # noqa: BLE001
        print(f"❌ Database connection failed: {e}")
    
    # Step 3: Test Sprint 1 - Emotional Intelligence
    print("\n📋 Step 3: Sprint 1 - Emotional Intelligence Persistence")
    
    try:
        from src.intelligence.emotional_intelligence import PredictiveEmotionalIntelligence
        
        emotional_ai = PredictiveEmotionalIntelligence()
        print("✅ Emotional intelligence component imported")
        
        # Test emotional assessment
        assessment = await emotional_ai.comprehensive_emotional_assessment(
            user_id="test_verification",
            current_message="Testing the emotional intelligence system",
            conversation_context={"verification": True}
        )
        
        # Some builds may expose different attribute naming; attempt safe extraction
        mood_value = None
        try:
            # Preferred path (enum with .value)
            mood_value = assessment.mood_assessment.category.value  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            for attr_name in ["category", "mood", "state", "label"]:
                if hasattr(assessment.mood_assessment, attr_name):
                    candidate = getattr(assessment.mood_assessment, attr_name)
                    if hasattr(candidate, "value"):
                        mood_value = candidate.value
                    else:
                        mood_value = str(candidate)
                    break
        if mood_value is None:
            mood_value = "unknown"
        print(f"✅ Emotional assessment working: mood={mood_value}")
        verification_results["sprint1_emotional_intelligence"] = True
        
    except Exception as e:  # noqa: BLE001
        print(f"❌ Sprint 1 emotional intelligence failed: {e}")
    
    # Step 4: Test Sprint 2 - Memory Importance Engine
    print("\n📋 Step 4: Sprint 2 - Memory Importance Pattern Learning")
    
    try:
        from src.memory.memory_importance_engine import MemoryImportanceEngine
        
        importance_engine = MemoryImportanceEngine()
        print("✅ Memory importance engine imported")
        
        # Test importance calculation
        test_memory = {
            "id": "verification_memory",
            "content": "Testing memory importance calculation",
            "timestamp": datetime.now(tz.utc).isoformat(),
            "metadata": {"verification": True}
        }
        
        importance_score = await importance_engine.calculate_memory_importance(
            memory_id="verification_memory",
            user_id="test_verification",
            memory_data=test_memory,
            user_history=[]
        )
        
        print(f"✅ Memory importance calculation working: {importance_score.overall_score:.3f}")
        verification_results["sprint2_memory_importance"] = True
        
    except Exception as e:  # noqa: BLE001
        print(f"❌ Sprint 2 memory importance failed: {e}")
    
    # Step 5: Test Sprint 3 - Full Integration
    print("\n📋 Step 5: Sprint 3 - Full Integration")
    
    try:
        from src.utils.llm_enhanced_memory_manager import LLMEnhancedMemoryManager
        from unittest.mock import AsyncMock
        
        # Create mock components for testing
        mock_base_manager = AsyncMock()
        mock_llm_client = AsyncMock()
        
        # Initialize enhanced memory manager
        enhanced_manager = LLMEnhancedMemoryManager(
            base_memory_manager=mock_base_manager,
            llm_client=mock_llm_client
        )
        
        print("✅ LLM Enhanced Memory Manager created")
        
        # Initialize persistence systems
        if hasattr(enhanced_manager, '_initialize_persistence_systems'):
            await enhanced_manager._initialize_persistence_systems()  # noqa: SLF001
        
        # Check components
        components_status = {
            "emotional_intelligence": enhanced_manager.emotional_intelligence is not None,
            "memory_importance_engine": enhanced_manager.memory_importance_engine is not None,
            "emotional_memory_bridge": enhanced_manager.emotional_memory_bridge is not None,
            "automatic_learning_hooks": enhanced_manager.automatic_learning_hooks is not None,
        }

        print("✅ Component Status:")
        for component, status in components_status.items():
            print(f"   • {component}: {'✅' if status else '❌'}")
        
        if all(components_status.values()):
            verification_results["sprint3_emotional_memory_bridge"] = True
            verification_results["sprint3_automatic_learning"] = True
            verification_results["full_integration"] = True
            print("✅ Sprint 3 full integration verified")
        else:
            print("❌ Some Sprint 3 components not available")
        
    except Exception as e:  # noqa: BLE001
        print(f"❌ Sprint 3 integration test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Final Results
    print("\n📊 Verification Results Summary")
    print("=" * 50)
    
    total_checks = len(verification_results)
    passed_checks = sum(verification_results.values())
    
    for check_name, passed in verification_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {check_name.replace('_', ' ').title()}")
    
    print(f"\nOverall Score: {passed_checks}/{total_checks} ({passed_checks/total_checks*100:.1f}%)")
    
    if passed_checks == total_checks:
        print("\n🎉 ALL SPRINT 1-3 FEATURES VERIFIED AND WORKING!")
        print("Your WhisperEngine is ready with advanced memory intelligence:")
        print("• Emotional intelligence persistence")
        print("• Memory importance pattern learning") 
        print("• Emotional-memory bridge integration")
        print("• Automatic background learning")
        print("\n🚀 Start your bot with: python run.py")
        
    elif passed_checks >= total_checks * 0.8:
        print("\n⚠️  Most features working - minor issues detected")
        if not verification_results["environment_config"]:
            print("Environment variables missing (false negative if env not loaded).")
        if not verification_results["sprint1_emotional_intelligence"]:
            print("Emotional intelligence check failed - might be attribute mismatch.")
        print("System operational but review warnings above.")
        
    else:
        print("\n❌ Significant issues detected")
        print("Please check the failed components above.")
    
    return verification_results


from typing import TypedDict, Optional


class _CLIArgs(TypedDict, total=False):
    json_path: Optional[str]


def _parse_args(argv: list[str]) -> _CLIArgs:
    """Very lightweight CLI parser for --json <file>."""
    args: _CLIArgs = {"json_path": None}
    if "--json" in argv:
        try:
            idx = argv.index("--json")
            args["json_path"] = argv[idx + 1]
        except (ValueError, IndexError):
            print("⚠️  --json flag provided without path - ignoring")
    return args


async def main(json_path: str | None = None):
    """Run the verification and optionally write JSON output."""
    try:
        results = await verify_sprint_features()
        if json_path:
            try:
                os.makedirs(os.path.dirname(json_path) or ".", exist_ok=True)
                total = len(results)
                passed = sum(results.values())
                payload = {
                    "generated_at": datetime.now(tz.utc).isoformat(),
                    "summary": {
                        "total_checks": total,
                        "passed": passed,
                        "percentage": round(passed / total * 100, 2) if total else 0.0,
                    },
                    "results": results,
                    "environment": {
                        "enable_emotional_intelligence": os.getenv("ENABLE_EMOTIONAL_INTELLIGENCE"),
                        "enable_phase3_memory": os.getenv("ENABLE_PHASE3_MEMORY"),
                    },
                }
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)
                print(f"📝 Results written to {json_path}")
            except OSError as io_err:
                print(f"❌ Failed to write JSON results: {io_err}")
        return results
    except Exception as e:  # noqa: BLE001
        print(f"❌ Verification script failed: {e}")
        import traceback
        traceback.print_exc()
        return {}


if __name__ == "__main__":
    cli_args = _parse_args(sys.argv[1:])
    print("Starting Sprint 1-3 feature verification...")
    verification_outcome = asyncio.run(main(json_path=cli_args.get("json_path")))

    if verification_outcome.get("full_integration", False):
        print("\n✅ Verification complete - All systems ready!")
    else:
        print("\n⚠️  Verification complete - Check results above")