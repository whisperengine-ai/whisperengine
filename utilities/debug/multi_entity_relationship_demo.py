"""
Comprehensive Multi-Entity Relationship Demo

This demo showcases the complete multi-entity association system:
- Characters ↔ Users ↔ AI "Self" relationships
- Dynamic relationship evolution
- Cross-entity awareness and introductions
- AI-facilitated relationship management
"""

import asyncio
import logging
import json
from typing import Dict, List, Any
from datetime import datetime

from src.graph_database.multi_entity_manager import MultiEntityRelationshipManager
from src.graph_database.ai_self_bridge import AISelfEntityBridge
from src.graph_database.multi_entity_models import EntityType, RelationshipType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiEntityDemo:
    """Comprehensive demonstration of multi-entity relationship capabilities"""
    
    def __init__(self):
        self.relationship_manager = MultiEntityRelationshipManager()
        self.ai_bridge = AISelfEntityBridge()
        self.demo_entities = {
            'users': {},
            'characters': {},
            'ai_self': None
        }
        
    async def run_complete_demo(self) -> Dict[str, Any]:
        """Run the complete multi-entity relationship demonstration"""
        logger.info("🎭 Starting Comprehensive Multi-Entity Relationship Demo")
        
        demo_results = {
            "timestamp": datetime.now().isoformat(),
            "demo_phases": {},
            "final_summary": {}
        }
        
        try:
            # Phase 1: Initialize System and Entities
            logger.info("\n📋 Phase 1: System Initialization")
            phase1_results = await self._phase1_initialize_system()
            demo_results["demo_phases"]["phase1_initialization"] = phase1_results
            
            # Phase 2: Create Multi-Entity Network
            logger.info("\n🌐 Phase 2: Multi-Entity Network Creation")
            phase2_results = await self._phase2_create_network()
            demo_results["demo_phases"]["phase2_network_creation"] = phase2_results
            
            # Phase 3: Relationship Evolution Through Interactions
            logger.info("\n📈 Phase 3: Relationship Evolution")
            phase3_results = await self._phase3_relationship_evolution()
            demo_results["demo_phases"]["phase3_evolution"] = phase3_results
            
            # Phase 4: AI-Facilitated Cross-Entity Introductions
            logger.info("\n🤝 Phase 4: AI-Facilitated Introductions")
            phase4_results = await self._phase4_ai_facilitated_introductions()
            demo_results["demo_phases"]["phase4_introductions"] = phase4_results
            
            # Phase 5: Advanced Relationship Analysis
            logger.info("\n🔍 Phase 5: Advanced Relationship Analysis")
            phase5_results = await self._phase5_advanced_analysis()
            demo_results["demo_phases"]["phase5_analysis"] = phase5_results
            
            # Generate final summary
            demo_results["final_summary"] = await self._generate_final_summary()
            
            logger.info("✅ Multi-Entity Relationship Demo completed successfully!")
            return demo_results
            
        except Exception as e:
            logger.error("❌ Demo failed: %s", e)
            demo_results["error"] = str(e)
            return demo_results
    
    async def _phase1_initialize_system(self) -> Dict[str, Any]:
        """Phase 1: Initialize the multi-entity system"""
        try:
            # Initialize relationship manager and AI bridge
            await self.relationship_manager.initialize_schema()
            await self.ai_bridge.initialize()
            
            # Get AI Self entity
            ai_self_id = await self.relationship_manager.get_or_create_ai_self()
            self.demo_entities['ai_self'] = ai_self_id
            
            logger.info("✅ System initialized with AI Self: %s", ai_self_id[:8] if ai_self_id else "None")
            
            return {
                "status": "success",
                "ai_self_id": ai_self_id,
                "components_initialized": ["relationship_manager", "ai_bridge", "schema"]
            }
            
        except Exception as e:
            logger.error("Phase 1 failed: %s", e)
            return {"status": "failed", "error": str(e)}
    
    async def _phase2_create_network(self) -> Dict[str, Any]:
        """Phase 2: Create multi-entity network with diverse relationships"""
        try:
            network_results = {
                "users_created": [],
                "characters_created": [],
                "initial_relationships": []
            }
            
            # Create diverse users
            users_data = [
                {
                    "discord_id": "user_001",
                    "username": "alice_writer",
                    "display_name": "Alice (Creative Writer)",
                    "personality_traits": ["creative", "introspective", "empathetic"],
                    "communication_style": "thoughtful",
                    "preferences": {"topics": ["writing", "literature", "philosophy"]},
                    "privacy_level": "standard"
                },
                {
                    "discord_id": "user_002", 
                    "username": "bob_engineer",
                    "display_name": "Bob (Software Engineer)",
                    "personality_traits": ["analytical", "practical", "curious"],
                    "communication_style": "direct",
                    "preferences": {"topics": ["technology", "programming", "science"]},
                    "privacy_level": "high"
                },
                {
                    "discord_id": "user_003",
                    "username": "charlie_artist",
                    "display_name": "Charlie (Digital Artist)",
                    "personality_traits": ["creative", "visual", "passionate"],
                    "communication_style": "expressive",
                    "preferences": {"topics": ["art", "design", "creativity"]},
                    "privacy_level": "open"
                }
            ]
            
            # Create users
            for user_data in users_data:
                user_id = await self.relationship_manager.create_user_entity(user_data)
                if user_id:
                    self.demo_entities['users'][user_data['username']] = user_id
                    network_results["users_created"].append({
                        "username": user_data['username'],
                        "user_id": user_id,
                        "traits": user_data['personality_traits']
                    })
                    logger.info("Created user: %s (%s)", user_data['display_name'], user_id[:8])
            
            # Create diverse characters with different creators
            characters_data = [
                {
                    "name": "Sage the Philosopher",
                    "occupation": "philosopher",
                    "age": 45,
                    "personality_traits": ["wise", "thoughtful", "patient", "introspective"],
                    "communication_style": "philosophical",
                    "background_summary": "A wise philosopher who enjoys deep conversations about life and meaning",
                    "preferred_topics": ["philosophy", "ethics", "wisdom", "life_lessons"],
                    "conversation_style": "reflective",
                    "creator": "alice_writer"
                },
                {
                    "name": "Nova the Innovator",
                    "occupation": "inventor",
                    "age": 28,
                    "personality_traits": ["innovative", "energetic", "optimistic", "curious"],
                    "communication_style": "enthusiastic",
                    "background_summary": "A brilliant inventor always working on the next breakthrough technology",
                    "preferred_topics": ["technology", "innovation", "future", "problem_solving"],
                    "conversation_style": "dynamic",
                    "creator": "bob_engineer"
                },
                {
                    "name": "Luna the Artist",
                    "occupation": "digital_artist",
                    "age": 24,
                    "personality_traits": ["creative", "sensitive", "intuitive", "expressive"],
                    "communication_style": "artistic",
                    "background_summary": "A talented digital artist who sees beauty and inspiration everywhere",
                    "preferred_topics": ["art", "creativity", "beauty", "inspiration"],
                    "conversation_style": "imaginative",
                    "creator": "charlie_artist"
                },
                {
                    "name": "Echo the Storyteller",
                    "occupation": "storyteller",
                    "age": 32,
                    "personality_traits": ["charismatic", "imaginative", "empathetic", "wise"],
                    "communication_style": "narrative",
                    "background_summary": "A master storyteller who weaves tales that touch hearts and minds",
                    "preferred_topics": ["stories", "mythology", "human_nature", "adventure"],
                    "conversation_style": "storytelling",
                    "creator": "alice_writer"  # Alice creates multiple characters
                }
            ]
            
            # Create characters
            for char_data in characters_data:
                creator_username = char_data.pop('creator')
                creator_id = self.demo_entities['users'].get(creator_username)
                
                character_id = await self.relationship_manager.create_character_entity(
                    char_data, creator_id
                )
                
                if character_id:
                    self.demo_entities['characters'][char_data['name']] = character_id
                    network_results["characters_created"].append({
                        "name": char_data['name'],
                        "character_id": character_id,
                        "creator": creator_username,
                        "traits": char_data['personality_traits']
                    })
                    logger.info("Created character: %s (%s) by %s", 
                              char_data['name'], character_id[:8], creator_username)
            
            # Create additional cross-entity relationships
            cross_relationships = [
                # Users appreciating each other's characters
                {
                    "from": self.demo_entities['users']['bob_engineer'],
                    "to": self.demo_entities['characters']['Sage the Philosopher'],
                    "from_type": EntityType.USER,
                    "to_type": EntityType.CHARACTER,
                    "rel_type": RelationshipType.FAVORITE_OF,
                    "context": "Bob appreciates Sage's philosophical insights",
                    "trust": 0.6,
                    "familiarity": 0.4
                },
                # Characters knowing about each other through shared creator
                {
                    "from": self.demo_entities['characters']['Sage the Philosopher'],
                    "to": self.demo_entities['characters']['Echo the Storyteller'],
                    "from_type": EntityType.CHARACTER,
                    "to_type": EntityType.CHARACTER,
                    "rel_type": RelationshipType.KNOWS_ABOUT,
                    "context": "Both created by Alice, share narrative wisdom",
                    "trust": 0.7,
                    "familiarity": 0.6
                },
                # Cross-domain inspiration
                {
                    "from": self.demo_entities['characters']['Luna the Artist'],
                    "to": self.demo_entities['characters']['Nova the Innovator'],
                    "from_type": EntityType.CHARACTER,
                    "to_type": EntityType.CHARACTER,
                    "rel_type": RelationshipType.INSPIRED_BY,
                    "context": "Luna draws inspiration from Nova's innovative thinking",
                    "trust": 0.5,
                    "familiarity": 0.3
                }
            ]
            
            # Create cross-relationships
            for rel in cross_relationships:
                success = await self.relationship_manager.create_relationship(
                    rel["from"], rel["to"], rel["from_type"], rel["to_type"],
                    rel["rel_type"], rel["context"], rel["trust"], rel["familiarity"]
                )
                if success:
                    network_results["initial_relationships"].append({
                        "relationship_type": rel["rel_type"].value,
                        "context": rel["context"],
                        "trust_level": rel["trust"]
                    })
            
            logger.info("✅ Created network: %d users, %d characters, %d cross-relationships",
                       len(network_results["users_created"]),
                       len(network_results["characters_created"]),
                       len(network_results["initial_relationships"]))
            
            return network_results
            
        except Exception as e:
            logger.error("Phase 2 failed: %s", e)
            return {"status": "failed", "error": str(e)}
    
    async def _phase3_relationship_evolution(self) -> Dict[str, Any]:
        """Phase 3: Simulate relationship evolution through interactions"""
        try:
            evolution_results = {
                "interactions_recorded": [],
                "relationship_changes": []
            }
            
            # Simulate various interactions
            interactions = [
                # Alice and Sage (creator-character) deep conversation
                {
                    "from": self.demo_entities['users']['alice_writer'],
                    "to": self.demo_entities['characters']['Sage the Philosopher'],
                    "type": "deep_conversation",
                    "summary": "Discussed the nature of creativity and wisdom in writing",
                    "tone": "philosophical",
                    "sentiment": 0.8,
                    "duration": 45.0
                },
                # Bob learning from Nova (user-character) technical discussion
                {
                    "from": self.demo_entities['users']['bob_engineer'],
                    "to": self.demo_entities['characters']['Nova the Innovator'],
                    "type": "technical_discussion",
                    "summary": "Explored innovative approaches to software architecture",
                    "tone": "analytical",
                    "sentiment": 0.7,
                    "duration": 30.0
                },
                # Charlie getting artistic inspiration from Luna
                {
                    "from": self.demo_entities['users']['charlie_artist'],
                    "to": self.demo_entities['characters']['Luna the Artist'],
                    "type": "creative_collaboration",
                    "summary": "Shared artistic techniques and inspiration sources",
                    "tone": "inspiring",
                    "sentiment": 0.9,
                    "duration": 60.0
                },
                # AI Self facilitating character interactions
                {
                    "from": self.demo_entities['ai_self'],
                    "to": self.demo_entities['characters']['Sage the Philosopher'],
                    "type": "character_development",
                    "summary": "AI Self helped Sage develop deeper philosophical insights",
                    "tone": "supportive",
                    "sentiment": 0.6,
                    "duration": 15.0
                },
                # Cross-character interaction (Sage and Echo storytelling)
                {
                    "from": self.demo_entities['characters']['Sage the Philosopher'],
                    "to": self.demo_entities['characters']['Echo the Storyteller'],
                    "type": "narrative_philosophy",
                    "summary": "Sage and Echo explored philosophical themes through storytelling",
                    "tone": "collaborative",
                    "sentiment": 0.8,
                    "duration": 40.0
                }
            ]
            
            # Record interactions
            for interaction in interactions:
                success = await self.relationship_manager.record_interaction(
                    interaction["from"],
                    interaction["to"],
                    interaction["type"],
                    interaction["summary"],
                    interaction["tone"],
                    interaction["sentiment"],
                    interaction["duration"]
                )
                
                if success:
                    evolution_results["interactions_recorded"].append({
                        "type": interaction["type"],
                        "summary": interaction["summary"],
                        "sentiment": interaction["sentiment"]
                    })
                    logger.info("Recorded interaction: %s (%s sentiment)", 
                              interaction["type"], interaction["sentiment"])
            
            # Analyze relationship changes
            key_relationships = [
                (self.demo_entities['users']['alice_writer'], 
                 self.demo_entities['characters']['Sage the Philosopher']),
                (self.demo_entities['characters']['Sage the Philosopher'],
                 self.demo_entities['characters']['Echo the Storyteller']),
                (self.demo_entities['users']['bob_engineer'],
                 self.demo_entities['characters']['Nova the Innovator'])
            ]
            
            for entity1_id, entity2_id in key_relationships:
                evolution = await self.ai_bridge.analyze_relationship_evolution(entity1_id, entity2_id)
                if evolution.get("current_stage"):
                    evolution_results["relationship_changes"].append({
                        "entities": f"{entity1_id[:8]} ↔ {entity2_id[:8]}",
                        "current_stage": evolution["current_stage"],
                        "trust_level": evolution.get("trust_level", 0),
                        "relationship_strength": evolution.get("relationship_strength", 0),
                        "development_trend": evolution.get("development_trend", "unknown")
                    })
            
            logger.info("✅ Recorded %d interactions, analyzed %d relationship evolutions",
                       len(evolution_results["interactions_recorded"]),
                       len(evolution_results["relationship_changes"]))
            
            return evolution_results
            
        except Exception as e:
            logger.error("Phase 3 failed: %s", e)
            return {"status": "failed", "error": str(e)}
    
    async def _phase4_ai_facilitated_introductions(self) -> Dict[str, Any]:
        """Phase 4: AI Self facilitates cross-entity introductions"""
        try:
            introduction_results = {
                "introductions_attempted": [],
                "successful_introductions": [],
                "compatibility_analyses": []
            }
            
            # AI Self facilitates introductions between users and characters they haven't met
            introduction_scenarios = [
                # Introduce Bob to Sage (cross-domain learning)
                {
                    "character": self.demo_entities['characters']['Sage the Philosopher'],
                    "user": self.demo_entities['users']['bob_engineer'],
                    "context": "Bob could benefit from Sage's philosophical perspective on technology ethics"
                },
                # Introduce Charlie to Nova (creative-technical fusion)
                {
                    "character": self.demo_entities['characters']['Nova the Innovator'],
                    "user": self.demo_entities['users']['charlie_artist'],
                    "context": "Charlie's artistic vision could inspire Nova's innovations"
                },
                # Introduce Alice to Luna (creative synergy)
                {
                    "character": self.demo_entities['characters']['Luna the Artist'],
                    "user": self.demo_entities['users']['alice_writer'],
                    "context": "Both share deep creative sensibilities across different mediums"
                }
            ]
            
            # Perform AI-facilitated introductions
            for scenario in introduction_scenarios:
                introduction_result = await self.ai_bridge.introduce_character_to_user(
                    scenario["character"],
                    scenario["user"],
                    scenario["context"]
                )
                
                introduction_results["introductions_attempted"].append({
                    "character_id": scenario["character"][:8],
                    "user_id": scenario["user"][:8],
                    "context": scenario["context"]
                })
                
                if introduction_result.get("introduction_successful"):
                    introduction_results["successful_introductions"].append({
                        "character_id": scenario["character"][:8],
                        "user_id": scenario["user"][:8],
                        "compatibility_score": introduction_result.get("relationship_potential", 0),
                        "conversation_starters": introduction_result.get("recommended_conversation_starters", [])
                    })
                    logger.info("✅ Successful introduction: %s ↔ %s (compatibility: %.2f)",
                              scenario["character"][:8], scenario["user"][:8],
                              introduction_result.get("relationship_potential", 0))
                
                # Store compatibility analysis
                if "compatibility_analysis" in introduction_result:
                    introduction_results["compatibility_analyses"].append({
                        "character_id": scenario["character"][:8],
                        "user_id": scenario["user"][:8],
                        "analysis": introduction_result["compatibility_analysis"]
                    })
            
            logger.info("✅ Completed %d introductions, %d successful",
                       len(introduction_results["introductions_attempted"]),
                       len(introduction_results["successful_introductions"]))
            
            return introduction_results
            
        except Exception as e:
            logger.error("Phase 4 failed: %s", e)
            return {"status": "failed", "error": str(e)}
    
    async def _phase5_advanced_analysis(self) -> Dict[str, Any]:
        """Phase 5: Advanced relationship analysis and network insights"""
        try:
            analysis_results = {
                "character_networks": {},
                "user_social_summaries": {},
                "ai_self_overview": {},
                "similarity_analyses": {}
            }
            
            # Analyze character networks
            for char_name, char_id in self.demo_entities['characters'].items():
                network = await self.relationship_manager.get_character_network(char_id)
                analysis_results["character_networks"][char_name] = {
                    "character_id": char_id[:8],
                    "total_relationships": network.get("total_relationships", 0),
                    "network_strength": network.get("network_strength", 0),
                    "connected_users": len(network.get("connected_users", [])),
                    "connected_characters": len(network.get("connected_characters", [])),
                    "ai_relationships": len(network.get("ai_relationships", []))
                }
                logger.info("Analyzed %s network: %d relationships, %.2f strength",
                          char_name, network.get("total_relationships", 0),
                          network.get("network_strength", 0))
            
            # Analyze user social networks
            for user_name, user_id in self.demo_entities['users'].items():
                social_summary = await self.ai_bridge.get_entity_social_network_summary(user_id)
                analysis_results["user_social_summaries"][user_name] = {
                    "user_id": user_id[:8],
                    "network_size": social_summary.get("network_size", 0),
                    "strong_relationships": social_summary.get("strong_relationships", 0),
                    "average_trust": social_summary.get("average_trust_level", 0),
                    "network_diversity": social_summary.get("network_diversity", 0),
                    "health_assessment": social_summary.get("ai_network_assessment", {}).get("assessment", "unknown")
                }
                logger.info("Analyzed %s social network: %d connections, %s health",
                          user_name, social_summary.get("network_size", 0),
                          social_summary.get("ai_network_assessment", {}).get("assessment", "unknown"))
            
            # Get AI Self overview - using entity social network summary as proxy
            ai_overview = await self.ai_bridge.get_entity_social_network_summary(self.demo_entities['ai_self'])
            analysis_results["ai_self_overview"] = {
                "network_size": ai_overview.get("network_size", 0),
                "strong_relationships": ai_overview.get("strong_relationships", 0),
                "total_managed": ai_overview.get("network_size", 0),
                "health_assessment": ai_overview.get("ai_network_assessment", {}).get("assessment", "unknown")
            }
            logger.info("AI Self network: %d connections, %s health",
                       ai_overview.get("network_size", 0),
                       ai_overview.get("ai_network_assessment", {}).get("assessment", "unknown"))
            
            # Analyze character similarities
            similarity_pairs = [
                ("Sage the Philosopher", "Echo the Storyteller"),  # Both wisdom-focused
                ("Luna the Artist", "Nova the Innovator"),        # Both creative
            ]
            
            for char1_name, char2_name in similarity_pairs:
                char1_id = self.demo_entities['characters'].get(char1_name)
                char2_id = self.demo_entities['characters'].get(char2_name)
                
                if char1_id and char2_id:
                    similarities = await self.relationship_manager.find_character_similarities(char1_id, 0.3)
                    # Find similarity data for char2
                    for sim in similarities:
                        if sim['character'].get('id') == char2_id:
                            analysis_results["similarity_analyses"][f"{char1_name} ↔ {char2_name}"] = {
                                "similarity_score": sim["similarity_score"],
                                "trait_overlap": sim["trait_overlap"],
                                "topic_overlap": sim["topic_overlap"],
                                "style_match": sim["style_match"]
                            }
                            logger.info("Similarity %s ↔ %s: %.2f",
                                      char1_name, char2_name, sim["similarity_score"])
                            break
            
            logger.info("✅ Completed advanced analysis of all network relationships")
            
            return analysis_results
            
        except Exception as e:
            logger.error("Phase 5 failed: %s", e)
            return {"status": "failed", "error": str(e)}
    
    async def _generate_final_summary(self) -> Dict[str, Any]:
        """Generate comprehensive summary of the multi-entity demo"""
        try:
            summary = {
                "entities_created": {
                    "users": len(self.demo_entities['users']),
                    "characters": len(self.demo_entities['characters']),
                    "ai_self": 1 if self.demo_entities['ai_self'] else 0
                },
                "relationship_capabilities_demonstrated": [
                    "User-Character creator relationships",
                    "Character-Character knowledge and inspiration",
                    "AI Self entity management and facilitation",
                    "Cross-domain relationship introductions",
                    "Dynamic trust and familiarity evolution",
                    "Compatibility analysis and matching",
                    "Social network health assessment",
                    "Character similarity detection"
                ],
                "key_insights": [
                    "Multi-entity associations enable rich relationship networks",
                    "AI Self can facilitate meaningful connections across entities",
                    "Relationship evolution through interactions builds authentic bonds",
                    "Cross-domain compatibility analysis improves introduction success",
                    "Network analysis provides valuable insights for relationship management"
                ],
                "technical_achievements": [
                    "Graph database multi-entity schema implementation",
                    "Dynamic relationship strength calculation",
                    "AI-facilitated compatibility analysis",
                    "Cross-entity interaction tracking",
                    "Network health assessment algorithms",
                    "Character similarity matching system"
                ]
            }
            
            logger.info("📊 Demo Summary: %d users, %d characters, %d relationship types demonstrated",
                       summary["entities_created"]["users"],
                       summary["entities_created"]["characters"],
                       len(summary["relationship_capabilities_demonstrated"]))
            
            return summary
            
        except Exception as e:
            logger.error("Failed to generate final summary: %s", e)
            return {"error": str(e)}


async def main():
    """Run the comprehensive multi-entity relationship demo"""
    print("🎭 WhisperEngine Multi-Entity Relationship System Demo")
    print("=" * 60)
    
    demo = MultiEntityDemo()
    results = await demo.run_complete_demo()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"multi_entity_demo_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Demo results saved to: {filename}")
    print("\n✨ Multi-Entity Association Demo Complete!")
    print("\nKey Capabilities Demonstrated:")
    
    if "final_summary" in results:
        for capability in results["final_summary"].get("relationship_capabilities_demonstrated", []):
            print(f"  ✅ {capability}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())