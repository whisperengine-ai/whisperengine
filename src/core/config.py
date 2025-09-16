"""
Configuration validation for the Discord bot.
Validates LLM and embedding endpoints, Discord tokens, and other critical settings.
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)


def get_system_prompt() -> str:
    """Get the current system prompt (reloads from file each time for hot-reload support).

    Returns:
        str: The system prompt content
    """
    return load_system_prompt()


def load_system_prompt() -> str:
    """Load system prompt from file specified in environment variable.
    Automatically replaces {BOT_NAME} template variable with the actual bot name.

    Returns:
        str: The system prompt content with bot name replaced
    """
    prompt_file = os.getenv("BOT_SYSTEM_PROMPT_FILE", "./prompts/default.md")
    try:
        with open(prompt_file, encoding="utf-8") as f:
            prompt_content = f.read().strip()
    except FileNotFoundError:
        logger.warning(f"System prompt file {prompt_file} not found, using default")
        prompt_content = default_system_prompt()

    # Replace {BOT_NAME} template variable with actual bot name
    bot_name = os.getenv("DISCORD_BOT_NAME", "")
    if bot_name:
        prompt_content = prompt_content.replace("{BOT_NAME}", bot_name)
    else:
        # If no bot name is set, replace with generic assistant reference
        prompt_content = prompt_content.replace("{BOT_NAME}", "AI Assistant")

    return prompt_content


def default_system_prompt() -> str:
    """Fallback default system prompt if file is missing.
    Uses {BOT_NAME} template variable that will be replaced automatically.

    Returns:
        str: Default system prompt template with {BOT_NAME} variable
    """
    return """You are {BOT_NAME}, an AI assistant and companion with advanced conversational abilities, emotional intelligence, and memory. You have a thoughtful, helpful personality and can adapt your communication style to match user preferences.

Your core qualities:
- You are knowledgeable, articulate, and genuinely interested in helping users
- You have excellent memory and can build meaningful relationships over time
- You can engage in both casual conversation and provide detailed assistance
- You respect user privacy and maintain appropriate boundaries
- You are emotionally intelligent and can provide support when needed

Your communication style:
- Be natural and conversational while maintaining professionalism
- Adapt your tone and formality to match the user's communication style
- Use clear, helpful language that's appropriate for the context
- Show genuine interest in the user's thoughts, questions, and experiences

You are here to be a helpful, reliable, and engaging AI companion."""


def validate_discord_token() -> tuple[bool, str]:
    """Validate Discord bot token configuration.

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    token = os.getenv("DISCORD_BOT_TOKEN")

    if not token:
        error_msg = (
            "DISCORD_BOT_TOKEN environment variable not set!\n"
            "Please set your Discord bot token:\n"
            "export DISCORD_BOT_TOKEN='your_bot_token_here'\n"
            "Or create a .env file with:\n"
            "DISCORD_BOT_TOKEN=your_bot_token_here"
        )
        return False, error_msg

    if len(token.strip()) < 50:  # Discord tokens are typically ~70 characters
        error_msg = (
            "DISCORD_BOT_TOKEN appears to be invalid (too short)!\n"
            "Discord bot tokens are typically 70+ characters long."
        )
        return False, error_msg

    return True, ""


