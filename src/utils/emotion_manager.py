"""
Emotion and Relationship State Management System

This module implements dynamic emotional and relationship awareness for the chatbot,
using a two-tier emotion analysis system:

1. Phase 2 Predictive Emotional Intelligence (Primary):
   - Sophisticated AI-powered emotional analysis with multi-dimensional assessment
   - Mood detection, stress analysis, and emotional prediction
   - Always attempted first for comprehensive emotional understanding

2. LLM-based Sentiment Analysis (Fallback):
   - Simple emotion detection using configured LLM model
   - JSON-structured prompts for consistent classification
   - Used only when Phase 2 fails due to runtime errors

The system ensures reliable emotion analysis while prioritizing sophisticated AI capabilities.
"""

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class EmotionalState(Enum):
    """Define the possible emotional states"""

    NEUTRAL = "neutral"
    HAPPY = "happy"
    EXCITED = "excited"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"
    SAD = "sad"
    DISAPPOINTED = "disappointed"
    CURIOUS = "curious"
    WORRIED = "worried"
    GRATEFUL = "grateful"


class RelationshipLevel(Enum):
    """Define the possible relationship levels"""

    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    FRIEND = "friend"
    CLOSE_FRIEND = "close_friend"


@dataclass
class EmotionProfile:
    """Represents the emotional context of a user interaction"""

    detected_emotion: EmotionalState
    confidence: float
    triggers: list[str]  # Words/phrases that triggered this emotion
    intensity: float  # 0.0 to 1.0
    timestamp: datetime


@dataclass
class UserProfile:
    """Complete user profile with emotional and relationship state"""

    user_id: str
    name: str | None = None
    relationship_level: RelationshipLevel = RelationshipLevel.STRANGER
    current_emotion: EmotionalState = EmotionalState.NEUTRAL
    interaction_count: int = 0
    first_interaction: datetime | None = None
    last_interaction: datetime | None = None
    emotion_history: list[EmotionProfile] | None = None
    escalation_count: int = 0  # Count of negative emotional episodes
    trust_indicators: list[str] | None = None  # Things that indicate growing trust

    def __post_init__(self):
        if self.emotion_history is None:
            self.emotion_history = []
        if self.trust_indicators is None:
            self.trust_indicators = []


class SentimentAnalyzer:
    """
    LLM-based emotion analysis for fallback scenarios

    This analyzer provides simple but reliable emotion detection using the configured
    LLM model when Phase 2 Predictive Emotional Intelligence fails. It uses structured
    JSON prompts to classify emotions into 10 core emotional states with confidence scores.
    """

    def __init__(self, llm_client=None):
        """Initialize with LLM client for emotion detection"""
        self.llm_client = llm_client

    def analyze_emotion(self, message: str) -> EmotionProfile:
        """
        Analyze emotion using LLM client as fallback when Phase 2 fails

        This method provides reliable emotion detection using the configured LLM model
        with structured JSON prompts. It's designed as a fallback for when the primary
        Phase 2 Predictive Emotional Intelligence system encounters runtime errors.
        """

        if self.llm_client:
            try:
                logger.debug("Using LLM client for fallback emotion analysis")

                # Use a simple emotion analysis prompt
                prompt = f"""Analyze the emotion in this message and respond with JSON only:

Message: "{message}"

Respond with exactly this format:
{{
  "emotion": "happy|sad|angry|excited|frustrated|worried|grateful|curious|disappointed|neutral",
  "confidence": 0.0-1.0,
  "intensity": 0.0-1.0,
  "triggers": ["word1", "word2"]
}}"""

                messages = [{"role": "user", "content": prompt}]

                # Use emotion-specific endpoint if available, otherwise main endpoint
                if (
                    hasattr(self.llm_client, "generate_emotion_chat_completion")
                    and self.llm_client.emotion_chat_endpoint
                ):
                    response = self.llm_client.generate_emotion_chat_completion(
                        messages=messages,
                        temperature=0.1,
                        max_tokens=self.llm_client.max_tokens_emotion,
                    )
                else:
                    response = self.llm_client.generate_chat_completion(
                        messages=messages,
                        temperature=0.1,
                        max_tokens=self.llm_client.max_tokens_emotion,  # Use emotion limit even on main endpoint
                    )

                content = response["choices"][0]["message"]["content"].strip()

                # Parse JSON response
                import json

                if content.startswith("{") and content.endswith("}"):
                    emotion_data = json.loads(content)
                else:
                    # Try to extract JSON from the response
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    if start >= 0 and end > start:
                        emotion_data = json.loads(content[start:end])
                    else:
                        raise ValueError("No valid JSON found in response")

                # Map emotion string to EmotionalState enum
                emotion_mapping = {
                    "happy": EmotionalState.HAPPY,
                    "sad": EmotionalState.SAD,
                    "angry": EmotionalState.ANGRY,
                    "excited": EmotionalState.EXCITED,
                    "frustrated": EmotionalState.FRUSTRATED,
                    "worried": EmotionalState.WORRIED,
                    "grateful": EmotionalState.GRATEFUL,
                    "curious": EmotionalState.CURIOUS,
                    "disappointed": EmotionalState.DISAPPOINTED,
                    "neutral": EmotionalState.NEUTRAL,
                }

                detected_emotion = emotion_mapping.get(
                    emotion_data.get("emotion", "neutral").lower(), EmotionalState.NEUTRAL
                )

                confidence = float(emotion_data.get("confidence", 0.5))
                intensity = float(emotion_data.get("intensity", 0.5))
                triggers = emotion_data.get("triggers", [])

                # Ensure triggers is a list of strings
                if not isinstance(triggers, list):
                    triggers = []
                triggers = [str(t) for t in triggers if t][:5]  # Limit to 5 triggers

                logger.debug(
                    f"LLM emotion analysis: {detected_emotion.value} (confidence: {confidence:.2f})"
                )

                return EmotionProfile(
                    detected_emotion=detected_emotion,
                    confidence=confidence,
                    triggers=triggers,
                    intensity=intensity,
                    timestamp=datetime.now(),
                )

            except Exception as e:
                logger.warning(f"LLM emotion analysis failed: {e}")
                # Fall through to neutral fallback

        # Final safety fallback - return neutral with low confidence
        # This ensures the system never crashes due to emotion analysis failures
        logger.debug("Using neutral safety fallback for emotion analysis")
        return EmotionProfile(
            detected_emotion=EmotionalState.NEUTRAL,
            confidence=0.1,  # Low confidence since we couldn't analyze
            triggers=["analysis_failed"],
            intensity=0.0,
            timestamp=datetime.now(),
        )


