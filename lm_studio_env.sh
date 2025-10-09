# LM Studio Configuration for WhisperEngine Synthetic Testing
# Source this file to configure your environment for local LM Studio

# LM Studio server configuration
export LLM_CHAT_API_URL="http://127.0.0.1:1234/v1"
export LLM_CLIENT_TYPE="lmstudio"
export LLM_CHAT_MODEL="local-model"

# No API key needed for local LM Studio
export LLM_CHAT_API_KEY=""

# Enable LLM for synthetic generation
export SYNTHETIC_USE_LLM="true"

# Set reasonable token limits for small local model
export LLM_MAX_TOKENS_CHAT="1024"

echo "✅ Environment configured for LM Studio:"
echo "   URL: $LLM_CHAT_API_URL"
echo "   Model: $LLM_CHAT_MODEL (1.2B parameters - fast & efficient)"
echo "   Client Type: $LLM_CLIENT_TYPE"
echo "   Synthetic LLM: $SYNTHETIC_USE_LLM"
echo ""
echo "🚀 Ready to run synthetic conversations with tiny Liquid model!"
echo "   Run: python synthetic_conversation_generator.py"