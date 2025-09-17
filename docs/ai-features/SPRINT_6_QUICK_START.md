# 🚀 Sprint 6 Quick Start Guide

## Getting Started with Visual Emotion Implementation

### Step 1: Create the Core Processor

Create `src/emotion/visual_emotion_processor.py` with the basic structure:

```python
#!/usr/bin/env python3
"""
Visual Emotion Processor - Sprint 6 Core Implementation
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class VisualEmotionProcessor:
    """Core processor for visual emotion analysis"""
    
    def __init__(self, deployment_mode: str = None):
        self.deployment_mode = deployment_mode or os.getenv('ENV_MODE', 'development')
        self.config = self._load_config()
        self.vision_client = self._initialize_vision_client()
        
        logger.info(f"🎯 Visual Emotion Processor initialized in {self.deployment_mode} mode")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment"""
        return {
            'enabled': os.getenv('ENABLE_VISUAL_EMOTION_ANALYSIS', 'true').lower() == 'true',
            'confidence_threshold': float(os.getenv('VISUAL_EMOTION_CONFIDENCE_THRESHOLD', '0.6')),
            'max_image_size': int(os.getenv('VISUAL_EMOTION_MAX_IMAGE_SIZE', '10')),
            'processing_mode': os.getenv('VISUAL_EMOTION_PROCESSING_MODE', 'auto'),
            'vision_provider': os.getenv('VISION_MODEL_PROVIDER', 'local'),
            'vision_model': os.getenv('VISION_MODEL_NAME', 'llava-1.5-7b')
        }
    
    def _initialize_vision_client(self):
        """Initialize appropriate vision client"""
        if self.deployment_mode == "desktop" or self.config['vision_provider'] == 'local':
            return LocalVisionClient(self.config)
        else:
            return CloudVisionClient(self.config)
    
    async def analyze_image(self, image_data: bytes, context: Dict[str, Any]) -> Optional[Dict]:
        """Main entry point for image analysis"""
        if not self.config['enabled']:
            logger.debug("Visual emotion analysis disabled")
            return None
        
        try:
            # Check image size
            if len(image_data) > (self.config['max_image_size'] * 1024 * 1024):
                logger.warning(f"Image too large: {len(image_data)} bytes")
                return None
            
            # Perform analysis
            start_time = datetime.now()
            analysis_result = await self.vision_client.analyze_image(image_data, context)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if analysis_result:
                analysis_result['processing_time_ms'] = int(processing_time * 1000)
                analysis_result['processing_mode'] = self.deployment_mode
                analysis_result['model_used'] = self.config['vision_model']
                
                logger.info(f"✅ Visual analysis completed in {processing_time:.2f}s")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Visual emotion analysis failed: {e}")
            return None


class LocalVisionClient:
    """Local vision processing using CLIP/LLaVA models"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get('vision_model', 'llava-1.5-7b')
        logger.info(f"🔧 Initialized local vision client: {self.model_name}")
    
    async def analyze_image(self, image_data: bytes, context: Dict[str, Any]) -> Dict:
        """Analyze image using local models"""
        # Placeholder for local vision model integration
        # This would integrate with LLaVA, BLIP2, or similar local models
        
        return {
            'scene_description': 'Local analysis placeholder - image contains visual content',
            'emotions': [
                {'emotion': 'joy', 'confidence': 0.7, 'intensity': 0.6}
            ],
            'image_type': 'unknown',
            'people_count': 0,
            'contains_faces': False,
            'confidence': 0.7
        }


class CloudVisionClient:
    """Cloud vision processing using GPT-4V, Claude 3, etc."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = config.get('vision_provider', 'openai')
        self.model_name = config.get('vision_model', 'gpt-4-vision-preview')
        logger.info(f"☁️ Initialized cloud vision client: {self.provider}/{self.model_name}")
    
    async def analyze_image(self, image_data: bytes, context: Dict[str, Any]) -> Dict:
        """Analyze image using cloud vision APIs"""
        # Placeholder for cloud vision API integration
        # This would integrate with OpenAI GPT-4V, Anthropic Claude 3, etc.
        
        return {
            'scene_description': 'Cloud analysis placeholder - advanced visual understanding',
            'emotions': [
                {'emotion': 'joy', 'confidence': 0.85, 'intensity': 0.8}
            ],
            'image_type': 'photo',
            'people_count': 1,
            'contains_faces': True,
            'confidence': 0.85
        }


# Factory function for easy instantiation
def create_visual_emotion_processor(deployment_mode: str = None) -> VisualEmotionProcessor:
    """Factory function to create visual emotion processor"""
    return VisualEmotionProcessor(deployment_mode)


# CLI testing interface
if __name__ == "__main__":
    import asyncio
    
    async def test_processor():
        processor = create_visual_emotion_processor()
        
        # Test with dummy image data
        dummy_image = b"dummy_image_data_for_testing"
        context = {
            'user_id': 'test_user',
            'channel_id': 'test_channel',
            'message_text': 'Here is my image!',
            'filename': 'test.jpg'
        }
        
        result = await processor.analyze_image(dummy_image, context)
        print(f"📊 Analysis Result: {result}")
    
    asyncio.run(test_processor())
```

### Step 2: Test the Basic Processor

```bash
# Test the basic processor
cd /Users/markcastillo/git/whisperengine
source .venv/bin/activate
python src/emotion/visual_emotion_processor.py
```

### Step 3: Add Discord Integration

Next, we'll create the Discord handler that uses this processor.

## 🎯 Ready to Start?

This gives you a working foundation that you can build upon. The processor handles both local and cloud modes, respects the privacy architecture, and provides a clean interface for Discord integration.

Want to create this file and start building? 🚀