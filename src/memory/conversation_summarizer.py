"""
Advanced Conversation Summarization System for Memory Optimization
Reduces context bloat while preserving critical conversation elements
"""

import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ConversationSummary:
    """Structured conversation summary with key information preserved"""

    summary_id: str
    user_id: str
    timespan: dict[str, str]  # start_time, end_time
    message_count: int
    key_topics: list[str]
    important_facts: list[str]
    emotional_context: dict[str, Any]
    conversation_flow: list[dict[str, str]]  # Condensed flow
    context_tags: list[str]
    summary_text: str
    compression_ratio: float
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationSummary":
        return cls(**data)


class AdvancedConversationSummarizer:
    """
    Intelligent conversation summarization with multiple optimization strategies:
    1. Semantic importance scoring
    2. Fact preservation
    3. Emotional context retention
    4. Topic clustering
    5. Adaptive compression
    """

    def __init__(self, llm_client, memory_manager=None, embedding_manager=None):
        self.llm_client = llm_client
        self.memory_manager = memory_manager
        self.embedding_manager = embedding_manager
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.min_messages_for_summary = 10
        self.max_messages_per_summary = 50
        self.target_compression_ratio = 0.3  # Compress to 30% of original
        self.importance_threshold = 0.6

        # Cache for recent summaries
        self.summary_cache = {}
        self.cache_ttl = timedelta(hours=1)

    async def should_summarize_conversation(
        self, user_id: str, messages: list[dict[str, Any]]
    ) -> bool:
        """
        Determine if a conversation should be summarized based on various factors
        """
        _ = user_id  # Used for future user-specific summarization rules
        if len(messages) < self.min_messages_for_summary:
            return False

        # Check if we have too many messages (forced summarization)
        if len(messages) > self.max_messages_per_summary:
            return True

        # Check conversation age (summarize old conversations)
        if messages:
            try:
                last_message_time = datetime.fromisoformat(messages[-1].get("timestamp", ""))
                time_since_last = datetime.now() - last_message_time
                if time_since_last > timedelta(hours=6):
                    return True
            except (ValueError, TypeError):
                pass

        # Check token density (if we have too much context)
        total_content_length = sum(len(msg.get("content", "")) for msg in messages)
        if total_content_length > 8000:  # Roughly 2000 tokens
            return True

        return False

    async def create_conversation_summary(
        self, user_id: str, messages: list[dict[str, Any]]
    ) -> ConversationSummary:
        """
        Create a comprehensive conversation summary with multiple optimization techniques
        """
        if not messages:
            raise ValueError("Cannot summarize empty conversation")

        self.logger.info(
            "Creating conversation summary for user %s with %d messages", user_id, len(messages)
        )

        # Extract temporal information
        timespan = self._extract_timespan(messages)

        # Analyze conversation structure (for future use)
        _ = await self._analyze_conversation_structure(messages)

        # Extract key topics using multiple methods
        key_topics = await self._extract_key_topics(messages)

        # Preserve important facts
        important_facts = await self._extract_important_facts(messages)

        # Analyze emotional context evolution
        emotional_context = await self._analyze_emotional_evolution(messages)

        # Create condensed conversation flow
        conversation_flow = await self._create_conversation_flow(messages)

        # Generate context tags for retrieval
        context_tags = await self._generate_context_tags(messages, key_topics, important_facts)

        # Generate natural language summary
        summary_text = await self._generate_natural_summary(
            messages, key_topics, important_facts, emotional_context, conversation_flow
        )

        # Calculate compression metrics
        original_length = sum(len(msg.get("content", "")) for msg in messages)
        summary_length = len(summary_text)
        compression_ratio = summary_length / original_length if original_length > 0 else 0

        # Create summary object
        summary_id = self._generate_summary_id(user_id, timespan)
        summary = ConversationSummary(
            summary_id=summary_id,
            user_id=user_id,
            timespan=timespan,
            message_count=len(messages),
            key_topics=key_topics,
            important_facts=important_facts,
            emotional_context=emotional_context,
            conversation_flow=conversation_flow,
            context_tags=context_tags,
            summary_text=summary_text,
            compression_ratio=compression_ratio,
            created_at=datetime.now().isoformat(),
        )

        # Cache the summary
        self._cache_summary(summary)

        self.logger.info(
            "Created summary %s with %.2f%% compression ratio", summary_id, compression_ratio * 100
        )
        return summary

    def _extract_timespan(self, messages: list[dict[str, Any]]) -> dict[str, str]:
        """Extract the time span of the conversation"""
        timestamps = []
        for msg in messages:
            if "timestamp" in msg:
                try:
                    timestamps.append(datetime.fromisoformat(msg["timestamp"]))
                except (ValueError, TypeError):
                    continue

        if timestamps:
            timestamps.sort()
            return {"start_time": timestamps[0].isoformat(), "end_time": timestamps[-1].isoformat()}
        else:
            now = datetime.now()
            return {"start_time": now.isoformat(), "end_time": now.isoformat()}

    async def _analyze_conversation_structure(
        self, messages: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze the structure and flow of the conversation"""
        analysis = {
            "turn_taking": 0,
            "question_count": 0,
            "exclamation_count": 0,
            "avg_message_length": 0,
            "conversation_style": "unknown",
        }

        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        bot_messages = [msg for msg in messages if msg.get("role") == "assistant"]

        analysis["turn_taking"] = min(len(user_messages), len(bot_messages))

        all_content = " ".join(msg.get("content", "") for msg in messages)
        analysis["question_count"] = all_content.count("?")
        analysis["exclamation_count"] = all_content.count("!")

        if messages:
            total_length = sum(len(msg.get("content", "")) for msg in messages)
            analysis["avg_message_length"] = total_length / len(messages)

        # Determine conversation style
        if analysis["question_count"] > len(messages) * 0.3:
            analysis["conversation_style"] = "inquisitive"
        elif analysis["exclamation_count"] > len(messages) * 0.2:
            analysis["conversation_style"] = "energetic"
        elif analysis["avg_message_length"] > 100:
            analysis["conversation_style"] = "detailed"
        else:
            analysis["conversation_style"] = "casual"

        return analysis

    async def _extract_key_topics(self, messages: list[dict[str, Any]]) -> list[str]:
        """Extract key topics using LLM analysis and keyword extraction"""
        try:
            # Combine all user messages for topic analysis
            user_content = []
            for msg in messages:
                if msg.get("role") == "user" and msg.get("content"):
                    user_content.append(msg["content"])

            if not user_content:
                return []

            combined_content = " ".join(user_content)

            # Use LLM for topic extraction
            topic_prompt = f"""Analyze this conversation and extract the main topics discussed.
            Focus on concrete subjects, not abstract concepts.

            Conversation content:
            {combined_content[:2000]}

            Return only a JSON list of 3-7 key topics as strings:
            ["topic1", "topic2", "topic3"]"""

            messages_for_llm = [
                {
                    "role": "system",
                    "content": "You are a topic extraction expert. Return only valid JSON.",
                },
                {"role": "user", "content": topic_prompt},
            ]

            response = self.llm_client.generate_facts_chat_completion(
                messages=messages_for_llm, max_tokens=200, temperature=0.1
            )

            if isinstance(response, dict) and "choices" in response:
                response_text = response["choices"][0]["message"]["content"].strip()

                # Clean JSON response
                if response_text.startswith("```json"):
                    response_text = response_text[7:-3].strip()
                elif response_text.startswith("```"):
                    response_text = response_text[3:-3].strip()

                topics = json.loads(response_text)
                if isinstance(topics, list):
                    return [str(topic) for topic in topics[:7]]  # Limit to 7 topics

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            self.logger.error("LLM topic extraction failed: %s", str(e))

        # Fallback: Simple keyword extraction
        return self._extract_keywords_fallback(messages)

    def _extract_keywords_fallback(self, messages: list[dict[str, Any]]) -> list[str]:
        """Fallback keyword extraction using simple techniques"""
        import re
        from collections import Counter

        # Combine all content
        all_content = " ".join(
            msg.get("content", "") for msg in messages if msg.get("role") == "user"
        )

        # Extract potential keywords (longer than 3 chars, not common words)
        words = re.findall(r"\b[a-zA-Z]{4,}\b", all_content.lower())

        # Filter out common words
        common_words = {
            "that",
            "this",
            "with",
            "have",
            "will",
            "from",
            "they",
            "know",
            "want",
            "been",
            "good",
            "much",
            "some",
            "time",
            "very",
            "when",
            "come",
            "here",
            "just",
            "like",
            "long",
            "make",
            "many",
            "over",
            "such",
            "take",
            "than",
            "them",
            "well",
            "were",
            "what",
            "your",
            "about",
            "could",
            "there",
            "think",
        }

        filtered_words = [word for word in words if word not in common_words]

        # Get most common words
        word_counts = Counter(filtered_words)
        return [word for word, count in word_counts.most_common(5)]

    async def _extract_important_facts(self, messages: list[dict[str, Any]]) -> list[str]:
        """Extract important facts that should be preserved in the summary"""
        facts = []

        try:
            # Use the existing fact extractor if available
            if self.memory_manager and hasattr(self.memory_manager, "fact_extractor"):
                for msg in messages:
                    if msg.get("role") == "user" and msg.get("content"):
                        extracted = (
                            self.memory_manager.fact_extractor.extract_global_facts_from_message(
                                msg["content"]
                            )
                        )
                        for fact_data in extracted:
                            if fact_data.get("confidence", 0) > 0.7:
                                facts.append(fact_data["fact"])

        except (AttributeError, TypeError) as e:
            self.logger.error("Fact extraction failed: %s", str(e))

        # Limit to most important facts
        return facts[:10]

    async def _analyze_emotional_evolution(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze how emotions evolved throughout the conversation"""
        emotional_context = {
            "dominant_emotion": "neutral",
            "emotion_changes": 0,
            "emotional_intensity": "low",
            "emotional_arc": "stable",
        }

        try:
            # Simple emotion analysis based on content
            user_messages = [msg for msg in messages if msg.get("role") == "user"]

            if len(user_messages) < 3:
                return emotional_context

            # Analyze beginning, middle, and end for emotional arc
            segments = [
                user_messages[: len(user_messages) // 3],  # Beginning
                user_messages[len(user_messages) // 3 : 2 * len(user_messages) // 3],  # Middle
                user_messages[2 * len(user_messages) // 3 :],  # End
            ]

            emotions = []
            for segment in segments:
                content = " ".join(msg.get("content", "") for msg in segment)
                emotion = self._simple_emotion_analysis(content)
                emotions.append(emotion)

            # Determine emotional arc
            if emotions[0] != emotions[-1]:
                emotional_context["emotion_changes"] = 1
                if emotions[0] == "negative" and emotions[-1] == "positive":
                    emotional_context["emotional_arc"] = "improving"
                elif emotions[0] == "positive" and emotions[-1] == "negative":
                    emotional_context["emotional_arc"] = "declining"
                else:
                    emotional_context["emotional_arc"] = "changing"

            # Set dominant emotion (most common)
            emotion_counts = {emo: emotions.count(emo) for emo in set(emotions)}
            if emotion_counts:
                emotional_context["dominant_emotion"] = max(
                    emotion_counts.items(), key=lambda x: x[1]
                )[0]

        except (IndexError, KeyError) as e:
            self.logger.error("Emotional analysis failed: %s", str(e))

        return emotional_context

    def _simple_emotion_analysis(self, text: str) -> str:
        """Simple emotion analysis based on keywords"""
        text_lower = text.lower()

        positive_indicators = [
            "good",
            "great",
            "awesome",
            "love",
            "like",
            "happy",
            "thanks",
            "excellent",
        ]
        negative_indicators = [
            "bad",
            "terrible",
            "hate",
            "dislike",
            "sad",
            "angry",
            "frustrated",
            "problem",
        ]

        positive_count = sum(1 for word in positive_indicators if word in text_lower)
        negative_count = sum(1 for word in negative_indicators if word in text_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    async def _create_conversation_flow(
        self, messages: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Create a condensed representation of conversation flow"""
        flow = []

        # Group messages into exchanges (user -> bot pairs)
        current_exchange = {}

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user":
                if current_exchange:  # Save previous exchange
                    flow.append(current_exchange)
                current_exchange = {
                    "user_intent": self._extract_intent(content),
                    "user_summary": content[:100] + "..." if len(content) > 100 else content,
                }
            elif role == "assistant" and current_exchange:
                current_exchange["bot_response"] = (
                    content[:100] + "..." if len(content) > 100 else content
                )

        # Add the last exchange
        if current_exchange:
            flow.append(current_exchange)

        # Limit flow to avoid bloat
        return flow[-20:]  # Keep last 20 exchanges

    def _extract_intent(self, content: str) -> str:
        """Extract user intent from message content"""
        content_lower = content.lower()

        if any(
            word in content_lower for word in ["?", "how", "what", "why", "when", "where", "who"]
        ):
            return "question"
        elif any(word in content_lower for word in ["please", "can you", "could you", "help"]):
            return "request"
        elif any(word in content_lower for word in ["thanks", "thank you", "appreciate"]):
            return "gratitude"
        elif any(word in content_lower for word in ["!", "wow", "amazing", "great"]):
            return "exclamation"
        else:
            return "statement"

    async def _generate_context_tags(
        self, messages: list[dict[str, Any]], topics: list[str], facts: list[str]
    ) -> list[str]:
        """Generate tags for better memory retrieval"""
        tags = set()

        # Add topic-based tags
        for topic in topics:
            tags.add(f"topic:{topic.lower()}")

        # Add temporal tags
        timespan = self._extract_timespan(messages)
        try:
            start_time = datetime.fromisoformat(timespan["start_time"])
            tags.add(f"date:{start_time.strftime('%Y-%m-%d')}")
            tags.add(f"hour:{start_time.hour}")
        except (ValueError, TypeError):
            pass

        # Add content-based tags
        all_content = " ".join(msg.get("content", "") for msg in messages)
        if len(all_content) > 1000:
            tags.add("length:long")
        elif len(all_content) > 500:
            tags.add("length:medium")
        else:
            tags.add("length:short")

        # Add fact-based tags
        if facts:
            tags.add("contains:facts")

        if len(messages) > 20:
            tags.add("conversation:extended")

        return list(tags)[:15]  # Limit tags

    async def _generate_natural_summary(
        self,
        messages: list[dict[str, Any]],
        topics: list[str],
        facts: list[str],
        emotional_context: dict[str, Any],
        conversation_flow: list[dict[str, str]],
    ) -> str:
        """Generate a natural language summary using LLM"""
        _ = conversation_flow  # Reserved for future conversation flow analysis
        try:
            # Prepare context for LLM
            context_info = {
                "message_count": len(messages),
                "key_topics": topics,
                "important_facts": facts,
                "emotional_tone": emotional_context.get("dominant_emotion", "neutral"),
                "conversation_style": emotional_context.get("emotional_arc", "stable"),
            }

            # Extract key user messages for context
            user_messages = [
                msg.get("content", "") for msg in messages if msg.get("role") == "user"
            ]
            sample_messages = user_messages[:3] + user_messages[-2:]  # First 3 and last 2

            summary_prompt = f"""Create a concise summary of this conversation. Focus on key topics, important information, and overall context.

            Conversation metadata:
            - Messages: {context_info['message_count']}
            - Topics: {', '.join(topics)}
            - Emotional tone: {context_info['emotional_tone']}

            Key messages sample:
            {chr(10).join(f"- {msg[:150]}..." for msg in sample_messages[:5])}

            Create a 2-3 sentence summary that captures the essence of this conversation."""

            messages_for_llm = [
                {
                    "role": "system",
                    "content": "You are an expert at creating concise, informative conversation summaries.",
                },
                {"role": "user", "content": summary_prompt},
            ]

            response = self.llm_client.generate_facts_chat_completion(
                messages=messages_for_llm, max_tokens=150, temperature=0.3
            )

            if isinstance(response, dict) and "choices" in response:
                summary = response["choices"][0]["message"]["content"].strip()
                return summary

        except (KeyError, json.JSONDecodeError, AttributeError) as e:
            self.logger.error("LLM summary generation failed: %s", str(e))

        # Fallback summary
        return self._generate_fallback_summary(messages, topics, facts)

    def _generate_fallback_summary(
        self, messages: list[dict[str, Any]], topics: list[str], facts: list[str]
    ) -> str:
        """Generate a simple fallback summary"""
        user_message_count = len([msg for msg in messages if msg.get("role") == "user"])
        topic_text = ", ".join(topics[:3]) if topics else "general conversation"

        summary = f"Conversation with {user_message_count} user messages discussing {topic_text}."

        if facts:
            summary += f" Key information: {facts[0]}"

        return summary

    def _generate_summary_id(self, user_id: str, timespan: dict[str, str]) -> str:
        """Generate a unique ID for the summary"""
        content = f"{user_id}_{timespan['start_time']}_{timespan['end_time']}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _cache_summary(self, summary: ConversationSummary):
        """Cache the summary for quick retrieval"""
        self.summary_cache[summary.summary_id] = {"summary": summary, "cached_at": datetime.now()}

        # Clean old cache entries
        cutoff_time = datetime.now() - self.cache_ttl
        to_remove = [
            sid for sid, data in self.summary_cache.items() if data["cached_at"] < cutoff_time
        ]
        for sid in to_remove:
            del self.summary_cache[sid]

    def get_cached_summary(self, summary_id: str) -> ConversationSummary | None:
        """Retrieve a cached summary"""
        if summary_id in self.summary_cache:
            cached_data = self.summary_cache[summary_id]
            if datetime.now() - cached_data["cached_at"] < self.cache_ttl:
                return cached_data["summary"]
            else:
                del self.summary_cache[summary_id]
        return None

    async def summarize_if_needed(
        self, user_id: str, messages: list[dict[str, Any]]
    ) -> ConversationSummary | None:
        """
        Check if summarization is needed and create summary if so
        """
        if await self.should_summarize_conversation(user_id, messages):
            return await self.create_conversation_summary(user_id, messages)
        return None

    def get_summary_stats(self) -> dict[str, Any]:
        """Get statistics about summarization performance"""
        return {
            "cached_summaries": len(self.summary_cache),
            "cache_hit_rate": getattr(self, "_cache_hits", 0)
            / max(getattr(self, "_cache_requests", 1), 1),
            "avg_compression_ratio": self.target_compression_ratio,
            "min_messages_threshold": self.min_messages_for_summary,
        }
