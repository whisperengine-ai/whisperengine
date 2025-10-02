# 🧠 Multi-Dimensional Vector Embedding Generation: Complete Decision Logic

## 📊 Embedding Generation Matrix: Storage Phase

Here's exactly how the 6 named vectors are generated during memory storage:

### **Example: "I'm really worried about the coral reefs dying. My grandmother used to dive here when she was young."**

| Vector Dimension | Input Construction | Embedding Text | Purpose |
|-----------------|-------------------|----------------|---------|
| **content** | Raw message | `"I'm really worried about the coral reefs dying. My grandmother used to dive here when she was young."` | Semantic similarity search |
| **emotion** | `f"emotion {emotional_context}: {content}"` | `"emotion worried_concerned: I'm really worried about the coral reefs dying..."` | Sentiment-aware retrieval |
| **semantic** | `f"concept {semantic_key}: {content}"` | `"concept environmental_concern: I'm really worried about the coral reefs dying..."` | Contradiction detection |
| **relationship** | `f"relationship {relationship_context}: {content}"` | `"relationship intimacy_personal_trust_trusting: I'm really worried about..."` | Bond-appropriate responses |
| **context** | `f"context {context_situation}: {content}"` | `"context mode_emotional_support_time_general: I'm really worried about..."` | Situational awareness |
| **personality** | `f"personality {personality_prominence}: {content}"` | `"personality traits_empathy_scientific: I'm really worried about..."` | Character trait consistency |

### **🔍 Extraction Logic Details**

#### **1. Emotional Context Extraction**
```python
def _extract_emotional_context(self, content: str, user_id: str) -> Tuple[str, float]:
    content_lower = content.lower()
    
    # Keywords → Emotions mapping
    emotion_keywords = {
        'worried_concerned': ['worried', 'concerned', 'anxious', 'scared'],
        'happy_excited': ['happy', 'excited', 'thrilled', 'amazing'],
        'sad_depressed': ['sad', 'depressed', 'down', 'upset'],
        'angry_frustrated': ['angry', 'frustrated', 'mad', 'furious'],
        'confused_uncertain': ['confused', 'uncertain', 'unclear', 'unsure']
    }
    
    # Result: "worried_concerned" (intensity: 0.8)
    # Embedding: "emotion worried_concerned: I'm really worried about..."
```

#### **2. Semantic Key Extraction**  
```python
def _get_semantic_key(self, content: str) -> str:
    content_lower = content.lower()
    
    # Pattern matching for concept categories
    if any(word in content_lower for word in ['coral', 'reef', 'ocean', 'marine']):
        return 'environmental_concern'
    elif any(word in content_lower for word in ['algorithm', 'neural', 'machine learning']):
        return 'technical_education'
    elif any(word in content_lower for word in ['family', 'grandmother', 'parent']):
        return 'family_memory'
    
    # Result: "environmental_concern"
    # Embedding: "concept environmental_concern: I'm really worried about..."
```

#### **3. Relationship Context Extraction (NEW)**
```python
def _extract_relationship_context(self, content: str, user_id: str) -> str:
    content_lower = content.lower()
    
    # Intimacy analysis
    intimacy_keywords = {
        'intimate': ['love', 'relationship', 'feelings', 'heart', 'soul'],
        'deep': ['worry', 'fear', 'dream', 'hope', 'struggle', 'personal'],
        'personal': ['family', 'grandmother', 'friend', 'life', 'experience'],
        'casual': ['weather', 'news', 'general', 'how are you']
    }
    
    # Trust analysis  
    trust_keywords = {
        'confidential': ['secret', "don't tell", 'between us', 'private'],
        'trusting': ['trust you', 'count on', 'believe you'],
        'skeptical': ['doubt', 'unsure', 'suspicious']
    }
    
    # Result: "intimacy_personal_trust_trusting" 
    # Embedding: "relationship intimacy_personal_trust_trusting: I'm really worried..."
```

#### **4. Context Situation Extraction (NEW)**
```python
def _extract_context_situation(self, content: str) -> str:
    content_lower = content.lower()
    
    # Conversation mode detection
    mode_keywords = {
        'crisis_support': ['help', 'emergency', 'urgent', 'panic', 'desperate'],
        'educational': ['learn', 'explain', 'teach', 'understand', 'how does'],
        'emotional_support': ['sad', 'upset', 'worried', 'anxious', 'hurt'],
        'playful': ['lol', 'haha', 'funny', 'joke', 'silly'],
        'serious': ['important', 'serious', 'formal', 'business']
    }
    
    # Time context detection
    time_keywords = {
        'morning': ['morning', 'breakfast', 'wake up'],
        'evening': ['evening', 'night', 'tired'],
        'weekend': ['weekend', 'saturday', 'sunday']
    }
    
    # Result: "mode_emotional_support_time_general"
    # Embedding: "context mode_emotional_support_time_general: I'm really worried..."
```

