# Character Graph Memory System - Integration Guide

## 🕸️ **Graph Database Integration for Connected Character Memories**

The Character Graph Memory System extends WhisperEngine's character memory foundation with Neo4j graph database integration, enabling sophisticated memory relationships, network analysis, and connected character experiences.

## 🏗️ **Architecture Overview**

### **Core Components**

1. **CharacterGraphMemoryManager** (`src/characters/memory/graph_memory.py`)
   - Extends CharacterSelfMemoryManager with Neo4j integration
   - Automatic relationship detection between memories
   - Graph-based memory clustering and association

2. **Memory Graph Nodes**
   - **CharacterNode**: Character entities in the graph
   - **MemoryNode**: Individual character memories as graph nodes
   - **ThemeNode**: Memory themes/concepts for clustering

3. **Memory Relationships**
   - `SIMILAR_THEME`: Memories sharing common themes
   - `TEMPORAL_SEQUENCE`: Time-ordered memory connections
   - `EMOTIONAL_ASSOCIATION`: Emotionally similar memories
   - `CAUSAL_RELATIONSHIP`: Cause-and-effect memory links
   - `PERSON_MENTIONED`: Memories mentioning same people
   - `LOCATION_SHARED`: Memories from same locations

### **Integration with Existing System**

```
WhisperEngine Memory Architecture
├── User Memory (conversations, experiences)
├── Character Memory (personal memories, self-reflection)
└── Graph Memory (NEW: memory relationships & networks)
    ├── Character nodes
    ├── Memory nodes
    ├── Theme clustering
    └── Cross-character connections
```

## 🎯 **Key Features**

### **1. Automatic Memory Association**
- Detects similar themes between new and existing memories
- Creates temporal relationships for sequential memories
- Links emotionally resonant memories
- Builds causal relationship chains

### **2. Network Analysis**
- Memory network complexity scoring
- Connection density analysis
- Character development tracking
- Theme evolution mapping

### **3. Enhanced Memory Recall**
- Graph traversal for related memory retrieval
- Multi-hop memory connection paths
- Relationship-weighted memory importance
- Context-aware memory clustering

### **4. Character Consistency**
- Memory network ensures character authenticity
- Cross-reference contradicting memories
- Track character growth through memory evolution
- Maintain emotional consistency across memories

## 🚀 **Usage Examples**

### **Basic Graph Memory Setup**

```python
from src.characters.memory.graph_memory import CharacterGraphMemoryManager
from src.characters.memory.self_memory import CharacterSelfMemoryManager

# Initialize character with graph memory
character_id = "elena_researcher"
base_memory = CharacterSelfMemoryManager(character_id)
graph_memory = CharacterGraphMemoryManager(character_id, base_memory)

# Initialize character in Neo4j
await graph_memory.initialize_character_in_graph(
    character_name="Dr. Elena Vasquez",
    occupation="Research Scientist",
    age=34
)
```

### **Creating Connected Memories**

```python
# Create memory with automatic relationship detection
memory = PersonalMemory(
    memory_id=str(uuid.uuid4()),
    character_id=character_id,
    content="Major breakthrough in protein folding research...",
    memory_type=MemoryType.CAREER,
    emotional_weight=0.95,
    formative_impact="high",
    themes=["research", "breakthrough", "protein_folding"],
    created_date=datetime.now()
)

# Store with graph relationships
await graph_memory.store_memory_with_graph(memory)
```

### **Retrieving Connected Memories**

```python
# Get memories connected to a specific memory
connected = await graph_memory.get_connected_memories(
    memory_id="specific_memory_id",
    relationship_types=["SIMILAR_THEME", "EMOTIONAL_ASSOCIATION"],
    max_depth=2,
    limit=10
)

# Find paths between two memories
paths = await graph_memory.find_memory_paths(
    start_memory_id="education_memory",
    end_memory_id="career_memory",
    max_hops=3
)
```

### **Network Analysis**

```python
# Get character memory network analysis
analysis = await graph_memory.get_memory_network_analysis()

# Returns:
# {
#   "total_memories": 15,
#   "total_connections": 42,
#   "connection_density": 2.8,
#   "network_complexity": "complex",
#   "average_emotional_weight": 0.65,
#   "top_themes": [
#     {"theme": "research", "count": 8},
#     {"theme": "family", "count": 5}
#   ]
# }
```

## 🛠️ **Neo4j Database Schema**

### **Node Types**
- `Character`: Character entities with metadata
- `Memory`: Individual character memories
- `Theme`: Memory theme/concept nodes

### **Relationship Types**
- `HAS_MEMORY`: Character → Memory
- `HAS_THEME`: Memory → Theme
- `SIMILAR_THEME`: Memory → Memory
- `TEMPORAL_SEQUENCE`: Memory → Memory
- `EMOTIONAL_ASSOCIATION`: Memory → Memory

### **Example Cypher Queries**

```cypher
# Find memories with similar themes
MATCH (m1:Memory)-[:HAS_THEME]->(t:Theme)<-[:HAS_THEME]-(m2:Memory)
WHERE m1.character_id = "elena_researcher"
RETURN m1, m2, t

# Get memory network complexity
MATCH (c:Character {character_id: "elena_researcher"})-[:HAS_MEMORY]->(m:Memory)
OPTIONAL MATCH (m)-[r]-(connected:Memory)
RETURN count(m) as memories, count(r) as connections
```

