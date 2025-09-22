# LLM Tool Calling for Vector Store Management

## 🎯 Concept Overview

Using LLM tool calling to dynamically manage the vector store creates an **intelligent, self-optimizing memory system** where the AI companion can:

1. **Proactively update memory** based on conversation context
2. **Correct misconceptions** when users provide clarifications
3. **Organize memories semantically** using AI understanding
4. **Optimize vector storage** based on retrieval patterns
5. **Manage memory lifecycle** with intelligent retention/deletion

This transforms WhisperEngine from a passive memory system to an **active, intelligent knowledge curator**.

## 🔍 Current Foundation Analysis

### Existing Memory Tools (`src/memory/memory_tools.py`)
WhisperEngine already has basic LLM tool calling for memory management:

```python
# Current tools available:
- update_memory_fact()    # Update/correct specific facts
- delete_memory_fact()    # Remove incorrect information  
- search_memory_facts()   # Query existing facts
```

**Strengths:**
- ✅ Clean tool definition structure
- ✅ Validation and error handling
- ✅ User-driven corrections supported
- ✅ Structured fact management

**Limitations:**
- ❌ Only works with structured facts (hierarchical memory)
- ❌ No vector store integration
- ❌ No semantic understanding of content
- ❌ Limited to explicit user corrections

### LLM Client Capabilities
Current LLM support includes:
- **OpenRouter** - ✅ Supports function calling
- **LM Studio** - ✅ Supports function calling (OpenAI compatible)
- **Ollama** - ✅ Supports function calling (recent versions)
- **Local models** - ⚠️ Depends on model capabilities

## 🚀 Enhanced Vector Tool Calling Implementation

### Phase 1: Vector Memory Tools

```python
class VectorMemoryToolManager:
    """Advanced LLM tools for intelligent vector store management"""
    
    def __init__(self, vector_memory_store, llm_client):
        self.vector_store = vector_memory_store
        self.llm_client = llm_client
        self.tools = self._initialize_vector_tools()
    
    def _initialize_vector_tools(self) -> List[Dict[str, Any]]:
        """Initialize vector-specific memory tools"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "store_semantic_memory",
                    "description": "Store important information with semantic understanding and proper categorization",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "The important information to remember"
                            },
                            "memory_type": {
                                "type": "string",
                                "enum": ["personal_fact", "preference", "relationship", "experience", "learning", "goal"],
                                "description": "Type of memory for optimal storage and retrieval"
                            },
                            "importance": {
                                "type": "number",
                                "minimum": 1,
                                "maximum": 10,
                                "description": "Importance level (1-10) for retention priority"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Semantic tags for better retrieval (e.g., ['work', 'project', 'deadline'])"
                            },
                            "related_to": {
                                "type": "string",
                                "description": "What this memory relates to or expands upon"
                            }
                        },
                        "required": ["content", "memory_type"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_memory_context",
                    "description": "Update or correct existing memories with new context or corrections",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_query": {
                                "type": "string",
                                "description": "Query to find the memory to update"
                            },
                            "correction_content": {
                                "type": "string",
                                "description": "The correct information to store"
                            },
                            "update_reason": {
                                "type": "string",
                                "description": "Why this update is being made"
                            },
                            "merge_strategy": {
                                "type": "string",
                                "enum": ["replace", "append", "merge_semantic"],
                                "description": "How to handle the update"
                            }
                        },
                        "required": ["search_query", "correction_content", "update_reason"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "organize_related_memories",
                    "description": "Group and cross-reference related memories for better retrieval",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "The topic or theme to organize around"
                            },
                            "relationship_type": {
                                "type": "string",
                                "enum": ["sequential", "causal", "thematic", "temporal", "contradictory"],
                                "description": "How these memories relate to each other"
                            },
                            "consolidation_strategy": {
                                "type": "string",
                                "enum": ["link_only", "create_summary", "merge_similar"],
                                "description": "How to organize the related memories"
                            }
                        },
                        "required": ["topic"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "archive_outdated_memories",
                    "description": "Identify and archive memories that are no longer relevant or accurate",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "criteria": {
                                "type": "string", 
                                "enum": ["temporal", "superseded", "contradicted", "irrelevant"],
                                "description": "Criteria for archiving memories"
                            },
                            "topic_filter": {
                                "type": "string",
                                "description": "Focus archival on specific topic (optional)"
                            },
                            "archive_reason": {
                                "type": "string",
                                "description": "Explanation for why these memories should be archived"
                            },
                            "retention_period": {
                                "type": "integer",
                                "description": "Days to keep in archive before deletion (0 = permanent archive)"
                            }
                        },
                        "required": ["criteria", "archive_reason"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "enhance_memory_retrieval",
                    "description": "Add semantic enhancement and cross-references to improve future memory retrieval",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "memory_id": {
                                "type": "string",
                                "description": "ID of memory to enhance"
                            },
                            "enhancement_type": {
                                "type": "string",
                                "enum": ["add_synonyms", "extract_entities", "add_context", "create_summary"],
                                "description": "Type of enhancement to apply"
                            },
                            "enhancement_data": {
                                "type": "object",
                                "description": "Additional data for the enhancement (synonyms, entities, etc.)"
                            }
                        },
                        "required": ["memory_id", "enhancement_type"],
                        "additionalProperties": False
                    }
                }
            }
        ]
```

