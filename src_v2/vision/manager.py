from typing import Optional
from loguru import logger
from langchain_core.messages import HumanMessage
from src_v2.agents.llm_factory import create_llm
from src_v2.config.settings import settings
from src_v2.memory.manager import memory_manager

class VisionManager:
    def __init__(self):
        self.llm = create_llm(temperature=0.5) # Use a slightly lower temp for accurate descriptions

    async def analyze_and_store(self, image_url: str, user_id: str, channel_id: str) -> Optional[str]:
        """
        Analyzes an image using a multimodal LLM and stores the description in memory.
        Returns the description.
        """
        if not settings.LLM_SUPPORTS_VISION:
            logger.warning("Vision analysis requested but LLM_SUPPORTS_VISION is False.")
            return None

        try:
            logger.info(f"Analyzing image: {image_url}")
            
            # 1. Generate Description
            prompt = [
                HumanMessage(
                    content=[
                        {"type": "text", "text": "Describe this image in detail. Focus on the main subjects, setting, colors, and any text visible. Be objective but comprehensive."},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                )
            ]
            
            response = await self.llm.ainvoke(prompt)
            description = response.content
            
            logger.info(f"Image description generated: {description[:50]}...")

            # 2. Store in Memory
            # We store it as a "system" or "observation" memory so the bot knows it "saw" this.
            # We prefix it to make it clear it's an image description.
            memory_content = f"[Visual Memory] User sent an image. Description: {description}"
            
            await memory_manager.add_message(
                user_id=user_id,
                character_name=settings.DISCORD_BOT_NAME or "default_bot",
                role="system",
                content=memory_content,
                channel_id=channel_id,
                metadata={"type": "image_analysis", "image_url": image_url}
            )
            
            return str(description)

        except Exception as e:
            logger.error(f"Failed to analyze image: {e}")
            return None

vision_manager = VisionManager()
