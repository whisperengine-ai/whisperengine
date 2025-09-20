"""
Example of how to update handlers to use the unified memory manager interface.

This eliminates all the async/sync detection patterns and provides clean, 
consistent async calls.
"""

import asyncio
import logging
from typing import Optional

from src.memory.core.memory_interface import MemoryContext, MemoryContextType
from src.memory.core.memory_factory import create_memory_manager
from src.utils.exceptions import MemoryRetrievalError

logger = logging.getLogger(__name__)


class ModernizedEventHandler:
    """
    Example of how event handlers should look with the unified memory manager.
    
    Compare this to the old handlers with async/sync detection patterns.
    """
    
    def __init__(self, bot, memory_manager=None, emotion_manager=None, graph_manager=None):
        self.bot = bot
        
        # Create unified memory manager
        self.memory_manager = create_memory_manager(
            base_manager=memory_manager,
            emotion_manager=emotion_manager,
            graph_manager=graph_manager,
        )
        
        # Initialize async
        self._initialization_task = None
    
    async def initialize(self):
        """Initialize the handler asynchronously."""
        if self._initialization_task is None:
            self._initialization_task = asyncio.create_task(self.memory_manager.initialize())
        await self._initialization_task
    
    async def handle_dm_message(self, message):
        """
        Handle DM message with clean async memory operations.
        
        Compare this to the old version with async/sync detection chaos.
        """
        user_id = str(message.author.id)
        
        try:
            # Create context for DM
            context = MemoryContext(
                context_type=MemoryContextType.DM,
                channel_id=str(message.channel.id),
            )
            
            # OLD WAY (with async/sync detection):
            # ```python
            # if asyncio.iscoroutinefunction(self.memory_manager.retrieve_context_aware_memories):
            #     relevant_memories = await self.memory_manager.retrieve_context_aware_memories(...)
            # else:
            #     loop = asyncio.get_running_loop()
            #     relevant_memories = await loop.run_in_executor(...)
            # ```
            
            # NEW WAY (clean async interface):
            relevant_memories = await self.memory_manager.retrieve_memories(
                user_id=user_id,
                query=message.content,
                limit=20,
                context=context,
            )
            
            # OLD WAY (with async/sync detection):
            # ```python
            # if asyncio.iscoroutinefunction(self.memory_manager.get_emotion_context):
            #     emotion_context = await self.memory_manager.get_emotion_context(user_id)
            # else:
            #     loop = asyncio.get_running_loop()
            #     emotion_context = await loop.run_in_executor(...)
            # ```
            
            # NEW WAY (clean async interface):
            emotion_context = await self.memory_manager.get_emotion_context(
                user_id=user_id,
                context=context,
            )
            
            # Generate AI response (existing logic)
            ai_response = await self._generate_ai_response(
                message, relevant_memories, emotion_context
            )
            
            # Store conversation
            await self.memory_manager.store_conversation(
                user_id=user_id,
                user_message=message.content,
                bot_response=ai_response,
                context=context,
                emotion_data=emotion_context.to_dict(),
            )
            
            # Send response
            await message.channel.send(ai_response)
            
        except MemoryRetrievalError as e:
            logger.error(f"Memory retrieval failed for user {user_id}: {e}")
            # Graceful fallback
            await message.channel.send("I'm having trouble accessing my memory right now.")
        
        except Exception as e:
            logger.error(f"Unexpected error in DM handler: {e}")
            await message.channel.send("Something went wrong. Please try again.")
    
    async def handle_guild_message(self, message):
        """Handle guild message with proper context."""
        user_id = str(message.author.id)
        
        try:
            # Create context for guild
            context = MemoryContext(
                context_type=MemoryContextType.GUILD_PUBLIC,
                channel_id=str(message.channel.id),
                guild_id=str(message.guild.id) if message.guild else None,
            )
            
            # Clean async calls (no async/sync detection needed)
            relevant_memories = await self.memory_manager.retrieve_memories(
                user_id=user_id,
                query=message.content,
                limit=20,
                context=context,
            )
            
            emotion_context = await self.memory_manager.get_emotion_context(
                user_id=user_id,
                context=context,
            )
            
            # Rest of the handler logic...
            
        except Exception as e:
            logger.error(f"Guild message handler error: {e}")
    
    async def _generate_ai_response(self, message, memories, emotion_context):
        """Generate AI response using provided context."""
        # Existing AI response generation logic
        # Now with clean, typed context objects instead of mixed formats
        
        memory_context = "\n".join([
            f"- {entry.content} (score: {entry.score:.2f})"
            for entry in memories[:5]
        ])
        
        emotion_info = (
            f"Current emotion: {emotion_context.current_emotion} "
            f"(intensity: {emotion_context.emotion_intensity:.1f}), "
            f"Relationship: {emotion_context.relationship_level}"
        )
        
        # Use your existing LLM client
        prompt = f"""
        Context: {memory_context}
        Emotion: {emotion_info}
        User message: {message.content}
        
        Generate an appropriate response...
        """
        
        # Return generated response
        return "Sample AI response"


