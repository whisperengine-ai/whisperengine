import logging
import traceback
import discord
from typing import Optional

from src.platforms.universal_chat import ChatPlatform
from src.security.system_message_security import scan_response_for_system_leakage

logger = logging.getLogger(__name__)


class ResponseGenerationService:
    def __init__(self, bot_core):
        self.bot_core = bot_core
        self.bot = bot_core.bot
        self.memory_manager = bot_core.memory_manager
        self.llm_client = bot_core.llm_client
        # chat_orchestrator will be set later by the event handlers
        self.chat_orchestrator = getattr(bot_core, 'chat_orchestrator', None)
    
    def set_chat_orchestrator(self, chat_orchestrator):
        """Set the chat orchestrator after it's initialized by event handlers"""
        self.chat_orchestrator = chat_orchestrator
        
    async def generate_and_send_response(
        self,
        reply_channel,
        message,
        user_id,
        conversation_context,
        current_emotion_data,
        external_emotion_data,
        phase2_context,
        phase4_context=None,
        comprehensive_context=None,
        dynamic_personality_context=None,
        phase3_context_switches=None,
        phase3_empathy_calibration=None,
        original_content=None,
    ) -> Optional[str]:
        """Generate AI response and send to channel - implemented service version."""
        # Show typing indicator
        async with reply_channel.typing():
            logger.info(f"[RESPONSE-SERVICE] Starting response generation for user {user_id}")
            
            try:
                # Use Universal Chat Orchestrator if available
                if self.chat_orchestrator:
                    logger.info("[RESPONSE-SERVICE] Using Universal Chat Orchestrator")
                    
                    # Convert Discord message to universal format
                    if (hasattr(self.chat_orchestrator, "adapters") 
                        and ChatPlatform.DISCORD in self.chat_orchestrator.adapters):
                        
                        discord_adapter = self.chat_orchestrator.adapters[ChatPlatform.DISCORD]
                        universal_message = discord_adapter.discord_message_to_universal_message(message)

                        # Generate response through orchestrator
                        ai_response = await self.chat_orchestrator.generate_ai_response(
                            universal_message, conversation_context
                        )
                        
                        # Extract the text content from the AIResponse object
                        response = ai_response.content if hasattr(ai_response, 'content') else str(ai_response)
                        
                        logger.info(f"✅ Generated response of {len(response) if response else 0} characters")
                    else:
                        logger.error("Discord adapter not found in chat orchestrator")
                        response = "I'm sorry, I encountered an issue processing your message."
                else:
                    logger.error("Universal Chat Orchestrator is not available.")
                    response = "I'm sorry, the chat system is not properly configured."

                if not response:
                    logger.error(f"Response is empty for user {user_id}")
                    response = "I received your message but couldn't generate a response."

                # Apply security scanning
                leakage_scan = scan_response_for_system_leakage(response)
                if leakage_scan["has_leakage"]:
                    logger.error(f"SECURITY: System message leakage detected in response to user {user_id}")
                    response = leakage_scan["sanitized_response"]

                # Send response to Discord
                sent_message = await reply_channel.send(response)
                logger.info(f"✅ Response sent to channel {reply_channel.id}")

                # Store conversation memory (simplified for now)
                if self.memory_manager:
                    await self.memory_manager.store_conversation(
                        user_id=user_id,
                        user_message=original_content if original_content else message.content,
                        bot_response=response,
                        pre_analyzed_emotion_data={
                            'current_emotion': current_emotion_data,
                            'external_emotion': external_emotion_data,
                            'phase2_context': phase2_context,
                        }
                    )

                logger.info(f"[RESPONSE-SERVICE] Completed response generation for user {user_id}")
                return response

            except discord.HTTPException as e:
                logger.error(f"Discord HTTP error sending message: {e}")
                await reply_channel.send("I encountered an issue sending the message. Please try again.")
                return None
            except Exception as e:
                logger.error(f"Unexpected error in response generation: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                try:
                    await reply_channel.send("I encountered an unexpected error. Please try again.")
                except:
                    logger.error("Failed to send error message")
                return None
