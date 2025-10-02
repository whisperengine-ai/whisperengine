#!/usr/bin/env python3
"""
Enhanced Multi-Dimensional Embedding: Content Extraction vs Tag Prefixing

Demonstrates the difference between simple tag prefixing (current) 
and intelligent content extraction (enhanced) for each vector dimension.
"""

import re
from typing import Dict, List, Tuple

class EnhancedEmbeddingDemo:
    """Compare tag prefixing vs content extraction approaches"""
    
    def demonstrate_approaches(self):
        message = "I'm really worried about the coral reefs dying. My grandmother used to dive here when she was young and the reefs were so colorful back then."
        
        print("🔍 EMBEDDING GENERATION APPROACHES COMPARISON")
        print("=" * 60)
        print(f"Original Message: '{message}'")
        print()
        
        print("📋 APPROACH 1: Current Implementation (Tag Prefixing)")
        print("-" * 50)
        self.show_current_approach(message)
        
        print("\n📋 APPROACH 2: Enhanced Implementation (Content Extraction)")
        print("-" * 50) 
        self.show_enhanced_approach(message)
        
        print("\n🎯 COMPARISON & INSIGHTS")
        print("-" * 30)
        self.show_comparison()
    
    def show_current_approach(self, message: str):
        """Show current tag prefixing approach"""
        
        # Current implementation - just prefix tags
        dimensions = {
            "content": message,
            "emotion": f"emotion worried_concerned: {message}",
            "semantic": f"concept environmental_concern: {message}", 
            "relationship": f"relationship intimacy_personal_trust_trusting: {message}",
            "context": f"context mode_emotional_support_time_general: {message}",
            "personality": f"personality traits_empathy_scientific: {message}"
        }
        
        for dim, embedding_text in dimensions.items():
            print(f"🏷️ {dim.upper()} VECTOR:")
            print(f"   Input: '{embedding_text[:80]}...'")
            print()
    
    def show_enhanced_approach(self, message: str):
        """Show enhanced content extraction approach"""
        
        # Enhanced implementation - extract relevant content for each dimension
        extracted_content = self.extract_dimensional_content(message)
        
        dimensions = {
            "content": extracted_content["content"],
            "emotion": f"emotion worried_concerned: {extracted_content['emotional']}",
            "semantic": f"concept environmental_concern: {extracted_content['conceptual']}", 
            "relationship": f"relationship intimacy_personal_trust_trusting: {extracted_content['relational']}",
            "context": f"context mode_emotional_support_time_general: {extracted_content['contextual']}",
            "personality": f"personality traits_empathy_scientific: {extracted_content['personality']}"
        }
        
        for dim, embedding_text in dimensions.items():
            print(f"🎯 {dim.upper()} VECTOR:")
            print(f"   Input: '{embedding_text[:80]}...'")
            print()
    
    def extract_dimensional_content(self, message: str) -> Dict[str, str]:
        """Extract dimension-specific content from the message"""
        
        # Analyze message components
        sentences = self.split_into_sentences(message)
        
        return {
            "content": message,  # Full content for baseline semantic
            
            "emotional": self.extract_emotional_content(sentences),
            # → "I'm really worried about the coral reefs dying"
            
            "conceptual": self.extract_conceptual_content(sentences), 
            # → "coral reefs dying, reefs were colorful back then"
            
            "relational": self.extract_relational_content(sentences),
            # → "My grandmother used to dive here when she was young"
            
            "contextual": self.extract_contextual_content(sentences),
            # → "I'm really worried" (emotional state indicator)
            
            "personality": self.extract_personality_content(sentences)
            # → "coral reefs dying, environmental concern" (Elena's scientific focus)
        }
    
    def split_into_sentences(self, message: str) -> List[str]:
        """Split message into sentences for analysis"""
        sentences = re.split(r'[.!?]+', message)
        return [s.strip() for s in sentences if s.strip()]
    
    def extract_emotional_content(self, sentences: List[str]) -> str:
        """Extract emotionally-charged content"""
        emotional_words = ['worried', 'scared', 'excited', 'happy', 'sad', 'angry', 'frustrated']
        emotional_sentences = []
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in emotional_words):
                emotional_sentences.append(sentence)
        
        return " ".join(emotional_sentences) if emotional_sentences else sentences[0]
    
    def extract_conceptual_content(self, sentences: List[str]) -> str:
        """Extract topic/concept-specific content"""
        concept_keywords = ['coral', 'reefs', 'ocean', 'marine', 'dive', 'colorful', 'environment']
        concept_sentences = []
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in concept_keywords):
                concept_sentences.append(sentence)
                
        return " ".join(concept_sentences) if concept_sentences else sentences[0]
    
    def extract_relational_content(self, sentences: List[str]) -> str:
        """Extract relationship/personal content"""
        relational_keywords = ['grandmother', 'family', 'my', 'mother', 'father', 'friend', 'personal']
        relational_sentences = []
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in relational_keywords):
                relational_sentences.append(sentence)
                
        return " ".join(relational_sentences) if relational_sentences else "general conversation"
    
    def extract_contextual_content(self, sentences: List[str]) -> str:
        """Extract situational context indicators"""
        context_indicators = ['worried', 'excited', 'learning', 'asking', 'explaining', 'joking']
        contextual_parts = []
        
        for sentence in sentences:
            for indicator in context_indicators:
                if indicator in sentence.lower():
                    # Extract the contextual part
                    contextual_parts.append(f"{indicator}: {sentence}")
                    
        return " ".join(contextual_parts) if contextual_parts else "general conversation"
    
    def extract_personality_content(self, sentences: List[str]) -> str:
        """Extract content relevant to character personality traits"""
        # For Elena (marine biologist) - environmental and empathetic content
        elena_keywords = ['coral', 'reefs', 'ocean', 'marine', 'environment', 'worried', 'care']
        personality_sentences = []
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in elena_keywords):
                personality_sentences.append(sentence)
                
        return " ".join(personality_sentences) if personality_sentences else sentences[0]
    
    def show_comparison(self):
        """Show comparison between approaches"""
        
        print("🏷️ CURRENT APPROACH (Tag Prefixing):")
        print("   ✅ Simple to implement")
        print("   ✅ Works with existing embedding models")
        print("   ⚠️  Embeds entire message for each dimension")
        print("   ⚠️  May dilute dimension-specific signals")
        print()
        
        print("🎯 ENHANCED APPROACH (Content Extraction):")
        print("   ✅ Dimension-specific content focus")
        print("   ✅ Cleaner semantic separation") 
        print("   ✅ More precise similarity matching")
        print("   ⚠️  More complex extraction logic")
        print("   ⚠️  Risk of losing important context")
        print()
        
        print("🔬 WHICH IS BETTER?")
        print("   Current: Good for proof-of-concept and development")
        print("   Enhanced: Better for production character authenticity")
        print("   Hybrid: Could combine both approaches for robustness")

def main():
    demo = EnhancedEmbeddingDemo()
    demo.demonstrate_approaches()

if __name__ == "__main__":
    main()