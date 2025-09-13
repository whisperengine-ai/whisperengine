#!/bin/bash

# WhisperEngine GitHub Wiki Setup Script
# This script prepares wiki pages for GitHub Wiki import

echo "🚀 Setting up WhisperEngine GitHub Wiki structure..."

WIKI_DIR="wiki"
DOCS_DIR="docs"

# Create wiki directory if it doesn't exist
mkdir -p "$WIKI_DIR"

# Copy and rename key files for GitHub Wiki
echo "📋 Creating main wiki pages..."

# Home page (main table of contents)
if [ -f "$WIKI_DIR/Home.md" ]; then
    echo "✅ Home.md already exists"
else
    echo "❌ Home.md not found - please ensure WIKI.md was moved to wiki/Home.md"
fi

# Create Getting Started page
cat > "$WIKI_DIR/Getting-Started.md" << 'EOF'
# 🚀 Getting Started with WhisperEngine

Welcome to WhisperEngine! This guide will get you up and running quickly.

## Prerequisites
- Python 3.13+
- Discord Bot Token
- Local LLM (LM Studio, Ollama, etc.) or API access

## Quick Setup

### 1. Clone Repository
```bash
git clone https://github.com/whisperengine-ai/whisperengine
cd whisperengine
```

### 2. Configure Environment
```bash
cp .env.minimal .env
nano .env  # Set your Discord token and LLM settings
```

### 3. Start Bot
```bash
./bot.sh start
```

## Detailed Guides
- [📋 Installation Guide](docs/getting-started/INSTALLATION.md)
- [👥 End User Guide](docs/getting-started/END_USER_GUIDE.md)
- [🔑 API Configuration](docs/configuration/API_KEY_CONFIGURATION.md)

## Next Steps
- [🎭 Create Your Character](Character-Creation)
- [🧠 Configure AI Systems](AI-Intelligence)
- [🔧 Development Setup](Development-Guide)
EOF

# Create Character Creation page
cat > "$WIKI_DIR/Character-Creation.md" << 'EOF'
# 🎭 Character Creation & Personality

Learn how to create unique AI personalities for your bot.

## Core Guides
- [🎨 Character Prompt Guide](docs/character/character_prompt_guide.md)
- [🔄 System Prompt Hot Reload](docs/character/SYSTEM_PROMPT_HOT_RELOAD.md)
- [🌟 Main Character: Dream](system_prompt.md)

## Personality Templates
Choose from pre-built personality templates:

- [👔 Professional AI](config/system_prompts/professional_ai_template.md) - Business assistant
- [💝 Empathetic Companion](config/system_prompts/empathetic_companion_template.md) - Supportive friend
- [😊 Casual Friend](config/system_prompts/casual_friend_template.md) - Relaxed conversation
- [🎭 Character AI](config/system_prompts/character_ai_template.md) - Roleplay characters
- [🧠 Adaptive AI](config/system_prompts/adaptive_ai_template.md) - Self-adapting personality
- [✨ Dream Enhanced](config/system_prompts/dream_ai_enhanced.md) - Advanced Dream personality

## Template Resources
- [📚 Template Integration Guide](config/system_prompts/integration_guide.md)
- [🔍 Quick Reference](config/system_prompts/quick_reference.md)
EOF

# Create AI Intelligence page
cat > "$WIKI_DIR/AI-Intelligence.md" << 'EOF'
# 🧠 AI Intelligence & Memory Systems

Configure WhisperEngine's advanced AI capabilities.

## Core AI Systems
- [🏗️ AI System Architecture](docs/ai-systems/AI_SYSTEM_ARCHITECTURE.md)
- [💾 Memory System](docs/ai-systems/MEMORY_SYSTEM_README.md)
- [❤️ Emotion System](docs/ai-systems/EMOTION_SYSTEM_README.md)
- [🤖 Human-like Behavior](docs/ai-systems/HUMAN_LIKE_CHATBOT_GUIDE.md)