class ModernizedUniversalChat:
    """
    Example of how universal chat should look with unified memory manager.
    """
    
    def __init__(self, memory_manager=None, emotion_manager=None):
        self.memory_manager = create_memory_manager(
            base_manager=memory_manager,
            emotion_manager=emotion_manager,
        )
    
    async def process_message(self, message):
        """Process message with clean async interface."""
        user_id = message.user_id
        
        # Determine context based on message type
        if message.is_dm:
            context = MemoryContext(context_type=MemoryContextType.DM)
        else:
            context = MemoryContext(
                context_type=MemoryContextType.GUILD_PUBLIC,
                guild_id=message.guild_id,
                channel_id=message.channel_id,
            )
        
        # OLD WAY (universal_chat.py with async/sync detection):
        # ```python
        # emotion_method = getattr(memory_manager, "get_emotion_context", None)
        # if asyncio.iscoroutinefunction(emotion_method):
        #     emotion_context = await emotion_method(message.user_id)
        # else:
        #     loop = asyncio.get_running_loop()
        #     emotion_context = await loop.run_in_executor(...)
        # ```
        
        # NEW WAY (clean and simple):
        emotion_context = await self.memory_manager.get_emotion_context(
            user_id=user_id,
            context=context,
        )
        
        relevant_memories = await self.memory_manager.retrieve_memories(
            user_id=user_id,
            query=message.content,
            limit=10,
            context=context,
        )
        
        # Generate and store response
        response = await self._generate_response(message, relevant_memories, emotion_context)
        
        await self.memory_manager.store_conversation(
            user_id=user_id,
            user_message=message.content,
            bot_response=response,
            context=context,
            emotion_data=emotion_context.to_dict(),
        )
        
        return response
    
    async def _generate_response(self, message, memories, emotion_context):
        """Generate response with clean typed interfaces."""
        # Implementation here...
        return "Generated response"


# Migration example
async def migrate_existing_bot(old_bot):
    """
    Example of how to migrate an existing bot to use the unified memory manager.
    """
    
    # Extract components from old bot
    old_memory_manager = getattr(old_bot, 'memory_manager', None)
    emotion_manager = getattr(old_bot, 'emotion_manager', None)
    graph_manager = getattr(old_bot, 'graph_manager', None)
    
    # Create new unified manager
    new_memory_manager = create_memory_manager(
        base_manager=old_memory_manager,
        emotion_manager=emotion_manager,
        graph_manager=graph_manager,
    )
    
    # Initialize
    await new_memory_manager.initialize()
    
    # Replace in bot
    old_bot.memory_manager = new_memory_manager
    
    # Remove old wrapped managers
    if hasattr(old_bot, 'safe_memory_manager'):
        delattr(old_bot, 'safe_memory_manager')
    if hasattr(old_bot, 'context_memory_manager'):
        delattr(old_bot, 'context_memory_manager')
    
    logger.info("Bot migrated to unified memory manager")
    
    return old_bot