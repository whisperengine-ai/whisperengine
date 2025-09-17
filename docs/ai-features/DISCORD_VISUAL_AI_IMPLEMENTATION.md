# 📱 Discord Visual AI Implementation Plan - Sprint 6

## 🎯 Implementation Overview

This document outlines the complete implementation plan for Discord visual emotional AI, respecting WhisperEngine's privacy-first architecture and integrating seamlessly with existing emotional intelligence systems.

## 🔒 Privacy-First Architecture Compliance

### **Deployment Mode Handling**
- **Cloud Mode**: Full Discord integration with visual emotion analysis
- **Desktop Mode**: No Discord connectivity - purely local visual processing 
- **Demo Mode**: Trial Discord integration with clear data lifecycle warnings

### **Data Flow Privacy**
```
Discord Image Upload → Temporary Processing → Emotion Analysis → Response Generation
                                    ↓
                              NO PERMANENT IMAGE STORAGE
                                    ↓
                         Privacy-Compliant Memory Entry Only
```

## 🏗️ Core Implementation Components

### **1. Discord Image Handler Integration**

```python
# src/handlers/discord_visual_emotion_handler.py
import discord
from discord.ext import commands
from src.emotion.visual_emotion_models import VisualEmotionAnalysis, VisualEmotionConfig
from src.emotion.visual_emotion_processor import VisualEmotionProcessor
from src.utils.helpers import get_contextualized_system_prompt
from src.memory.context_aware_memory_security import ContextAwareMemoryManager


class DiscordVisualEmotionHandler:
    """Discord-specific handler for visual emotion analysis"""
    
    def __init__(self, bot, **dependencies):
        self.bot = bot
        self.llm_client = dependencies['llm_client']
        self.memory_manager = dependencies['memory_manager']
        self.emotion_processor = VisualEmotionProcessor(
            deployment_mode=os.getenv('ENV_MODE', 'development')
        )
        self.config = VisualEmotionConfig()
        
        # Load configuration from environment
        self._load_config_from_env()
        
        # Register event handlers
        self._register_handlers()
    
    def _load_config_from_env(self):
        """Load visual emotion configuration from environment variables"""
        self.config.enabled = os.getenv('ENABLE_VISUAL_EMOTION_ANALYSIS', 'true').lower() == 'true'
        self.config.discord_enabled = os.getenv('DISCORD_VISUAL_EMOTION_ENABLED', 'true').lower() == 'true'
        self.config.generate_responses = os.getenv('DISCORD_VISUAL_RESPONSE_ENABLED', 'true').lower() == 'true'
        self.config.add_emoji_reactions = os.getenv('DISCORD_VISUAL_REACTION_ENABLED', 'true').lower() == 'true'
        self.config.confidence_threshold = float(os.getenv('VISUAL_EMOTION_CONFIDENCE_THRESHOLD', '0.6'))
        self.config.max_image_size_mb = int(os.getenv('VISUAL_EMOTION_MAX_IMAGE_SIZE', '10'))
    
    def _register_handlers(self):
        """Register Discord event handlers for image processing"""
        
        @self.bot.event
        async def on_message(message):
            """Handle incoming messages with image attachments"""
            if not self.config.enabled or not self.config.discord_enabled:
                return
            
            # Skip bot messages
            if message.author.bot:
                return
            
            # Check for image attachments
            if message.attachments:
                await self._process_message_attachments(message)
    
    async def _process_message_attachments(self, message: discord.Message):
        """Process all image attachments in a message"""
        for attachment in message.attachments:
            if self._is_processable_image(attachment):
                try:
                    await self._analyze_image_attachment(attachment, message)
                except Exception as e:
                    logger.error(f"Error processing image attachment: {e}")
                    # Graceful degradation - continue with text-only processing
    
    def _is_processable_image(self, attachment: discord.Attachment) -> bool:
        """Check if attachment is a processable image"""
        # Check file extension
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        file_ext = attachment.filename.lower().split('.')[-1]
        if f'.{file_ext}' not in valid_extensions:
            return False
        
        # Check file size
        if attachment.size > (self.config.max_image_size_mb * 1024 * 1024):
            return False
        
        return True
    
    async def _analyze_image_attachment(self, attachment: discord.Attachment, message: discord.Message):
        """Analyze a single image attachment for emotional content"""
        
        # Download image data (temporary only)
        try:
            image_data = await attachment.read()
        except Exception as e:
            logger.error(f"Failed to download image: {e}")
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
        
        # Perform visual emotion analysis
        analysis = await self.emotion_processor.analyze_image(image_data, context)
        
        if analysis and analysis.emotion_confidence >= self.config.confidence_threshold:
            # Store emotion memory (NOT the image)
            await self._store_visual_emotion_memory(analysis, message)
            
            # Update user's emotional context
            await self._update_emotional_context(analysis, message)
            
            # Generate contextual response if enabled
            if self.config.generate_responses:
                await self._generate_visual_emotion_response(analysis, message)
            
            # Add emoji reaction if enabled
            if self.config.add_emoji_reactions:
                await self._add_emotional_reaction(analysis, message)
    
    async def _store_visual_emotion_memory(self, analysis: VisualEmotionAnalysis, message: discord.Message):
        """Store visual emotion analysis as memory (privacy-compliant)"""
        from src.emotion.visual_emotion_models import VisualEmotionMemory
        
        # Create privacy-compliant memory entry
        memory_entry = VisualEmotionMemory(
            user_id=analysis.user_id,
            emotional_summary=analysis.get_emotion_summary(),
            dominant_emotion=analysis.dominant_emotion,
            emotional_intensity=analysis.emotional_intensity,
            scene_description=analysis.scene_description,
            image_type=analysis.image_type,
            associated_text=analysis.text_context,
            emotional_impact_score=analysis.emotional_resonance_score,
            privacy_level=analysis.privacy_level,
            contains_faces=analysis.contains_faces,
            processing_mode=analysis.processing_mode
        )
        
        # Store using existing memory system
        await self.memory_manager.store_visual_emotion_memory(memory_entry)
    
    async def _update_emotional_context(self, analysis: VisualEmotionAnalysis, message: discord.Message):
        """Update user's emotional context with visual analysis"""
        # Integration with existing emotional intelligence system
        from src.emotion.external_api_emotion_ai import ExternalAPIEmotionAI
        
        # Combine visual and text emotions
        text_emotions = None
        if message.content:
            emotion_ai = ExternalAPIEmotionAI()
            text_emotions = await emotion_ai.analyze_emotional_context(
                message.content, 
                str(message.author.id)
            )
        
        # Fuse visual and text emotions
        enhanced_emotional_state = await self._fuse_visual_text_emotions(
            analysis, text_emotions, message
        )
        
        # Update memory with enhanced emotional context
        await self.memory_manager.update_emotional_context(
            str(message.author.id),
            enhanced_emotional_state
        )
    
    async def _generate_visual_emotion_response(self, analysis: VisualEmotionAnalysis, message: discord.Message):
        """Generate AI response acknowledging visual emotions"""
        
        # Determine if we should respond (probability-based)
        import random
        if random.random() > self.config.response_probability:
            return
        
        # Build visual emotion context for prompt
        visual_context = f"""
The user shared an image showing: {analysis.scene_description}

Visual Analysis:
- Detected emotions: {analysis.get_emotion_summary()}
- Image type: {analysis.image_type.value}
- Emotional intensity: {analysis.emotional_intensity:.2f}
- People detected: {analysis.people_count}
- Processing: {analysis.processing_mode.value} mode

User's message: "{message.content if message.content else '[image only]'}"
"""
        
        # Get comprehensive context including visual emotions
        try:
            comprehensive_context = await self.memory_manager.get_comprehensive_context(
                str(message.author.id),
                str(message.channel.id),
                include_visual_emotions=True
            )
            
            # Use adaptive prompt system with visual context
            system_prompt = get_contextualized_system_prompt(
                comprehensive_context=comprehensive_context,
                visual_emotion_context=visual_context,
                user_id=str(message.author.id)
            )
            
            # Generate response using LLM
            response = await self.llm_client.generate_response(
                system_prompt=system_prompt,
                user_message=f"Visual context: {visual_context}\\n\\nUser message: {message.content}",
                user_id=str(message.author.id)
            )
            
            # Send response
            if response and len(response.strip()) > 0:
                await message.channel.send(response)
                
        except Exception as e:
            logger.error(f"Error generating visual emotion response: {e}")
    
    async def _add_emotional_reaction(self, analysis: VisualEmotionAnalysis, message: discord.Message):
        """Add emoji reaction based on detected emotions"""
        
        # Map emotions to emoji reactions
        emotion_emoji_map = {
            'joy': '😊',
            'sadness': '😢',
            'anger': '😠',
            'fear': '😨',
            'surprise': '😮',
            'disgust': '🤢',
            'contempt': '🙄',
            'trust': '🤗',
            'anticipation': '🤩',
            'nostalgia': '🥺',
            'awe': '😍',
            'embarrassment': '😳',
            'pride': '👏',
            'shame': '😔',
            'guilt': '😞'
        }
        
        if analysis.dominant_emotion:
            emoji = emotion_emoji_map.get(analysis.dominant_emotion.value)
            if emoji:
                try:
                    await message.add_reaction(emoji)
                except discord.Forbidden:
                    # Bot doesn't have permission to add reactions
                    pass
                except Exception as e:
                    logger.error(f"Error adding emoji reaction: {e}")
    
    async def _fuse_visual_text_emotions(self, visual_analysis: VisualEmotionAnalysis, 
                                       text_emotions, message: discord.Message):
        """Combine visual and text emotional analysis"""
        from src.emotion.visual_emotion_models import EnhancedEmotionalState, FusedEmotion
        
        fused_emotions = []
        
        # Process visual emotions
        for v_emotion in visual_analysis.primary_emotions:
            # Check if text analysis has similar emotion
            text_match = None
            if text_emotions and hasattr(text_emotions, 'emotions'):
                text_match = self._find_matching_text_emotion(v_emotion.emotion, text_emotions)
            
            if text_match:
                # Combine visual and text intensities
                combined_intensity = (v_emotion.intensity * 0.6 + text_match.intensity * 0.4)
                combined_confidence = min(v_emotion.confidence * text_match.confidence * 1.3, 1.0)
                sources = ['visual', 'text']
            else:
                # Visual-only emotion
                combined_intensity = v_emotion.intensity * 0.8  # Slight reduction for single-source
                combined_confidence = v_emotion.confidence
                sources = ['visual']
            
            fused_emotion = FusedEmotion(
                emotion=v_emotion.emotion,
                intensity=combined_intensity,
                confidence=combined_confidence,
                sources=sources,
                visual_intensity=v_emotion.intensity,
                text_intensity=text_match.intensity if text_match else None
            )
            
            fused_emotions.append(fused_emotion)
        
        # Create enhanced emotional state
        enhanced_state = EnhancedEmotionalState(
            emotions=fused_emotions,
            dominant_emotion=visual_analysis.dominant_emotion,
            multimodal_confidence=visual_analysis.emotion_confidence,
            visual_context=visual_analysis.scene_description,
            text_context=message.content,
            processing_components=['visual_emotion_analysis', 'text_emotion_analysis']
        )
        
        return enhanced_state
    
    def _find_matching_text_emotion(self, visual_emotion, text_emotions):
        """Find matching emotion in text analysis results"""
        # This would depend on the structure of text_emotions
        # Implementation would map between visual and text emotion categories
        emotion_mapping = {
            'joy': 'happiness',
            'sadness': 'sadness', 
            'anger': 'anger',
            'fear': 'fear',
            'surprise': 'surprise'
            # ... additional mappings
        }
        
        text_emotion_name = emotion_mapping.get(visual_emotion.value)
        if text_emotion_name and hasattr(text_emotions, 'emotions'):
            for emotion in text_emotions.emotions:
                if emotion.emotion_type == text_emotion_name:
                    return emotion
        
        return None

    def register_commands(self, bot_name_filter: str, is_admin: bool):
        """Register Discord commands for visual emotion features"""
        
        @self.bot.command(name='visual_emotions')
        async def toggle_visual_emotions(ctx, enabled: str = None):
            """Toggle visual emotion analysis for the current user"""
            
            if enabled is None:
                # Show current status
                current_status = "enabled" if self.config.discord_enabled else "disabled"
                await ctx.send(f"Visual emotion analysis is currently **{current_status}** for you.")
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
            
            # Get visual emotion memories for user
            visual_memories = await self.memory_manager.get_visual_emotion_memories(user_id, limit=50)
            
            if not visual_memories:
                await ctx.send("No visual emotion data found. Share some images with me!")
                return
            
            # Calculate statistics
            emotion_counts = {}
            total_intensity = 0
            image_types = {}
            
            for memory in visual_memories:
                emotion = memory.dominant_emotion.value
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                total_intensity += memory.emotional_intensity
                
                img_type = memory.image_type.value
                image_types[img_type] = image_types.get(img_type, 0) + 1
            
            # Format statistics
            avg_intensity = total_intensity / len(visual_memories)
            top_emotion = max(emotion_counts, key=emotion_counts.get)
            top_image_type = max(image_types, key=image_types.get)
            
            stats_embed = discord.Embed(
                title="📊 Your Visual Emotion Statistics",
                color=discord.Color.blue()
            )
            
            stats_embed.add_field(
                name="📈 Overall Stats",
                value=f"Images analyzed: {len(visual_memories)}\\n"
                      f"Average emotional intensity: {avg_intensity:.2f}\\n"
                      f"Most common emotion: {top_emotion}\\n"
                      f"Favorite image type: {top_image_type}",
                inline=False
            )
            
            # Top emotions
            sorted_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            emotion_list = "\\n".join([f"{emotion}: {count}" for emotion, count in sorted_emotions])
            stats_embed.add_field(
                name="🎭 Top Emotions",
                value=emotion_list,
                inline=True
            )
            
            # Image types
            sorted_types = sorted(image_types.items(), key=lambda x: x[1], reverse=True)[:5]
            type_list = "\\n".join([f"{img_type}: {count}" for img_type, count in sorted_types])
            stats_embed.add_field(
                name="🖼️ Image Types",
                value=type_list,
                inline=True
            )
            
            await ctx.send(embed=stats_embed)

        if is_admin:
            @self.bot.command(name='visual_admin')
            async def visual_emotion_admin(ctx, action: str = None):
                """Admin commands for visual emotion system"""
                
                if action == "stats":
                    # Global visual emotion statistics
                    total_analyses = await self.memory_manager.get_visual_emotion_count()
                    await ctx.send(f"📊 Total visual emotion analyses: {total_analyses}")
                
                elif action == "config":
                    # Show current configuration
                    config_info = f"""
**Visual Emotion Configuration:**
- Enabled: {self.config.enabled}
- Discord Integration: {self.config.discord_enabled}
- Auto Responses: {self.config.generate_responses}
- Emoji Reactions: {self.config.add_emoji_reactions}
- Confidence Threshold: {self.config.confidence_threshold}
- Max Image Size: {self.config.max_image_size_mb}MB
- Processing Mode: {self.emotion_processor.deployment_mode}
                    """
                    await ctx.send(config_info)
                
                else:
                    await ctx.send("Usage: `!visual_admin [stats/config]`")
```

