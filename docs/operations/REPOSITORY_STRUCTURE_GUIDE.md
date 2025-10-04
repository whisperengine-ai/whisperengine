# WhisperEngine Repository Organization Guide

**Quick Reference**: Where to find and place files in the organized repository structure

---

## 📁 DIRECTORY STRUCTURE QUICK REFERENCE

### Root Directory (Essential Files Only)
```
whisperengine/
├── README.md                  # Primary project documentation
├── LICENSE                    # Project license
├── run.py                     # Main application entry point
├── env_manager.py             # Environment configuration manager
├── multi-bot.sh              # Multi-bot operations script
├── push-to-dockerhub.sh      # Docker deployment script
├── docker-compose*.yml        # Infrastructure configurations
├── requirements*.txt          # Python dependencies
├── pyproject.toml            # Python project configuration
├── .env*                     # Environment files (not committed)
└── .gitignore                # Git ignore rules
```

---

## 📚 DOCUMENTATION LOCATIONS

### Refactoring Documentation
**Location**: `docs/refactoring/`

**What goes here**:
- CDL system refactoring docs
- Prompt system refactoring docs
- Feature restoration documentation
- Code cleanup and migration docs
- Bug fix documentation with technical details

**Examples**:
- `CDL_ARCHITECTURE_IMPROVEMENT_COMPLETE.md`
- `PROMPT_LAYERING_EXPLAINED.md`
- `REFACTOR_VALIDATION_COMPLETE.md`
- `TIME_AND_NAME_FIXES.md`

### Architecture Documentation
**Location**: `docs/architecture/`

**What goes here**:
- System architecture overviews
- Integration guides
- API documentation
- Design patterns and principles

**Examples**:
- `EXTERNAL_CHAT_API.md`
- `INTEGRATION_GUIDE.md`

### Testing Documentation
**Location**: `docs/testing/`

**What goes here**:
- Bot testing documentation
- Validation results
- Test reports and summaries
- Migration test results

**Examples**:
- `GABRIEL_7D_TEST_DOCUMENTATION.md`
- `SOPHIA_7D_RESPONSE_OPTIMIZATION.md`
- `dotty_test_summary.md`

### Operations Documentation
**Location**: `docs/operations/`

**What goes here**:
- Deployment guides
- Operations procedures
- Repository management
- Infrastructure setup

**Examples**:
- `REPOSITORY_ORGANIZATION_COMPLETE.md`
- Deployment guides
- Operations runbooks

---

## 🧪 TEST FILE LOCATIONS

### Validation Scripts
**Location**: `tests/validation_scripts/`

**What goes here**:
- Bot validation tests (test_*_7d_validation.py)
- Feature validation tests
- CDL validation tests
- Demo scripts
- Verification scripts

**Naming Convention**: `test_*.py` or `validate_*.py` or `demo_*.py`

**Examples**:
- `test_elena_7d_validation.py`
- `test_vector_native_prompt.py`
- `validate_all_cdl_files.py`
- `demo_enhanced_7d_vector_system.py`

### Debug Scripts
**Location**: `tests/debug_scripts/`

**What goes here**:
- Bug fix scripts
- Patch scripts
- Debug utilities
- One-off fixes

**Naming Convention**: `fix_*.py` or `*_patch.py` or `debug_*.py`

**Examples**:
- `fix_context_switch_detector.py`
- `vector_memory_manager_patch.py`
- `meta_awareness_prompt_fix.py`

### Manual Test Plans
**Location**: `tests/manual_tests/`

**What goes here**:
- Manual test plans for specific bots
- Test scenarios
- Human-guided test procedures

**Naming Convention**: `manual_test_plan_*.py` or `*_test_scenarios.py`

**Examples**:
- `manual_test_plan_gabriel.py`
- `elena_test_scenarios.py`

---

## 🔧 SCRIPT LOCATIONS

### Build Scripts
**Location**: `scripts/build/`

**What goes here**:
- Docker build scripts
- Model bundling scripts
- Build automation

**Examples**:
- `build.py`
- `build_with_models.py`
- `build.sh`

### Utility Scripts
**Location**: `scripts/`

**What goes here**:
- Configuration generators
- Environment setup scripts
- Database utilities
- General automation

**Examples**:
- `generate_multi_bot_config.py`
- `verify_environment.py`
- `quick_bot_test.sh`

---

## 📋 FILE PLACEMENT DECISION TREE

### "Where should I put this file?"

#### Is it a documentation file (.md)?
- **Refactoring/Bug fixes** → `docs/refactoring/`
- **Architecture/Design** → `docs/architecture/`
- **Testing/Validation** → `docs/testing/`
- **Operations/Deployment** → `docs/operations/`
- **Primary README** → Root directory

#### Is it a test file (.py with "test" in name)?
- **Validation tests** → `tests/validation_scripts/`
- **Debug/fix scripts** → `tests/debug_scripts/`
- **Manual test plans** → `tests/manual_tests/`
- **Unit/Integration tests** → `tests/unit/` or `tests/integration/`

#### Is it a build file?
- **Docker/Model builds** → `scripts/build/`

#### Is it a script utility?
- **Config generation** → `scripts/`
- **Database utilities** → `scripts/`
- **Environment setup** → `scripts/`

