# 👁️ Visual Emotion Analysis - Sprint 6

## 🎯 Overview

Sprint 6 introduces visual emotion analysis for user-uploaded images through Discord. This feature extends WhisperEngine's emotional intelligence to understand emotions conveyed through images, selfies, memes, and visual content.

## 🔒 Privacy Architecture

### **Deployment Mode Support**
- **Cloud Mode**: Full visual emotion analysis with Discord integration
- **Desktop Mode**: Local-only image analysis (no Discord connectivity)
- **Demo Mode**: Trial visual emotion features with data lifecycle warnings

### **Data Handling**
- **Cloud Mode**: Images processed via cloud vision APIs (OpenAI GPT-4V, Claude 3)
- **Desktop Mode**: Local multimodal models only (LLaVA, CLIP-based)
- **Image Storage**: Temporary processing only - no permanent image storage

## 🖼️ Visual Emotion Categories

### **Primary Visual Emotions**
```python
class VisualEmotionCategory(Enum):
    # Core emotions detected in images
    JOY = "joy"                    # Smiles, celebrations, positive scenes
    SADNESS = "sadness"            # Tears, melancholy expressions, somber scenes
    ANGER = "anger"                # Frowns, aggressive gestures, tense scenes
    FEAR = "fear"                  # Wide eyes, defensive postures, scary content
    SURPRISE = "surprise"          # Open mouth, raised eyebrows, unexpected scenes
    DISGUST = "disgust"            # Wrinkled nose, negative reactions
    CONTEMPT = "contempt"          # Eye rolls, dismissive expressions
    TRUST = "trust"                # Warm expressions, intimate moments
    ANTICIPATION = "anticipation"  # Excited expressions, expectant scenes
    
    # Visual-specific emotions
    NOSTALGIA = "nostalgia"        # Old photos, vintage content, memories
    AWE = "awe"                    # Breathtaking landscapes, impressive scenes
    EMBARRASSMENT = "embarrassment" # Blushing, hiding faces, awkward moments
```

### **Visual Context Categories**
```python
class VisualContextType(Enum):
    SELFIE = "selfie"              # Personal photos, self-portraits
    GROUP_PHOTO = "group_photo"    # Multiple people, social gatherings
    LANDSCAPE = "landscape"        # Nature, scenery, places
    MEME = "meme"                  # Humor, internet culture, reaction images
    ARTWORK = "artwork"            # Creative content, illustrations, designs
    PET = "pet"                    # Animals, pets, cute creatures
    FOOD = "food"                  # Meals, cooking, dining experiences
    EVENT = "event"                # Celebrations, parties, special occasions
    SCREENSHOT = "screenshot"      # Digital content, conversations, apps
    DOCUMENT = "document"          # Text-heavy images, forms, papers
```

## 🏗️ Data Models

### **Core Visual Emotion Models**

```python
@dataclass
class VisualEmotionAnalysis:
    """Complete visual emotion analysis results"""
    
    # Basic metadata
    image_id: str
    user_id: str
    channel_id: str
    analysis_timestamp: datetime
    
    # Visual emotion detection
    primary_emotions: List[DetectedEmotion]
    emotion_confidence: float
    emotional_intensity: float  # 0.0-1.0
    
    # Visual context
    image_type: VisualContextType
    scene_description: str
    detected_objects: List[str]
    people_count: int
    
    # Facial emotion analysis (if faces detected)
    facial_emotions: List[FacialEmotionData]
    
    # Privacy and processing
    processing_mode: str  # "local" or "cloud"
    model_used: str
    processing_time_ms: int
    
    # Integration data
    text_context: Optional[str]  # Associated message text
    conversation_context: Optional[str]
    emotional_resonance_score: float

@dataclass
class DetectedEmotion:
    """Individual emotion detection result"""
    emotion: VisualEmotionCategory
    confidence: float  # 0.0-1.0
    intensity: float   # 0.0-1.0
    region_coords: Optional[Tuple[int, int, int, int]]  # Bounding box if localized

@dataclass
class FacialEmotionData:
    """Facial emotion analysis for individual faces"""
    face_id: str
    bounding_box: Tuple[int, int, int, int]
    emotions: List[DetectedEmotion]
    age_estimate: Optional[int]
    gender_estimate: Optional[str]
    expression_description: str

@dataclass
class VisualEmotionMemory:
    """Visual emotion memory entry for long-term storage"""
    
    # Memory metadata
    memory_id: str
    user_id: str
    created_at: datetime
    
    # Visual summary (no raw image stored)
    emotional_summary: str
    scene_description: str
    image_type: VisualContextType
    
    # Emotional significance
    emotional_impact_score: float
    memorable_elements: List[str]
    associated_text: Optional[str]
    
    # Privacy compliance
    contains_faces: bool
    privacy_level: str  # "public", "private", "sensitive"
    retention_policy: str
```

