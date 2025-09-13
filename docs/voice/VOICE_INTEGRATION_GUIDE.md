# Discord Voice Integration with ElevenLabs

This document explains the Discord Voice functionality that has been added to your bot, including setup, usage, and architecture.

## 🎤 Features

### Text-to-Speech (TTS)
- Convert bot responses to natural-sounding speech
- High-quality ElevenLabs voice synthesis with **streaming API support**
- **Low-latency streaming**: Audio starts playing immediately as it's generated
- Configurable voice settings (stability, similarity, style)
- Multiple output formats optimized for Discord
- Streaming optimization levels (0-4) for cost vs latency balance

### Speech-to-Text (STT)
- Process voice messages from users in voice channels
- Automatic transcription of spoken input
- Integration with existing conversation memory
- Multi-language support

### Voice Commands
- Join/leave voice channels
- Manual text-to-speech conversion
- Voice status monitoring
- Administrative controls

## 🛠️ Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

The voice functionality requires these additional packages:
- `PyNaCl>=1.5.0` - For Discord voice connection
- `wave` - For audio processing
- `audioop-lts>=0.2.1` - For audio operations

### 2. Install FFmpeg

FFmpeg is required for audio processing:

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html and add to PATH.

### 3. ElevenLabs Setup

1. Sign up at https://elevenlabs.io/
2. Get your API key from your profile
3. Browse available voices and note the Voice ID you want to use

### 4. Environment Configuration

Add these variables to your `.env` file:

```env
# === ElevenLabs Configuration ===
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_DEFAULT_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # Rachel voice

# Voice feature toggles
VOICE_RESPONSE_ENABLED=true
VOICE_LISTENING_ENABLED=true
VOICE_MAX_AUDIO_LENGTH=30

# Optional: Fine-tune voice settings
ELEVENLABS_VOICE_STABILITY=0.5
ELEVENLABS_VOICE_SIMILARITY_BOOST=0.8
ELEVENLABS_VOICE_STYLE=0.0
ELEVENLABS_USE_SPEAKER_BOOST=true

# Streaming settings for lower latency (recommended)
ELEVENLABS_USE_STREAMING=true              # Enable streaming API
ELEVENLABS_OPTIMIZE_STREAMING=2            # 0-4, higher = lower latency but higher cost
```

See `.env.voice.example` for all available configuration options.

## 🎮 Usage

### Basic Voice Commands

#### Join Voice Channel
```
!join                    # Joins your current voice channel
!join "General Voice"    # Joins specific channel by name
```

#### Leave Voice Channel
```
!leave                   # Leaves current voice channel
```

#### Text-to-Speech
```
!speak Hello everyone!   # Makes bot speak the text
!tts Good morning!       # Alternative command
```

#### Voice Status
```
!voice_status           # Shows current voice status
!vstatus                # Short version
```

#### Voice Help
```
!voice_help             # Shows all voice commands
!vhelp                  # Short version
```

### Admin Commands (Require Manage Server permission)

#### Toggle Listening
```
!voice_toggle_listening  # Enable/disable voice message listening
```

#### Voice Settings
```
!voice_settings         # Show detailed configuration
```

### Automatic Features

When the bot joins a voice channel:
1. **Voice Listening**: Automatically listens for voice messages from users
2. **Speech Recognition**: Converts speech to text using ElevenLabs STT
3. **AI Processing**: Processes voice messages through your LLM
4. **Voice Response**: Responds with both text and voice (if enabled)
5. **Memory Storage**: Stores voice conversations in your memory system

## 🏗️ Architecture

### Core Components

#### 1. ElevenLabsClient (`elevenlabs_client.py`)
- Handles TTS and STT API calls
- Manages voice settings and audio formats
- Async-compatible with proper error handling
- Configurable timeouts and retry logic

#### 2. DiscordVoiceManager (`voice_manager.py`)
- Manages Discord voice connections
- Handles audio processing and queuing
- Coordinates between Discord and ElevenLabs
- Per-guild voice state management

#### 3. VoiceCommands (`voice_commands.py`)
- Discord commands for voice control
- User-friendly interfaces for voice features
- Error handling and permission checks
- Help and status reporting

### Voice Processing Flow

```
User speaks in voice channel
         ↓
Discord captures audio packets
         ↓
Audio buffered and processed
         ↓
ElevenLabs STT converts to text
         ↓
LLM processes the message
         ↓
Response generated
         ↓
ElevenLabs TTS converts to speech
         ↓
Audio played in voice channel
```

### Memory Integration

Voice messages are integrated with your existing memory system:
- Voice messages tagged with `[Voice]` prefix
- Stored in ChromaDB for future context
- Emotion analysis applied to voice messages
- User profiles updated based on voice interactions

## ⚙️ Configuration Options

### Voice Quality Settings

**Stability (0.0-1.0):**
- Lower = more expressive but variable
- Higher = more consistent but monotone
- Default: 0.5

**Similarity Boost (0.0-1.0):**
- How closely to match the original voice
- Higher = closer to training voice
- Default: 0.8

**Style (0.0-1.0):**
- Amount of stylistic variation
- 0.0 = most natural sounding
- Default: 0.0

### Performance Settings

**Audio Formats:**
- `mp3_44100_128` - Good quality, Discord compatible
- `mp3_22050_32` - Lower quality, faster processing
- `pcm_16000` - Uncompressed, highest quality

**Streaming Optimization (0-4):**
- Higher = lower latency but higher cost
- 0 = standard processing
- 4 = maximum optimization

### Streaming API Benefits

