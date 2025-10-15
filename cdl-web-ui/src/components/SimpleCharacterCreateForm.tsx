'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

interface SimpleCharacterData {
  // Basic Identity
  name: string
  occupation: string
  description: string
  location?: string
  character_archetype: 'real-world' | 'fantasy' | 'narrative-ai'
  allow_full_roleplay_immersion: boolean
  
  // Basic Personality (Big Five)
  big_five: {
    openness: number
    conscientiousness: number
    extraversion: number
    agreeableness: number
    neuroticism: number
  }
  
  // Core Values (simple list)
  values: string[]
  
  // LLM Configuration
  llm_config: {
    llm_client_type: string
    llm_chat_api_url: string
    llm_chat_model: string
    llm_chat_api_key: string
    llm_temperature: number
  }
  
  // Discord Configuration
  discord_config: {
    enable_discord: boolean
    discord_bot_token?: string
    discord_status: string
    discord_activity_name: string
  }
}

const defaultCharacterData: SimpleCharacterData = {
  name: '',
  occupation: '',
  description: '',
  location: '',
  character_archetype: 'real-world',
  allow_full_roleplay_immersion: false,
  big_five: {
    openness: 0.7,        // Slightly curious and open to new experiences
    conscientiousness: 0.7, // Reasonably organized and reliable
    extraversion: 0.6,     // Slightly more social than introverted  
    agreeableness: 0.8,    // Friendly and cooperative
    neuroticism: 0.3       // Generally stable and calm
  },
  values: ['helpfulness', 'honesty', 'learning'], // Good starter values
  llm_config: {
    llm_client_type: 'openrouter',
    llm_chat_api_url: 'https://openrouter.ai/api/v1',
    llm_chat_model: 'anthropic/claude-3-haiku',
    llm_chat_api_key: '',
    llm_temperature: 0.7
  },
  discord_config: {
    enable_discord: false,
    discord_status: 'online',
    discord_activity_name: 'conversations'
  }
}

const commonValues = [
  'Honesty', 'Kindness', 'Intelligence', 'Creativity', 'Humor', 'Empathy',
  'Independence', 'Loyalty', 'Justice', 'Adventure', 'Learning', 'Helping Others'
]

