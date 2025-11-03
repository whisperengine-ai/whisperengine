# Stance Analyzer Documentation Organization

## Overview

All stance analyzer documentation has been reorganized into appropriate folders under `docs/` following WhisperEngine's documentation structure.

## File Organization

### 1. **Stance Analysis Implementation** 
📁 Location: `docs/ai-features/STANCE_ANALYSIS_IMPLEMENTATION.md`

**Purpose**: Technical deep-dive into the stance analyzer architecture and design

**Contents**:
- Architecture overview
- Problem statement (emotion misattribution)
- Solution design (spaCy dependency parsing)
- Four detection strategies
- Implementation details
- Performance characteristics

**Audience**: AI/ML engineers, architecture review

---

### 2. **Stance Analysis Integration Guide**
📁 Location: `docs/implementation/STANCE_ANALYSIS_INTEGRATION_GUIDE.md`

**Purpose**: Step-by-step integration guide for adding stance analyzer to existing systems

**Contents**:
- Phase-by-phase integration instructions
- Code examples for each integration point
- Key methods and signatures
- Testing approach
- Expected behavior after integration

**Audience**: Implementation engineers, code reviewers

---

### 3. **Stance Analysis InfluxDB Integration**
📁 Location: `docs/memory/STANCE_ANALYSIS_INFLUXDB_INTEGRATION.md`

**Purpose**: Metrics collection and telemetry integration with InfluxDB

**Contents**:
- InfluxDB schema design
- Measurements and fields
- Query examples
- Grafana dashboard integration
- Monitoring emotional attribution accuracy
- Data flow architecture

**Audience**: DevOps, monitoring, analytics teams

---

### 4. **Stance Analysis Checklist**
📁 Location: `docs/testing/STANCE_ANALYSIS_CHECKLIST.md`

**Purpose**: Implementation checklist and testing requirements

**Contents**:
- Pre-integration checklist
- Unit test requirements
- Integration test requirements
- Memory storage verification
- Qdrant schema updates
- Metrics recording validation
- Post-deployment verification

**Audience**: QA, testers, implementation leads

---

### 5. **Stance Analysis Delivery Notes**
📁 Location: `docs/implementation_sessions/STANCE_ANALYSIS_DELIVERY.md`

**Purpose**: Session notes and delivery summary

**Contents**:
- Component inventory
- Key architectural decisions
- Development workflow
- Testing results
- Performance metrics
- Deployment notes
- Known limitations

**Audience**: Project managers, session participants

---

## Documentation Structure Rationale

```
docs/
├── ai-features/           ← Architecture & design
│   └── STANCE_ANALYSIS_IMPLEMENTATION.md
│
├── implementation/        ← Integration guides
│   └── STANCE_ANALYSIS_INTEGRATION_GUIDE.md
│
├── memory/               ← Memory & metrics integration
│   └── STANCE_ANALYSIS_INFLUXDB_INTEGRATION.md
│
├── testing/              ← Testing & validation
│   └── STANCE_ANALYSIS_CHECKLIST.md
│
└── implementation_sessions/  ← Session documentation
    └── STANCE_ANALYSIS_DELIVERY.md
```

## Quick Navigation

### For Understanding the Feature
1. Start with: `docs/ai-features/STANCE_ANALYSIS_IMPLEMENTATION.md`
2. Then review: `docs/implementation/STANCE_ANALYSIS_INTEGRATION_GUIDE.md`

### For Integration
1. Reference: `docs/implementation/STANCE_ANALYSIS_INTEGRATION_GUIDE.md`
2. Follow: `docs/testing/STANCE_ANALYSIS_CHECKLIST.md`
3. Verify: `docs/memory/STANCE_ANALYSIS_INFLUXDB_INTEGRATION.md`

### For Monitoring
1. Setup: `docs/memory/STANCE_ANALYSIS_INFLUXDB_INTEGRATION.md`
2. Dashboard queries included for Grafana integration

