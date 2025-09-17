#!/usr/bin/env python3
"""
Character Graph Memory System Demo

This demo showcases the graph-enhanced character memory system that connects
memories through relationships and enables sophisticated memory networks.
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.characters.memory.self_memory import (
    CharacterSelfMemoryManager, 
    PersonalMemory, 
    MemoryType
)
from src.characters.memory.graph_memory import (
    CharacterGraphMemoryManager,
    CharacterMemoryNetworkIntegrator
)


async def create_demo_character():
    """Create a demo character with rich memory network"""
    print("🎭 Creating Demo Character: Dr. Elena Vasquez")
    print("=" * 60)
    
    # Initialize character memory systems
    character_id = "elena_vasquez_researcher"
    base_memory = CharacterSelfMemoryManager(character_id)
    
    # Initialize graph memory system
    graph_memory = CharacterGraphMemoryManager(character_id, base_memory)
    
    # For the demo, create a simple network integrator without full integration
    network_integrator = CharacterMemoryNetworkIntegrator(character_id, None)
    network_integrator.graph_memory_manager = graph_memory
    
    # Initialize character in graph database
    await network_integrator.initialize_graph_integration(
        character_name="Dr. Elena Vasquez",
        occupation="Research Scientist",
        age=34
    )
    
    print("✅ Character initialized in graph database")
    return graph_memory, network_integrator


async def create_connected_memories(graph_memory: CharacterGraphMemoryManager):
    """Create a network of interconnected memories"""
    print("\n🧠 Creating Connected Memory Network")
    print("=" * 60)
    
    # Educational memories - forming a temporal sequence
    education_memories = [
        PersonalMemory(
            memory_id=str(uuid.uuid4()),
            character_id=graph_memory.character_id,
            content="Started undergraduate studies in biochemistry at MIT. Fascinated by molecular interactions and protein folding mechanisms. Professor Martinez's organic chemistry class sparked my passion for research.",
            memory_type=MemoryType.EDUCATION,
            emotional_weight=0.8,
            formative_impact="high",
            themes=["university", "biochemistry", "MIT", "research_passion", "mentorship"],
            location="Cambridge, MA",
            related_people=["Professor Martinez"],
            created_date=datetime.now() - timedelta(days=4000)  # ~11 years ago
        ),
        PersonalMemory(
            memory_id=str(uuid.uuid4()),
            character_id=graph_memory.character_id,
            content="Completed my PhD thesis on 'Protein Folding Dynamics in Neurodegenerative Diseases' under Dr. Chen's supervision. The research revealed novel therapeutic targets for Alzheimer's disease.",
            memory_type=MemoryType.EDUCATION,
            emotional_weight=0.9,
            formative_impact="high",
            themes=["PhD", "protein_folding", "neurodegeneration", "research", "breakthrough", "mentorship"],
            location="Cambridge, MA",
            related_people=["Dr. Chen"],
            created_date=datetime.now() - timedelta(days=2500)  # ~7 years ago
        )
    ]
    
    # Career memories - connected through shared themes
    career_memories = [
        PersonalMemory(
            memory_id=str(uuid.uuid4()),
            character_id=graph_memory.character_id,
            content="First day at the Neurological Research Institute. Dr. Chen recommended me for this position. Excited to continue protein folding research with state-of-the-art equipment and collaborative team.",
            memory_type=MemoryType.CAREER,
            emotional_weight=0.85,
            formative_impact="medium",
            themes=["new_job", "research_institute", "protein_folding", "collaboration", "career_growth"],
            location="San Francisco, CA",
            related_people=["Dr. Chen", "Research Team"],
            created_date=datetime.now() - timedelta(days=2200)  # ~6 years ago
        ),
        PersonalMemory(
            memory_id=str(uuid.uuid4()),
            character_id=graph_memory.character_id,
            content="Major breakthrough! Our team discovered a new protein folding pathway that could lead to early Alzheimer's intervention. The excitement in the lab was electric. Dr. Rodriguez called it 'paradigm-shifting research.'",
            memory_type=MemoryType.CAREER,
            emotional_weight=0.95,
            formative_impact="high",
            themes=["breakthrough", "protein_folding", "Alzheimer_research", "team_success", "recognition"],
            location="San Francisco, CA",
            related_people=["Dr. Rodriguez", "Research Team"],
            created_date=datetime.now() - timedelta(days=800)  # ~2 years ago
        )
    ]
    
    # Personal memories - emotionally connected
    personal_memories = [
        PersonalMemory(
            memory_id=str(uuid.uuid4()),
            character_id=graph_memory.character_id,
            content="Grandmother Rosa was diagnosed with Alzheimer's disease today. Watching her struggle with memory loss makes my research feel more personal and urgent. I'm determined to find answers.",
            memory_type=MemoryType.EMOTIONAL_MOMENT,
            emotional_weight=0.2,  # Sad but motivating
            formative_impact="high",
            themes=["family", "Alzheimer_disease", "personal_motivation", "loss", "determination"],
            location="Home",
            related_people=["Grandmother Rosa"],
            created_date=datetime.now() - timedelta(days=1500)  # ~4 years ago
        ),
        PersonalMemory(
            memory_id=str(uuid.uuid4()),
            character_id=graph_memory.character_id,
            content="Celebrated our research breakthrough with the team at Mario's restaurant. Sarah, our lab technician, said our work could help millions of families like mine. Grandmother Rosa would be proud.",
            memory_type=MemoryType.EMOTIONAL_MOMENT,
            emotional_weight=0.9,
            formative_impact="medium",
            themes=["celebration", "team_bonding", "family_pride", "breakthrough", "personal_connection"],
            location="Mario's Restaurant",
            related_people=["Sarah", "Research Team", "Grandmother Rosa"],
            created_date=datetime.now() - timedelta(days=790)  # ~2 years ago
        )
    ]
    
    # Store all memories in graph database with automatic relationship detection
    all_memories = education_memories + career_memories + personal_memories
    
    for i, memory in enumerate(all_memories):
        success = await graph_memory.store_memory_with_graph(memory)
        if success:
            print(f"✅ Memory {i+1}/6: {memory.memory_type.value.title()} - {memory.themes[0]}")
        else:
            print(f"❌ Failed to store memory {i+1}")
        
        # Small delay to ensure proper temporal ordering
        await asyncio.sleep(0.1)
    
    return all_memories


async def demonstrate_memory_connections(graph_memory: CharacterGraphMemoryManager, memories):
    """Demonstrate how memories are connected through the graph"""
    print("\n🕸️ Memory Network Connections")
    print("=" * 60)
    
    # Get network analysis
    network_analysis = await graph_memory.get_memory_network_analysis()
    
    print("📊 Network Statistics:")
    print(f"   Total Memories: {network_analysis.get('total_memories', 0)}")
    print(f"   Total Connections: {network_analysis.get('total_connections', 0)}")
    print(f"   Connection Density: {network_analysis.get('connection_density', 0):.2f}")
    print(f"   Network Complexity: {network_analysis.get('network_complexity', 'unknown')}")
    print(f"   Average Emotional Weight: {network_analysis.get('average_emotional_weight', 0):.2f}")
    
    # Show top themes
    top_themes = network_analysis.get('top_themes', [])
    if top_themes:
        print("\n🎯 Top Memory Themes:")
        for theme in top_themes[:5]:
            print(f"   • {theme['theme']}: {theme['count']} memories")
    
    # Demonstrate connected memories for the breakthrough memory
    if memories and len(memories) >= 4:
        breakthrough_memory = memories[3]  # Career breakthrough memory
        print("\n🔗 Connections for Breakthrough Memory:")
        print(f"   Memory: {breakthrough_memory.content[:80]}...")
        
        connected = await graph_memory.get_connected_memories(
            breakthrough_memory.memory_id,
            limit=10
        )
        
        for i, connection in enumerate(connected):
            memory_data = connection.get('memory', {})
            depth = connection.get('connection_depth', 0)
            relationships = connection.get('relationships', [])
            
            print(f"   {i+1}. Connected Memory (depth {depth}):")
            print(f"      Content: {memory_data.get('content', 'N/A')[:60]}...")
            print(f"      Themes: {memory_data.get('themes', [])}")
            if relationships:
                print(f"      Relationship Types: {[r.get('type', 'unknown') for r in relationships]}")
    
    # Find memory paths between education and personal motivation
    if memories and len(memories) >= 5:
        education_memory = memories[0]
        personal_memory = memories[4]
        
        print("\n🛤️ Memory Paths from Education to Personal Motivation:")
        paths = await graph_memory.find_memory_paths(
            education_memory.memory_id,
            personal_memory.memory_id,
            max_hops=3
        )
        
        if paths:
            print(f"   Found {len(paths)} connection path(s)")
            for i, path in enumerate(paths):
                print(f"   Path {i+1}: {len(path)} steps")
        else:
            print("   No direct paths found (memories may be connected through broader themes)")


async def demonstrate_enhanced_recall(graph_memory: CharacterGraphMemoryManager):
    """Demonstrate enhanced memory recall using graph relationships"""
    print("\n🎯 Enhanced Memory Recall with Graph Relationships")
    print("=" * 60)
    
    # Test different conversation themes
    test_themes = [
        ["research", "breakthrough"],
        ["family", "motivation"],
        ["education", "mentorship"],
        ["protein_folding", "Alzheimer_research"]
    ]
    
    for themes in test_themes:
        print(f"\n🔍 Searching for memories related to: {', '.join(themes)}")
        
        # Get basic relevant memories from base system
        relevant_memories = graph_memory.base_memory_manager.recall_memories(
            themes=themes,
            limit=3
        )
        
        print(f"   Found {len(relevant_memories)} relevant memories:")
        
        for i, memory in enumerate(relevant_memories):
            # Get connected memories for each relevant memory
            connected = await graph_memory.get_connected_memories(
                memory.memory_id,
                limit=3,
                max_depth=2
            )
            
            print(f"\n   Memory {i+1}:")
            print(f"     Content: {memory.content[:80]}...")
            print(f"     Themes: {memory.themes}")
            print(f"     Network Connections: {len(connected)}")
            print(f"     Emotional Weight: {memory.emotional_weight}")
            
            if connected:
                print("     Connected Memories:")
                for j, conn in enumerate(connected[:2]):  # Show top 2 connections
                    conn_memory = conn.get('memory', {})
                    print(f"       {j+1}. {conn_memory.get('content', 'N/A')[:50]}...")


async def show_memory_insights(network_integrator: CharacterMemoryNetworkIntegrator):
    """Show insights about the character's memory network"""
    print("\n🧭 Character Memory Network Insights")
    print("=" * 60)
    
    insights = await network_integrator.get_memory_network_insights()
    
    if insights.get('graph_enabled'):
        network_analysis = insights.get('network_analysis', {})
        insight_list = insights.get('insights', [])
        
        print("📈 Network Analysis:")
        for key, value in network_analysis.items():
            if key != 'top_themes':
                print(f"   {key.replace('_', ' ').title()}: {value}")
        
        print("\n💡 Character Insights:")
        for insight in insight_list:
            print(f"   • {insight}")
        
        # Show how this could be used in conversation
        print("\n🎭 Conversation Application:")
        print("   This memory network analysis reveals that Elena:")
        print("   - Has a strong research focus with personal motivation")
        print("   - Connects scientific achievements to family experiences")
        print("   - Shows consistent character development from education to career")
        print("   - Has emotionally rich memories that could drive authentic responses")
        
    else:
        print("❌ Graph database not available, using basic memory only")


