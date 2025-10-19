# 🔄 WhisperEngine Upgrade & Migration Guides

This directory contains guides for upgrading between WhisperEngine versions and resolving migration-related issues.

## 📚 Available Guides

### v1.0.6 → v1.0.24: Assistant Personality Restoration

**Problem**: After upgrading from v1.0.6 to v1.0.24, the "assistant" character loses its personality and behaves like a generic AI.

**Root Cause**: Database migrations created new CDL tables (character_personalities, character_voices, character_modes) but didn't populate data for existing characters.

**Quick Start**: [📄 README_PERSONALITY_RESTORATION.md](./README_PERSONALITY_RESTORATION.md)

#### Available Solutions

1. **🖱️ Web UI Method (Non-Technical)** - [RESTORE_ASSISTANT_PERSONALITY_WEB_UI.md](./RESTORE_ASSISTANT_PERSONALITY_WEB_UI.md)
   - Step-by-step walkthrough using CDL Web UI
   - Takes 10-15 minutes
   - No technical knowledge required
   - **Recommended for most users**

2. **💻 SQL Method (Technical)** - `sql/migrations/fix_assistant_personality_v106_to_v124.sql`
   - One-command database fix
   - Requires Docker/PostgreSQL access
   - Takes 1 minute
   - **Recommended for technical users**

#### Supporting Documents

- **📋 Quick Reference Card** - [ASSISTANT_PERSONALITY_QUICK_REFERENCE.md](./ASSISTANT_PERSONALITY_QUICK_REFERENCE.md)
  - Printable checklist with all values to enter
  - Perfect companion for Web UI method

- **🔧 Troubleshooting** - [WEB_UI_TROUBLESHOOTING.md](./WEB_UI_TROUBLESHOOTING.md)
  - Common Web UI issues and solutions
  - Browser compatibility notes
  - Network access problems

- **🔍 System Diagnostics** - [SYSTEM_DIAGNOSTICS.md](./SYSTEM_DIAGNOSTICS.md)
  - Docker commands to verify system state
  - Confirm migrations ran vs missing data
  - Check Qdrant vector database health
  - Inspect PostgreSQL tables and data

---

## 🎯 Quick Decision Tree

```
Do you have database/Docker access?
│
├─ YES, and I'm comfortable with SQL
│  └─ Use SQL Method (1 minute)
│     └─ File: sql/migrations/fix_assistant_personality_v106_to_v124.sql
│
└─ NO, or prefer visual interface
   └─ Use Web UI Method (10-15 minutes)
      └─ Start: README_PERSONALITY_RESTORATION.md
```

---

## 📁 File Organization

```
upgrades/
├── README.md (you are here)
├── README_PERSONALITY_RESTORATION.md (start here for personality issue)
├── RESTORE_ASSISTANT_PERSONALITY_WEB_UI.md (main Web UI walkthrough)
├── ASSISTANT_PERSONALITY_QUICK_REFERENCE.md (printable checklist)
├── WEB_UI_TROUBLESHOOTING.md (common issues)
└── SYSTEM_DIAGNOSTICS.md (Docker verification commands)
```

---

## 🆘 Need Help?

1. **Start with diagnostics**: Run commands from [SYSTEM_DIAGNOSTICS.md](./SYSTEM_DIAGNOSTICS.md) to confirm the issue
2. **Choose your path**: Web UI (easier) or SQL (faster)
3. **Follow the guide**: Step-by-step instructions with verification
4. **Check troubleshooting**: If stuck, see [WEB_UI_TROUBLESHOOTING.md](./WEB_UI_TROUBLESHOOTING.md)

---

**Last Updated**: October 19, 2025  
**Applies To**: WhisperEngine v1.0.6 → v1.0.24 upgrades