### Phase 2: Intelligent Memory Triggers

```python
class IntelligentMemoryManager:
    """AI-driven memory management using tool calling"""
    
    def __init__(self, vector_store, llm_client, tool_manager):
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.tool_manager = tool_manager
    
    async def process_conversation_for_memory_actions(
        self, 
        user_message: str, 
        bot_response: str, 
        user_id: str,
        conversation_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze conversation and determine memory actions using LLM tool calling"""
        
        # Create memory management prompt
        system_prompt = """You are an intelligent memory curator for an AI companion. 
        
        Your job is to analyze conversations and determine what memory actions to take:
        1. Store important new information
        2. Update or correct existing memories  
        3. Organize related memories
        4. Archive outdated information
        5. Enhance memories for better retrieval
        
        Use the available tools to manage memory intelligently. Consider:
        - Information importance and relevance
        - Relationships between different memories
        - Corrections or clarifications from the user
        - Temporal relevance of information
        - Semantic connections and cross-references
        
        Always prioritize user-provided corrections and preferences."""
        
        conversation_analysis_prompt = f"""
        Analyze this conversation and determine memory actions:
        
        User: {user_message}
        Assistant: {bot_response}
        
        Context: {json.dumps(conversation_context, indent=2)}
        
        What memory management actions should be taken? Use the available tools to:
        1. Store any important new information
        2. Correct any misconceptions or outdated info
        3. Organize related memories
        4. Enhance existing memories for better retrieval
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": conversation_analysis_prompt}
        ]
        
        # Call LLM with memory management tools
        response = await self.llm_client.generate_chat_completion(
            messages=messages,
            tools=self.tool_manager.tools,
            tool_choice="auto",  # Let LLM decide when to use tools
            temperature=0.1  # Low temperature for consistent memory management
        )
        
        # Execute any tool calls
        executed_actions = []
        if "tool_calls" in response.get("choices", [{}])[0].get("message", {}):
            tool_calls = response["choices"][0]["message"]["tool_calls"]
            
            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                parameters = json.loads(tool_call["function"]["arguments"])
                
                result = await self.tool_manager.execute_tool(
                    function_name, 
                    parameters, 
                    user_id
                )
                
                executed_actions.append({
                    "tool": function_name,
                    "parameters": parameters,
                    "result": result
                })
        
        return executed_actions
```

### Phase 3: Proactive Memory Optimization

