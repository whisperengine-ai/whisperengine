#!/usr/bin/env python3
"""
Test runner for hierarchical memory architecture

Validates implementation before integration
"""

import sys
import os
import asyncio
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all hierarchical memory components can be imported"""
    try:
        print("Testing imports...")
        
        from src.memory.core.storage_abstraction import HierarchicalMemoryManager, ConversationContext
        from src.memory.core.context_assembler import IntelligentContextAssembler, ContextSource, ContextPriority
        from src.memory.core.migration_manager import HierarchicalMigrationManager, MigrationStats
        from src.memory.processors.conversation_summarizer import ConversationSummarizer, SummaryType
        
        # Test tier imports (some may fail if dependencies not installed, which is expected)
        import_results = []
        
        try:
            from src.memory.tiers.tier1_redis_cache import RedisContextCache
            import_results.append("✅ Redis tier")
        except ImportError as e:
            import_results.append(f"⏳ Redis tier (expected: {str(e)[:50]}...)")
        
        try:
            from src.memory.tiers.tier2_postgresql import PostgreSQLConversationArchive
            import_results.append("✅ PostgreSQL tier")
        except ImportError as e:
            import_results.append(f"⏳ PostgreSQL tier (expected: {str(e)[:50]}...)")
            
        try:
            from src.memory.tiers.tier3_chromadb_summaries import ChromaDBSemanticSummaries
            import_results.append("✅ ChromaDB tier")
        except ImportError as e:
            import_results.append(f"⏳ ChromaDB tier (expected: {str(e)[:50]}...)")
            
        try:
            from src.memory.tiers.tier4_neo4j_relationships import Neo4jRelationshipEngine
            import_results.append("✅ Neo4j tier")
        except ImportError as e:
            import_results.append(f"⏳ Neo4j tier (expected: {str(e)[:50]}...)")
        
        print("Core imports successful")
        for result in import_results:
            print(f"  {result}")
        
        print("✅ Core components importable (tier dependencies expected to be missing)")
        return True
        
    except ImportError as e:
        print(f"❌ Critical import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False

def test_data_structures():
    """Test basic data structure creation"""
    try:
        print("Testing data structures...")
        
        from src.memory.core.storage_abstraction import ConversationContext
        from src.memory.core.context_assembler import ContextSource, ContextPriority
        from src.memory.core.migration_manager import MigrationStats
        from datetime import datetime
        
        # Test ConversationContext
        context = ConversationContext(
            recent_messages=[{"user_message": "test", "bot_response": "test"}],
            semantic_summaries=[],
            related_topics=[],
            full_conversations=[],
            assembly_metadata={}
        )
        assert hasattr(context, 'to_context_string')
        
        # Test ContextSource
        source = ContextSource(
            source_type="test",
            content="test content",
            metadata={},
            priority=ContextPriority.HIGH,
            relevance_score=0.8
        )
        assert source.get_weighted_score() > 0
        
        # Test MigrationStats
        stats = MigrationStats()
        assert stats.success_rate == 0.0
        
        print("✅ Data structures created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Data structure test failed: {e}")
        return False

async def test_conversation_summarizer():
    """Test conversation summarizer functionality"""
    try:
        print("Testing conversation summarizer...")
        
        from src.memory.processors.conversation_summarizer import ConversationSummarizer, SummaryType
        
        summarizer = ConversationSummarizer(max_summary_length=150)
        
        # Test basic summarization
        summaries = await summarizer.summarize_conversation(
            user_message="What is artificial intelligence?",
            bot_response="Artificial intelligence is a field of computer science that aims to create intelligent machines.",
            summary_types=[SummaryType.SEMANTIC]
        )
        
        assert len(summaries) == 1
        summary = summaries[0]
        assert len(summary.summary_text) <= 150
        assert summary.confidence_score > 0
        assert isinstance(summary.topics, list)
        
        print("✅ Conversation summarizer working")
        return True
        
    except Exception as e:
        print(f"❌ Conversation summarizer test failed: {e}")
        return False

async def test_context_assembler():
    """Test context assembler with mock data"""
    try:
        print("Testing context assembler...")
        
        from src.memory.core.context_assembler import IntelligentContextAssembler
        from datetime import datetime
        
        assembler = IntelligentContextAssembler()
        
        # Create mock context data in the expected format
        recent_context = [
            {
                "user_message": "Hello",
                "bot_response": "Hi there!",
                "timestamp": datetime.now().isoformat(),
                "conversation_id": "conv_1"
            }
        ]
        
        semantic_context = [
            {
                "summary": "User greeting conversation",
                "topics": ["greeting", "conversation"],
                "relevance_score": 0.8,
                "conversation_id": "conv_2"
            }
        ]
        
        topical_context = [
            {
                "topic": "greetings",
                "strength": 0.7,
                "related_conversations": ["conv_1", "conv_2"]
            }
        ]
        
        # Test context assembly with correct method signature
        assembled = await assembler.assemble_context(
            user_id="test_user",
            current_query="test query",
            recent_context=recent_context,
            semantic_context=semantic_context,
            topical_context=topical_context,
            historical_context=[]
        )
        
        assert assembled is not None
        assert assembled.assembly_time_ms > 0
        assert len(assembled.context_sources) > 0
        assert isinstance(assembled.context_string, str)
        assert len(assembled.context_string) > 0
        
        print("✅ Context assembler working")
        return True
        
    except Exception as e:
        print(f"❌ Context assembler test failed: {e}")
        return False

def test_migration_manager():
    """Test migration manager basic functionality"""
    try:
        print("Testing migration manager...")
        
        from src.memory.core.migration_manager import ConversationData
        from datetime import datetime
        
        # Test ConversationData creation from ChromaDB format
        metadata = {
            "user_id": "test_user",
            "user_message": "Hello",
            "bot_response": "Hi there!",
            "timestamp": "2025-09-19T10:00:00Z"
        }
        
        conv_data = ConversationData.from_chromadb_document(
            doc_id="test_doc",
            document="test document",
            metadata=metadata
        )
        
        assert conv_data is not None
        assert conv_data.user_id == "test_user"
        assert conv_data.user_message == "Hello"
        assert conv_data.bot_response == "Hi there!"
        assert isinstance(conv_data.timestamp, datetime)
        
        print("✅ Migration manager working")
        return True
        
    except Exception as e:
        print(f"❌ Migration manager test failed: {e}")
        return False

def test_hierarchical_manager_creation():
    """Test hierarchical manager can be created"""
    try:
        print("Testing hierarchical manager creation...")
        
        from src.memory.core.storage_abstraction import HierarchicalMemoryManager
        
        config = {
            "redis": {"enabled": False},  # Disable for testing
            "postgresql": {"enabled": False},
            "chromadb": {"enabled": False},
            "neo4j": {"enabled": False}
        }
        
        manager = HierarchicalMemoryManager(config=config)
        assert manager is not None
        assert manager.config == config
        
        print("✅ Hierarchical manager created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Hierarchical manager creation failed: {e}")
        return False

async def run_all_tests():
    """Run all validation tests"""
    print("🚀 Running Hierarchical Memory Architecture Validation Tests\n")
    
    tests = [
        ("Import Tests", test_imports),
        ("Data Structure Tests", test_data_structures),
        ("Conversation Summarizer", test_conversation_summarizer),
        ("Context Assembler", test_context_assembler),
        ("Migration Manager", test_migration_manager),
        ("Hierarchical Manager", test_hierarchical_manager_creation)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
            else:
                failed += 1
                
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            failed += 1
    
    print(f"\n🎯 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Hierarchical memory architecture is ready for integration.")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please fix issues before integration.")
        return False

def main():
    """Main test runner"""
    print("Hierarchical Memory Architecture - Validation Test Suite")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("src/memory/core"):
        print("❌ Error: Please run this script from the WhisperEngine root directory")
        sys.exit(1)
    
    # Run async tests
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n✅ Ready to proceed with integration and infrastructure setup!")
        sys.exit(0)
    else:
        print("\n❌ Please fix failing tests before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()