## Advanced Features
- [📊 Emotional Intelligence Strategy](docs/ai-systems/EMOTIONAL_INTELLIGENCE_STRATEGY.md)
- [🔗 LLM Memory Integration](docs/ai-systems/LLM_MEMORY_INTEGRATION_GUIDE.md)
- [🌐 Global Facts System](docs/ai-systems/HYBRID_GLOBAL_FACTS_IMPLEMENTATION.md)
- [📈 AI Metrics & Analytics](docs/ai-systems/HOLISTIC_AI_METRICS_GUIDE.md)

## Enhancement Roadmap
- [🗺️ AI Memory Roadmap](docs/ai-roadmap/AI_MEMORY_ENHANCEMENT_ROADMAP.md)
- [👤 Phase 1: Personality](docs/ai-roadmap/PHASE_1_PERSONALITY_PROFILING.md)
- [💭 Phase 2: Emotions](docs/ai-roadmap/PHASE_2_PREDICTIVE_EMOTIONS.md)
- [🧠 Phase 3: Memory Networks](docs/ai-roadmap/PHASE_3_MEMORY_NETWORKS.md)
- [🗣️ Phase 4: Conversations](docs/ai-roadmap/PHASE_4_CONVERSATION_ARCHITECTURE.md)
EOF

# Create Development Guide page
cat > "$WIKI_DIR/Development-Guide.md" << 'EOF'
# 💻 Development Guide

Everything you need to contribute to WhisperEngine.

## Getting Started
- [🤝 Contributing Guide](CONTRIBUTING.md)
- [💻 Development Setup](docs/development/DEVELOPMENT_GUIDE.md)
- [🏗️ Build Guide](BUILD_GUIDE.md)

## Architecture
- [🔄 Modular Architecture](docs/development/MODULAR_REFACTORING_GUIDE.md)
- [🏛️ Migration Guide](docs/development/ARCHITECTURAL_MIGRATION.md)
- [💾 Database Schema](docs/development/DATABASE_SCHEMA_FOLLOW_UP.md)
- [📝 Conversation Cache](docs/development/CONVERSATION_CACHE_DESIGN.md)
- [🔗 System Integration](docs/development/SYSTEM_INTEGRATION_OPTIMIZATION.md)

## Testing
- [🧪 Testing Framework](docs/testing/TESTING_FRAMEWORK.md)
- [🔍 Manual Testing](docs/testing/MANUAL_TESTING_GUIDE.md)
EOF

# Create Configuration page
cat > "$WIKI_DIR/Configuration.md" << 'EOF'
# ⚙️ Configuration & Setup

Complete configuration guides for WhisperEngine.

## Essential Configuration
- [🔑 API Keys & LLM Setup](docs/configuration/API_KEY_CONFIGURATION.md)
- [⚙️ Environment Variables](docs/configuration/ENVIRONMENT_VARIABLES_REFERENCE.md)
- [🖥️ Running Modes](docs/configuration/RUNNING_MODES_GUIDE.md)

## Advanced Setup
- [🏠 Local vs Remote Models](docs/deployment/LOCAL_VS_REMOTE_MODELS_GUIDE.md)
- [🔗 Embedding Models](docs/deployment/EMBEDDING_MODEL_GUIDE.md)
- [🌐 External API Integration](docs/deployment/EXTERNAL_API_EMOTION_INTEGRATION.md)
EOF

# Create Database & Storage page
cat > "$WIKI_DIR/Database-Storage.md" << 'EOF'
# 🗃️ Database & Storage

Database configuration and data management.

## Database Systems
- [🌐 Graph Database Guide](docs/database/GRAPH_DATABASE_COMPLETE_GUIDE.md)
- [⚡ Graph Quick Start](docs/database/GRAPH_DATABASE_QUICK_START.md)
- [🔗 Graph Enhancements](docs/database/GRAPH_DATABASE_ENHANCEMENT_DESIGN.md)
- [📊 Facts Architecture](docs/database/GLOBAL_FACTS_ARCHITECTURE_ANALYSIS.md)

