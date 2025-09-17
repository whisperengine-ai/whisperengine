#!/usr/bin/env python3
"""
Discord Visual Emotion Handler - Sprint 6

This module implements Discord-specific handlers for visual emotion analysis,
integrating with WhisperEngine's existing Discord bot infrastructure and
emotional intelligence systems.

Key Features:
- Discord image upload handling
- Visual emotion analysis integration  
- Multi-modal emotion fusion
- Privacy-compliant processing
- User commands and statistics
"""

import discord
import logging
import os
import random
from typing import Dict, Any, Optional
from datetime import datetime

from src.emotion.visual_emotion_processor import create_visual_emotion_processor
from src.emotion.visual_emotion_models import (
    VisualEmotionAnalysis, 
    VisualEmotionConfig,
    VisualEmotionCategory,
    EnhancedEmotionalState,
    FusedEmotion
)

logger = logging.getLogger(__name__)


class DiscordVisualEmotionHandler:
    """Discord-specific handler for visual emotion analysis"""
    
    def __init__(self, bot, **dependencies):
        self.bot = bot
        self.llm_client = dependencies.get('llm_client')
        self.memory_manager = dependencies.get('memory_manager')
        
        # Initialize visual emotion processor
        deployment_mode = os.getenv('ENV_MODE', 'development')
        self.emotion_processor = create_visual_emotion_processor(deployment_mode)
        
        # Load configuration
        self.config = self._load_config()
        
        # Performance tracking
        self.stats = {
            'images_processed': 0,
            'emotions_detected': 0,
            'responses_generated': 0,
            'processing_time_total': 0
        }
        
        logger.info("🖼️ Discord Visual Emotion Handler initialized")
        
        # Register event handlers
        self._register_handlers()
    
    def _load_config(self) -> VisualEmotionConfig:
        """Load visual emotion configuration from environment"""
        config = VisualEmotionConfig()
        
        # Load from environment variables
        config.enabled = os.getenv('ENABLE_VISUAL_EMOTION_ANALYSIS', 'true').lower() == 'true'
        config.discord_enabled = os.getenv('DISCORD_VISUAL_EMOTION_ENABLED', 'true').lower() == 'true'
        config.generate_responses = os.getenv('DISCORD_VISUAL_RESPONSE_ENABLED', 'true').lower() == 'true'
        config.add_emoji_reactions = os.getenv('DISCORD_VISUAL_REACTION_ENABLED', 'true').lower() == 'true'
        config.confidence_threshold = float(os.getenv('VISUAL_EMOTION_CONFIDENCE_THRESHOLD', '0.6'))
        config.max_image_size_mb = int(os.getenv('VISUAL_EMOTION_MAX_IMAGE_SIZE', '10'))
        config.response_probability = float(os.getenv('DISCORD_VISUAL_RESPONSE_PROBABILITY', '0.7'))
        
        return config
    
    def _register_handlers(self):
        """Register Discord event handlers for image processing"""
        
        # IMPORTANT: Do NOT override the core bot on_message handler. Using @self.bot.event here
        # would replace the primary event pipeline (responses, commands, memory, etc.).
        # Instead we register an additional listener so the main handler in events.py still runs.

        async def visual_emotion_on_message(message):
            """Passive listener for messages to extract visual emotional signals.

            This listener is additive only: it never blocks or returns early to change normal
            processing. The main on_message handler (BotEventHandlers.on_message) remains intact.
            """
            try:
                if not self.config.enabled or not self.config.discord_enabled:
                    return
                if message.author.bot:
                    return

                # Only act if there are attachments that might be images
                if message.attachments:
                    await self._process_message_attachments(message)
            except Exception as e:
                logger.warning("Visual emotion listener error (non-fatal): %s", e)

        # Register additive listener
        self.bot.add_listener(visual_emotion_on_message, 'on_message')
        logger.info("✅ Visual emotion listener registered (non-intrusive)")
    
    async def _process_message_attachments(self, message: discord.Message):
        """Process all image attachments in a message"""
        
        for attachment in message.attachments:
            if self._is_processable_image(attachment):
                try:
                    await self._analyze_image_attachment(attachment, message)
                    self.stats['images_processed'] += 1
                except Exception as e:
                    logger.error("Error processing image attachment: %s", e)
                    # Graceful degradation - continue processing
    
    def _is_processable_image(self, attachment: discord.Attachment) -> bool:
        """Check if attachment is a processable image"""
        
        # Check file extension
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        filename_lower = attachment.filename.lower()
        
        if not any(filename_lower.endswith(ext) for ext in valid_extensions):
            return False
        
        # Check file size
        max_size_bytes = self.config.max_image_size_mb * 1024 * 1024
        if attachment.size > max_size_bytes:
            logger.warning("Image too large: %d bytes > %d bytes", attachment.size, max_size_bytes)
            return False
        
        return True
    
    async def _analyze_image_attachment(self, attachment: discord.Attachment, message: discord.Message):
        """Analyze a single image attachment for emotional content"""
        
        # Download image data (temporary only)
        try:
            image_data = await attachment.read()
        except Exception as e:
            logger.error("Failed to download image: %s", e)
            return
        
        # Prepare context for analysis
        context = {
            'user_id': str(message.author.id),
            'channel_id': str(message.channel.id),
            'guild_id': str(message.guild.id) if message.guild else None,
            'message_id': str(message.id),
            'message_text': message.content,
            'timestamp': message.created_at,
            'filename': attachment.filename
        }
        logger.info(f"[VISUAL-CTX] Processing image message_id={message.id} user_id={message.author.id} channel_id={message.channel.id} guild_id={getattr(message.guild, 'id', None)} text='{message.content[:60]}' context={context}")
        
        # Perform visual emotion analysis
        analysis = await self.emotion_processor.analyze_image(image_data, context)
        
        if analysis and analysis.emotion_confidence >= self.config.confidence_threshold:
            logger.info(f"[VISUAL-CTX] Analysis complete for message_id={message.id} user_id={message.author.id} emotions={analysis.primary_emotions} confidence={analysis.emotion_confidence}")
            # Update statistics
            self.stats['emotions_detected'] += len(analysis.primary_emotions)
            self.stats['processing_time_total'] += analysis.processing_time_ms
            
            # Store emotion memory (NOT the image)
            if self.memory_manager:
                await self._store_visual_emotion_memory(analysis, message)
            
            # Update user's emotional context
            logger.info(f"[VISUAL-CTX] Updating emotional context for message_id={message.id} user_id={message.author.id}")
            await self._update_emotional_context(analysis, message)
            
            # Generate contextual response if enabled
            if self.config.generate_responses and self._should_generate_response():
                logger.info(f"[VISUAL-CTX] Generating response for message_id={message.id} user_id={message.author.id}")
                await self._generate_visual_emotion_response(analysis, message)
                self.stats['responses_generated'] += 1
            
            # Add emoji reaction if enabled
            if self.config.add_emoji_reactions:
                await self._add_emotional_reaction(analysis, message)
        
        else:
            logger.debug("Visual analysis below confidence threshold or failed")
    
    def _should_generate_response(self) -> bool:
        """Determine if we should generate a response (probability-based)"""
        return random.random() < self.config.response_probability
    
    async def _store_visual_emotion_memory(self, analysis: VisualEmotionAnalysis, message: discord.Message):
        """Store visual emotion analysis as memory (privacy-compliant)"""
        
        from src.emotion.visual_emotion_models import VisualEmotionMemory
        
        # Create privacy-compliant memory entry
        memory_entry = VisualEmotionMemory(
            user_id=analysis.user_id,
            emotional_summary=analysis.get_emotion_summary(),
            dominant_emotion=analysis.dominant_emotion or VisualEmotionCategory.JOY,
            emotional_intensity=analysis.emotional_intensity,
            scene_description=analysis.scene_description,
            image_type=analysis.image_type,
            associated_text=analysis.text_context,
            emotional_impact_score=analysis.emotional_resonance_score,
            privacy_level=analysis.privacy_level,
            contains_faces=analysis.contains_faces,
            processing_mode=analysis.processing_mode
        )
        
        # Store using existing memory system (if available)
        if hasattr(self.memory_manager, 'store_visual_emotion_memory'):
            await self.memory_manager.store_visual_emotion_memory(memory_entry)
        else:
            logger.warning("Memory manager does not support visual emotion storage yet")
    
    async def _update_emotional_context(self, analysis: VisualEmotionAnalysis, message: discord.Message):
        """Update user's emotional context with visual analysis"""
        
        try:
            # For now, just use visual emotions (text fusion can be added later)
            enhanced_emotional_state = self._create_visual_emotional_state(analysis, message)
            
            # Update memory with enhanced emotional context (if memory manager supports it)
            if self.memory_manager and hasattr(self.memory_manager, 'update_emotional_context'):
                await self.memory_manager.update_emotional_context(
                    str(message.author.id),
                    enhanced_emotional_state
                )
        
        except Exception as e:
            logger.error("Error updating emotional context: %s", e)
    
    def _create_visual_emotional_state(self, analysis: VisualEmotionAnalysis, message: discord.Message) -> EnhancedEmotionalState:
        """Create enhanced emotional state from visual analysis only"""
        
        fused_emotions = []
        
        # Convert visual emotions to fused emotions
        for v_emotion in analysis.primary_emotions:
            fused_emotion = FusedEmotion(
                emotion=v_emotion.emotion,
                intensity=v_emotion.intensity,
                confidence=v_emotion.confidence,
                sources=['visual'],
                visual_intensity=v_emotion.intensity,
                text_intensity=None
            )
            fused_emotions.append(fused_emotion)
        
        # Create enhanced emotional state
        enhanced_state = EnhancedEmotionalState(
            emotions=fused_emotions,
            dominant_emotion=analysis.dominant_emotion or VisualEmotionCategory.JOY,
            multimodal_confidence=analysis.emotion_confidence,
            visual_context=analysis.scene_description,
            text_context=message.content,
            processing_components=['visual_emotion_analysis']
        )
        
        return enhanced_state
    
    async def _generate_visual_emotion_response(self, analysis: VisualEmotionAnalysis, message: discord.Message):
        """Generate AI response acknowledging visual emotions"""
        
        try:
            # Build visual emotion context for prompt
            visual_context = self._build_visual_context_description(analysis, message)
            
            # Get comprehensive context if memory manager available
            comprehensive_context = None
            if self.memory_manager and hasattr(self.memory_manager, 'get_comprehensive_context'):
                try:
                    comprehensive_context = await self.memory_manager.get_comprehensive_context(
                        str(message.author.id),
                        str(message.channel.id),
                        include_visual_emotions=True
                    )
                except Exception as e:
                    logger.warning("Could not get comprehensive context: %s", e)
            
            # Generate response using LLM
            if self.llm_client:
                response = await self._generate_llm_response(
                    visual_context, message, comprehensive_context
                )
                
                if response and len(response.strip()) > 0:
                    await message.channel.send(response)
            else:
                # Fallback response if no LLM client
                fallback_response = self._generate_fallback_response(analysis)
                await message.channel.send(fallback_response)
                
        except Exception as e:
            logger.error("Error generating visual emotion response: %s", e)
    
    def _build_visual_context_description(self, analysis: VisualEmotionAnalysis, message: discord.Message) -> str:
        """Build a description of the visual context for the LLM"""
        
        visual_context = f"""The user shared an image showing: {analysis.scene_description}

Visual Analysis:
- Detected emotions: {analysis.get_emotion_summary()}
- Image type: {analysis.image_type.value}
- Emotional intensity: {analysis.emotional_intensity:.2f}
- People detected: {analysis.people_count}
- Processing mode: {analysis.processing_mode.value}
- Privacy level: {analysis.privacy_level.value}

User's message: "{message.content if message.content else '[image only]'}"
"""
        return visual_context
    
    async def _generate_llm_response(self, visual_context: str, message: discord.Message, 
                                   comprehensive_context: Optional[Dict] = None) -> Optional[str]:
        """Generate response using LLM with visual context"""
        
        try:
            # Use adaptive prompt system
            from src.utils.helpers import get_contextualized_system_prompt
            
            system_prompt = get_contextualized_system_prompt(
                comprehensive_context=comprehensive_context,
                user_id=str(message.author.id)
            )
            
            # Include visual context in the user message
            user_message = f"{visual_context}\\n\\nUser message: {message.content if message.content else '[shared an image]'}"
            
            # Generate response (with null checks)
            if self.llm_client and hasattr(self.llm_client, 'generate_response'):
                response = await self.llm_client.generate_response(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    user_id=str(message.author.id)
                )
                return response
            else:
                logger.warning("LLM client not available for visual emotion response")
                return None
            
        except Exception as e:
            logger.error("LLM response generation failed: %s", e)
            return None
    
    def _generate_fallback_response(self, analysis: VisualEmotionAnalysis) -> str:
        """Generate a simple fallback response without LLM"""
        
        emotion_responses = {
            VisualEmotionCategory.JOY: "I can see the happiness in your image! 😊",
            VisualEmotionCategory.SADNESS: "I notice some sadness in what you've shared. 💙",
            VisualEmotionCategory.AWE: "What an amazing image! I'm in awe! 😍",
            VisualEmotionCategory.PRIDE: "You look proud in this image! 👏",
            VisualEmotionCategory.NOSTALGIA: "This brings back memories, doesn't it? 🥺"
        }
        
        if analysis.dominant_emotion:
            response = emotion_responses.get(
                analysis.dominant_emotion, 
                f"I can sense the {analysis.dominant_emotion.value} in your image."
            )
        else:
            response = "Thanks for sharing that image with me!"
        
        return response
    
    async def _add_emotional_reaction(self, analysis: VisualEmotionAnalysis, message: discord.Message):
        """Add emoji reaction based on detected emotions"""
        
        # Map emotions to emoji reactions
        emotion_emoji_map = {
            VisualEmotionCategory.JOY: '😊',
            VisualEmotionCategory.SADNESS: '😢',
            VisualEmotionCategory.ANGER: '😠',
            VisualEmotionCategory.FEAR: '😨',
            VisualEmotionCategory.SURPRISE: '😮',
            VisualEmotionCategory.DISGUST: '🤢',
            VisualEmotionCategory.CONTEMPT: '🙄',
            VisualEmotionCategory.TRUST: '🤗',
            VisualEmotionCategory.ANTICIPATION: '🤩',
            VisualEmotionCategory.NOSTALGIA: '🥺',
            VisualEmotionCategory.AWE: '😍',
            VisualEmotionCategory.EMBARRASSMENT: '😳',
            VisualEmotionCategory.PRIDE: '👏',
            VisualEmotionCategory.SHAME: '😔',
            VisualEmotionCategory.GUILT: '😞'
        }
        
        if analysis.dominant_emotion:
            emoji = emotion_emoji_map.get(analysis.dominant_emotion)
            if emoji:
                try:
                    await message.add_reaction(emoji)
                except discord.Forbidden:
                    logger.debug("No permission to add reactions")
                except Exception as e:
                    logger.warning("Error adding emoji reaction: %s", e)
    
    def _fuse_visual_text_emotions(self, visual_analysis: VisualEmotionAnalysis, 
                                 text_emotions, message: discord.Message) -> EnhancedEmotionalState:
        """Combine visual and text emotional analysis"""
        
        fused_emotions = []
        
        # Process visual emotions
        for v_emotion in visual_analysis.primary_emotions:
            # Check if text analysis has similar emotion
            text_match = self._find_matching_text_emotion(v_emotion.emotion, text_emotions) if text_emotions else None
            
            if text_match:
                # Combine visual and text intensities (favor visual for images)
                combined_intensity = (v_emotion.intensity * 0.7 + text_match.intensity * 0.3)
                combined_confidence = min(v_emotion.confidence * 1.2, 1.0)  # Boost for multi-modal
                sources = ['visual', 'text']
                text_intensity = text_match.intensity
            else:
                # Visual-only emotion
                combined_intensity = v_emotion.intensity
                combined_confidence = v_emotion.confidence
                sources = ['visual']
                text_intensity = None
            
            fused_emotion = FusedEmotion(
                emotion=v_emotion.emotion,
                intensity=combined_intensity,
                confidence=combined_confidence,
                sources=sources,
                visual_intensity=v_emotion.intensity,
                text_intensity=text_intensity
            )
            
            fused_emotions.append(fused_emotion)
        
        # Create enhanced emotional state
        enhanced_state = EnhancedEmotionalState(
            emotions=fused_emotions,
            dominant_emotion=visual_analysis.dominant_emotion or VisualEmotionCategory.JOY,
            multimodal_confidence=visual_analysis.emotion_confidence,
            visual_context=visual_analysis.scene_description,
            text_context=message.content,
            processing_components=['visual_emotion_analysis']
        )
        
        if text_emotions:
            enhanced_state.processing_components.append('text_emotion_analysis')
        
        return enhanced_state
    
    def _find_matching_text_emotion(self, visual_emotion: VisualEmotionCategory, text_emotions) -> Optional[Any]:
        """Find matching emotion in text analysis results"""
        
        # Basic emotion mapping (would be more sophisticated in practice)
        emotion_mapping = {
            VisualEmotionCategory.JOY: ['happiness', 'joy', 'pleased'],
            VisualEmotionCategory.SADNESS: ['sadness', 'sad', 'melancholy'],
            VisualEmotionCategory.ANGER: ['anger', 'angry', 'frustrated'],
            VisualEmotionCategory.FEAR: ['fear', 'scared', 'anxious'],
            VisualEmotionCategory.SURPRISE: ['surprise', 'surprised', 'shocked']
        }
        
        if not text_emotions or not hasattr(text_emotions, 'emotions'):
            return None
        
        visual_emotion_keywords = emotion_mapping.get(visual_emotion, [])
        
        for emotion in text_emotions.emotions:
            emotion_type = getattr(emotion, 'emotion_type', '').lower()
            if emotion_type in visual_emotion_keywords:
                return emotion
        
        return None
    
    def register_commands(self, bot_name_filter, is_admin):
        """Register Discord commands for visual emotion features"""
        
        @self.bot.command(name='visual_emotions')
        @bot_name_filter()
        async def toggle_visual_emotions(ctx, enabled: Optional[str] = None):
            """Toggle visual emotion analysis for the current user"""
            
            if not is_admin(ctx):
                await ctx.send("❌ This command requires admin permissions.")
                return
            
            if enabled is None:
                # Show current status
                current_status = "enabled" if self.config.discord_enabled else "disabled"
                await ctx.send(f"Visual emotion analysis is currently **{current_status}**.")
                return
            
            if enabled.lower() in ['on', 'true', 'enable', 'yes']:
                self.config.discord_enabled = True
                await ctx.send("✅ Visual emotion analysis **enabled**. I'll now analyze emotions in your images!")
            elif enabled.lower() in ['off', 'false', 'disable', 'no']:
                self.config.discord_enabled = False
                await ctx.send("❌ Visual emotion analysis **disabled**. I'll skip analyzing your images.")
            else:
                await ctx.send("Usage: `!visual_emotions [on/off]`")
        
        @self.bot.command(name='visual_stats')
        async def visual_emotion_stats(ctx):
            """Show visual emotion analysis statistics"""
            
            user_id = str(ctx.author.id)
            
            # Get basic statistics
            stats_embed = discord.Embed(
                title="📊 Visual Emotion Statistics",
                color=discord.Color.blue()
            )
            
            # System stats
            avg_processing_time = (self.stats['processing_time_total'] / max(self.stats['images_processed'], 1))
            
            stats_embed.add_field(
                name="🖼️ System Stats",
                value=f"Images processed: {self.stats['images_processed']}\\n"
                      f"Emotions detected: {self.stats['emotions_detected']}\\n"
                      f"Responses generated: {self.stats['responses_generated']}\\n"
                      f"Avg processing time: {avg_processing_time:.1f}ms",
                inline=False
            )
            
            # Configuration
            config_status = "✅ Enabled" if self.config.enabled and self.config.discord_enabled else "❌ Disabled"
            stats_embed.add_field(
                name="⚙️ Configuration",
                value=f"Status: {config_status}\\n"
                      f"Confidence threshold: {self.config.confidence_threshold}\\n"
                      f"Max image size: {self.config.max_image_size_mb}MB\\n"
                      f"Auto responses: {'Yes' if self.config.generate_responses else 'No'}",
                inline=False
            )
            
            await ctx.send(embed=stats_embed)
        
        @self.bot.command(name='visual_admin')
        @bot_name_filter()
        async def visual_emotion_admin(ctx, action: Optional[str] = None):
            """Admin commands for visual emotion system"""
            
            if not is_admin(ctx):
                await ctx.send("❌ This command requires admin permissions.")
                return
            
            if action == "stats":
                # Global statistics
                await ctx.send(f"""📊 **Global Visual Emotion Statistics:**
- Images processed: {self.stats['images_processed']}
- Total emotions detected: {self.stats['emotions_detected']} 
- Responses generated: {self.stats['responses_generated']}
- Total processing time: {self.stats['processing_time_total']}ms""")
            
            elif action == "config":
                # Show current configuration
                config_info = f"""**Visual Emotion Configuration:**
- System enabled: {self.config.enabled}
- Discord integration: {self.config.discord_enabled}
- Auto responses: {self.config.generate_responses}
- Emoji reactions: {self.config.add_emoji_reactions}
- Confidence threshold: {self.config.confidence_threshold}
- Max image size: {self.config.max_image_size_mb}MB
- Response probability: {self.config.response_probability}
- Processing mode: {self.emotion_processor.deployment_mode}"""
                await ctx.send(config_info)
            
            elif action == "test":
                # Test the visual emotion system
                await ctx.send("🧪 Visual emotion system is ready! Upload an image to test it.")
            
            else:
                await ctx.send("Usage: `!visual_admin [stats/config/test]`")


# Factory function for handler creation
def create_discord_visual_emotion_handler(bot, **dependencies) -> DiscordVisualEmotionHandler:
    """Factory function to create Discord visual emotion handler"""
    return DiscordVisualEmotionHandler(bot, **dependencies)