class RelationshipManager:
    """Manages relationship progression based on user interactions"""

    def __init__(self, llm_client=None, memory_manager=None):
        """
        Initialize relationship progression rules with LLM support

        Args:
            llm_client: LLMClient instance for LLM-based analysis
            memory_manager: Reference to memory manager for accessing user facts
        """
        self.llm_client = llm_client
        self.memory_manager = memory_manager

        self.relationship_rules = {
            RelationshipLevel.STRANGER: {
                "interaction_threshold": 0,
                "requirements": [],
                "progression_to": RelationshipLevel.ACQUAINTANCE,
            },
            RelationshipLevel.ACQUAINTANCE: {
                "interaction_threshold": 3,
                "requirements": ["multiple_interactions"],
                "progression_to": RelationshipLevel.FRIEND,
            },
            RelationshipLevel.FRIEND: {
                "interaction_threshold": 10,
                "requirements": ["name_shared", "personal_info"],
                "progression_to": RelationshipLevel.CLOSE_FRIEND,
            },
            RelationshipLevel.CLOSE_FRIEND: {
                "interaction_threshold": 25,
                "requirements": ["deep_conversation", "trust_indicators"],
                "progression_to": None,  # Max level
            },
        }

    def detect_personal_info(self, message: str) -> dict[str, list[str]]:
        """Detect personal information sharing in a message using LLM"""
        if not self.llm_client:
            logger.warning("No LLM client available for personal info detection")
            return {}

        try:
            logger.debug("Using LLM for personal info detection")
            result = self.llm_client.extract_personal_info(message)

            if not isinstance(result, dict) or "personal_info" not in result:
                logger.warning("Invalid LLM response for personal info detection")
                return {}

            personal_info = result["personal_info"]

            # Convert to expected format
            detected_info = {}
            for info_type, items in personal_info.items():
                if isinstance(items, list) and items:
                    # Filter out empty strings and ensure items are strings
                    filtered_items = []
                    for item in items:
                        if item and isinstance(item, str) and item.strip():
                            filtered_items.append(item.strip())
                        elif item and not isinstance(item, str):
                            # Convert non-string items to strings
                            item_str = str(item).strip()
                            if item_str:
                                filtered_items.append(item_str)

                    if filtered_items:
                        detected_info[info_type] = filtered_items

            if detected_info:
                logger.debug(f"LLM detected personal info types: {list(detected_info.keys())}")

            return detected_info

        except (ConnectionError, TimeoutError, ConnectionRefusedError) as e:
            logger.warning(
                f"LLM connection failed for personal info detection, returning empty dict: {e}"
            )
            return {}
        except AttributeError as e:
            if "has no attribute" in str(e) and "extract_personal_info" in str(e):
                logger.warning(f"LLM client missing extract_personal_info method: {e}")
                return {}
            else:
                logger.error(f"LLM personal info detection failed with AttributeError: {e}")
                raise e
        except Exception as e:
            # For other exceptions (API errors, rate limits, etc.), re-raise them
            logger.error(f"Error in LLM personal info detection: {e}")
            raise e

    def detect_trust_indicators(self, message: str) -> list[str]:
        """
        DEPRECATED: Trust detection is now handled by Phase 4 Dynamic Personality Profiler
        
        This method returns empty list as trust analysis is done more comprehensively
        in the personality profiler with relationship depth, conversation patterns,
        and evidence-based trait tracking.
        """
        return []

    def should_progress_relationship(self, profile: UserProfile) -> bool:
        """Determine if relationship should progress to next level"""
        current_level = profile.relationship_level

        if current_level == RelationshipLevel.CLOSE_FRIEND:
            return False  # Already at max level

        rules = self.relationship_rules[current_level]

        # Check interaction threshold
        if profile.interaction_count < rules["interaction_threshold"]:
            return False

        # Check specific requirements
        requirements = rules["requirements"]

        if "multiple_interactions" in requirements:
            if profile.interaction_count < 3:
                return False

        if "name_shared" in requirements:
            if not profile.name:
                return False

        if "personal_info" in requirements:
            # Check if user has shared personal info via memory system
            if self.memory_manager:
                try:
                    # Query memory manager for user facts
                    memories = self.memory_manager.retrieve_relevant_memories(
                        profile.user_id, "facts about user", limit=5
                    )
                    user_facts = [
                        m for m in memories if m.get("metadata", {}).get("type") == "user_fact"
                    ]
                    if len(user_facts) < 2:  # Need at least 2 facts for personal info requirement
                        return False
                except Exception:
                    return False  # Can't access memory system
            else:
                return False  # No memory system available

        if "deep_conversation" in requirements:
            if profile.interaction_count < 10:
                return False
            # Could add more sophisticated deep conversation detection

        if "trust_indicators" in requirements:
            if not profile.trust_indicators or len(profile.trust_indicators) < 2:
                return False

        return True

    def get_next_relationship_level(
        self, current_level: RelationshipLevel
    ) -> RelationshipLevel | None:
        """Get the next relationship level"""
        if current_level in self.relationship_rules:
            return self.relationship_rules[current_level]["progression_to"]
        return None


