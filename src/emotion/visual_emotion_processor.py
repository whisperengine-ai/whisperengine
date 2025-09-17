#!/usr/bin/env python3
"""
Visual Emotion Processor - Sprint 6 Core Implementation

This module implements the core visual emotion analysis processor for WhisperEngine,
supporting both local and cloud-based vision models while maintaining privacy compliance.

Key Features:
- Deployment mode awareness (Desktop vs Cloud)
- Local and cloud vision model support
- Privacy-compliant processing
- Integration with existing emotion systems
"""

import asyncio
import logging
import os
import base64
import io
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from PIL import Image
import aiohttp

from src.emotion.visual_emotion_models import (
    VisualEmotionAnalysis,
    VisualEmotionCategory,
    VisualContextType,
    ProcessingMode,
    PrivacyLevel,
    DetectedEmotion,
    FacialEmotionData
)

logger = logging.getLogger(__name__)


class VisualEmotionProcessor:
    """Core processor for visual emotion analysis"""
    
    def __init__(self, deployment_mode: str = None):
        self.deployment_mode = deployment_mode or os.getenv('ENV_MODE', 'development')
        self.config = self._load_config()
        self.vision_client = self._initialize_vision_client()
        self.processing_semaphore = asyncio.Semaphore(
            self.config.get('max_concurrent', 3)
        )
        
        logger.info("🎯 Visual Emotion Processor initialized in %s mode", self.deployment_mode)
        logger.info("📊 Using %s vision provider", self.config['vision_provider'])
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        return {
            'enabled': os.getenv('ENABLE_VISUAL_EMOTION_ANALYSIS', 'true').lower() == 'true',
            'confidence_threshold': float(os.getenv('VISUAL_EMOTION_CONFIDENCE_THRESHOLD', '0.6')),
            'max_image_size': int(os.getenv('VISUAL_EMOTION_MAX_IMAGE_SIZE', '10')),
            'processing_mode': os.getenv('VISUAL_EMOTION_PROCESSING_MODE', 'auto'),
            'vision_provider': os.getenv('VISION_MODEL_PROVIDER', 'local'),
            'vision_model': os.getenv('VISION_MODEL_NAME', 'llava-1.5-7b'),
            'local_model': os.getenv('LOCAL_VISION_MODEL', 'llava-1.5-7b'),
            'privacy_mode': os.getenv('VISUAL_EMOTION_PRIVACY_MODE', 'enhanced'),
            'max_concurrent': int(os.getenv('MAX_CONCURRENT_VISUAL_ANALYSES', '3')),
            'timeout': int(os.getenv('VISUAL_ANALYSIS_TIMEOUT', '30'))
        }
    
    def _initialize_vision_client(self):
        """Initialize appropriate vision client based on deployment mode"""
        if (self.deployment_mode == "desktop" or 
            self.config['vision_provider'] == 'local' or
            self.config['processing_mode'] == 'local'):
            return LocalVisionClient(self.config)
        else:
            return CloudVisionClient(self.config)
    
    async def analyze_image(self, image_data: bytes, context: Dict[str, Any]) -> Optional[VisualEmotionAnalysis]:
        """Main entry point for visual emotion analysis"""
        
        if not self.config['enabled']:
            logger.debug("Visual emotion analysis disabled in configuration")
            return None
        
        async with self.processing_semaphore:
            try:
                # Validate image
                if not self._validate_image(image_data):
                    return None
                
                # Start timing
                start_time = datetime.now()
                
                # Perform vision analysis
                logger.info("🔍 Starting visual analysis for %d byte image", len(image_data))
                vision_results = await self._perform_vision_analysis(image_data, context)
                
                if not vision_results:
                    logger.warning("❌ Vision analysis returned no results")
                    return None
                
                # Convert to structured analysis
                analysis = self._create_emotion_analysis(vision_results, context, start_time)
                
                # Validate analysis quality
                if analysis.emotion_confidence < self.config['confidence_threshold']:
                    logger.info("⚠️ Analysis confidence %.2f below threshold %.2f", 
                               analysis.emotion_confidence, self.config['confidence_threshold'])
                    return None
                
                logger.info(f"✅ Visual emotion analysis completed: {analysis.get_emotion_summary()}")
                return analysis
                
            except Exception as e:
                logger.error(f"❌ Visual emotion analysis failed: {e}")
                return None
    
    def _validate_image(self, image_data: bytes) -> bool:
        """Validate image data and size"""
        if not image_data:
            logger.warning("Empty image data provided")
            return False
        
        # Check size
        size_mb = len(image_data) / (1024 * 1024)
        if size_mb > self.config['max_image_size']:
            logger.warning(f"Image too large: {size_mb:.1f}MB > {self.config['max_image_size']}MB")
            return False
        
        # Try to validate as image
        try:
            image = Image.open(io.BytesIO(image_data))
            if image.size[0] < 32 or image.size[1] < 32:
                logger.warning(f"Image too small: {image.size}")
                return False
            return True
        except Exception as e:
            logger.warning(f"Invalid image data: {e}")
            return False
    
    async def _perform_vision_analysis(self, image_data: bytes, context: Dict[str, Any]) -> Optional[Dict]:
        """Perform the actual vision analysis"""
        try:
            # Use appropriate vision client
            analysis_timeout = self.config['timeout']
            vision_results = await asyncio.wait_for(
                self.vision_client.analyze_image(image_data, context),
                timeout=analysis_timeout
            )
            return vision_results
        except asyncio.TimeoutError:
            logger.error(f"Vision analysis timed out after {analysis_timeout} seconds")
            return None
        except Exception as e:
            logger.error(f"Vision analysis error: {e}")
            return None
    
    def _create_emotion_analysis(self, vision_results: Dict, context: Dict, start_time: datetime) -> VisualEmotionAnalysis:
        """Convert vision results to structured emotion analysis"""
        
        # Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Create base analysis object
        analysis = VisualEmotionAnalysis(
            user_id=context.get('user_id', ''),
            channel_id=context.get('channel_id', ''),
            message_id=context.get('message_id'),
            text_context=context.get('message_text'),
            processing_mode=ProcessingMode.LOCAL if self.deployment_mode == "desktop" else ProcessingMode.CLOUD,
            model_used=self.vision_client.model_name,
            processing_time_ms=processing_time
        )
        
        # Extract emotions from vision results
        analysis.primary_emotions = self._extract_emotions(vision_results)
        analysis.scene_description = vision_results.get('scene_description', '')
        analysis.image_type = self._classify_image_type(vision_results)
        analysis.people_count = vision_results.get('people_count', 0)
        analysis.contains_faces = vision_results.get('contains_faces', False)
        analysis.detected_objects = vision_results.get('objects', [])
        
        # Process facial emotions if detected
        if vision_results.get('facial_emotions'):
            analysis.facial_emotions = self._process_facial_emotions(vision_results['facial_emotions'])
        
        # Determine dominant emotion and overall confidence
        if analysis.primary_emotions:
            dominant = max(analysis.primary_emotions, key=lambda e: e.confidence)
            analysis.dominant_emotion = dominant.emotion
            analysis.emotion_confidence = dominant.confidence
            analysis.emotional_intensity = dominant.intensity
        
        # Calculate emotional resonance score
        analysis.emotional_resonance_score = self._calculate_resonance_score(analysis)
        
        # Classify privacy level
        analysis.privacy_level = self._classify_privacy_level(analysis)
        
        # Set image dimensions if available
        if 'image_dimensions' in vision_results:
            analysis.image_dimensions = tuple(vision_results['image_dimensions'])
        
        return analysis
    
    def _extract_emotions(self, vision_results: Dict) -> List[DetectedEmotion]:
        """Extract emotions from raw vision analysis results"""
        emotions = []
        
        raw_emotions = vision_results.get('emotions', [])
        if isinstance(raw_emotions, list):
            for emotion_data in raw_emotions:
                try:
                    # Map emotion names to our categories
                    emotion_name = emotion_data.get('emotion', '').lower()
                    emotion_category = self._map_emotion_name(emotion_name)
                    
                    if emotion_category:
                        detected_emotion = DetectedEmotion(
                            emotion=emotion_category,
                            confidence=float(emotion_data.get('confidence', 0.0)),
                            intensity=float(emotion_data.get('intensity', 0.0)),
                            description=emotion_data.get('description', '')
                        )
                        emotions.append(detected_emotion)
                except Exception as e:
                    logger.warning(f"Error processing emotion data: {e}")
        
        # Sort by confidence
        emotions.sort(key=lambda e: e.confidence, reverse=True)
        return emotions[:5]  # Keep top 5 emotions
    
    def _map_emotion_name(self, emotion_name: str) -> Optional[VisualEmotionCategory]:
        """Map string emotion names to our emotion categories"""
        emotion_mapping = {
            'joy': VisualEmotionCategory.JOY,
            'happiness': VisualEmotionCategory.JOY,
            'happy': VisualEmotionCategory.JOY,
            'sadness': VisualEmotionCategory.SADNESS,
            'sad': VisualEmotionCategory.SADNESS,
            'anger': VisualEmotionCategory.ANGER,
            'angry': VisualEmotionCategory.ANGER,
            'fear': VisualEmotionCategory.FEAR,
            'scared': VisualEmotionCategory.FEAR,
            'surprise': VisualEmotionCategory.SURPRISE,
            'surprised': VisualEmotionCategory.SURPRISE,
            'disgust': VisualEmotionCategory.DISGUST,
            'contempt': VisualEmotionCategory.CONTEMPT,
            'trust': VisualEmotionCategory.TRUST,
            'anticipation': VisualEmotionCategory.ANTICIPATION,
            'nostalgia': VisualEmotionCategory.NOSTALGIA,
            'awe': VisualEmotionCategory.AWE,
            'embarrassment': VisualEmotionCategory.EMBARRASSMENT,
            'pride': VisualEmotionCategory.PRIDE,
            'shame': VisualEmotionCategory.SHAME,
            'guilt': VisualEmotionCategory.GUILT
        }
        return emotion_mapping.get(emotion_name.lower())
    
    def _classify_image_type(self, vision_results: Dict) -> VisualContextType:
        """Classify the type of image based on vision analysis"""
        
        # Check for explicit type classification
        if 'image_type' in vision_results:
            type_mapping = {
                'selfie': VisualContextType.SELFIE,
                'group_photo': VisualContextType.GROUP_PHOTO,
                'landscape': VisualContextType.LANDSCAPE,
                'meme': VisualContextType.MEME,
                'artwork': VisualContextType.ARTWORK,
                'pet': VisualContextType.PET,
                'food': VisualContextType.FOOD,
                'event': VisualContextType.EVENT,
                'screenshot': VisualContextType.SCREENSHOT,
                'document': VisualContextType.DOCUMENT,
                'nature': VisualContextType.NATURE,
                'architecture': VisualContextType.ARCHITECTURE,
                'vehicle': VisualContextType.VEHICLE
            }
            return type_mapping.get(vision_results['image_type'], VisualContextType.UNKNOWN)
        
        # Infer from content
        description = vision_results.get('scene_description', '').lower()
        objects = [obj.lower() for obj in vision_results.get('objects', [])]
        people_count = vision_results.get('people_count', 0)
        
        # Classification logic
        if people_count == 1 and any(word in description for word in ['selfie', 'portrait', 'close-up']):
            return VisualContextType.SELFIE
        elif people_count > 1:
            return VisualContextType.GROUP_PHOTO
        elif any(word in description for word in ['landscape', 'mountain', 'ocean', 'sky']):
            return VisualContextType.LANDSCAPE
        elif any(word in description for word in ['pet', 'dog', 'cat', 'animal']):
            return VisualContextType.PET
        elif any(word in description for word in ['food', 'meal', 'restaurant', 'cooking']):
            return VisualContextType.FOOD
        elif 'meme' in description or 'funny' in description:
            return VisualContextType.MEME
        elif any(word in description for word in ['art', 'painting', 'drawing', 'illustration']):
            return VisualContextType.ARTWORK
        elif any(word in description for word in ['screenshot', 'screen', 'interface', 'app']):
            return VisualContextType.SCREENSHOT
        elif any(word in description for word in ['text', 'document', 'paper', 'form']):
            return VisualContextType.DOCUMENT
        else:
            return VisualContextType.UNKNOWN
    
    def _process_facial_emotions(self, facial_data: List[Dict]) -> List[FacialEmotionData]:
        """Process facial emotion data from vision analysis"""
        facial_emotions = []
        
        for face_data in facial_data:
            try:
                face_emotions = []
                for emotion_data in face_data.get('emotions', []):
                    emotion_category = self._map_emotion_name(emotion_data.get('emotion', ''))
                    if emotion_category:
                        face_emotions.append(DetectedEmotion(
                            emotion=emotion_category,
                            confidence=float(emotion_data.get('confidence', 0.0)),
                            intensity=float(emotion_data.get('intensity', 0.0))
                        ))
                
                if face_emotions:
                    dominant = max(face_emotions, key=lambda e: e.confidence)
                    facial_emotion = FacialEmotionData(
                        face_id=face_data.get('face_id', f"face_{len(facial_emotions)}"),
                        bounding_box=tuple(face_data.get('bounding_box', [0, 0, 0, 0])),
                        emotions=face_emotions,
                        dominant_emotion=dominant.emotion,
                        overall_confidence=dominant.confidence,
                        expression_description=face_data.get('expression', '')
                    )
                    facial_emotions.append(facial_emotion)
                    
            except Exception as e:
                logger.warning(f"Error processing facial emotion data: {e}")
        
        return facial_emotions
    
    def _calculate_resonance_score(self, analysis: VisualEmotionAnalysis) -> float:
        """Calculate emotional resonance score based on multiple factors"""
        score = 0.0
        
        # Base score from emotion confidence
        if analysis.primary_emotions:
            avg_confidence = sum(e.confidence for e in analysis.primary_emotions) / len(analysis.primary_emotions)
            score += avg_confidence * 0.4
        
        # Boost for facial emotions (more personal)
        if analysis.facial_emotions:
            score += 0.2
        
        # Boost for certain image types
        type_boosts = {
            VisualContextType.SELFIE: 0.3,
            VisualContextType.GROUP_PHOTO: 0.2,
            VisualContextType.PET: 0.15,
            VisualContextType.EVENT: 0.1
        }
        score += type_boosts.get(analysis.image_type, 0.0)
        
        # Boost for high emotional intensity
        if analysis.emotional_intensity > 0.7:
            score += 0.1
        
        return min(score, 1.0)
    
    def _classify_privacy_level(self, analysis: VisualEmotionAnalysis) -> PrivacyLevel:
        """Classify privacy level based on image content"""
        
        # Sensitive: Contains faces or is a selfie
        if analysis.contains_faces or analysis.image_type == VisualContextType.SELFIE:
            return PrivacyLevel.SENSITIVE
        
        # Private: Multiple people or personal content
        if (analysis.people_count > 1 or 
            analysis.image_type in [VisualContextType.GROUP_PHOTO, VisualContextType.EVENT]):
            return PrivacyLevel.PRIVATE
        
        # Restricted: Screenshots might contain personal info
        if analysis.image_type == VisualContextType.SCREENSHOT:
            return PrivacyLevel.RESTRICTED
        
        # Default to public for landscapes, artwork, etc.
        return PrivacyLevel.PUBLIC


