from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from loguru import logger

from src_v2.config.settings import settings

def create_llm(temperature: Optional[float] = None) -> BaseChatModel:
    """
    Creates a LangChain Chat Model based on the configuration.
    Supports: openai, openrouter, ollama, lmstudio
    """
    provider = settings.LLM_PROVIDER
    api_key = settings.LLM_API_KEY.get_secret_value() if settings.LLM_API_KEY else "dummy"
    base_url = settings.LLM_BASE_URL
    model_name = settings.LLM_MODEL_NAME
    
    # Use default from settings if not provided, or 0.7 as fallback
    temp = temperature if temperature is not None else 0.7

    logger.info(f"Initializing LLM: {provider} ({model_name}) Temp: {temp}")

    if provider == "openai":
        return ChatOpenAI(
            api_key=api_key,
            model=model_name,
            temperature=temp
        )
    
    elif provider == "openrouter":
        # OpenRouter is OpenAI-compatible
        return ChatOpenAI(
            api_key=api_key,
            base_url=base_url or "https://openrouter.ai/api/v1",
            model=model_name,
            temperature=temp
        )
        
    elif provider == "lmstudio":
        # LM Studio is OpenAI-compatible
        return ChatOpenAI(
            api_key="lm-studio", # Usually ignored
            base_url=base_url or "http://localhost:1234/v1",
            model=model_name, # Usually ignored by local server but good to pass
            temperature=temp
        )
    
    elif provider == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            base_url=base_url or "http://localhost:11434",
            model=model_name,
            temperature=temp
        )

    elif provider == "ollama":
        # We can use ChatOllama or ChatOpenAI (Ollama supports OpenAI API now)
        # Let's use ChatOpenAI for consistency if base_url is provided
        return ChatOpenAI(
            api_key="ollama",
            base_url=base_url or "http://localhost:11434/v1",
            model=model_name,
            temperature=0.7
        )
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