```python
class ProactiveMemoryOptimizer:
    """Proactively optimize vector store based on usage patterns"""
    
    def __init__(self, vector_store, llm_client):
        self.vector_store = vector_store
        self.llm_client = llm_client
    
    async def optimize_memory_organization(self, user_id: str) -> Dict[str, Any]:
        """Use LLM to analyze and optimize memory organization"""
        
        # Get memory usage analytics
        memories = await self.vector_store.get_user_memories(user_id, limit=100)
        search_patterns = await self.vector_store.get_search_analytics(user_id)
        
        optimization_prompt = f"""
        Analyze this user's memory patterns and suggest optimizations:
        
        Recent Memories: {len(memories)} entries
        Search Patterns: {json.dumps(search_patterns, indent=2)}
        
        Memory Sample:
        {self._format_memories_for_analysis(memories[:10])}
        
        Suggest memory organization improvements:
        1. Identify related memories that should be linked
        2. Find duplicate or redundant information
        3. Suggest better categorization
        4. Identify memories that need enhancement
        5. Recommend archival of outdated information
        
        Provide specific tool calls to implement optimizations.
        """
        
        # Use tools to implement optimizations
        return await self._execute_optimization_tools(optimization_prompt, user_id)
    
    async def semantic_memory_clustering(self, user_id: str) -> Dict[str, Any]:
        """Group semantically related memories for better retrieval"""
        
        clustering_prompt = """
        Use semantic analysis to identify memory clusters that should be linked.
        Look for:
        1. Memories about the same person, place, or topic
        2. Sequential events or experiences  
        3. Related preferences or opinions
        4. Complementary factual information
        
        Create cross-references and summaries where beneficial.
        """
        
        return await self._execute_clustering_tools(clustering_prompt, user_id)
```

## 🛠️ Implementation Strategy

### Step 1: Enhance LLM Client for Tool Calling

```python
# Add to src/llm/llm_client.py

async def generate_chat_completion_with_tools(
    self,
    messages: List[Dict[str, str]],
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: Optional[str] = "auto",
    **kwargs
) -> Dict[str, Any]:
    """Generate chat completion with tool calling support"""
    
    payload = {
        "model": kwargs.get("model", self.default_model_name),
        "messages": messages,
        "temperature": kwargs.get("temperature", 0.7),
        "max_tokens": kwargs.get("max_tokens", self.default_max_tokens_chat)
    }
    
    # Add tools if provided
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = tool_choice
    
    # Handle different provider formats
    if self.is_openrouter:
        # OpenRouter supports OpenAI tool calling format
        pass
    elif self.is_ollama:
        # Convert to Ollama tool format if needed
        payload = self._convert_tools_for_ollama(payload)
    elif self.is_local_studio:
        # LM Studio supports OpenAI format
        pass
    
    response = await self._make_api_request(payload)
    return response

def _convert_tools_for_ollama(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Convert tool definitions for Ollama compatibility"""
    # Ollama may have different tool calling format
    # Implement conversion logic based on Ollama's current API
    return payload
```

### Step 2: Integrate with Vector Memory System

```python
# Add to src/memory/vector_memory_system.py

async def store_memory_with_intelligence(
    self, 
    user_id: str, 
    content: str, 
    memory_type: str = None,
    metadata: Dict[str, Any] = None
) -> str:
    """Store memory with LLM-driven optimization"""
    
    # Let LLM analyze and enhance the memory before storage
    enhancement_result = await self.intelligent_memory_manager.analyze_for_storage(
        content=content,
        user_id=user_id,
        existing_context=metadata or {}
    )
    
    # Apply LLM recommendations
    optimized_content = enhancement_result.get("optimized_content", content)
    suggested_tags = enhancement_result.get("tags", [])
    memory_type = enhancement_result.get("memory_type", memory_type)
    
    # Store with enhancements
    memory_id = await self.store_memory(
        user_id=user_id,
        content=optimized_content,
        memory_type=memory_type,
        metadata={
            **(metadata or {}),
            "llm_enhanced": True,
            "tags": suggested_tags,
            "importance": enhancement_result.get("importance", 5)
        }
    )
    
    # Execute any additional memory actions suggested by LLM
    for action in enhancement_result.get("additional_actions", []):
        await self.tool_manager.execute_tool(
            action["tool"], 
            action["parameters"], 
            user_id
        )
    
    return memory_id
```

### Step 3: Conversation Integration

```python
# Add to src/conversation/conversation_manager.py

async def process_conversation_with_memory_intelligence(
    self, 
    user_message: str, 
    user_id: str
) -> str:
    """Process conversation with intelligent memory management"""
    
    # Generate response normally
    bot_response = await self.generate_response(user_message, user_id)
    
    # Use LLM to analyze conversation for memory actions
    memory_actions = await self.intelligent_memory_manager.process_conversation_for_memory_actions(
        user_message=user_message,
        bot_response=bot_response,
        user_id=user_id,
        conversation_context=await self.get_conversation_context(user_id)
    )
    
    # Log memory actions for transparency
    if memory_actions:
        logger.info(f"Memory actions taken for user {user_id}: {len(memory_actions)} actions")
        for action in memory_actions:
            logger.debug(f"Memory action: {action['tool']} - {action['result'].get('message', 'Success')}")
    
    return bot_response
```

