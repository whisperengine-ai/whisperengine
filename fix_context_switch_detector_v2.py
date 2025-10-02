"""
Fix for context switch detection in WhisperEngine
"""

import logging
import os
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_vector_memory_manager_fix():
    """
    Applies the fix to the VectorMemoryManager class by adding the detect_contradictions method.
    
    This method adds the missing method needed for proper topic shift detection in the
    context_switch_detector.py file.
    """
    try:
        # Import the module and class
        from src.memory.vector_memory_system import VectorMemoryManager
        
        # Check if the method already exists
        if hasattr(VectorMemoryManager, 'detect_contradictions'):
            logger.info("detect_contradictions method already exists, no fix needed")
            return
        
        logger.info("Adding detect_contradictions method to VectorMemoryManager")
        
        # Add the method to the class
        async def detect_contradictions(self, new_content: str, user_id: str, similarity_threshold: float = 0.85):
            """
            Proxy method to call the underlying vector store's detect_contradictions if it exists
            or implement enhanced topic shift detection if not.
            
            Args:
                new_content: The new message content to check for contradictions/topic shifts
                user_id: The user ID
                similarity_threshold: Threshold for semantic similarity
                
            Returns:
                List of contradiction dictionaries
            """
            logger.info("🔍🔍🔍 DETECTING CONTRADICTIONS/TOPIC SHIFTS: %s", new_content[:50])
            
            try:
                # Check if the underlying vector store has the method
                if hasattr(self.vector_store, 'detect_contradictions'):
                    logger.info("🔍 Using vector_store.detect_contradictions")
                    return await self.vector_store.detect_contradictions(
                        new_content, user_id, similarity_threshold
                    )
                
                # If not, implement enhanced topic shift detection
                logger.info("🔍 Implementing enhanced topic shift detection")
                
                # Check for "By the way" marker which often indicates topic shifts
                if " by the way" in new_content.lower() or "by the way " in new_content.lower():
                    parts = new_content.lower().split("by the way")
                    if len(parts) > 1:
                        # Extract topics from before and after "by the way"
                        topic_before = self._extract_primary_topic(parts[0]) if hasattr(self, '_extract_primary_topic') else "previous topic"
                        topic_after = self._extract_primary_topic(parts[1]) if hasattr(self, '_extract_primary_topic') else "new topic"
                        
                        logger.info(f"🔍 TOPIC SHIFT DETECTED: '{topic_before}' -> '{topic_after}'")
                        
                        return [{
                            'content': 'topic shift detected',
                            'confidence': 0.95,
                            'previous_topic': topic_before,
                            'new_topic': topic_after,
                            'transition_phrase': 'by the way'
                        }]
                
                # Check for multiple distinct topics using keyword analysis
                marine_keywords = ["ocean", "marine", "coral", "reef", "sea", "fish", "water", "aquatic", "ecosystem", "acidification"]
                food_keywords = ["restaurant", "food", "eat", "dinner", "lunch", "cuisine", "meal", "dish", "menu", "chef"]
                tech_keywords = ["computer", "software", "code", "program", "technology", "app", "device", "system", "algorithm"]
                travel_keywords = ["travel", "trip", "vacation", "visit", "destination", "city", "country", "flight", "tour"]
                
                # Count keywords for each topic
                marine_count = sum(1 for keyword in marine_keywords if keyword in new_content.lower())
                food_count = sum(1 for keyword in food_keywords if keyword in new_content.lower())
                tech_count = sum(1 for keyword in tech_keywords if keyword in new_content.lower())
                travel_count = sum(1 for keyword in travel_keywords if keyword in new_content.lower())
                
                # Check for multiple topics
                topics = []
                if marine_count >= 1:
                    topics.append(("marine biology", marine_count))
                if food_count >= 1:
                    topics.append(("food and dining", food_count))
                if tech_count >= 1:
                    topics.append(("technology", tech_count))
                if travel_count >= 1:
                    topics.append(("travel", travel_count))
                
                # If multiple topics with sufficient keywords, report a topic shift
                if len(topics) >= 2:
                    topics.sort(key=lambda x: x[1], reverse=True)
                    logger.info(f"🔍 MULTIPLE TOPICS DETECTED: {topics}")
                    
                    return [{
                        'content': 'multiple topics detected',
                        'confidence': 0.9,
                        'previous_topic': topics[0][0],
                        'new_topic': topics[1][0]
                    }]
                
                return []
                
            except Exception as e:
                logger.error(f"Error in detect_contradictions: {e}")
                return []
        
        # Add the method to the class
        setattr(VectorMemoryManager, 'detect_contradictions', detect_contradictions)
        logger.info("✅ detect_contradictions method added to VectorMemoryManager")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Failed to apply fix: {e}")
        return False

