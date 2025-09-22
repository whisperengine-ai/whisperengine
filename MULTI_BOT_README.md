# Multi-Bot Documentation Index

WhisperEngine's multi-bot system documentation is organized as follows:

## 📖 Core Documentation

### 🚀 [MULTI_BOT_SETUP.md](./MULTI_BOT_SETUP.md)
**Primary setup and operations guide** - Start here for getting multi-bot system running.

**Contents:**
- Template-based architecture overview
- Quick start guide for adding new bots
- Complete command reference (`./multi-bot.sh`)
- Configuration management
- Troubleshooting guide

### 🧠 [MULTI_BOT_MEMORY_ARCHITECTURE.md](./MULTI_BOT_MEMORY_ARCHITECTURE.md)
**Memory system architecture and design** - Technical details on memory isolation and cross-bot querying.

**Contents:**
- Memory isolation by default
- Multi-bot query capabilities
- Payload-based segmentation design
- Performance considerations
- Future enhancement roadmap

### 🔧 [MULTI_BOT_IMPLEMENTATION_GUIDE.md](./MULTI_BOT_IMPLEMENTATION_GUIDE.md)
**Technical implementation reference** - Code examples and integration patterns.

**Contents:**
- Multi-bot querier API usage
- Cross-bot analysis examples
- Memory system integration
- Development patterns
- Code examples

## 🎯 Key Files

**Template System:**
- `docker-compose.multi-bot.template.yml` - Infrastructure template (SAFE TO EDIT)
- `docker-compose.multi-bot.yml` - Generated compose file (AUTO-GENERATED)
- `multi-bot.sh` - Generated management script (AUTO-GENERATED)

**Configuration:**
- `.env.{bot_name}` - Bot-specific environment files
- `characters/examples/*.json` - Character personality definitions
- `scripts/generate_multi_bot_config.py` - Template-based generator

## 🚀 Quick Start

```bash
# 1. List available bots
./multi-bot.sh list

# 2. Start a specific bot
./multi-bot.sh start elena

# 3. Check status
./multi-bot.sh status

# 4. View logs
./multi-bot.sh logs elena
```

For complete setup instructions, see [MULTI_BOT_SETUP.md](./MULTI_BOT_SETUP.md).

## 🏗️ Architecture Summary

WhisperEngine uses a **template-based multi-bot architecture** with:

- **Shared Infrastructure**: PostgreSQL 16.4, Redis 7.4, Qdrant v1.15.4 (pinned versions)
- **Isolated Personalities**: Each bot has unique character definition and environment
- **Memory Intelligence**: Cross-bot analysis with perfect isolation by default
- **Template Safety**: Infrastructure defined in editable template, not programmatic generation

---

*For AI context and development patterns, see `.github/copilot-instructions.md`*