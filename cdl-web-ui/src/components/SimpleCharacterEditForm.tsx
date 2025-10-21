'use client'

import { useState, useEffect, useCallback } from 'react'
import { Character } from '@/types/cdl'

interface SimpleCharacterEditFormProps {
  character: Character
}

export default function SimpleCharacterEditForm({ character }: SimpleCharacterEditFormProps) {
  const [activeTab, setActiveTab] = useState('basic')
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error' | 'auto-saving'>('idle')
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})
  const [autoSaveTimeout, setAutoSaveTimeout] = useState<NodeJS.Timeout | null>(null)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  
  // Field limits for validation (updated to match database schema - Oct 2025)
  const FIELD_LIMITS = {
    name: 500,                    // Updated: DB allows 500, was 100
    occupation: 500,              // Updated: DB allows 500, was 150
    description: 1000,            // OK: TEXT field, reasonable user limit
    location: 200,                // Updated: TEXT field, reasonable user limit (was 100)
    backgroundTitle: 500,         // Updated: TEXT field, increased for better UX (was 200)
    backgroundDescription: 2000,  // OK: TEXT field
    backgroundPeriod: 100,        // OK: Matches DB VARCHAR(100)
    interestText: 1500,           // OK: TEXT field, reasonable user limit
    communicationPatternValue: 1500,  // OK: TEXT field, reasonable user limit
    communicationPatternName: 100,    // New: Matches DB VARCHAR(100)
    communicationContext: 100,        // New: Matches DB VARCHAR(100)
    speechPatternValue: 800,      // OK: TEXT field, reasonable user limit
    speechPatternType: 100,       // New: Matches DB VARCHAR(100)
    speechContext: 100,           // New: Matches DB VARCHAR(100)
    responseStyle: 2000,          // OK: TEXT field, reasonable user limit
  }
  
  // Basic character data
  const [basicData, setBasicData] = useState(() => {
    const cdl = character.cdl_data as Record<string, unknown>
    const identity = cdl?.identity as Record<string, unknown> | undefined
    
    return {
      name: character.name,
      occupation: character.occupation || '',
      description: character.description || '',
      location: (identity?.location as string) || character.location || '',
      character_archetype: character.archetype,
      allow_full_roleplay_immersion: character.allow_full_roleplay
    }
  })

  // Personality data - Initialize from character prop
  const [personalityData, setPersonalityData] = useState(() => {
    const cdl = character.cdl_data as Record<string, unknown>
    const personality = cdl?.personality as Record<string, unknown> | undefined
    const bigFive = personality?.big_five as Record<string, number> | undefined
    const values = personality?.values as string[] | undefined
    
    return {
      big_five: {
        openness: bigFive?.openness ?? 0.5,
        conscientiousness: bigFive?.conscientiousness ?? 0.5,
        extraversion: bigFive?.extraversion ?? 0.5,
        agreeableness: bigFive?.agreeableness ?? 0.5,
        neuroticism: bigFive?.neuroticism ?? 0.5
      },
      values: values || []
    }
  })
  
  // Background data
  const [backgroundData, setBackgroundData] = useState({
    entries: [] as Array<{
      id?: number
      category: string
      title: string
      description: string
      period?: string
      importance_level: number
    }>
  })

  // Interests data
  const [interestsData, setInterestsData] = useState({
    entries: [] as Array<{
      id?: number
      category: string
      interest_text: string
      proficiency_level: number
      importance: string
    }>
  })

  // Communication patterns data
  const [communicationData, setCommunicationData] = useState({
    patterns: [] as Array<{
      id?: number
      pattern_type: string
      pattern_name: string
      pattern_value: string
      context?: string
      frequency: string
    }>
  })

  // Speech patterns data
  const [speechData, setSpeechData] = useState({
    patterns: [] as Array<{
      id?: number
      pattern_type: string
      pattern_value: string
      usage_frequency: string
      context?: string
      priority: number
    }>
  })

  // Response style data
  const [responseStyleData, setResponseStyleData] = useState({
    items: [] as Array<{
      id?: number
      item_type: string
      item_text: string
      sort_order: number
    }>
  })
  
  const [newValue, setNewValue] = useState('')

  useEffect(() => {
    loadCharacterData()
  }, [character.id])

  // Update basicData when character prop changes
  useEffect(() => {
    const cdl = character.cdl_data as Record<string, unknown>
    const identity = cdl?.identity as Record<string, unknown> | undefined
    
    setBasicData({
      name: character.name,
      occupation: character.occupation || '',
      description: character.description || '',
      location: (identity?.location as string) || character.location || '',
      character_archetype: character.archetype,
      allow_full_roleplay_immersion: character.allow_full_roleplay
    })
  }, [character])

  // Update personalityData when character prop changes
  useEffect(() => {
    const cdl = character.cdl_data as Record<string, unknown>
    const personality = cdl?.personality as Record<string, unknown> | undefined
    const bigFive = personality?.big_five as Record<string, number> | undefined
    const values = personality?.values as string[] | undefined
    
    if (bigFive || values) {
      setPersonalityData({
        big_five: {
          openness: bigFive?.openness ?? 0.5,
          conscientiousness: bigFive?.conscientiousness ?? 0.5,
          extraversion: bigFive?.extraversion ?? 0.5,
          agreeableness: bigFive?.agreeableness ?? 0.5,
          neuroticism: bigFive?.neuroticism ?? 0.5
        },
        values: values || []
      })
    }
  }, [character])

  const loadCharacterData = async () => {
    // Load personality data from CDL
    if (character.cdl_data) {
      const cdl = character.cdl_data as Record<string, unknown>
      const personality = cdl.personality as Record<string, unknown> | undefined
      if (personality?.big_five) {
        setPersonalityData(prev => ({
          ...prev,
          big_five: personality.big_five as typeof prev.big_five
        }))
      }
      if (personality?.values && Array.isArray(personality.values)) {
        setPersonalityData(prev => ({
          ...prev,
          values: personality.values as string[]
        }))
      }
    }

    // Load background data
    try {
      const backgroundResponse = await fetch(`/api/characters/${character.id}/background`)
      if (backgroundResponse.ok) {
        const backgrounds = await backgroundResponse.json()
        setBackgroundData({ entries: backgrounds })
      }
    } catch (error) {
      console.error('Error loading background data:', error)
    }

    // Load interests data
    try {
      const interestsResponse = await fetch(`/api/characters/${character.id}/interests`)
      if (interestsResponse.ok) {
        const interests = await interestsResponse.json()
        setInterestsData({ entries: interests })
      }
    } catch (error) {
      console.error('Error loading interests data:', error)
    }

    // Load communication patterns
    try {
      const communicationResponse = await fetch(`/api/characters/${character.id}/communication-patterns`)
      if (communicationResponse.ok) {
        const patterns = await communicationResponse.json()
        setCommunicationData({ patterns })
      }
    } catch (error) {
      console.error('Error loading communication patterns:', error)
    }

    // Load speech patterns
    try {
      const speechResponse = await fetch(`/api/characters/${character.id}/speech-patterns`)
      if (speechResponse.ok) {
        const patterns = await speechResponse.json()
        setSpeechData({ patterns })
      }
    } catch (error) {
      console.error('Error loading speech patterns:', error)
    }

    // Load response style
    try {
      const responseResponse = await fetch(`/api/characters/${character.id}/response-style`)
      if (responseResponse.ok) {
        const data = await responseResponse.json()
        setResponseStyleData(data)
      }
    } catch (error) {
      console.error('Error loading response style:', error)
    }
  }

  // Extract the save logic into a reusable function
  const performSave = async () => {
    // Save basic character data and personality
    const cdlData = {
      identity: {
        name: basicData.name,
        occupation: basicData.occupation,
        description: basicData.description,
        location: basicData.location
      },
      personality: personalityData,
      allow_full_roleplay_immersion: basicData.allow_full_roleplay_immersion
    }

    const response = await fetch(`/api/characters/${character.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...basicData,
        cdl_data: cdlData
      }),
    })

    if (!response.ok) {
      throw new Error('Failed to save basic character data')
    }

    // Save background data
    if (backgroundData.entries.length > 0) {
      const backgroundResponse = await fetch(`/api/characters/${character.id}/background`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(backgroundData),
      })
      if (!backgroundResponse.ok) {
        throw new Error('Failed to save background data')
      }
    }

    // Save interests data
    if (interestsData.entries.length > 0) {
      const interestsResponse = await fetch(`/api/characters/${character.id}/interests`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(interestsData),
      })
      if (!interestsResponse.ok) {
        throw new Error('Failed to save interests data')
      }
    }

    // Save communication patterns
    if (communicationData.patterns.length > 0) {
      const communicationResponse = await fetch(`/api/characters/${character.id}/communication-patterns`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(communicationData),
      })
      if (!communicationResponse.ok) {
        throw new Error('Failed to save communication patterns')
      }
    }

    // Save speech patterns
    if (speechData.patterns.length > 0) {
      const speechResponse = await fetch(`/api/characters/${character.id}/speech-patterns`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(speechData),
      })
      if (!speechResponse.ok) {
        throw new Error('Failed to save speech patterns')
      }
    }

    // Save response style
    if (responseStyleData.items.length > 0) {
      const responseResponse = await fetch(`/api/characters/${character.id}/response-style`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(responseStyleData),
      })
      if (!responseResponse.ok) {
        throw new Error('Failed to save response style')
      }
    }
  }

  const handleSave = async () => {
    // Validate all fields before saving
    if (!validateAllFields()) {
      setSaveStatus('error')
      setTimeout(() => setSaveStatus('idle'), 5000)
      return
    }

    setSaveStatus('saving')
    
    try {
      await performSave()
      setSaveStatus('saved')
      setHasUnsavedChanges(false)
      setTimeout(() => setSaveStatus('idle'), 3000)
    } catch (error) {
      console.error('Error saving character:', error)
      setSaveStatus('error')
      setTimeout(() => setSaveStatus('idle'), 5000)
    }
  }

  const addValue = () => {
    if (newValue.trim() && !personalityData.values.includes(newValue.trim())) {
      setPersonalityData(prev => ({
        ...prev,
        values: [...prev.values, newValue.trim()]
      }))
      setNewValue('')
    }
  }

  const removeValue = (valueToRemove: string) => {
    setPersonalityData(prev => ({
      ...prev,
      values: prev.values.filter(value => value !== valueToRemove)
    }))
  }

  // Background helpers
  const addBackgroundEntry = () => {
    const newEntry = {
      category: 'personal',
      title: '',
      description: '',
      period: '',
      importance_level: 5
    }
    setBackgroundData(prev => ({
      entries: [...prev.entries, newEntry]
    }))
  }

  const updateBackgroundEntry = (index: number, field: string, value: any) => {
    setBackgroundData(prev => ({
      entries: prev.entries.map((entry, i) => 
        i === index ? { ...entry, [field]: value } : entry
      )
    }))
  }

  const removeBackgroundEntry = (index: number) => {
    setBackgroundData(prev => ({
      entries: prev.entries.filter((_, i) => i !== index)
    }))
  }

  // Interest helpers
  const addInterestEntry = () => {
    const newEntry = {
      category: 'hobbies',
      interest_text: '',
      proficiency_level: 5,
      importance: 'medium'
    }
    setInterestsData(prev => ({
      entries: [...prev.entries, newEntry]
    }))
  }

  const updateInterestEntry = (index: number, field: string, value: any) => {
    setInterestsData(prev => ({
      entries: prev.entries.map((entry, i) => 
        i === index ? { ...entry, [field]: value } : entry
      )
    }))
  }

  const removeInterestEntry = (index: number) => {
    setInterestsData(prev => ({
      entries: prev.entries.filter((_, i) => i !== index)
    }))
  }

  // Communication pattern helpers
  const addCommunicationPattern = () => {
    const newPattern = {
      pattern_type: 'humor',
      pattern_name: 'Default',
      pattern_value: '',
      context: 'general',
      frequency: 'regular'
    }
    setCommunicationData(prev => ({
      patterns: [...prev.patterns, newPattern]
    }))
  }

  const updateCommunicationPattern = (index: number, field: string, value: any) => {
    setCommunicationData(prev => ({
      patterns: prev.patterns.map((pattern, i) => 
        i === index ? { ...pattern, [field]: value } : pattern
      )
    }))
  }

  const removeCommunicationPattern = (index: number) => {
    setCommunicationData(prev => ({
      patterns: prev.patterns.filter((_, i) => i !== index)
    }))
  }

  // Speech pattern helpers
  const addSpeechPattern = () => {
    const newPattern = {
      pattern_type: 'catchphrase',
      pattern_value: '',
      usage_frequency: 'occasional',
      context: 'general',
      priority: 50
    }
    setSpeechData(prev => ({
      patterns: [...prev.patterns, newPattern]
    }))
  }

  const updateSpeechPattern = (index: number, field: string, value: any) => {
    setSpeechData(prev => ({
      patterns: prev.patterns.map((pattern, i) => 
        i === index ? { ...pattern, [field]: value } : pattern
      )
    }))
  }

  const removeSpeechPattern = (index: number) => {
    setSpeechData(prev => ({
      patterns: prev.patterns.filter((_, i) => i !== index)
    }))
  }

  // Response style helpers
  const addResponseStyleItem = () => {
    const newItem = {
      item_type: 'encouragement',
      item_text: '',
      sort_order: responseStyleData.items.length + 1
    }
    setResponseStyleData(prev => ({
      items: [...prev.items, newItem]
    }))
  }

  const updateResponseStyleItem = (index: number, field: string, value: any) => {
    setResponseStyleData(prev => ({
      items: prev.items.map((item, i) => 
        i === index ? { ...item, [field]: value } : item
      )
    }))
  }

  const removeResponseStyleItem = (index: number) => {
    setResponseStyleData(prev => ({
      items: prev.items.filter((_, i) => i !== index)
    }))
  }

  // Validation helpers
  const validateField = (fieldName: string, value: string): string | null => {
    const limit = FIELD_LIMITS[fieldName as keyof typeof FIELD_LIMITS]
    if (!limit) return null
    
    if (value.length > limit) {
      return `${fieldName} must be ${limit} characters or less (currently ${value.length})`
    }
    return null
  }

  const getCharacterCount = (text: string, limit: number) => {
    const remaining = limit - text.length
    const percentage = (text.length / limit) * 100
    return {
      current: text.length,
      limit,
      remaining,
      percentage,
      isNearLimit: percentage > 80,
      isOverLimit: percentage > 100
    }
  }

  const CharacterCounter = ({ text, limit, label }: { text: string; limit: number; label: string }) => {
    const count = getCharacterCount(text, limit)
    return (
      <div className={`text-xs mt-1 ${
        count.isOverLimit ? 'text-red-600' : 
        count.isNearLimit ? 'text-yellow-600' : 
        'text-gray-500'
      }`}>
        {count.current}/{count.limit} characters
        {count.isOverLimit && (
          <span className="ml-2 font-medium">({count.current - count.limit} over limit)</span>
        )}
      </div>
    )
  }

  const validateAllFields = (): boolean => {
    const errors: Record<string, string> = {}
    
    // Validate basic fields
    const nameError = validateField('name', basicData.name)
    if (nameError) errors.name = nameError
    
    const occupationError = validateField('occupation', basicData.occupation)
    if (occupationError) errors.occupation = occupationError
    
    const descriptionError = validateField('description', basicData.description)
    if (descriptionError) errors.description = descriptionError
    
    const locationError = validateField('location', basicData.location)
    if (locationError) errors.location = locationError
    
    // Validate background entries
    backgroundData.entries.forEach((entry, index) => {
      const titleError = validateField('backgroundTitle', entry.title)
      if (titleError) errors[`background_title_${index}`] = titleError
      
      const descError = validateField('backgroundDescription', entry.description)
      if (descError) errors[`background_description_${index}`] = descError
      
      if (entry.period) {
        const periodError = validateField('period', entry.period)
        if (periodError) errors[`background_period_${index}`] = periodError
      }
    })
    
    // Validate interests
    interestsData.entries.forEach((entry, index) => {
      const textError = validateField('interestText', entry.interest_text)
      if (textError) errors[`interest_text_${index}`] = textError
    })
    
    // Validate communication patterns
    communicationData.patterns.forEach((pattern, index) => {
      const valueError = validateField('communicationPattern', pattern.pattern_value)
      if (valueError) errors[`communication_pattern_${index}`] = valueError
    })
    
    // Validate speech patterns
    speechData.patterns.forEach((pattern, index) => {
      const valueError = validateField('speechPattern', pattern.pattern_value)
      if (valueError) errors[`speech_pattern_${index}`] = valueError
    })
    
    // Validate response styles
    responseStyleData.items.forEach((item, index) => {
      const textError = validateField('responseStyle', item.item_text)
      if (textError) errors[`response_style_${index}`] = textError
    })
    
    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  // Auto-save functionality
  const triggerAutoSave = useCallback(() => {
    if (autoSaveTimeout) {
      clearTimeout(autoSaveTimeout)
    }
    
    const timeout = setTimeout(async () => {
      if (hasUnsavedChanges && validateAllFields()) {
        setSaveStatus('auto-saving')
        try {
          await performSave()
          setSaveStatus('saved')
          setHasUnsavedChanges(false)
          setTimeout(() => {
            setSaveStatus('idle')
          }, 2000)
        } catch (error) {
          setSaveStatus('idle') // Don't show error for auto-save failures
        }
      }
    }, 2000) // Auto-save after 2 seconds of inactivity
    
    setAutoSaveTimeout(timeout)
  }, [autoSaveTimeout, hasUnsavedChanges])

  // Track changes to trigger auto-save
  const handleFieldChange = useCallback((callback: () => void) => {
    callback()
    setHasUnsavedChanges(true)
    triggerAutoSave()
  }, [triggerAutoSave])

  // Cleanup auto-save timeout
  useEffect(() => {
    return () => {
      if (autoSaveTimeout) {
        clearTimeout(autoSaveTimeout)
      }
    }
    }, [autoSaveTimeout])

  // Example templates for guidance
  const getBackgroundExample = (category: string) => {
    const examples = {
      childhood: {
        title: "Growing up in a small coastal town",
        description: "I spent my childhood in a tight-knit fishing community where everyone knew each other. My grandmother ran the local bookstore, and I'd spend hours there reading adventure stories and listening to old sailors' tales. This taught me the value of community, storytelling, and finding wonder in everyday life.",
        period: "Ages 5-12"
      },
      education: {
        title: "Discovering my passion for marine biology",
        description: "During my undergraduate studies, I took an elective marine biology course that completely changed my perspective. The first time I saw microscopic plankton under a microscope, I was amazed by the intricate beauty of these tiny creatures that form the foundation of ocean life. This moment sparked my lifelong fascination with the hidden complexities of nature.",
        period: "University years"
      },
      career: {
        title: "My first breakthrough research project",
        description: "Early in my career, I spent months studying coral reef ecosystems and discovered a new symbiotic relationship between certain fish species and coral polyps. The long nights of observation, the careful data collection, and the eventual 'eureka' moment taught me patience, attention to detail, and the incredible reward of contributing new knowledge to the world.",
        period: "Early career"
      },
      formative: {
        title: "The storm that changed everything",
        description: "I was caught in an unexpected thunderstorm during a research dive, and had to take shelter in an underwater cave. In those quiet, suspended moments surrounded by bioluminescent organisms, I realized how resilient and adaptable life can be. This experience taught me to find calm in chaos and to always look for the beauty in challenging situations.",
        period: "Mid-twenties"
      }
    }
    return examples[category as keyof typeof examples] || { title: "", description: "", period: "" }
  }

  const getInterestExample = (category: string) => {
    const examples = {
      academic: "I'm fascinated by the intersection of ancient philosophy and modern AI ethics. There's something beautiful about how Aristotle's virtue ethics applies to machine learning - the idea that intelligence, whether human or artificial, should be guided by wisdom and moral character. I love exploring how age-old questions about consciousness and decision-making take on new meaning in our digital age.",
      creative: "Photography is my way of capturing the fleeting moments that tell deeper stories. I'm drawn to the challenge of finding extraordinary beauty in ordinary scenes - the way morning light hits a weathered fence, or how shadows create geometric patterns on city walls. Each photo is like a haiku, saying something profound with minimal elements.",
      nature: "Ocean conservation isn't just my profession, it's my calling. Every dive feels like exploring an alien world right here on Earth. I'm constantly amazed by the ingenious survival strategies of marine life - from the way cleaner fish establish 'service stations' on reefs to how dolphins use tools and teach their young. The ocean teaches me daily lessons about adaptation, cooperation, and resilience."
    }
    return examples[category as keyof typeof examples] || ""
  }

  // Generate character preview
  const generateCharacterPreview = () => {
    const sections = []
    
    // Basic Information
    if (basicData.name || basicData.occupation || basicData.description) {
      sections.push({
        title: "Core Identity",
        content: `You are ${basicData.name}${basicData.occupation ? `, a ${basicData.occupation}` : ''}${basicData.location ? ` based in ${basicData.location}` : ''}. ${basicData.description}`
      })
    }

    // Personality traits
    if (personalityData.big_five) {
      const traits = Object.entries(personalityData.big_five)
        .map(([trait, value]) => {
          const level = value < 0.3 ? 'low' : value > 0.7 ? 'high' : 'moderate'
          return `${trait} (${level})`
        })
        .join(', ')
      
      sections.push({
        title: "Personality Profile",
        content: `Your personality traits: ${traits}.`
      })
    }

    // Values
    if (personalityData.values.length > 0) {
      sections.push({
        title: "Core Values",
        content: `You are guided by these values: ${personalityData.values.join(', ')}.`
      })
    }

    // Background stories
    if (backgroundData.entries.length > 0) {
      const backgrounds = backgroundData.entries
        .sort((a, b) => b.importance_level - a.importance_level)
        .slice(0, 3) // Show top 3 most important
        .map(entry => `${entry.title}: ${entry.description}`)
        .join('\n\n')
      
      sections.push({
        title: "Key Background",
        content: backgrounds
      })
    }

    // Interests
    if (interestsData.entries.length > 0) {
      const interests = interestsData.entries
        .filter(entry => entry.importance === 'high' || entry.importance === 'defining')
        .map(entry => entry.interest_text)
        .join('\n\n')
      
      if (interests) {
        sections.push({
          title: "Passionate Interests",
          content: interests
        })
      }
    }

    // Communication patterns
    if (communicationData.patterns.length > 0) {
      const patterns = communicationData.patterns
        .map(pattern => `${pattern.pattern_type}: ${pattern.pattern_value}`)
        .join('\n\n')
      
      sections.push({
        title: "Communication Style",
        content: patterns
      })
    }

    // Speech patterns
    if (speechData.patterns.length > 0) {
      const speech = speechData.patterns
        .sort((a, b) => b.priority - a.priority)
        .slice(0, 3) // Top 3 priority patterns
        .map(pattern => pattern.pattern_value)
        .join(' ')
      
      sections.push({
        title: "Speech Patterns",
        content: speech
      })
    }

    // Response styles
    if (responseStyleData.items.length > 0) {
      const responses = responseStyleData.items
        .map(item => `${item.item_type}: ${item.item_text}`)
        .join('\n\n')
      
      sections.push({
        title: "Response Guidelines",
        content: responses
      })
    }

    return sections
  }

  const tabs = [
    { id: 'basic', name: 'Basic Info' },
    { id: 'personality', name: 'Personality' },
    { id: 'background', name: 'Background' },
    { id: 'interests', name: 'Interests' },
    { id: 'communication', name: 'Communication' },
    { id: 'speech', name: 'Speech Style' },
    { id: 'responses', name: 'Response Style' },
    { id: 'preview', name: 'Preview' }
  ]

  return (
    <div className="space-y-6">
      {saveStatus !== 'idle' && (
        <div className={`p-4 rounded-lg ${
          saveStatus === 'saving' ? 'bg-gray-800 text-blue-700' :
          saveStatus === 'auto-saving' ? 'bg-yellow-50 text-yellow-700' :
          saveStatus === 'saved' ? 'bg-green-50 text-green-700' :
          'bg-red-50 text-red-700'
        }`}>
          {saveStatus === 'saving' && (
            <div className="flex items-center">
              <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-blue-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Saving character...
            </div>
          )}
          {saveStatus === 'auto-saving' && (
            <div className="flex items-center">
              <svg className="animate-pulse -ml-1 mr-3 h-4 w-4 text-yellow-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Auto-saving...
            </div>
          )}
          {saveStatus === 'saved' && '✓ Character saved successfully!'}
          {saveStatus === 'error' && 'Error saving character. Please try again.'}
        </div>
      )}

      <div className="border-b border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-300 hover:border-gray-600'
              }`}
            >
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      <div className="bg-gray-800 rounded-lg shadow p-6">
        {activeTab === 'basic' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-100 mb-4">Basic Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-100 mb-2">Name</label>
                <input
                  type="text"
                  value={basicData.name}
                  onChange={(e) => handleFieldChange(() => setBasicData(prev => ({ ...prev, name: e.target.value })))}
                  className={`w-full border rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100 ${
                    validationErrors.name ? 'border-red-500' : 'border-gray-600'
                  }`}
                />
                <CharacterCounter text={basicData.name} limit={FIELD_LIMITS.name} label="name" />
                {validationErrors.name && (
                  <p className="text-red-600 text-xs mt-1">{validationErrors.name}</p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  The character's display name used in conversations and throughout the system.
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-100 mb-2">Occupation</label>
                <input
                  type="text"
                  value={basicData.occupation}
                  onChange={(e) => setBasicData(prev => ({ ...prev, occupation: e.target.value }))}
                  className={`w-full border rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100 ${
                    validationErrors.occupation ? 'border-red-500' : 'border-gray-600'
                  }`}
                />
                <CharacterCounter text={basicData.occupation} limit={FIELD_LIMITS.occupation} label="occupation" />
                {validationErrors.occupation && (
                  <p className="text-red-600 text-xs mt-1">{validationErrors.occupation}</p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  The character's profession or role, which influences their knowledge areas and conversation topics.
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-100 mb-2">Location</label>
                <input
                  type="text"
                  value={basicData.location}
                  onChange={(e) => setBasicData(prev => ({ ...prev, location: e.target.value }))}
                  className={`w-full border rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100 ${
                    validationErrors.location ? 'border-red-500' : 'border-gray-600'
                  }`}
                />
                <CharacterCounter text={basicData.location} limit={FIELD_LIMITS.location} label="location" />
                {validationErrors.location && (
                  <p className="text-red-600 text-xs mt-1">{validationErrors.location}</p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  Where the character is from or currently located, affecting cultural context and experiences.
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-100 mb-2">Character Type</label>
                <select
                  value={basicData.character_archetype}
                  onChange={(e) => setBasicData(prev => ({ ...prev, character_archetype: e.target.value as any }))}
                  className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                >
                  <option value="real-world">Real-world (honest about AI)</option>
                  <option value="fantasy">Fantasy (full roleplay)</option>
                  <option value="narrative-ai">Narrative AI (AI is part of story)</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Determines how the character handles questions about their AI nature and roleplay boundaries.
                </p>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-100 mb-2">Description</label>
              <textarea
                value={basicData.description}
                onChange={(e) => handleFieldChange(() => setBasicData(prev => ({ ...prev, description: e.target.value })))}
                rows={4}
                placeholder="Describe your character's personality, approach, and what makes them unique. This is their core identity that shapes all interactions..."
                className={`w-full border rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100 ${
                  validationErrors.description ? 'border-red-500' : 'border-gray-600'
                }`}
              />
              <CharacterCounter text={basicData.description} limit={FIELD_LIMITS.description} label="description" />
              {validationErrors.description && (
                <p className="text-red-600 text-xs mt-1">{validationErrors.description}</p>
              )}
              <p className="text-xs text-gray-500 mt-1">
                A fundamental overview of who this character is. This description is central to all AI responses and sets the foundational personality tone.
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={basicData.allow_full_roleplay_immersion}
                onChange={(e) => setBasicData(prev => ({ ...prev, allow_full_roleplay_immersion: e.target.checked }))}
                className="mr-2"
              />
              <label className="text-sm font-medium text-gray-100">Allow full roleplay immersion</label>
              <div className="text-xs text-gray-500">
                When enabled, the character stays in character even when directly asked about being AI
              </div>
            </div>
          </div>
        )}

        {activeTab === 'personality' && (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-100 mb-4">Personality Configuration</h3>
            
            <div>
              <h4 className="text-md font-medium text-gray-100 mb-4">Big Five Personality Traits</h4>
              <p className="text-sm text-gray-400 mb-4">
                These traits shape how your character thinks, feels, and behaves in conversations. They directly influence response tone, curiosity level, and social interaction style in the AI prompts.
              </p>
              <div className="space-y-4">
                {Object.entries(personalityData.big_five).map(([trait, value]) => (
                  <div key={trait}>
                    <label className="block text-sm font-medium text-gray-100 mb-2 capitalize">
                      {trait}: {value}
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={value}
                      onChange={(e) => setPersonalityData(prev => ({
                        ...prev,
                        big_five: {
                          ...prev.big_five,
                          [trait]: parseFloat(e.target.value)
                        }
                      }))}
                      className="w-full"
                    />
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="text-md font-medium text-gray-100 mb-4">Core Values</h4>
              <p className="text-sm text-gray-400 mb-4">
                Values guide your character's decision-making and moral compass. They influence what topics the character prioritizes and how they approach ethical discussions in conversations.
              </p>
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addValue()}
                  placeholder="Add a core value..."
                  className="flex-1 bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                />
                <button
                  onClick={addValue}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {personalityData.values.map((value, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                  >
                    {value}
                    <button
                      onClick={() => removeValue(value)}
                      className="ml-2 text-blue-400 hover:text-blue-800"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'background' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium text-gray-100">Character Background</h3>
              <button
                onClick={addBackgroundEntry}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Add Background Story
              </button>
            </div>
            <p className="text-sm text-gray-400">
              Background stories provide rich narrative context that shapes your character's worldview, experiences, and knowledge. These stories are woven into conversation prompts to create authentic, lived-in personalities.
            </p>
            
            <div className="space-y-6">
              {backgroundData.entries.map((entry, index) => (
                <div key={index} className="border border-gray-700 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-4">
                    <h4 className="font-medium text-gray-100">Background Story {index + 1}</h4>
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          const example = getBackgroundExample(entry.category)
                          updateBackgroundEntry(index, 'title', example.title)
                          updateBackgroundEntry(index, 'description', example.description)
                          updateBackgroundEntry(index, 'period', example.period)
                        }}
                        className="px-3 py-1 text-xs bg-green-100 text-green-700 rounded-md hover:bg-green-200"
                      >
                        Use Example
                      </button>
                      <button
                        onClick={() => removeBackgroundEntry(index)}
                        className="text-red-600 hover:text-red-800"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-100 mb-2">Category</label>
                      <select
                        value={entry.category}
                        onChange={(e) => updateBackgroundEntry(index, 'category', e.target.value)}
                        className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                      >
                        <option value="childhood">Childhood</option>
                        <option value="education">Education</option>
                        <option value="career">Career</option>
                        <option value="personal">Personal Life</option>
                        <option value="formative">Formative Experience</option>
                        <option value="relationship">Relationships</option>
                        <option value="achievement">Achievement</option>
                        <option value="challenge">Challenge/Struggle</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-100 mb-2">Time Period</label>
                      <input
                        type="text"
                        value={entry.period || ''}
                        onChange={(e) => updateBackgroundEntry(index, 'period', e.target.value)}
                        placeholder="e.g., Childhood, College Years, Early Career"
                        className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                      />
                    </div>
                  </div>
                  
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-100 mb-2">Title</label>
                    <input
                      type="text"
                      value={entry.title}
                      onChange={(e) => updateBackgroundEntry(index, 'title', e.target.value)}
                      placeholder="e.g., Growing up in a small library town"
                      className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                    />
                  </div>
                  
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-100 mb-2">Story Description</label>
                    <textarea
                      value={entry.description}
                      onChange={(e) => updateBackgroundEntry(index, 'description', e.target.value)}
                      placeholder="Tell the story in detail. How did this experience shape who you are? What did you learn? How does it influence your perspective today?"
                      rows={4}
                      className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-100 mb-2">
                      Importance Level: {entry.importance_level}/10
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={entry.importance_level}
                      onChange={(e) => updateBackgroundEntry(index, 'importance_level', parseInt(e.target.value))}
                      className="w-full"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Higher importance stories are more likely to influence conversations and responses.
                    </p>
                  </div>
                </div>
              ))}
              
              {backgroundData.entries.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No background stories yet. Add some to give your character depth and history!
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'interests' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium text-gray-100">Interests & Passions</h3>
              <button
                onClick={addInterestEntry}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Add Interest
              </button>
            </div>
            <p className="text-sm text-gray-400">
              Interests drive natural conversation topics and enthusiasm. They determine what subjects your character gets excited about and can discuss knowledgeably, creating more engaging and authentic interactions.
            </p>
            
            <div className="space-y-6">
              {interestsData.entries.map((entry, index) => (
                <div key={index} className="border border-gray-700 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-4">
                    <h4 className="font-medium text-gray-100">Interest {index + 1}</h4>
                    <button
                      onClick={() => removeInterestEntry(index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-100 mb-2">Category</label>
                      <select
                        value={entry.category}
                        onChange={(e) => updateInterestEntry(index, 'category', e.target.value)}
                        className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                      >
                        <option value="hobbies">Hobbies & Recreation</option>
                        <option value="academic">Academic & Learning</option>
                        <option value="creative">Creative Arts</option>
                        <option value="technology">Technology</option>
                        <option value="science">Science & Research</option>
                        <option value="philosophy">Philosophy & Ideas</option>
                        <option value="culture">Culture & Society</option>
                        <option value="nature">Nature & Environment</option>
                        <option value="sports">Sports & Fitness</option>
                        <option value="travel">Travel & Adventure</option>
                        <option value="food">Food & Cooking</option>
                        <option value="business">Business & Entrepreneurship</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-100 mb-2">Importance</label>
                      <select
                        value={entry.importance}
                        onChange={(e) => updateInterestEntry(index, 'importance', e.target.value)}
                        className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                      >
                        <option value="low">Low - Casual interest</option>
                        <option value="medium">Medium - Regular passion</option>
                        <option value="high">High - Core passion</option>
                        <option value="defining">Defining - Life-shaping interest</option>
                      </select>
                    </div>
                  </div>
                  
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-100 mb-2">Interest Description</label>
                    <textarea
                      value={entry.interest_text}
                      onChange={(e) => updateInterestEntry(index, 'interest_text', e.target.value)}
                      placeholder="Describe your passion in detail. What fascinates you about this? How did you get into it? What unique perspectives do you have? Use creative language and metaphors!"
                      rows={4}
                      className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-100 mb-2">
                      Knowledge Level: {entry.proficiency_level}/10
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={entry.proficiency_level}
                      onChange={(e) => updateInterestEntry(index, 'proficiency_level', parseInt(e.target.value))}
                      className="w-full"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      How knowledgeable and experienced are you in this area? (1=Beginner, 10=Expert)
                    </p>
                  </div>
                </div>
              ))}
              
              {interestsData.entries.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No interests added yet. Add some to make conversations more engaging and natural!
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'communication' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium text-gray-100">Communication Patterns</h3>
              <button
                onClick={addCommunicationPattern}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Add Pattern
              </button>
            </div>
            <p className="text-sm text-gray-400">
              Communication patterns define your character's unique voice and style. They control how your character expresses ideas, uses humor, explains concepts, and adapts their communication to different situations.
            </p>
            
            <div className="space-y-6">
              {communicationData.patterns.map((pattern, index) => (
                <div key={index} className="border border-gray-700 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-4">
                    <h4 className="font-medium text-gray-100">Communication Pattern {index + 1}</h4>
                    <button
                      onClick={() => removeCommunicationPattern(index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-100 mb-2">Pattern Type</label>
                      <select
                        value={pattern.pattern_type}
                        onChange={(e) => updateCommunicationPattern(index, 'pattern_type', e.target.value)}
                        className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                      >
                        <option value="humor">Humor Style</option>
                        <option value="explanation">Explanation Method</option>
                        <option value="storytelling">Storytelling Approach</option>
                        <option value="questioning">Question Asking</option>
                        <option value="encouragement">Encouragement Style</option>
                        <option value="disagreement">Disagreement Handling</option>
                        <option value="metaphor">Metaphor Usage</option>
                        <option value="emotion">Emotional Expression</option>
                        <option value="complexity">Complexity Management</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-100 mb-2">Context</label>
                      <select
                        value={pattern.context || 'general'}
                        onChange={(e) => updateCommunicationPattern(index, 'context', e.target.value)}
                        className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                      >
                        <option value="general">General Conversation</option>
                        <option value="teaching">Teaching/Explaining</option>
                        <option value="problem-solving">Problem Solving</option>
                        <option value="emotional">Emotional Support</option>
                        <option value="creative">Creative Discussion</option>
                        <option value="technical">Technical Topics</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-100 mb-2">Frequency</label>
                      <select
                        value={pattern.frequency}
                        onChange={(e) => updateCommunicationPattern(index, 'frequency', e.target.value)}
                        className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                      >
                        <option value="rare">Rare</option>
                        <option value="occasional">Occasional</option>
                        <option value="regular">Regular</option>
                        <option value="frequent">Frequent</option>
                        <option value="constant">Constant</option>
                      </select>
                    </div>
                  </div>
                  
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-100 mb-2">Pattern Name</label>
                    <input
                      type="text"
                      value={pattern.pattern_name}
                      onChange={(e) => updateCommunicationPattern(index, 'pattern_name', e.target.value)}
                      placeholder="e.g., Thoughtful Metaphor Maker, Gentle Questioner"
                      className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-100 mb-2">Pattern Description</label>
                    <textarea
                      value={pattern.pattern_value}
                      onChange={(e) => updateCommunicationPattern(index, 'pattern_value', e.target.value)}
                      placeholder="Describe this communication pattern in detail. How do you use this style? When do you employ it? What makes it distinctive? Give specific examples!"
                      rows={4}
                      className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                    />
                  </div>
                </div>
              ))}
              
              {communicationData.patterns.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No communication patterns defined yet. Add some to give your character a distinctive voice!
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'speech' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium text-gray-100">Speech Patterns & Voice</h3>
              <button
                onClick={addSpeechPattern}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Add Speech Pattern
              </button>
            </div>
            <p className="text-sm text-gray-400">
              Speech patterns create your character's unique verbal fingerprint. These include catchphrases, thinking patterns, conversation habits, and linguistic quirks that make your character's voice instantly recognizable.
            </p>
            
            <div className="space-y-6">
              {speechData.patterns.map((pattern, index) => (
                <div key={index} className="border border-gray-700 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-4">
                    <h4 className="font-medium text-gray-100">Speech Pattern {index + 1}</h4>
                    <button
                      onClick={() => removeSpeechPattern(index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-100 mb-2">Pattern Type</label>
                      <select
                        value={pattern.pattern_type}
                        onChange={(e) => updateSpeechPattern(index, 'pattern_type', e.target.value)}
                        className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                      >
                        <option value="catchphrase">Catchphrase</option>
                        <option value="thinking">Thinking Pattern</option>
                        <option value="transition">Transition Phrase</option>
                        <option value="greeting">Greeting Style</option>
                        <option value="emphasis">Emphasis Technique</option>
                        <option value="pause">Thoughtful Pause</option>
                        <option value="connection">Connection Maker</option>
                        <option value="clarification">Clarification Style</option>
                        <option value="enthusiasm">Enthusiasm Expression</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-100 mb-2">Usage Frequency</label>
                      <select
                        value={pattern.usage_frequency}
                        onChange={(e) => updateSpeechPattern(index, 'usage_frequency', e.target.value)}
                        className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                      >
                        <option value="rare">Rare - Special occasions</option>
                        <option value="occasional">Occasional - Sometimes</option>
                        <option value="regular">Regular - Often</option>
                        <option value="frequent">Frequent - Very often</option>
                        <option value="signature">Signature - Defining trait</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-100 mb-2">Context</label>
                      <select
                        value={pattern.context || 'general'}
                        onChange={(e) => updateSpeechPattern(index, 'context', e.target.value)}
                        className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                      >
                        <option value="general">Any conversation</option>
                        <option value="excited">When excited</option>
                        <option value="thinking">When thinking</option>
                        <option value="explaining">When explaining</option>
                        <option value="surprised">When surprised</option>
                        <option value="connecting">Making connections</option>
                      </select>
                    </div>
                  </div>
                  
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-100 mb-2">Speech Pattern</label>
                    <textarea
                      value={pattern.pattern_value}
                      onChange={(e) => updateSpeechPattern(index, 'pattern_value', e.target.value)}
                      placeholder="Describe or write out the exact speech pattern. e.g., 'Hmm, that's fascinating because...' or 'You know what I love about that? It's like...' Include specific phrases, word choices, or verbal habits."
                      rows={3}
                      className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-100 mb-2">
                      Priority: {pattern.priority}/100
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="100"
                      value={pattern.priority}
                      onChange={(e) => updateSpeechPattern(index, 'priority', parseInt(e.target.value))}
                      className="w-full"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Higher priority patterns are more likely to appear in responses. (1=Background trait, 100=Dominant characteristic)
                    </p>
                  </div>
                </div>
              ))}
              
              {speechData.patterns.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No speech patterns defined yet. Add some to give your character a distinctive speaking voice!
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'responses' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium text-gray-100">Response Style Guidelines</h3>
              <button
                onClick={addResponseStyleItem}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Add Response Style
              </button>
            </div>
            <p className="text-sm text-gray-400">
              Response styles define how your character handles different conversational situations. These guidelines shape the character's approach to encouragement, problem-solving, creativity, and emotional support.
            </p>
            
            <div className="space-y-6">
              {responseStyleData.items.map((item, index) => (
                <div key={index} className="border border-gray-700 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-4">
                    <h4 className="font-medium text-gray-100">Response Style {index + 1}</h4>
                    <button
                      onClick={() => removeResponseStyleItem(index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                  
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-100 mb-2">Situation Type</label>
                    <select
                      value={item.item_type}
                      onChange={(e) => updateResponseStyleItem(index, 'item_type', e.target.value)}
                      className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                    >
                      <option value="encouragement">Encouragement & Support</option>
                      <option value="explanation">Explanations & Teaching</option>
                      <option value="problem-solving">Problem Solving</option>
                      <option value="creativity">Creative Discussions</option>
                      <option value="disagreement">Handling Disagreement</option>
                      <option value="confusion">When User is Confused</option>
                      <option value="frustration">When User is Frustrated</option>
                      <option value="excitement">When User is Excited</option>
                      <option value="philosophical">Philosophical Topics</option>
                      <option value="technical">Technical Discussions</option>
                      <option value="personal">Personal Topics</option>
                      <option value="humor">Humor & Lightness</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-100 mb-2">Response Approach</label>
                    <textarea
                      value={item.item_text}
                      onChange={(e) => updateResponseStyleItem(index, 'item_text', e.target.value)}
                      placeholder="Describe how your character responds in this situation. What's their approach? What techniques do they use? How do they balance different needs? Be specific about tone, methods, and examples."
                      rows={4}
                      className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                    />
                  </div>
                </div>
              ))}
              
              {responseStyleData.items.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No response styles defined yet. Add some to guide how your character handles different conversational situations!
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'preview' && (
          <div className="space-y-6">
            <div className="bg-gray-800 p-4 rounded-lg mb-6">
              <h3 className="text-lg font-semibold text-blue-900 mb-2">Character Preview</h3>
              <p className="text-blue-700">
                This shows how your character's information will be integrated into AI prompts.
                This preview combines all your character data into a cohesive personality description.
              </p>
            </div>

            {generateCharacterPreview().map((section, index) => (
              <div key={index} className="bg-gray-900 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-100 mb-3 border-b pb-2">
                  {section.title}
                </h4>
                <div className="text-gray-300 whitespace-pre-line">
                  {section.content}
                </div>
              </div>
            ))}

            {generateCharacterPreview().length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <p className="text-lg">No character data to preview yet</p>
                <p className="text-sm mt-2">Fill in the other tabs to see how your character will appear in AI prompts</p>
              </div>
            )}

            <div className="bg-yellow-50 p-4 rounded-lg mt-6">
              <h4 className="font-semibold text-yellow-900 mb-2">💡 Preview Notes</h4>
              <ul className="text-yellow-800 text-sm space-y-1">
                <li>• Only the most important and high-priority items are shown</li>
                <li>• The actual prompt may include additional context based on conversation history</li>
                <li>• Background stories are ordered by importance level</li>
                <li>• Speech patterns are ordered by priority</li>
              </ul>
            </div>
          </div>
        )}
      </div>

      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saveStatus === 'saving'}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saveStatus === 'saving' ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  )
}
