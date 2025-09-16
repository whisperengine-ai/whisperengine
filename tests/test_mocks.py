"""
Mock objects and fixtures for testing LLM-dependent functionality
"""

from unittest.mock import MagicMock, Mock
from typing import Dict, Any, List, Optional


class MockLMStudioClient:
    """Mock LMStudioClient for unit testing"""

    def __init__(
        self,
        connection_works: bool = True,
        emotion_responses: Optional[Dict[str, Dict[str, Any]]] = None,
        personal_info_responses: Optional[Dict[str, Dict[str, Any]]] = None,
        trust_responses: Optional[Dict[str, Dict[str, Any]]] = None,
        user_facts_responses: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        """
        Initialize mock LLM client with configurable responses

        Args:
            connection_works: Whether check_connection() should return True
            emotion_responses: Dict mapping messages to emotion analysis responses
            personal_info_responses: Dict mapping messages to personal info responses
            trust_responses: Dict mapping messages to trust indicator responses
            user_facts_responses: Dict mapping messages to user facts responses
        """
        self.connection_works = connection_works
        self.emotion_responses = emotion_responses or {}
        self.personal_info_responses = personal_info_responses or {}
        self.trust_responses = trust_responses or {}
        self.user_facts_responses = user_facts_responses or {}

        # Track method calls for assertions
        self.analyze_emotion_calls = []
        self.extract_personal_info_calls = []
        self.detect_trust_indicators_calls = []
        self.extract_user_facts_calls = []

    def check_connection(self) -> bool:
        """Mock connection check"""
        return self.connection_works

    def analyze_emotion(self, message: str) -> Dict[str, Any]:
        """Mock emotion analysis"""
        self.analyze_emotion_calls.append(message)

        # Return configured response or default
        if message in self.emotion_responses:
            return self.emotion_responses[message]

        # Default happy response for positive keywords
        if any(
            word in message.lower() for word in ["happy", "excited", "great", "awesome", "love"]
        ):
            return {
                "primary_emotion": "happy",
                "confidence": 0.85,
                "intensity": 0.7,
                "secondary_emotions": ["excited"],
                "reasoning": f"Message '{message}' contains positive language indicating happiness",
            }

        # Default frustrated response for negative keywords
        if any(
            word in message.lower()
            for word in ["frustrated", "frustrating", "angry", "hate", "terrible", "awful"]
        ):
            return {
                "primary_emotion": "frustrated",
                "confidence": 0.8,
                "intensity": 0.6,
                "secondary_emotions": ["disappointed"],
                "reasoning": f"Message '{message}' contains negative language indicating frustration",
            }

        # Default sad response for sad keywords
        if any(word in message.lower() for word in ["sad", "depressed", "down", "blue"]):
            return {
                "primary_emotion": "sad",
                "confidence": 0.75,
                "intensity": 0.6,
                "secondary_emotions": [],
                "reasoning": f"Message '{message}' expresses sadness",
            }

        # Default worried response for worried keywords
        if any(word in message.lower() for word in ["worried", "anxious", "concerned", "nervous"]):
            return {
                "primary_emotion": "worried",
                "confidence": 0.7,
                "intensity": 0.5,
                "secondary_emotions": [],
                "reasoning": f"Message '{message}' expresses worry or anxiety",
            }

        # Default grateful response for thankful keywords
        if any(word in message.lower() for word in ["thank", "grateful", "appreciate"]):
            return {
                "primary_emotion": "grateful",
                "confidence": 0.8,
                "intensity": 0.6,
                "secondary_emotions": ["happy"],
                "reasoning": f"Message '{message}' expresses gratitude",
            }

        # Default curious response for question keywords
        if any(word in message.lower() for word in ["how", "what", "why", "curious", "wonder"]):
            return {
                "primary_emotion": "curious",
                "confidence": 0.7,
                "intensity": 0.5,
                "secondary_emotions": [],
                "reasoning": f"Message '{message}' shows curiosity or inquiry",
            }

        # Default neutral response
        return {
            "primary_emotion": "neutral",
            "confidence": 0.5,
            "intensity": 0.3,
            "secondary_emotions": [],
            "reasoning": f"Message '{message}' appears neutral in tone",
        }

    def extract_personal_info(self, message: str) -> Dict[str, Any]:
        """Mock personal info extraction"""
        self.extract_personal_info_calls.append(message)

        # Return configured response or default
        if message in self.personal_info_responses:
            return self.personal_info_responses[message]

        # Default response based on common patterns
        personal_info = {}

        # Look for name patterns
        if "my name is" in message.lower():
            name_part = message.lower().split("my name is")[1].strip()
            name = name_part.split()[0].capitalize()
            personal_info["names"] = [name]

        # Look for occupation patterns
        if any(word in message.lower() for word in ["work at", "job at", "employed at"]):
            if "google" in message.lower():
                personal_info["occupation"] = ["works at Google"]
            elif "microsoft" in message.lower():
                personal_info["occupation"] = ["works at Microsoft"]

        # Look for hobby patterns
        if any(word in message.lower() for word in ["love", "enjoy", "hobby", "like"]):
            hobbies = []
            if "programming" in message.lower():
                hobbies.append("programming")
            if "hiking" in message.lower():
                hobbies.append("hiking")
            if hobbies:
                personal_info["hobbies"] = hobbies

        return {"personal_info": personal_info}

    def detect_trust_indicators(self, message: str) -> Dict[str, Any]:
        """Mock trust indicator detection"""
        self.detect_trust_indicators_calls.append(message)

        # Return configured response or default
        if message in self.trust_responses:
            return self.trust_responses[message]

        # Default response based on trust patterns
        trust_indicators = []

        if any(word in message.lower() for word in ["thank you", "thanks", "grateful"]):
            trust_indicators.append("expressing gratitude")

        if any(word in message.lower() for word in ["help", "support", "assist"]):
            trust_indicators.append("seeking help")

        if "my name is" in message.lower():
            trust_indicators.append("sharing personal name")

        if any(word in message.lower() for word in ["work", "job", "family"]):
            trust_indicators.append("sharing personal details")

        return {"trust_indicators": trust_indicators}

    def extract_user_facts(self, message: str) -> Dict[str, Any]:
        """Mock user facts extraction"""
        self.extract_user_facts_calls.append(message)

        # Return configured response or default
        if message in self.user_facts_responses:
            return self.user_facts_responses[message]

        # Default fact extraction
        facts = []

        if "my name is" in message.lower():
            name_part = message.lower().split("my name is")[1].strip()
            name = name_part.split()[0].capitalize()
            facts.append(f"User's name is {name}")

        if "work at" in message.lower():
            work_part = message.lower().split("work at")[1].strip()
            company = work_part.split()[0].capitalize()
            facts.append(f"User works at {company}")

        if any(word in message.lower() for word in ["love", "enjoy"]):
            if "programming" in message.lower():
                facts.append("User enjoys programming")
            if "hiking" in message.lower():
                facts.append("User enjoys hiking")

        return {"extracted_facts": facts}

    def generate_chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Mock chat completion"""
        return {
            "choices": [
                {
                    "message": {
                        "content": "This is a mock response from the LLM.",
                        "role": "assistant",
                    }
                }
            ]
        }


def create_mock_llm_client(
    connection_works: bool = True,
    emotion_responses: Optional[Dict[str, Dict[str, Any]]] = None,
    personal_info_responses: Optional[Dict[str, Dict[str, Any]]] = None,
    trust_responses: Optional[Dict[str, Dict[str, Any]]] = None,
    user_facts_responses: Optional[Dict[str, Dict[str, Any]]] = None,
) -> MockLMStudioClient:
    """
    Factory function to create a mock LLM client with specific responses

    Args:
        connection_works: Whether the mock should report connection success
        emotion_responses: Custom emotion analysis responses
        personal_info_responses: Custom personal info extraction responses
        trust_responses: Custom trust indicator responses
        user_facts_responses: Custom user facts responses

    Returns:
        MockLMStudioClient instance
    """
    return MockLMStudioClient(
        connection_works=connection_works,
        emotion_responses=emotion_responses,
        personal_info_responses=personal_info_responses,
        trust_responses=trust_responses,
        user_facts_responses=user_facts_responses,
    )


def create_disconnected_mock_llm_client() -> MockLMStudioClient:
    """Create a mock LLM client that simulates connection failure"""
    return MockLMStudioClient(connection_works=False)


# Predefined response sets for common test scenarios
HAPPY_EMOTION_RESPONSES = {
    "I'm so excited about this!": {
        "primary_emotion": "excited",
        "confidence": 0.95,
        "intensity": 0.8,
        "secondary_emotions": ["happy"],
        "reasoning": "The use of 'so excited' directly indicates a strong feeling of excitement and happiness",
    }
}

PERSONAL_INFO_RESPONSES = {
    "My name is Alice and I work at Google": {
        "personal_info": {"names": ["Alice"], "occupation": ["works at Google"]}
    }
}

TRUST_INDICATOR_RESPONSES = {
    "Thank you so much for your help!": {
        "trust_indicators": ["expressing gratitude", "acknowledging help"]
    }
}

USER_FACTS_RESPONSES = {
    "My name is Alice and I love programming": {
        "extracted_facts": ["User's name is Alice", "User loves programming"]
    }
}
