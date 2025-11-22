from typing import List, Dict, Any, Optional
import json
import datetime
from pathlib import Path
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from loguru import logger

from src_v2.config.settings import settings
from src_v2.core.character import Character
from src_v2.agents.llm_factory import create_llm

class AgentEngine:
    def __init__(self):
        self.llm = create_llm()
        logger.info("AgentEngine initialized")

    async def generate_response(
        self, 
        character: Character, 
        user_message: str, 
        chat_history: Optional[List[BaseMessage]] = None,
        context_variables: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> str:
        """
        Generates a response for the given character and user message.
        """
        chat_history = chat_history or []
        context_variables = context_variables or {}
        
        # 1. Construct System Prompt
        # The character object already contains the full prompt loaded from the markdown file
        system_content = character.system_prompt
        
        # 2. Create Prompt Template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_content),
            MessagesPlaceholder(variable_name="chat_history"),
            MessagesPlaceholder(variable_name="user_input_message")
        ])

        # 3. Create Chain
        chain = prompt | self.llm

        # 4. Execute
        try:
            # Prepare input content
            if image_url and settings.LLM_SUPPORTS_VISION:
                # Multimodal input
                input_content = [
                    {"type": "text", "text": user_message},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    }
                ]
            else:
                # Text-only input
                input_content = user_message

            # Wrap in HumanMessage to ensure structure is preserved
            user_input_message = [HumanMessage(content=input_content)]

            # Prepare inputs
            inputs = {
                "chat_history": chat_history,
                "user_input_message": user_input_message,
                **context_variables
            }
            
            response = await chain.ainvoke(inputs)
            
            # 5. Log Prompt (if enabled)
            if settings.ENABLE_PROMPT_LOGGING:
                await self._log_prompt(
                    character_name=character.name,
                    user_id=user_id or "unknown",
                    system_prompt=system_content,
                    chat_history=chat_history,
                    user_input=user_message,
                    context_variables=context_variables,
                    response=response.content,
                    image_url=image_url
                )
            
            return response.content
            
        except Exception as e:
            logger.exception(f"Error generating response: {e}")
            return "I'm having a bit of trouble thinking right now..." # Fallback response

    async def _log_prompt(
        self,
        character_name: str,
        user_id: str,
        system_prompt: str,
        chat_history: List[BaseMessage],
        user_input: str,
        context_variables: Dict[str, Any],
        response: str,
        image_url: Optional[str] = None
    ):
        """
        Logs the full prompt context and response to a JSON file.
        """
        try:
            # Create logs directory if it doesn't exist
            log_dir = Path("logs/prompts")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename: {BotName}_{YYYYMMDD}_{HHMMSS}_{UserID}.json
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{character_name}_{timestamp}_{user_id}.json"
            file_path = log_dir / filename
            
            # Serialize chat history
            history_serialized = []
            for msg in chat_history:
                role = "unknown"
                if isinstance(msg, HumanMessage): role = "human"
                elif isinstance(msg, AIMessage): role = "ai"
                elif isinstance(msg, SystemMessage): role = "system"
                
                history_serialized.append({
                    "role": role,
                    "content": msg.content
                })
            
            # Construct log data
            log_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "character": character_name,
                "user_id": user_id,
                "inputs": {
                    "system_prompt": system_prompt,
                    "context_variables": context_variables,
                    "chat_history": history_serialized,
                    "user_input": user_input,
                    "image_url": image_url
                },
                "response": response
            }
            
            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"Prompt logged to {file_path}")
            
        except Exception as e:
            logger.warning(f"Failed to log prompt: {e}")
