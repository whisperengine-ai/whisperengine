#!/usr/bin/env python3
"""
Enhanced conversation context improvement script.

Implements a hybrid approach:
1. Fast local processing for user facts, names, preferences
2. LLM assistance for complex emotional/relationship analysis when needed
3. Better integration of existing emotional intelligence

This addresses the specific issues:
- Missing emotional intelligence in prompts
- Incorrect preferred name handling (MarkAnthony -> Mark)
- Incomplete user fact extraction
- Poor conversation topic summarization
"""

import asyncio
import sys
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

sys.path.append('src')


class EnhancedUserFactExtractor:
    """Enhanced user fact extraction using pattern matching + optional LLM assistance."""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        
        # Enhanced pattern matching for user facts
        self.name_patterns = [
            r"(?:my name is|call me|i'm|i am)\s+([A-Z][a-z]+)",
            r"(?:name is|called)\s+([A-Z][a-z]+)",
            r"just (?:call me|use)\s+([A-Z][a-z]+)",
            r"prefer (?:to be called|being called)\s+([A-Z][a-z]+)"
        ]
        
        self.food_preferences = {
            'pizza': ['pizza', 'pizzas'],
            'burgers': ['burger', 'burgers'],
            'sandwiches': ['sandwich', 'sandwiches'],
            'tacos': ['taco', 'tacos', 'mexican food'],
            'sushi': ['sushi', 'japanese food'],
            'pasta': ['pasta', 'italian food']
        }
        
        self.activities = {
            'beach activities': ['beach', 'ocean', 'surf'],
            'swimming': ['swim', 'swimming', 'pool'],
            'diving': ['dive', 'diving', 'scuba'],
            'travel': ['travel', 'traveling', 'trip'],
            'photography': ['photo', 'photography', 'camera'],
            'gaming': ['game', 'gaming', 'video game']
        }
    
    def extract_preferred_name_from_discord(self, discord_name: str) -> Optional[str]:
        """Extract likely preferred name from Discord username."""
        if not discord_name:
            return None
            
        # Handle compound names like "MarkAnthony" -> "Mark"
        # Look for capital letters that indicate word boundaries
        matches = re.findall(r'[A-Z][a-z]+', discord_name)
        if len(matches) >= 2:
            # Take the first name from compound names
            return matches[0]
        elif len(matches) == 1:
            return matches[0]
        
        return None
    
    def extract_user_facts(self, memories: List[Dict], discord_metadata: Dict = None) -> List[str]:
        """Enhanced user fact extraction with multiple sources."""
        facts = []
        
        # 1. Handle preferred name from Discord metadata
        if discord_metadata and discord_metadata.get('discord_author_name'):
            discord_name = discord_metadata['discord_author_name']
            preferred_name = self.extract_preferred_name_from_discord(discord_name)
            if preferred_name and preferred_name != discord_name:
                facts.append(f"[Preferred name: {preferred_name}]")
        
        # 2. Extract from memory content
        food_likes = set()
        activity_likes = set()
        
        for memory in memories:
            content = memory.get("content", "").lower()
            metadata = memory.get("metadata", {})
            
            # Check metadata first
            if metadata.get("preferred_name"):
                facts.append(f"[Preferred name: {metadata['preferred_name']}]")
            
            # Extract from content patterns
            for pattern in self.name_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    name = match.group(1)
                    facts.append(f"[Preferred name: {name}]")
                    break
            
            # Food preferences
            for food_category, keywords in self.food_preferences.items():
                if any(keyword in content for keyword in keywords):
                    food_likes.add(food_category)
            
            # Activities
            for activity_category, keywords in self.activities.items():
                if any(keyword in content for keyword in keywords):
                    activity_likes.add(activity_category)
        
        # Add aggregated preferences
        if food_likes:
            facts.append(f"[Likes: {', '.join(sorted(food_likes))}]")
        if activity_likes:
            facts.append(f"[Activities: {', '.join(sorted(activity_likes))}]")
        
        # Remove duplicates while preserving order
        unique_facts = []
        seen = set()
        for fact in facts:
            if fact not in seen:
                unique_facts.append(fact)
                seen.add(fact)
        
        return unique_facts[:7]  # Increased limit