export default function SimpleCharacterCreateForm() {
  const [characterData, setCharacterData] = useState<SimpleCharacterData>(defaultCharacterData)
  const [currentStep, setCurrentStep] = useState(1)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [newValue, setNewValue] = useState('')
  const router = useRouter()

  const updateField = (path: string, value: any) => {
    setCharacterData(prev => {
      const newData = { ...prev }
      const keys = path.split('.')
      let current: any = newData
      
      for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) current[keys[i]] = {}
        current = current[keys[i]]
      }
      
      current[keys[keys.length - 1]] = value
      return newData
    })
  }

  const addValue = () => {
    if (newValue.trim() && !characterData.values.includes(newValue.trim())) {
      setCharacterData(prev => ({
        ...prev,
        values: [...prev.values, newValue.trim()]
      }))
      setNewValue('')
    }
  }

  const removeValue = (valueToRemove: string) => {
    setCharacterData(prev => ({
      ...prev,
      values: prev.values.filter(v => v !== valueToRemove)
    }))
  }

  const handleSubmit = async () => {
    setIsSubmitting(true)
    
    try {
      // Create the character
      const characterResponse = await fetch('/api/characters', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: characterData.name,
          occupation: characterData.occupation,
          description: characterData.description,
          character_archetype: characterData.character_archetype,
          allow_full_roleplay_immersion: characterData.allow_full_roleplay_immersion,
          cdl_data: {
            identity: {
              name: characterData.name,
              occupation: characterData.occupation,
              description: characterData.description,
              location: characterData.location || ''
            },
            personality: {
              big_five: characterData.big_five,
              values: characterData.values
            }
          }
        })
      })

      if (!characterResponse.ok) {
        throw new Error('Failed to create character')
      }

      const characterResult = await characterResponse.json()
      const characterId = characterResult.character.id

      // Create the configurations
      await fetch(`/api/characters/${characterId}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          llm_config: characterData.llm_config,
          discord_config: characterData.discord_config,
          deployment_config: {
            docker_image: 'whisperengine-bot:latest',
            memory_limit: '512m',
            cpu_limit: '0.5',
            deployment_status: 'inactive'
          }
        })
      })

      router.push(`/characters/${characterId}?mode=edit`)
    } catch (error) {
      console.error('Error creating character:', error)
      alert('Failed to create character. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const isStepValid = () => {
    switch (currentStep) {
      case 1: return characterData.name.trim() && characterData.occupation.trim()
      case 2: return true // Personality always valid
      case 3: return characterData.llm_config.llm_chat_api_key.trim()
      case 4: return !characterData.discord_config.enable_discord || characterData.discord_config.discord_bot_token?.trim()
      default: return false
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {[1, 2, 3, 4].map((step) => (
            <div key={step} className={`flex items-center ${step < 4 ? 'flex-1' : ''}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                step === currentStep ? 'bg-blue-600 text-white' :
                step < currentStep ? 'bg-green-600 text-white' :
                'bg-gray-300 text-gray-400'
              }`}>
                {step}
              </div>
              {step < 4 && <div className={`flex-1 h-0.5 mx-4 ${step < currentStep ? 'bg-green-600' : 'bg-gray-300'}`} />}
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-2 text-sm text-gray-400">
          <span>Basic Info</span>
          <span>Personality</span>
          <span>LLM Config</span>
          <span>Discord</span>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg shadow p-6">
        {/* Step 1: Basic Information */}
        {currentStep === 1 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold mb-4">Basic Character Information</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-100 mb-2">Character Name *</label>
                <input
                  type="text"
                  value={characterData.name}
                  onChange={(e) => updateField('name', e.target.value)}
                  placeholder="Assistant, Helper, Guide..."
                  className="w-full border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-100 mb-2">Occupation *</label>
                <input
                  type="text"
                  value={characterData.occupation}
                  onChange={(e) => updateField('occupation', e.target.value)}
                  placeholder="Marine Biologist, AI Researcher..."
                  className="w-full border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-100 mb-2">Location</label>
                <input
                  type="text"
                  value={characterData.location}
                  onChange={(e) => updateField('location', e.target.value)}
                  placeholder="San Francisco, London..."
                  className="w-full border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-100 mb-2">Character Type</label>
                <select
                  value={characterData.character_archetype}
                  onChange={(e) => updateField('character_archetype', e.target.value)}
                  className="w-full border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                >
                  <option value="real-world">Real-world (honest about AI)</option>
                  <option value="fantasy">Fantasy (full roleplay)</option>
                  <option value="narrative-ai">Narrative AI (AI is part of story)</option>
                </select>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-100 mb-2">Description</label>
              <textarea
                value={characterData.description}
                onChange={(e) => updateField('description', e.target.value)}
                rows={3}
                placeholder="Brief description of the character's background and personality..."
                className="w-full border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={characterData.allow_full_roleplay_immersion}
                onChange={(e) => updateField('allow_full_roleplay_immersion', e.target.checked)}
                className="mr-2"
              />
              <label className="text-sm font-medium text-gray-100">Allow full roleplay immersion</label>
            </div>
          </div>
        )}

        {/* Step 2: Personality */}
        {currentStep === 2 && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold mb-4">Personality Configuration</h2>
            
            {/* Big Five Traits */}
            <div>
              <h3 className="text-lg font-medium text-gray-100 mb-4">Big Five Personality Traits</h3>
              <div className="space-y-4">
                {Object.entries(characterData.big_five).map(([trait, value]) => (
                  <div key={trait}>
                    <label className="block text-sm font-medium text-gray-100 mb-2 capitalize">
                      {trait} ({Number(value).toFixed(1)})
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={value}
                      onChange={(e) => updateField(`big_five.${trait}`, parseFloat(e.target.value))}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>Low</span>
                      <span>High</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Core Values */}
            <div>
              <h3 className="text-lg font-medium text-gray-100 mb-4">Core Values</h3>
              
              {/* Quick Add Common Values */}
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-100 mb-2">Quick Add</h4>
                <div className="flex flex-wrap gap-2">
                  {commonValues.map((value) => (
                    <button
                      key={value}
                      onClick={() => !characterData.values.includes(value) && updateField('values', [...characterData.values, value])}
                      disabled={characterData.values.includes(value)}
                      className={`px-3 py-1 text-sm rounded ${
                        characterData.values.includes(value)
                          ? 'bg-green-100 text-green-800 cursor-not-allowed'
                          : 'bg-gray-100 hover:bg-gray-200 text-gray-100'
                      }`}
                    >
                      {value} {characterData.values.includes(value) && '✓'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Custom Value Input */}
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  placeholder="Add custom value..."
                  className="flex-1 border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  onKeyPress={(e) => e.key === 'Enter' && addValue()}
                />
                <button
                  onClick={addValue}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Add
                </button>
              </div>

              {/* Selected Values */}
              <div className="flex flex-wrap gap-2">
                {characterData.values.map((value) => (
                  <span key={value} className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded flex items-center">
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

        {/* Step 3: LLM Configuration */}
        {currentStep === 3 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold mb-4">LLM Configuration</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-100 mb-2">Provider</label>
                <select
                  value={characterData.llm_config.llm_client_type}
                  onChange={(e) => {
                    const newProvider = e.target.value;
                    updateField('llm_config.llm_client_type', newProvider);
                    
                    // Auto-populate API URL based on provider
                    const providerUrls: Record<string, string> = {
                      'openai': 'https://api.openai.com/v1',
                      'openrouter': 'https://openrouter.ai/api/v1',
                      'lmstudio': 'http://localhost:1234/v1',
                      'ollama': 'http://localhost:11434/api'
                    };
                    
                    if (providerUrls[newProvider]) {
                      updateField('llm_config.llm_chat_api_url', providerUrls[newProvider]);
                    }
                  }}
                  className="w-full border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                >
                  <option value="openrouter">OpenRouter</option>
                  <option value="openai">OpenAI</option>
                  <option value="lmstudio">LM Studio</option>
                  <option value="ollama">Ollama</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-100 mb-2">Model</label>
                <input
                  type="text"
                  value={characterData.llm_config.llm_chat_model}
                  onChange={(e) => updateField('llm_config.llm_chat_model', e.target.value)}
                  placeholder="e.g., gpt-4, meta-llama/llama-3.1-8b-instruct"
                  className="w-full border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                />
              </div>
              
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-100 mb-2">API URL</label>
                <input
                  type="url"
                  value={characterData.llm_config.llm_chat_api_url}
                  onChange={(e) => updateField('llm_config.llm_chat_api_url', e.target.value)}
                  className="w-full border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                />
              </div>
              
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-100 mb-2">API Key *</label>
                <input
                  type="password"
                  value={characterData.llm_config.llm_chat_api_key}
                  onChange={(e) => updateField('llm_config.llm_chat_api_key', e.target.value)}
                  placeholder="Enter your API key"
                  className="w-full border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-100 mb-2">
                  Temperature ({characterData.llm_config.llm_temperature})
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={characterData.llm_config.llm_temperature}
                  onChange={(e) => updateField('llm_config.llm_temperature', parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Discord Configuration */}
        {currentStep === 4 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold mb-4">Discord Configuration</h2>
            
            <div className="flex items-center mb-4">
              <input
                type="checkbox"
                checked={characterData.discord_config.enable_discord}
                onChange={(e) => updateField('discord_config.enable_discord', e.target.checked)}
                className="mr-2"
              />
              <label className="text-sm font-medium text-gray-100">Enable Discord Integration</label>
            </div>

            {characterData.discord_config.enable_discord && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-100 mb-2">Discord Bot Token *</label>
                  <input
                    type="password"
                    value={characterData.discord_config.discord_bot_token || ''}
                    onChange={(e) => updateField('discord_config.discord_bot_token', e.target.value)}
                    placeholder="Enter Discord bot token"
                    className="w-full border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-100 mb-2">Status</label>
                  <select
                    value={characterData.discord_config.discord_status}
                    onChange={(e) => updateField('discord_config.discord_status', e.target.value)}
                    className="w-full border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                  >
                    <option value="online">Online</option>
                    <option value="idle">Idle</option>
                    <option value="dnd">Do Not Disturb</option>
                    <option value="invisible">Invisible</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-100 mb-2">Activity Name</label>
                  <input
                    type="text"
                    value={characterData.discord_config.discord_activity_name}
                    onChange={(e) => updateField('discord_config.discord_activity_name', e.target.value)}
                    placeholder="conversations"
                    className="w-full border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-100"
                  />
                </div>
              </div>
            )}

            {!characterData.discord_config.enable_discord && (
              <div className="bg-gray-900 p-4 rounded-lg">
                <p className="text-sm text-gray-400">
                  Discord integration is disabled. This character will only be accessible via API endpoints.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between pt-6 border-t">
          <button
            onClick={() => setCurrentStep(prev => prev - 1)}
            disabled={currentStep === 1}
            className="px-4 py-2 text-gray-400 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          
          {currentStep < 4 ? (
            <button
              onClick={() => setCurrentStep(prev => prev + 1)}
              disabled={!isStepValid()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!isStepValid() || isSubmitting}
              className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Creating...' : 'Create Character'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}