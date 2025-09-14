# Stale Documentation Archive Branch

**Branch**: `archive/stale-documentation-sept-2025`  
**Archive Date**: September 14, 2025  
**Reason**: Documentation causing context confusion with inaccurate status claims

## 📋 **What's Archived Here**

This branch preserves documentation that was removed from the main development branches because it contained misleading completion claims or outdated architecture decisions that were confusing AI development context.

### **Documents Preserved**

#### **Overly Optimistic Status Claims**
- **`RELEASE_READINESS_REPORT.md`** 
  - **Issue**: Claimed "all items passed" and ready for release
  - **Reality**: Desktop app has major build issues, signal handling broken
  - **Contains**: Useful repository review and checklist structure

#### **Premature Architecture Documents**
- **`docs/advanced/SCALING_ARCHITECTURE_PLAN.md`**
  - **Issue**: Detailed scaling plans overstating implementation status  
  - **Reality**: Contains real OpenRouter usage data but claims 90% completion
  - **Contains**: Valuable real-world metrics and cost analysis

- **`docs/advanced/NATIVE_APPLICATION_ARCHITECTURE.md`**
  - **Issue**: Comprehensive native app architecture for broken build system
  - **Reality**: PyInstaller integration has syntax errors and instability
  - **Contains**: Good packaging tool comparisons and performance analysis

#### **Phase Roadmap Confusion**
- **`docs/ai-roadmap/PHASE4_QUICK_REFERENCE.md`**
  - **Issue**: Described features as "automatically integrated" 
  - **Reality**: Unclear what phase features actually work in current codebase
  - **Contains**: Useful feature descriptions and configuration examples

### **Additional Archived Content**
- `docs/archived/` directory structure and README
- Various other outdated architecture and status documents

## 🎯 **Current Project Focus (September 2025)**

The main development branches now focus on a **simplified 2-tier architecture**:

1. **Docker Compose Tier** (✅ Working)
   - Production-ready for technical users
   - PostgreSQL + Redis + ChromaDB
   - Web UI accessible via browser

2. **Native Desktop Tier** (🔧 ~1% Complete)
   - Build system has major issues
   - Signal handling broken
   - PyInstaller integration unstable

## 🔄 **If You Need This Content**

If any of these archived documents contain useful information for future development:

1. **Cherry-pick specific content** rather than restoring entire documents
2. **Update status claims** to match reality before re-integrating
3. **Focus on technical details** rather than completion percentages
4. **Test claims** before documenting them as working features

## 📖 **Current Accurate Documentation**

For up-to-date project status, see the main development branch:
- `.github/copilot-instructions.md` - AI agent guidance with honest status
- `CURRENT_STATUS.md` - Session-by-session progress tracking
- `REAL_IMPLEMENTATION_STATUS.md` - Honest assessment vs aspirational claims

## 🚨 **Why This Matters**

WhisperEngine has complex multi-deployment architecture and a history of documentation accuracy issues. Stale docs with false completion claims were:
- Confusing AI agents about actual implementation status
- Creating unrealistic expectations about working features  
- Making it harder to focus on real development priorities
- Polluting context with contradictory information

This archive preserves the work while preventing context pollution in active development.