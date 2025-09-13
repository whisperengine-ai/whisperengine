# Discord Voice Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### 1. Install Dependencies
```bash
pip install PyNaCl wave audioop-lts
```

### 2. Install FFmpeg
- **macOS**: `brew install ffmpeg`
- **Ubuntu**: `sudo apt install ffmpeg`
- **Windows**: Download from https://ffmpeg.org/

### 3. Get ElevenLabs API Key
1. Sign up at https://elevenlabs.io/
2. Go to Profile → API Keys
3. Copy your API key

### 4. Add to .env File
```env
ELEVENLABS_API_KEY=your_api_key_here
VOICE_RESPONSE_ENABLED=true
VOICE_LISTENING_ENABLED=true
```

### 5. Test Setup
```bash
python setup_voice.py
```

### 6. Start Your Bot
```bash
python basic_discord_bot.py
```

## 🎤 Basic Usage

### Join Voice Channel
```
!join                 # Joins your current voice channel
!join "General"       # Joins specific channel
```

### Make Bot Speak
```
!speak Hello everyone!
!tts Good morning!
```

### Voice Status
```
!voice_status         # Shows current status
!voice_help          # Shows all commands
```

### Leave Voice Channel
```
!leave
```

## 🎯 How It Works

1. **Join Voice**: Bot joins your voice channel
2. **Listen**: Bot automatically listens for voice messages
3. **Process**: Converts speech to text with ElevenLabs
4. **Respond**: Bot responds with both text and voice
5. **Remember**: Voice conversations stored in memory

## 🛠️ Common Issues

### "Voice functionality unavailable"
- Run: `pip install PyNaCl`
- Install FFmpeg
- Check all dependencies

### "Invalid API key"
- Verify key in .env file
- Check ElevenLabs account has credits
- Ensure key has proper permissions

### "Cannot join voice channel"
- Check bot has Connect permission
- Verify Speak permission enabled
- Make sure channel isn't full

## 🔧 Voice Settings

### Quality Settings (.env)
```env
ELEVENLABS_VOICE_STABILITY=0.5        # 0.0-1.0 (expressiveness)
ELEVENLABS_VOICE_SIMILARITY_BOOST=0.8 # 0.0-1.0 (voice matching)
ELEVENLABS_VOICE_STYLE=0.0            # 0.0-1.0 (naturalness)
```

### Voice Selection
1. Find voices at https://elevenlabs.io/voices
2. Copy Voice ID
3. Set `ELEVENLABS_DEFAULT_VOICE_ID=voice_id_here`

### Performance Tuning
```env
VOICE_MAX_AUDIO_LENGTH=30     # Max seconds per voice message
VOICE_RESPONSE_DELAY=1.0      # Delay between responses
ELEVENLABS_REQUEST_TIMEOUT=30 # API timeout
```

## 🎮 Advanced Features

### Admin Commands
```
!voice_toggle_listening    # Toggle voice listening (Admin only)
!voice_settings           # Show detailed settings (Admin only)
```

### Voice Testing
```
!voice_test               # Test voice functionality
```

### Multiple Languages
```env
ELEVENLABS_TTS_MODEL=eleven_multilingual_v1  # For multi-language support
```

## 📊 Monitoring

### Check Status
- `!voice_status` - Current voice state
- `!bot_status` - Overall bot health
- Monitor logs for voice errors

### Usage Tracking
- Check ElevenLabs dashboard for API usage
- Monitor Discord bot logs
- Track voice command usage

## 💡 Tips

1. **Voice Quality**: Lower stability = more expressive
2. **Performance**: Use monolingual model for English only
3. **Costs**: Monitor ElevenLabs usage to control costs
4. **Privacy**: Voice data is sent to ElevenLabs for processing

## 🔗 Resources

- Full Documentation: `docs/VOICE_INTEGRATION_GUIDE.md`
- Voice Setup Script: `python setup_voice.py`
- ElevenLabs Docs: https://docs.elevenlabs.io/
- Discord Voice Docs: https://discordpy.readthedocs.io/

---

**Need Help?** Check the full documentation or run `!voice_help` in Discord!