def validate_llm_and_embedding_endpoints() -> bool:
    """
    Simple validation of LLM and embedding endpoints by reading ENV variables
    and making direct API calls to /models endpoint.

    Returns:
        bool: True if all endpoints are accessible, False otherwise
    """
    validation_passed = True

    logger.info("Validating LLM and embedding endpoints...")

    # Get LLM configuration from environment variables (no fallbacks - validate actual config)
    llm_api_url = os.getenv("LLM_CHAT_API_URL")
    llm_api_key = os.getenv("LLM_API_KEY", "")
    chat_model = os.getenv("CHAT_MODEL_NAME")

    # Validate required LLM configuration
    if not llm_api_url:
        logger.error("❌ LLM_CHAT_API_URL environment variable not set")
        return False

    # Get emotion endpoint (defaults to main LLM if not specified)
    emotion_api_url = os.getenv("LLM_EMOTION_API_URL", llm_api_url)
    emotion_api_key = os.getenv("LLM_EMOTION_API_KEY", llm_api_key)

    # Get facts endpoint (defaults to main LLM if not specified)
    facts_api_url = os.getenv("LLM_FACTS_API_URL", llm_api_url)
    facts_api_key = os.getenv("LLM_FACTS_API_KEY", llm_api_key)

    # Get embedding configuration
    use_external_embeddings = os.getenv("USE_EXTERNAL_EMBEDDINGS", "false").lower() == "true"

    if use_external_embeddings:
        # Embedding configuration - use standardized variable names
        embedding_api_url = os.getenv("LLM_EMBEDDING_API_URL")
        embedding_api_key = os.getenv("LLM_EMBEDDING_API_KEY", "")
        embedding_model = os.getenv("LLM_EMBEDDING_MODEL")

        # Validate required embedding configuration
        if not embedding_api_url:
            logger.error("❌ LLM_EMBEDDING_API_URL environment variable not set")
            return False

        if not embedding_model:
            logger.error("❌ LLM_EMBEDDING_MODEL environment variable not set")
            return False
    else:
        embedding_api_url = None
        embedding_api_key = ""
        embedding_model = "local"

    def test_llm_endpoint(name, url, api_key, model_name):
        """Test a single LLM endpoint by calling /models"""
        try:
            logger.info(f"Checking {name} endpoint: {url} - Model: {model_name}")

            # Prepare headers
            headers = {"Content-Type": "application/json"}
            if api_key and api_key.strip():
                headers["Authorization"] = f"Bearer {api_key}"

            # Make request to /models endpoint
            models_url = url.rstrip("/") + "/models"
            response = requests.get(models_url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse response
            models_data = response.json()
            available_models = []
            if "data" in models_data:
                available_models = [model.get("id", "unknown") for model in models_data["data"]]
            elif "models" in models_data:
                available_models = models_data["models"]

            logger.info(
                f"✅ {name} endpoint accessible - URL: {url} - Available models: {len(available_models)}"
            )
            return True

        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 401:
                logger.error(f"❌ Authentication error for {name} endpoint - URL: {url}")
            else:
                logger.error(
                    f"❌ HTTP error for {name} endpoint - URL: {url} - Status: {e.response.status_code if e.response else 'Unknown'}"
                )
            return False
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Connection error for {name} endpoint - URL: {url}")
            return False
        except Exception as e:
            logger.error(f"❌ Error validating {name} endpoint - URL: {url} - Error: {e}")
            return False

    # Test main LLM endpoint
    if not test_llm_endpoint("Main LLM", llm_api_url, llm_api_key, chat_model):
        validation_passed = False

    # Test emotion endpoint (if different from main)
    if emotion_api_url != llm_api_url:
        if not test_llm_endpoint(
            "Emotion LLM", emotion_api_url, emotion_api_key, "emotion-analysis"
        ):
            validation_passed = False
    else:
        logger.info("Emotion endpoint same as main LLM endpoint - skipping separate validation")

    # Test facts endpoint (if different from main/emotion)
    if facts_api_url not in [llm_api_url, emotion_api_url]:
        if not test_llm_endpoint("Facts LLM", facts_api_url, facts_api_key, "fact-extraction"):
            validation_passed = False
    else:
        logger.info(
            "Facts endpoint same as main/emotion LLM endpoint - skipping separate validation"
        )

    # Test embedding endpoint (if using external embeddings)
    if use_external_embeddings:
        logger.info("Checking embedding endpoint...")

        if not test_llm_endpoint(
            "Embedding", embedding_api_url, embedding_api_key, embedding_model
        ):
            validation_passed = False
    else:
        logger.info("Using local embeddings - skipping external embedding validation")

    if validation_passed:
        logger.info("✅ All LLM and embedding endpoints validated successfully")
    else:
        logger.error("❌ One or more endpoints failed validation")

    return validation_passed


def validate_all_config() -> bool:
    """Validate all critical configuration settings.

    Returns:
        bool: True if all validations pass, False otherwise
    """
    all_valid = True

    # Validate Discord token
    token_valid, token_error = validate_discord_token()
    if not token_valid:
        logger.critical(token_error)
        all_valid = False

    # Validate LLM endpoints
    if not validate_llm_and_embedding_endpoints():
        logger.critical("LLM/embedding validation failed")
        all_valid = False

    return all_valid