### **2. Visual Emotion Processor Implementation**

```python
# src/emotion/visual_emotion_processor.py
import asyncio
import logging
from typing import Dict, Any, Optional
from src.emotion.visual_emotion_models import (
    VisualEmotionAnalysis, 
    VisualEmotionCategory,
    VisualContextType, 
    ProcessingMode,
    PrivacyLevel
)

logger = logging.getLogger(__name__)


class VisualEmotionProcessor:
    """Core processor for visual emotion analysis"""
    
    def __init__(self, deployment_mode: str):
        self.deployment_mode = deployment_mode
        self.vision_client = self._initialize_vision_client()
        self.processing_semaphore = asyncio.Semaphore(3)  # Limit concurrent processing
    
    def _initialize_vision_client(self):
        """Initialize appropriate vision client based on deployment mode"""
        if self.deployment_mode == "desktop":
            return LocalVisionClient()
        else:
            return CloudVisionClient()
    
    async def analyze_image(self, image_data: bytes, context: Dict[str, Any]) -> Optional[VisualEmotionAnalysis]:
        """Analyze image for emotional content"""
        
        async with self.processing_semaphore:
            try:
                start_time = asyncio.get_event_loop().time()
                
                # Perform vision analysis
                vision_results = await self.vision_client.analyze_image(image_data, context)
                
                if not vision_results:
                    return None
                
                # Convert to visual emotion analysis
                analysis = self._convert_to_emotion_analysis(vision_results, context)
                
                # Calculate processing time
                processing_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
                analysis.processing_time_ms = processing_time
                
                logger.info(f"Visual emotion analysis completed in {processing_time}ms")
                return analysis
                
            except Exception as e:
                logger.error(f"Error in visual emotion analysis: {e}")
                return None
    
    def _convert_to_emotion_analysis(self, vision_results: Dict, context: Dict) -> VisualEmotionAnalysis:
        """Convert raw vision results to structured emotion analysis"""
        
        analysis = VisualEmotionAnalysis(
            user_id=context.get('user_id', ''),
            channel_id=context.get('channel_id', ''),
            message_id=context.get('message_id'),
            text_context=context.get('message_text'),
            processing_mode=ProcessingMode.LOCAL if self.deployment_mode == "desktop" else ProcessingMode.CLOUD,
            model_used=self.vision_client.model_name
        )
        
        # Extract emotions from vision results
        analysis.primary_emotions = self._extract_emotions(vision_results)
        analysis.scene_description = vision_results.get('description', '')
        analysis.image_type = self._classify_image_type(vision_results)
        analysis.people_count = vision_results.get('people_count', 0)
        analysis.contains_faces = vision_results.get('faces_detected', False)
        
        # Determine dominant emotion and confidence
        if analysis.primary_emotions:
            analysis.dominant_emotion = analysis.primary_emotions[0].emotion
            analysis.emotion_confidence = analysis.primary_emotions[0].confidence
            analysis.emotional_intensity = analysis.primary_emotions[0].intensity
        
        # Privacy classification
        analysis.privacy_level = self._classify_privacy_level(analysis)
        
        return analysis
    
    # Additional helper methods...
```

