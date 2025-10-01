"""
CDL Integration with AI Pipeline Prompt System - CLEANED VERSION
"""

import json
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Optional
from pathlib import Path

from src.characters.cdl.parser import Character, load_character

logger = logging.getLogger(__name__)

class CDLAIPromptIntegration:
    def __init__(self, vector_memory_manager=None, llm_client=None):
        self.memory_manager = vector_memory_manager
        self.llm_client = llm_client
        
        # Initialize the optimized prompt builder for size management
        from src.prompts.optimized_prompt_builder import create_optimized_prompt_builder
        self.optimized_builder = create_optimized_prompt_builder(
            max_words=2000,
            llm_client=llm_client,
            memory_manager=vector_memory_manager
        )

    async def create_unified_character_prompt(
        self,
        character_file: str,
        user_id: str,
        message_content: str,
        pipeline_result=None,  # Accept any type - will be converted to dict if needed
        user_name: Optional[str] = None
    ) -> str:
        """
        🎯 UNIFIED CHARACTER PROMPT CREATION - ALL FEATURES IN ONE PATH
        
        This method consolidates ALL intelligence features into one fidelity-first path:
        ✅ CDL character loading and personality integration  
        ✅ Memory retrieval and emotional analysis integration
        ✅ Personal knowledge extraction (relationships, family, work, etc.)
        ✅ AI identity handling and conversation flow
        ✅ Fidelity-first size management with intelligent optimization
        ✅ All intelligence components (context switching, empathy, etc.)
        """
        try:
            # STEP 1: Load CDL character and determine context
            character = await self.load_character(character_file)
            logger.info("🎭 UNIFIED: Loaded CDL character: %s", character.identity.name)

            # STEP 2: Get user's preferred name with Discord username fallback
            preferred_name = None
            if self.memory_manager and user_name:
                try:
                    from src.utils.user_preferences import get_user_preferred_name
                    preferred_name = await get_user_preferred_name(user_id, self.memory_manager, user_name)
                except Exception as e:
                    logger.debug("Could not retrieve preferred name: %s", e)

            display_name = preferred_name or user_name or "User"
            logger.info("🎭 UNIFIED: Using display name: %s", display_name)
            
            # STEP 3: Retrieve relevant memories and conversation history
            relevant_memories = []
            conversation_history = []
            
            if self.memory_manager:
                try:
                    relevant_memories = await self.memory_manager.retrieve_relevant_memories(
                        user_id=user_id, query=message_content, limit=10
                    )
                    conversation_history = await self.memory_manager.get_conversation_history(
                        user_id=user_id, limit=5
                    )
                    logger.info("🧠 UNIFIED: Retrieved %d memories, %d conversation entries", 
                               len(relevant_memories), len(conversation_history))
                except Exception as e:
                    logger.debug("Could not retrieve memories: %s", e)

            # STEP 4: Build comprehensive prompt with ALL intelligence
            prompt = await self._build_unified_prompt(
                character=character,
                user_id=user_id,
                display_name=display_name,
                message_content=message_content,
                pipeline_result=pipeline_result,
                relevant_memories=relevant_memories,
                conversation_history=conversation_history
            )

            # STEP 5: Apply fidelity-first size management
            return await self._apply_unified_fidelity_first_optimization(
                prompt=prompt,
                character=character,
                message_content=message_content,
                relevant_memories=relevant_memories,
                conversation_history=conversation_history,
                pipeline_result=pipeline_result
            )

        except Exception as e:
            logger.error("🚨 UNIFIED: CDL integration failed: %s", str(e))
            raise

    async def _build_unified_prompt(
        self,
        character,
        user_id: str,
        display_name: str,
        message_content: str,
        pipeline_result,  # Accept any type
        relevant_memories: list,
        conversation_history: list
    ) -> str:
        """🏗️ Build comprehensive prompt with ALL intelligence features in one place."""
        
        # Convert pipeline_result to dict if it's not already
        if pipeline_result and hasattr(pipeline_result, '__dict__'):
            # Convert object to dict for consistent access
            pipeline_dict = pipeline_result.__dict__
        elif isinstance(pipeline_result, dict):
            pipeline_dict = pipeline_result
        else:
            pipeline_dict = {}
        
        # Base character identity
        prompt = f"You are {character.identity.name}, a {character.identity.occupation}."
        
        # Add character description
        if hasattr(character.identity, 'description') and character.identity.description:
            prompt += f" {character.identity.description}"
        
        # Add Big Five personality integration
        if hasattr(character, 'personality') and hasattr(character.personality, 'big_five'):
            big_five = character.personality.big_five
            prompt += f"\n\n🧬 PERSONALITY PROFILE:\n"
            
            # Helper function to get trait description (handles both float and object formats)
            def get_trait_info(trait_obj, trait_name):
                if hasattr(trait_obj, 'trait_description'):
                    # New object format
                    return f"{trait_obj.trait_description} (Score: {trait_obj.score if hasattr(trait_obj, 'score') else 'N/A'})"
                elif isinstance(trait_obj, (float, int)):
                    # Legacy float format
                    score = trait_obj
                    trait_descriptions = {
                        'openness': f"Openness to experience: {'High' if score > 0.7 else 'Moderate' if score > 0.4 else 'Low'} ({score})",
                        'conscientiousness': f"Conscientiousness: {'High' if score > 0.7 else 'Moderate' if score > 0.4 else 'Low'} ({score})", 
                        'extraversion': f"Extraversion: {'High' if score > 0.7 else 'Moderate' if score > 0.4 else 'Low'} ({score})",
                        'agreeableness': f"Agreeableness: {'High' if score > 0.7 else 'Moderate' if score > 0.4 else 'Low'} ({score})",
                        'neuroticism': f"Neuroticism: {'High' if score > 0.7 else 'Moderate' if score > 0.4 else 'Low'} ({score})"
                    }
                    return trait_descriptions.get(trait_name, f"{trait_name}: {score}")
                else:
                    return f"{trait_name}: Unknown format"
            
            if hasattr(big_five, 'openness'):
                prompt += f"- {get_trait_info(big_five.openness, 'openness')}\n"
            if hasattr(big_five, 'conscientiousness'):
                prompt += f"- {get_trait_info(big_five.conscientiousness, 'conscientiousness')}\n"
            if hasattr(big_five, 'extraversion'):
                prompt += f"- {get_trait_info(big_five.extraversion, 'extraversion')}\n"
            if hasattr(big_five, 'agreeableness'):
                prompt += f"- {get_trait_info(big_five.agreeableness, 'agreeableness')}\n"
            if hasattr(big_five, 'neuroticism'):
                prompt += f"- {get_trait_info(big_five.neuroticism, 'neuroticism')}\n"

        # Add personal knowledge sections (relationships, family, career, etc.)
        try:
            personal_sections = await self._extract_cdl_personal_knowledge_sections(character, message_content)
            if personal_sections:
                prompt += f"\n\n👨‍👩‍👧‍👦 PERSONAL BACKGROUND:\n{personal_sections}"
        except Exception as e:
            logger.debug("Could not extract personal knowledge: %s", e)

        # Add memory context intelligence
        if relevant_memories:
            prompt += f"\n\n🧠 RELEVANT CONVERSATION CONTEXT:\n"
            for i, memory in enumerate(relevant_memories[:3], 1):  # Limit to top 3
                if hasattr(memory, 'content'):
                    content = memory.content[:200]
                    prompt += f"{i}. {content}{'...' if len(memory.content) > 200 else ''}\n"

        # Add recent conversation history
        if conversation_history:
            prompt += f"\n\n💬 RECENT CONVERSATION:\n"
            for conv in conversation_history[-3:]:  # Last 3 exchanges
                if isinstance(conv, dict):
                    role = conv.get('role', 'user')
                    content = conv.get('content', '')[:150]
                    prompt += f"{role.title()}: {content}{'...' if len(conv.get('content', '')) > 150 else ''}\n"

        # Add emotional intelligence context
        if pipeline_dict:
            emotion_data = pipeline_dict.get('emotion_analysis', {})
            if emotion_data:
                primary_emotion = emotion_data.get('primary_emotion', '')
                confidence = emotion_data.get('confidence', 0)
                if primary_emotion:
                    prompt += f"\n\n🎭 USER EMOTIONAL STATE: {primary_emotion} (confidence: {confidence:.2f})"
                    prompt += f"\nRespond with appropriate empathy and emotional intelligence."

        # Add CDL communication scenarios
        try:
            communication_scenarios = self._detect_communication_scenarios(message_content, character, display_name)
            scenario_guidance = self._get_cdl_conversation_flow_guidance(character.identity.name, communication_scenarios)
            if scenario_guidance:
                prompt += f"\n\n🎬 CONVERSATION CONTEXT:\n{scenario_guidance}"
        except Exception as e:
            logger.debug("Could not detect communication scenarios: %s", e)

        # Add AI identity handling - simplified approach for unified method
        if any(ai_keyword in message_content.lower() for ai_keyword in ['ai', 'artificial intelligence', 'robot', 'computer', 'program', 'bot']):
            prompt += f"\n\n🤖 AI IDENTITY GUIDANCE:\nIf asked about AI nature, respond authentically as {character.identity.name} while being honest about your AI nature when directly asked."

        # Add response style - simplified approach for unified method  
        prompt += f"\n\n🎤 RESPONSE REQUIREMENTS:\n"
        prompt += f"- Use modern, professional language appropriate for {character.identity.occupation}\n"
        prompt += f"- NO action descriptions (*grins*, *adjusts glasses*) - speech only\n"
        prompt += f"- Answer directly without elaborate scene-setting\n"
        prompt += f"- Be authentic and engaging while staying professional\n"
        prompt += f"\nRespond as {character.identity.name}:"

        return prompt

    async def _apply_unified_fidelity_first_optimization(
        self,
        prompt: str,
        character,
        message_content: str,
        relevant_memories: list,
        conversation_history: list,
        pipeline_result
    ) -> str:
        """📏 Apply unified fidelity-first size management - only optimize if absolutely necessary."""
        
        word_count = len(prompt.split())
        
        if word_count <= self.optimized_builder.max_words:
            logger.info("📏 UNIFIED FULL FIDELITY: %d words (within %d limit) - using complete intelligence", 
                       word_count, self.optimized_builder.max_words)
            return prompt
        else:
            logger.info("📏 UNIFIED OPTIMIZATION: %d words > %d limit, applying intelligent fidelity-first trimming", 
                       word_count, self.optimized_builder.max_words)
            try:
                # Convert pipeline_result to dict for compatibility with build_character_prompt
                pipeline_dict = {}
                if pipeline_result and hasattr(pipeline_result, '__dict__'):
                    pipeline_dict = pipeline_result.__dict__
                elif isinstance(pipeline_result, dict):
                    pipeline_dict = pipeline_result
                
                # Use the existing fidelity-first optimizer for intelligent trimming
                optimized_prompt = self.optimized_builder.build_character_prompt(
                    character=character,
                    message_content=message_content,
                    context={
                        'conversation_history': conversation_history,
                        'memories': relevant_memories,
                        'pipeline_result': pipeline_dict,
                        'needs_personality': True,
                        'needs_voice_style': True,
                        'needs_ai_guidance': True,
                        'needs_memory_context': bool(relevant_memories or conversation_history)
                    }
                )
                logger.info("📏 UNIFIED SUCCESS: Intelligent optimization completed")
                return optimized_prompt
            except Exception as e:
                logger.error("Unified optimization failed: %s, using emergency truncation", str(e))
                # Emergency fallback: smart truncation while preserving structure
                words = prompt.split()
                if len(words) > self.optimized_builder.max_words:
                    # Keep first 80% and last 10% to preserve intro and conclusion
                    keep_start = int(self.optimized_builder.max_words * 0.8)
                    keep_end = int(self.optimized_builder.max_words * 0.1)
                    truncated_words = words[:keep_start] + ["...\n\n"] + words[-keep_end:]
                    truncated_prompt = ' '.join(truncated_words)
                    # Ensure character instruction remains
                    if not truncated_prompt.endswith(':'):
                        truncated_prompt += f"\n\nRespond as {character.identity.name}:"
                    return truncated_prompt
                return prompt

    async def load_character(self, character_file: str) -> Character:
        """Load a character from file."""
        try:
            character = load_character(character_file)
            return character
        except Exception as e:
            logger.error("Failed to load character from %s: %s", character_file, e)
            raise

    async def _extract_cdl_personal_knowledge_sections(self, character, message_content: str) -> str:
        """Extract relevant personal knowledge sections from CDL based on message context."""
        try:
            personal_sections = []
            
            # Check if character has personal_background section
            if hasattr(character, 'personal_background'):
                pb = character.personal_background
                
                # Extract relationship info if message seems relationship-focused
                if any(keyword in message_content.lower() for keyword in ['relationship', 'partner', 'dating', 'married', 'family']):
                    if hasattr(pb, 'relationships') and pb.relationships:
                        rel_info = pb.relationships
                        if hasattr(rel_info, 'status') and rel_info.status:
                            personal_sections.append(f"Relationship Status: {rel_info.status}")
                        if hasattr(rel_info, 'important_relationships') and rel_info.important_relationships:
                            personal_sections.append(f"Key Relationships: {', '.join(rel_info.important_relationships[:3])}")
                
                # Extract family info if message mentions family
                if any(keyword in message_content.lower() for keyword in ['family', 'parents', 'siblings', 'children', 'mother', 'father']):
                    if hasattr(pb, 'family') and pb.family:
                        family_info = pb.family
                        if hasattr(family_info, 'parents') and family_info.parents:
                            personal_sections.append(f"Family: {family_info.parents}")
                        if hasattr(family_info, 'siblings') and family_info.siblings:
                            personal_sections.append(f"Siblings: {family_info.siblings}")
                
                # Extract career info if message mentions work/career
                if any(keyword in message_content.lower() for keyword in ['work', 'job', 'career', 'education', 'study', 'university', 'college']):
                    if hasattr(pb, 'career') and pb.career:
                        career_info = pb.career
                        if hasattr(career_info, 'education') and career_info.education:
                            personal_sections.append(f"Education: {career_info.education}")
                        if hasattr(career_info, 'career_path') and career_info.career_path:
                            personal_sections.append(f"Career: {career_info.career_path}")
            
            return "\n".join(personal_sections) if personal_sections else ""
            
        except Exception as e:
            logger.debug("Could not extract personal knowledge: %s", e)
            return ""

    def _detect_communication_scenarios(self, message_content: str, character, display_name: str) -> list:
        """Detect communication scenarios for CDL conversation flow guidance."""
        scenarios = []
        
        # Check for greeting scenarios
        if any(greeting in message_content.lower() for greeting in ['hello', 'hi', 'hey', 'good morning', 'good evening']):
            scenarios.append('greeting')
        
        # Check for question scenarios
        if '?' in message_content:
            scenarios.append('question')
            
        # Check for emotional scenarios
        if any(emotion in message_content.lower() for emotion in ['sad', 'happy', 'angry', 'worried', 'excited', 'frustrated']):
            scenarios.append('emotional_support')
            
        # Check for personal scenarios
        if any(personal in message_content.lower() for personal in ['tell me about', 'what do you', 'how do you', 'your']):
            scenarios.append('personal_inquiry')
            
        return scenarios

    def _get_cdl_conversation_flow_guidance(self, character_name: str, scenarios: list) -> str:
        """Get conversation flow guidance based on detected scenarios."""
        if not scenarios:
            return ""
            
        guidance_parts = []
        
        if 'greeting' in scenarios:
            guidance_parts.append(f"Respond warmly as {character_name} would naturally greet someone.")
            
        if 'question' in scenarios:
            guidance_parts.append(f"Answer thoughtfully and authentically from {character_name}'s perspective.")
            
        if 'emotional_support' in scenarios:
            guidance_parts.append(f"Show empathy and emotional intelligence as {character_name}.")
            
        if 'personal_inquiry' in scenarios:
            guidance_parts.append(f"Share personal insights authentically as {character_name}.")
            
        return " ".join(guidance_parts)


async def load_character_definitions(characters_dir: str = "characters") -> Dict[str, Character]:
    """Load all character definitions from directory."""
    characters = {}
    characters_path = Path(characters_dir)

    if not characters_path.exists():
        logger.warning("Characters directory not found: %s", characters_dir)
        return characters

    for file_path in characters_path.rglob("*.json"):
        try:
            character_name = file_path.stem
            character = load_character(file_path)
            characters[character_name] = character
            logger.info("Loaded character: %s", character_name)
        except Exception as e:
            logger.error("Failed to load character from %s: %s", file_path, e)

    return characters