# CDL YAML Export/Import Scripts

Quick reference for WhisperEngine character backup and restoration.

## Quick Commands

### Export All Characters
```bash
python scripts/simple_character_backup.py
```
Output: `backups/characters_yaml/YYYY-MM-DD/*.yaml`

### Import Single Character
```bash
# Without overwrite (fails if exists)
python scripts/import_character_from_yaml.py backups/characters_yaml/2025-10-13/elena_rodriguez.yaml

# With overwrite (updates existing)
python scripts/import_character_from_yaml.py backups/characters_yaml/2025-10-13/elena_rodriguez.yaml --overwrite
```

### Import All Characters
```bash
python scripts/import_character_from_yaml.py backups/characters_yaml/2025-10-13/ --all --overwrite
```

## Available Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `simple_character_backup.py` | Export all characters to YAML | ✅ Production Ready |
| `import_character_from_yaml.py` | Import characters from YAML | ✅ Production Ready |
| `cdl_yaml_manager.py` | Comprehensive export/import (needs schema updates) | ⚠️  In Development |
| `test_cdl_yaml_roundtrip.py` | Automated testing | 🧪 Testing |
| `cdl_yaml_examples.sh` | Interactive examples | 📖 Documentation |

## Documentation

- **Implementation Summary**: `/CDL_YAML_IMPLEMENTATION.md` (root directory)
- **Full Guide**: `docs/guides/CDL_YAML_EXPORT_IMPORT.md`
- **Feature Summary**: `docs/features/CDL_YAML_EXPORT_IMPORT_SUMMARY.md`

## Common Workflows

### Daily Backup
```bash
python scripts/simple_character_backup.py
git add backups/characters_yaml/
git commit -m "Character backup: $(date +%Y-%m-%d)"
```

### Character Edit Workflow
```bash
# 1. Export current version
python scripts/simple_character_backup.py

# 2. Edit YAML file
vim backups/characters_yaml/2025-10-13/elena_rodriguez.yaml

# 3. Import changes
python scripts/import_character_from_yaml.py backups/characters_yaml/2025-10-13/elena_rodriguez.yaml --overwrite

# 4. Restart bot
./multi-bot.sh restart elena
```

### Disaster Recovery
```bash
# Restore all characters from backup
python scripts/import_character_from_yaml.py backups/characters_yaml/2025-10-13/ --all --overwrite
```

## Environment Variables

Ensure these are set in `.env`:
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=whisperengine
POSTGRES_USER=whisperengine
POSTGRES_PASSWORD=whisperengine_password
```

## Testing

Verify exports are working:
```bash
python scripts/simple_character_backup.py
ls -lh backups/characters_yaml/$(date +%Y-%m-%d)/
```

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -h localhost -p 5433 -U whisperengine -d whisperengine -c "SELECT COUNT(*) FROM characters;"
```

### Invalid YAML
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('character.yaml'))"
```

## Need Help?

1. Read `/CDL_YAML_IMPLEMENTATION.md` in root directory
2. Check `docs/guides/CDL_YAML_EXPORT_IMPORT.md` for full documentation
3. Run `./scripts/cdl_yaml_examples.sh` for interactive examples
4. Open GitHub issue if problems persist
