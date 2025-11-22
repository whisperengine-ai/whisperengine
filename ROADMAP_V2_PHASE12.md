# Roadmap V2 - Phase 12: Multimodal Capabilities (Voice & Vision)

This phase brings the character to life by giving them a voice and the ability to see. We will integrate ElevenLabs for high-quality TTS and enable the bot to understand images shared by users.

## Goals
- [ ] **Voice Output (TTS)**: Integrate ElevenLabs API to generate speech from bot responses.
- [ ] **Discord Voice**: Implement a Discord Voice Client to join voice channels and stream audio.
- [ ] **Vision Support**: Enable the bot to "see" images sent by users and describe/react to them.
- [ ] **Multimodal Memory**: Store descriptions of seen images in vector memory.

## Tasks

### 1. ElevenLabs Integration (`src_v2/voice/tts.py`)
- [x] Create `TTSManager` class.
- [x] Implement `generate_speech(text, voice_id)`:
    - Calls ElevenLabs API.
    - Returns audio stream or file path.
    - Caches common phrases (optional).
- [x] Add `ELEVENLABS_API_KEY` to `settings.py`.

### 2. Discord Voice Client (`src_v2/discord/voice.py`)
- [x] Create `VoiceManager` class.
- [x] Implement `join_channel(channel_id)`.
- [x] Implement `speak(audio_source)`.
- [x] Handle voice state updates (joining/leaving).

### 3. Vision Support (`src_v2/vision/manager.py`)
- [x] Update `AgentEngine` to handle `image_urls`.
- [x] Update `LLMFactory` to support multimodal models (gpt-4o, claude-3-opus).
- [x] Implement `analyze_image(image_url)`:
    - Generates a text description of the image.
    - Stores this description in `v2_memories` (so the bot remembers seeing it).

### 4. Integration
- [x] Add `/join` and `/leave` commands to `src_v2/discord/commands.py`.
- [x] Update `MessageProcessor` to detect attachments and trigger vision pipeline.
- [x] Update `MessageProcessor` to trigger TTS if in a voice channel.

## Success Criteria
- [x] Bot can join a voice channel and speak its response.
- [x] Bot can describe an image sent by the user ("That's a cute cat!").
- [x] Bot remembers the image content in future turns.
