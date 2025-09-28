# WhisperEngine Voice Chat Integration

## Overview

WhisperEngine now supports **voice chat integration** in the web UI using the existing ElevenLabs configuration. This enables users to:

- 🎤 **Record voice messages** using their microphone
- 🗣️ **Convert speech to text** via ElevenLabs STT API
- 🔊 **Receive AI responses as audio** via ElevenLabs TTS API
- ⚙️ **Customize voice settings** (voice ID, stability, similarity, style)
- 🎭 **Choose from available voices** for different AI characters

## Architecture

### Web Voice Handler (`src/web/voice_handler.py`)
- **Purpose**: Adapts existing ElevenLabs client for web-based voice chat
- **Key Features**:
  - Text-to-speech conversion with custom voice settings
  - Speech-to-text transcription
  - Voice settings management
  - Available voices listing

### Voice API Endpoints (`src/web/voice_api.py`)
- **Base URL**: `/api/voice`
- **Endpoints**:
  - `POST /api/voice/tts` - Convert text to speech (returns base64 audio)
  - `POST /api/voice/stt` - Convert speech to text (accepts audio file)
  - `GET /api/voice/voices` - List available voices
  - `GET /api/voice/settings` - Get current voice settings
  - `PUT /api/voice/settings` - Update voice settings
  - `GET /api/voice/health` - Voice service health check

### Frontend Voice Chat (`src/web/static/voice-chat.js`)
- **Purpose**: JavaScript library for browser-based voice interactions
- **Features**:
  - Web Audio API integration for microphone access
  - Real-time audio recording and playback
  - Base64 audio encoding/decoding
  - Automatic voice settings management
  - Event-driven callback system

## Using Existing ElevenLabs Configuration

The voice chat system **reuses your existing ElevenLabs setup**:

### Environment Variables (Already Configured)
```bash
# From your .env.* files
VOICE_SERVICE_TYPE=discord_elevenlabs
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_DEFAULT_VOICE_ID=your_voice_id_here
ELEVENLABS_VOICE_STABILITY=0.5
ELEVENLABS_VOICE_SIMILARITY_BOOST=0.8
ELEVENLABS_VOICE_STYLE=0.0
ELEVENLABS_USE_SPEAKER_BOOST=true
```

### Bot-Specific Voice Configuration
Each bot can have its own voice:
- **Elena**: Marine biologist voice (ocean-like, calming)
- **Marcus**: AI researcher voice (technical, precise) 
- **Marcus Chen**: Game developer voice (energetic, creative)
- **Dream**: Mythological voice (ethereal, mysterious)
- **Gabriel**: Spiritual guide voice (warm, compassionate)

## Integration Steps

### 1. Enable Voice API in Web App

The voice API is automatically included in `simple_chat_app.py`:

```python
# Include voice API routes
try:
    from src.web.voice_api import voice_router
    self.app.include_router(voice_router)
    logger.info("Voice API routes included")
except Exception as e:
    logger.warning("Failed to include voice API routes: %s", e)
```

### 2. Add Voice Controls to HTML

Example voice chat integration in your web interface:

```html
<!-- Include voice chat library -->
<script src="/static/voice-chat.js"></script>

<!-- Voice controls -->
<button onclick="toggleRecording()">🎤 Record</button>
<button onclick="testTTS()">🔊 Test TTS</button>

<script>
// Initialize voice chat
const voiceChat = new VoiceChat('/api/voice');

// Setup callbacks
voiceChat.onTranscription = async (text) => {
    // Send to AI bot and get response
    const aiResponse = await sendToBot(text);
    
    // Convert AI response to speech
    await voiceChat.textToSpeech(aiResponse);
};

// Toggle recording
async function toggleRecording() {
    if (voiceChat.isRecording) {
        voiceChat.stopRecording();
    } else {
        await voiceChat.startRecording();
    }
}
</script>
```

### 3. Voice Settings Management

```javascript
// Get available voices
const voices = await voiceChat.loadAvailableVoices();

// Update voice settings
await voiceChat.updateVoiceSettings({
    voice_id: "new_voice_id",
    stability: 0.7,
    similarity_boost: 0.9,
    style: 0.2,
    use_speaker_boost: true
});
```

## Demo Implementation

A complete demo is available at `src/web/voice_chat_demo.html` with:

- ✅ **Real-time voice recording** with visual feedback
- ✅ **Speech-to-text transcription** display
- ✅ **Text-to-speech playback** with audio controls
- ✅ **Voice settings configuration** (voice selection, stability, etc.)
- ✅ **Health monitoring** for voice service status
- ✅ **Audio visualizer** during recording

