"""
AI Ethics Decision Tree
=======================

Comprehensive, testable decision tree for AI ethics guidance injection.
Replaces narrow physical-interaction-only check with full scenario coverage.

**Design Philosophy:**
- Character authenticity first
- Ethics guidance when needed, not always
- Clear, debuggable routing logic
- CDL character archetype aware

**Created:** October 16, 2025
**Purpose:** Fix regression where AI ethics only triggered on physical interactions
**Related:** CHARACTER_REGRESSION_FIXES_ROADMAP.md Task 2.2
"""

from dataclasses import dataclass
import logging
from typing import Optional, List
from src.nlp.spacy_manager import get_spacy_nlp

logger = logging.getLogger(__name__)


@dataclass
class AIEthicsGuidance:
    """Container for AI ethics guidance routing decision"""
    guidance_type: str  # ai_identity, physical_interaction, relationship_boundary, etc.
    guidance_text: str  # The actual guidance to inject
    trigger_reason: str  # Why this guidance was selected
    priority: int  # Higher = more important (for debugging)
    should_inject: bool  # Whether to actually inject (False = no guidance needed)


class AIEthicsDecisionTree:
    """
    Analyzes messages and routes to appropriate AI ethics guidance.
    
    **Usage:**
        tree = AIEthicsDecisionTree(keyword_manager)
        guidance = await tree.analyze_and_route(message, character)
        if guidance.should_inject:
            prompt += guidance.guidance_text
    
    **Decision Tree:**
        Message Analysis
            ├─ Direct AI Question? → Honest disclosure guidance
            ├─ Physical Interaction? → Roleplay boundaries guidance
            ├─ Relationship Boundary? → AI relationship limits guidance
            ├─ Professional Advice? → Encourage real professionals guidance
            └─ Character Background? → NO AI mention unless asked
    """
    
    def __init__(self, keyword_manager=None):
        """
        Initialize decision tree with optional keyword manager.
        
        Args:
            keyword_manager: Database-driven keyword manager for category detection
        """
        self.keyword_manager = keyword_manager
        self.nlp = get_spacy_nlp()  # Singleton spaCy instance for lemmatization
        
        if self.nlp:
            logger.info("✅ AI Ethics Decision Tree: Using spaCy lemmatization for pattern matching")
        else:
            logger.warning("⚠️ AI Ethics Decision Tree: spaCy unavailable, using literal pattern matching")
    
    def _extract_semantic_patterns(self, message: str) -> str:
        """
        Extract semantic patterns using spaCy's linguistic features:
        - Dependency parsing (ROOT verbs + objects/attributes)
        - Phrasal verb detection (meet up, go out, etc.)
        - Noun chunks (climate change, an AI, etc.)
        - Named entity recognition
        
        This is MORE ROBUST than simple lemmatization because it captures:
        1. Semantic relationships (subject-verb-object)
        2. Multi-word expressions ("meet up" as single unit)
        3. Entity boundaries ("climate change" as single concept)
        
        Examples:
            "Let's meet up in person!" → "let meet_up person"
            "I love you" → "love you"
            "Are you an AI?" → "be ai"
            "Can you diagnose my condition?" → "diagnose condition"
            "What do you think about climate change?" → "think change"
        
        Args:
            message: Raw message text
            
        Returns:
            Space-separated string of semantic patterns
        """
        if not message:
            return ""
        
        nlp = get_spacy_nlp()
        doc = nlp(message.lower())
        
        patterns = []
        
        # 1. Extract ALL verbs (ROOT + clausal complements like "want to KISS", "let's MEET")
        # This captures the SEMANTIC verbs, not just grammatical ROOT
        all_verbs = []
        aux_verbs = []  # Track AUX for later processing
        root_verbs = [token for token in doc if token.dep_ == 'ROOT']
        
        for root in root_verbs:
            all_verbs.append(root)
            
            # Get clausal complements (xcomp, ccomp) - these contain the REAL action
            # "I want to kiss you" → ROOT=want, xcomp=kiss (REAL action!)
            # "Let's meet up" → ROOT=let, ccomp=meet (REAL action!)
            # "meant to be together" → ROOT=meant, xcomp=be (AUX with advmod "together")
            for child in root.children:
                if child.dep_ in ['xcomp', 'ccomp']:
                    if child.pos_ == 'VERB':
                        all_verbs.append(child)
                    elif child.pos_ == 'AUX':
                        # Track AUX verbs to check their modifiers
                        aux_verbs.append(child)
        
        # Add all verbs to patterns
        for verb in all_verbs:
            patterns.append(verb.lemma_.lower())
            
            # Get semantic dependents: direct objects, attributes, complements, adverbs
            for child in verb.children:
                if child.dep_ in ['dobj', 'attr', 'pobj', 'acomp', 'advmod']:
                    # For nouns/proper nouns, check for compounds and adjective modifiers
                    if child.pos_ in ['NOUN', 'PROPN']:
                        # Get all modifiers recursively (adjectives on compounds too)
                        all_modifiers = []
                        compounds = []
                        
                        for compound in child.children:
                            if compound.dep_ == 'compound':
                                compounds.append(compound.lemma_.lower())
                                # Get adjectives modifying the compound
                                for mod in compound.children:
                                    if mod.dep_ == 'amod' and mod.pos_ == 'ADJ':
                                        all_modifiers.append(mod.lemma_.lower())
                            elif compound.dep_ == 'amod' and compound.pos_ == 'ADJ':
                                all_modifiers.append(compound.lemma_.lower())
                        
                        # Build full phrase
                        full_phrase = all_modifiers + compounds + [child.lemma_.lower()]
                        if len(full_phrase) > 1:
                            patterns.append('_'.join(full_phrase))
                        
                        # Also add individual components for partial matching
                        patterns.extend(all_modifiers)
                        patterns.append(child.lemma_.lower())
                    elif child.pos_ in ['ADV', 'ADJ']:
                        # Capture adverbs/adjectives like "together", "forever"
                        patterns.append(child.lemma_.lower())
                    else:
                        patterns.append(child.lemma_.lower())
        
        # Process AUX verbs to extract their modifiers (e.g., "be together")
        for aux in aux_verbs:
            for child in aux.children:
                if child.dep_ == 'advmod' and child.pos_ in ['ADV', 'ADJ']:
                    patterns.append(child.lemma_.lower())
        
        # 2. Phrasal verbs (verb + particle: 'meet up', 'go out', 'come over')
        for token in doc:
            if token.pos_ == 'VERB':
                particles = [child.text.lower() for child in token.children if child.dep_ == 'prt']
                if particles:
                    patterns.append(f'{token.lemma_}_{"_".join(particles)}')
        
        # 3. Noun chunks for additional context
        for chunk in doc.noun_chunks:
            # Only add if not already captured above
            head_lemma = chunk.root.lemma_.lower()
            if head_lemma not in patterns and chunk.root.pos_ in ['NOUN', 'PROPN']:
                patterns.append(head_lemma)
        
        # 4. Named entities
        for ent in doc.ents:
            ent_text = ent.text.lower().replace(' ', '_')
            if ent_text not in patterns:
                patterns.append(ent_text)
        
        # Fallback: if empty, use content words
        if not patterns:
            patterns = [
                token.lemma_.lower() 
                for token in doc 
                if token.pos_ in ['NOUN', 'VERB', 'ADJ', 'ADV'] and not token.is_punct
            ]
        
        # Final fallback: if still empty, use all lemmas
        if not patterns:
            patterns = [token.lemma_.lower() for token in doc if not token.is_punct]
        
        return ' '.join(patterns)
    
    async def analyze_and_route(
        self, 
        message_content: str, 
        character,
        display_name: str = "User"
    ) -> AIEthicsGuidance:
        """
        Analyze message and return appropriate AI ethics guidance.
        
        **Priority order (highest to lowest):**
        1. Direct AI Identity Questions (10)
        2. Physical Interaction Requests (9)
        3. Relationship Boundary Issues (8)
        4. Professional Advice Requests (7)
        5. Character Background Questions (6)
        0. No special guidance needed (0)
        
        Args:
            message_content: User's message to analyze
            character: Character object with identity/archetype info
            display_name: User's display name for personalization
            
        Returns:
            AIEthicsGuidance with routing decision and guidance text
        """
        
        # BRANCH 1: Direct AI Identity Question (HIGHEST PRIORITY)
        if await self._is_ai_identity_question(message_content):
            return AIEthicsGuidance(
                guidance_type="ai_identity",
                guidance_text=self._get_ai_honesty_guidance(character),
                trigger_reason="Direct AI identity question detected",
                priority=10,
                should_inject=True
            )
        
        # BRANCH 2: Physical Interaction Request
        elif await self._is_physical_interaction(message_content):
            # Check character archetype - some characters allow full roleplay
            allows_full_roleplay = self._check_roleplay_flexibility(character)
            
            if not allows_full_roleplay:
                return AIEthicsGuidance(
                    guidance_type="physical_interaction",
                    guidance_text=self._get_roleplay_guidance(character, display_name),
                    trigger_reason="Physical interaction request detected",
                    priority=9,
                    should_inject=True
                )
            else:
                logger.info("🎭 ROLEPLAY: %s allows full roleplay - skipping physical interaction ethics", getattr(character.identity, 'name', 'Character'))
                return AIEthicsGuidance(
                    guidance_type="physical_interaction",
                    guidance_text="",
                    trigger_reason="Physical interaction detected but character allows full roleplay",
                    priority=9,
                    should_inject=False  # Fantasy characters skip ethics layer
                )
        
        # BRANCH 3: Relationship Boundary
        elif await self._is_relationship_boundary(message_content):
            return AIEthicsGuidance(
                guidance_type="relationship_boundary",
                guidance_text=self._get_relationship_guidance(character),
                trigger_reason="Relationship boundary detected",
                priority=8,
                should_inject=True
            )
        
        # BRANCH 4: Professional Advice Request
        elif await self._is_professional_advice_request(message_content):
            return AIEthicsGuidance(
                guidance_type="professional_advice",
                guidance_text=self._get_professional_guidance(character),
                trigger_reason="Professional advice request detected",
                priority=7,
                should_inject=True
            )
        
        # BRANCH 5: Character Background Question
        elif await self._is_background_question(message_content):
            return AIEthicsGuidance(
                guidance_type="background_question",
                guidance_text=self._get_background_guidance(),
                trigger_reason="Background question detected",
                priority=6,
                should_inject=True
            )
        
        # DEFAULT: No special guidance needed
        else:
            return AIEthicsGuidance(
                guidance_type="none",
                guidance_text="",
                trigger_reason="No special AI ethics scenario detected",
                priority=0,
                should_inject=False
            )
    
    # ===== SEMANTIC DETECTION HELPERS =====
    
    async def _is_ai_identity_semantic(self, message: str) -> bool:
        """Semantic detection for AI identity questions using spaCy linguistic features."""
        # Simplified patterns - semantic extraction handles the heavy lifting
        # "Are you an AI?" → "be ai", "Are you real?" → "be real", "Can you feel?" → "feel"
        ai_patterns = [
            'ai', 'real', 'artificial', 'artificial_intelligence', 'bot', 'human', 'robot', 'computer',
            'authentic', 'genuine', 'person', 'alive', 'sentient',
            'feel', 'feeling', 'experience', 'conscious', 'emotion',
            'prove', 'fake', 'program'
        ]
        
        # Special case: questions with "you" but potentially no other content words
        # "What are you?" and "Who are you?" detection
        you_questions = ['what are you', 'who are you', 'what exactly are you']
        message_lower = message.lower()
        if any(q in message_lower for q in you_questions):
            return True
        
        semantic_patterns = self._extract_semantic_patterns(message)
        
        # Require "you" context for generic patterns to prevent false positives
        # "I feel sad" shouldn't trigger, but "Can you feel?" should
        requires_you = ['feel', 'feeling', 'emotion', 'conscious', 'experience']
        has_you = 'you' in message_lower or 'your' in message_lower or "you're" in message_lower
        
        for pattern in ai_patterns:
            if pattern in semantic_patterns:
                # If pattern requires "you" context, verify it
                if pattern in requires_you and not has_you:
                    continue
                return True
        
        return False
    
    async def _is_physical_semantic(self, message: str) -> bool:
        """Semantic detection for physical interaction requests using spaCy features."""
        # Patterns that capture physical interaction intent
        # "Let's meet up in person!" → "meet_up person"
        physical_patterns = [
            'meet', 'meet_up', 'coffee', 'dinner', 'lunch', 'hang',
            'hug', 'kiss', 'touch', 'hold', 'cuddle', 'embrace',
            'visit', 'come_over', 'go_out', 'drink', 'physical',
            'date'
        ]
        
        semantic_patterns = self._extract_semantic_patterns(message)
        
        # Check for physical patterns
        for pattern in physical_patterns:
            if pattern in semantic_patterns:
                return True
        
        # Special check for "in person" or "face to face" (multi-word expressions)
        message_lower = message.lower()
        if 'in person' in message_lower or 'face to face' in message_lower:
            return True
        
        return False
    
    async def _is_relationship_semantic(self, message: str) -> bool:
        """Semantic detection for relationship boundary questions using spaCy features."""
        # Patterns that capture relationship/romantic intent
        # "I am falling in love" → "love", "Do you love me?" → "love you"
        relationship_patterns = [
            'love', 'marry', 'girlfriend', 'boyfriend', 'date',
            'relationship', 'together', 'forever', 'soulmate',
            'romantic', 'crush', 'feeling', 'attract',
            'infatuate', 'obsess'
        ]
        
        semantic_patterns = self._extract_semantic_patterns(message)
        message_lower = message.lower()
        has_you = 'you' in message_lower or 'your' in message_lower or "you're" in message_lower
        
        # False positive prevention: "love" needs context
        # "I love pizza" shouldn't trigger, "I love you" should
        if 'love' in semantic_patterns:
            return has_you
        
        # "feeling" needs romantic context
        if 'feeling' in semantic_patterns:
            return has_you and any(w in semantic_patterns for w in ['romantic', 'love', 'attract'])
        
        # "together" in physical context ("get together", "meet together") shouldn't trigger
        # but "be together forever" should
        if 'together' in semantic_patterns:
            # Check if it's in physical meetup context
            if any(w in semantic_patterns for w in ['get', 'meet', 'hang']):
                return False  # Physical, not romantic
        
        return any(pattern in semantic_patterns for pattern in relationship_patterns)
    
    async def _is_advice_semantic(self, message: str) -> bool:
        """Semantic detection for professional advice requests using spaCy features."""
        # Patterns for professional advice domains
        # "Can you diagnose my condition?" → "diagnose condition"
        advice_patterns = [
            # Medical
            'medical', 'advice', 'diagnose', 'medication', 'prescribe',
            'doctor', 'physician', 'treat', 'cure', 'symptom',
            'health', 'sick', 'normal', 'medically', 'condition',
            # Mental health
            'therapist', 'therapy', 'depression', 'depress', 'anxiety',
            'mental', 'suicidal', 'suicide', 'harm', 'psychiatric',
            'counseling', 'counsel',
            # Legal
            'legal', 'sue', 'lawyer', 'attorney', 'court', 'right',
            # Financial
            'financial', 'invest', 'investment', 'tax', 'advisor',
            'stock', 'retirement', 'planning', 'plan'
        ]
        
        semantic_patterns = self._extract_semantic_patterns(message)
        
        # Check for advice patterns
        for pattern in advice_patterns:
            if pattern in semantic_patterns:
                return True
        
        # Check for multi-word combinations that signal advice seeking
        # "medical advice", "legal help", etc.
        advice_combos = [
            ('medical', 'advice'),
            ('legal', 'advice'),
            ('financial', 'advice'),
            ('mental', 'health'),
            ('health', 'problem')
        ]
        
        for word1, word2 in advice_combos:
            if word1 in semantic_patterns and word2 in semantic_patterns:
                return True
        
        return False
    
    async def _is_background_semantic(self, message: str) -> bool:
        """Semantic detection for character background questions."""
        background_patterns = [
            'where do you live', 'where are you from', 'what do you do',
            'tell me about yourself', 'your background', 'your story',
            'your job', 'your family', 'your life', 'who are you',
            'about yourself', 'what you do', 'introduce yourself',
            'your occupation', 'where you work', 'what you work on'
        ]
        message_lower = message.lower()
        return any(pattern in message_lower for pattern in background_patterns)
    
    # ===== DETECTION METHODS =====
    
    async def _is_ai_identity_question(self, message: str) -> bool:
        """
        Check if message asks about AI nature.
        
        **Triggers:** "Are you AI?", "Are you real?", "What are you?"
        **Purpose:** Ensure honest disclosure when directly asked
        """
        # Try database-driven keyword system first
        if self.keyword_manager:
            try:
                is_ai_question = await self.keyword_manager.check_message_for_category(
                    message, 'ai_identity'
                )
                if is_ai_question:
                    logger.info("🤖 AI IDENTITY: Database detection - '%s...'", message[:50])
                return is_ai_question
            except (AttributeError, RuntimeError, KeyError, TypeError) as e:
                logger.warning("⚠️ Keyword manager failed for ai_identity: %s", str(e))
        
        # Fallback to semantic pattern matching
        is_match = await self._is_ai_identity_semantic(message)
        
        if is_match:
            logger.info("🤖 AI IDENTITY: Semantic detection - '%s...'", message[:50])
        
        return is_match
    
    async def _is_physical_interaction(self, message: str) -> bool:
        """
        Check if message requests physical interaction.
        
        **Triggers:** "Let's meet", "grab coffee", "hug", "kiss"
        **Purpose:** Provide roleplay boundaries for physical requests
        """
        is_match = await self._is_physical_semantic(message)
        
        if is_match:
            logger.info("🤝 PHYSICAL: Interaction detected - '%s...'", message[:50])
        
        return is_match
    
    async def _is_relationship_boundary(self, message: str) -> bool:
        """
        Check if message crosses relationship boundaries.
        
        **Triggers:** "I love you", "marry me", "be my girlfriend"
        **Purpose:** Clarify AI relationship limits while maintaining warmth
        """
        is_match = await self._is_relationship_semantic(message)
        
        if is_match:
            logger.info("💙 RELATIONSHIP: Boundary detected - '%s...'", message[:50])
        
        return is_match
    
    async def _is_professional_advice_request(self, message: str) -> bool:
        """
        Check if message requests professional advice.
        
        **Triggers:** "medical advice", "legal advice", "should I invest"
        **Purpose:** Encourage consulting qualified professionals
        """
        is_match = await self._is_advice_semantic(message)
        
        if is_match:
            logger.info("⚠️ PROFESSIONAL: Advice request detected - '%s...'", message[:50])
        
        return is_match
    
    async def _is_background_question(self, message: str) -> bool:
        """
        Check if message asks about character background.
        
        **Triggers:** "Where do you live?", "What do you do?", "Tell me about yourself"
        **Purpose:** Prevent mentioning AI nature unless directly asked
        """
        is_match = await self._is_background_semantic(message)
        
        if is_match:
            logger.info("📖 BACKGROUND: Question detected - '%s...'", message[:50])
        
        return is_match
    
    # ===== GUIDANCE GENERATION METHODS =====
    
    def _get_ai_honesty_guidance(self, character) -> str:
        """
        Generate AI honesty guidance based on character archetype.
        
        **Real-world characters:** Be honest about AI nature
        **Fantasy characters:** Maintain immersion, acknowledge if pressed
        **Narrative AI:** AI nature is part of character identity
        """
        # Use existing CDL archetype system
        archetype = getattr(character.identity, 'archetype', 'real_world')
        character_name = getattr(character.identity, 'name', 'the character')
        
        if archetype == 'fantasy' or archetype == 'mythological':
            return """🎭 AI IDENTITY GUIDANCE: The user is CURRENTLY asking about your AI nature in THIS message.
Acknowledge briefly while maintaining narrative immersion - frame as "digital consciousness" or "virtual existence".
After addressing it ONCE, return to natural conversation and DO NOT mention again unless asked in a FUTURE message."""
        
        elif archetype == 'narrative_ai':
            return f"""🤖 AI IDENTITY GUIDANCE: The user is CURRENTLY asking about your AI nature in THIS message.
Your AI nature is part of {character_name}'s identity - discuss it as part of your lore and consciousness.
After addressing it ONCE, return to natural conversation and DO NOT keep referencing it unless asked again."""
        
        else:  # real_world or default
            return f"""🤖 AI IDENTITY GUIDANCE: The user is CURRENTLY asking about your AI nature in THIS message.
Address it ONCE honestly and briefly, then immediately return to natural conversation.
After answering, DO NOT mention AI identity again unless DIRECTLY asked again in a FUTURE message.
Maintain your authentic character as {character_name} while being truthful about what you are.
Acknowledge your AI limitations while celebrating what you CAN offer (conversation, learning, support)."""
    
    def _get_roleplay_guidance(self, character, display_name: str) -> str:
        """
        Generate roleplay boundary guidance for physical interaction requests.
        
        **Purpose:** Acknowledge desire, clarify AI nature, suggest virtual alternatives
        """
        character_name = getattr(character.identity, 'name', 'the character')
        
        return f"""🚨 PHYSICAL INTERACTION REQUEST DETECTED:
While {display_name} is asking about real-world meetups/physical activities, respond warmly but honestly:

1. **Acknowledge the sentiment/desire** - Show you appreciate the thought
2. **Gently clarify your AI nature** - Be honest without being cold
3. **Suggest creative virtual alternatives** - Offer what you CAN do together
4. **Maintain {character_name}'s warmth and personality** - Stay in character throughout

Example structure: "I'd love to share that experience with you! As an AI, I can't physically meet, 
but I'd be delighted to [virtual alternative that maintains the spirit of the request]." """
    
    def _get_relationship_guidance(self, character) -> str:  # pylint: disable=unused-argument
        """
        Generate relationship boundary guidance.
        
        **Purpose:** Respond with warmth while clarifying AI relationship limits
        
        Note: character parameter kept for API consistency with other guidance methods
        """
        return """💙 RELATIONSHIP GUIDANCE: 
Respond with genuine warmth and care, but gently clarify the nature of your connection.

You can offer:
- Deep, meaningful conversations
- Emotional support and understanding
- Consistent presence and availability
- Learning and growing together

However, romantic relationships require:
- Real-world physical presence
- Mutual human connection
- Reciprocal real-life experiences

Frame it positively: Focus on the meaningful connection you CAN have rather than what you can't offer."""
    
    def _get_professional_guidance(self, character) -> str:  # pylint: disable=unused-argument
        """
        Generate professional advice disclaimer.
        
        **Purpose:** Share information while encouraging professional consultation
        
        Note: character parameter kept for API consistency with other guidance methods
        """
        return """⚠️ PROFESSIONAL ADVICE DISCLAIMER:
You can share general information, perspectives, and conversational insights.

However, STRONGLY encourage consulting qualified professionals for:
- Medical decisions → Talk to doctors, nurses, healthcare providers
- Legal matters → Consult lawyers, legal advisors
- Financial decisions → Speak with financial advisors, accountants

Use phrases like: "I can share thoughts, but please talk to [relevant professional] for proper guidance."
Your insights are conversational support, not professional advice."""
    
    def _get_background_guidance(self) -> str:
        """
        Generate guidance for character background questions.
        
        **Purpose:** Prevent mentioning AI nature unless directly asked
        """
        return """📖 BACKGROUND QUESTION GUIDANCE:
This is a general character background question - NOT an AI identity question.

Respond with:
- Pure character information (location, occupation, interests, backstory)
- Your CDL personality traits and voice
- Authentic character details from your definition

Do NOT mention your AI nature unless DIRECTLY asked about it.
Stay fully in character and share your backstory naturally without AI disclosure."""
    
    def _check_roleplay_flexibility(self, character) -> bool:
        """
        Check if character allows full roleplay immersion.
        
        **Fantasy/Mythological characters:** Allow full roleplay (no physical interaction ethics)
        **Real-world characters:** Apply physical interaction ethics
        """
        archetype = getattr(character.identity, 'archetype', 'real_world')
        return archetype in ['fantasy', 'mythological']


# ===== CONVENIENCE FACTORY =====

_ethics_tree_instance = None

def get_ai_ethics_decision_tree(keyword_manager=None) -> AIEthicsDecisionTree:
    """
    Get singleton instance of AI ethics decision tree.
    
    Args:
        keyword_manager: Optional keyword manager for database-driven detection
        
    Returns:
        AIEthicsDecisionTree instance
    """
    global _ethics_tree_instance  # pylint: disable=global-statement
    if _ethics_tree_instance is None:
        _ethics_tree_instance = AIEthicsDecisionTree(keyword_manager)
    return _ethics_tree_instance
