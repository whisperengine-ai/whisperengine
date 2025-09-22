#!/usr/bin/env python3
"""
Enable comprehensive AI features across all bot environment files
This script adds missing AI/emotional intelligence features to all .env.* bot files
"""

import os
import glob
from pathlib import Path

# Comprehensive AI features to add/verify
COMPREHENSIVE_AI_FEATURES = {
    # Phase 2 Emotional Intelligence
    "ENABLE_EMOTIONAL_INTELLIGENCE": "true",
    "ENABLE_EMOTIONAL_INTELLIGENCE_PERSISTENCE": "true", 
    "AI_EMOTIONAL_RESONANCE": "true",
    "ENABLE_VADER_EMOTION": "true",
    "ENABLE_ROBERTA_EMOTION": "true",
    "USE_LOCAL_EMOTION_ANALYSIS": "true",
    "EMOTION_CACHE_SIZE": "1000",
    "EMOTION_BATCH_SIZE": "16",
    "EMOTION_CONFIDENCE_THRESHOLD": "0.7",
    
    # Phase 3 Memory & Personality
    "ENABLE_PHASE3_MEMORY": "true",
    "ENABLE_PHASE3_MEMORY_NETWORKS": "true",
    "AI_ADAPTIVE_MODE": "true",
    "AI_PERSONALITY_ANALYSIS": "true", 
    "ENABLE_DYNAMIC_PERSONALITY": "true",
    "PHASE3_MAX_MEMORIES": "100",
    
    # Phase 4 Human-Like Intelligence (Complete Stack)
    "ENABLE_PHASE4_HUMAN_LIKE": "true",
    "ENABLE_PHASE4_INTELLIGENCE": "true",
    "PHASE4_PERSONALITY_TYPE": "caring_friend",
    "PHASE4_CONVERSATION_MODE": "adaptive",
    "PHASE4_EMOTIONAL_INTELLIGENCE_LEVEL": "high",
    "PHASE4_RELATIONSHIP_AWARENESS": "true",
    "PHASE4_CONVERSATION_FLOW_PRIORITY": "true",
    "PHASE4_EMPATHETIC_LANGUAGE": "true",
    "PHASE4_MEMORY_PERSONAL_DETAILS": "true",
    
    # Phase 4.2: Advanced Thread Management
    "ENABLE_PHASE4_THREAD_MANAGER": "true",
    "PHASE4_THREAD_MAX_ACTIVE": "10",
    "PHASE4_THREAD_TIMEOUT_MINUTES": "60",
    
    # Phase 4.3: Proactive Engagement Engine
    "ENABLE_PHASE4_PROACTIVE_ENGAGEMENT": "true",
    "PHASE4_ENGAGEMENT_MIN_SILENCE_MINUTES": "5",
    "PHASE4_ENGAGEMENT_MAX_SUGGESTIONS_PER_DAY": "10",
    
    # Advanced Intelligence Features
    "ENABLE_CONTEXT_INTELLIGENCE": "true",
    "ENABLE_CONVERSATION_FLOW": "true",
    "ENABLE_PROACTIVE_ENGAGEMENT": "true",
    "ENABLE_CONTEXTUAL_RESPONSES": "true",
    "ENABLE_CONVERSATION_MOMENTS": "true",
    
    # Memory Optimization Suite
    "ENABLE_MEMORY_SUMMARIZATION": "true",
    "ENABLE_MEMORY_DEDUPLICATION": "true",
    "ENABLE_MEMORY_CLUSTERING": "true",
    "ENABLE_MEMORY_PRIORITIZATION": "true",
    "SEMANTIC_CLUSTERING_MAX_MEMORIES": "50",
    "ENABLE_MEMORY_DECAY_SYSTEM": "true",
    "ENABLE_MEMORY_SIGNIFICANCE_SCORING": "true",
    "ENABLE_EMOTIONAL_TRAJECTORY_TRACKING": "true",
    "ENABLE_MULTI_QUERY_RETRIEVAL": "true",
    
    # Query Enhancement
    "ENABLE_QUERY_VARIATIONS": "true",
    "MAX_QUERY_VARIATIONS": "3",
    "QUERY_VARIATION_WEIGHT": "0.8",
    
    # Performance & Production Optimization
    "ENABLE_PRODUCTION_OPTIMIZATION": "true",
    "ENABLE_PARALLEL_PROCESSING": "true",
    "PARALLEL_PROCESSING_MAX_WORKERS": "8",
    "ENABLE_BACKGROUND_PROCESSING": "true",
    "BACKGROUND_PROCESSING_QUEUE_SIZE": "200",
    
    # Visual Emotion Analysis (if supported)
    "ENABLE_VISUAL_EMOTION_ANALYSIS": "true",
    "VISION_MODEL_PROVIDER": "openai",
    "DISCORD_VISUAL_EMOTION_ENABLED": "true",
    "VISUAL_EMOTION_MAX_IMAGE_SIZE": "20",
    "VISUAL_EMOTION_RETENTION_DAYS": "90",
    "VISUAL_EMOTION_CONFIDENCE_THRESHOLD": "0.6",
    
    # Advanced Emotion Features
    "ENABLE_LOCAL_EMOTION_ENGINE": "true",
    "ENABLE_VECTORIZED_EMOTION_PROCESSOR": "true",
    "ENABLE_ADVANCED_EMOTION_DETECTOR": "true",
    "ADVANCED_EMOTIONAL_INTELLIGENCE": "true",
    "EMOTION_DETECTION_THRESHOLD": "0.3",
    "CULTURAL_ADAPTATION_ENABLED": "true",
    "DEFAULT_CULTURAL_CONTEXT": "neutral",
    "EMOTIONAL_MEMORY_INTEGRATION": "true",
    "EMOTIONAL_RESPONSE_ADAPTATION": "true",
    
    # Adaptive Features
    "ADAPTIVE_PROMPT_ENABLED": "true",
    "ADAPTIVE_PROMPT_PERFORMANCE_MODE": "quality",
    "LARGE_MODEL_MAX_PROMPT": "4000",
    "ADAPTIVE_CONTEXT_STRATEGY": "smart_truncation",
    "PERSONALITY_ADAPTATION_ENABLED": "true",
    "CONVERSATION_CONTEXT_DEPTH": "10",
    
    # Multi-Entity Relationship Features
    "ENABLE_MULTI_ENTITY_RELATIONSHIPS": "true",
    "ENABLE_CHARACTER_CREATION": "true",
    "ENABLE_AI_FACILITATED_INTRODUCTIONS": "true",
    "ENABLE_RELATIONSHIP_EVOLUTION": "true",
    "ENABLE_CROSS_CHARACTER_AWARENESS": "true",
    
    # Comprehensive Memory Features
    "ENABLE_CONVERSATION_MEMORY": "true",
    "ENABLE_EPISODIC_MEMORY": "true",
    "ENABLE_SEMANTIC_MEMORY": "true",
    "ENABLE_HIERARCHICAL_MEMORY": "true",
    "ENABLE_ADVANCED_MEMORY_FEATURES": "true",
    "ENABLE_CONVERSATION_INTELLIGENCE": "true",
}