## API Usage Examples

### Convert Text to Speech
```bash
curl -X POST "http://localhost:8081/api/voice/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello! I am Elena, your marine biologist AI companion.",
    "voice_id": "ked1vRAQW5Sk9vhZC3vI"
  }'
```

### Convert Speech to Text
```bash
curl -X POST "http://localhost:8081/api/voice/stt" \
  -F "audio_file=@recording.webm"
```

### List Available Voices
```bash
curl "http://localhost:8081/api/voice/voices"
```

## Voice Chat Workflow

1. **User clicks "Record"** → JavaScript requests microphone access
2. **User speaks** → Audio is recorded using Web Audio API
3. **User stops recording** → Audio blob is sent to `/api/voice/stt`
4. **Speech-to-text** → ElevenLabs converts audio to text
5. **Send to AI bot** → Text is processed by selected AI companion
6. **AI responds** → Bot returns text response
7. **Text-to-speech** → ElevenLabs converts response to audio
8. **Audio playback** → User hears AI response through speakers

## Character-Specific Voices

Configure different voices for each AI companion:

```javascript
const characterVoices = {
    'elena': 'ocean_voice_id',      // Marine biologist
    'marcus': 'tech_voice_id',      // AI researcher  
    'marcus-chen': 'creative_voice_id', // Game developer
    'dream': 'ethereal_voice_id',   // Mythological being
    'gabriel': 'warm_voice_id'      // Spiritual guide
};

// Use character-specific voice
await voiceChat.textToSpeech(response, characterVoices[botName]);
```

## Browser Compatibility

Voice chat requires modern browser features:
- ✅ **Web Audio API** (for microphone access)
- ✅ **MediaRecorder API** (for audio recording)
- ✅ **Fetch API** (for API communication)
- ✅ **Async/Await** (for promise handling)

Supported browsers:
- Chrome 47+ ✅
- Firefox 25+ ✅  
- Safari 14.1+ ✅
- Edge 79+ ✅

## Security Considerations

- 🔐 **API Key Security**: ElevenLabs API keys are handled server-side only
- 🔐 **HTTPS Required**: Voice recording requires secure contexts (HTTPS/localhost)
- 🔐 **User Permission**: Microphone access requires explicit user consent
- 🔐 **Rate Limiting**: ElevenLabs API has usage limits and costs

## Testing Voice Integration

Start the web UI with voice support:

```bash
# Ensure infrastructure is running
./multi-bot.sh start all

# Set PostgreSQL environment for web UI
export POSTGRES_HOST=localhost POSTGRES_PORT=5433 POSTGRES_DB=whisperengine 
export POSTGRES_USER=whisperengine POSTGRES_PASSWORD=whisperengine123

# Start web interface with voice support
source .venv/bin/activate
python src/web/simple_chat_app.py
```

Then visit:
- **Main Interface**: http://localhost:8081 (full chat with voice integration)
- **Voice Demo**: http://localhost:8081/voice_chat_demo.html (voice-focused demo)

## Cost Considerations

ElevenLabs charges per character:
- **Text-to-Speech**: ~$0.30 per 1K characters
- **Speech-to-Text**: ~$0.20 per minute of audio
- **Voice Cloning**: Additional costs for custom voices

Monitor usage in ElevenLabs dashboard and set appropriate limits.

## Future Enhancements

Potential voice chat improvements:
- 🎯 **Real-time streaming** (WebSocket + streaming TTS)
- 🎯 **Voice activity detection** (automatic start/stop recording)
- 🎯 **Multi-language support** (automatic language detection)
- 🎯 **Voice emotions** (emotional tone analysis and synthesis)
- 🎯 **Voice interruption** (stop AI mid-sentence for more natural conversation)

## Troubleshooting

### Common Issues

**"Voice service unavailable"**
- Check ElevenLabs API key in environment variables
- Verify API key has sufficient credits
- Test `/api/voice/health` endpoint

**"Microphone not accessible"**
- Ensure HTTPS or localhost (required for microphone access)
- Check browser permissions for microphone
- Test with different browsers

**"Audio playback fails"**
- Check browser audio settings
- Verify audio codec support (MP3)
- Test with different audio formats

**"ElevenLabs rate limit exceeded"**
- Check API usage in ElevenLabs dashboard
- Implement request queuing/throttling
- Consider upgrading ElevenLabs plan

---

The voice chat integration leverages WhisperEngine's existing ElevenLabs infrastructure to provide seamless voice interactions with AI companions, making conversations more natural and engaging! 🎤✨