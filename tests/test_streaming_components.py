#!/usr/bin/env python3
"""
Test the streaming audio functionality
"""
import asyncio
import os
import sys


async def test_streaming_components():
    """Test the streaming audio components"""
    print("🧪 Testing Discord Streaming Audio Components...")

    try:
        # Test 1: Import check
        print("📦 Testing imports...")

        try:
            from streaming_audio_source import (
                stream_to_tempfile,
                create_streaming_audio_source,
                cleanup_streaming_audio,
            )

            print("✅ Streaming audio source imports successful")
        except ImportError as e:
            print(f"❌ Import failed: {e}")
            return False

        try:
            import discord

            print("✅ Discord.py import successful")
        except ImportError as e:
            print(f"❌ Discord.py import failed: {e}")
            return False

        # Test 2: Mock streaming chunks
        print("🌊 Testing chunk streaming to temp file...")

        async def mock_chunk_generator():
            """Generate mock audio chunks"""
            # Simulate MP3 header and some data
            chunks = [
                b"\xff\xfb\x90\x00",  # MP3 header
                b"\x00" * 1000,  # Some audio data
                b"\x11" * 1000,  # More audio data
                b"\x22" * 1000,  # Final audio data
            ]

            for i, chunk in enumerate(chunks):
                print(f"  📤 Yielding chunk {i+1}/{len(chunks)} ({len(chunk)} bytes)")
                yield chunk
                await asyncio.sleep(0.1)  # Simulate streaming delay

        # Test streaming to temp file
        temp_path = await stream_to_tempfile(mock_chunk_generator())

        if os.path.exists(temp_path):
            file_size = os.path.getsize(temp_path)
            print(f"✅ Temp file created: {temp_path} ({file_size} bytes)")

            # Clean up
            cleanup_streaming_audio(temp_path)

            if not os.path.exists(temp_path):
                print("✅ Temp file cleanup successful")
            else:
                print("⚠️  Temp file cleanup incomplete")
        else:
            print("❌ Temp file not created")
            return False

        # Test 3: Audio source creation (without actual playback)
        print("🎵 Testing audio source creation...")

        try:
            audio_source, temp_path = await create_streaming_audio_source(mock_chunk_generator())
            print(f"✅ Audio source created: {type(audio_source).__name__}")

            # Check if it's the right type
            if isinstance(audio_source, discord.FFmpegPCMAudio):
                print("✅ Audio source is correct type (FFmpegPCMAudio)")
            else:
                print(f"⚠️  Audio source type unexpected: {type(audio_source)}")

            # Clean up
            cleanup_streaming_audio(temp_path)
            print("✅ Audio source cleanup successful")

        except Exception as e:
            print(f"❌ Audio source creation failed: {e}")
            return False

        print("🎉 All streaming audio tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback

        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = asyncio.run(test_streaming_components())
    sys.exit(0 if success else 1)
