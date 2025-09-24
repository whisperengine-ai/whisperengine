"""
LLM-Powered Bot Self-Memory System

Uses WhisperEngine's LLM Tool Calling infrastructure to intelligently extract,
organize, and query bot personal knowledge. Provides AI-driven self-reflection
and personality evolution capabilities.
"""

import logging
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json

from src.memory.memory_protocol import MemoryManagerProtocol

logger = logging.getLogger(__name__)


@dataclass
class LLMKnowledgeExtraction:
    """Result of LLM-powered knowledge extraction"""
    categories: Dict[str, List[Dict]]
    total_items: int
    confidence_score: float
    extraction_metadata: Dict[str, Any]


@dataclass
class LLMSelfReflection:
    """Result of LLM-powered self-reflection analysis"""
    effectiveness_score: float
    authenticity_score: float
    emotional_resonance: float
    self_evaluation: str
    learning_insight: str
    improvement_suggestion: str
    dominant_personality_trait: str
    reflection_metadata: Dict[str, Any]


class LLMPoweredBotMemory:
    """
    AI-powered bot self-memory system using LLM Tool Calling.
    
    Leverages WhisperEngine's existing LLM infrastructure to intelligently:
    - Extract personal knowledge from CDL files
    - Generate self-reflections on interactions
    - Query personal knowledge contextually
    - Track personality evolution patterns
    """
    
    def __init__(self, bot_name: str, llm_client: Any, memory_manager: MemoryManagerProtocol):
        self.bot_name = bot_name
        self.llm_client = llm_client
        self.memory_manager = memory_manager
        self.namespace = f"bot_self_{bot_name}"
        
        logger.info(f"🧠 Initialized LLM-Powered Bot Memory for {bot_name}")
    
    async def extract_cdl_knowledge_with_llm(self, character_file: str) -> LLMKnowledgeExtraction:
        """
        Use LLM to intelligently extract and categorize personal knowledge from CDL file.
        
        Args:
            character_file: Path to CDL character JSON file
            
        Returns:
            LLMKnowledgeExtraction with categorized knowledge
        """
        try:
            # Load character file - handle relative paths correctly
            if character_file.startswith('characters/'):
                character_path = Path(character_file)
            else:
                character_path = Path(f"characters/examples/{character_file}")
            
            if not character_path.exists():
                logger.error(f"Character file not found: {character_path}")
                return LLMKnowledgeExtraction({}, 0, 0.0, {"error": "file_not_found"})
            
            with open(character_path, 'r', encoding='utf-8') as f:
                character_data = json.load(f)
            
            # Create LLM prompt for knowledge extraction
            extraction_prompt = self._create_knowledge_extraction_prompt(character_data, character_file)
            
            # Use LLM to extract knowledge
            extraction_result = await self.llm_client.generate_chat_completion_safe([
                {"role": "system", "content": "You are a character knowledge expert. Extract personal information from character data that would help answer personal questions authentically."},
                {"role": "user", "content": extraction_prompt}
            ])
            
            # Parse LLM response
            parsed_knowledge = self._parse_llm_knowledge_extraction(extraction_result)
            
            # Store extracted knowledge in vector memory
            total_stored = 0
            for category, knowledge_items in parsed_knowledge.items():
                for item in knowledge_items:
                    await self._store_knowledge_item(item, category)
                    total_stored += 1
            
            logger.info(f"✅ LLM extracted and stored {total_stored} knowledge items for {self.bot_name}")
            
            return LLMKnowledgeExtraction(
                categories=parsed_knowledge,
                total_items=total_stored,
                confidence_score=0.85,  # LLM-based extractions are generally reliable
                extraction_metadata={
                    "character_file": character_file,
                    "extraction_method": "llm_powered",
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to extract CDL knowledge with LLM for {self.bot_name}: {e}")
            return LLMKnowledgeExtraction({}, 0, 0.0, {"error": str(e)})
    
    def _create_knowledge_extraction_prompt(self, character_data: Dict, character_file: str) -> str:
        """Create LLM prompt for intelligent knowledge extraction"""
        
        character_json = json.dumps(character_data, indent=2)[:4000]  # Limit size for context
        
        return f"""
Analyze this character data and extract personal information that would help the character answer questions about themselves authentically.

CHARACTER FILE: {character_file}
CHARACTER DATA: {character_json}

Extract information for these categories:
1. RELATIONSHIPS - romantic status, family, friends, social connections
2. BACKGROUND - childhood, formative experiences, education, life history  
3. CURRENT_PROJECTS - work, research, goals, aspirations, active projects
4. DAILY_ROUTINE - habits, schedule, regular activities, lifestyle
5. PERSONALITY_INSIGHTS - character traits, values, fears, quirks

For each piece of information, provide:
- content: The actual information in natural language
- search_queries: List of terms/questions that would find this info
- confidence: How certain you are this information is accurate (0.0-1.0)
- relevance: How useful this would be for personal conversations (0.0-1.0)

Focus on information that would help answer personal questions like:
- "Do you have a boyfriend/girlfriend?"
- "Tell me about your childhood"  
- "What are you working on?"
- "What's your daily routine?"
- "What are you afraid of?"

Return as JSON format:
{{
  "relationships": [
    {{
      "content": "Currently single and focused on career...",
      "search_queries": ["boyfriend", "dating", "relationship", "single"],
      "confidence": 0.9,
      "relevance": 0.95
    }}
  ],
  "background": [...],
  "current_projects": [...],
  "daily_routine": [...],
  "personality_insights": [...]
}}

Be thorough but focus on the most authentic and useful personal information.
"""
    
    def _parse_llm_knowledge_extraction(self, llm_response: str) -> Dict[str, List[Dict]]:
        """Parse LLM response into structured knowledge categories"""
        try:
            # Try to extract JSON from LLM response
            import re
            
            # Look for JSON content in response
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed_data = json.loads(json_str)
                
                # Validate structure and add defaults
                valid_categories = ["relationships", "background", "current_projects", "daily_routine", "personality_insights"]
                result = {}
                
                for category in valid_categories:
                    if category in parsed_data and isinstance(parsed_data[category], list):
                        result[category] = parsed_data[category]
                    else:
                        result[category] = []
                
                return result
            else:
                logger.warning(f"Could not find JSON in LLM response for {self.bot_name}")
                return {}
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM knowledge extraction for {self.bot_name}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing LLM knowledge extraction for {self.bot_name}: {e}")
            return {}
    
    async def _store_knowledge_item(self, knowledge_item: Dict, category: str):
        """Store individual knowledge item in vector memory"""
        try:
            content = knowledge_item.get("content", "")
            search_queries = knowledge_item.get("search_queries", [])
            confidence = knowledge_item.get("confidence", 0.8)
            relevance = knowledge_item.get("relevance", 0.8)
            
            # Create searchable content
            searchable_content = f"{content}\nSearchable terms: {', '.join(search_queries)}"
            
            metadata = {
                "category": category,
                "source": "llm_extraction",
                "confidence_score": confidence,
                "relevance_score": relevance,
                "searchable_queries": search_queries,
                "bot_name": self.bot_name,
                "memory_type": "bot_self_knowledge_llm",
                "created_at": datetime.now(UTC).isoformat()
            }
            
            # Store using bot's isolated namespace
            await self.memory_manager.store_conversation(
                user_id=self.namespace,
                user_message=f"[LLM_KNOWLEDGE] {category}",
                bot_response=searchable_content,
                metadata=metadata
            )
            
            logger.debug(f"Stored LLM-extracted {category} knowledge for {self.bot_name}")
            
        except Exception as e:
            logger.error(f"Failed to store knowledge item for {self.bot_name}: {e}")
    
    async def query_personal_knowledge_with_llm(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Use LLM to intelligently search and format personal knowledge for response generation.
        
        Args:
            query: User's question or topic
            limit: Maximum number of knowledge items to consider
            
        Returns:
            LLM-formatted response with relevant knowledge and guidance
        """
        try:
            # First, get raw knowledge from vector memory
            raw_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=self.namespace,
                query=query,
                limit=limit * 2  # Get more to let LLM choose best
            )
            
            # Filter for self-knowledge
            knowledge_items = []
            for memory in raw_memories:
                metadata = memory.get('metadata', {})
                if metadata.get('memory_type') == 'bot_self_knowledge_llm':
                    content = memory.get('content', '')
                    if '\nSearchable terms:' in content:
                        content = content.split('\nSearchable terms:')[0]
                    
                    knowledge_items.append({
                        'content': content,
                        'category': metadata.get('category', 'unknown'),
                        'confidence': metadata.get('confidence_score', 0.8),
                        'relevance': memory.get('relevance_score', 0.0)
                    })
            
            if not knowledge_items:
                return {
                    "found_relevant_info": False,
                    "relevant_items": [],
                    "response_guidance": "No personal knowledge found for this query."
                }
            
            # Use LLM to intelligently select and format relevant knowledge
            knowledge_query_prompt = self._create_knowledge_query_prompt(query, knowledge_items)
            
            llm_response = await self.llm_client.generate_chat_completion_safe([
                {"role": "system", "content": f"You are {self.bot_name}, deciding which personal knowledge is most relevant to answer a user's question authentically."},
                {"role": "user", "content": knowledge_query_prompt}
            ])
            
            # Parse LLM response
            parsed_response = self._parse_llm_knowledge_query(llm_response)
            
            logger.debug(f"LLM knowledge query for '{query}' returned {len(parsed_response.get('relevant_items', []))} items")
            
            return parsed_response
            
        except Exception as e:
            logger.error(f"Failed to query personal knowledge with LLM for {self.bot_name}: {e}")
            return {
                "found_relevant_info": False,
                "relevant_items": [],
                "response_guidance": f"Error querying knowledge: {str(e)}"
            }
    
    def _create_knowledge_query_prompt(self, query: str, knowledge_items: List[Dict]) -> str:
        """Create LLM prompt for intelligent knowledge querying"""
        
        knowledge_list = ""
        for i, item in enumerate(knowledge_items, 1):
            knowledge_list += f"{i}. [{item['category'].upper()}] {item['content']} (confidence: {item['confidence']:.2f})\n"
        
        return f"""
A user is asking: "{query}"

Here is your personal knowledge that might be relevant:
{knowledge_list}

Your task:
1. Determine which knowledge items are most relevant to answering this question authentically
2. Format the relevant information for natural integration into your response
3. Provide guidance on how to use this knowledge in your reply

Return as JSON:
{{
  "found_relevant_info": true/false,
  "relevant_items": [
    {{
      "formatted_content": "How to naturally include this info in response",
      "category": "category_name",
      "confidence": 0.9
    }}
  ],
  "response_guidance": "How to approach answering this question using your knowledge",
  "authenticity_tips": "Specific ways to make the response feel genuine to your character"
}}

If no knowledge is relevant, set found_relevant_info to false and explain why.
Focus on authenticity and natural conversation flow.
"""
    
    def _parse_llm_knowledge_query(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM response for knowledge query"""
        try:
            import re
            
            # Look for JSON content in response
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed_data = json.loads(json_str)
                
                # Validate and provide defaults
                return {
                    "found_relevant_info": parsed_data.get("found_relevant_info", False),
                    "relevant_items": parsed_data.get("relevant_items", []),
                    "response_guidance": parsed_data.get("response_guidance", ""),
                    "authenticity_tips": parsed_data.get("authenticity_tips", "")
                }
            else:
                logger.warning(f"Could not find JSON in LLM knowledge query response for {self.bot_name}")
                return {"found_relevant_info": False, "relevant_items": [], "response_guidance": "Failed to parse LLM response"}
                
        except Exception as e:
            logger.error(f"Error parsing LLM knowledge query for {self.bot_name}: {e}")
            return {"found_relevant_info": False, "relevant_items": [], "response_guidance": f"Parse error: {str(e)}"}
    
    async def generate_self_reflection_with_llm(self, interaction_data: Dict) -> LLMSelfReflection:
        """
        Use LLM to generate intelligent self-reflection on bot's interaction.
        
        Args:
            interaction_data: Dict with user_message, bot_response, character_context, etc.
            
        Returns:
            LLMSelfReflection with scores and insights
        """
        try:
            # Create self-reflection prompt
            reflection_prompt = self._create_self_reflection_prompt(interaction_data)
            
            # Use LLM to analyze the interaction
            llm_response = await self.llm_client.generate_chat_completion_safe([
                {"role": "system", "content": f"You are {self.bot_name}, reflecting objectively on your recent interaction to improve future conversations."},
                {"role": "user", "content": reflection_prompt}
            ])
            
            # Parse LLM response
            parsed_reflection = self._parse_llm_self_reflection(llm_response)
            
            # Store reflection in memory
            await self._store_self_reflection(parsed_reflection, interaction_data)
            
            logger.info(f"Generated LLM self-reflection for {self.bot_name}: {parsed_reflection.learning_insight[:50]}...")
            
            return parsed_reflection
            
        except Exception as e:
            logger.error(f"Failed to generate self-reflection with LLM for {self.bot_name}: {e}")
            return LLMSelfReflection(
                effectiveness_score=0.5,
                authenticity_score=0.5,
                emotional_resonance=0.5,
                self_evaluation="Could not generate self-reflection due to error.",
                learning_insight="System error prevented reflection analysis.",
                improvement_suggestion="Fix the self-reflection system.",
                dominant_personality_trait="unknown",
                reflection_metadata={"error": str(e)}
            )
    
    def _create_self_reflection_prompt(self, interaction_data: Dict) -> str:
        """Create LLM prompt for self-reflection analysis"""
        
        user_message = interaction_data.get("user_message", "")
        bot_response = interaction_data.get("bot_response", "")
        character_context = interaction_data.get("character_context", "")
        interaction_outcome = interaction_data.get("interaction_outcome", "unknown")
        
        return f"""
Reflect on your recent interaction and provide an honest self-evaluation.

USER MESSAGE: {user_message}
YOUR RESPONSE: {bot_response}
CHARACTER CONTEXT: {character_context}
INTERACTION OUTCOME: {interaction_outcome}

Evaluate your response objectively:

1. EFFECTIVENESS (0.0-1.0): Did you address what the user needed/wanted?
2. AUTHENTICITY (0.0-1.0): Were you true to your character and personality?
3. EMOTIONAL RESONANCE (0.0-1.0): Did you connect emotionally in an appropriate way?

Provide insights:
- Brief self-evaluation (2-3 sentences about what worked or didn't work)
- Specific learning insight (what you discovered about effective communication)
- One concrete improvement for similar future conversations
- Which aspect of your personality came through strongest

Return as JSON:
{{
  "effectiveness_score": 0.85,
  "authenticity_score": 0.90,
  "emotional_resonance": 0.80,
  "self_evaluation": "I connected well with the user's question and provided helpful information...",
  "learning_insight": "I'm most effective when I combine expertise with personal passion...",
  "improvement_suggestion": "I could have asked a follow-up question to increase engagement...",
  "dominant_personality_trait": "high_openness_with_expertise",
  "conversation_effectiveness_factors": ["specific factors that made this work or not work"]
}}

Be honest and constructive. Focus on practical improvements while maintaining character authenticity.
"""
    
    def _parse_llm_self_reflection(self, llm_response: str) -> LLMSelfReflection:
        """Parse LLM response into structured self-reflection"""
        try:
            import re
            
            # Look for JSON content in response
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed_data = json.loads(json_str)
                
                return LLMSelfReflection(
                    effectiveness_score=float(parsed_data.get("effectiveness_score", 0.5)),
                    authenticity_score=float(parsed_data.get("authenticity_score", 0.5)),
                    emotional_resonance=float(parsed_data.get("emotional_resonance", 0.5)),
                    self_evaluation=parsed_data.get("self_evaluation", ""),
                    learning_insight=parsed_data.get("learning_insight", ""),
                    improvement_suggestion=parsed_data.get("improvement_suggestion", ""),
                    dominant_personality_trait=parsed_data.get("dominant_personality_trait", "unknown"),
                    reflection_metadata={
                        "conversation_effectiveness_factors": parsed_data.get("conversation_effectiveness_factors", []),
                        "timestamp": datetime.now(UTC).isoformat()
                    }
                )
            else:
                logger.warning(f"Could not find JSON in LLM self-reflection response for {self.bot_name}")
                return self._create_default_reflection("Failed to parse LLM response")
                
        except Exception as e:
            logger.error(f"Error parsing LLM self-reflection for {self.bot_name}: {e}")
            return self._create_default_reflection(f"Parse error: {str(e)}")
    
    def _create_default_reflection(self, error_msg: str) -> LLMSelfReflection:
        """Create default reflection when parsing fails"""
        return LLMSelfReflection(
            effectiveness_score=0.5,
            authenticity_score=0.5,
            emotional_resonance=0.5,
            self_evaluation=f"Self-reflection generation failed: {error_msg}",
            learning_insight="Need to improve self-reflection system reliability.",
            improvement_suggestion="Fix reflection parsing and generation.",
            dominant_personality_trait="system_error",
            reflection_metadata={"error": error_msg}
        )
    
    async def _store_self_reflection(self, reflection: LLMSelfReflection, interaction_data: Dict):
        """Store LLM-generated self-reflection in memory"""
        try:
            content = f"""
LLM Self-Reflection Analysis:
Effectiveness: {reflection.effectiveness_score:.2f}
Authenticity: {reflection.authenticity_score:.2f}
Emotional Resonance: {reflection.emotional_resonance:.2f}

Self-Evaluation: {reflection.self_evaluation}
Learning Insight: {reflection.learning_insight}
Improvement Suggestion: {reflection.improvement_suggestion}
Dominant Trait: {reflection.dominant_personality_trait}
"""
            
            metadata = {
                "effectiveness_score": reflection.effectiveness_score,
                "authenticity_score": reflection.authenticity_score,
                "emotional_resonance": reflection.emotional_resonance,
                "learning_insight": reflection.learning_insight,
                "improvement_suggestion": reflection.improvement_suggestion,
                "dominant_personality_trait": reflection.dominant_personality_trait,
                "bot_name": self.bot_name,
                "memory_type": "bot_self_reflection_llm",
                "interaction_context": interaction_data.get("user_message", "")[:100],
                "created_at": datetime.now(UTC).isoformat(),
                **reflection.reflection_metadata
            }
            
            await self.memory_manager.store_conversation(
                user_id=self.namespace,
                user_message="[LLM_SELF_REFLECTION]",
                bot_response=content.strip(),
                metadata=metadata
            )
            
            logger.debug(f"Stored LLM self-reflection for {self.bot_name}")
            
        except Exception as e:
            logger.error(f"Failed to store LLM self-reflection for {self.bot_name}: {e}")
    
    async def get_recent_llm_insights(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Get recent LLM-generated self-reflection insights"""
        try:
            memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=self.namespace,
                query="self-reflection learning insight improvement",
                limit=limit * 2
            )
            
            insights = []
            for memory in memories:
                metadata = memory.get('metadata', {})
                if metadata.get('memory_type') == 'bot_self_reflection_llm':
                    insights.append({
                        'learning_insight': metadata.get('learning_insight', ''),
                        'improvement_suggestion': metadata.get('improvement_suggestion', ''),
                        'effectiveness_score': metadata.get('effectiveness_score', 0.0),
                        'dominant_personality_trait': metadata.get('dominant_personality_trait', ''),
                        'created_at': metadata.get('created_at', '')
                    })
                    
                    if len(insights) >= limit:
                        break
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get recent LLM insights for {self.bot_name}: {e}")
            return []


# Factory function for easy integration
def create_llm_powered_bot_memory(bot_name: str, llm_client: Any, memory_manager: MemoryManagerProtocol) -> LLMPoweredBotMemory:
    """Create an LLM-powered bot self-memory system instance"""
    return LLMPoweredBotMemory(bot_name, llm_client, memory_manager)