## Data Management
- [💾 Backup System](docs/database/BACKUP_SYSTEM_GUIDE.md)
- [📥 ChatGPT Import](docs/database/CHATGPT_IMPORT_GUIDE.md)
EOF

# Create Voice & Media page
cat > "$WIKI_DIR/Voice-Media.md" << 'EOF'
# 🎵 Voice & Media Features

Voice conversation and media processing capabilities.

## Voice Setup
- [🎤 Voice Quick Start](docs/voice/VOICE_QUICK_START.md)
- [🔊 Voice Integration](docs/voice/VOICE_INTEGRATION_GUIDE.md)
- [🖼️ Vision Response Fix](docs/voice/VISION_RESPONSE_FORMAT_FIX.md)
EOF

# Create Security page
cat > "$WIKI_DIR/Security-Privacy.md" << 'EOF'
# 🔒 Security & Privacy

Security implementation and privacy protection.

## Security Features
- [🛡️ Security Design](docs/security/SECURITY_AUTHORIZATION_DESIGN.md)
- [📋 Security Logging](docs/security/SECURITY_LOGGING_CONFIGURATION.md)
- [🔧 System Message Security](docs/security/SYSTEM_MESSAGE_TRUNCATION_FIX.md)

## Privacy First
WhisperEngine is designed with privacy as the top priority:
- All AI processing happens locally
- No data collection or telemetry
- Secure memory isolation between users
- Open source for complete transparency
EOF

# Create Deployment page
cat > "$WIKI_DIR/Deployment-Operations.md" << 'EOF'
# 🚀 Deployment & Operations

Production deployment and operational guides.

## Deployment
- [📈 Horizontal Scaling](docs/deployment/HORIZONTAL_SCALING_GUIDE.md)
- [📝 Logging Guide](docs/deployment/LOGGING_GUIDE.md)
- [⚙️ Job Scheduler](docs/deployment/INTEGRATED_JOB_SCHEDULER_GUIDE.md)
- [📤 Follow-up Service](docs/deployment/FOLLOW_UP_SERVICE_DESIGN.md)

## Operations
- [🏠 Local vs Remote Models](docs/deployment/LOCAL_VS_REMOTE_MODELS_GUIDE.md)
- [🔗 Embedding Models](docs/deployment/EMBEDDING_MODEL_GUIDE.md)
- [🌐 External API Integration](docs/deployment/EXTERNAL_API_EMOTION_INTEGRATION.md)
EOF

# Create Advanced Features page
cat > "$WIKI_DIR/Advanced-Features.md" << 'EOF'
# 🔬 Advanced Features

Experimental and cutting-edge capabilities.

## Advanced AI
- [💡 Advanced Emotions](docs/advanced/ADVANCED_EMOTION_OPTIONS.md)
- [📊 Conversation Analysis](docs/advanced/CONVERSATION_CONCEPT_ANALYSIS.md)
- [📈 Data Formatting Analysis](docs/advanced/CONVERSATION_DATA_FORMATTING_ANALYSIS.md)

## Experimental Features
These features are under active development and may change:
- Phase 3 Memory Networks
- Phase 4 Conversation Architecture
- Advanced Personality Profiling
EOF

echo "✅ Wiki pages created successfully!"
echo ""
echo "📋 GitHub Wiki Setup Instructions:"
echo "1. Go to your GitHub repository"
echo "2. Click on the 'Wiki' tab"
echo "3. Create a new wiki or edit existing pages"
echo "4. Copy content from wiki/*.md files to corresponding GitHub wiki pages"
echo ""
echo "📁 Wiki pages created:"
ls -la "$WIKI_DIR"
echo ""
echo "🔗 The Home.md file contains the main table of contents"
echo "🔗 Each themed page links to relevant documentation"
echo ""
echo "💡 Pro tip: You can also use the GitHub CLI to bulk import:"
echo "   gh repo wiki create --title 'Page Title' --body \"\$(cat wiki/Page-Name.md)\""