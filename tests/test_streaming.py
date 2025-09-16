#!/usr/bin/env python3
"""
Test script to verify ElevenLabs streaming functionality
"""
import os
import asyncio
import time
from elevenlabs_client import ElevenLabsClient


async def test_streaming_vs_regular():
    """Compare streaming vs regular TTS performance"""
    print("Testing ElevenLabs Streaming vs Regular TTS...")

    # Check for API key
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found in environment")
        print("Set ELEVENLABS_API_KEY to test streaming functionality")
        return

    if api_key == "your_elevenlabs_api_key_here":
        print("❌ Please set a real ElevenLabs API key to test streaming")
        return

    client = ElevenLabsClient(api_key)
    test_text = "This is a test of the ElevenLabs streaming API. The streaming version should start producing audio much faster than the regular version."

    print(f"🧪 Test text: {test_text}")
    print()

    try:
        # Test regular TTS
        print("📥 Testing regular TTS (non-streaming)...")
        start_time = time.time()
        regular_audio = await client.text_to_speech(test_text, stream=False)
        regular_time = time.time() - start_time
        print(f"✅ Regular TTS: {len(regular_audio)} bytes in {regular_time:.2f} seconds")

        # Test streaming TTS
        print("🌊 Testing streaming TTS...")
        start_time = time.time()
        streaming_audio = await client.text_to_speech(test_text, stream=True)
        streaming_time = time.time() - start_time
        print(f"✅ Streaming TTS: {len(streaming_audio)} bytes in {streaming_time:.2f} seconds")

        # Test the actual streaming generator
        print("⚡ Testing real-time streaming (generator)...")
        start_time = time.time()
        chunks = []
        first_chunk_time = None

        async for chunk in client.text_to_speech_stream(test_text):
            if first_chunk_time is None:
                first_chunk_time = time.time() - start_time
                print(f"🎯 First chunk received in {first_chunk_time:.2f} seconds")
            chunks.append(chunk)

        total_streaming_time = time.time() - start_time
        streaming_generator_audio = b"".join(chunks)

        print(
            f"✅ Streaming generator: {len(streaming_generator_audio)} bytes in {total_streaming_time:.2f} seconds"
        )
        print(
            f"⚡ Time to first chunk: {first_chunk_time:.2f} seconds ({len(chunks)} total chunks)"
        )

        # Compare results
        print("\n📊 Performance Comparison:")
        print(f"Regular TTS:          {regular_time:.2f}s (complete audio)")
        print(f"Streaming TTS:        {streaming_time:.2f}s (complete audio)")
        print(f"Streaming (1st chunk): {first_chunk_time:.2f}s (audio starts playing)")

        if first_chunk_time and first_chunk_time < regular_time:
            improvement = ((regular_time - first_chunk_time) / regular_time) * 100
            print(f"🚀 Streaming is {improvement:.1f}% faster to start playing!")

        # Verify audio data integrity
        if len(regular_audio) == len(streaming_audio) == len(streaming_generator_audio):
            print("✅ All methods produced same amount of audio data")
        else:
            print(
                f"⚠️  Audio size mismatch: regular={len(regular_audio)}, streaming={len(streaming_audio)}, generator={len(streaming_generator_audio)}"
            )

        print("\n🎉 Streaming functionality test completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        print(traceback.format_exc())


if __name__ == "__main__":
    # Load environment for testing
    try:
        from dotenv import load_dotenv

        load_dotenv(".env.dream")  # Use dream config for testing
    except ImportError:
        pass

    asyncio.run(test_streaming_vs_regular())