class LocalVisionClient:
    """Local vision processing using CLIP/LLaVA models"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get('local_model', 'llava-1.5-7b')
        self.initialized = False
        logger.info(f"🔧 Initialized local vision client: {self.model_name}")
    
    async def analyze_image(self, image_data: bytes, context: Dict[str, Any]) -> Dict:
        """Analyze image using local models"""
        
        # For now, this is a sophisticated placeholder
        # In a real implementation, this would integrate with:
        # - LLaVA for visual-language understanding
        # - CLIP for scene classification
        # - Local emotion detection models
        
        try:
            # Simulate local processing
            await asyncio.sleep(0.1)  # Simulate processing time
            
            # Basic image analysis
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            
            # Generate placeholder analysis based on image properties
            analysis = {
                'scene_description': f'Local analysis: Image shows visual content ({width}x{height})',
                'emotions': [
                    {'emotion': 'joy', 'confidence': 0.7, 'intensity': 0.6},
                    {'emotion': 'anticipation', 'confidence': 0.5, 'intensity': 0.4}
                ],
                'image_type': 'unknown',
                'people_count': 0,
                'contains_faces': False,
                'objects': ['visual_content'],
                'image_dimensions': [width, height],
                'processing_method': 'local'
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Local vision analysis failed: {e}")
            return {}


class CloudVisionClient:
    """Cloud vision processing using GPT-4V, Claude 3, etc."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = config.get('vision_provider', 'openai')
        self.model_name = config.get('vision_model', 'gpt-4-vision-preview')
        logger.info(f"☁️ Initialized cloud vision client: {self.provider}/{self.model_name}")
    
    async def analyze_image(self, image_data: bytes, context: Dict[str, Any]) -> Dict:
        """Analyze image using cloud vision APIs"""
        
        if self.provider == 'openai':
            return await self._analyze_with_openai(image_data, context)
        elif self.provider == 'anthropic':
            return await self._analyze_with_anthropic(image_data, context)
        else:
            logger.warning(f"Unknown vision provider: {self.provider}")
            return {}
    
    async def _analyze_with_openai(self, image_data: bytes, context: Dict[str, Any]) -> Dict:
        """Analyze image using OpenAI GPT-4V"""
        
        # Placeholder for OpenAI integration
        # This would use the OpenAI API with GPT-4 Vision
        await asyncio.sleep(0.2)  # Simulate API call
        
        return {
            'scene_description': 'OpenAI GPT-4V analysis: Advanced visual understanding with detailed scene analysis',
            'emotions': [
                {'emotion': 'joy', 'confidence': 0.85, 'intensity': 0.8},
                {'emotion': 'trust', 'confidence': 0.7, 'intensity': 0.6}
            ],
            'image_type': 'photo',
            'people_count': 1,
            'contains_faces': True,
            'objects': ['person', 'face', 'expression'],
            'facial_emotions': [
                {
                    'face_id': 'face_1',
                    'bounding_box': [100, 100, 200, 200],
                    'emotions': [
                        {'emotion': 'joy', 'confidence': 0.9, 'intensity': 0.85}
                    ],
                    'expression': 'smiling, happy expression'
                }
            ],
            'processing_method': 'openai_gpt4v'
        }
    
    async def _analyze_with_anthropic(self, image_data: bytes, context: Dict[str, Any]) -> Dict:
        """Analyze image using Anthropic Claude 3"""
        
        # Placeholder for Anthropic integration
        await asyncio.sleep(0.2)  # Simulate API call
        
        return {
            'scene_description': 'Anthropic Claude 3 analysis: Sophisticated visual understanding',
            'emotions': [
                {'emotion': 'awe', 'confidence': 0.8, 'intensity': 0.75}
            ],
            'image_type': 'landscape',
            'people_count': 0,
            'contains_faces': False,
            'objects': ['nature', 'scenery'],
            'processing_method': 'anthropic_claude3'
        }