def apply_context_switch_detector_fix():
    """
    Adds code improvement to the context switch detector to directly access vector_store
    if memory_manager doesn't have detect_contradictions.
    """
    try:
        # Import the module and class
        from src.intelligence.context_switch_detector import ContextSwitchDetector
        
        # Original _detect_topic_shift method
        original_detect_topic_shift = ContextSwitchDetector._detect_topic_shift
        
        # Create enhanced version
        async def enhanced_detect_topic_shift(self, user_id, new_message, current_context):
            """Enhanced topic shift detection with better vector store access"""
            logger.info("🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Entered _detect_topic_shift method")
            
            if not self.vector_store:
                logger.info("🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: No vector store available")
                return None
                
            logger.info("🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Vector store is available")
            
            # Extract primary topic from new message
            logger.info(f"🔍🔍🔍 TOPIC EXTRACTION: Analyzing message for topic: '{new_message[:40]}'")
            new_topic = self._extract_primary_topic(new_message)
            logger.info(f"🔍🔍🔍 TOPIC EXTRACTION: Detected topic '{new_topic}' from keywords")
            
            # Compare with current topic
            current_topic = getattr(current_context, 'primary_topic', 'general') if current_context else 'general'
            logger.info(f"🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: New topic detected: '{new_topic}', current topic: '{current_topic}'")
            
            if new_topic == current_topic:
                logger.info("🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Same topic, no shift detected")
                return None
                
            # Use configured threshold
            threshold = self.topic_shift_threshold
            logger.info(f"🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Using threshold value: {threshold}")
            
            # IMPROVED: Check for contradictions using the vector store
            logger.info("🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Starting contradiction detection")
            
            # Try with memory_manager.detect_contradictions
            if hasattr(self.vector_store, 'detect_contradictions'):
                logger.info("🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Vector store has detect_contradictions method")
                logger.info(f"🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Calling detect_contradictions with threshold {threshold}")
                
                contradictions = await self.vector_store.detect_contradictions(
                    new_message, user_id, threshold
                )
                
                logger.info(f"🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Retrieved contradictions for '{new_message[:50]}...': {len(contradictions)} contradictions found")
                
                if contradictions:
                    logger.info(f"🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Found {len(contradictions)} contradictions")
                    
                    # Create topic shift from contradictions
                    highest_confidence = max([c.get('confidence', 0) for c in contradictions])
                    strength = self._determine_strength(highest_confidence)
                    
                    previous_topic = contradictions[0].get('previous_topic', current_topic)
                    new_topic_from_contradictions = contradictions[0].get('new_topic', new_topic)
                    
                    return self._create_topic_shift(
                        user_id, 
                        previous_topic, 
                        new_topic_from_contradictions,
                        strength, 
                        highest_confidence,
                        [c.get('content', '') for c in contradictions]
                    )
                else:
                    logger.info("🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: No contradictions found")
            else:
                logger.info("🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Vector store does NOT have detect_contradictions method")
                
                # ENHANCEMENT: Try to access vector_store through vector_store.vector_store if available
                if hasattr(self.vector_store, 'vector_store') and hasattr(self.vector_store.vector_store, 'detect_contradictions'):
                    logger.info("🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Using nested vector_store.vector_store.detect_contradictions")
                    
                    contradictions = await self.vector_store.vector_store.detect_contradictions(
                        new_message, user_id, threshold
                    )
                    
                    if contradictions:
                        logger.info(f"🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Found {len(contradictions)} contradictions via nested access")
                        
                        # Create topic shift from contradictions
                        highest_confidence = max([c.get('confidence', 0) for c in contradictions])
                        strength = self._determine_strength(highest_confidence)
                        
                        previous_topic = contradictions[0].get('previous_topic', current_topic)
                        new_topic_from_contradictions = contradictions[0].get('new_topic', new_topic)
                        
                        return self._create_topic_shift(
                            user_id, 
                            previous_topic, 
                            new_topic_from_contradictions,
                            strength, 
                            highest_confidence,
                            [c.get('content', '') for c in contradictions]
                        )
            
            # If we don't have any contradictions, fall back to simple topic shift detection
            # Simple topic shift based on topic name change
            topic_difference = self._calculate_topic_difference(current_topic, new_topic)
            if topic_difference > threshold:
                strength = self._determine_strength(topic_difference)
                return self._create_topic_shift(
                    user_id, current_topic, new_topic, strength, topic_difference
                )
                
            return None
        
        # Patch the method
        setattr(ContextSwitchDetector, '_detect_topic_shift', enhanced_detect_topic_shift)
        logger.info("✅ Enhanced _detect_topic_shift method added to ContextSwitchDetector")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to apply context switch detector fix: {e}")
        return False

if __name__ == "__main__":
    # Apply both fixes
    vector_memory_fix = apply_vector_memory_manager_fix()
    context_switch_fix = apply_context_switch_detector_fix()
    
    if vector_memory_fix and context_switch_fix:
        print("\n✅✅✅ FIXES APPLIED SUCCESSFULLY ✅✅✅")
        print("The context switch detection system should now correctly identify topic shifts.")
        print("\nRestart the bot with:")
        print("  ./multi-bot.sh restart elena")
    else:
        print("\n❌ FIXES FAILED TO APPLY ❌")
        print("Check the logs for details.")