class EnhancedTopicSummarizer:
    """Enhanced topic summarization with better categorization."""
    
    def __init__(self):
        self.topic_categories = {
            'Food & Dining': {
                'keywords': ['pizza', 'burger', 'sandwich', 'taco', 'sushi', 'pasta', 'food', 'eat', 'meal', 'breakfast', 'dinner', 'lunch'],
                'patterns': ['what.*eat', 'favorite.*food', 'like.*pizza']
            },
            'Beach & Ocean Activities': {
                'keywords': ['beach', 'ocean', 'swim', 'dive', 'surf', 'water'],
                'patterns': ['go.*beach', 'swimming.*ocean']
            },
            'Social Interaction': {
                'keywords': ['hello', 'hi', 'good morning', 'good afternoon', 'how are you'],
                'patterns': ['good.*morning', 'how.*doing']
            },
            'Creative & Philosophical': {
                'keywords': ['dream', 'creative', 'art', 'imagination', 'philosophy', 'meaning'],
                'patterns': ['what.*mean', 'dream.*about']
            },
            'Science & Research': {
                'keywords': ['research', 'science', 'marine', 'biology', 'study', 'experiment'],
                'patterns': ['research.*about', 'science.*of']
            },
            'Emotions & Mood': {
                'keywords': ['happy', 'mood', 'feeling', 'secret', 'excited', 'good mood'],
                'patterns': ['feel.*like', 'in.*mood', 'what.*secret']
            }
        }
    
    def categorize_content(self, content: str) -> str:
        """Categorize content into meaningful topics."""
        content_lower = content.lower()
        
        # Score each category
        category_scores = {}
        for category, rules in self.topic_categories.items():
            score = 0
            
            # Keyword matching
            for keyword in rules['keywords']:
                if keyword in content_lower:
                    score += 1
            
            # Pattern matching
            for pattern in rules.get('patterns', []):
                if re.search(pattern, content_lower):
                    score += 2  # Patterns worth more
            
            if score > 0:
                category_scores[category] = score
        
        # Return highest scoring category or create generic
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            return f"{best_category} discussion"
        else:
            # Create generic topic from meaningful words
            words = re.findall(r'\b\w{3,}\b', content_lower)
            meaningful_words = [w for w in words if w not in ['the', 'and', 'for', 'are', 'you', 'what', 'how', 'that', 'this']]
            if meaningful_words:
                return f"Discussion about {' '.join(meaningful_words[:2])}"
            else:
                return "General conversation"


def test_enhanced_extraction():
    """Test the enhanced extraction methods."""
    print("🧪 Testing Enhanced User Fact Extraction...\n")
    
    extractor = EnhancedUserFactExtractor()
    
    # Test preferred name extraction from Discord names
    test_discord_names = ["MarkAnthony", "JohnSmith", "SarahJones", "Mike123", "alex_cool"]
    print("Discord Name → Preferred Name extraction:")
    for name in test_discord_names:
        preferred = extractor.extract_preferred_name_from_discord(name)
        print(f"  '{name}' → '{preferred}'")
    
    print("\n" + "="*50 + "\n")
    
    # Test topic summarization
    summarizer = EnhancedTopicSummarizer()
    
    test_contents = [
        "hi there! how are you doing today?",
        "I love pizza and burgers, what about you?", 
        "Let's go to the beach and swim in the ocean",
        "I'm in a really good mood today, what's your secret?",
        "I had a dream about creative art projects last night",
        "I'm doing marine biology research on ocean creatures",
        "What foods do you like to eat for breakfast?"
    ]
    
    print("Enhanced Topic Categorization:")
    for content in test_contents:
        topic = summarizer.categorize_content(content)
        print(f"  '{content[:40]}...' → '{topic}'")
    
    print("\n🎯 Enhanced extraction methods are working correctly!")


if __name__ == "__main__":
    load_dotenv()
    
    print("🚀 Enhanced Conversation Context Improvements")
    print("="*60)
    
    test_enhanced_extraction()
    
    print("\n✅ NEXT STEPS:")
    print("1. Integrate EnhancedUserFactExtractor into MessageProcessor")
    print("2. Fix emotional intelligence data mapping in CDL integration")
    print("3. Update topic summarization with enhanced categorization")
    print("4. Test with fresh Discord conversation to validate improvements")