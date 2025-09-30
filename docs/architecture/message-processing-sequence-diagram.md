# Message Processing Sequence Diagram

This sequence diagram illustrates the data flow from an incoming message to a response in the WhisperEngine system, showing how messages are processed through various components.

```mermaid
sequenceDiagram
    participant User
    participant DiscordInterface as Discord Interface
    participant BotEventHandlers as Bot Event Handlers
    participant SecurityValidator as Security Validator
    participant MemoryManager as Memory Manager
    participant CDLIntegration as CDL Integration
    participant PromptBuilder as Prompt Builder
    participant ContextDetector as Context Detector
    participant LLMClient as LLM Client
    participant ConsistencyValidator as Consistency Validator
    participant StorageManager as Storage Manager

    User->>DiscordInterface: Send message
    DiscordInterface->>BotEventHandlers: Process message event
    
    %% Security Validation
    BotEventHandlers->>SecurityValidator: Validate message content
    SecurityValidator-->>BotEventHandlers: Validation result
    alt If validation fails
        BotEventHandlers-->>DiscordInterface: Error response
        DiscordInterface-->>User: Display error
    end
    
    %% Memory Retrieval
    BotEventHandlers->>MemoryManager: retrieve_relevant_memories(user_id, query, limit)
    MemoryManager->>MemoryManager: Vector semantic search
    MemoryManager-->>BotEventHandlers: Relevant memories
    
    %% Conversation History
    BotEventHandlers->>MemoryManager: get_conversation_history(user_id, limit)
    MemoryManager-->>BotEventHandlers: Recent conversation
    
    %% Character Enhancement
    BotEventHandlers->>CDLIntegration: create_character_aware_prompt(character_file, user_id, message)
    CDLIntegration->>CDLIntegration: Load character data from JSON
    CDLIntegration->>CDLIntegration: Apply personality traits
    CDLIntegration-->>BotEventHandlers: Character-enhanced system prompt
    
    %% Fidelity-First Prompt Building
    BotEventHandlers->>PromptBuilder: build_optimized_prompt(system_prompt, conversation_context, user_message)
    PromptBuilder->>PromptBuilder: Assemble complete context
    PromptBuilder->>PromptBuilder: Apply graduated optimization if needed
    PromptBuilder-->>BotEventHandlers: Optimized prompt
    
    %% Context Detection
    BotEventHandlers->>ContextDetector: detect_context_patterns(message, history)
    ContextDetector->>ContextDetector: Vector-enhanced pattern recognition
    ContextDetector-->>BotEventHandlers: Context analysis
    
    %% LLM Generation
    BotEventHandlers->>LLMClient: generate_response(prompt)
    LLMClient->>LLMClient: Send to appropriate model
    LLMClient-->>BotEventHandlers: Generated response
    
    %% Character Consistency Validation
    BotEventHandlers->>ConsistencyValidator: validate_character_consistency(response, character_data)
    ConsistencyValidator-->>BotEventHandlers: Validation result
    
    %% Memory Storage
    BotEventHandlers->>StorageManager: store_conversation(user_id, user_message, bot_response, emotion_data)
    StorageManager->>StorageManager: Generate vector embeddings
    StorageManager->>StorageManager: Store with named vectors
    StorageManager-->>BotEventHandlers: Storage confirmation
    
    %% Response Delivery
    BotEventHandlers-->>DiscordInterface: Final response
    DiscordInterface-->>User: Display response
```

## Detailed Flow Explanation

1. **Initial Message Handling**
   - User sends a message through Discord
   - Discord interface receives the message and forwards to event handlers
   - Event handlers begin processing the message

2. **Security Validation**
   - Message is validated against security policies
   - If validation fails, error response is returned to user
   - If validation passes, processing continues

3. **Memory Retrieval**
   - System retrieves relevant memories using vector semantic search
   - Conversation history is fetched to provide immediate context
   - Both long-term memories and recent conversation provide context

4. **Character Enhancement**
   - CDL Integration loads character data from JSON definition
   - Character personality traits are applied to create a character-aware prompt
   - System prompt is enhanced with character-specific context

5. **Prompt Building**
   - Optimized prompt builder assembles complete context
   - Fidelity-first approach preserves character nuance
   - Graduated optimization applied only if context limit is exceeded

6. **Context Detection**
   - Vector-enhanced pattern recognition analyzes message content
   - Conversation context is determined for appropriate response framing
   - Analysis results inform the response generation

7. **LLM Response Generation**
   - Complete prompt is sent to appropriate LLM model
   - LLM generates response based on provided context and character
   - Generated response is returned to handlers

8. **Consistency Validation**
   - Response is validated for character consistency
   - Ensures the generated content aligns with character personality
   - Validation result determines if response needs adjustment

9. **Memory Storage**
   - Conversation is stored with emotional context for future retrieval
   - Vector embeddings are generated for content, emotion, and semantics
   - Named vectors are stored in Qdrant with bot-specific segmentation

10. **Response Delivery**
    - Final response is returned to Discord interface
    - Discord displays the response to the user
    - Conversation cycle completes

## Key Architectural Patterns

- **Fidelity-First Processing**: Full context preservation until optimization is necessary
- **Vector-Native Operations**: Semantic processing uses existing Qdrant infrastructure
- **Character Consistency**: CDL system ensures authentic personality responses
- **Bot-Specific Memory Isolation**: Memories are segmented by bot name
- **Named Vector Architecture**: Multi-dimensional search with content/emotion/semantic vectors
