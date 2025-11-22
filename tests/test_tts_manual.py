import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src_v2.voice.tts import TTSManager
from src_v2.config.settings import settings

async def main():
    print("Testing TTSManager...")
    
    if not settings.ELEVENLABS_API_KEY:
        print("SKIPPING: ELEVENLABS_API_KEY not set in environment.")
        return

    tts = TTSManager()
    if not tts.client:
        print("TTS Client failed to initialize.")
        return

    text = "Hello! This is a test of the Whisper Engine voice system."
    print(f"Generating speech for: '{text}'")
    
    try:
        audio_data = await tts.generate_speech(text)
        
        if audio_data:
            output_file = "test_tts_output.mp3"
            with open(output_file, "wb") as f:
                f.write(audio_data)
            print(f"SUCCESS: Audio generated and saved to {output_file} ({len(audio_data)} bytes)")
        else:
            print("FAILURE: No audio data returned.")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