## 🔌 Integration Architecture

### **Vision Model Integration**

```python
class VisualEmotionProcessor:
    """Main processor for visual emotion analysis"""
    
    def __init__(self, deployment_mode: str):
        self.deployment_mode = deployment_mode
        self.vision_client = self._initialize_vision_client()
        self.emotion_integrator = VisualEmotionIntegrator()
    
    def _initialize_vision_client(self) -> VisionClient:
        if self.deployment_mode == "desktop":
            return LocalVisionClient()  # LLaVA, CLIP-based local models
        else:
            return CloudVisionClient()  # GPT-4V, Claude 3, etc.
    
    async def analyze_image(self, image_data: bytes, context: Dict) -> VisualEmotionAnalysis:
        """Process image for emotional content"""
        
    async def integrate_with_conversation(self, analysis: VisualEmotionAnalysis, 
                                        message_context: str) -> EmotionalContext:
        """Integrate visual emotions with conversation state"""
```

### **Privacy-Compliant Storage**

```python
class VisualEmotionStorage:
    """Handles visual emotion data storage with privacy compliance"""
    
    def __init__(self, deployment_mode: str):
        self.deployment_mode = deployment_mode
        self.storage_backend = self._get_storage_backend()
    
    async def store_analysis(self, analysis: VisualEmotionAnalysis) -> str:
        """Store emotion analysis (NOT the original image)"""
        
        # Create privacy-compliant memory entry
        memory_entry = VisualEmotionMemory(
            emotional_summary=analysis.scene_description,
            emotional_impact_score=analysis.emotional_intensity,
            contains_faces=len(analysis.facial_emotions) > 0,
            privacy_level=self._determine_privacy_level(analysis)
        )
        
        return await self.storage_backend.store_memory(memory_entry)
    
    def _determine_privacy_level(self, analysis: VisualEmotionAnalysis) -> str:
        """Determine appropriate privacy level for content"""
        if analysis.image_type == VisualContextType.SELFIE:
            return "sensitive"
        elif len(analysis.facial_emotions) > 0:
            return "private"
        else:
            return "public"
```

## 🎨 Discord Integration

### **Image Upload Handling**

```python
class DiscordVisualEmotionHandler:
    """Discord-specific visual emotion processing"""
    
    async def handle_image_upload(self, message: discord.Message) -> Optional[VisualEmotionAnalysis]:
        """Process Discord image uploads for emotional content"""
        
        if not message.attachments:
            return None
        
        for attachment in message.attachments:
            if self._is_image(attachment):
                # Download and analyze image
                image_data = await attachment.read()
                
                context = {
                    'user_id': str(message.author.id),
                    'channel_id': str(message.channel.id),
                    'message_text': message.content,
                    'timestamp': message.created_at
                }
                
                analysis = await self.vision_processor.analyze_image(image_data, context)
                
                # Integrate with conversation context
                await self._update_emotional_context(analysis, message)
                
                # Generate contextual response
                await self._generate_visual_response(analysis, message)
                
                return analysis
    
    async def _generate_visual_response(self, analysis: VisualEmotionAnalysis, 
                                      message: discord.Message):
        """Generate AI response acknowledging visual emotions"""
        
        # Build emotion-aware prompt
        visual_context = f"""
        User shared an image showing {analysis.scene_description}.
        Detected emotions: {[e.emotion.value for e in analysis.primary_emotions]}
        Emotional intensity: {analysis.emotional_intensity:.2f}
        Image type: {analysis.image_type.value}
        """
        
        # Use adaptive prompt system for response
        response_prompt = await get_visual_emotion_prompt(
            visual_context=visual_context,
            conversation_context=message.content,
            user_emotional_state=analysis
        )
        
        # Generate and send response
        response = await self.llm_client.generate_response(response_prompt)
        await message.channel.send(response)
```

## 🧠 Emotional Intelligence Integration

### **Visual-Text Emotion Fusion**

