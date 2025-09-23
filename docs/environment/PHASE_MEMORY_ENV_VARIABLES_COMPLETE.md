# Phase 1 & 2 Memory System Environment Variables - Complete Reference

## Overview

This document provides a comprehensive reference for all Phase 1 and Phase 2 memory system environment variables that have been added to WhisperEngine's configuration system.

## Phase Features Control

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_PHASE1_ENHANCED_MEMORY` | `true` | Enable Phase 1 enhanced memory features |
| `ENABLE_PHASE2_THREE_TIER_MEMORY` | `true` | Enable Phase 2 three-tier memory architecture |
| `ENABLE_PHASE3_MEMORY_NETWORKS` | `true` | Enable Phase 3 memory networks |
| `ENABLE_PHASE4_INTELLIGENCE` | `true` | Enable Phase 4 intelligence features |
| `ENABLE_PHASE4_THREAD_MANAGER` | `true` | Enable Phase 4 thread management |
| `ENABLE_PHASE4_PROACTIVE_ENGAGEMENT` | `true` | Enable Phase 4 proactive engagement |
| `DISABLE_PHASE2_EMOTION` | `false` | Disable Phase 2 emotional processing |
| `DISABLE_PHASE4_INTELLIGENCE` | `false` | Disable Phase 4 intelligence features |

## Phase 1: Enhanced Memory Features

### 1.1 Enhanced Emotional Detection Thresholds

| Variable | Default | Description |
|----------|---------|-------------|
| `PHASE1_EMOTIONAL_DETECTION_ENABLED` | `true` | Enable enhanced emotional detection |
| `PHASE1_EMOTION_VERY_POSITIVE_THRESHOLD` | `0.95` | Threshold for very positive emotions |
| `PHASE1_EMOTION_POSITIVE_THRESHOLD` | `0.7` | Threshold for positive emotions |
| `PHASE1_EMOTION_MILDLY_POSITIVE_THRESHOLD` | `0.4` | Threshold for mildly positive emotions |
| `PHASE1_EMOTION_VERY_NEGATIVE_THRESHOLD` | `0.95` | Threshold for very negative emotions |
| `PHASE1_EMOTION_NEGATIVE_THRESHOLD` | `0.7` | Threshold for negative emotions |
| `PHASE1_EMOTION_MILDLY_NEGATIVE_THRESHOLD` | `0.4` | Threshold for mildly negative emotions |
| `PHASE1_EMOTION_ANXIOUS_THRESHOLD` | `0.8` | Threshold for anxious emotions |
| `PHASE1_EMOTION_CONTEMPLATIVE_THRESHOLD` | `0.3` | Threshold for contemplative emotions |
| `PHASE1_EMOTION_NEUTRAL_INTENSITY` | `0.1` | Intensity value for neutral emotions |

### 1.2 Emotional Trajectory Tracking

| Variable | Default | Description |
|----------|---------|-------------|
| `PHASE1_EMOTIONAL_TRAJECTORY_ENABLED` | `true` | Enable emotional trajectory tracking |
| `PHASE1_EMOTIONAL_MOMENTUM_WEIGHT` | `0.7` | Weight for emotional momentum calculation |
| `PHASE1_EMOTIONAL_VELOCITY_DECAY` | `0.9` | Decay rate for emotional velocity |

### 1.3 Memory Significance Scoring

| Variable | Default | Description |
|----------|---------|-------------|
| `PHASE1_SIGNIFICANCE_SCORING_ENABLED` | `true` | Enable memory significance scoring |
| `PHASE1_SIGNIFICANCE_BASE_SCORE` | `0.5` | Base significance score for new memories |
| `PHASE1_SIGNIFICANCE_EMOTIONAL_WEIGHT` | `0.3` | Weight of emotional content in significance |
| `PHASE1_SIGNIFICANCE_CONTEXT_WEIGHT` | `0.4` | Weight of contextual relevance in significance |
| `PHASE1_SIGNIFICANCE_INTERACTION_WEIGHT` | `0.3` | Weight of user interaction in significance |

## Phase 2: Three-Tier Memory Architecture

### 2.1 Memory Tier Management

| Variable | Default | Description |
|----------|---------|-------------|
| `PHASE2_THREE_TIER_ENABLED` | `true` | Enable three-tier memory system |
| `PHASE2_MEMORY_TIER_SHORT_TERM_MAX_AGE_DAYS` | `7` | Maximum age for short-term memories |
| `PHASE2_MEMORY_TIER_MEDIUM_TERM_MAX_AGE_DAYS` | `30` | Maximum age for medium-term memories |
| `PHASE2_MEMORY_TIER_LONG_TERM_PRESERVATION` | `true` | Preserve long-term memories indefinitely |

### 2.2 Memory Tier Promotion Thresholds

| Variable | Default | Description |
|----------|---------|-------------|
| `PHASE2_TIER_PROMOTE_TO_MEDIUM_SIGNIFICANCE` | `0.6` | Significance threshold to promote to medium-term |
| `PHASE2_TIER_PROMOTE_TO_MEDIUM_EMOTIONAL_INTENSITY` | `0.7` | Emotional intensity threshold for medium-term |
| `PHASE2_TIER_PROMOTE_TO_MEDIUM_MIN_AGE_DAYS` | `3` | Minimum age before medium-term promotion |
| `PHASE2_TIER_PROMOTE_TO_LONG_SIGNIFICANCE` | `0.8` | Significance threshold to promote to long-term |
| `PHASE2_TIER_PROMOTE_TO_LONG_EMOTIONAL_INTENSITY` | `0.9` | Emotional intensity threshold for long-term |
| `PHASE2_TIER_PROMOTE_TO_LONG_MIN_AGE_DAYS` | `7` | Minimum age before long-term promotion |

### 2.3 Memory Tier Demotion & Expiration

| Variable | Default | Description |
|----------|---------|-------------|
| `PHASE2_TIER_DEMOTE_TO_SHORT_SIGNIFICANCE` | `0.4` | Significance threshold for demotion to short-term |
| `PHASE2_TIER_DEMOTE_TO_SHORT_MAX_AGE_DAYS` | `14` | Maximum age before demotion consideration |
| `PHASE2_TIER_EXPIRE_SHORT_TERM_SIGNIFICANCE` | `0.3` | Significance below which short-term memories expire |
| `PHASE2_TIER_EXPIRE_SHORT_TERM_MAX_AGE_DAYS` | `7` | Age at which low-significance short-term memories expire |

### 2.4 Memory Decay System

| Variable | Default | Description |
|----------|---------|-------------|
| `PHASE2_MEMORY_DECAY_ENABLED` | `true` | Enable memory decay mechanism |
| `PHASE2_MEMORY_DECAY_RATE` | `0.1` | Base decay rate (0.0-1.0) |
| `PHASE2_MEMORY_DECAY_PROTECTION_THRESHOLD` | `0.8` | Significance threshold for decay protection |
| `PHASE2_MEMORY_DECAY_HIGH_PROTECTION_MULTIPLIER` | `0.1` | Decay multiplier for highly significant memories |
| `PHASE2_MEMORY_DECAY_MEDIUM_PROTECTION_MULTIPLIER` | `0.3` | Decay multiplier for moderately significant memories |
| `PHASE2_MEMORY_DECAY_AGE_MAX_MULTIPLIER` | `3.0` | Maximum age multiplier for decay acceleration |
| `PHASE2_MEMORY_DECAY_DELETE_THRESHOLD` | `0.05` | Significance below which memories are deleted |

### 2.5 Tier-Specific Decay Rates

| Variable | Default | Description |
|----------|---------|-------------|
| `PHASE2_DECAY_SHORT_TERM_MULTIPLIER` | `1.0` | Decay rate multiplier for short-term memories |
| `PHASE2_DECAY_MEDIUM_TERM_MULTIPLIER` | `0.5` | Decay rate multiplier for medium-term memories |
| `PHASE2_DECAY_LONG_TERM_MULTIPLIER` | `0.1` | Decay rate multiplier for long-term memories |

### 2.6 Phase 2 Integration Controls

| Variable | Default | Description |
|----------|---------|-------------|
| `EMOTION_GRAPH_SYNC_INTERVAL` | `300` | Interval in seconds for emotion graph synchronization |

## Configuration by Deployment Type

### Quick Start (.env.example.quick-start)
- **Focus**: Basic functionality with minimal configuration
- **Memory Decay Rate**: `0.1` (standard)
- **Features**: Phase 1 & 2 enabled, simplified settings

### Development (.env.example.development)
- **Focus**: Full features with debug settings
- **Memory Decay Rate**: `0.05` (slower for debugging)
- **Features**: All phases enabled, lower thresholds for testing

### Production (.env.example.production)
- **Focus**: Stable, conservative settings
- **Memory Decay Rate**: `0.1` (standard)
- **Features**: All phases enabled, production-optimized thresholds

### Enterprise (.env.example.enterprise)
- **Focus**: Maximum precision and features
- **Memory Decay Rate**: `0.08` (slightly slower for data retention)
- **Features**: All phases enabled, fine-tuned thresholds for enterprise use

### Local AI (.env.example.local-ai)
- **Focus**: Performance optimization for local hardware
- **Memory Decay Rate**: `0.15` (faster to conserve resources)
- **Features**: Phase 3 disabled for performance, conservative limits

## Implementation Status

✅ **Complete**: All Phase 1 and Phase 2 memory system environment variables have been:
- Added to the main `.env` file with comprehensive settings
- Integrated into all 5 example configuration files
- Tailored for each deployment scenario
- Documented with clear descriptions and defaults

## Usage Examples

### Enabling Conservative Memory Settings
```bash
PHASE2_MEMORY_DECAY_RATE=0.05
PHASE2_TIER_PROMOTE_TO_MEDIUM_SIGNIFICANCE=0.7
PHASE2_TIER_PROMOTE_TO_LONG_SIGNIFICANCE=0.9
```

### Enabling Aggressive Memory Management
```bash
PHASE2_MEMORY_DECAY_RATE=0.2
PHASE2_TIER_EXPIRE_SHORT_TERM_MAX_AGE_DAYS=3
PHASE2_MEMORY_DECAY_DELETE_THRESHOLD=0.1
```

### Disabling Specific Phase Features
```bash
ENABLE_PHASE1_ENHANCED_MEMORY=false
ENABLE_PHASE2_THREE_TIER_MEMORY=false
DISABLE_PHASE2_EMOTION=true
```

## Related Files

- **Main Configuration**: `.env`
- **Example Configurations**: `config/examples/.env.*.example`
- **Implementation**: `src/memory/vector_memory_system.py`
- **Integration**: `src/memory/phase2_integration.py`
- **Character System**: Added to all character environment variables

## Summary

This comprehensive environment variable system provides full control over WhisperEngine's Phase 1 and Phase 2 memory features, enabling fine-tuned configuration for different deployment scenarios while maintaining backward compatibility with existing installations.