**Why Use Streaming:**
- **Lower Latency**: Audio starts playing immediately as it's generated
- **Better User Experience**: No delay waiting for complete audio generation
- **Natural Conversation Flow**: More responsive, real-time feel
- **Reduced Memory Usage**: No need to buffer entire audio files
- **Cost Optimization**: Balance latency vs cost with optimization levels

**Configuration:**
```env
ELEVENLABS_USE_STREAMING=true              # Enable streaming (recommended)
ELEVENLABS_OPTIMIZE_STREAMING=2            # Balanced latency/cost (0-4)
```

**Performance Comparison:**
- Regular API: 2-5 seconds to start audio playback
- Streaming API: 0.2-0.8 seconds to start audio playback
- Streaming provides 60-90% faster response times

**End-to-End Streaming:**
The bot now supports complete streaming from ElevenLabs to Discord:
1. ElevenLabs generates audio chunks in real-time
2. Chunks are streamed to a temporary file as they arrive
3. Discord starts playing audio while file is still being written
4. Users hear bot responses almost immediately

**Configuration:**
```env
VOICE_STREAMING_ENABLED=true              # Enable voice streaming (recommended)
ELEVENLABS_USE_STREAMING=true              # Enable ElevenLabs streaming API
ELEVENLABS_OPTIMIZE_STREAMING=2            # Streaming optimization level
```

### Bot Behavior

**Response Modes:**
- Text only: `VOICE_RESPONSE_ENABLED=false`
- Voice only: Modify response logic in code
- Both: `VOICE_RESPONSE_ENABLED=true` (default)

**Listening Control:**
- Always listen: `VOICE_LISTENING_ENABLED=true`
- Manual only: `VOICE_LISTENING_ENABLED=false`

## 🔧 Troubleshooting

### Common Issues

#### "Voice functionality unavailable"
- Install PyNaCl: `pip install PyNaCl`
- Install FFmpeg and ensure it's in PATH
- Check all voice dependencies are installed

#### "Invalid ElevenLabs API key"
- Verify API key is correct in `.env`
- Check ElevenLabs account has sufficient credits
- Ensure API key has proper permissions

#### "Cannot join voice channel"
- Check bot has Connect permission in voice channel
- Verify bot has Speak permission
- Ensure voice channel isn't full

#### "Audio processing errors"
- Verify FFmpeg installation
- Check audio format settings
- Monitor ElevenLabs rate limits

### Debug Information

Enable debug logging for voice troubleshooting:
```python
logging.getLogger('voice_manager').setLevel(logging.DEBUG)
logging.getLogger('elevenlabs_client').setLevel(logging.DEBUG)
```

Use `!voice_status` to check current state and `!voice_test` to verify functionality.

## 🎯 Advanced Usage

### Custom Voice Models

ElevenLabs offers different models:
- `eleven_monolingual_v1` - English only, fastest
- `eleven_multilingual_v1` - Multiple languages
- `eleven_turbo_v2` - Fastest generation

### Voice Cloning

1. Create custom voice in ElevenLabs dashboard
2. Copy the Voice ID
3. Set `ELEVENLABS_DEFAULT_VOICE_ID` in your `.env`

### Integration with Emotion System

Voice messages automatically integrate with your emotion system:
- Emotional context influences voice responses
- Voice tone can be adjusted based on detected emotions
- Relationship levels affect response style

### Performance Optimization

For high-traffic servers:
1. Use separate ElevenLabs accounts for TTS and STT
2. Configure different models for different functions
3. Implement voice message queuing
4. Set appropriate rate limits

## 🔐 Security Considerations

### API Key Management
- Store ElevenLabs API key securely
- Use environment variables, never hardcode
- Monitor API usage and costs
- Rotate keys regularly

### Voice Privacy
- Voice messages are sent to ElevenLabs for processing
- Consider privacy implications for users
- Implement opt-out mechanisms if needed
- Review ElevenLabs privacy policy

### Rate Limiting
- ElevenLabs has usage limits
- Implement proper error handling
- Consider caching for repeated phrases
- Monitor costs and usage

## 📊 Monitoring and Analytics

### Voice Usage Metrics
- Track voice command usage
- Monitor TTS/STT API calls
- Measure response times
- Analyze user engagement

### Performance Monitoring
- Audio processing latency
- API response times
- Error rates and types
- Resource usage

### Cost Management
- ElevenLabs usage tracking
- Set up billing alerts
- Optimize for cost-effective usage
- Monitor per-user consumption

## 🔄 Updates and Maintenance

### Regular Maintenance
- Update dependencies regularly
- Monitor ElevenLabs service status
- Review and optimize voice settings
- Clean up voice logs and cache

### Version Compatibility
- Keep discord.py updated for voice features
- Monitor ElevenLabs API changes
- Test voice functionality after updates
- Maintain backup configurations

## 🤝 Contributing

To extend voice functionality:

1. **Adding Voice Commands**: Create new commands in `voice_commands.py`
2. **Custom Audio Processing**: Extend `voice_manager.py`
3. **Additional TTS/STT Providers**: Create new client classes
4. **Voice Effects**: Add audio processing filters

## 📚 Additional Resources

- [ElevenLabs Documentation](https://docs.elevenlabs.io/)
- [Discord.py Voice Documentation](https://discordpy.readthedocs.io/en/stable/api.html#voice-related)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [PyNaCl Documentation](https://pynacl.readthedocs.io/)

---

The voice integration transforms your Discord bot into a fully interactive voice assistant, capable of natural conversations through speech. The modular design allows for easy customization and extension while maintaining compatibility with your existing bot features.