def get_bot_env_files():
    """Get all bot environment files"""
    env_files = []
    for pattern in [".env.elena", ".env.marcus", ".env.marcus-chen", ".env.dream", ".env.gabriel"]:
        if os.path.exists(pattern):
            env_files.append(pattern)
    return env_files

def read_env_file(filepath):
    """Read environment file and return lines"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.readlines()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return []

def write_env_file(filepath, lines):
    """Write lines to environment file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return True
    except Exception as e:
        print(f"Error writing {filepath}: {e}")
        return False

def parse_env_file(lines):
    """Parse environment file lines and return dict of existing variables"""
    env_vars = {}
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            env_vars[key.strip()] = value.strip()
    return env_vars

def add_missing_features_to_env(filepath):
    """Add missing AI features to environment file"""
    print(f"\n🔍 Processing {filepath}...")
    
    lines = read_env_file(filepath)
    if not lines:
        return False
        
    existing_vars = parse_env_file(lines)
    
    # Find missing features
    missing_features = {}
    updated_features = {}
    
    for feature, value in COMPREHENSIVE_AI_FEATURES.items():
        if feature not in existing_vars:
            missing_features[feature] = value
        elif existing_vars[feature] != value:
            # Update if value is different (e.g., false -> true)
            if existing_vars[feature].lower() in ["false", "0"] and value.lower() in ["true", "1"]:
                updated_features[feature] = value
    
    if not missing_features and not updated_features:
        print(f"✅ {filepath} already has all comprehensive AI features enabled")
        return True
    
    # Add missing features section
    if missing_features:
        lines.append("\n# ===== COMPREHENSIVE AI FEATURES =====\n")
        lines.append("# Added by enable_comprehensive_ai_features.py for complete AI testing\n")
        
        # Group features by category
        categories = {
            "# Phase 2: Advanced Emotional Intelligence": [
                "ENABLE_EMOTIONAL_INTELLIGENCE_PERSISTENCE", "AI_EMOTIONAL_RESONANCE", 
                "ENABLE_VADER_EMOTION", "ENABLE_ROBERTA_EMOTION", "USE_LOCAL_EMOTION_ANALYSIS",
                "EMOTION_CACHE_SIZE", "EMOTION_BATCH_SIZE", "EMOTION_CONFIDENCE_THRESHOLD"
            ],
            "# Phase 3: Memory & Personality Enhancement": [
                "ENABLE_PHASE3_MEMORY_NETWORKS", "AI_ADAPTIVE_MODE", "AI_PERSONALITY_ANALYSIS",
                "ENABLE_DYNAMIC_PERSONALITY", "PHASE3_MAX_MEMORIES"
            ],
            "# Phase 4: Human-Like Intelligence Suite": [
                "ENABLE_PHASE4_HUMAN_LIKE", "PHASE4_PERSONALITY_TYPE", "PHASE4_CONVERSATION_MODE",
                "PHASE4_EMOTIONAL_INTELLIGENCE_LEVEL", "PHASE4_RELATIONSHIP_AWARENESS",
                "PHASE4_CONVERSATION_FLOW_PRIORITY", "PHASE4_EMPATHETIC_LANGUAGE",
                "PHASE4_MEMORY_PERSONAL_DETAILS", "ENABLE_PHASE4_THREAD_MANAGER",
                "PHASE4_THREAD_MAX_ACTIVE", "PHASE4_THREAD_TIMEOUT_MINUTES",
                "ENABLE_PHASE4_PROACTIVE_ENGAGEMENT", "PHASE4_ENGAGEMENT_MIN_SILENCE_MINUTES",
                "PHASE4_ENGAGEMENT_MAX_SUGGESTIONS_PER_DAY"
            ],
            "# Advanced Intelligence & Context": [
                "ENABLE_CONTEXT_INTELLIGENCE", "ENABLE_CONVERSATION_FLOW", 
                "ENABLE_CONTEXTUAL_RESPONSES", "ENABLE_CONVERSATION_MOMENTS"
            ],
            "# Memory Optimization Suite": [
                "ENABLE_MEMORY_SUMMARIZATION", "ENABLE_MEMORY_DEDUPLICATION",
                "ENABLE_MEMORY_CLUSTERING", "ENABLE_MEMORY_PRIORITIZATION",
                "SEMANTIC_CLUSTERING_MAX_MEMORIES", "ENABLE_MEMORY_DECAY_SYSTEM",
                "ENABLE_MEMORY_SIGNIFICANCE_SCORING", "ENABLE_EMOTIONAL_TRAJECTORY_TRACKING",
                "ENABLE_MULTI_QUERY_RETRIEVAL"
            ],
            "# Query Enhancement & Performance": [
                "ENABLE_QUERY_VARIATIONS", "MAX_QUERY_VARIATIONS", "QUERY_VARIATION_WEIGHT",
                "ENABLE_PRODUCTION_OPTIMIZATION", "ENABLE_PARALLEL_PROCESSING",
                "PARALLEL_PROCESSING_MAX_WORKERS", "ENABLE_BACKGROUND_PROCESSING",
                "BACKGROUND_PROCESSING_QUEUE_SIZE"
            ],
            "# Visual & Advanced Emotion Analysis": [
                "ENABLE_VISUAL_EMOTION_ANALYSIS", "VISION_MODEL_PROVIDER",
                "DISCORD_VISUAL_EMOTION_ENABLED", "VISUAL_EMOTION_MAX_IMAGE_SIZE",
                "VISUAL_EMOTION_RETENTION_DAYS", "VISUAL_EMOTION_CONFIDENCE_THRESHOLD",
                "ENABLE_LOCAL_EMOTION_ENGINE", "ENABLE_VECTORIZED_EMOTION_PROCESSOR",
                "ENABLE_ADVANCED_EMOTION_DETECTOR", "ADVANCED_EMOTIONAL_INTELLIGENCE",
                "EMOTION_DETECTION_THRESHOLD", "CULTURAL_ADAPTATION_ENABLED",
                "DEFAULT_CULTURAL_CONTEXT", "EMOTIONAL_MEMORY_INTEGRATION",
                "EMOTIONAL_RESPONSE_ADAPTATION"
            ],
            "# Adaptive & Relationship Features": [
                "ADAPTIVE_PROMPT_ENABLED", "ADAPTIVE_PROMPT_PERFORMANCE_MODE",
                "LARGE_MODEL_MAX_PROMPT", "ADAPTIVE_CONTEXT_STRATEGY",
                "PERSONALITY_ADAPTATION_ENABLED", "CONVERSATION_CONTEXT_DEPTH",
                "ENABLE_AI_FACILITATED_INTRODUCTIONS", "ENABLE_RELATIONSHIP_EVOLUTION",
                "ENABLE_CROSS_CHARACTER_AWARENESS", "ENABLE_CONVERSATION_MEMORY",
                "ENABLE_EPISODIC_MEMORY", "ENABLE_SEMANTIC_MEMORY",
                "ENABLE_HIERARCHICAL_MEMORY", "ENABLE_ADVANCED_MEMORY_FEATURES",
                "ENABLE_CONVERSATION_INTELLIGENCE"
            ]
        }
        
        for category, features in categories.items():
            category_has_missing = any(f in missing_features for f in features)
            if category_has_missing:
                lines.append(f"\n{category}\n")
                for feature in features:
                    if feature in missing_features:
                        lines.append(f"{feature}={missing_features[feature]}\n")
    
    # Update existing features
    if updated_features:
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith('#') and '=' in line_stripped:
                key = line_stripped.split('=')[0].strip()
                if key in updated_features:
                    lines[i] = f"{key}={updated_features[key]}\n"
                    print(f"  🔄 Updated {key}: {existing_vars[key]} -> {updated_features[key]}")
    
    # Write updated file
    success = write_env_file(filepath, lines)
    if success:
        print(f"✅ Added {len(missing_features)} missing features and updated {len(updated_features)} features to {filepath}")
        if missing_features:
            print(f"   📦 New features: {', '.join(list(missing_features.keys())[:5])}{'...' if len(missing_features) > 5 else ''}")
    else:
        print(f"❌ Failed to update {filepath}")
    
    return success

