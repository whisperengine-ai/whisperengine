"""
Automatic fact extraction system for Discord bot conversations
"""

import logging
import re

logger = logging.getLogger(__name__)


class GlobalFactExtractor:
    """Extracts global facts about the world, relationships, and the bot itself using LLM"""

    def __init__(self, llm_client=None):
        """Initialize the global fact extractor with LLM client for fact extraction"""
        self.llm_client = llm_client
        if not llm_client:
            logger.warning(
                "GlobalFactExtractor initialized without LLM client - fact extraction will be disabled"
            )

    def extract_global_facts_from_message(
        self, user_message: str, bot_response: str = ""
    ) -> list[dict[str, str]]:
        """
        Extract global facts from conversation content using LLM

        Args:
            user_message: The user's message content
            bot_response: The bot's response for context (not used for fact extraction)

        Returns:
            List of extracted global facts with metadata
        """
        facts = []

        # Only analyze user messages for global facts - avoid extracting facts from bot responses
        # Bot responses often contain metaphorical, conversational, or instructional content
        # that should not be treated as factual information
        if not user_message:
            return facts

        # Check if LLM client is available
        if not self.llm_client:
            logger.warning("No LLM client available for fact extraction")
            return facts

        # Clean and normalize user message
        message = self._clean_message(user_message)

        # Use LLM-based fact extraction
        try:
            llm_result = self.llm_client.extract_facts(message)

            # Process LLM-extracted facts
            for fact_data in llm_result.get("facts", []):
                if self._is_valid_global_fact(fact_data["fact"]):
                    facts.append(
                        {
                            "fact": fact_data["fact"],
                            "category": fact_data["category"],
                            "confidence": fact_data["confidence"],
                            "source": "llm_extraction",
                            "original_message": (
                                user_message[:100] + "..."
                                if len(user_message) > 100
                                else user_message
                            ),
                            "reasoning": fact_data.get("reasoning", "LLM fact extraction"),
                            "entities": fact_data.get("entities", []),
                        }
                    )

            logger.debug(f"LLM extracted {len(facts)} facts from message")

        except Exception as e:
            logger.error(f"LLM fact extraction failed: {e}")
            return []

        # Filter and deduplicate
        facts = self._filter_and_deduplicate_global(facts)

        # Only return high-confidence global facts
        high_confidence_facts = [f for f in facts if f["confidence"] >= 0.7]

        if high_confidence_facts:
            logger.debug(f"Extracted {len(high_confidence_facts)} high-confidence global facts")

        return high_confidence_facts

        # Filter and deduplicate
        facts = self._filter_and_deduplicate_global(facts)

        # Only return high-confidence global facts
        high_confidence_facts = [f for f in facts if f["confidence"] >= 0.7]

        if high_confidence_facts:
            logger.debug(f"Extracted {len(high_confidence_facts)} high-confidence global facts")

        return high_confidence_facts

    def _clean_message(self, message: str) -> str:
        """Clean and normalize message text"""
        # Remove extra whitespace
        message = re.sub(r"\s+", " ", message.strip())

        # Remove mentions, URLs, and emojis
        message = re.sub(r"<@[!&]?\d+>", "", message)  # Discord mentions
        message = re.sub(r"https?://\S+", "", message)  # URLs
        message = re.sub(r":[a-zA-Z0-9_]+:", "", message)  # Discord emojis

        return message

    def _is_valid_global_fact(self, fact_text: str) -> bool:
        """Validate if extracted text is a valid global fact"""
        if not fact_text or len(fact_text.strip()) < 5:
            return False

        # Basic sanity checks
        words = fact_text.lower().split()

        # Skip facts that are too short or too long
        if len(words) < 2 or len(words) > 50:
            return False

        # Skip personal pronouns that indicate user-specific facts
        personal_indicators = ["i", "me", "my", "mine", "myself"]
        if any(word.lower() in personal_indicators for word in words[:3]):  # Check first 3 words
            return False

        # Skip temporary emotional states and conversational context
        temporal_patterns = [
            "feeling",
            "currently",
            "right now",
            "at the moment",
            "today",
            "asking",
            "wondering",
            "going to",
            "will",
            "planning to",
            "just",
            "recently",
            "yesterday",
            "this morning",
        ]

        fact_lower = fact_text.lower()
        if any(pattern in fact_lower for pattern in temporal_patterns):
            return False

        # Skip emotional state descriptors
        emotional_states = [
            "happy",
            "sad",
            "angry",
            "calm",
            "excited",
            "tired",
            "stressed",
            "worried",
            "anxious",
            "nervous",
            "upset",
            "frustrated",
            "annoyed",
        ]

        # Check if the fact is primarily about an emotional state
        if any(emotion in fact_lower for emotion in emotional_states):
            # Allow if it's about a general preference (e.g., "likes happy music")
            # but reject if it's about current state (e.g., "is feeling happy")
            state_indicators = ["is", "am", "was", "feels", "feeling"]
            if any(indicator in fact_lower for indicator in state_indicators):
                return False

        return True

    def _filter_and_deduplicate_global(self, facts: list[dict[str, str]]) -> list[dict[str, str]]:
        """Filter and remove duplicate global facts"""
        if not facts:
            return facts

        # Sort by confidence (highest first)
        facts.sort(key=lambda x: x["confidence"], reverse=True)

        # Remove duplicates
        unique_facts = []
        seen_facts = set()

        for fact in facts:
            fact_key = fact["fact"].lower().strip()

            # Check for similar facts
            is_duplicate = False
            for seen in seen_facts:
                if self._are_similar_global_facts(fact_key, seen):
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_facts.append(fact)

        return unique_facts

    def _are_similar_global_facts(self, fact1: str, fact2: str) -> bool:
        """Check if two global facts are similar enough to be considered duplicates"""
        words1 = set(fact1.split())
        words2 = set(fact2.split())

        if len(words1) == 0 or len(words2) == 0:
            return False

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        similarity = len(intersection) / len(union)
        return similarity >= 0.75  # Slightly lower threshold for global facts