### For Project Review
1. Session notes: `docs/implementation_sessions/STANCE_ANALYSIS_DELIVERY.md`

## Related Code Files

### Core Implementation
- `src/intelligence/spacy_stance_analyzer.py` - Stance analyzer module (497 lines)
- `tests/automated/test_spacy_stance_analyzer.py` - Unit tests (188 lines, 8/8 passing)

### Integration Points
- `src/core/message_processor.py` - Message processor integration
  - Line 241: Stance analyzer initialization
  - Line 1089: User stance analysis (Phase 2.75)
  - Line 7127: Bot response filtering
  - Line 7152: Stance metadata storage
  - Line 1547: InfluxDB metrics recording

- `src/memory/vector_memory_system.py` - Qdrant storage
  - Line 817: Stance metadata extraction
  - Stance fields in payload: stance_self_focus, stance_emotion_type, etc.

- `src/monitoring/fidelity_metrics_collector.py` - Metrics recording
  - `record_emotion_and_stance()` method for InfluxDB

### Testing
- `tests/automated/test_stance_integration.py` - Integration tests

## Key Concepts

### Stance Types
- **Direct**: User's own emotions ("I'm frustrated")
- **Attributed**: Others' emotions ("You seem upset")
- **Mixed**: Combination ("I'm frustrated and you seem defensive")
- **None**: No emotions detected

### Emotion Self-Focus Ratio
- Range: 0.0 to 1.0
- 1.0 = All emotions about self
- 0.0 = All emotions about others
- 0.5 = Equal mix

### Integration Points
1. **Phase 2.75**: Early stance analysis for context-aware memory retrieval
2. **Phase 7.5**: Bot response filtering and emotion analysis
3. **Memory Storage**: Stance metadata stored with conversation
4. **Qdrant**: Stance fields enable stance-based memory queries
5. **Metrics**: InfluxDB recording for monitoring

## Testing Status

✅ **Unit Tests**: 8/8 passing
- Direct emotion detection
- Attributed emotion detection
- Mixed emotion detection
- Second-person filtering
- Negation handling
- Edge cases
- spaCy singleton reuse
- Performance (<5% overhead)

✅ **Integration Tests**: Available in `test_stance_integration.py`

## Deployment Checklist

- [x] Stance analyzer module implemented (497 lines)
- [x] Message processor integration (4 integration points)
- [x] Qdrant payload updated with stance fields
- [x] InfluxDB metrics recording added
- [x] Unit tests created and passing (8/8)
- [x] Integration tests created
- [x] Documentation organized
- [ ] Grafana dashboards created (optional)
- [ ] Production monitoring enabled (optional)

## References

### Architecture Documents
- `docs/architecture/README.md` - Overall architecture
- `docs/architecture/CHARACTER_ARCHETYPES.md` - Character design

### Related Memory Systems
- `docs/memory/` - Vector memory system documentation
- `docs/memory/STANCE_ANALYSIS_INFLUXDB_INTEGRATION.md` - Metrics integration

### Development Guides
- `docs/testing/DIRECT_PYTHON_TESTING_GUIDE.md` - Testing methodology
- `docs/implementation/STANCE_ANALYSIS_INTEGRATION_GUIDE.md` - Integration steps

## Support

For questions about:
- **Architecture**: See `docs/ai-features/STANCE_ANALYSIS_IMPLEMENTATION.md`
- **Integration**: See `docs/implementation/STANCE_ANALYSIS_INTEGRATION_GUIDE.md`
- **Testing**: See `docs/testing/STANCE_ANALYSIS_CHECKLIST.md`
- **Monitoring**: See `docs/memory/STANCE_ANALYSIS_INFLUXDB_INTEGRATION.md`
- **Session Context**: See `docs/implementation_sessions/STANCE_ANALYSIS_DELIVERY.md`

---

**Last Updated**: November 3, 2025  
**Documentation Status**: Complete ✅
