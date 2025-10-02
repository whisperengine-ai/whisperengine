#!/usr/bin/env python3
"""
🎯 6-DIMENSIONAL EMBEDDING KEY GENERATION DEMONSTRATION

This script demonstrates how WhisperEngine generates embedding keys/tags for 
each of the 6 dimensions, showing the actual logic used in production.

UPDATED: Now includes the enhanced CDL integration using all 6 dimensions!
"""

import asyncio
import logging
from typing import Dict, List, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmbeddingKeyGenerationDemo:
    """
    Demonstrates the 6-dimensional embedding key generation process
    """
    
    def __init__(self):
        self.setup_extraction_methods()
    
    def setup_extraction_methods(self):
        """Setup extraction method implementations (simplified versions)"""
        pass
    
    def extract_emotional_context(self, content: str) -> Tuple[str, float]:
        """
        Simplified emotion extraction (mirrors WhisperEngine logic)
        Uses keyword analysis as fallback when RoBERTa/VADER unavailable
        """
        content_lower = content.lower()
        
        # Emotion keywords (from WhisperEngine)
        emotion_patterns = {
            "joy": ["happy", "joy", "delighted", "pleased", "cheerful", "elated", "ecstatic", 
                   "thrilled", "excited", "wonderful", "amazing", "fantastic", "great", "awesome"],
            "sadness": ["sad", "unhappy", "depressed", "melancholy", "sorrowful", "grief", 
                       "disappointed", "heartbroken", "down", "blue", "gloomy", "miserable"],
            "anger": ["angry", "mad", "furious", "rage", "irritated", "annoyed", "frustrated", 
                     "outraged", "livid", "incensed", "hostile", "aggressive"],
            "fear": ["afraid", "scared", "frightened", "terrified", "worried", "anxious", 
                    "nervous", "panic", "dread", "horror", "alarmed"],
            "excitement": ["excited", "thrilled", "energetic", "enthusiastic", "pumped", 
                          "eager", "anticipation", "can't wait", "hyped"],
            "gratitude": ["grateful", "thankful", "appreciate", "blessed", "fortunate", 
                         "thank you", "thanks"],
            "curiosity": ["curious", "wondering", "interested", "intrigued", "questioning", 
                         "exploring", "learning", "discovery"],
            "surprise": ["surprised", "shocked", "amazed", "astonished", "bewildered", 
                        "stunned", "confused", "puzzled", "unexpected", "wow"]
        }
        
        emotion_scores = {}
        for emotion, keywords in emotion_patterns.items():
            matches = sum(1 for keyword in keywords if keyword in content_lower)
            if matches > 0:
                emotion_scores[emotion] = matches
        
        if emotion_scores:
            best_emotion = max(emotion_scores.items(), key=lambda x: x[1])
            intensity = min(best_emotion[1] * 0.3, 1.0)
            return best_emotion[0], intensity
        else:
            return 'neutral', 0.1
    
    def get_semantic_key(self, content: str) -> str:
        """Extract semantic key for concept clustering"""
        content_lower = content.lower()
        
        # Pet name patterns
        if any(word in content_lower for word in ['cat', 'dog', 'pet']) and 'name' in content_lower:
            return 'pet_name'
        
        # Color preferences
        if 'favorite color' in content_lower or 'like color' in content_lower:
            return 'favorite_color'
        
        # User name
        if 'my name is' in content_lower or 'i am called' in content_lower:
            return 'user_name'
        
        # Location
        if any(word in content_lower for word in ['live in', 'from', 'location']):
            return 'user_location'
        
        # Generic fallback - use first few words
        words = content_lower.split()[:3]
        return '_'.join(words)
    
    def extract_relationship_context(self, content: str, user_id: str) -> str:
        """Extract relationship context for intimacy + trust analysis"""
        content_lower = content.lower()
        
        # Trust indicators
        trust_keywords = {
            'confidential': ['secret', "don't tell", 'between us', 'private', 'confidential'],
            'trusting': ['trust you', 'count on', 'believe you', 'rely on'],
            'skeptical': ['doubt', 'unsure', 'not sure', 'suspicious', 'questioning']
        }
        
        # Intimacy indicators
        intimacy_keywords = {
            'intimate': ['love', 'relationship', 'feelings', 'heart', 'soul', 'deep inside'],
            'deep': ['worry', 'fear', 'dream', 'hope', 'struggle', 'personal'],
            'personal': ['family', 'friend', 'work', 'life', 'experience'],
            'casual': ['weather', 'news', 'general', 'how are you']
        }
        
        # Determine intimacy level
        intimacy_level = 'casual'
        for level, keywords in intimacy_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                intimacy_level = level
                break
            
        # Determine trust level
        trust_level = 'neutral'
        for level, keywords in trust_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                trust_level = level
                break
            
        return f"intimacy_{intimacy_level}_trust_{trust_level}"
    
    def extract_context_situation(self, content: str) -> str:
        """Extract situational and environmental context"""
        content_lower = content.lower()
        
        # Conversation mode indicators
        mode_keywords = {
            'crisis_support': ['help', 'emergency', 'urgent', 'crisis', 'scared', 'panic', 'desperate'],
            'educational': ['learn', 'explain', 'teach', 'understand', 'how does', 'what is'],
            'emotional_support': ['sad', 'upset', 'worried', 'anxious', 'depressed', 'hurt'],
            'playful': ['lol', 'haha', 'funny', 'joke', 'silly', 'fun', 'game'],
            'serious': ['important', 'serious', 'formal', 'business', 'official']
        }
        
        # Time context indicators
        time_keywords = {
            'morning': ['morning', 'breakfast', 'wake up', 'start day'],
            'evening': ['evening', 'night', 'dinner', 'tired', 'end of day'],
            'weekend': ['weekend', 'saturday', 'sunday', 'relax'],
            'holiday': ['holiday', 'vacation', 'christmas', 'birthday']
        }
        
        # Determine conversation mode
        conversation_mode = 'casual_chat'
        for mode, keywords in mode_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                conversation_mode = mode
                break
            
        # Determine time context
        time_context = 'general'
        for time, keywords in time_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                time_context = time
                break
                
        return f"mode_{conversation_mode}_time_{time_context}"
    
    def extract_personality_prominence(self, content: str, character_name: str = "general") -> str:
        """Extract personality traits for character alignment"""
        content_lower = content.lower()
        
        # Universal personality trait indicators
        trait_keywords = {
            'empathy': ['understand', 'feel', 'emotion', 'support', 'care', 'comfort'],
            'analytical': ['analyze', 'think', 'logic', 'reason', 'calculate', 'data'],
            'creative': ['create', 'imagine', 'art', 'design', 'innovative', 'original'],
            'adventurous': ['adventure', 'explore', 'travel', 'risk', 'exciting', 'journey'],
            'scientific': ['research', 'study', 'experiment', 'science', 'theory', 'hypothesis'],
            'philosophical': ['meaning', 'purpose', 'existence', 'philosophy', 'deep', 'profound'],
            'humorous': ['funny', 'joke', 'laugh', 'humor', 'wit', 'amusing'],
            'protective': ['protect', 'safe', 'security', 'guard', 'defend', 'shield'],
            'curious': ['wonder', 'question', 'curious', 'investigate', 'discover', 'learn']
        }
        
        # Determine prominent traits
        prominent_traits = []
        for trait, keywords in trait_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                prominent_traits.append(trait)
        
        # Default to 'balanced' if no specific traits detected
        if not prominent_traits:
            prominent_traits = ['balanced']
            
        # Return top 2 traits to avoid overly complex embeddings
        return f"traits_{'_'.join(prominent_traits[:2])}"
    
    def demonstrate_6d_key_generation(self, message: str, user_id: str = "user123", character_name: str = "elena"):
        """
        Demonstrate complete 6-dimensional key generation for a message
        """
        print(f"\n🎯 6-DIMENSIONAL KEY GENERATION DEMO")
        print(f"Message: '{message}'")
        print(f"User ID: {user_id}")
        print(f"Character: {character_name}")
        print("=" * 80)
        
        # Generate all 6 dimensional keys
        results = {}
        
        # 1. CONTENT (no tag prefix)
        results["content"] = {
            "key": message,
            "embedding_text": message,
            "description": "Direct semantic content"
        }
        
        # 2. EMOTION (uses RoBERTa/VADER/Keywords)
        emotion_context, intensity = self.extract_emotional_context(message)
        results["emotion"] = {
            "key": emotion_context,
            "embedding_text": f"emotion {emotion_context}: {message}",
            "intensity": intensity,
            "description": f"Emotional context with {intensity:.3f} intensity"
        }
        
        # 3. SEMANTIC (concept clustering)
        semantic_key = self.get_semantic_key(message)
        results["semantic"] = {
            "key": semantic_key,
            "embedding_text": f"concept {semantic_key}: {message}",
            "description": "Semantic grouping for contradiction detection"
        }
        
        # 4. RELATIONSHIP (intimacy + trust)
        relationship_context = self.extract_relationship_context(message, user_id)
        results["relationship"] = {
            "key": relationship_context,
            "embedding_text": f"relationship {relationship_context}: {message}",
            "description": "Bond development and interaction patterns"
        }
        
        # 5. CONTEXT (situational awareness)
        context_situation = self.extract_context_situation(message)
        results["context"] = {
            "key": context_situation,
            "embedding_text": f"context {context_situation}: {message}",
            "description": "Situational and environmental context"
        }
        
        # 6. PERSONALITY (character traits)
        personality_prominence = self.extract_personality_prominence(message, character_name)
        results["personality"] = {
            "key": personality_prominence,
            "embedding_text": f"personality {personality_prominence}: {message}",
            "description": "Character trait prominence for authenticity"
        }
        
        # Display results
        for i, (dimension, data) in enumerate(results.items(), 1):
            print(f"\n{i}. {dimension.upper()} DIMENSION:")
            print(f"   Key: '{data['key']}'")
            print(f"   Embedding Text: '{data['embedding_text']}'")
            if 'intensity' in data:
                print(f"   Intensity: {data['intensity']:.3f}")
            print(f"   Purpose: {data['description']}")
        
        return results
    
    def run_comprehensive_demo(self):
        """
        Run comprehensive demonstration with various message types
        """
        print("🎯 WHISPERENGINE 6-DIMENSIONAL EMBEDDING KEY GENERATION")
        print("=" * 90)
        
        test_messages = [
            {
                "message": "I'm so excited about my new research project on marine ecosystems!",
                "user_id": "scientist_user",
                "character": "elena",
                "description": "Scientific excitement with Elena character"
            },
            {
                "message": "I'm worried about telling you this secret, but I trust you completely.",
                "user_id": "close_friend", 
                "character": "marcus",
                "description": "Deep relationship with confidential trust"
            },
            {
                "message": "My cat's name is Whiskers and my favorite color is blue.",
                "user_id": "pet_owner",
                "character": "jake", 
                "description": "Personal facts for semantic clustering"
            },
            {
                "message": "Help! This is an emergency and I need urgent assistance!",
                "user_id": "emergency_user",
                "character": "gabriel",
                "description": "Crisis support context"
            },
            {
                "message": "Good morning! What's the weather like today?",
                "user_id": "casual_user",
                "character": "sophia",
                "description": "Casual morning interaction"
            }
        ]
        
        for i, test in enumerate(test_messages, 1):
            print(f"\n\n🧪 TEST CASE {i}: {test['description']}")
            results = self.demonstrate_6d_key_generation(
                test["message"], 
                test["user_id"], 
                test["character"]
            )
        
        # Show the enhanced CDL integration
        self.show_enhanced_cdl_integration()
    
    def show_enhanced_cdl_integration(self):
        """
        Show how the enhanced CDL integration uses all 6 dimensions
        """
        print(f"\n\n🚀 ENHANCED CDL INTEGRATION (NOW USING ALL 6 DIMENSIONS)")
        print("=" * 80)
        
        print("""
📊 BEFORE (3 dimensions only):
dimensions = {
    "content": content_embedding,           # 50% weight
    "relationship": relationship_embedding, # 30% weight  
    "personality": personality_embedding    # 20% weight
}

🎯 AFTER (Full 6-dimensional intelligence):
dimensions = {
    "content": content_embedding,           # 25% - Core semantic relevance
    "emotion": emotion_embedding,          # 20% - Emotional intelligence  
    "personality": personality_embedding,   # 20% - Character consistency
    "relationship": relationship_embedding, # 15% - Bond-appropriate responses
    "context": context_embedding,          # 15% - Situational awareness
    "semantic": semantic_embedding        # 5% - Concept clustering support
}

💡 IMPACT:
✅ Emotional Intelligence: Now captures RoBERTa/VADER emotion analysis
✅ Concept Clustering: Detects contradictory information 
✅ Situational Awareness: Understands crisis vs casual vs educational contexts
✅ Complete Character Depth: All 6 dimensions of personality and context
✅ Better Memory Retrieval: More nuanced and contextually appropriate responses

🔧 IMPLEMENTATION:
- Updated src/prompts/cdl_ai_integration.py to use retrieve_memories_by_dimensions()
- Balanced weighting system for optimal character authenticity
- Full extraction pipeline with proper embedding tag generation
- Production-ready 6D intelligence for all WhisperEngine characters
        """)
        
        print(f"\n🎉 RESULT: WhisperEngine now has complete 6-dimensional emotional and contextual intelligence!")

def main():
    """Run the 6-dimensional embedding key generation demonstration"""
    demo = EmbeddingKeyGenerationDemo()
    demo.run_comprehensive_demo()

if __name__ == "__main__":
    main()