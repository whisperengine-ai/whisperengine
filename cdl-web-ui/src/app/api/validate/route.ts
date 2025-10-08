import { NextRequest, NextResponse } from 'next/server'

interface CharacterData {
  name?: string
  cdl_data?: {
    identity?: {
      occupation?: string
      description?: string
      location?: string
      age?: number
      voice?: unknown
    }
    personality?: {
      big_five?: {
        openness: number
        conscientiousness: number
        extraversion: number
        agreeableness: number
        neuroticism: number
      }
      values?: string[]
      communication_style?: unknown
    }
    communication?: {
      response_length?: string
      ai_identity_handling?: {
        approach?: string
      }
    }
    personal_knowledge?: {
      background?: string
      interests?: string[]
      skills?: string[]
    }
  }
  learning_metadata?: {
    learning_profile?: unknown
  }
  learningProfile?: unknown
}

interface ValidationResult {
  isValid: boolean
  score: number
  errors: string[]
  warnings: string[]
  suggestions: string[]
  completeness: {
    identity: number
    personality: number
    communication: number
    knowledge: number
    overall: number
  }
  learning_profile_analysis?: {
    adaptability_assessment: string
    attachment_risk_level: string
    growth_potential: string
    recommendations: string[]
  }
}

export async function POST(request: NextRequest) {
  try {
    const { character_data, analysis_type = 'full' } = await request.json()
    
    if (!character_data) {
      return NextResponse.json({
        success: false,
        error: 'Missing character data'
      }, { status: 400 })
    }

    const validation = validateCharacter(character_data, analysis_type)
    
    return NextResponse.json({
      success: true,
      validation,
      analysis_type,
      analyzed_at: new Date().toISOString()
    })
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}

function validateCharacter(data: CharacterData, analysisType: string): ValidationResult {
  const errors: string[] = []
  const warnings: string[] = []
  const suggestions: string[] = []
  
  // Identity validation
  let identityScore = 0
  if (data.name) identityScore += 25
  if (data.cdl_data?.identity?.occupation) identityScore += 25
  if (data.cdl_data?.identity?.description) identityScore += 25
  if (data.cdl_data?.identity?.location) identityScore += 15
  if (data.cdl_data?.identity?.age) identityScore += 10

  if (!data.name) errors.push('Missing required field: name')
  if (!data.cdl_data?.identity?.occupation) errors.push('Missing required field: occupation')
  if (!data.cdl_data?.identity?.description) warnings.push('Missing description - helps users understand the character')

  // Personality validation
  let personalityScore = 0
  if (data.cdl_data?.personality?.big_five) {
    personalityScore += 30
    const bigFive = data.cdl_data.personality.big_five
    const scores = [bigFive.openness, bigFive.conscientiousness, bigFive.extraversion, bigFive.agreeableness, bigFive.neuroticism]
    if (scores.every(s => typeof s === 'number' && s >= 0 && s <= 1)) {
      personalityScore += 20
    } else {
      warnings.push('Big Five scores should be between 0 and 1')
    }
  } else {
    errors.push('Missing Big Five personality scores')
  }

  if (data.cdl_data?.personality?.values && data.cdl_data.personality.values.length > 0) {
    personalityScore += 25
  } else {
    warnings.push('No values defined - helps establish character priorities')
  }

  if (data.cdl_data?.personality?.communication_style) {
    personalityScore += 25
  } else {
    errors.push('Missing communication style')
  }

  // Communication validation
  let communicationScore = 0
  if (data.cdl_data?.communication?.response_length) communicationScore += 25
  if (data.cdl_data?.communication?.ai_identity_handling) {
    communicationScore += 50
    if (data.cdl_data.communication.ai_identity_handling.approach) communicationScore += 25
  } else {
    errors.push('Missing AI identity handling configuration')
  }

  // Knowledge validation
  let knowledgeScore = 0
  if (data.cdl_data?.personal_knowledge?.background) knowledgeScore += 30
  if (data.cdl_data?.personal_knowledge?.interests && data.cdl_data.personal_knowledge.interests.length > 0) knowledgeScore += 35
  if (data.cdl_data?.personal_knowledge?.skills && data.cdl_data.personal_knowledge.skills.length > 0) knowledgeScore += 35

  if (knowledgeScore < 50) {
    suggestions.push('Add more personal knowledge (background, interests, skills) to make character more engaging')
  }

  // Learning profile analysis (if available)
  let learningProfileAnalysis
  if (data.learning_metadata?.learning_profile || data.learningProfile) {
    const profile = data.learning_metadata?.learning_profile || data.learningProfile
    if (profile && typeof profile === 'object') {
      const typedProfile = profile as { adaptabilityLevel?: string; attachmentRisk?: string; growthAreas?: string[] }
      learningProfileAnalysis = {
        adaptability_assessment: getAdaptabilityAssessment(typedProfile.adaptabilityLevel || ''),
        attachment_risk_level: getAttachmentRiskAssessment(typedProfile.attachmentRisk || ''),
        growth_potential: getGrowthPotential(typedProfile.growthAreas || []),
        recommendations: getLearningRecommendations(typedProfile)
      }
    }
  }

  // Generate suggestions based on analysis
  if (analysisType === 'full') {
    if (personalityScore < 80) {
      suggestions.push('Enhance personality depth with more detailed values and communication preferences')
    }
    if (identityScore < 80) {
      suggestions.push('Add more identity details like location, age, or background story')
    }
    if (!data.cdl_data?.identity?.voice) {
      suggestions.push('Consider adding voice characteristics (pace, tone, accent) for richer character expression')
    }
  }

  const completeness = {
    identity: identityScore,
    personality: personalityScore,
    communication: communicationScore,
    knowledge: knowledgeScore,
    overall: Math.round((identityScore + personalityScore + communicationScore + knowledgeScore) / 4)
  }

  return {
    isValid: errors.length === 0,
    score: completeness.overall,
    errors,
    warnings,
    suggestions,
    completeness,
    learning_profile_analysis: learningProfileAnalysis
  }
}

function getAdaptabilityAssessment(level: string): string {
  switch (level) {
    case 'high': return 'High adaptability - Character learns quickly from user interactions'
    case 'medium': return 'Medium adaptability - Balanced learning with personality stability'
    case 'low': return 'Low adaptability - Consistent personality with minimal drift'
    default: return 'Adaptability level not specified'
  }
}

function getAttachmentRiskAssessment(risk: string): string {
  switch (risk) {
    case 'high': return 'High attachment risk - Monitor for emotional dependency patterns'
    case 'medium': return 'Medium attachment risk - Standard monitoring recommended'
    case 'low': return 'Low attachment risk - Healthy boundaries maintained'
    default: return 'Attachment risk not specified'
  }
}

function getGrowthPotential(areas: string[]): string {
  if (!areas || areas.length === 0) return 'No growth areas specified'
  if (areas.length >= 4) return 'High growth potential - Multiple development areas'
  if (areas.length >= 2) return 'Medium growth potential - Focused development areas'
  return 'Limited growth potential - Single development focus'
}

function getLearningRecommendations(profile: { adaptabilityLevel?: string; attachmentRisk?: string; memoryRetention?: string; growthAreas?: string[] }): string[] {
  const recommendations = []
  
  if (profile.adaptabilityLevel === 'high') {
    recommendations.push('Implement conversation tracking to monitor learning patterns')
    recommendations.push('Set up periodic personality drift detection')
  }
  
  if (profile.attachmentRisk === 'high') {
    recommendations.push('Enable attachment monitoring and intervention protocols')
    recommendations.push('Define clear professional boundaries in communication style')
  }
  
  if (profile.memoryRetention === 'long') {
    recommendations.push('Implement memory cleanup policies to prevent information overload')
  }
  
  if (profile.growthAreas?.includes('emotional_intelligence')) {
    recommendations.push('Enable advanced emotion detection and response capabilities')
  }
  
  if (profile.growthAreas?.includes('domain_expertise')) {
    recommendations.push('Integrate domain-specific knowledge bases and update mechanisms')
  }

  return recommendations
}