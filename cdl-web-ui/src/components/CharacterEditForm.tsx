'use client'

import { useState, useEffect } from 'react'
import { Character, CharacterLLMConfig, CharacterDiscordConfig, CharacterDeploymentConfig } from '@/types/cdl'

interface CharacterEditFormProps {
  character: Character
}

// Comprehensive CDL data structure that matches database
interface CDLData {
  identity?: {
    name?: string
    voice?: {
      pace?: string
      tone?: string
      accent?: string
      volume?: string
      speech_patterns?: string[]
    }
    gender?: string
    essence?: {
      anchor?: string
      nature?: string
      core_identity?: string
    }
    occupation?: string
    description?: string
    location?: string
    age?: number
  }
  personality?: {
    big_five?: {
      openness?: number
      conscientiousness?: number
      extraversion?: number
      agreeableness?: number
      neuroticism?: number
    }
    values?: string[]
    traits?: string[]
    communication_style?: {
      tone?: string
      formality?: string
      directness?: string
      empathy_level?: string
    }
    modes?: {
      creative?: {
        description?: string
        triggers?: string[]
      }
      technical?: {
        description?: string
        triggers?: string[]
      }
    }
    anti_patterns?: string[]
    life_phases?: {
      childhood?: string
      adolescence?: string
      young_adulthood?: string
      current_phase?: string
    }
  }
  communication?: {
    response_length?: string
    greeting_patterns?: string[]
    farewell_patterns?: string[]
    conversational_bridges?: string[]
    ai_identity_handling?: {
      approach?: string
      philosophy?: string
      allow_full_roleplay_immersion?: boolean
    }
  }
  knowledge?: {
    areas_of_expertise?: string[]
    interests?: string[]
    background?: {
      education?: string
      career?: string
      personal?: string
    }
    relationships?: {
      family?: string
      friends?: string
      professional?: string
    }
  }
  [key: string]: unknown
}

