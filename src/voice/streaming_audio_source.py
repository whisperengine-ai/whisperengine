"""
Streaming audio utilities for Discord.py that works with ElevenLabs streaming API
"""

import asyncio
import logging
import os
import tempfile
from collections.abc import AsyncGenerator

import discord


async def stream_to_tempfile(
    chunk_generator: AsyncGenerator[bytes], logger: logging.Logger | None = None
) -> str:
    """
    Stream audio chunks to a temporary file as they arrive for immediate playback

    Args:
        chunk_generator: Async generator that yields audio chunks
        logger: Optional logger instance

    Returns:
        Path to temporary file containing streamed audio
    """
    logger = logger or logging.getLogger(__name__)

    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    temp_path = temp_file.name

    chunks_received = 0
    total_bytes = 0

    try:
        # Start writing chunks to file as they arrive
        async for chunk in chunk_generator:
            temp_file.write(chunk)
            temp_file.flush()  # Ensure data is written immediately for concurrent reading

            chunks_received += 1
            total_bytes += len(chunk)

            if chunks_received == 1:
                logger.debug(f"First chunk written to {temp_path}, streaming can begin")

            # Small delay to prevent overwhelming the file system
            await asyncio.sleep(0.005)  # 5ms delay

    except Exception as e:
        logger.error(f"Error streaming chunks to file: {e}")
    finally:
        temp_file.close()
        logger.debug(
            f"Streaming complete: {chunks_received} chunks, {total_bytes} bytes -> {temp_path}"
        )

    return temp_path


async def create_streaming_audio_source(
    chunk_generator: AsyncGenerator[bytes], logger: logging.Logger | None = None
) -> tuple[discord.FFmpegPCMAudio, str]:
    """
    Create a Discord audio source from streaming audio chunks with minimal latency

    Args:
        chunk_generator: Async generator that yields audio chunks
        logger: Optional logger instance

    Returns:
        Tuple of (Discord audio source ready for playback, temporary file path for cleanup)
    """
    logger = logger or logging.getLogger(__name__)

    # Start streaming to temporary file in background
    temp_path = await stream_to_tempfile(chunk_generator, logger)

    # Create audio source that can start playing while file is still being written
    # FFmpeg can handle reading from a file that's still being written to
    audio_source = discord.FFmpegPCMAudio(
        temp_path,
        before_options="-re",  # Read input at its native frame rate (important for streaming)
        options="-vn",  # Disable video processing
    )

    logger.debug(f"Created streaming audio source from {temp_path}")
    return audio_source, temp_path


def cleanup_streaming_audio(temp_path: str, logger: logging.Logger | None = None):
    """
    Clean up temporary files created for streaming audio

    Args:
        temp_path: Path to temporary file to clean up
        logger: Optional logger instance
    """
    logger = logger or logging.getLogger(__name__)

    try:
        os.unlink(temp_path)
        logger.debug(f"Cleaned up streaming audio temp file: {temp_path}")
    except Exception as e:
        logger.debug(f"Error cleaning up temp file: {e}")