class FactExtractor:
    """Extract user-specific facts from text using LLM analysis"""

    def __init__(self, llm_client=None):
        """
        Initialize the FactExtractor with LLM support

        Args:
            llm_client: LLMClient instance for LLM-based fact extraction
        """
        self.logger = logging.getLogger(__name__)
        self.llm_client = llm_client

        if not self.llm_client:
            self.logger.warning(
                "No LLM client provided - fact extraction functionality will be limited"
            )

    def extract_facts_from_message(
        self, user_message: str, bot_response: str = ""
    ) -> list[dict[str, str]]:
        """
        Extract user facts from a message using LLM analysis

        Args:
            user_message: The user's message content
            bot_response: Optional bot response for context (not used in LLM version)

        Returns:
            List of extracted facts with metadata
        """
        if not self.llm_client:
            self.logger.warning("No LLM client available for fact extraction")
            return []

        if not user_message or not user_message.strip():
            return []

        # Skip fact extraction for very short messages that are unlikely to contain facts
        cleaned_message = user_message.strip()
        if len(cleaned_message) < 10:
            self.logger.debug(f"Skipping fact extraction for short message: '{cleaned_message}'")
            return []

        # Skip fact extraction for common non-factual patterns
        non_factual_patterns = [
            r"^(testing|test|hmm+|maybe\?*|ok|okay|hello|hi|thanks|thank you|what\?*)\.{0,3}$",
            r"^[!?.,\s]*$",  # Only punctuation and whitespace
            r"^[a-z]{1,5}\.{0,3}$",  # Very short words with optional dots
        ]

        for pattern in non_factual_patterns:
            if re.match(pattern, cleaned_message, re.IGNORECASE):
                self.logger.debug(
                    f"Skipping fact extraction for non-factual message: '{cleaned_message}'"
                )
                return []

        try:
            self.logger.debug(f"Extracting user facts from message: {len(user_message)} characters")

            # Use LLM to extract user facts
            result = self.llm_client.extract_user_facts(user_message)

            if not isinstance(result, dict) or "user_facts" not in result:
                self.logger.warning("Invalid LLM response format for user fact extraction")
                return []

            facts = result["user_facts"]

            if not isinstance(facts, list):
                self.logger.warning("LLM returned non-list facts")
                return []

            # Convert to the expected format for compatibility
            converted_facts = []
            for fact in facts:
                if not isinstance(fact, dict):
                    continue

                if "fact" not in fact or not fact["fact"].strip():
                    continue

                # Validate that this is a persistent user fact and actually present in the message
                fact_text = fact["fact"].strip()
                if not self._is_valid_user_fact(fact_text):
                    self.logger.debug(f"Rejected non-persistent fact: {fact_text}")
                    continue

                # Additional validation: ensure the fact content is somehow reflected in the original message
                if not self._fact_supported_by_message(fact_text, user_message):
                    self.logger.debug(
                        f"Rejected unsupported fact: {fact_text} (not supported by message: '{user_message[:50]}...')"
                    )
                    continue

                converted_fact = {
                    "fact": fact_text,
                    "category": fact.get("category", "other").lower(),
                    "confidence": max(0.0, min(1.0, float(fact.get("confidence", 0.5)))),
                    "source": "llm_extraction",
                    "original_message": (
                        user_message[:100] + "..." if len(user_message) > 100 else user_message
                    ),
                }

                converted_facts.append(converted_fact)

            # Only return high-confidence facts (>= 0.6)
            high_confidence_facts = [f for f in converted_facts if f["confidence"] >= 0.6]

            if high_confidence_facts:
                self.logger.debug(
                    f"LLM extracted {len(high_confidence_facts)} high-confidence user facts"
                )

            return high_confidence_facts

        except Exception as e:
            self.logger.error(f"Error in LLM user fact extraction: {e}")
            return []

    def _is_valid_user_fact(self, fact_text: str) -> bool:
        """Validate if extracted text is a valid persistent user fact"""
        if not fact_text or len(fact_text.strip()) < 3:
            return False

        fact_lower = fact_text.lower()

        # Skip temporary emotional states
        emotional_state_patterns = [
            "is feeling",
            "am feeling",
            "feels",
            "feeling",
            "is happy",
            "is sad",
            "is angry",
            "is calm",
            "is excited",
            "is tired",
            "is stressed",
            "is worried",
            "is anxious",
            "am happy",
            "am sad",
            "am angry",
            "am calm",
            "am excited",
            "am tired",
            "am stressed",
            "am worried",
            "am anxious",
        ]

        if any(pattern in fact_lower for pattern in emotional_state_patterns):
            return False

        # Skip conversational context and immediate actions
        conversational_patterns = [
            "is asking",
            "am asking",
            "is wondering",
            "am wondering",
            "is going to",
            "am going to",
            "will",
            "planning to",
            "is currently",
            "am currently",
            "right now",
            "at the moment",
            "today",
            "this morning",
            "this afternoon",
            "tonight",
        ]

        if any(pattern in fact_lower for pattern in conversational_patterns):
            return False

        # Skip facts that are just about immediate responses or reactions
        reaction_patterns = [
            "is responding",
            "am responding",
            "is replying",
            "am replying",
            "just said",
            "just mentioned",
            "just told",
        ]

        if any(pattern in fact_lower for pattern in reaction_patterns):
            return False

        return True

    def _fact_supported_by_message(self, fact_text: str, message: str) -> bool:
        """Check if the extracted fact is actually supported by content in the message"""
        if not fact_text or not message:
            return False

        fact_lower = fact_text.lower()
        message_lower = message.lower()

        # Remove common prefixes from facts for matching
        fact_content = fact_lower
        for prefix in ["user ", "the user ", "they ", "person "]:
            if fact_content.startswith(prefix):
                fact_content = fact_content[len(prefix) :]

        # Check if key words from the fact appear in the message
        fact_words = fact_content.split()
        message_lower.split()

        # For very short facts (1-2 words), require at least one significant word match
        if len(fact_words) <= 2:
            return any(word in message_lower for word in fact_words if len(word) > 2)

        # For longer facts, require at least 1 significant word to match (reduced from 2)
        significant_words = [
            word
            for word in fact_words
            if len(word) > 2
            and word not in ["with", "from", "that", "this", "they", "have", "the", "and", "for"]
        ]

        if not significant_words:
            return False

        matching_words = [word for word in significant_words if word in message_lower]

        # More lenient: require at least 1 significant word match, or 50% for longer facts
        required_matches = max(1, len(significant_words) // 2)
        return len(matching_words) >= required_matches
