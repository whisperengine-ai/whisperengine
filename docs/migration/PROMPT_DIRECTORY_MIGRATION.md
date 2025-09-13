# 🔄 Prompt Directory Migration Guide

## ⚠️ Important Change Notice

WhisperEngine has migrated from individual file mounting to a unified `prompts/` directory structure. This provides better organization, easier management, and improved user experience.

## 📅 Migration Timeline

- **✅ New installations**: Automatically use `prompts/` directory
- **⚠️ Existing installations**: Continue working with backward compatibility
- **📅 Future versions**: `config/system_prompts/` may be deprecated in favor of `prompts/`

## 🔄 What Changed

### Old Structure (Still Supported)
```
project/
├── system_prompt.md              # Individual file
├── config/
│   └── system_prompts/          # Template directory
│       ├── empathetic_companion_template.md
│       ├── professional_ai_template.md
│       └── casual_friend_template.md
└── docker-compose.yml           # Mounts individual files
```

### New Structure (Recommended)
```
project/
├── prompts/                     # Unified prompt directory
│   ├── README.md               # Documentation
│   ├── default.md              # Default personality
│   ├── empathetic_companion_template.md
│   ├── professional_ai_template.md
│   ├── casual_friend_template.md
│   ├── dream_ai_enhanced.md
│   └── gaming_buddy_example.md
├── config/                     # Legacy symlinks (auto-created)
│   └── system_prompts/         # Points to prompts/
└── docker-compose.yml          # Mounts entire prompts/ directory
```

## 🚀 Migration Steps

### Automatic Migration (Recommended)

The quick-start script now automatically:
1. Creates the new `prompts/` directory
2. Downloads all templates to `prompts/`
3. Creates backward-compatible symlinks
4. Updates Docker configurations

**For new installations**: No action needed - everything is set up correctly.

### Manual Migration (Existing Users)

If you have an existing installation:

#### Step 1: Create the New Structure
```bash
# Create prompts directory
mkdir -p prompts

# Copy existing files
cp system_prompt.md prompts/default.md
cp config/system_prompts/*.md prompts/

# Verify the copy
ls -la prompts/
```

#### Step 2: Update Environment Configuration
```bash
# Update your .env file
# Old
BOT_SYSTEM_PROMPT_FILE=./system_prompt.md
# OR
BOT_SYSTEM_PROMPT_FILE=./config/system_prompts/empathetic_companion_template.md

# New
BOT_SYSTEM_PROMPT_FILE=./prompts/default.md
# OR  
BOT_SYSTEM_PROMPT_FILE=./prompts/empathetic_companion_template.md
```

#### Step 3: Update Docker Configuration (if using Docker)
The new docker-compose files already include:
```yaml
volumes:
  - ./prompts:/app/prompts:ro
```

If you have custom docker-compose files, update them to mount the prompts directory.

#### Step 4: Test the Migration
```bash
# Test prompt loading
python -c "from src.core.config import get_system_prompt; print('✅ Prompt loaded successfully')"

# Start the bot with new configuration
./bot.sh restart
```

## 🔄 Backward Compatibility

### Automatic Symlinks
The new quick-start script creates symlinks for backward compatibility:

```bash
# These are automatically created:
config/system_prompts/empathetic_companion_template.md -> ../../prompts/empathetic_companion_template.md
system_prompt.md -> prompts/default.md
```

### Legacy Support
- **Old paths continue to work** during the transition period
- **Existing .env files** don't need immediate updates
- **Custom workflows** can be migrated gradually

## 🎯 Benefits of the New Structure

### For Users
- **Single directory** for all personality management
- **Easier organization** of custom prompts
- **Better documentation** with built-in README
- **Hot reloading** of all prompt files
- **Version control** friendly structure

### For Developers
- **Simplified Docker mounting** (one directory vs multiple files)
- **Consistent file organization**
- **Easier backup and restore**
- **Better examples and templates**

## 🛠️ Advanced Migration

### Custom Prompt Organization
```bash
# Organize by category
mkdir -p prompts/{business,gaming,creative,support}
mv prompts/professional_ai_template.md prompts/business/
mv prompts/gaming_buddy_example.md prompts/gaming/
mv prompts/character_ai_template.md prompts/creative/
mv prompts/empathetic_companion_template.md prompts/support/

# Update environment paths
BOT_SYSTEM_PROMPT_FILE=./prompts/business/professional_ai_template.md
```

### Multi-Environment Setup
```bash
# Environment-specific prompts
prompts/
├── production/
│   ├── default.md
│   └── professional.md
├── development/
│   ├── debug.md
│   └── test.md
└── staging/
    └── preview.md

# Use with environment variables
BOT_SYSTEM_PROMPT_FILE=./prompts/${ENVIRONMENT:-production}/default.md
```

## 🔧 Troubleshooting Migration

### Common Issues

#### File Not Found Errors
```bash
# Check file exists
ls -la prompts/default.md

# Verify environment variable
echo $BOT_SYSTEM_PROMPT_FILE

# Test with absolute path
BOT_SYSTEM_PROMPT_FILE=$(pwd)/prompts/default.md python run.py
```

#### Docker Mount Issues
```bash
# Verify directory exists on host
ls -la prompts/

# Check Docker mount
docker-compose exec discord-bot ls -la /app/prompts/

# Test with development mount
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

#### Permission Issues
```bash
# Fix permissions
chmod -R 644 prompts/*.md
chmod 755 prompts/

# Check ownership
ls -la prompts/
```

### Rollback Procedure
If you need to rollback to the old system:

```bash
# Restore original files
cp prompts/default.md system_prompt.md

# Update environment
BOT_SYSTEM_PROMPT_FILE=./system_prompt.md

# Remove new directory (optional)
rm -rf prompts/

# Restart bot
./bot.sh restart
```

## 🎉 Migration Complete!

After migration, you'll have:
- ✅ **Unified prompt directory** at `prompts/`
- ✅ **All templates** available and organized
- ✅ **Hot reloading** for all prompt files
- ✅ **Backward compatibility** maintained
- ✅ **Better documentation** with `prompts/README.md`
- ✅ **Improved Docker mounting**

## 📚 Next Steps

1. **Explore new templates** in the `prompts/` directory
2. **Read the prompt management guide**: `docs/configuration/prompt-management.md`
3. **Create custom prompts** using the new structure
4. **Share your creations** with the community

## ❓ Need Help?

- **Documentation**: Check `prompts/README.md` and `docs/configuration/prompt-management.md`
- **Issues**: Create a GitHub issue with your migration question
- **Community**: Join our Discord for real-time help

---

**Happy prompting!** 🎭✨