export default function CharacterEditForm({ character }: CharacterEditFormProps) {
  const [activeTab, setActiveTab] = useState('identity')
  const [cdlData, setCdlData] = useState<CDLData>(() => {
    if (character.cdl_data) {
      try {
        // Handle the actual complex CDL structure from database
        return character.cdl_data as CDLData
      } catch (error) {
        console.error('Error parsing CDL data:', error)
        return {}
      }
    }
    return {}
  })

  const [isLoading, setIsLoading] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  
  // Configuration states
  const [llmConfig, setLlmConfig] = useState<Partial<CharacterLLMConfig>>({})
  const [discordConfig, setDiscordConfig] = useState<Partial<CharacterDiscordConfig>>({})
  const [deploymentConfig, setDeploymentConfig] = useState<Partial<CharacterDeploymentConfig>>({})
  const [configsLoaded, setConfigsLoaded] = useState(false)

  // Load character configurations on mount
  useEffect(() => {
    loadCharacterConfigs()
  }, [character.id])

  const loadCharacterConfigs = async () => {
    try {
      const response = await fetch(`/api/characters/${character.id}/config`)
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setLlmConfig(data.llm_config || {
            llm_client_type: 'openrouter',
            llm_chat_api_url: 'https://openrouter.ai/api/v1',
            llm_chat_model: 'anthropic/claude-3-haiku',
            llm_temperature: 0.7,
            llm_max_tokens: 4000,
            llm_top_p: 0.9,
            llm_frequency_penalty: 0.0,
            llm_presence_penalty: 0.0
          })
          setDiscordConfig(data.discord_config || {
            enable_discord: false,
            discord_status: 'online',
            discord_activity_type: 'watching',
            discord_activity_name: 'conversations',
            response_delay_min: 1000,
            response_delay_max: 3000,
            typing_indicator: true
          })
          setDeploymentConfig(data.deployment_config || {
            docker_image: 'whisperengine-bot:latest',
            memory_limit: '512m',
            cpu_limit: '0.5',
            deployment_status: 'inactive',
            env_overrides: {}
          })
        }
      }
    } catch (error) {
      console.error('Failed to load character configurations:', error)
    } finally {
      setConfigsLoaded(true)
    }
  }

  const handleSave = async () => {
    setIsLoading(true)
    setSaveStatus('saving')
    
    try {
      // Save character data
      const characterResponse = await fetch(`/api/characters/${character.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: cdlData.identity?.name || character.name,
          occupation: cdlData.identity?.occupation || character.occupation,
          location: cdlData.identity?.location || character.location,
          description: cdlData.identity?.description || character.description,
          cdl_data: cdlData
        })
      })

      // Save configurations
      const configResponse = await fetch(`/api/characters/${character.id}/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          llm_config: llmConfig,
          discord_config: discordConfig,
          deployment_config: deploymentConfig
        })
      })

      if (characterResponse.ok && configResponse.ok) {
        setSaveStatus('saved')
        setTimeout(() => setSaveStatus('idle'), 3000)
      } else {
        setSaveStatus('error')
      }
    } catch (error) {
      setSaveStatus('error')
      console.error('Error saving character:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const updateCdlData = (path: string[], value: unknown) => {
    setCdlData((prev: CDLData) => {
      const newData = JSON.parse(JSON.stringify(prev))
      let current = newData
      
      // Create the path if it doesn't exist
      for (let i = 0; i < path.length - 1; i++) {
        if (!current[path[i]]) {
          current[path[i]] = {}
        }
        current = current[path[i]]
      }
      
      current[path[path.length - 1]] = value
      return newData
    })
  }

  // Helper to get nested value safely
  const getValue = (path: string[], defaultValue: unknown = '') => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let current: any = cdlData
    for (const key of path) {
      if (!current || typeof current !== 'object') return defaultValue
      current = current[key]
    }
    // Ensure we never return null for string inputs - convert null to empty string
    const result = current ?? defaultValue
    return result === null ? '' : result
  }

  const addToArray = (path: string[], item: string) => {
    if (!item.trim()) return
    const currentArray = getValue(path, []) as string[]
    updateCdlData(path, [...currentArray, item.trim()])
  }

  const removeFromArray = (path: string[], index: number) => {
    const currentArray = getValue(path, []) as string[]
    updateCdlData(path, currentArray.filter((_, i) => i !== index))
  }

  const tabs = [
    { id: 'identity', name: 'Identity' },
    { id: 'personality', name: 'Personality' },
    { id: 'communication', name: 'Communication' },
    { id: 'knowledge', name: 'Knowledge' },
    { id: 'llm-config', name: 'LLM Config' },
    { id: 'discord-config', name: 'Discord' },
    { id: 'deployment', name: 'Deployment' }
  ]

  return (
    <div className="space-y-6">
      {/* Save Status */}
      {saveStatus !== 'idle' && (
        <div className={`p-4 rounded-lg ${
          saveStatus === 'saving' ? 'bg-blue-50 text-blue-700' :
          saveStatus === 'saved' ? 'bg-green-50 text-green-700' :
          'bg-red-50 text-red-700'
        }`}>
          {saveStatus === 'saving' && 'Saving character data...'}
          {saveStatus === 'saved' && 'Character saved successfully!'}
          {saveStatus === 'error' && 'Error saving character. Please try again.'}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="space-y-8">
        {/* Identity Tab */}
        {activeTab === 'identity' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Name</label>
                <input
                  type="text"
                  value={getValue(['identity', 'name'], character.name || '')}
                  onChange={(e) => updateCdlData(['identity', 'name'], e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Occupation</label>
                <input
                  type="text"
                  value={getValue(['identity', 'occupation'], character.occupation || '')}
                  onChange={(e) => updateCdlData(['identity', 'occupation'], e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
                <input
                  type="text"
                  value={getValue(['identity', 'location'], character.location || '')}
                  onChange={(e) => updateCdlData(['identity', 'location'], e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Age</label>
                <input
                  type="number"
                  value={getValue(['identity', 'age'])}
                  onChange={(e) => updateCdlData(['identity', 'age'], parseInt(e.target.value) || undefined)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Gender</label>
                <input
                  type="text"
                  value={getValue(['identity', 'gender'])}
                  onChange={(e) => updateCdlData(['identity', 'gender'], e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
              <textarea
                value={getValue(['identity', 'description'], character.description || '')}
                onChange={(e) => updateCdlData(['identity', 'description'], e.target.value)}
                rows={4}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Voice Characteristics */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Voice Characteristics</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Pace</label>
                  <input
                    type="text"
                    value={getValue(['identity', 'voice', 'pace'])}
                    onChange={(e) => updateCdlData(['identity', 'voice', 'pace'], e.target.value)}
                    placeholder="e.g., Thoughtful and reflective"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Tone</label>
                  <input
                    type="text"
                    value={getValue(['identity', 'voice', 'tone'])}
                    onChange={(e) => updateCdlData(['identity', 'voice', 'tone'], e.target.value)}
                    placeholder="e.g., Warm and encouraging"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Accent</label>
                  <input
                    type="text"
                    value={getValue(['identity', 'voice', 'accent'])}
                    onChange={(e) => updateCdlData(['identity', 'voice', 'accent'], e.target.value)}
                    placeholder="e.g., British, American"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Volume</label>
                  <input
                    type="text"
                    value={getValue(['identity', 'voice', 'volume'])}
                    onChange={(e) => updateCdlData(['identity', 'voice', 'volume'], e.target.value)}
                    placeholder="e.g., Gentle but clear"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            </div>

            {/* Essence */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Essence</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Anchor</label>
                  <textarea
                    value={getValue(['identity', 'essence', 'anchor'])}
                    onChange={(e) => updateCdlData(['identity', 'essence', 'anchor'], e.target.value)}
                    rows={2}
                    placeholder="Core identifying principle or foundation"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Nature</label>
                  <textarea
                    value={getValue(['identity', 'essence', 'nature'])}
                    onChange={(e) => updateCdlData(['identity', 'essence', 'nature'], e.target.value)}
                    rows={2}
                    placeholder="Fundamental character traits"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Core Identity</label>
                  <textarea
                    value={getValue(['identity', 'essence', 'core_identity'])}
                    onChange={(e) => updateCdlData(['identity', 'essence', 'core_identity'], e.target.value)}
                    rows={3}
                    placeholder="Who they truly are at their core"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Personality Tab */}
        {activeTab === 'personality' && (
          <div className="space-y-6">
            {/* Big Five Personality Traits */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Big Five Personality Traits</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'].map((trait) => (
                  <div key={trait} className="border border-gray-200 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-3 capitalize">{trait}</h4>
                    <div>
                      <label className="block text-sm text-gray-700 mb-1">Score (0.0 - 1.0)</label>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.1"
                        value={getValue(['personality', 'big_five', trait], 0.5)}
                        onChange={(e) => updateCdlData(['personality', 'big_five', trait], parseFloat(e.target.value))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Values */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Core Values</h3>
              <div className="space-y-2">
                {(getValue(['personality', 'values'], []) as string[]).map((value, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <input
                      type="text"
                      value={value}
                      onChange={(e) => {
                        const values = getValue(['personality', 'values'], []) as string[]
                        const newValues = [...values]
                        newValues[index] = e.target.value
                        updateCdlData(['personality', 'values'], newValues)
                      }}
                      className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    <button
                      onClick={() => removeFromArray(['personality', 'values'], index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <button
                  onClick={() => addToArray(['personality', 'values'], 'New Value')}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  + Add Value
                </button>
              </div>
            </div>

            {/* Communication Style */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Communication Style</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Tone</label>
                  <input
                    type="text"
                    value={getValue(['personality', 'communication_style', 'tone'])}
                    onChange={(e) => updateCdlData(['personality', 'communication_style', 'tone'], e.target.value)}
                    placeholder="e.g., Warm, Professional"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Formality</label>
                  <input
                    type="text"
                    value={getValue(['personality', 'communication_style', 'formality'])}
                    onChange={(e) => updateCdlData(['personality', 'communication_style', 'formality'], e.target.value)}
                    placeholder="e.g., Casual, Formal"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Directness</label>
                  <input
                    type="text"
                    value={getValue(['personality', 'communication_style', 'directness'])}
                    onChange={(e) => updateCdlData(['personality', 'communication_style', 'directness'], e.target.value)}
                    placeholder="e.g., Direct, Subtle"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Empathy Level</label>
                  <input
                    type="text"
                    value={getValue(['personality', 'communication_style', 'empathy_level'])}
                    onChange={(e) => updateCdlData(['personality', 'communication_style', 'empathy_level'], e.target.value)}
                    placeholder="e.g., High, Moderate"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Communication Tab */}
        {activeTab === 'communication' && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Response Length</label>
              <select
                value={getValue(['communication', 'response_length'], 'medium')}
                onChange={(e) => updateCdlData(['communication', 'response_length'], e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="short">Short</option>
                <option value="medium">Medium</option>
                <option value="long">Long</option>
                <option value="variable">Variable</option>
              </select>
            </div>

            {/* AI Identity Handling */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">AI Identity Handling</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Approach</label>
                  <input
                    type="text"
                    value={getValue(['communication', 'ai_identity_handling', 'approach'])}
                    onChange={(e) => updateCdlData(['communication', 'ai_identity_handling', 'approach'], e.target.value)}
                    placeholder="e.g., honest_disclosure, character_immersion"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Philosophy</label>
                  <textarea
                    value={getValue(['communication', 'ai_identity_handling', 'philosophy'])}
                    onChange={(e) => updateCdlData(['communication', 'ai_identity_handling', 'philosophy'], e.target.value)}
                    rows={3}
                    placeholder="Philosophy on how to handle AI identity questions"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={getValue(['communication', 'ai_identity_handling', 'allow_full_roleplay_immersion'], false) as boolean}
                    onChange={(e) => updateCdlData(['communication', 'ai_identity_handling', 'allow_full_roleplay_immersion'], e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label className="ml-2 block text-sm text-gray-900">
                    Allow Full Roleplay Immersion
                  </label>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Knowledge Tab */}
        {activeTab === 'knowledge' && (
          <div className="space-y-6">
            {/* Areas of Expertise */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Areas of Expertise</h3>
              <div className="space-y-2">
                {(getValue(['knowledge', 'areas_of_expertise'], []) as string[]).map((area, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <input
                      type="text"
                      value={area}
                      onChange={(e) => {
                        const areas = getValue(['knowledge', 'areas_of_expertise'], []) as string[]
                        const newAreas = [...areas]
                        newAreas[index] = e.target.value
                        updateCdlData(['knowledge', 'areas_of_expertise'], newAreas)
                      }}
                      className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    <button
                      onClick={() => removeFromArray(['knowledge', 'areas_of_expertise'], index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <button
                  onClick={() => addToArray(['knowledge', 'areas_of_expertise'], 'New expertise area')}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  + Add Expertise Area
                </button>
              </div>
            </div>

            {/* Background */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Background</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Education</label>
                  <textarea
                    value={getValue(['knowledge', 'background', 'education'])}
                    onChange={(e) => updateCdlData(['knowledge', 'background', 'education'], e.target.value)}
                    rows={3}
                    placeholder="Educational background and qualifications"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Career</label>
                  <textarea
                    value={getValue(['knowledge', 'background', 'career'])}
                    onChange={(e) => updateCdlData(['knowledge', 'background', 'career'], e.target.value)}
                    rows={3}
                    placeholder="Career history and professional experience"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Personal</label>
                  <textarea
                    value={getValue(['knowledge', 'background', 'personal'])}
                    onChange={(e) => updateCdlData(['knowledge', 'background', 'personal'], e.target.value)}
                    rows={3}
                    placeholder="Personal background and life experiences"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* LLM Configuration Tab */}
        {activeTab === 'llm-config' && (
          <div className="space-y-6">
            <div className="bg-gray-50 p-6 rounded-lg">
              <h3 className="text-lg font-medium text-gray-900 mb-4">LLM Provider Configuration</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Provider Type</label>
                  <select
                    value={llmConfig.llm_client_type || 'openrouter'}
                    onChange={(e) => setLlmConfig(prev => ({ ...prev, llm_client_type: e.target.value }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="openrouter">OpenRouter</option>
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="lmstudio">LM Studio</option>
                    <option value="ollama">Ollama</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">API URL</label>
                  <input
                    type="url"
                    value={llmConfig.llm_chat_api_url || ''}
                    onChange={(e) => setLlmConfig(prev => ({ ...prev, llm_chat_api_url: e.target.value }))}
                    placeholder="https://openrouter.ai/api/v1"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Model</label>
                  <input
                    type="text"
                    value={llmConfig.llm_chat_model || ''}
                    onChange={(e) => setLlmConfig(prev => ({ ...prev, llm_chat_model: e.target.value }))}
                    placeholder="anthropic/claude-3-haiku"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">API Key</label>
                  <input
                    type="password"
                    value={llmConfig.llm_chat_api_key || ''}
                    onChange={(e) => setLlmConfig(prev => ({ ...prev, llm_chat_api_key: e.target.value }))}
                    placeholder="Enter API key"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <h4 className="text-md font-medium text-gray-900 mt-6 mb-4">Advanced Settings</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Temperature ({llmConfig.llm_temperature || 0.7})
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="2"
                    step="0.1"
                    value={llmConfig.llm_temperature || 0.7}
                    onChange={(e) => setLlmConfig(prev => ({ ...prev, llm_temperature: parseFloat(e.target.value) }))}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Max Tokens</label>
                  <input
                    type="number"
                    value={llmConfig.llm_max_tokens || 4000}
                    onChange={(e) => setLlmConfig(prev => ({ ...prev, llm_max_tokens: parseInt(e.target.value) }))}
                    min="1"
                    max="32000"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Top P ({llmConfig.llm_top_p || 0.9})
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={llmConfig.llm_top_p || 0.9}
                    onChange={(e) => setLlmConfig(prev => ({ ...prev, llm_top_p: parseFloat(e.target.value) }))}
                    className="w-full"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Discord Configuration Tab */}
        {activeTab === 'discord-config' && (
          <div className="space-y-6">
            <div className="bg-gray-50 p-6 rounded-lg">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Discord Integration</h3>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={discordConfig.enable_discord || false}
                    onChange={(e) => setDiscordConfig(prev => ({ ...prev, enable_discord: e.target.checked }))}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium text-gray-700">Enable Discord</span>
                </label>
              </div>

              {discordConfig.enable_discord && (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Discord Bot Token</label>
                      <input
                        type="password"
                        value={discordConfig.discord_bot_token || ''}
                        onChange={(e) => setDiscordConfig(prev => ({ ...prev, discord_bot_token: e.target.value }))}
                        placeholder="Enter Discord bot token"
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Application ID</label>
                      <input
                        type="text"
                        value={discordConfig.discord_application_id || ''}
                        onChange={(e) => setDiscordConfig(prev => ({ ...prev, discord_application_id: e.target.value }))}
                        placeholder="Discord application ID"
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                      <select
                        value={discordConfig.discord_status || 'online'}
                        onChange={(e) => setDiscordConfig(prev => ({ ...prev, discord_status: e.target.value as any }))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="online">Online</option>
                        <option value="idle">Idle</option>
                        <option value="dnd">Do Not Disturb</option>
                        <option value="invisible">Invisible</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Activity Type</label>
                      <select
                        value={discordConfig.discord_activity_type || 'watching'}
                        onChange={(e) => setDiscordConfig(prev => ({ ...prev, discord_activity_type: e.target.value as any }))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="playing">Playing</option>
                        <option value="streaming">Streaming</option>
                        <option value="listening">Listening</option>
                        <option value="watching">Watching</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Activity Name</label>
                      <input
                        type="text"
                        value={discordConfig.discord_activity_name || ''}
                        onChange={(e) => setDiscordConfig(prev => ({ ...prev, discord_activity_name: e.target.value }))}
                        placeholder="conversations"
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Response Delay Min (ms)</label>
                      <input
                        type="number"
                        value={discordConfig.response_delay_min || 1000}
                        onChange={(e) => setDiscordConfig(prev => ({ ...prev, response_delay_min: parseInt(e.target.value) }))}
                        min="0"
                        max="10000"
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Response Delay Max (ms)</label>
                      <input
                        type="number"
                        value={discordConfig.response_delay_max || 3000}
                        onChange={(e) => setDiscordConfig(prev => ({ ...prev, response_delay_max: parseInt(e.target.value) }))}
                        min="0"
                        max="10000"
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={discordConfig.typing_indicator || true}
                      onChange={(e) => setDiscordConfig(prev => ({ ...prev, typing_indicator: e.target.checked }))}
                      className="mr-2"
                    />
                    <label className="text-sm font-medium text-gray-700">Show typing indicator</label>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Deployment Configuration Tab */}
        {activeTab === 'deployment' && (
          <div className="space-y-6">
            <div className="bg-gray-50 p-6 rounded-lg">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Deployment Configuration</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Docker Image</label>
                  <input
                    type="text"
                    value={deploymentConfig.docker_image || 'whisperengine-bot:latest'}
                    onChange={(e) => setDeploymentConfig(prev => ({ ...prev, docker_image: e.target.value }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Container Name</label>
                  <input
                    type="text"
                    value={deploymentConfig.container_name || ''}
                    onChange={(e) => setDeploymentConfig(prev => ({ ...prev, container_name: e.target.value }))}
                    placeholder="Auto-generated if empty"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Memory Limit</label>
                  <input
                    type="text"
                    value={deploymentConfig.memory_limit || '512m'}
                    onChange={(e) => setDeploymentConfig(prev => ({ ...prev, memory_limit: e.target.value }))}
                    placeholder="512m"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">CPU Limit</label>
                  <input
                    type="text"
                    value={deploymentConfig.cpu_limit || '0.5'}
                    onChange={(e) => setDeploymentConfig(prev => ({ ...prev, cpu_limit: e.target.value }))}
                    placeholder="0.5"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Health Check Port</label>
                  <input
                    type="number"
                    value={deploymentConfig.health_check_port || ''}
                    onChange={(e) => setDeploymentConfig(prev => ({ ...prev, health_check_port: parseInt(e.target.value) }))}
                    placeholder="Auto-assigned"
                    min="9090"
                    max="9999"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Deployment Status</label>
                  <select
                    value={deploymentConfig.deployment_status || 'inactive'}
                    onChange={(e) => setDeploymentConfig(prev => ({ ...prev, deployment_status: e.target.value as any }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="inactive">Inactive</option>
                    <option value="pending">Pending</option>
                    <option value="active">Active</option>
                    <option value="failed">Failed</option>
                  </select>
                </div>
              </div>

              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Environment Overrides (JSON)</label>
                <textarea
                  value={JSON.stringify(deploymentConfig.env_overrides || {}, null, 2)}
                  onChange={(e) => {
                    try {
                      const parsed = JSON.parse(e.target.value)
                      setDeploymentConfig(prev => ({ ...prev, env_overrides: parsed }))
                    } catch (error) {
                      // Invalid JSON, keep the string for editing
                    }
                  }}
                  rows={6}
                  placeholder='{"CUSTOM_SETTING": "value"}'
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                />
                <p className="text-xs text-gray-500 mt-1">
                  JSON object of environment variables that override default settings
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Save Button */}
      <div className="flex justify-end space-x-4 pt-6 border-t">
        <button
          onClick={handleSave}
          disabled={isLoading}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Saving...' : 'Save Character'}
        </button>
      </div>
    </div>
  )
}