def main():
    """Main function to enable comprehensive AI features"""
    print("🧠 WhisperEngine Comprehensive AI Feature Enablement")
    print("=" * 60)
    print(f"📋 Features to enable/verify: {len(COMPREHENSIVE_AI_FEATURES)} AI features")
    
    bot_files = get_bot_env_files()
    if not bot_files:
        print("❌ No bot environment files found!")
        return
    
    print(f"🤖 Found {len(bot_files)} bot environment files: {', '.join(bot_files)}")
    
    success_count = 0
    for bot_file in bot_files:
        if add_missing_features_to_env(bot_file):
            success_count += 1
    
    print(f"\n🎉 Results:")
    print(f"✅ Successfully updated: {success_count}/{len(bot_files)} files")
    
    if success_count == len(bot_files):
        print(f"\n🚀 All bot environment files now have comprehensive AI features enabled!")
        print(f"📋 Next steps:")
        print(f"   1. Regenerate multi-bot config: source .venv/bin/activate && python scripts/generate_multi_bot_config.py")
        print(f"   2. Restart bots: ./multi-bot.sh restart")
        print(f"   3. Test AI features: ./multi-bot.sh logs [bot_name]")
    else:
        print(f"⚠️  Some files failed to update. Check permissions and try again.")

if __name__ == "__main__":
    main()