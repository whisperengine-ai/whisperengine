# 🎭 WhisperEngine
### Production-Ready AI Personalities That Feel Truly Human

[![Docker Build](https://github.com/WhisperEngine-AI/whisperengine/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/WhisperEngine-AI/whisperengine/actions/workflows/docker-publish.yml)
[![Docker Hub](https://img.shields.io/docker/pulls/whisperengine/whisperengine.svg)](https://hub.docker.com/r/whisperengine/whisperengine)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Production Ready](https://img.shields.io/badge/Production-Ready-brightgreen.svg)](docs/production/PRODUCTION_DEPLOYMENT.md)

WhisperEngine is an enterprise-grade AI personality platform with real emotional intelligence, persistent memories, and adaptive personalities. Deploy locally for maximum privacy or in the cloud for unified experiences across Discord, Slack, Teams, and custom applications.

**🏠 100% Private Local** • **☁️ Enterprise Cloud** • **🧠 Emotionally Intelligent** • **📊 Production Monitoring** • **🎭 Unlimited Personalities**

## 🚀 Quick Start (New User Experience)

WhisperEngine features an **interactive setup wizard** that guides you through configuration:

```bash
git clone https://github.com/whisperengine-ai/whisperengine
cd whisperengine
python run.py  # Launches setup wizard automatically
```

The setup wizard will:
- ✅ Detect your system capabilities
- ✅ Recommend optimal AI service configurations  
- ✅ Configure Discord bot tokens automatically
- ✅ Set up personality profiles for your use case
- ✅ Validate all connections before launch

**First-time users** get personalized guidance based on experience level (Beginner/Intermediate/Advanced).

---

## ✨ Production-Ready Features

### 🎯 **Enterprise-Grade Reliability**
- **Comprehensive Error Handling** - Graceful degradation and automatic recovery
- **Performance Optimization** - Intelligent caching and resource management
- **Health Monitoring** - Real-time system health tracking across 8 components
- **Operational Dashboards** - Web-based monitoring with admin Discord commands

### 🔍 **Operational Visibility**
- **Real-Time Health Dashboard** - Monitor system performance at `http://localhost:8080`
- **User Engagement Analytics** - Track usage patterns and conversation quality
- **Error Tracking & Analysis** - Automatic error pattern detection and alerting
- **Performance Metrics** - Response times, resource usage, and optimization insights

### 🛡️ **Production Security**
- **Input Validation** - Comprehensive user input sanitization and safety checks
- **Memory Isolation** - User data completely isolated with secure access controls
- **Admin Verification** - Role-based access for sensitive operations
- **Context Boundaries** - Strict enforcement of user and channel permissions

## 🚀 Choose Your Deployment Mode

### � **Demo Mode (Try It Now!)** - One-Click Experience
**[📥 Download Demo Package](https://github.com/whisperengine-ai/whisperengine/releases)** (~10GB)  
Complete demo with bundled AI models. Download → Extract → Double-click → Start chatting!
- ✅ Pre-configured AI personalities
- ✅ No setup or technical knowledge required  
- ✅ 100% private and offline
- ✅ Works immediately out of the box

### 🏠 **Local Mode (Maximum Privacy)** - Full Installation
**[📖 Local Setup Guide](docs/deployment/LOCAL_SETUP.md)**  
Complete local installation with your choice of AI models and full customization.

### ☁️ **Cloud Mode (Production Ready)** - Enterprise Setup  
```bash
git clone https://github.com/whisperengine-ai/whisperengine
cd whisperengine && ./setup.sh
python run.py  # Discord bot with cloud AI
```

**[📖 Full Setup Guide](docs/getting-started/QUICK_START.md)** for detailed instructions

### 🐳 **Docker Deployment (Scalable)** - Container Setup
```bash
# Development Environment
docker-compose -f docker-compose.dev.yml up

# Production Environment  
docker-compose -f docker-compose.prod.yml up

# With Full Monitoring
docker-compose -f docker-compose.yml up
```

**[📖 Docker Deployment Guide](docs/deployment/DOCKER.md)** for enterprise setup

---

## ✨ What Makes WhisperEngine Special

### 🧠 **Multi-Phase AI Intelligence**
Your AI companion gets smarter over time through four progressive intelligence phases:
- **Context Awareness** - Understands conversation flow and maintains coherent discussions
- **Emotional Intelligence** - Detects your mood and adapts responses to provide appropriate support
- **Memory Networks** - Remembers your preferences, shared experiences, and relationship history  
- **Personality Adaptation** - Develops unique quirks and communication patterns just for you

### 🎭 **Create Any Personality You Can Imagine**
- **Professional Assistant** - Focused, efficient, perfect for work tasks
- **Empathetic Friend** - Caring, supportive, great for emotional conversations
- **Creative Partner** - Imaginative, inspiring, ideal for brainstorming
- **Gaming Companion** - Fun, engaging, remembers your play style
- **Custom Characters** - Build anyone from scratch with our personality engine

### 🏢 **Enterprise-Ready Features**
- **Advanced Error Handling** - Intelligent error recovery with pattern detection
- **Performance Optimization** - Efficient memory management and caching systems
- **User Onboarding** - Guided setup with adaptive personality recommendations
- **Production Monitoring** - Comprehensive health tracking and analytics dashboard
- **Role-based Access** - Admin commands and security controls
- **Horizontal Scaling** - Docker deployment with load balancing support

### 🔒 **Privacy You Can Trust**
- **🏠 Local Mode**: 100% private - AI runs on your machine, zero external connections
- **☁️ Cloud Mode**: Transparent about data flow - conversations sync across platforms
- **Your Choice**: Pick your privacy level based on your needs
- **Open Source** - Full transparency, audit the code yourself

### 💭 **Memory That Feels Human**
- **Relationship Building** - Remembers your shared jokes, preferences, and history
- **Emotional Context** - Knows when you're stressed, excited, or need support
- **🏠 Local**: Private memories stored only on your machine
- **☁️ Cloud**: Unified memories across Discord, Slack, Teams, and more

---

## 🎯 Popular Use Cases

Whether you're looking for productivity, creativity, or companionship, WhisperEngine adapts to your needs:

### 💼 **Work & Productivity**
- **Personal Assistant** - Schedule management, email drafting, task planning
- **Code Companion** - Programming help, debugging, architecture discussions
- **Research Partner** - Information gathering, analysis, report writing

### 🎨 **Creativity & Entertainment**  
- **Writing Collaborator** - Story brainstorming, character development, editing
- **Game Master** - Interactive storytelling, character roleplay, world building
- **Creative Muse** - Art concepts, music ideas, creative problem solving

### 💙 **Personal & Emotional**
- **Supportive Friend** - Daily check-ins, emotional support, life advice
- **Learning Buddy** - Study sessions, exam prep, skill development
- **Therapeutic Companion** - Mindfulness, reflection, personal growth

### 🏢 **Business & Teams**
- **Customer Service** - Support automation with personality and context
- **Training Assistant** - Onboarding, skill development, knowledge transfer  
- **Brand Personality** - Consistent voice across all customer interactions

---

## 📚 **Learn More**

### 📖 **Quick References**
- **[📄 Complete Documentation](docs/)** - Full guides for every feature
- **[🚀 Quick Start Guide](docs/getting-started/QUICK_START.md)** - Step-by-step setup  
- **[🎭 Character Creation Guide](docs/character/character_prompt_guide.md)** - Build unique personalities
- **[🔧 Developer Setup](docs/development/DEVELOPMENT_GUIDE.md)** - Customize and extend WhisperEngine

### 🏗️ **Advanced Features**
- **[🧠 Memory System](docs/ai-systems/MEMORY_SYSTEM_README.md)** - How AI remembers and learns
- **[🎯 Emotional Intelligence](docs/ai-systems/ADVANCED_EMOTIONAL_INTELLIGENCE.md)** - Understanding user emotions
- **[📊 Analytics Dashboard](docs/ai-systems/MEMORY_ANALYTICS_DASHBOARD.md)** - System monitoring and insights
- **[🌐 Cross-Platform Sync](docs/ai-systems/CROSS_PLATFORM_OPTIMIZATION.md)** - Unified experience across devices

### 🛠️ **For Developers**
- **[⚙️ API Configuration](docs/configuration/API_KEY_CONFIGURATION.md)** - LLM provider setup
- **[🐳 Docker Deployment](docs/deployment/DOCKER_HUB_SETUP.md)** - Production deployment
- **[🧪 Testing Guide](MLX_TESTING_GUIDE.md)** - Validation and testing
- **[🍎 Apple Silicon Guide](MLX_INTEGRATION_GUIDE.md)** - Optimized for M1/M2/M3 Macs

---

---

## 📊 **Production Monitoring & Operations**

WhisperEngine includes comprehensive monitoring for production deployments:

### 🏥 **Health Monitoring**
Real-time system health monitoring across all critical components:
```bash
# Discord Admin Commands
!health          # System health overview
!health detailed  # Component-by-component analysis
!errors          # Recent error analysis
!engagement      # User interaction metrics
```

**Monitored Components:**
- System Resources (CPU, Memory, Disk)
- LLM Service Connectivity & Performance
- Database Health & Query Performance
- Memory System Operations
- Cache Performance & Hit Rates
- Discord Bot Status & Latency

### 📈 **Analytics Dashboard**
Optional web dashboard for real-time monitoring:
```bash
# Access at http://localhost:8080/dashboard (when enabled)
!dashboard       # Get dashboard URL and access token
```

**Dashboard Features:**
- Real-time system metrics with live graphs
- Error tracking with pattern detection
- User engagement analytics
- Performance trends and alerts
- Component health visualization

### 🚨 **Intelligent Error Tracking**
Automatic error categorization and pattern detection:
- **Smart Categorization** - AI, System, User, Network error types
- **Pattern Detection** - Identifies recurring issues automatically
- **Severity Analysis** - Auto-prioritizes critical vs routine errors
- **Resolution Tracking** - Monitors fix success rates

**[📖 Monitoring Setup Guide](docs/operations/MONITORING.md)** for detailed configuration

---

## 🤝 **Community & Support**

### **Getting Help**
- **📖 [Complete Documentation](docs/)** - Comprehensive guides and tutorials
- **🐛 [Report Issues](https://github.com/whisperengine-ai/whisperengine/issues)** - Bug reports and feature requests  
- **💬 [Discussions](https://github.com/whisperengine-ai/whisperengine/discussions)** - Community chat and support
- **🔧 [Contributing Guide](CONTRIBUTING.md)** - Help improve WhisperEngine

### **What People Are Building**
- **Educational Tutors** - Personalized learning companions for students
- **Mental Health Support** - Emotional wellness and mindfulness assistants  
- **Creative Writers** - AI collaborators for novels, screenplays, and poetry
- **Customer Service** - Brand-consistent support agents for businesses
- **Gaming NPCs** - Memorable characters for interactive fiction and games

### **Join the WhisperEngine Community**
Whether you're building your first AI companion or deploying enterprise-scale personalities, our community is here to help you succeed.

---

## 📄 **License & Contributing**

WhisperEngine is open source under the **[MIT License](LICENSE)** - you're free to use, modify, and distribute it however you like.

**Want to contribute?** We welcome:
- 🐛 Bug fixes and improvements  
- ✨ New personality templates
- 📚 Documentation enhancements
- 🔧 Feature development
- 🧪 Testing and validation

See our **[Contributing Guide](CONTRIBUTING.md)** to get started!

---

**Ready to create your first AI companion?** 

🚀 **[Get Started Now](docs/getting-started/QUICK_START.md)** and bring your digital personality to life!