class EmotionManager:
    """Main manager for emotion and relationship state"""

    def __init__(
        self,
        llm_client=None,
        memory_manager=None,
        use_database: bool = True,
        postgres_pool=None,
        phase2_integration=None,
    ):
        """Initialize the emotion manager"""
        self.use_database = use_database
        self.postgres_pool = postgres_pool  # Store reference to shared connection pool
        self.sentiment_analyzer = SentimentAnalyzer(llm_client=llm_client)
        self.relationship_manager = RelationshipManager(
            llm_client=llm_client, memory_manager=memory_manager
        )
        self.user_profiles: dict[str, UserProfile] = {}
        self.memory_manager = memory_manager  # Reference to memory system for user facts
        self.phase2_integration = (
            phase2_integration  # Phase 2 Predictive Emotional Intelligence system
        )

        # Thread safety for concurrent operations
        self._save_lock = threading.RLock()
        self._auto_save_timer = None
        self._auto_save_interval = 300  # 5 minutes
        self._last_save = time.time()
        self._unsaved_changes = False

        # Save batching to reduce database load
        self._pending_saves = set()  # Set of user_ids that need saving
        self._save_batch_size = 10
        self._last_batch_save = time.time()
        self._save_debounce_delay = 5.0  # Wait 5 seconds before saving after changes

        # Initialize database connection if using database
        if self.use_database:
            # Check if PostgreSQL is actually enabled before attempting to use it
            import os  # Import os here for environment variable access

            use_postgresql = os.getenv("USE_POSTGRESQL", "true").lower() == "true"
            if not use_postgresql:
                logger.info("PostgreSQL is disabled, using SQLite database for emotion profiles")
                try:
                    # Use SQLite database as fallback
                    from src.utils.user_profile_db import UserProfileDatabase

                    self.database = UserProfileDatabase()
                    self.database.init_database()  # Initialize SQLite schema
                    logger.info("Using SQLite database for user profiles")
                    self.is_async_db = False
                except (ImportError, Exception) as e:
                    logger.error(f"SQLite database not available: {e}")
                    logger.info("Falling back to memory-only emotion profiles")
                    self.database = None
                    self.is_async_db = False
            else:
                try:
                    # Use synchronous PostgreSQL database to avoid event loop conflicts
                    from src.utils.sync_postgresql_user_db import SyncPostgreSQLUserDB

                    # Initialize synchronous PostgreSQL database
                    self.database = SyncPostgreSQLUserDB()
                    logger.info("Using synchronous PostgreSQL database for user profiles")
                    self.is_async_db = False

                except (ImportError, Exception) as e:
                    logger.error(f"Synchronous PostgreSQL database not available: {e}")
                    # Fallback to async PostgreSQL if sync version fails
                    try:
                        from src.utils.postgresql_user_db import PostgreSQLUserDB

                        self.database = PostgreSQLUserDB()
                        if self.postgres_pool:
                            self.database.pool = self.postgres_pool
                            logger.info("Using shared PostgreSQL connection pool for user profiles")
                        else:
                            logger.info(
                                "Using PostgreSQL database for user profiles (will initialize pool)"
                            )
                        self.is_async_db = True
                    except (ImportError, Exception) as e2:
                        logger.error(f"PostgreSQL database not available: {e2}")
                        logger.info("Falling back to SQLite database for emotion profiles")
                        try:
                            # Fallback to SQLite database
                            from src.utils.user_profile_db import UserProfileDatabase

                            self.database = UserProfileDatabase()
                            self.database.init_database()  # Initialize SQLite schema
                            logger.info("Using SQLite database as fallback for user profiles")
                            self.is_async_db = False
                        except (ImportError, Exception) as e3:
                            logger.error(f"SQLite database also not available: {e3}")
                            logger.info("Falling back to memory-only emotion profiles")
                            self.database = None
                            self.is_async_db = False
        else:
            self.database = None
            self.is_async_db = False

        self.load_profiles()
        self._start_auto_save()

        logger.info(
            f"EmotionManager initialized with {'LLM-based' if llm_client else 'pattern-based'} sentiment analysis"
        )

    def set_postgres_pool(self, postgres_pool):
        """Set the PostgreSQL connection pool after initialization"""
        if self.use_database and self.database:
            self.database.pool = postgres_pool
            self.postgres_pool = postgres_pool
            logger.info("PostgreSQL connection pool set for EmotionManager")

    async def _analyze_emotion_with_phase2(self, message: str, user_id: str) -> EmotionProfile:
        """Analyze emotion using Phase 2 Predictive Emotional Intelligence system"""
        try:
            # Use Phase 2 Predictive Emotional Intelligence system
            conversation_context = {
                "topic": "general",
                "communication_style": "casual",
                "user_id": user_id,
                "message_length": len(message),
                "timestamp": datetime.now().isoformat(),
                "context": "emotion_analysis",
            }

            result = await self.phase2_integration.process_message_with_emotional_intelligence(
                user_id=user_id, message=message, conversation_context=conversation_context
            )

            # Extract emotional intelligence assessment from result
            ei_data = result.get("emotional_intelligence", {})
            assessment = ei_data.get("assessment")

            if assessment:
                # Convert Phase 2 assessment to EmotionProfile format
                mood_category = assessment.mood_assessment.mood_category.value
                predicted_emotion = assessment.emotional_prediction.predicted_emotion
                confidence = assessment.confidence_score

                # Map mood/emotion to our EmotionalState enum
                emotion_mapping = {
                    "very_positive": EmotionalState.HAPPY,
                    "positive": EmotionalState.HAPPY,
                    "neutral": EmotionalState.NEUTRAL,
                    "negative": EmotionalState.SAD,
                    "very_negative": EmotionalState.SAD,
                    "joy": EmotionalState.HAPPY,
                    "happiness": EmotionalState.HAPPY,
                    "excited": EmotionalState.EXCITED,
                    "excitement": EmotionalState.EXCITED,
                    "angry": EmotionalState.ANGRY,
                    "anger": EmotionalState.ANGRY,
                    "frustrated": EmotionalState.FRUSTRATED,
                    "frustration": EmotionalState.FRUSTRATED,
                    "sad": EmotionalState.SAD,
                    "sadness": EmotionalState.SAD,
                    "disappointed": EmotionalState.DISAPPOINTED,
                    "disappointment": EmotionalState.DISAPPOINTED,
                    "curious": EmotionalState.CURIOUS,
                    "curiosity": EmotionalState.CURIOUS,
                    "worried": EmotionalState.WORRIED,
                    "worry": EmotionalState.WORRIED,
                    "grateful": EmotionalState.GRATEFUL,
                    "gratitude": EmotionalState.GRATEFUL,
                }

                # Try to map predicted emotion first, then mood category
                detected_emotion = emotion_mapping.get(
                    predicted_emotion.lower(),
                    emotion_mapping.get(mood_category.lower(), EmotionalState.NEUTRAL),
                )

                # Extract triggers from assessment
                triggers = []
                if hasattr(assessment.mood_assessment, "evidence_keywords"):
                    triggers.extend(assessment.mood_assessment.evidence_keywords)
                if hasattr(assessment.stress_assessment, "indicators"):
                    triggers.extend(assessment.stress_assessment.indicators)
                if not triggers:
                    triggers = [predicted_emotion, mood_category]  # Fallback

                # Use stress level as intensity
                stress_level = assessment.stress_assessment.stress_level.value
                intensity_mapping = {
                    "none": 0.1,
                    "low": 0.3,
                    "moderate": 0.5,
                    "high": 0.7,
                    "severe": 0.9,
                }
                intensity = intensity_mapping.get(stress_level, confidence)

                # Ensure intensity is never None
                if intensity is None:
                    intensity = 0.5  # Default fallback value

                logger.debug(
                    f"Phase 2 emotion analysis: {detected_emotion.value} "
                    f"(mood: {mood_category}, prediction: {predicted_emotion}, "
                    f"confidence: {confidence:.2f})"
                )

                return EmotionProfile(
                    detected_emotion=detected_emotion,
                    confidence=confidence,
                    triggers=triggers[:5],  # Limit triggers for readability
                    intensity=intensity,
                    timestamp=datetime.now(),
                )

        except Exception as e:
            logger.warning(f"Phase 2 emotion analysis failed, falling back to LLM: {e}")
            # Fallback to LLM-based sentiment analysis
            return self.sentiment_analyzer.analyze_emotion(message)

    def load_profiles(self):
        """Load user profiles from persistent storage"""
        if self.use_database and self.database:
            try:
                # Initialize database if needed (only for PostgreSQL databases with pools)
                if (
                    hasattr(self.database, "initialize")
                    and hasattr(self.database, "pool")
                    and (not hasattr(self.database, "pool") or not self.database.pool)
                ):
                    if self.is_async_db:
                        # For async database, we need to initialize it properly
                        import asyncio

                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                # Skip initialization if loop is running - will be initialized on first use
                                logger.info("Async database initialization deferred")
                                self.user_profiles = {}
                                return
                        except RuntimeError:
                            pass
                        # Initialize in new event loop
                        if self.database and hasattr(self.database, "initialize"):
                            asyncio.run(self.database.initialize())
                    else:
                        # For sync database, initialize directly
                        self.database.initialize()

                # Load all profiles from database
                profiles_dict = self.database.load_all_profiles()
                self.user_profiles = profiles_dict
                logger.info(f"Loaded {len(self.user_profiles)} user profiles from database")
                return
            except Exception as e:
                logger.error(f"Error loading profiles from database: {e}")
                logger.error("Database load failed - starting with empty profiles")
                self.user_profiles = {}  # Start with empty profiles
        else:
            logger.warning("Database not configured - starting with empty user profiles")
            self.user_profiles = {}

    def _start_auto_save(self):
        """Start periodic auto-save timer"""
        if self._auto_save_timer:
            self._auto_save_timer.cancel()

        self._auto_save_timer = threading.Timer(self._auto_save_interval, self._periodic_save)
        self._auto_save_timer.daemon = True  # Don't prevent shutdown
        self._auto_save_timer.start()
        logger.debug(f"Auto-save timer started with {self._auto_save_interval}s interval")

    def _periodic_save(self):
        """Periodic save with error handling"""
        try:
            if self._unsaved_changes:
                logger.debug("Auto-saving emotion profiles...")
                self.save_profiles()
                self._unsaved_changes = False
                logger.debug("Auto-save completed")
        except Exception as e:
            logger.error(f"Auto-save failed: {e}")
        finally:
            # Schedule next auto-save
            self._start_auto_save()

    def _mark_unsaved_changes(self, user_id: str | None = None):
        """Mark that there are unsaved changes, optionally for a specific user"""
        self._unsaved_changes = True
        if user_id:
            self._pending_saves.add(user_id)

    def save_profiles(self):
        """Thread-safe profile saving with proper database handling"""
        with self._save_lock:
            if self.use_database and self.database:
                try:
                    # Determine profiles to save
                    if self._pending_saves:
                        profiles_to_save = {
                            user_id: self.user_profiles[user_id]
                            for user_id in self._pending_saves
                            if user_id in self.user_profiles
                        }
                    else:
                        # Save all profiles
                        profiles_to_save = self.user_profiles.copy()

                    if not profiles_to_save:
                        logger.debug("No profiles to save")
                        return

                    # Use appropriate save method based on database type
                    if self.is_async_db:
                        # Use thread-based approach for async database
                        saved_count = self._save_async_database(profiles_to_save)
                    else:
                        # Use direct approach for sync database
                        saved_count = self._save_sync_database(profiles_to_save)

                    if saved_count > 0:
                        logger.debug(f"Saved {saved_count} profiles to database")
                        self._last_save = time.time()
                        self._last_batch_save = time.time()
                        self._unsaved_changes = False
                        self._pending_saves.clear()
                    else:
                        logger.warning("No profiles were saved to database")

                except Exception as e:
                    logger.error(f"Error saving profiles to database: {e}")
            else:
                logger.error("Database not configured for emotion manager - profiles not saved")

    def _save_sync_database(self, profiles_to_save: dict[str, UserProfile]) -> int:
        """Save profiles using synchronous database"""
        if not self.database:
            return 0

        # Initialize database if needed (only for PostgreSQL databases with pools)
        if hasattr(self.database, "pool") and (
            not hasattr(self.database, "pool") or not self.database.pool
        ):
            self.database.initialize()

        saved_count = 0
        failed_saves = []

        # Save profiles one by one with error recovery
        for user_id, profile in profiles_to_save.items():
            try:
                self.database.save_user_profile(profile)
                saved_count += 1
                # Remove from pending saves on successful save
                self._pending_saves.discard(user_id)
            except Exception as e:
                logger.error(f"Error saving profile for user {user_id}: {e}")
                failed_saves.append(user_id)
                # Add failed saves back to pending for retry
                self._pending_saves.add(user_id)

        if failed_saves:
            logger.warning(f"Failed to save {len(failed_saves)} profiles: {failed_saves}")

        return saved_count

    def _save_async_database(self, profiles_to_save: dict[str, UserProfile]) -> int:
        """Save profiles using async database with thread isolation"""
        import asyncio
        import concurrent.futures

        def _run_save_in_thread():
            """Run the async save operation in a dedicated thread"""
            try:
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self._batch_save_async(profiles_to_save))
                finally:
                    loop.close()
            except Exception as e:
                logger.error(f"Error in thread save operation: {e}")
                return 0

        # Run in a separate thread to avoid event loop conflicts
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_save_in_thread)
            try:
                return future.result(timeout=30)  # 30 second timeout
            except concurrent.futures.TimeoutError:
                logger.error("Save operation timed out after 30 seconds")
                return 0
            except Exception as e:
                logger.error(f"Error in save operation: {e}")
                return 0

    async def _batch_save_async(self, profiles_to_save: dict[str, UserProfile]):
        """Save multiple profiles in a batch with proper error handling"""
        if not self.database:
            return 0

        # Ensure database is initialized and check pool health
        if not self.database.pool:
            try:
                await self.database.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize database pool: {e}")
                return 0

        # Check if pool is still healthy
        if not self.database.pool or self.database.pool.is_closing():
            logger.error("Database pool is not available or closing")
            return 0

        saved_count = 0
        failed_saves = []

        # Save profiles one by one with error recovery
        for user_id, profile in profiles_to_save.items():
            try:
                await self.database.save_user_profile(profile)
                saved_count += 1
                # Remove from pending saves on successful save
                self._pending_saves.discard(user_id)
            except Exception as e:
                logger.error(f"Error saving profile for user {user_id}: {e}")
                failed_saves.append(user_id)
                # Add failed saves back to pending for retry
                self._pending_saves.add(user_id)

        if failed_saves:
            logger.warning(f"Failed to save {len(failed_saves)} profiles: {failed_saves}")

        return saved_count

    async def _save_all_profiles_async(self):
        """Helper method to save all profiles asynchronously and return count"""
        if not self.database:
            return 0

        # Ensure database is initialized
        if not self.database.pool:
            await self.database.initialize()

        saved_count = 0
        for user_id, profile in self.user_profiles.items():
            try:
                await self.database.save_user_profile(profile)
                saved_count += 1
            except Exception as e:
                logger.error(f"Error saving profile for user {user_id}: {e}")

        return saved_count

    async def save_profiles_async(self):
        """Async version of save_profiles for database operations"""
        if self.use_database and self.database:
            try:
                saved_count = await self._save_all_profiles_async()
                if saved_count > 0:
                    logger.debug(f"Saved {saved_count} profiles to database")
                    self._last_save = time.time()
                    self._unsaved_changes = False
                return
            except Exception as e:
                logger.error(f"Error saving profiles to database: {e}")
                logger.error("Async database save failed - no fallback configured")

    def cleanup(self):
        """Clean up resources and save final state"""
        if self._auto_save_timer:
            self._auto_save_timer.cancel()

        # Final save
        if self._unsaved_changes:
            logger.info("Performing final save of emotion profiles...")
            self.save_profiles()

        logger.info("EmotionManager cleanup complete")

    def get_or_create_profile(self, user_id: str, display_name: str | None = None) -> UserProfile:
        """Get existing user profile or create a new one"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(
                user_id=user_id, name=display_name, first_interaction=datetime.now()
            )
            logger.debug(f"Created new user profile for {user_id} (name: {display_name or 'None'})")
        else:
            # Update name if provided and different (allows for Discord name changes)
            existing_profile = self.user_profiles[user_id]
            if display_name and existing_profile.name != display_name:
                logger.debug(
                    f"Updating name for {user_id}: '{existing_profile.name}' -> '{display_name}'"
                )
                existing_profile.name = display_name

        return self.user_profiles[user_id]

    def analyze_and_update_emotion(
        self, user_id: str, message: str, display_name: str | None = None
    ) -> tuple[UserProfile, EmotionProfile]:
        """Analyze emotion and update user state, returning the data for later storage"""
        profile = self.get_or_create_profile(user_id, display_name)

        # Primary: Use Phase 2 Predictive Emotional Intelligence (always available)
        # Fallback: Use LLM-based sentiment analysis only for runtime failures
        import asyncio

        try:
            # Try to get current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we need to handle this differently
                # For now, fall back to LLM system to avoid conflicts
                logger.debug("Event loop running, using LLM emotion analysis fallback")
                emotion_profile = self.sentiment_analyzer.analyze_emotion(message)
            else:
                # Run async Phase 2 emotion analysis
                emotion_profile = loop.run_until_complete(
                    self._analyze_emotion_with_phase2(message, user_id)
                )
        except RuntimeError:
            # No event loop, create one for Phase 2 analysis
            emotion_profile = asyncio.run(self._analyze_emotion_with_phase2(message, user_id))
        except Exception as e:
            logger.warning(f"Phase 2 emotion analysis failed with error: {e}")
            logger.debug("Falling back to LLM-based sentiment analysis")
            emotion_profile = self.sentiment_analyzer.analyze_emotion(message)

        # Update user profile
        profile.interaction_count += 1
        profile.last_interaction = datetime.now()
        profile.current_emotion = emotion_profile.detected_emotion

        # Add to emotion history (keep last 50 emotions)
        if profile.emotion_history is None:
            profile.emotion_history = []
        profile.emotion_history.append(emotion_profile)
        if len(profile.emotion_history) > 50:
            profile.emotion_history = profile.emotion_history[-50:]

        # Note: Trust detection is now handled comprehensively by Phase 4 Dynamic Personality Profiler
        # which tracks trust as a personality dimension with evidence-based confidence scoring
        
        # Ensure trust_indicators exists for backward compatibility but don't populate it
        if profile.trust_indicators is None:
            profile.trust_indicators = []
        elif not isinstance(profile.trust_indicators, list):
            # Handle cases where trust_indicators is a string or other type
            logger.warning(
                f"trust_indicators for user {user_id} is not a list (type: {type(profile.trust_indicators)}), resetting to empty list"
            )
            profile.trust_indicators = []
        # Legacy trust_indicators no longer collected - Phase 4 personality profiler handles this

        # Check for relationship progression
        if self.relationship_manager.should_progress_relationship(profile):
            new_level = self.relationship_manager.get_next_relationship_level(
                profile.relationship_level
            )
            if new_level:
                old_level = profile.relationship_level
                profile.relationship_level = new_level
                logger.info(
                    f"User {user_id} relationship progressed from {old_level.value} to {new_level.value}"
                )

        # Track negative emotion escalation
        if emotion_profile.detected_emotion in [
            EmotionalState.FRUSTRATED,
            EmotionalState.ANGRY,
            EmotionalState.SAD,
            EmotionalState.DISAPPOINTED,
        ]:
            profile.escalation_count += 1
        else:
            # Reset escalation count on positive interactions
            if emotion_profile.detected_emotion in [
                EmotionalState.HAPPY,
                EmotionalState.EXCITED,
                EmotionalState.GRATEFUL,
            ]:
                profile.escalation_count = max(0, profile.escalation_count - 1)

        # Mark changes for auto-save
        self._mark_unsaved_changes(user_id)

        # Save profiles periodically but less frequently to reduce conflicts
        # Save every 50 interactions OR if there are many pending saves
        should_save = (
            profile.interaction_count % 50 == 0
            or len(self._pending_saves) >= self._save_batch_size
            or time.time() - self._last_batch_save > 60
        )  # Or every minute

        if should_save:
            self.save_profiles()

        return profile, emotion_profile

    def process_interaction(
        self, user_id: str, message: str, display_name: str | None = None
    ) -> tuple[UserProfile, EmotionProfile]:
        """Process a user interaction - wrapper for analyze_and_update_emotion"""
        return self.analyze_and_update_emotion(user_id, message, display_name)

    async def analyze_and_update_emotion_async(
        self, user_id: str, message: str, display_name: str | None = None
    ) -> tuple[UserProfile, EmotionProfile]:
        """Async version of analyze_and_update_emotion for use in async contexts"""
        profile = self.get_or_create_profile(user_id, display_name)

        # Analyze emotion using Phase 2 system when available
        emotion_profile = await self._analyze_emotion_with_phase2(message, user_id)

        # Update user profile
        profile.interaction_count += 1
        profile.last_interaction = datetime.now()
        profile.current_emotion = emotion_profile.detected_emotion

        # Add to emotion history (keep last 50 emotions)
        if profile.emotion_history is None:
            profile.emotion_history = []
        profile.emotion_history.append(emotion_profile)
        if len(profile.emotion_history) > 50:
            profile.emotion_history = profile.emotion_history[-50:]

        # Note: Trust detection is now handled comprehensively by Phase 4 Dynamic Personality Profiler
        # which tracks trust as a personality dimension with evidence-based confidence scoring
        
        # Ensure trust_indicators exists for backward compatibility but don't populate it
        if profile.trust_indicators is None:
            profile.trust_indicators = []
        elif not isinstance(profile.trust_indicators, list):
            # Handle cases where trust_indicators is a string or other type
            logger.warning(
                f"trust_indicators for user {user_id} is not a list (type: {type(profile.trust_indicators)}), resetting to empty list"
            )
            profile.trust_indicators = []
        # Legacy trust_indicators no longer collected - Phase 4 personality profiler handles this

        # Check for relationship progression
        if self.relationship_manager.should_progress_relationship(profile):
            new_level = self.relationship_manager.get_next_relationship_level(
                profile.relationship_level
            )
            if new_level:
                old_level = profile.relationship_level
                profile.relationship_level = new_level
                logger.info(
                    f"User {user_id} relationship progressed from {old_level.value} to {new_level.value}"
                )

        # Track negative emotion escalation
        if emotion_profile.detected_emotion in [
            EmotionalState.FRUSTRATED,
            EmotionalState.ANGRY,
            EmotionalState.SAD,
            EmotionalState.DISAPPOINTED,
        ]:
            profile.escalation_count += 1
        else:
            # Reset escalation count on positive interactions
            if emotion_profile.detected_emotion in [
                EmotionalState.HAPPY,
                EmotionalState.EXCITED,
                EmotionalState.GRATEFUL,
            ]:
                profile.escalation_count = max(0, profile.escalation_count - 1)

        # Mark changes for auto-save
        self._mark_unsaved_changes(user_id)

        # Save profiles periodically but less frequently to reduce conflicts
        # Save every 50 interactions OR if there are many pending saves
        should_save = (
            profile.interaction_count % 50 == 0
            or len(self._pending_saves) >= self._save_batch_size
            or time.time() - self._last_batch_save > 60
        )  # Or every minute

        if should_save:
            self.save_profiles()

        return profile, emotion_profile

    async def process_interaction_async(
        self, user_id: str, message: str, display_name: str | None = None
    ) -> tuple[UserProfile, EmotionProfile]:
        """Async version of process_interaction for use in async contexts"""
        return await self.analyze_and_update_emotion_async(user_id, message, display_name)

    def get_emotion_context(self, user_id: str) -> str:
        """Generate emotion and relationship context for the system prompt"""
        if user_id not in self.user_profiles:
            return (
                "User: Stranger, Emotion: Neutral. This is your first interaction with this user."
            )

        profile = self.user_profiles[user_id]

        # Build context string
        context_parts = []

        # Basic info
        name_part = f"({profile.name})" if profile.name else ""
        context_parts.append(f"User: {profile.relationship_level.value.title()} {name_part}")
        context_parts.append(f"Current Emotion: {profile.current_emotion.value.title()}")
        context_parts.append(f"Interactions: {profile.interaction_count}")

        # Relationship-specific context
        if profile.relationship_level == RelationshipLevel.STRANGER:
            context_parts.append("Be polite, formal, and helpful. This is a new user.")
        elif profile.relationship_level == RelationshipLevel.ACQUAINTANCE:
            context_parts.append("Be friendly and remember previous interactions.")
        elif profile.relationship_level == RelationshipLevel.FRIEND:
            context_parts.append(
                f"Be warm and personal. Use their name ({profile.name}) when appropriate."
            )
            # Get user facts from memory manager
            if self.memory_manager:
                try:
                    user_facts = self._get_user_facts_summary(profile.user_id)
                    if user_facts:
                        context_parts.append(f"Known info: {user_facts}")
                except Exception as e:
                    logger.warning(f"Could not retrieve user facts for emotional context: {e}")
        elif profile.relationship_level == RelationshipLevel.CLOSE_FRIEND:
            context_parts.append(
                f"Be very personal, empathetic, and supportive. You know {profile.name} well."
            )
            # Get detailed user facts from memory manager
            if self.memory_manager:
                try:
                    user_facts = self._get_user_facts_summary(profile.user_id, detailed=True)
                    if user_facts:
                        context_parts.append(f"Their background: {user_facts}")
                except Exception as e:
                    logger.warning(f"Could not retrieve user facts for emotional context: {e}")

        # Emotional context
        if profile.current_emotion != EmotionalState.NEUTRAL:
            emotion_guidance = self._get_emotion_response_guidance(profile.current_emotion)
            context_parts.append(emotion_guidance)

        # Escalation warning
        if profile.escalation_count >= 3:
            context_parts.append(
                "WARNING: User has shown repeated negative emotions. Be extra empathetic and consider offering additional help."
            )

        return " | ".join(context_parts)

    def _get_emotion_response_guidance(self, emotion: EmotionalState) -> str:
        """Get guidance on how to respond to specific emotions"""
        guidance = {
            EmotionalState.HAPPY: "Respond with enthusiasm and share in their joy",
            EmotionalState.EXCITED: "Match their excitement and encourage them",
            EmotionalState.FRUSTRATED: "Be patient, empathetic, and solution-focused",
            EmotionalState.ANGRY: "Stay calm, acknowledge their feelings, and de-escalate",
            EmotionalState.SAD: "Be compassionate, offer support, and listen actively",
            EmotionalState.DISAPPOINTED: "Acknowledge their disappointment and offer encouragement",
            EmotionalState.CURIOUS: "Be informative, detailed, and encourage learning",
            EmotionalState.WORRIED: "Be reassuring, practical, and offer concrete help",
            EmotionalState.GRATEFUL: "Accept their gratitude graciously and continue being helpful",
        }

        return guidance.get(emotion, "Respond appropriately to their emotional state")

    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old emotion history and inactive users"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        users_to_remove = []

        for user_id, profile in self.user_profiles.items():
            # Remove old emotion history
            if profile.emotion_history is not None:
                profile.emotion_history = [
                    emotion
                    for emotion in profile.emotion_history
                    if emotion.timestamp > cutoff_date
                ]

            # Mark inactive users for removal
            if profile.last_interaction and profile.last_interaction < cutoff_date:
                if profile.relationship_level == RelationshipLevel.STRANGER:
                    users_to_remove.append(user_id)

        # Remove inactive stranger users
        for user_id in users_to_remove:
            del self.user_profiles[user_id]
            logger.info(f"Removed inactive user profile: {user_id}")

        if users_to_remove:
            self.save_profiles()

    def _get_user_facts_summary(self, user_id: str, detailed: bool = False) -> str:
        """Get a summary of user facts from the memory manager"""
        if not self.memory_manager:
            return ""

        try:
            # Query memory manager for user facts
            # Use a generic query to get user facts
            facts_query = (
                f"facts about user {user_id}" if detailed else f"basic info about user {user_id}"
            )
            memories = self.memory_manager.retrieve_relevant_memories(
                user_id, facts_query, limit=10
            )

            # Extract facts from memories
            facts = []
            for memory in memories:
                metadata = memory.get("metadata", {})
                if metadata.get("type") == "user_fact":
                    fact = metadata.get("fact", "")
                    if fact and len(fact) < 100:  # Keep facts concise for context
                        facts.append(fact)

            # Limit facts for context (prevent overwhelming the LLM)
            max_facts = 5 if detailed else 3
            if facts:
                return ", ".join(facts[:max_facts])

            return ""

        except Exception as e:
            logger.warning(f"Error retrieving user facts for {user_id}: {e}")
            return ""


# Example usage and testing
if __name__ == "__main__":
    # Test the emotion manager
    emotion_manager = EmotionManager(use_database=True)

    # Test user interactions
    test_messages = [
        "Hi there!",
        "My name is Alice and I'm really excited about this project!",
        "I love programming and hiking. I work at Google.",
        "This is frustrating, it's not working at all!",
        "Thank you so much for your help, you're amazing!",
        "I'm worried about my presentation tomorrow. Can you help me prepare?",
    ]

    user_id = "test_user_123"

    for message in test_messages:
        profile, emotion = emotion_manager.process_interaction(user_id, message)
        context = emotion_manager.get_emotion_context(user_id)
