"""
Enhanced Context-Aware Memory Security with Privacy Controls

This module extends the existing context-aware memory security system to include
comprehensive user privacy preferences and consent management.

SECURITY ENHANCEMENT: Addresses "Insufficient Context Boundaries" (CVSS 6.8)
- User consent for cross-context memory sharing
- Granular privacy preference controls
- Context-aware response filtering
- Audit trail for privacy decisions
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from context_aware_memory_security import ContextAwareMemoryManager, MemoryContext
from context_boundaries_security import get_context_boundaries_manager, ConsentStatus

logger = logging.getLogger(__name__)


class EnhancedContextAwareMemoryManager(ContextAwareMemoryManager):
    """
    Enhanced memory manager with comprehensive privacy controls and user consent
    """

    def __init__(self, base_memory_manager):
        """Initialize enhanced context-aware memory manager"""
        super().__init__(base_memory_manager)
        self.boundaries_manager = get_context_boundaries_manager()
        logger.info("Enhanced context-aware memory manager with privacy controls initialized")

    def retrieve_context_aware_memories(
        self, user_id: str, query: str, context: MemoryContext, limit: int = 10
    ) -> List[Dict]:
        """
        Enhanced memory retrieval with privacy controls and consent management

        Args:
            user_id: User ID
            query: Search query
            context: Current memory context
            limit: Maximum number of memories to retrieve

        Returns:
            List of memories filtered by context security AND user privacy preferences
        """
        try:
            # Get all potentially relevant memories from base system
            all_memories = self.base_memory_manager.retrieve_relevant_memories(
                user_id, query, limit * 3
            )

            if not all_memories:
                return []

            # Get compatible contexts based on base security rules
            compatible_contexts = self.get_compatible_contexts(context)
            filtered_memories = []
            consent_requests = []

            for memory in all_memories:
                memory_context = self._get_memory_context(memory)

                # First check: Base context compatibility (existing security)
                if not self._is_context_compatible(memory_context, context, compatible_contexts):
                    continue

                # Second check: User privacy preferences and consent
                permission_result = self._check_user_privacy_permission(
                    user_id, memory_context, context, memory
                )

                if permission_result["allowed"]:
                    # Memory is allowed - add to results
                    memory["metadata"]["privacy_checked"] = True
                    memory["metadata"]["privacy_reason"] = permission_result["reason"]
                    filtered_memories.append(memory)

                elif permission_result["requires_consent"]:
                    # Memory requires user consent - track for potential consent request
                    consent_requests.append(
                        {
                            "memory": memory,
                            "source_context": memory_context.context_type.value,
                            "target_context": context.context_type.value,
                            "reason": permission_result["reason"],
                        }
                    )

                # If not allowed and doesn't require consent, memory is blocked

                if len(filtered_memories) >= limit:
                    break

            # Log privacy decisions
            logger.debug(
                f"Privacy filtering: {len(all_memories)} -> {len(filtered_memories)} memories allowed, "
                f"{len(consent_requests)} require consent"
            )

            # If we have consent requests, we might want to notify the user
            # (This would be handled at the bot level, not here)
            if consent_requests:
                filtered_memories.append(
                    {
                        "id": "consent_required",
                        "content": f"Additional information is available but requires your permission to share.",
                        "metadata": {
                            "is_consent_request": True,
                            "consent_requests": len(consent_requests),
                            "context_filtered": True,
                        },
                        "relevance_score": 0.0,  # Low relevance so it appears last
                    }
                )

            return filtered_memories

        except Exception as e:
            logger.error(f"Error in enhanced context-aware memory retrieval: {e}")
            # Fallback to base implementation
            return super().retrieve_context_aware_memories(user_id, query, context, limit)

    def _check_user_privacy_permission(
        self,
        user_id: str,
        memory_context: MemoryContext,
        current_context: MemoryContext,
        memory: Dict,
    ) -> Dict[str, Any]:
        """
        Check user privacy preferences for cross-context memory sharing

        Args:
            user_id: User ID
            memory_context: Context where memory was created
            current_context: Current interaction context
            memory: Memory object for sensitivity analysis

        Returns:
            Dict with permission decision
        """
        try:
            # Same context is always allowed
            if (
                memory_context.context_type == current_context.context_type
                and memory_context.server_id == current_context.server_id
                and memory_context.channel_id == current_context.channel_id
            ):
                return {"allowed": True, "reason": "same_context", "requires_consent": False}

            # Analyze memory sensitivity
            memory_sensitivity = self._analyze_memory_sensitivity(memory)

            # Check user's privacy boundaries
            permission = self.boundaries_manager.check_context_boundary_permission(
                user_id=user_id,
                source_context=memory_context.context_type.value,
                target_context=current_context.context_type.value,
                memory_sensitivity=memory_sensitivity,
            )

            return permission

        except Exception as e:
            logger.error(f"Error checking user privacy permission: {e}")
            # Default to requiring consent for safety
            return {"allowed": False, "reason": "error_safety_block", "requires_consent": True}

    def _analyze_memory_sensitivity(self, memory: Dict) -> str:
        """
        Analyze memory content to determine sensitivity level

        Args:
            memory: Memory object

        Returns:
            Sensitivity level: 'low', 'normal', 'high'
        """
        try:
            content = memory.get("content", "").lower()
            metadata = memory.get("metadata", {})

            # High sensitivity indicators
            high_sensitivity_patterns = [
                "health",
                "medical",
                "doctor",
                "medicine",
                "symptoms",
                "diagnosis",
                "password",
                "ssn",
                "social security",
                "credit card",
                "bank account",
                "address",
                "phone number",
                "email",
                "personal",
                "private",
                "confidential",
                "secret",
                "family",
                "relationship",
                "financial",
                "income",
                "salary",
                "money",
                "debt",
                "legal",
                "court",
                "lawyer",
                "lawsuit",
            ]

            # Check content for high sensitivity patterns
            for pattern in high_sensitivity_patterns:
                if pattern in content:
                    return "high"

            # Check if memory was from a private context originally
            if metadata.get("is_private", False):
                return "high"

            # Check if memory contains personal pronouns suggesting personal information
            personal_indicators = [
                "my ",
                "i am",
                "i have",
                "i feel",
                "i think",
                "my family",
                "my job",
            ]
            personal_count = sum(1 for indicator in personal_indicators if indicator in content)

            if personal_count >= 2:
                return "normal"

            return "low"

        except Exception as e:
            logger.warning(f"Error analyzing memory sensitivity, defaulting to high: {e}")
            return "high"  # Default to high sensitivity for safety

    def store_conversation(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        context: Optional[MemoryContext] = None,
        **kwargs,
    ) -> None:
        """
        Enhanced conversation storage with privacy metadata

        Args:
            user_id: User ID
            user_message: User's message
            bot_response: Bot's response
            context: Memory context (if not provided, will try to infer from kwargs)
            **kwargs: Additional arguments passed to base storage method
        """
        try:
            # Get user privacy preferences for storage metadata
            user_prefs = self.boundaries_manager.get_user_preferences(user_id)

            # Enhanced context metadata
            if context:
                privacy_metadata = {
                    "user_privacy_level": user_prefs.privacy_level.value,
                    "consent_status": user_prefs.consent_status.value,
                    "storage_timestamp": user_prefs.updated_timestamp,
                    "privacy_controlled": True,
                }

                # Merge with existing metadata
                if "metadata" in kwargs:
                    kwargs["metadata"].update(privacy_metadata)
                else:
                    kwargs["metadata"] = privacy_metadata

            # Call parent storage method
            return super().store_conversation(
                user_id, user_message, bot_response, context, **kwargs
            )

        except Exception as e:
            logger.error(f"Error in enhanced conversation storage: {e}")
            # Fallback to parent method
            return super().store_conversation(
                user_id, user_message, bot_response, context, **kwargs
            )

    def generate_consent_request_message(
        self, user_id: str, consent_requests: List[Dict]
    ) -> Optional[str]:
        """
        Generate user-friendly consent request message for cross-context sharing

        Args:
            user_id: User ID
            consent_requests: List of memories requiring consent

        Returns:
            Formatted consent request message or None
        """
        try:
            if not consent_requests:
                return None

            count = len(consent_requests)

            # Get unique context transitions
            transitions = set()
            for request in consent_requests:
                source = request["source_context"].replace("_", " ")
                target = request["target_context"].replace("_", " ")
                transitions.add(f"{source} → {target}")

            transition_text = ", ".join(transitions)

            if count == 1:
                message = (
                    f"🔒 **Privacy Notice**: I have information from your {request['source_context'].replace('_', ' ')} "
                    f"that might be relevant here. Would you like me to use it? "
                    f"Use `!privacy_consent allow_once` to allow just this time, or "
                    f"`!privacy_consent allow_always` to always allow {transition_text} sharing."
                )
            else:
                message = (
                    f"🔒 **Privacy Notice**: I have {count} pieces of information from other contexts "
                    f"({transition_text}) that might be relevant here. "
                    f"Use `!privacy_consent allow_once` to allow just this time, or "
                    f"`!privacy_consent allow_always` to update your privacy settings."
                )

            return message

        except Exception as e:
            logger.error(f"Error generating consent request message: {e}")
            return None

    def get_privacy_filtered_context_summary(
        self, user_id: str, context: MemoryContext
    ) -> Dict[str, Any]:
        """
        Get summary of user's information in current context with privacy filtering

        Args:
            user_id: User ID
            context: Current context

        Returns:
            Privacy-filtered context summary
        """
        try:
            # Get user's privacy preferences
            user_prefs = self.boundaries_manager.get_user_preferences(user_id)

            # Get memories allowed in current context
            allowed_memories = self.retrieve_context_aware_memories(
                user_id, "summary", context, limit=20
            )

            # Filter out consent requests from summary
            actual_memories = [
                mem
                for mem in allowed_memories
                if not mem.get("metadata", {}).get("is_consent_request", False)
            ]

            return {
                "user_id": user_id,
                "context_type": context.context_type.value,
                "privacy_level": user_prefs.privacy_level.value,
                "memories_available": len(actual_memories),
                "consent_requests_pending": len(allowed_memories) - len(actual_memories),
                "context_summary": self._generate_context_summary(actual_memories),
            }

        except Exception as e:
            logger.error(f"Error generating privacy-filtered context summary: {e}")
            return {"error": str(e), "user_id": user_id, "memories_available": 0}

    def _generate_context_summary(self, memories: List[Dict]) -> str:
        """Generate a brief summary of available memories"""
        if not memories:
            return "No previous context available."

        # Simple summary based on memory count and types
        memory_types = {}
        for memory in memories:
            metadata = memory.get("metadata", {})
            context_type = metadata.get("context_type", "unknown")
            memory_types[context_type] = memory_types.get(context_type, 0) + 1

        summary_parts = []
        for context_type, count in memory_types.items():
            readable_type = context_type.replace("_", " ").title()
            summary_parts.append(f"{count} {readable_type} memories")

        return f"Available context: {', '.join(summary_parts)}"


def get_enhanced_context_aware_memory_manager(
    base_memory_manager,
) -> EnhancedContextAwareMemoryManager:
    """Get singleton instance of enhanced context-aware memory manager"""
    if not hasattr(get_enhanced_context_aware_memory_manager, "_instance"):
        get_enhanced_context_aware_memory_manager._instance = EnhancedContextAwareMemoryManager(
            base_memory_manager
        )
    return get_enhanced_context_aware_memory_manager._instance