#### **5. Personality Prominence Extraction (NEW)**
```python
def _extract_personality_prominence(self, content: str, character_name: str = None) -> str:
    content_lower = content.lower()
    
    # Universal trait detection
    trait_keywords = {
        'empathy': ['understand', 'feel', 'emotion', 'support', 'care', 'comfort'],
        'analytical': ['analyze', 'think', 'logic', 'reason', 'calculate'],
        'creative': ['create', 'imagine', 'art', 'design', 'innovative'],
        'adventurous': ['adventure', 'explore', 'travel', 'risk', 'exciting'],
        'scientific': ['research', 'study', 'experiment', 'theory', 'coral', 'reef'],
        'humorous': ['funny', 'joke', 'laugh', 'humor', 'wit'],
        'protective': ['protect', 'safe', 'security', 'guard', 'defend'],
        'curious': ['wonder', 'question', 'curious', 'investigate', 'learn']
    }
    
    # Result: "traits_empathy_scientific" (coral + worried = empathy + scientific)
    # Embedding: "personality traits_empathy_scientific: I'm really worried..."
```

## 🔍 Query Phase: Search Embedding Generation

### **Query: "Tell me more about ocean conservation efforts"**

| Dimension | Query Embedding Construction | Search Vector |
|-----------|----------------------------|---------------|
| **content** | `generate_embedding(query)` | `"Tell me more about ocean conservation efforts"` |
| **relationship** | `generate_embedding(f"relationship {extracted_context}: {query}")` | `"relationship intimacy_casual_trust_neutral: Tell me more..."` |
| **personality** | `generate_embedding(f"personality {traits}: {query}")` | `"personality traits_scientific_curious: Tell me more..."` |

### **🎯 Multi-Dimensional Search Execution**

```python
# 1. Generate query embeddings for each dimension
content_embedding = await generate_embedding("Tell me more about ocean conservation efforts")

relationship_context = _extract_relationship_context("Tell me more...", user_id) 
# → "intimacy_casual_trust_neutral"
relationship_embedding = await generate_embedding("relationship intimacy_casual_trust_neutral: Tell me more...")

personality_prominence = _extract_personality_prominence("Tell me more...", "elena")
# → "traits_scientific_curious" 
personality_embedding = await generate_embedding("personality traits_scientific_curious: Tell me more...")

# 2. Execute separate searches for each dimension
results = {}
for dimension, embedding in dimensions.items():
    search_results = client.search(
        collection_name=collection_name,
        query_vector=models.NamedVector(name=dimension, vector=embedding),
        query_filter=user_and_bot_filters,
        limit=limit * 2
    )
    
    # Apply dimension-specific weighting
    weight = weights[dimension]  # content: 0.5, relationship: 0.3, personality: 0.2
    for result in search_results:
        memory_id = result.id
        weighted_score = result.score * weight
        # Combine scores across dimensions...
```

## 📊 Real Example: Complete Flow

### **Storage Example:**
```python
user_message = "I'm worried about coral reefs dying. My grandmother used to dive here."

# Generated embeddings:
vectors = {
    "content": embedding_of("I'm worried about coral reefs dying..."),
    "emotion": embedding_of("emotion worried_concerned: I'm worried about coral reefs..."), 
    "semantic": embedding_of("concept environmental_concern: I'm worried about coral reefs..."),
    "relationship": embedding_of("relationship intimacy_personal_trust_trusting: I'm worried..."),
    "context": embedding_of("context mode_emotional_support_time_general: I'm worried..."),
    "personality": embedding_of("personality traits_empathy_scientific: I'm worried...")
}

# Stored in Qdrant with metadata:
payload = {
    "content": "I'm worried about coral reefs dying...",
    "emotional_context": "worried_concerned",
    "semantic_key": "environmental_concern", 
    "relationship_context": "intimacy_personal_trust_trusting",
    "context_situation": "mode_emotional_support_time_general",
    "personality_prominence": "traits_empathy_scientific"
}
```

### **Query Example:**
```python
query = "Tell me about ocean conservation"

# Multi-dimensional search:
dimensions = {
    "content": embedding_of("Tell me about ocean conservation"),
    "relationship": embedding_of("relationship intimacy_casual_trust_neutral: Tell me..."),
    "personality": embedding_of("personality traits_scientific_curious: Tell me...")
}

# Results combined with weights:
# - Original coral reef memory matches on content (0.85) + personality (0.92) = high relevance
# - Relationship appropriately weighted for casual follow-up question
```

## 🎯 Key Insights

### **Embedding Differentiation Strategy**
1. **Prefixed Content**: Each dimension uses specific prefixes (`"emotion"`, `"relationship"`, etc.) to create semantically distinct embedding spaces
2. **Context Injection**: Extracted contextual information is injected into embedding text to capture nuanced patterns
3. **Character Awareness**: Bot-specific traits influence personality embeddings for character consistency
4. **Graduated Weighting**: Search combines dimensions with configurable weights for balanced relevance

### **Why This Works**
- **Semantic Separation**: Prefixes create distinct vector spaces for different aspects
- **Pattern Recognition**: FastEMBED model learns to associate prefixed patterns with specific search intents
- **Multi-Dimensional Similarity**: Each dimension captures different types of conversational relevance
- **Character Authenticity**: Personality and relationship dimensions ensure responses match character and bond level

The multi-dimensional embedding system transforms flat semantic search into **character-authentic relationship intelligence** that preserves conversation nuance across all contextual layers.