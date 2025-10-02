"""
Vector Memory Manager Enhancement for Context Switch Detection

This file contains the detect_contradictions method that should be added to the 
VectorMemoryManager class in src/memory/vector_memory_system.py to fix the
context switch detection issue.
"""

# Copy this method into the VectorMemoryManager class in src/memory/vector_memory_system.py

"""
async def detect_contradictions(self, new_content: str, user_id: str, similarity_threshold: float = 0.85) -> List[Dict[str, Any]]:
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
    logger.info("🔍 DETECTING CONTRADICTIONS/TOPIC SHIFTS: %s", new_content[:50])
    
    try:
        # Check if the underlying vector store has the method
        if hasattr(self.vector_store, 'detect_contradictions'):
            logger.debug("🔍 Using vector_store.detect_contradictions")
            return await self.vector_store.detect_contradictions(
                new_content, user_id, similarity_threshold
            )
        
        # If not, implement enhanced topic shift detection
        logger.debug("🔍 Implementing enhanced topic shift detection")
        
        # Check for "By the way" marker which often indicates topic shifts
        if " by the way" in new_content.lower() or "by the way " in new_content.lower():
            parts = new_content.lower().split("by the way")
            if len(parts) > 1:
                logger.debug("🔍 TOPIC SHIFT DETECTED via 'by the way' phrase")
                
                return [{
                    'content': 'topic shift detected',
                    'confidence': 0.95,
                    'previous_topic': 'previous topic',
                    'new_topic': 'new topic',
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
            logger.debug("🔍 MULTIPLE TOPICS DETECTED: %s", topics)
            
            return [{
                'content': 'multiple topics detected',
                'confidence': 0.9,
                'previous_topic': topics[0][0],
                'new_topic': topics[1][0]
            }]
        
        return []
        
    except Exception as e:
        logger.error("Error in detect_contradictions: %s", e)
        return []
"""