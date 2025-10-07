// TypeScript types for CDL (Character Definition Language) data structures

export interface Character {
  id: number
  name: string
  normalized_name: string
  bot_name: string | null
  created_at: string
  updated_at: string
  is_active: boolean
  version: number
  
  // Identity fields
  occupation: string | null
  location: string | null
  age_range: string | null
  background: string | null
  description: string | null
  
  // Character archetype and AI behavior
  character_archetype: 'real-world' | 'fantasy' | 'narrative-ai'
  allow_full_roleplay_immersion: boolean
  
  // Enhanced JSONB CDL data
  cdl_data: Record<string, unknown> | null
  
  // Metadata
  created_by: string | null
  notes: string | null
}

export interface PersonalityTrait {
  id: number
  character_id: number
  trait_category: 'big_five' | 'custom' | 'emotional'
  trait_name: string
  trait_value: number | null // 0.00 to 1.00 for quantitative traits
  trait_description: string | null
  intensity: 'low' | 'medium' | 'high' | 'very_high'
  created_at: string
}

export interface CommunicationStyle {
  id: number
  character_id: number
  style_category: 'speaking_style' | 'interaction_preferences' | 'modes'
  style_name: string
  style_value: string // JSON or text value
  description: string | null
  priority: number
  created_at: string
}

export interface CharacterValue {
  id: number
  character_id: number
  value_category: 'core_values' | 'beliefs' | 'motivations'
  value_name: string
  value_description: string
  importance_level: 'low' | 'medium' | 'high' | 'critical'
  created_at: string
}

export interface AntiPattern {
  id: number
  character_id: number
  pattern_category: 'avoid_behaviors' | 'conversation_limits' | 'personality_constraints'
  pattern_name: string
  pattern_description: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  created_at: string
}

export interface PersonalKnowledge {
  id: number
  character_id: number
  knowledge_category: 'family' | 'career' | 'relationships' | 'experiences' | 'preferences'
  knowledge_type: 'fact' | 'preference' | 'experience' | 'relationship' | 'skill'
  knowledge_key: string
  knowledge_value: string
  knowledge_context: string | null
  confidence_level: number // 0.00 to 1.00
  is_public: boolean
  created_at: string
}

export interface EvolutionHistory {
  id: number
  character_id: number
  change_type: 'trait_update' | 'knowledge_added' | 'style_modified' | 'major_revision'
  change_description: string
  old_value: Record<string, unknown> // JSON
  new_value: Record<string, unknown> // JSON
  change_reason: string | null
  changed_by: string | null
  change_timestamp: string
  performance_metrics: Record<string, unknown> // JSON
  validation_status: 'pending' | 'validated' | 'rejected'
}

export interface InteractionMode {
  id: number
  character_id: number
  mode_name: 'creative' | 'technical' | 'educational' | 'casual' | string
  mode_description: string | null
  trigger_keywords: string[] // Array of keywords that activate this mode
  response_guidelines: string | null
  avoid_patterns: string[] // What to avoid in this mode
  is_default: boolean
  priority: number
  created_at: string
}

// Form data types for creating/editing characters
export interface CharacterFormData {
  name: string
  bot_name?: string
  occupation?: string
  location?: string
  age_range?: string
  background?: string
  description?: string
  character_archetype: 'real-world' | 'fantasy' | 'narrative-ai'
  allow_full_roleplay_immersion: boolean
  notes?: string
}

// API response types
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

// Type aliases for specific API responses
export type CharacterListResponse = ApiResponse<Character[]>
export type CharacterResponse = ApiResponse<Character>

// Database query filters
export interface CharacterFilters {
  archetype?: 'real-world' | 'fantasy' | 'narrative-ai'
  has_bot?: boolean
  search?: string
  sort_by?: 'name' | 'created_at' | 'updated_at'
  sort_order?: 'asc' | 'desc'
}