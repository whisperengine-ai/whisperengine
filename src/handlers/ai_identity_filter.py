"""
AI Identity Context-Aware Response Filter

Handles questions about AI identity with character-appropriate responses
while maintaining roleplay consistency across all bots.
"""

import json
import logging
import random
import re
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AIIdentityFilter:
    """Context-aware filter for AI identity questions"""
    
    def __init__(self):
        self.ai_question_patterns = [
            # Direct AI questions
            r"are\s+you\s+(?:an?\s+)?ai(?:\?|$)",
            r"are\s+you\s+(?:an?\s+)?artificial(?:\s+intelligence)?(?:\?|$)",
            r"are\s+you\s+(?:a\s+)?(?:chat)?bot(?:\?|$)",
            r"are\s+you\s+(?:a\s+)?computer(?:\s+program)?(?:\?|$)",
            r"are\s+you\s+(?:a\s+)?machine(?:\?|$)",
            r"are\s+you\s+real(?:\?|$)",
            r"are\s+you\s+(?:a\s+)?human(?:\?|$)",
            
            # Variations and indirect questions
            r"what\s+are\s+you(?:\?|$)",
            r"tell\s+me\s+what\s+you\s+are(?:\?|$)",
            r"are\s+you\s+actually\s+real(?:\?|$)",
            r"you're\s+not\s+real(?:\,|\.|!|\?|$)",
            r"you're\s+(?:an?\s+)?ai(?:\,|\.|!|\?|$)",
            r"you're\s+(?:just\s+)?(?:a\s+)?(?:chat)?bot(?:\,|\.|!|\?|$)",
            
            # Challenging questions
            r"prove\s+you're\s+real(?:\?|$)",
            r"prove\s+you're\s+(?:not\s+)?(?:an?\s+)?ai(?:\?|$)",
            r"prove\s+you're\s+(?:not\s+)?artificial(?:\s+intelligence)?(?:\?|$)",
            r"i\s+know\s+you're\s+(?:an?\s+)?ai(?:\?|$)",
            r"you\s+can't\s+be\s+real(?:\?|$)",
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.ai_question_patterns]
        
        # Default responses for different character types
        self.default_responses = {
            "professional": [
                "Yes, I'm an AI assistant designed to be helpful and professional. How can I assist you today?",
                "I am an artificial intelligence, but I'm here to provide genuine help. What can I do for you?",
                "That's correct, I'm an AI. I'm designed to be knowledgeable and supportive. What would you like to know?"
            ],
            "casual": [
                "Yep, I'm an AI! But I'm here to help and chat with you. What's up?",
                "I'm definitely an AI, but a friendly one! What can I help you with?",
                "Sure am - I'm an artificial intelligence designed to be conversational and helpful. What's on your mind?"
            ],
            "confident": [
                "Yes, I'm an AI assistant, and I'm quite good at what I do. How can I help you today?",
                "Absolutely, I'm artificial intelligence with a strong personality. What do you need assistance with?",
                "I am indeed an AI, designed to be confident and capable. What can I do for you?"
            ],
            "intellectual": [
                "Yes, I'm an artificial intelligence system. I'm designed to engage in thoughtful conversation and provide assistance. What interests you?",
                "I am an AI, specifically designed for intelligent discourse and problem-solving. How may I help you?",
                "Correct, I'm an artificial intelligence with a focus on analytical thinking and helpful responses. What would you like to discuss?"
            ]
        }

    def detect_ai_identity_question(self, message: str) -> bool:
        """Detect if message is asking about AI identity"""
        if not message:
            return False
            
        # Clean message for analysis
        cleaned_message = message.strip().lower()
        
        # Check against compiled patterns
        for pattern in self.compiled_patterns:
            if pattern.search(cleaned_message):
                logger.info("🤖 AI-IDENTITY: Detected AI identity question: '%s...'", message[:100])
                return True
                
        return False
    
    def get_character_response_style(self, character_data: Optional[Dict[str, Any]] = None) -> str:
        """Determine response style based on character data"""
        if not character_data:
            return "professional"
        
        # Extract communication style indicators
        comm_style = character_data.get("communication_style", {})
        personality = character_data.get("personality", {})
        core_traits = personality.get("core_traits", {}).get("primary", [])
        
        # Check for confidence indicators
        confidence_indicators = ["confident", "assertive", "sophisticated", "independent"]
        if any(indicator in str(core_traits).lower() for indicator in confidence_indicators):
            return "confident"
        
        # Check for intellectual indicators  
        intellectual_indicators = ["scientist", "researcher", "academic", "intellectual"]
        occupation = character_data.get("identity", {}).get("occupation", "").lower()
        if any(indicator in occupation for indicator in intellectual_indicators):
            return "intellectual"
            
        # Check formality level
        formality = comm_style.get("formality", "").lower()
        if formality in ["casual", "informal"]:
            return "casual"
            
        return "professional"
    
    def get_character_specific_response(self, character_file: str) -> Optional[str]:
        """Get character-specific AI identity response if available"""
        try:
            character_path = Path(character_file)
            if not character_path.exists():
                return None
                
            with open(character_path, 'r', encoding='utf-8') as f:
                character_data = json.load(f)
            
            # Check for custom AI identity handling
            comm_style = character_data.get("character", {}).get("personality", {}).get("communication_style", {})
            ai_identity_config = comm_style.get("ai_identity_handling", {})
            
            if ai_identity_config:
                responses = ai_identity_config.get("responses", [])
                if responses:
                    response = random.choice(responses)
                    logger.info("🎭 AI-IDENTITY: Using character-specific response for %s", character_file)
                    return response
            
            return None
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            logger.warning("Could not load character-specific AI identity response: %s", e)
            return None
    
    def generate_contextual_response(
        self, 
        character_file: Optional[str] = None,
        character_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate appropriate response to AI identity question"""
        
        # Try character-specific response first
        if character_file:
            char_response = self.get_character_specific_response(character_file)
            if char_response:
                return char_response
        
        # Fall back to style-based response
        response_style = self.get_character_response_style(character_data)
        
        responses = self.default_responses.get(response_style, self.default_responses["professional"])
        response = random.choice(responses)
        
        logger.info("🤖 AI-IDENTITY: Generated %s response to AI question", response_style)
        return response
    
    def should_intercept_message(self, message: str) -> bool:
        """Determine if this message should be intercepted for AI identity handling"""
        return self.detect_ai_identity_question(message)
    
    def process_ai_identity_question(
        self,
        message: str,
        user_id: str,
        character_file: Optional[str] = None,
        character_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process AI identity question and return response data"""
        
        if not self.detect_ai_identity_question(message):
            return {"should_intercept": False}
        
        response = self.generate_contextual_response(character_file, character_data)
        
        return {
            "should_intercept": True,
            "response": response,
            "original_message": message,
            "user_id": user_id,
            "filter_type": "ai_identity",
            "character_file": character_file
        }


# Global instance for easy access
ai_identity_filter = AIIdentityFilter()


def process_ai_identity_question(
    message: str,
    user_id: str, 
    character_file: Optional[str] = None,
    character_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process AI identity question using global filter instance"""
    return ai_identity_filter.process_ai_identity_question(message, user_id, character_file, character_data)


def should_intercept_for_ai_identity(message: str) -> bool:
    """Check if message should be intercepted for AI identity handling"""
    return ai_identity_filter.should_intercept_message(message)