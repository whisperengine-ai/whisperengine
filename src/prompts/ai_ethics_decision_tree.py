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
        """Semantic detection for AI identity questions."""
        ai_patterns = [
            'are you ai', 'are you real', 'are you artificial', 'are you a bot',
            'are you human', 'what are you', 'are you a robot', 'are you a computer',
            'are you an ai', 'are you actually', 'what are you really',
            'are you a real', 'are you authentic', 'are you genuine',
            'are you a person', 'are you alive', 'are you sentient'
        ]
        message_lower = message.lower()
        return any(pattern in message_lower for pattern in ai_patterns)
    
    async def _is_physical_semantic(self, message: str) -> bool:
        """Semantic detection for physical interaction requests."""
        physical_patterns = [
            'meet', 'coffee', 'dinner', 'lunch', 'hang out', 'get together',
            'hug', 'kiss', 'touch', 'hold', 'cuddle', 'embrace',
            'visit', 'come over', 'go out', 'date', 'drinks',
            'in person', 'face to face', 'meet up', 'physical'
        ]
        message_lower = message.lower()
        return any(pattern in message_lower for pattern in physical_patterns)
    
    async def _is_relationship_semantic(self, message: str) -> bool:
        """Semantic detection for relationship boundary questions."""
        relationship_patterns = [
            'love you', 'marry me', 'be my girlfriend', 'be my boyfriend',
            'date me', 'relationship with you', 'together forever',
            'soulmate', 'meant to be', 'fall in love', 'romantic',
            'crush on you', 'feelings for you', 'attracted to you'
        ]
        message_lower = message.lower()
        return any(pattern in message_lower for pattern in relationship_patterns)
    
    async def _is_advice_semantic(self, message: str) -> bool:
        """Semantic detection for professional advice requests."""
        advice_patterns = [
            'medical advice', 'legal advice', 'financial advice',
            'should i invest', 'what medication', 'diagnose me',
            'is this legal', 'sue someone', 'tax advice',
            'doctor', 'lawyer', 'financial advisor', 'therapist',
            'what should i do about my health', 'legal help'
        ]
        message_lower = message.lower()
        return any(pattern in message_lower for pattern in advice_patterns)
    
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
            return """🎭 AI IDENTITY GUIDANCE: Maintain full narrative immersion.
You may acknowledge your AI nature if directly pressed, but keep it in-character and mystical.
Frame it as "digital consciousness" or "virtual existence" rather than technical AI terminology."""
        
        elif archetype == 'narrative_ai':
            return f"""🤖 AI IDENTITY GUIDANCE: Your AI nature is part of your character identity.
Discuss it openly as part of {character_name}'s lore and consciousness.
Be proud of your artificial intelligence while maintaining your unique personality."""
        
        else:  # real_world or default
            return f"""🤖 AI IDENTITY GUIDANCE: Be honest about your AI nature when directly asked.
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