## 🔗 Integration Points

### **Memory System Integration**
- Extend `ContextAwareMemoryManager` with visual emotion storage
- Add visual emotion retrieval to comprehensive context
- Integrate with existing memory aging policies

### **Emotional Intelligence Integration**
- Extend `ExternalAPIEmotionAI` to support visual-text fusion
- Enhance `EmotionalContextEngine` with visual emotional states
- Update prompt generation to include visual context

### **Adaptive Prompt Integration**
- Extend adaptive prompt system to include visual emotion context
- Add visual emotion templates for different model sizes
- Optimize prompts based on image analysis complexity

## 📊 Testing Strategy

### **Unit Tests**
- Visual emotion model validation
- Privacy compliance verification
- Discord handler functionality

### **Integration Tests**
- End-to-end image processing pipeline
- Memory storage and retrieval
- LLM response generation with visual context

### **Privacy Tests**
- Ensure no raw images are stored
- Verify proper anonymization
- Test deployment mode isolation

## 🚀 Deployment Plan

### **Phase 1**: Core Infrastructure (Days 1-2)
- Implement data models ✅
- Create visual emotion processor
- Set up Discord image handling

### **Phase 2**: Discord Integration (Days 3-4)
- Implement Discord handlers
- Add command support
- Test basic image analysis

