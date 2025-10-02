#!/usr/bin/env python3
"""
🎯 EMOTION VECTORS vs EMOTION SCORES COMPARISON

This demonstration shows WHY emotion vector queries are superior to 
emotion score filtering for memory retrieval in WhisperEngine.

SPOILER ALERT: Vector similarity captures semantic meaning and context
that numerical score filtering simply cannot match!
"""

import asyncio
import logging
from typing import Dict, List, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmotionVectorVsScoreComparison:
    """
    Compare emotion vector similarity vs emotion score filtering approaches
    """
    
    def __init__(self):
        self.setup_test_data()
    
    def setup_test_data(self):
        """Setup realistic test memories with emotions"""
        self.test_memories = [
            {
                "id": 1,
                "content": "I'm absolutely thrilled about getting the job! This is amazing!",
                "emotion_scores": {"primary_emotion": "joy", "emotional_intensity": 0.95},
                "emotion_embedding": "emotion joy: I'm absolutely thrilled about getting the job! This is amazing!"
            },
            {
                "id": 2, 
                "content": "The weather is nice today, feels good to be outside.",
                "emotion_scores": {"primary_emotion": "joy", "emotional_intensity": 0.65},
                "emotion_embedding": "emotion joy: The weather is nice today, feels good to be outside."
            },
            {
                "id": 3,
                "content": "I'm excited about the concert tonight, can't wait to hear them play!",
                "emotion_scores": {"primary_emotion": "joy", "emotional_intensity": 0.88},
                "emotion_embedding": "emotion joy: I'm excited about the concert tonight, can't wait to hear them play!"
            },
            {
                "id": 4,
                "content": "Feeling really happy that my friend recovered from surgery.",
                "emotion_scores": {"primary_emotion": "joy", "emotional_intensity": 0.78},
                "emotion_embedding": "emotion joy: Feeling really happy that my friend recovered from surgery."
            },
            {
                "id": 5,
                "content": "I'm disappointed about the meeting being cancelled again.",
                "emotion_scores": {"primary_emotion": "sadness", "emotional_intensity": 0.72},
                "emotion_embedding": "emotion sadness: I'm disappointed about the meeting being cancelled again."
            },
            {
                "id": 6,
                "content": "This is incredibly frustrating! The system keeps crashing.",
                "emotion_scores": {"primary_emotion": "anger", "emotional_intensity": 0.91},
                "emotion_embedding": "emotion anger: This is incredibly frustrating! The system keeps crashing."
            },
            {
                "id": 7,
                "content": "Wow, that promotion announcement was totally unexpected!",
                "emotion_scores": {"primary_emotion": "surprise", "emotional_intensity": 0.89},
                "emotion_embedding": "emotion surprise: Wow, that promotion announcement was totally unexpected!"
            },
            {
                "id": 8,
                "content": "I feel grateful for all the support during this difficult time.",
                "emotion_scores": {"primary_emotion": "joy", "emotional_intensity": 0.71},  # RoBERTa might classify gratitude as joy
                "emotion_embedding": "emotion joy: I feel grateful for all the support during this difficult time."
            }
        ]
    
    def demonstrate_score_filtering_approach(self, query: str, target_emotion: str, min_intensity: float = 0.7):
        """
        Demonstrate traditional emotion score filtering approach
        """
        print(f"\n🔢 EMOTION SCORE FILTERING APPROACH")
        print(f"Query: '{query}'")
        print(f"Filter: primary_emotion='{target_emotion}' AND emotional_intensity >= {min_intensity}")
        print("-" * 60)
        
        # Filter by emotion scores
        filtered_memories = []
        for memory in self.test_memories:
            scores = memory["emotion_scores"]
            if (scores["primary_emotion"] == target_emotion and 
                scores["emotional_intensity"] >= min_intensity):
                filtered_memories.append(memory)
        
        print(f"📊 RESULTS ({len(filtered_memories)} matches):")
        for memory in filtered_memories:
            scores = memory["emotion_scores"]
            print(f"  ID {memory['id']}: {scores['primary_emotion']} ({scores['emotional_intensity']:.2f})")
            print(f"    Content: '{memory['content'][:60]}...'")
        
        # Show what we missed
        missed_memories = []
        for memory in self.test_memories:
            scores = memory["emotion_scores"]
            if scores["primary_emotion"] == target_emotion and scores["emotional_intensity"] < min_intensity:
                missed_memories.append(memory)
        
        if missed_memories:
            print(f"\n❌ MISSED RELEVANT MEMORIES (below intensity threshold):")
            for memory in missed_memories:
                scores = memory["emotion_scores"]
                print(f"  ID {memory['id']}: {scores['primary_emotion']} ({scores['emotional_intensity']:.2f})")
                print(f"    Content: '{memory['content'][:60]}...'")
        
        return filtered_memories
    
    def simulate_vector_similarity(self, query_embedding: str, memory_embedding: str) -> float:
        """
        Simulate vector similarity calculation (simplified)
        In real WhisperEngine, this would use FastEMBED cosine similarity
        """
        # Extract key emotion and content words for similarity simulation
        query_words = set(query_embedding.lower().split())
        memory_words = set(memory_embedding.lower().split())
        
        # Calculate Jaccard similarity as a proxy for semantic similarity
        intersection = len(query_words.intersection(memory_words))
        union = len(query_words.union(memory_words))
        
        base_similarity = intersection / union if union > 0 else 0
        
        # Boost similarity if emotions match (semantic understanding)
        query_emotion = self._extract_emotion_from_embedding(query_embedding)
        memory_emotion = self._extract_emotion_from_embedding(memory_embedding)
        
        if query_emotion == memory_emotion:
            base_similarity += 0.3  # Emotion matching bonus
        elif self._emotions_are_similar(query_emotion, memory_emotion):
            base_similarity += 0.15  # Related emotion bonus
        
        # Boost for semantic content similarity
        content_similarity = self._calculate_content_similarity(query_embedding, memory_embedding)
        base_similarity += content_similarity * 0.2
        
        return min(1.0, base_similarity)
    
    def _extract_emotion_from_embedding(self, embedding_text: str) -> str:
        """Extract emotion from embedding text"""
        if embedding_text.startswith("emotion "):
            return embedding_text.split(":")[0].replace("emotion ", "").strip()
        return "unknown"
    
    def _emotions_are_similar(self, emotion1: str, emotion2: str) -> bool:
        """Check if emotions are semantically similar"""
        similar_groups = [
            ["joy", "happiness", "excitement", "gratitude"],
            ["sadness", "disappointment", "grief"],
            ["anger", "frustration", "irritation"],
            ["fear", "anxiety", "worry"],
            ["surprise", "amazement", "shock"]
        ]
        
        for group in similar_groups:
            if emotion1 in group and emotion2 in group:
                return True
        return False
    
    def _calculate_content_similarity(self, text1: str, text2: str) -> float:
        """Calculate content similarity beyond emotion tags"""
        # Remove emotion prefixes for content comparison
        content1 = text1.split(":", 1)[1].strip() if ":" in text1 else text1
        content2 = text2.split(":", 1)[1].strip() if ":" in text2 else text2
        
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0
    
    def demonstrate_vector_similarity_approach(self, query: str):
        """
        Demonstrate emotion vector similarity approach
        """
        print(f"\n🔤 EMOTION VECTOR SIMILARITY APPROACH")
        print(f"Query: '{query}'")
        
        # Create query embedding (simulated)
        query_emotion = self._detect_query_emotion(query)
        query_embedding = f"emotion {query_emotion}: {query}"
        
        print(f"Query Embedding: '{query_embedding}'")
        print("-" * 60)
        
        # Calculate similarity with all memories
        similarities = []
        for memory in self.test_memories:
            similarity = self.simulate_vector_similarity(query_embedding, memory["emotion_embedding"])
            similarities.append((memory, similarity))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        print(f"📊 RESULTS (ranked by similarity):")
        for memory, similarity in similarities[:6]:  # Show top 6
            scores = memory["emotion_scores"]
            print(f"  ID {memory['id']}: Similarity {similarity:.3f} | {scores['primary_emotion']} ({scores['emotional_intensity']:.2f})")
            print(f"    Content: '{memory['content'][:60]}...'")
        
        return similarities
    
    def _detect_query_emotion(self, query: str) -> str:
        """Detect emotion in query (simplified)"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["excited", "thrilled", "amazing", "great", "happy"]):
            return "joy"
        elif any(word in query_lower for word in ["sad", "disappointed", "upset"]):
            return "sadness"
        elif any(word in query_lower for word in ["angry", "frustrated", "mad"]):
            return "anger"
        elif any(word in query_lower for word in ["surprised", "unexpected", "shocked"]):
            return "surprise"
        elif any(word in query_lower for word in ["worried", "afraid", "nervous"]):
            return "fear"
        else:
            return "neutral"
    
    def run_comparative_analysis(self):
        """
        Run comparative analysis between both approaches
        """
        print("🎯 EMOTION VECTORS vs EMOTION SCORES COMPARATIVE ANALYSIS")
        print("=" * 80)
        
        # Test scenarios
        test_queries = [
            {
                "query": "I'm so excited about getting a new job!",
                "target_emotion": "joy",
                "min_intensity": 0.8,
                "description": "High-intensity joy query"
            },
            {
                "query": "Tell me about times when you felt happy about achievements",
                "target_emotion": "joy", 
                "min_intensity": 0.7,
                "description": "Achievement-related happiness query"
            },
            {
                "query": "I'm feeling disappointed about something that was cancelled",
                "target_emotion": "sadness",
                "min_intensity": 0.7,
                "description": "Disappointment query"
            }
        ]
        
        for i, test in enumerate(test_queries, 1):
            print(f"\n🧪 TEST SCENARIO {i}: {test['description']}")
            print("=" * 70)
            
            # Score filtering approach
            score_results = self.demonstrate_score_filtering_approach(
                test["query"], test["target_emotion"], test["min_intensity"]
            )
            
            # Vector similarity approach  
            vector_results = self.demonstrate_vector_similarity_approach(test["query"])
            
            # Analysis
            print(f"\n📈 ANALYSIS:")
            print(f"  Score Filtering: {len(score_results)} exact matches")
            print(f"  Vector Similarity: {len([r for r in vector_results if r[1] > 0.3])} relevant results (similarity > 0.3)")
            
            # Show advantages of vector approach
            high_similarity = [r for r in vector_results[:3] if r[1] > 0.4]
            if high_similarity:
                print(f"  Vector approach found high-relevance memories that score filtering might miss:")
                for memory, similarity in high_similarity:
                    if memory not in score_results:
                        scores = memory["emotion_scores"]
                        print(f"    ID {memory['id']}: {similarity:.3f} similarity | {scores['primary_emotion']} ({scores['emotional_intensity']:.2f})")
        
        self.show_why_vectors_are_better()
    
    def show_why_vectors_are_better(self):
        """
        Explain why emotion vectors outperform emotion score filtering
        """
        print(f"\n\n🧠 WHY EMOTION VECTORS ARE SUPERIOR TO SCORE FILTERING")
        print("=" * 70)
        
        advantages = {
            "1. Semantic Understanding": {
                "vectors": "Captures meaning and context: 'thrilled about job' matches 'excited about work'",
                "scores": "Only exact emotion labels: 'joy' matches 'joy', nothing else"
            },
            
            "2. Nuanced Similarity": {
                "vectors": "Finds related emotions: joy, excitement, gratitude all have semantic overlap",
                "scores": "Binary matching: either exact emotion match or no match at all"
            },
            
            "3. Content Awareness": {
                "vectors": "Understands context: 'job excitement' vs 'concert excitement' are differentiated",
                "scores": "Ignores context: all 'joy' memories treated equally regardless of topic"
            },
            
            "4. Flexible Querying": {
                "vectors": "Natural language: 'when I felt happy about achievements' finds relevant memories",
                "scores": "Rigid filters: must know exact emotion label and intensity threshold"
            },
            
            "5. Graceful Degradation": {
                "vectors": "Returns ranked results even when no perfect matches exist",
                "scores": "All-or-nothing: either meets criteria or completely excluded"
            },
            
            "6. Threshold Independence": {
                "vectors": "No arbitrary intensity thresholds needed - similarity is contextual",
                "scores": "Requires tuning thresholds (0.7? 0.8?) that may exclude relevant memories"
            }
        }
        
        for advantage, comparison in advantages.items():
            print(f"\n{advantage}:")
            print(f"  🔤 Vectors: {comparison['vectors']}")
            print(f"  🔢 Scores:  {comparison['scores']}")
        
        print(f"\n🎯 CONCLUSION:")
        print(f"Emotion vectors provide INTELLIGENT similarity matching that understands")
        print(f"meaning, context, and semantic relationships - something numerical")
        print(f"score filtering simply cannot achieve!")
        
        print(f"\n💡 BEST PRACTICE:")
        print(f"Use emotion VECTORS for retrieval (what WhisperEngine does) ✅")
        print(f"Use emotion SCORES for memory management (tiers, aging, significance) ✅")
        print(f"Both together = comprehensive emotional intelligence! 🧠✨")

def main():
    """Run the emotion vectors vs scores comparison"""
    comparison = EmotionVectorVsScoreComparison()
    comparison.run_comparative_analysis()

if __name__ == "__main__":
    main()