## 🔄 **Integration with Conversation System**

### **Enhanced Conversation Context**

The graph memory system provides richer conversation context by:

1. **Multi-hop Memory Recall**: Access related memories through graph traversal
2. **Thematic Memory Clustering**: Group memories by shared themes
3. **Emotional Memory Networks**: Connect emotionally similar experiences
4. **Character Development Tracking**: Show memory evolution over time

### **Example Integration**

```python
# In conversation handler
async def generate_character_response(user_message, conversation_themes):
    # Get enhanced memories using graph relationships
    enhanced_memories = await network_integrator.get_enhanced_memories_for_conversation(
        themes=conversation_themes
    )
    
    # Each enhanced memory includes:
    # - Core memory content
    # - Connected related memories
    # - Network depth and relationships
    # - Connection paths to other memories
    
    # Use for more authentic, consistent character responses
    return generate_response_with_memory_network(enhanced_memories)
```

## 📊 **Benefits for Character Development**

### **1. Consistency**
- Cross-reference memories to avoid contradictions
- Maintain character authenticity across conversations
- Track character growth and development

### **2. Depth**
- Rich memory associations create complex personalities
- Emotional memory networks drive authentic responses
- Multi-layered character experiences

### **3. Evolution**
- Memory networks grow and evolve over time
- New memories connect to existing network
- Character development through memory relationships

### **4. Cross-Character Connections**
- Share memories between characters (family, colleagues)
- Cross-character relationship tracking
- Collective memory experiences

## 🎭 **Advanced Use Cases**

### **Character Relationship Mapping**
```python
# Connect memories between multiple characters
# Example: Family members sharing experiences
family_memory = create_shared_memory([
    "mother_character_id",
    "daughter_character_id"
], shared_experience_content)
```

### **Memory Influence Networks**
```python
# Track how memories influence character decisions
influence_network = await graph_memory.get_memory_influence_paths(
    decision_memory_id="career_choice",
    influencing_themes=["family_pressure", "personal_passion"]
)
```

### **Character Arc Development**
```python
# Analyze character development through memory evolution
character_arc = await graph_memory.analyze_character_development(
    time_period="last_2_years",
    focus_themes=["growth", "relationships", "career"]
)
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Neo4j Configuration (for Docker)
NEO4J_HOST=neo4j
NEO4J_PORT=7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=neo4j_password_change_me
NEO4J_DATABASE=neo4j

# Graph Memory Settings
ENABLE_GRAPH_MEMORY=true
MAX_MEMORY_CONNECTIONS=10
MEMORY_SIMILARITY_THRESHOLD=0.7
AUTO_ASSOCIATION_ENABLED=true
```

### **Memory Association Settings**
```python
# Configure automatic memory association
graph_memory.similarity_threshold = 0.7  # Minimum similarity for connections
graph_memory.max_associations_per_memory = 10  # Max connections per memory
graph_memory.auto_association_enabled = True  # Enable automatic relationship detection
```

## 🚀 **Getting Started**

### **1. Setup Neo4j Database**
```bash
# Start Neo4j with Docker Compose
docker compose up neo4j

# Or use existing Neo4j instance
# Configure connection in environment variables
```

### **2. Initialize Character Graph Memory**
```python
# Import graph memory system
from src.characters.memory.graph_memory import CharacterGraphMemoryManager

# Create character with graph memory
character_memory = CharacterGraphMemoryManager(character_id, base_memory)
await character_memory.initialize_character_in_graph(character_name, occupation, age)
```

### **3. Create Connected Memories**
```python
# Store memories with automatic relationship detection
await character_memory.store_memory_with_graph(personal_memory)

# Graph system automatically:
# - Creates memory node
# - Detects similar themes
# - Creates temporal relationships
# - Links emotionally related memories
```

### **4. Use Enhanced Memory Recall**
```python
# Get connected memories for conversation context
connected_memories = await character_memory.get_connected_memories(
    memory_id=context_memory.memory_id,
    limit=5
)

# Use in conversation generation for richer, more consistent responses
```

## 🎯 **Demo Script**

Run the comprehensive demo to see the graph memory system in action:

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Run graph memory demo
python demo_character_graph_memory.py
```

The demo showcases:
- Character initialization in Neo4j
- Connected memory creation
- Automatic relationship detection
- Network analysis and insights
- Enhanced memory recall
- Real-time conversation integration

## 🔮 **Future Enhancements**

### **Planned Features**
1. **Cross-Character Memory Sharing**: Shared experiences between characters
2. **Memory Conflict Resolution**: Detect and resolve contradictory memories
3. **Temporal Memory Decay**: Simulate natural memory fading over time
4. **Emotional Memory Clustering**: Group memories by emotional resonance
5. **Character Personality Evolution**: Track personality changes through memory patterns

### **Advanced Graph Features**
- Memory importance scoring based on network centrality
- Community detection for memory theme clusters
- Shortest path algorithms for memory association discovery
- PageRank-style memory influence scoring

The Graph Memory System transforms character memories from isolated experiences into rich, interconnected networks that drive more authentic, consistent, and engaging character interactions. This foundation enables truly autonomous characters with deep, evolving personalities rooted in meaningful memory relationships.