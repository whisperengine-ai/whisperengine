import discord
import tempfile
import os
import asyncio
from loguru import logger
from src_v2.voice.service import voice_service

async def play_text(voice_client: discord.VoiceClient, text: str):
    """
    Generates audio for the text and plays it in the voice channel.
    """
    if not voice_client or not voice_client.is_connected():
        logger.warning("Voice client not connected.")
        return

    logger.info(f"play_text called with {len(text)} chars. Voice client: {voice_client.channel}")

    temp_path = None
    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_path = temp_file.name
            logger.debug(f"Created temp audio file: {temp_path}")

        # Download stream to file
        logger.info(f"Generating audio for: '{text[:30]}...'")
        
        # Check if we got any chunks
        has_content = False
        chunk_count = 0
        total_bytes = 0
        
        async for chunk in voice_service.generate_audio_stream(text):
            with open(temp_path, "ab") as f:
                f.write(chunk)
            has_content = True
            chunk_count += 1
            total_bytes += len(chunk)
            
        logger.info(f"Audio generation complete. Chunks: {chunk_count}, Bytes: {total_bytes}")
            
        if not has_content:
            logger.warning("No audio generated (0 chunks).")
            os.remove(temp_path)
            return
        
        # Play
        logger.info(f"Playing audio from {temp_path}...")
        
        def after_playing(error):
            if error:
                logger.error(f"Error in playback: {error}")
            else:
                logger.info("Playback finished successfully.")
            # Cleanup
            try:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                    logger.debug("Temp file removed.")
            except Exception as e:
                logger.warning(f"Failed to remove temp file: {e}")

        # Stop any current playback
        if voice_client.is_playing():
            logger.info("Stopping current playback to start new one.")
            voice_client.stop()

        source = discord.FFmpegPCMAudio(temp_path)
        voice_client.play(source, after=after_playing)
        logger.info("Playback started.")

    except Exception as e:
        logger.exception(f"Error in play_text: {e}")
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