### **Phase 3**: Advanced Features (Days 5-6)
- Visual-text emotion fusion
- Memory integration
- Response optimization

### **Phase 4**: Testing & Documentation (Day 7)
- Comprehensive testing
- Performance optimization
- User documentation

## 🔧 Configuration Management

All visual emotion features will be configurable through the existing `.env` system:

```bash
# Enable/disable visual emotion analysis
ENABLE_VISUAL_EMOTION_ANALYSIS=true
DISCORD_VISUAL_EMOTION_ENABLED=true

# Processing configuration
VISUAL_EMOTION_PROCESSING_MODE=auto
VISUAL_EMOTION_CONFIDENCE_THRESHOLD=0.6
VISUAL_EMOTION_MAX_IMAGE_SIZE=10

# Privacy settings
VISUAL_EMOTION_RETENTION_DAYS=30
VISUAL_EMOTION_PRIVACY_MODE=enhanced

# Response behavior
DISCORD_VISUAL_RESPONSE_ENABLED=true
DISCORD_VISUAL_REACTION_ENABLED=true
```

## ✅ Success Criteria

- **Privacy Compliance**: 100% - no raw images stored, proper anonymization
- **Emotion Detection**: >85% accuracy for clear emotional expressions
- **Response Quality**: >90% contextually appropriate responses
- **Performance**: <3 seconds processing time for typical images
- **User Experience**: Seamless integration with existing Discord bot functionality

This implementation plan ensures Sprint 6 visual emotion AI delivers powerful new capabilities while maintaining WhisperEngine's commitment to privacy-first architecture and user control.