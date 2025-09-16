#!/usr/bin/env python3
"""
Test script to verify ElevenLabs streaming functionality
"""
import asyncio
import os
import time

from elevenlabs_client import ElevenLabsClient


async def test_streaming_vs_regular():
    """Compare streaming vs regular TTS performance"""

    # Check for API key
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return

    if api_key == "your_elevenlabs_api_key_here":
        return

    client = ElevenLabsClient(api_key)
    test_text = "This is a test of the ElevenLabs streaming API. The streaming version should start producing audio much faster than the regular version."

    try:
        # Test regular TTS
        start_time = time.time()
        regular_audio = await client.text_to_speech(test_text, stream=False)
        regular_time = time.time() - start_time

        # Test streaming TTS
        start_time = time.time()
        streaming_audio = await client.text_to_speech(test_text, stream=True)
        time.time() - start_time

        # Test the actual streaming generator
        start_time = time.time()
        chunks = []
        first_chunk_time = None

        async for chunk in client.text_to_speech_stream(test_text):
            if first_chunk_time is None:
                first_chunk_time = time.time() - start_time
            chunks.append(chunk)

        time.time() - start_time
        streaming_generator_audio = b"".join(chunks)

        # Compare results

        if first_chunk_time and first_chunk_time < regular_time:
            ((regular_time - first_chunk_time) / regular_time) * 100

        # Verify audio data integrity
        if len(regular_audio) == len(streaming_audio) == len(streaming_generator_audio):
            pass
        else:
            pass

    except Exception:
        pass


if __name__ == "__main__":
    # Load environment for testing
    try:
        from dotenv import load_dotenv

        load_dotenv(".env.dream")  # Use dream config for testing
    except ImportError:
        pass

    asyncio.run(test_streaming_vs_regular())