## 🎯 Use Cases & Benefits

### 1. **Proactive Fact Correction**
```
User: "Actually, my cat's name is Whiskers, not Mittens"
LLM Tool Call: update_memory_context(
    search_query="cat name",
    correction_content="User's cat is named Whiskers",
    update_reason="User provided correction",
    merge_strategy="replace"
)
```

### 2. **Intelligent Memory Organization**
```
User: "I got the promotion at work! I'll be the new senior developer."
LLM Tool Calls:
- store_semantic_memory(
    content="User got promoted to senior developer",
    memory_type="experience", 
    importance=8,
    tags=["work", "career", "achievement"]
)
- organize_related_memories(
    topic="work career",
    relationship_type="sequential"
)
```

### 3. **Contextual Memory Enhancement**
```
User: "Remember when we talked about React? I'm using it for that project now."
LLM Tool Call: enhance_memory_retrieval(
    memory_id="react_discussion_123",
    enhancement_type="add_context",
    enhancement_data={"current_usage": "active project", "relevance": "high"}
)
```

### 4. **Automatic Cleanup**
```
After 30 days of no React discussions:
LLM Tool Call: archive_outdated_memories(
    criteria="temporal",
    topic_filter="React discussion", 
    archive_reason="No recent activity, likely outdated",
    retention_period=90
)
```

## 🚀 Implementation Phases

### Phase 1: Foundation (1-2 weeks)
1. ✅ Enhance LLM client with tool calling support
2. ✅ Create VectorMemoryToolManager
3. ✅ Basic memory tools (store, update, organize)
4. ✅ Integration with existing conversation flow

### Phase 2: Intelligence (2-3 weeks)  
1. ✅ IntelligentMemoryManager for conversation analysis
2. ✅ Proactive memory optimization
3. ✅ Advanced memory relationship detection
4. ✅ Semantic clustering and organization

### Phase 3: Advanced Features (3-4 weeks)
1. ✅ Memory lifecycle management
2. ✅ Usage pattern analysis
3. ✅ Automatic memory archival
4. ✅ Cross-user memory insights (with privacy)

### Phase 4: Optimization (2-3 weeks)
1. ✅ Performance optimization for tool calling
2. ✅ Memory efficiency improvements  
3. ✅ Advanced semantic understanding
4. ✅ Multi-modal memory support

## 📊 Expected Benefits

### Memory Quality
- **40-60% improvement** in memory relevance through semantic organization
- **50-70% reduction** in outdated/incorrect information
- **30-50% better** cross-referencing and relationship detection

### User Experience  
- **Proactive error correction** without user intervention
- **Intelligent memory suggestions** during conversations
- **Seamless knowledge evolution** as user preferences change

### System Performance
- **20-30% improvement** in retrieval precision through better organization
- **Reduced storage bloat** through intelligent archival
- **Enhanced conversation continuity** through better context management

## 🔧 Configuration & Controls

### Environment Variables
```bash
# Enable/disable LLM memory management
VECTOR_LLM_MEMORY_MANAGEMENT=true
VECTOR_LLM_PROACTIVE_OPTIMIZATION=true
VECTOR_LLM_AUTO_ARCHIVAL=false

# Tool calling configuration
LLM_TOOL_CALLING_ENABLED=true
LLM_MEMORY_TOOL_TEMPERATURE=0.1
LLM_MEMORY_ANALYSIS_FREQUENCY=every_conversation

# Memory retention policies
VECTOR_AUTO_ARCHIVE_DAYS=30
VECTOR_PERMANENT_DELETE_DAYS=90
VECTOR_MAX_MEMORIES_PER_USER=10000
```

### Admin Controls
```python
# Disable for specific users
await memory_manager.set_llm_management(user_id, enabled=False)

# Review LLM memory actions
actions = await memory_manager.get_llm_actions_log(user_id, days=7)

# Rollback LLM memory changes
await memory_manager.rollback_llm_actions(user_id, action_ids=[...])
```

---

**This approach transforms WhisperEngine into a truly intelligent AI companion with self-optimizing memory that learns and adapts to each user's unique conversation patterns and preferences!** 🎯