async def demonstrate_real_time_integration():
    """Demonstrate how graph memories integrate with real-time conversations"""
    print("\n💬 Real-Time Conversation Integration")
    print("=" * 60)
    
    # Simulate a conversation about research challenges
    conversation_content = """
    User: What drives you to continue your research even when experiments fail?
    Elena: Every failed experiment brings me closer to understanding protein folding mechanisms. 
    When I think about families affected by Alzheimer's, including my own, I find the strength 
    to persist. Each small discovery could lead to treatments that preserve precious memories.
    """
    
    print("🗨️ Sample Conversation:")
    print(conversation_content)
    
    print("\n🧠 How Graph Memory Would Enhance This:")
    print("   1. Character memories about grandmother's Alzheimer's diagnosis")
    print("   2. Connected memories about research breakthroughs and team celebrations")
    print("   3. Educational memories showing long-term research commitment")
    print("   4. Personal motivation memories linking family to professional goals")
    print("   5. Network relationships revealing consistent character development")
    
    print("\n✨ Result: More authentic, consistent, and emotionally resonant responses")


async def main():
    """Main demo execution"""
    print("🚀 Character Graph Memory System Demo")
    print("=" * 80)
    print("This demo showcases advanced character memory networks using Neo4j")
    print("graph database integration for connected, relationship-aware memories.")
    print("=" * 80)
    
    try:
        # Create demo character
        graph_memory, network_integrator = await create_demo_character()
        
        # Create connected memories
        memories = await create_connected_memories(graph_memory)
        
        # Demonstrate memory connections
        await demonstrate_memory_connections(graph_memory, memories)
        
        # Demonstrate enhanced recall
        await demonstrate_enhanced_recall(graph_memory)
        
        # Show memory insights
        await show_memory_insights(network_integrator)
        
        # Demonstrate real-time integration
        await demonstrate_real_time_integration()
        
        print("\n" + "=" * 80)
        print("✅ Demo completed successfully!")
        print("\n🎯 Key Features Demonstrated:")
        print("   • Character nodes and memory nodes in Neo4j graph database")
        print("   • Automatic relationship detection between memories")
        print("   • Theme-based, temporal, and emotional memory associations")
        print("   • Network analysis and complexity metrics")
        print("   • Enhanced memory recall using graph traversal")
        print("   • Character development insights from memory patterns")
        print("   • Real-time conversation integration with graph memories")
        
        print("\n📊 Graph Memory Benefits:")
        print("   • Richer character consistency through connected memories")
        print("   • More authentic emotional responses via memory relationships") 
        print("   • Character growth tracking through memory network evolution")
        print("   • Cross-character memory sharing capabilities")
        print("   • Advanced memory clustering and thematic organization")
        
    except (ConnectionError, ImportError, AttributeError) as e:
        print(f"\n❌ Demo failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("   • Ensure Neo4j is running (docker compose up neo4j)")
        print("   • Check graph database environment variables")
        print("   • Verify character memory system is properly initialized")
        
        # Fallback demo without graph database
        print("\n🔄 Running basic memory demo without graph database...")
        await basic_memory_demo()


async def basic_memory_demo():
    """Fallback demo using basic character memory system"""
    print("\n📝 Basic Character Memory Demo (No Graph Database)")
    print("=" * 60)
    
    character_id = "elena_basic_demo"
    base_memory = CharacterSelfMemoryManager(character_id)
    
    # Create a few memories
    memory1 = PersonalMemory(
        memory_id=str(uuid.uuid4()),
        character_id=character_id,
        content="Started PhD research on protein folding dynamics",
        memory_type=MemoryType.EDUCATION,
        emotional_weight=0.8,
        formative_impact="high",
        themes=["education", "research", "protein_folding"],
        created_date=datetime.now()
    )
    
    memory2 = PersonalMemory(
        memory_id=str(uuid.uuid4()),
        character_id=character_id,
        content="Grandmother diagnosed with Alzheimer's disease",
        memory_type=MemoryType.EMOTIONAL_MOMENT,
        emotional_weight=0.3,
        formative_impact="high",
        themes=["family", "Alzheimer_disease", "motivation"],
        created_date=datetime.now()
    )
    
    # Store memories
    base_memory.store_memory(memory1)
    base_memory.store_memory(memory2)
    
    # Recall memories
    recalled = base_memory.recall_memories(themes=["research"], limit=5)
    
    print(f"✅ Created and recalled {len(recalled)} memories")
    print("✅ Basic character memory system working")
    print("\n💡 For full graph capabilities, start Neo4j database")


if __name__ == "__main__":
    asyncio.run(main())