# Factory function for easy instantiation
def create_visual_emotion_processor(deployment_mode: str = None) -> VisualEmotionProcessor:
    """Factory function to create visual emotion processor"""
    return VisualEmotionProcessor(deployment_mode)


# CLI testing interface
if __name__ == "__main__":
    import asyncio
    
    async def test_processor():
        """Test the visual emotion processor"""
        print("🧪 Testing Visual Emotion Processor")
        
        processor = create_visual_emotion_processor()
        
        # Create a simple test image (1x1 pixel PNG)
        test_image = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format='PNG')
        test_image_data = img_bytes.getvalue()
        
        context = {
            'user_id': 'test_user_123',
            'channel_id': 'test_channel_456',
            'message_id': 'test_message_789',
            'message_text': 'Here is my test image!',
            'filename': 'test.png'
        }
        
        print(f"📊 Analyzing {len(test_image_data)} byte test image...")
        result = await processor.analyze_image(test_image_data, context)
        
        if result:
            print(f"✅ Analysis successful!")
            print(f"   Emotions: {result.get_emotion_summary()}")
            print(f"   Scene: {result.scene_description}")
            print(f"   Type: {result.image_type.value}")
            print(f"   Confidence: {result.emotion_confidence:.2f}")
            print(f"   Processing time: {result.processing_time_ms}ms")
            print(f"   Privacy level: {result.privacy_level.value}")
        else:
            print("❌ Analysis failed")
    
    # Run the test
    asyncio.run(test_processor())