```python
class VisualTextEmotionFusion:
    """Combines visual and text emotions for comprehensive understanding"""
    
    def fuse_emotions(self, visual_analysis: VisualEmotionAnalysis, 
                     text_emotions: EmotionalState) -> EnhancedEmotionalState:
        """Combine visual and textual emotional cues"""
        
        # Weight visual vs text emotions based on content type
        visual_weight = self._calculate_visual_weight(visual_analysis)
        text_weight = 1.0 - visual_weight
        
        # Fusion logic
        fused_emotions = []
        for v_emotion in visual_analysis.primary_emotions:
            # Find corresponding text emotion
            text_match = self._find_emotion_match(v_emotion.emotion, text_emotions)
            
            if text_match:
                # Reinforce matching emotions
                fused_intensity = (v_emotion.intensity * visual_weight + 
                                 text_match.intensity * text_weight)
                confidence = min(v_emotion.confidence * text_match.confidence * 1.5, 1.0)
            else:
                # Visual-only emotion
                fused_intensity = v_emotion.intensity * visual_weight
                confidence = v_emotion.confidence * 0.8
            
            fused_emotions.append(FusedEmotion(
                emotion=v_emotion.emotion,
                intensity=fused_intensity,
                confidence=confidence,
                sources=['visual', 'text'] if text_match else ['visual']
            ))
        
        return EnhancedEmotionalState(
            emotions=fused_emotions,
            visual_context=visual_analysis.scene_description,
            multimodal_confidence=self._calculate_fusion_confidence(fused_emotions)
        )
```

## 🔧 Configuration Options

### **New Environment Variables**

```bash
# === Visual Emotion Analysis ===
ENABLE_VISUAL_EMOTION_ANALYSIS=true         # Enable visual emotion features
VISUAL_EMOTION_PROCESSING_MODE=auto          # auto/local/cloud
VISUAL_EMOTION_CONFIDENCE_THRESHOLD=0.6      # Minimum confidence for emotion detection
VISUAL_EMOTION_MAX_IMAGE_SIZE=10             # MB limit for image processing

# === Vision Model Configuration ===
VISION_MODEL_PROVIDER=openai                 # openai/anthropic/local
VISION_MODEL_NAME=gpt-4-vision-preview       # Cloud: gpt-4v, claude-3-vision
LOCAL_VISION_MODEL=llava-1.5-7b              # Local: llava, blip2, clip

# === Privacy and Storage ===
VISUAL_EMOTION_RETENTION_DAYS=30             # How long to keep visual emotion memories
VISUAL_EMOTION_PRIVACY_MODE=enhanced         # basic/enhanced/strict
STORE_VISUAL_EMOTIONS_LOCALLY=true           # Desktop mode: store in local DB only

# === Discord Integration ===
DISCORD_VISUAL_EMOTION_ENABLED=true          # Enable Discord image analysis
DISCORD_VISUAL_RESPONSE_ENABLED=true         # Generate responses to images
DISCORD_VISUAL_REACTION_ENABLED=true         # Add emoji reactions based on emotions
```

## 🚀 Implementation Phases

### **Phase 1: Core Infrastructure** (Days 1-2)
- ✅ Data models and storage design
- ✅ Privacy-compliant architecture
- ✅ Basic vision model integration

### **Phase 2: Discord Integration** (Days 3-4)
- ⏳ Image upload handling
- ⏳ Emotion analysis pipeline
- ⏳ Response generation

### **Phase 3: Advanced Features** (Days 5-6)
- ⏳ Multi-modal emotion fusion
- ⏳ Facial emotion analysis
- ⏳ Memory integration

### **Phase 4: Testing & Optimization** (Days 7)
- ⏳ Comprehensive testing
- ⏳ Performance optimization
- ⏳ Privacy validation

## 📊 Success Metrics

- **Emotion Detection Accuracy**: >85% for clear emotional expressions
- **Response Relevance**: >90% contextually appropriate responses to images
- **Processing Speed**: <3 seconds for typical images
- **Privacy Compliance**: 100% - no raw images stored permanently
- **User Engagement**: Increased conversation depth with visual context

## 🔐 Privacy Safeguards

1. **No Permanent Image Storage**: Only emotion analysis results stored
2. **Processing Mode Transparency**: Clear indication of local vs cloud processing
3. **Consent Management**: Users can opt-out of visual emotion analysis
4. **Data Retention**: Configurable retention periods for visual emotion memories
5. **Facial Recognition Limits**: Emotion detection only, no identity recognition