#### Is it essential infrastructure?
- **Main entry point** → Root (run.py, env_manager.py)
- **Operations scripts** → Root (multi-bot.sh)
- **Docker configs** → Root (docker-compose*.yml)
- **Dependencies** → Root (requirements*.txt)

---

## 🚫 WHAT NOT TO PUT IN ROOT

### Never in Root Directory:
- ❌ Test scripts (unless critical smoke test)
- ❌ Debug/patch scripts
- ❌ Documentation markdown files (except README.md)
- ❌ Demo scripts
- ❌ Validation scripts
- ❌ Build scripts
- ❌ One-off utilities

### Exception Cases:
- ✅ `README.md` - Primary documentation
- ✅ `LICENSE` - Legal requirement
- ✅ `run.py` - Main entry point
- ✅ `env_manager.py` - Core configuration
- ✅ Operations scripts (multi-bot.sh, push-to-dockerhub.sh)
- ✅ Infrastructure configs (docker-compose, requirements, pyproject)

---

## 📊 BEFORE/AFTER COMPARISON

### Before Organization
```
whisperengine/
├── README.md
├── run.py
├── env_manager.py
├── test_elena_7d_validation.py      ❌ Should be in tests/
├── test_gabriel_7d_validation.py    ❌ Should be in tests/
├── test_context_switch.py           ❌ Should be in tests/
├── fix_context_switch_detector.py   ❌ Should be in tests/
├── CDL_STANDARDIZATION.md           ❌ Should be in docs/
├── PROMPT_LAYERING_EXPLAINED.md     ❌ Should be in docs/
├── TIME_AND_NAME_FIXES.md           ❌ Should be in docs/
├── REFACTOR_VALIDATION.md           ❌ Should be in docs/
├── build.py                         ❌ Should be in scripts/
├── [30+ more scattered files]       ❌
└── ...
```

### After Organization ✅
```
whisperengine/
├── README.md                        ✅ Essential
├── LICENSE                          ✅ Essential
├── run.py                           ✅ Essential
├── env_manager.py                   ✅ Essential
├── multi-bot.sh                     ✅ Operations
├── docker-compose*.yml              ✅ Infrastructure
├── requirements*.txt                ✅ Dependencies
├── docs/                            ✅ All documentation
│   ├── refactoring/                ✅ 17 refactoring docs
│   ├── architecture/               ✅ 2 architecture docs
│   ├── testing/                    ✅ 9 testing docs
│   └── operations/                 ✅ Operations docs
├── tests/                           ✅ All test files
│   ├── validation_scripts/         ✅ 30 validation tests
│   ├── debug_scripts/              ✅ 5 debug scripts
│   └── manual_tests/               ✅ 5 manual tests
└── scripts/                         ✅ Utility scripts
    └── build/                       ✅ 3 build scripts
```

**Result**: Clean, professional, organized ✅

---

## 🎯 CONVENTIONS TO FOLLOW

### Naming Conventions

#### Documentation Files
- Use descriptive ALL_CAPS names: `FEATURE_NAME_COMPLETE.md`
- Include status in name: `_COMPLETE`, `_GUIDE`, `_SUMMARY`
- Use underscores not spaces: `PROMPT_LAYERING_EXPLAINED.md`

#### Test Files
- Start with `test_`: `test_elena_7d_validation.py`
- Use descriptive names: `test_fidelity_first_memory.py`
- Include bot name if bot-specific: `test_gabriel_7d_validation.py`

#### Debug/Fix Scripts
- Start with `fix_` or end with `_patch`: `fix_context_switch.py`
- Be descriptive: `universal_chat_meta_awareness_patch.py`

#### Validation Scripts
- Start with `validate_`: `validate_all_cdl_files.py`
- Or start with `verify_`: `verify_vector_native_integration.py`

### Directory Conventions
- Use lowercase with underscores: `validation_scripts/`
- Be specific: `debug_scripts/` not just `debug/`
- Group related files: All refactoring docs together

---

## 🔍 FINDING FILES

### Quick Find Commands

**Find refactoring docs**:
```bash
ls docs/refactoring/
```

**Find test validation scripts**:
```bash
ls tests/validation_scripts/
```

**Find debug scripts**:
```bash
ls tests/debug_scripts/
```

**List all documentation**:
```bash
find docs/ -name "*.md"
```

**Find all test scripts**:
```bash
find tests/ -name "*.py"
```

---

## ✅ MAINTENANCE CHECKLIST

### When Adding New Files:

- [ ] Determine file type (doc, test, script, infrastructure)
- [ ] Check decision tree for proper location
- [ ] Follow naming conventions
- [ ] Place in appropriate directory
- [ ] Update relevant README if needed
- [ ] Verify root directory remains clean

### When Organizing Existing Files:

- [ ] Identify all files of same type
- [ ] Create directory if needed
- [ ] Move files in batches by type
- [ ] Verify no broken imports/references
- [ ] Update documentation references
- [ ] Test that moved scripts still work

---

**Created**: January 3, 2025  
**Purpose**: Quick reference for repository organization  
**Status**: Active guide for maintaining clean repository structure
