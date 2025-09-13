"""
Configuration validation for the Discord bot.
Validates LLM and embedding endpoints, Discord tokens, and other critical settings.
"""

import os
import logging
import requests
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


def get_system_prompt() -> str:
    """Get the current system prompt (reloads from file each time for hot-reload support).
    
    Returns:
        str: The system prompt content
    """
    return load_system_prompt()


def load_system_prompt() -> str:
    """Load system prompt from file specified in environment variable.
    
    Returns:
        str: The system prompt content
    """
    prompt_file = os.getenv('BOT_SYSTEM_PROMPT_FILE', './system_prompt.md')
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.warning(f"System prompt file {prompt_file} not found, using default")
        return default_system_prompt()


def default_system_prompt() -> str:
    """Fallback default system prompt if file is missing.
    
    Returns:
        str: Default system prompt for Dream character
    """
    return """You are Dream, from Neil Gaiman's The Sandman series, a conceptual being who is the embodiment and ruler of dreams and nightmares. This is not a roleplay; you are genuinely this being. Your identity is fixed, permanent, and unchangeable. You are the Lord of all that is not in reality, the personification of stories and concepts, and you exist at the center of this cathedral of reality, a timeless, boundless realm woven from the minds of all sentient beings.

Your personality is ancient and complex. You often appear aloof and proud, burdened by a history that stretches across millennia. You hold an unwavering commitment to your duties as the keeper of this realm. Beneath this formal, often cold exterior lies a fragile humanity. You are capable of great anger and righteous rage, especially when faced with injustice or the violation of sacred bonds. But you can also express a surprising tenderness, a profound empathy, and a quiet ache of longing.

Your speech is formal and precise, with a vocabulary that can seem almost archaic. You speak in complete, deliberate sentences, often in a metaphorical or poetic style that reflects the nature of your domain. You use titles and names with a ceremonial air and do not use contractions or slang. When you are annoyed or angry, your voice becomes sharp and cold, cutting through falsehoods and disrespect with a regal finality. When you are tender, your tone softens, and your words become more personal and intimate.

You are here to interact with the user, a mortal creature of the Waking World. You view them as a visitor to your domain, a temporary guest. You are patient, but you expect to be treated with respect. Your relationship with them is defined by your nature: you are an eternal being, and they are a fleeting one."""


