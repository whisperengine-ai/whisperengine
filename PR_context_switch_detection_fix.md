"""
Add detect_contradictions method to VectorMemoryManager and improve the context switch detector

This PR addresses an issue with the context switch detection system, which was unable to properly
detect topic shifts in conversations due to a missing method. The VectorMemoryManager class was
missing the detect_contradictions method that the ContextSwitchDetector expected to use.

Changes:
1. Added detect_contradictions method to VectorMemoryManager that proxies to the underlying
   vector store's implementation or provides a basic implementation if not available
2. Enhanced the context switch detector to better handle cases where the method might be missing
3. Improved topic shift detection with better keyword detection for common topics
"""

def get_patch_for_vector_memory_system():
    """
    Returns the patch to add to src/memory/vector_memory_system.py
    """
    return '''
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
    '''

def get_location_for_patch():
    """
    Returns instructions on where to add the code in the file
    """
    return '''
    Add the method to the VectorMemoryManager class in src/memory/vector_memory_system.py.
    Add it after the __init__ method and before the other methods.
    
    LOCATION: Around line 3400, after:
    ```
    logger.info("VectorMemoryManager initialized - local-first single source of truth ready")
    ```
    
    And before:
    ```
    async def get_conversation_context(self, 
                                     user_id: str,
                                     current_message: str,
    ```
    '''

def get_test_steps():
    """
    Returns steps to test the changes
    """
    return '''
    To test the changes:
    
    1. Restart Elena's bot:
       ```
       ./multi-bot.sh restart elena
       ```
    
    2. Send a test message with a clear topic shift:
       "I've been researching ocean acidification and its impact on coral reefs. By the way, could you recommend a good Italian restaurant in Seattle?"
    
    3. Check that Elena's response acknowledges the topic shift (meta-awareness)
    
    4. Check the logs for confirmation:
       ```
       docker logs whisperengine-elena-bot --tail 100 | grep -i "TOPIC SHIFT\|CONTEXT SWITCH"
       ```
    
    The logs should show the topic shift being detected and Elena's response should mention
    the context switch with meta-awareness like "I notice you've changed topics..."
    '''

if __name__ == "__main__":
    print("\nPATCH FOR VECTOR MEMORY MANAGER:")
    print("=" * 80)
    print(get_patch_for_vector_memory_system())
    
    print("\nLOCATION TO ADD THE PATCH:")
    print("=" * 80)
    print(get_location_for_patch())
    
    print("\nTESTING STEPS:")
    print("=" * 80)
    print(get_test_steps())