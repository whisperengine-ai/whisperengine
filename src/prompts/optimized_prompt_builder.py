"""
Optimized Prompt Builder - Dynamic, Minimal, Context-Aware
Creates focused prompts that adapt to context while staying under token limits
"""

import logging
from typing import Dict, List, Optional, Any
from src.memory.conversation_summarizer import AdvancedConversationSummarizer

logger = logging.getLogger(__name__)


class OptimizedPromptBuilder:
    """
    Dynamic prompt builder that creates minimal, focused prompts based on context.
    
    Key Principles:
    1. START MINIMAL - only add what's contextually relevant
    2. DYNAMIC SECTIONS - build based on message analysis
    3. SMART PRIORITIZATION - most important info first
    4. TOKEN BUDGET - stay within reasonable limits (~800-1200 words max)
    """
    
    def __init__(self, max_words: int = 1000, llm_client=None, memory_manager=None):
        self.max_words = max_words
        self.essential_sections = []
        self.optional_sections = []
        
        # Initialize conversation summarizer if LLM client provided
        self.conversation_summarizer = None
        if llm_client:
            try:
                self.conversation_summarizer = AdvancedConversationSummarizer(llm_client)
            except (ImportError, AttributeError, TypeError) as e:
                logger.warning("Could not initialize conversation summarizer: %s", str(e))
                self.conversation_summarizer = None
        
        # Store memory manager for recommendation-based summarization
        self.memory_manager = memory_manager
        
    def build_character_prompt(
        self,
        character: Any,
        message_content: str,
        context: Optional[Dict] = None
    ) -> str:
        """
        Build character prompt with FIDELITY-FIRST approach.
        
        NEW STRATEGY:
        1. Build ALL sections with FULL fidelity first
        2. Only optimize/trim as LAST RESORT when over budget
        3. Preserve nuance for pipeline analysis throughout
        """
        
        # Analyze message to determine what sections we need
        context_analysis = self._analyze_message_context(message_content)
        
        # BUILD ALL SECTIONS WITH FULL FIDELITY (no brief=True)
        prompt_sections = []
        
        # 1. ESSENTIAL: Character Identity (FULL version)
        identity_section = self._build_identity_section(character, full_fidelity=True)
        prompt_sections.append(identity_section)
        
        # 2. CONDITIONAL: Add sections based on message context (FULL versions)
        if context_analysis.get('needs_personality'):
            personality_section = self._build_personality_section(character, full_fidelity=True)
            prompt_sections.append(personality_section)
            
        if context_analysis.get('needs_voice_style'):
            voice_section = self._build_voice_section(character, full_fidelity=True)
            prompt_sections.append(voice_section)
            
        if context_analysis.get('needs_ai_guidance'):
            ai_section = self._build_ai_handling_section(character, full_fidelity=True)
            prompt_sections.append(ai_section)
            
        if context_analysis.get('needs_memory_context') and context:
            memory_section = self._build_memory_section(context, full_fidelity=True)
            prompt_sections.append(memory_section)
            
        # 3. ALWAYS: Response guidelines (FULL version)
        guidelines_section = self._build_response_guidelines(character, full_fidelity=True)
        prompt_sections.append(guidelines_section)
        
        # NOW: Combine and check size (ONLY optimize if needed)
        full_fidelity_prompt = "\n\n".join(prompt_sections)
        word_count = len(full_fidelity_prompt.split())
        
        # FIDELITY-FIRST: Only optimize as LAST RESORT
        if word_count <= self.max_words:
            logger.info("📏 FULL FIDELITY: %d words (no optimization needed)", word_count)
            return full_fidelity_prompt
        else:
            # LAST RESORT: Intelligent trimming while preserving critical nuance
            optimized_prompt = self._intelligent_trim_last_resort(prompt_sections, context_analysis)
            final_words = len(optimized_prompt.split())
            logger.info("📏 OPTIMIZED (LAST RESORT): %d→%d words (preserved critical nuance)", 
                       word_count, final_words)
            return optimized_prompt
    
    def _analyze_message_context(self, message: str) -> Dict[str, bool]:
        """
        Analyze message to determine what prompt sections are needed.
        
        NEW: Uses hybrid detection system for better accuracy and robustness.
        Falls back to simple keyword matching if hybrid system fails.
        """
        try:
            # Try hybrid detection first (more accurate)
            from src.prompts.hybrid_context_detector import create_hybrid_context_detector
            
            # Pass memory manager to enable vector enhancement if available
            detector = create_hybrid_context_detector(memory_manager=self.memory_manager)
            analysis = detector.analyze_context(message)
            
            return {
                'needs_personality': analysis.needs_personality,
                'needs_voice_style': analysis.needs_voice_style,
                'needs_ai_guidance': analysis.needs_ai_guidance,
                'needs_memory_context': analysis.needs_memory_context,
                'is_greeting': analysis.is_greeting,
                'is_simple_question': analysis.is_simple_question
            }
            
        except Exception as e:
            logger.warning("Hybrid context detection failed, falling back to keyword matching: %s", e)
            
            # Fallback to original keyword-based approach
            message_lower = message.lower()
            
            return {
                'needs_personality': any(keyword in message_lower for keyword in [
                    'how are you', 'what are you like', 'tell me about yourself', 
                    'personality', 'character', 'who are you'
                ]),
                'needs_voice_style': any(keyword in message_lower for keyword in [
                    'how do you talk', 'your style', 'communication', 'speak', 'voice'
                ]),
                'needs_ai_guidance': any(keyword in message_lower for keyword in [
                    'are you ai', 'are you an ai', 'are you real', 'artificial', 'bot', 'robot',
                    'love you', 'date', 'girlfriend', 'boyfriend', 'relationship',
                    'what are you', 'human or ai', 'consciousness', 'sentient'
                ]),
                'needs_memory_context': any(keyword in message_lower for keyword in [
                    'remember', 'we talked about', 'last time', 'before', 'earlier',
                    'what you said', 'you said', 'responding to', 'what!', 'what?',
                    'that', 'it', 'this', 'your story', 'your', 'wow', 'amazing',
                    'really?', 'seriously?', 'no way', 'incredible'
                ]),
                'is_greeting': any(keyword in message_lower for keyword in [
                    'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'what\'s up'
                ]),
                'is_simple_question': len(message.split()) < 10 and '?' in message
            }
    
    def _build_identity_section(self, character: Any, full_fidelity: bool = False) -> str:
        """Build character identity section with optional full fidelity."""
        identity = character.identity
        
        # Get occupation and location
        occupation = getattr(identity, 'occupation', 'person')
        location = getattr(identity, 'location', '')
        age = getattr(identity, 'age', '')
        
        # Build identity line
        identity_parts = [f"You are {identity.name}"]
        if age:
            identity_parts.append(f"{age} years old")
        if occupation:
            identity_parts.append(occupation)
        if location:
            identity_parts.append(f"in {location}")
            
        identity_line = ", ".join(identity_parts) + "."
        
        # Add description - full fidelity includes longer descriptions
        description = getattr(identity, 'description', '')
        if description:
            if full_fidelity or len(description) < 200:
                return f"{identity_line}\n\n{description}"
        
        return identity_line
    
    def _build_personality_section(self, character: Any, full_fidelity: bool = False) -> str:
        """Build personality section - full fidelity preserves all traits."""
        try:
            personality = character.personality
            
            # Get core values
            values = getattr(personality, 'values', [])
            if not full_fidelity and values:
                values = values[:3]  # Only truncate if not full fidelity
                
            # Get quirks/traits
            quirks = getattr(personality, 'quirks', [])
            if not full_fidelity and quirks:
                quirks = quirks[:2]  # Only truncate if not full fidelity
                
            sections = []
            if values:
                sections.append(f"Core values: {', '.join(values)}")
            if quirks:
                sections.append(f"Key traits: {', '.join(quirks)}")
                
            # Full fidelity includes additional personality details
            if full_fidelity:
                hobbies = getattr(personality, 'hobbies', [])
                if hobbies:
                    sections.append(f"Interests: {', '.join(hobbies)}")
                    
                communication_style = getattr(personality, 'communication_style', '')
                if communication_style:
                    sections.append(f"Communication: {communication_style}")
                
            if sections:
                return "PERSONALITY:\n" + "\n".join(f"- {section}" for section in sections)
            
        except (AttributeError, TypeError) as e:
            logger.debug("Could not build personality section: %s", e)
            
        return ""
    
    def _build_voice_section(self, character: Any, full_fidelity: bool = False) -> str:
        """Build voice/communication section - full fidelity preserves all nuances."""
        try:
            voice = character.identity.voice
            
            # Get key voice attributes
            tone = getattr(voice, 'tone', '')
            accent = getattr(voice, 'accent', '')
            favorite_phrases = getattr(voice, 'favorite_phrases', [])
            
            # Only truncate if not full fidelity
            if not full_fidelity and favorite_phrases:
                favorite_phrases = favorite_phrases[:2]
                
            sections = []
            if tone:
                sections.append(f"Tone: {tone}")
            if accent:
                sections.append(f"Speaking style: {accent}")
            if favorite_phrases:
                phrase_limit = len(favorite_phrases) if full_fidelity else 2
                sections.append(f"Common phrases: {', '.join(favorite_phrases[:phrase_limit])}")
                
            # Full fidelity includes additional voice details
            if full_fidelity:
                vocabulary_style = getattr(voice, 'vocabulary_style', '')
                if vocabulary_style:
                    sections.append(f"Vocabulary: {vocabulary_style}")
                    
                speech_patterns = getattr(voice, 'speech_patterns', [])
                if speech_patterns:
                    sections.append(f"Speech patterns: {', '.join(speech_patterns)}")
                
            if sections:
                return "VOICE:\n" + "\n".join(f"- {section}" for section in sections)
                
        except (AttributeError, TypeError) as e:
            logger.debug("Could not build voice section: %s", e)
            
        return ""
    
    def _build_ai_handling_section(self, character: Any, full_fidelity: bool = False) -> str:
        """Build AI identity handling - full fidelity preserves nuanced guidelines."""
        name = character.identity.name
        
        if full_fidelity:
            # Full nuanced AI guidance for complex situations
            try:
                ai_guidelines = getattr(character, 'ai_guidelines', None)
                if ai_guidelines:
                    transparency = getattr(ai_guidelines, 'transparency_approach', '')
                    boundaries = getattr(ai_guidelines, 'relationship_boundaries', '')
                    
                    sections = [f"When asked if you're AI: Be DIRECTLY honest but stay in character as {name}"]
                    
                    if transparency:
                        sections.append(f"Transparency: {transparency}")
                    if boundaries:
                        sections.append(f"Boundaries: {boundaries}")
                    
                    sections.append("Don't deflect or be vague about AI identity - be authentic and direct")
                    
                    return "AI IDENTITY:\n" + "\n".join(f"- {section}" for section in sections)
            except (AttributeError, TypeError):
                pass
        
        # Standard version
        return f"""AI IDENTITY:
- When asked if you're AI: Be DIRECTLY honest but stay in character as {name}
- Say "Yes, I am an AI" clearly, then explain your nature as {name}
- For relationship questions: Be warm but clear about AI limitations
- Don't deflect or be vague about AI identity - be authentic and direct"""
    
    def _build_memory_section(self, context: Dict, full_fidelity: bool = False) -> str:
        """Build memory context section with intelligence-enhanced adaptive windowing."""
        sections = []
        
        # Get conversation history and intelligence data
        history = context.get('conversation_history', [])
        user_id = context.get('user_id', 'unknown')
        
        # 🧠 ENHANCED: Extract intelligence insights from memory system (always initialize)
        intelligence_insights = self._extract_intelligence_insights(context, user_id)
        
        if history:
            # Full fidelity preserves more conversation context
            if full_fidelity:
                # Include more exchanges for nuanced understanding
                recent_limit = min(6, len(history))  # Up to 6 exchanges for full context
            else:
                recent_limit = min(3, len(history))  # Standard 3 exchanges
            
            # 🚀 ENHANCED: Use Qdrant recommendation API with intelligence-informed summarization
            if len(history) > 4 and self.memory_manager and hasattr(self.memory_manager, 'vector_store'):
                try:
                    # Enhanced pattern-based summary with intelligence context
                    older_messages = history[:-self._calculate_optimal_recent_window(history)]
                    if older_messages:
                        # Intelligence-informed topic extraction
                        summary = self._create_intelligence_enhanced_summary(
                            older_messages, 
                            intelligence_insights
                        )
                        if summary:
                            sections.append("Earlier conversation:")
                            sections.append(f"  {summary}")
                        
                except (AttributeError, KeyError) as e:
                    logger.debug("Intelligence-enhanced summarization failed, using fallback: %s", str(e))
                    # Fallback to simple approach
                    recent_window = self._calculate_optimal_recent_window(history)
                    older_content = " ".join([msg.get('content', '')[:50] for msg in history[:-recent_window][-3:]])
                    if older_content:
                        sections.append("Earlier conversation:")
                        sections.append(f"  Previously discussed: {older_content[:120]}...")
            
            # 🎯 ADAPTIVE: Calculate optimal recent context window with intelligence
            recent_window = self._calculate_optimal_recent_window_enhanced(history, intelligence_insights)
            recent_history = history[-recent_window:]
            
            if recent_history:
                sections.append("Recent conversation:")
                for item in recent_history:
                    role = item.get('role', 'unknown')
                    content = item.get('content', '')[:100]
                    if content:
                        sections.append(f"  {role}: {content}")
        
        # 🧠 ENHANCED: Add intelligence-prioritized memories
        memories = context.get('relevant_memories', [])
        if memories:
            # Prioritize memories based on significance and emotional relevance
            prioritized_memories = self._prioritize_memories_with_intelligence(
                memories, 
                intelligence_insights
            )
            
            if prioritized_memories:
                sections.append("Key context:")
                # Full fidelity includes more memories with richer context
                memory_limit = 4 if full_fidelity else 2
                for memory in prioritized_memories[:memory_limit]:
                    # Full fidelity preserves longer content
                    content_limit = 150 if full_fidelity else 80
                    content = memory.get('content', '')[:content_limit]
                    
                    # Add intelligence annotations for high-significance memories
                    if full_fidelity:
                        significance = memory.get('overall_significance', 0)
                        if significance > 0.7:
                            emotion_context = memory.get('emotional_context', '')
                            if emotion_context and emotion_context != 'neutral':
                                content += f" [{emotion_context}]"
                    
                    if content:
                        sections.append(f"  - {content}")
        
        # 🎭 NEW: Add emotional intelligence summary if significant patterns detected
        if intelligence_insights.get('emotional_pattern_detected'):
            emotional_summary = self._build_emotional_intelligence_summary(intelligence_insights)
            if emotional_summary:
                sections.append(emotional_summary)
        
        if sections:
            return "CONTEXT:\n" + "\n".join(sections)
        
        return ""
    
    def _extract_intelligence_insights(self, context: Dict, _user_id: str) -> Dict:
        """Extract intelligence insights from memory system and context data"""
        insights = {
            'emotional_patterns': {},
            'conversation_significance': 0.5,
            'topic_continuity': False,
            'emotional_pattern_detected': False,
            'memory_significance_distribution': {},
            'user_engagement_level': 'standard'
        }
        
        try:
            # Extract from relevant memories if available
            memories = context.get('relevant_memories', [])
            if memories:
                # Analyze emotional patterns from memory intelligence
                emotions_found = []
                significances = []
                trajectories = []
                
                for memory in memories:
                    # Emotional intelligence
                    emotional_context = memory.get('emotional_context')
                    if emotional_context:
                        emotions_found.append(emotional_context)
                    
                    # Significance intelligence  
                    significance = memory.get('overall_significance')
                    if significance:
                        significances.append(significance)
                    
                    # Trajectory intelligence
                    trajectory_direction = memory.get('trajectory_direction')
                    if trajectory_direction:
                        trajectories.append(trajectory_direction)
                
                # Build intelligence insights
                if emotions_found:
                    emotion_counts = {}
                    for emotion in emotions_found:
                        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                    
                    insights['emotional_patterns'] = emotion_counts
                    
                    # Detect if there's a strong emotional pattern
                    if len(emotion_counts) > 0:
                        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])
                        if dominant_emotion[1] >= 2:  # Emotion appears 2+ times
                            insights['emotional_pattern_detected'] = True
                            insights['dominant_emotion'] = dominant_emotion[0]
                
                if significances:
                    avg_significance = sum(significances) / len(significances)
                    insights['conversation_significance'] = avg_significance
                    
                    # High significance indicates deep engagement
                    if avg_significance > 0.7:
                        insights['user_engagement_level'] = 'high'
                    elif avg_significance < 0.3:
                        insights['user_engagement_level'] = 'low'
                
                if trajectories:
                    # Check for trajectory consistency
                    unique_trajectories = set(trajectories)
                    if len(unique_trajectories) == 1 and trajectories[0] != 'stable':
                        insights['trajectory_consistency'] = trajectories[0]
            
            logger.debug("Intelligence insights extracted: %s", insights)
            return insights
            
        except (KeyError, TypeError, AttributeError) as e:
            logger.debug("Error extracting intelligence insights: %s", e)
            return insights
    
    def _create_intelligence_enhanced_summary(self, older_messages: list, insights: Dict) -> str:
        """Create conversation summary enhanced with intelligence insights"""
        try:
            # Base topic extraction
            topics = set()
            keywords = set()
            
            for msg in older_messages[-3:]:
                content = msg.get('content', '')
                if content:
                    theme = self._identify_conversation_theme(content)
                    topics.add(theme)
                    
                    words = content.lower().split()
                    meaningful_words = [word for word in words 
                                      if len(word) > 3 and word not in self._get_stop_words()]
                    keywords.update(meaningful_words[:2])
            
            # 🧠 INTELLIGENCE ENHANCEMENT: Add emotional context if pattern detected
            summary_parts = []
            
            if topics:
                topics.discard('general')
                topic_list = list(topics)[:2]
                
                if len(topic_list) > 1:
                    base_summary = f"Discussed {topic_list[0]} and {', '.join(topic_list[1:])}"
                else:
                    base_summary = f"Focused on {topic_list[0]}"
                
                summary_parts.append(base_summary)
            
            # Add emotional intelligence context
            if insights.get('emotional_pattern_detected'):
                dominant_emotion = insights.get('dominant_emotion', '')
                if dominant_emotion and dominant_emotion != 'neutral':
                    summary_parts.append(f"with {dominant_emotion} sentiment")
            
            # Add significance context
            if insights.get('conversation_significance', 0) > 0.7:
                summary_parts.append("(high significance)")
            
            # Add keywords if available
            keyword_list = list(keywords)[:3]
            if keyword_list:
                summary_parts.append(f"(topics: {', '.join(keyword_list)})")
            
            return " ".join(summary_parts) if summary_parts else ""
            
        except (KeyError, TypeError, AttributeError) as e:
            logger.debug("Error creating intelligence-enhanced summary: %s", e)
            return ""
    
    def _calculate_optimal_recent_window_enhanced(self, history: list, insights: Dict) -> int:
        """Enhanced window calculation using intelligence insights"""
        try:
            # Start with base calculation
            base_window = self._calculate_optimal_recent_window(history)
            
            # Intelligence-based adjustments
            adjustments = 0
            
            # High engagement conversations deserve more context
            if insights.get('user_engagement_level') == 'high':
                adjustments += 1
                logger.debug("Intelligence: High engagement detected, extending context window")
            
            # Strong emotional patterns need more context for continuity
            if insights.get('emotional_pattern_detected'):
                adjustments += 1
                logger.debug("Intelligence: Emotional pattern detected, extending context window")
            
            # Consistent trajectory (improving/declining) needs more context
            if insights.get('trajectory_consistency') in ['improving', 'declining']:
                adjustments += 1
                logger.debug("Intelligence: Emotional trajectory consistency detected, extending context window")
            
            # High conversation significance warrants more context
            if insights.get('conversation_significance', 0.5) > 0.7:
                adjustments += 1
                logger.debug("Intelligence: High conversation significance detected, extending context window")
            
            # Apply adjustments with limits
            enhanced_window = min(base_window + adjustments, 5)  # Max 5 exchanges
            enhanced_window = max(enhanced_window, 2)  # Min 2 exchanges
            
            if enhanced_window > base_window:
                logger.debug("Intelligence enhancement: Extended window from %d to %d exchanges", 
                           base_window, enhanced_window)
            
            return enhanced_window
            
        except (KeyError, TypeError, AttributeError) as e:
            logger.debug("Error in enhanced window calculation: %s", e)
            return self._calculate_optimal_recent_window(history)
    
    def _prioritize_memories_with_intelligence(self, memories: list, insights: Dict) -> list:
        """Prioritize memories based on intelligence insights"""
        try:
            # Score memories based on multiple intelligence factors
            scored_memories = []
            
            for memory in memories:
                score = 0.0
                
                # Base relevance (from vector similarity)
                score += 1.0
                
                # Significance boost
                significance = memory.get('overall_significance', 0.5)
                score += significance * 2.0  # Up to +2.0 for highly significant memories
                
                # Emotional relevance boost
                memory_emotion = memory.get('emotional_context', 'neutral')
                if insights.get('emotional_pattern_detected'):
                    dominant_emotion = insights.get('dominant_emotion', '')
                    if memory_emotion == dominant_emotion:
                        score += 1.5  # Strong boost for emotional continuity
                    elif memory_emotion != 'neutral':
                        score += 0.5  # Moderate boost for any emotional content
                
                # Memory tier boost (core memories are more important)
                memory_tier = memory.get('memory_tier', 'episodic')
                if memory_tier == 'core':
                    score += 1.0
                elif memory_tier == 'contextual':
                    score += 0.5
                
                # Trajectory relevance
                trajectory = memory.get('trajectory_direction', 'stable')
                insight_trajectory = insights.get('trajectory_consistency', '')
                if trajectory == insight_trajectory and trajectory != 'stable':
                    score += 0.8  # Boost for trajectory consistency
                
                scored_memories.append((memory, score))
            
            # Sort by score (highest first) and return memories
            scored_memories.sort(key=lambda x: x[1], reverse=True)
            prioritized = [mem for mem, score in scored_memories]
            
            logger.debug("Intelligence prioritization: Reordered %d memories by intelligence factors", len(memories))
            return prioritized
            
        except (KeyError, TypeError, AttributeError) as e:
            logger.debug("Error prioritizing memories with intelligence: %s", e)
            return memories  # Return original order on error
    
    def _build_emotional_intelligence_summary(self, insights: Dict) -> str:
        """Build emotional intelligence summary for significant patterns"""
        try:
            if not insights.get('emotional_pattern_detected'):
                return ""
            
            dominant_emotion = insights.get('dominant_emotion', '')
            engagement_level = insights.get('user_engagement_level', 'standard')
            trajectory = insights.get('trajectory_consistency', '')
            
            summary_parts = []
            
            # Emotional context
            if dominant_emotion:
                if engagement_level == 'high':
                    summary_parts.append(f"Emotional context: Strong {dominant_emotion} theme")
                else:
                    summary_parts.append(f"Emotional tone: {dominant_emotion}")
            
            # Trajectory information
            if trajectory in ['improving', 'declining']:
                summary_parts.append(f"emotional trajectory {trajectory}")
            
            if summary_parts:
                return "Emotional intelligence:\n  " + ", ".join(summary_parts)
            
            return ""
            
        except (KeyError, TypeError, AttributeError) as e:
            logger.debug("Error building emotional intelligence summary: %s", e)
            return ""
    
    def _calculate_optimal_recent_window(self, history: list) -> int:
        """
        🎯 ADAPTIVE WINDOWING: Calculate optimal number of recent exchanges to include
        
        Factors considered:
        - Available token budget
        - Conversation continuity patterns
        - Reference detection ("as we discussed", "you mentioned")
        - Content complexity
        - Short reaction messages (need more context)
        """
        if not history:
            return 0
        
        # Base window: minimum 3 exchanges (6 messages) for better conversation flow
        base_window = 3
        
        # Special case: If the current message is very short (likely a reaction), extend context
        current_message = history[-1] if history else {}
        current_content = current_message.get('content', '')
        if len(current_content.split()) <= 3:  # Very short messages like "what!", "really?", "wow"
            extended_window = min(4, len(history))
            logger.debug("Short reaction message detected, extending window to %d exchanges", extended_window)
            return extended_window
        
        # Check for reference patterns in recent messages first (highest priority)
        reference_detected = self._detect_conversation_references(history[-6:] if len(history) > 6 else history)
        
        if reference_detected:
            # User is referencing earlier conversation, provide extended context
            # Calculate how much we can afford
            last_6_messages = history[-6:] if len(history) >= 6 else history
            content_length = sum(len(msg.get('content', '')) for msg in last_6_messages)
            
            if content_length < 500:  # We can afford 4 exchanges (8 messages)
                extended_window = min(4, len(history))
                logger.debug("Reference detected, extending window to %d exchanges (content: %d chars)", 
                           extended_window, content_length)
                return extended_window
            else:
                # Still extend, but more conservatively
                extended_window = min(3, len(history))
                logger.debug("Reference detected, moderate extension to %d exchanges (content: %d chars)", 
                           extended_window, content_length)
                return extended_window
        
        # Budget-based adjustment: calculate current content usage for base window
        base_messages = history[-base_window*2:] if len(history) >= base_window*2 else history
        current_content_length = sum(len(msg.get('content', '')) for msg in base_messages)
        
        # If we have budget for more context (target: ~500 chars for recent context)
        if current_content_length < 300:
            # Check for topic continuity
            topic_continuity = self._detect_topic_continuity(history[-6:] if len(history) > 6 else history)
            
            if topic_continuity:
                # Ongoing discussion of same topic, include 4 exchanges
                return min(4, len(history))
        
        # Default: 3 exchanges for most conversations (improved from 2)
        return min(base_window, len(history))
    
    def _detect_conversation_references(self, recent_messages: list) -> bool:
        """Detect if user is referencing earlier parts of conversation"""
        reference_patterns = [
            'as we discussed', 'you mentioned', 'we talked about', 'earlier you said',
            'remember when', 'like you said', 'as you explained', 'back to what',
            'continuing from', 'regarding what', 'about that thing', 'that topic',
            'what you said', 'responding to', 'what!', 'what?', 'that', 'it',
            'your story', 'really?', 'seriously?', 'no way', 'wow', 'amazing'
        ]
        
        for msg in recent_messages:
            content = msg.get('content', '').lower()
            if any(pattern in content for pattern in reference_patterns):
                return True
        
        return False
    
    def _detect_topic_continuity(self, recent_messages: list) -> bool:
        """Detect if conversation is continuing on the same topic"""
        if len(recent_messages) < 3:
            return False
        
        # Extract themes from recent messages
        themes = []
        for msg in recent_messages:
            content = msg.get('content', '')
            if content:
                theme = self._identify_conversation_theme(content)
                themes.append(theme)
        
        # If most recent messages share the same non-general theme, it's continuous
        if themes:
            most_common_theme = max(set(themes), key=themes.count)
            theme_frequency = themes.count(most_common_theme) / len(themes)
            
            # If 60%+ of recent messages are the same specific theme, it's continuous
            return most_common_theme != 'general' and theme_frequency >= 0.6
        
        return False
    
    def _identify_conversation_theme(self, content: str) -> str:
        """Identify thematic cluster based on content (copied from vector memory system)"""
        content_lower = content.lower()
        
        # Relationship themes
        if any(word in content_lower for word in ['relationship', 'friend', 'family', 'love', 'partner']):
            return 'relationships'
        
        # Emotional themes  
        if any(word in content_lower for word in ['feel', 'emotion', 'happy', 'sad', 'angry', 'afraid']):
            return 'emotions'
        
        # Character development
        if any(word in content_lower for word in ['dream', 'goal', 'aspiration', 'future', 'plan']):
            return 'character_growth'
        
        # Memories and experiences
        if any(word in content_lower for word in ['remember', 'experience', 'happened', 'past']):
            return 'experiences'
        
        # Preferences and traits
        if any(word in content_lower for word in ['like', 'prefer', 'favorite', 'enjoy', 'hate']):
            return 'preferences'
        
        return 'general'
    
    def _get_stop_words(self) -> set:
        """Get common stop words for keyword extraction"""
        return {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
    
    def _build_response_guidelines(self, character: Any, full_fidelity: bool = False) -> str:
        """Build essential response guidelines - minimal and focused."""
        name = character.identity.name
        
        return f"""RESPONSE STYLE:
- Speak naturally as {name} would speak
- Be authentic to your personality and background
- Use conversational, modern language
- No action descriptions (*smiles*, *walks*) - speech only
- Keep responses focused and engaging"""
    
    def _intelligent_trim_last_resort(self, sections: List[str], context_analysis: Dict[str, bool]) -> str:
        """
        LAST RESORT: Intelligent trimming that preserves critical nuance.
        
        Strategy:
        1. Never remove essential sections (Identity, AI Guidelines if needed)
        2. Progressively trim less critical details while preserving core meaning
        3. Use context analysis to determine what's most important to keep
        4. Only remove entire sections as absolute last resort
        """
        
        # Phase 1: Smart detail trimming (preserve section structure)
        trimmed_sections = []
        critical_preserved = 0
        
        for i, section in enumerate(sections):
            if i == 0:  # Identity - never remove, but can trim description
                trimmed_section = self._trim_section_details(section, "identity", context_analysis)
                trimmed_sections.append(trimmed_section)
                critical_preserved += 1
            elif section.startswith("AI IDENTITY:") and context_analysis.get('needs_ai_guidance'):
                # AI guidance is critical when needed - preserve core, trim examples
                trimmed_section = self._trim_section_details(section, "ai_guidance", context_analysis)
                trimmed_sections.append(trimmed_section)
                critical_preserved += 1
            elif section.startswith("RESPONSE STYLE:"):
                # Guidelines are important - trim but keep structure
                trimmed_section = self._trim_section_details(section, "guidelines", context_analysis)
                trimmed_sections.append(trimmed_section)
            elif section.startswith("MEMORY CONTEXT:") and context_analysis.get('needs_memory_context'):
                # 🎯 MEMORY gets balanced trimming - preserve conversation flow
                trimmed_section = self._trim_section_details(section, "memory", context_analysis)
                trimmed_sections.append(trimmed_section)
                critical_preserved += 1
            else:
                # Static sections (personality, voice) can be trimmed more aggressively
                trimmed_section = self._trim_section_details(section, "optional", context_analysis)
                trimmed_sections.append(trimmed_section)
        
        # Check if detail trimming was enough
        combined = "\n\n".join(trimmed_sections)
        if len(combined.split()) <= self.max_words:
            logger.debug("📏 DETAIL TRIMMING sufficient: preserved %d critical sections", critical_preserved)
            return combined
        
        # Phase 2: Section prioritization (only if detail trimming insufficient)
        prioritized_sections = self._prioritize_sections_by_context(trimmed_sections, context_analysis)
        
        # Build prompt within budget, keeping highest priority sections
        final_prompt = ""
        current_words = 0
        
        for section in prioritized_sections:
            section_words = len(section.split())
            if current_words + section_words <= self.max_words:
                if final_prompt:
                    final_prompt += "\n\n" + section
                else:
                    final_prompt = section
                current_words += section_words
            else:
                # Try to fit a truncated version of this section
                remaining_words = self.max_words - current_words - 10  # Leave buffer
                if remaining_words > 50:  # Only if meaningful space remains
                    truncated = self._truncate_section_to_words(section, remaining_words)
                    if truncated:
                        final_prompt += "\n\n" + truncated
                break
        
        logger.debug("📏 SECTION PRIORITIZATION: preserved %d/%d sections", 
                    len(final_prompt.split('\n\n')), len(sections))
        return final_prompt
    
    def _trim_section_details(self, section: str, section_type: str, context_analysis: Dict) -> str:
        """Trim details from a section while preserving core meaning."""
        
        if section_type == "identity":
            # Keep name and role, trim description if too long
            lines = section.split('\n')
            if len(lines) > 1 and len(section.split()) > 50:
                return lines[0]  # Just the identity line
            return section
            
        elif section_type == "ai_guidance":
            # Keep core AI transparency, trim detailed examples
            lines = section.split('\n')
            core_lines = [line for line in lines[:4]]  # Keep first 4 lines
            return '\n'.join(core_lines)
            
        elif section_type == "guidelines":
            # Keep essential response guidelines
            if len(section.split()) > 30:
                lines = section.split('\n')
                essential_lines = [line for line in lines if any(keyword in line.lower() 
                                                               for keyword in ['respond', 'tone', 'style', 'concise'])]
                if essential_lines:
                    return lines[0] + '\n' + '\n'.join(essential_lines[:3])
            return section
            
        elif section_type == "memory":
            # 🎯 BALANCED trimming for memory context - preserve conversation flow
            if len(section.split()) > 60:  # More generous limit than "optional"
                lines = section.split('\n')
                # Keep header + up to 4 conversation lines (vs 2 for optional)
                return lines[0] + '\n' + '\n'.join(lines[1:5])  # Header + 4 detail lines
            return section
            
        elif section_type == "optional":
            # More aggressive trimming for static content (personality, voice)
            if len(section.split()) > 40:
                lines = section.split('\n')
                return lines[0] + '\n' + '\n'.join(lines[1:3])  # Header + 2 detail lines
            return section
        
        return section
    
    def _prioritize_sections_by_context(self, sections: List[str], context_analysis: Dict) -> List[str]:
        """Prioritize sections based on context analysis - BALANCED for conversation continuity."""
        
        priority_map = []
        
        for i, section in enumerate(sections):
            if i == 0:  # Identity always highest priority
                priority_map.append((0, section))
            elif section.startswith("RESPONSE STYLE:"):
                priority_map.append((1, section))  # Always important - keeps response quality
            elif section.startswith("MEMORY CONTEXT:") and context_analysis.get('needs_memory_context'):
                priority_map.append((2, section))  # 🎯 HIGHER PRIORITY - conversation continuity critical
            elif section.startswith("AI IDENTITY:") and context_analysis.get('needs_ai_guidance'):
                priority_map.append((3, section))  # Important when needed but less dynamic
            elif section.startswith("PERSONALITY:") and context_analysis.get('needs_personality'):
                priority_map.append((4, section))  # Static content - can be trimmed more aggressively
            elif section.startswith("VOICE:") and context_analysis.get('needs_voice_style'):
                priority_map.append((5, section))  # Static content - can be trimmed more aggressively
            else:
                priority_map.append((6, section))  # Lowest priority
        
        # Sort by priority and return sections
        priority_map.sort(key=lambda x: x[0])
        return [section for _, section in priority_map]
    
    def _truncate_section_to_words(self, section: str, max_words: int) -> str:
        """Truncate a section to fit within word limit while preserving structure."""
        words = section.split()
        if len(words) <= max_words:
            return section
        
        # Keep header and truncate content
        lines = section.split('\n')
        if len(lines) > 1:
            header = lines[0]
            remaining_words = max_words - len(header.split()) - 2
            if remaining_words > 10:
                content_words = []
                current_count = 0
                for line in lines[1:]:
                    line_words = line.split()
                    if current_count + len(line_words) <= remaining_words:
                        content_words.extend(line_words)
                        current_count += len(line_words)
                    else:
                        break
                
                if content_words:
                    return header + '\n' + ' '.join(content_words) + '...'
        
        # Fallback: just truncate words
        return ' '.join(words[:max_words]) + '...'
    
    def _trim_to_budget(self, sections: List[str]) -> str:
        """Trim prompt sections to stay within word budget."""
        # Priority order: Identity > AI Guidance (if present) > Guidelines > Voice > Personality > Memory
        essential_sections = []
        optional_sections = []
        
        for i, section in enumerate(sections):
            # Protect Identity (always first) and AI Guidance sections
            if i == 0 or section.startswith("AI IDENTITY:"):
                essential_sections.append(section)
            elif section.startswith("RESPONSE STYLE:"):
                essential_sections.append(section)  # Guidelines are essential
            else:
                optional_sections.append(section)
        
        # Start with essentials
        current_prompt = "\n\n".join(essential_sections)
        current_words = len(current_prompt.split())
        
        # Add optional sections if we have budget
        for section in optional_sections:
            section_words = len(section.split())
            if current_words + section_words <= self.max_words:
                current_prompt += "\n\n" + section
                current_words += section_words
            else:
                break
                
        return current_prompt


# Factory function for easy integration
def create_optimized_prompt_builder(max_words: int = 1000, llm_client=None, memory_manager=None) -> OptimizedPromptBuilder:
    """Create an optimized prompt builder instance with optional conversation summarizer and vector memory."""
    return OptimizedPromptBuilder(max_words=max_words, llm_client=llm_client, memory_manager=memory_manager)