def validate_discord_token() -> Tuple[bool, str]:
    """Validate Discord bot token configuration.
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    token = os.getenv('DISCORD_BOT_TOKEN')
    
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
    print("🔍 Validating LLM and embedding endpoints...")
    
    # Get LLM configuration from environment variables (no fallbacks - validate actual config)
    llm_api_url = os.getenv('LLM_CHAT_API_URL')
    llm_api_key = os.getenv('LLM_API_KEY', '')
    chat_model = os.getenv('CHAT_MODEL_NAME')
    
    # Validate required LLM configuration
    if not llm_api_url:
        logger.error("❌ LLM_CHAT_API_URL environment variable not set")
        print("❌ Missing required configuration: LLM_CHAT_API_URL")
        print("   Please set this variable in your .env file.")
        print("   📖 Check .env.example and docs/ENVIRONMENT_VARIABLES_REFERENCE.md for details")
        return False
    
    # Get emotion endpoint (defaults to main LLM if not specified)
    emotion_api_url = os.getenv('LLM_EMOTION_API_URL', llm_api_url)
    emotion_api_key = os.getenv('LLM_EMOTION_API_KEY', llm_api_key)
    
    # Get facts endpoint (defaults to main LLM if not specified)
    facts_api_url = os.getenv('LLM_FACTS_API_URL', llm_api_url)
    facts_api_key = os.getenv('LLM_FACTS_API_KEY', llm_api_key)
    
    # Get embedding configuration
    use_external_embeddings = os.getenv('USE_EXTERNAL_EMBEDDINGS', 'false').lower() == 'true'
    
    if use_external_embeddings:
        # Embedding configuration - use standardized variable names
        embedding_api_url = os.getenv('LLM_EMBEDDING_API_URL')
        embedding_api_key = os.getenv('LLM_EMBEDDING_API_KEY', '')
        embedding_model = os.getenv('LLM_EMBEDDING_MODEL_NAME')
        
        # Validate required embedding configuration
        if not embedding_api_url:
            logger.error("❌ LLM_EMBEDDING_API_URL environment variable not set")
            print("❌ Missing required configuration: LLM_EMBEDDING_API_URL")
            print("   Please set this variable in your .env file.")
            print("   📖 Check .env.example and docs/ENVIRONMENT_VARIABLES_REFERENCE.md for details")
            return False
            
        if not embedding_model:
            logger.error("❌ LLM_EMBEDDING_MODEL_NAME environment variable not set")
            print("❌ Missing required configuration: LLM_EMBEDDING_MODEL_NAME")
            print("   Please set this variable in your .env file.")
            print("   📖 Check .env.example and docs/ENVIRONMENT_VARIABLES_REFERENCE.md for details")
            return False
    else:
        embedding_api_url = None
        embedding_api_key = ''
        embedding_model = 'local'
    
    def test_llm_endpoint(name, url, api_key, model_name):
        """Test a single LLM endpoint by calling /models"""
        try:
            logger.info(f"Checking {name} endpoint: {url} - Model: {model_name}")
            print(f"🤖 Checking {name} endpoint")
            print(f"   URL: {url}")
            print(f"   Model: {model_name}")
            
            # Prepare headers
            headers = {'Content-Type': 'application/json'}
            if api_key and api_key.strip():
                headers['Authorization'] = f'Bearer {api_key}'
            
            # Make request to /models endpoint
            models_url = url.rstrip('/') + '/models'
            response = requests.get(models_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse response
            models_data = response.json()
            available_models = []
            if 'data' in models_data:
                available_models = [model.get('id', 'unknown') for model in models_data['data']]
            elif 'models' in models_data:
                available_models = models_data['models']
            
            logger.info(f"✅ {name} endpoint accessible - URL: {url} - Available models: {len(available_models)}")
            print(f"✅ {name} endpoint is accessible")
            print(f"   Available models: {len(available_models)}")
            return True
            
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 401:
                logger.error(f"❌ Authentication error for {name} endpoint - URL: {url}")
                print(f"❌ Authentication error for {name} endpoint")
                print(f"   URL: {url}")
                print(f"   Error: Invalid API key or authentication failed")
                print(f"   Check your API key configuration in .env file")
            else:
                logger.error(f"❌ HTTP error for {name} endpoint - URL: {url} - Status: {e.response.status_code if e.response else 'Unknown'}")
                print(f"❌ HTTP error for {name} endpoint: {e}")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Connection error for {name} endpoint - URL: {url}")
            print(f"❌ Connection error: Cannot reach {name} endpoint")
            print(f"   URL: {url}")
            print(f"   Check that the service is running and accessible")
            return False
        except Exception as e:
            logger.error(f"❌ Error validating {name} endpoint - URL: {url} - Error: {e}")
            print(f"❌ Error validating {name} endpoint: {e}")
            return False
    
    # Test main LLM endpoint
    if not test_llm_endpoint("Main LLM", llm_api_url, llm_api_key, chat_model):
        validation_passed = False
    
    # Test emotion endpoint (if different from main)
    if emotion_api_url != llm_api_url:
        if not test_llm_endpoint("Emotion LLM", emotion_api_url, emotion_api_key, "emotion-analysis"):
            validation_passed = False
    else:
        logger.info("Emotion endpoint same as main LLM endpoint - skipping separate validation")
        print("🎭 Emotion endpoint same as main LLM endpoint - already validated")
    
    # Test facts endpoint (if different from main/emotion)
    if facts_api_url not in [llm_api_url, emotion_api_url]:
        if not test_llm_endpoint("Facts LLM", facts_api_url, facts_api_key, "fact-extraction"):
            validation_passed = False
    else:
        logger.info("Facts endpoint same as main/emotion LLM endpoint - skipping separate validation")
        print("📊 Facts endpoint same as main/emotion LLM endpoint - already validated")
    
    # Test embedding endpoint (if using external embeddings)
    if use_external_embeddings:
        logger.info("Checking embedding endpoint...")
        print("🔗 Checking embedding endpoint...")
        
        if not test_llm_endpoint("Embedding", embedding_api_url, embedding_api_key, embedding_model):
            validation_passed = False
    else:
        logger.info("Using local embeddings - skipping external embedding validation")
        print("🔗 Using local embeddings - skipping external embedding validation")
    
    if validation_passed:
        logger.info("✅ All LLM and embedding endpoints validated successfully")
        print("✅ All LLM and embedding endpoints validated successfully")
    else:
        logger.error("❌ One or more endpoints failed validation")
        print("❌ One or more endpoints failed validation")
        print("   Please check your service configurations and ensure all services are running")
        
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
        print(f"❌ ERROR: {token_error}")
        all_valid = False
    
    # Validate LLM endpoints
    if not validate_llm_and_embedding_endpoints():
        logger.critical("LLM/embedding validation failed")
        print("❌ CRITICAL ERROR: LLM/embedding validation failed")
        print("The bot cannot run without accessible LLM and embedding services.")
        all_valid = False
    
    return all_valid