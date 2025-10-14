'use client'

import { useState, useEffect } from 'react'
import { Character, CharacterLLMConfig, CharacterDiscordConfig, CharacterDeploymentConfig } from '@/types/cdl'
import DeploymentManager from './DeploymentManager'

interface SimpleCharacterEditFormProps {
  character: Character
}

export default function SimpleCharacterEditForm({ character }: SimpleCharacterEditFormProps) {
  const [activeTab, setActiveTab] = useState('basic')
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  
  // Basic character data
  const [basicData, setBasicData] = useState({
    name: character.name,
    occupation: character.occupation || '',
    description: character.description || '',
    location: character.location || '',
    character_archetype: character.character_archetype,
    allow_full_roleplay_immersion: character.allow_full_roleplay_immersion
  })

  // Personality data
  const [personalityData, setPersonalityData] = useState({
    big_five: {
      openness: 0.5,
      conscientiousness: 0.5,
      extraversion: 0.5,
      agreeableness: 0.5,
      neuroticism: 0.5
    },
    values: [] as string[]
  })

  // Configuration states
  const [llmConfig, setLlmConfig] = useState<Partial<CharacterLLMConfig>>({})
  const [discordConfig, setDiscordConfig] = useState<Partial<CharacterDiscordConfig>>({})
  const [deploymentConfig, setDeploymentConfig] = useState<Partial<CharacterDeploymentConfig>>({})
  
  const [newValue, setNewValue] = useState('')

  useEffect(() => {
    loadCharacterData()
    loadCharacterConfigs()
  }, [character.id])

  // Update basicData when character prop changes
  useEffect(() => {
    setBasicData({
      name: character.name,
      occupation: character.occupation || '',
      description: character.description || '',
      location: character.location || '',
      character_archetype: character.character_archetype,
      allow_full_roleplay_immersion: character.allow_full_roleplay_immersion
    })
  }, [character])

  const loadCharacterData = () => {
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
  }

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
            llm_max_tokens: 4000
          })
          setDiscordConfig(data.discord_config || {
            enable_discord: false,
            discord_status: 'online',
            discord_activity_name: 'conversations'
          })
          setDeploymentConfig(data.deployment_config || {
            docker_image: 'whisperengine-bot:latest',
            memory_limit: '512m',
            cpu_limit: '0.5',
            deployment_status: 'inactive'
          })
        }
      }
    } catch (error) {
      console.error('Failed to load character configurations:', error)
    }
  }

  const handleSave = async () => {
    setSaveStatus('saving')
    
    try {
      // Save character basic data and personality
      const characterResponse = await fetch(`/api/characters/${character.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...basicData,
          cdl_data: {
            identity: {
              name: basicData.name,
              occupation: basicData.occupation,
              description: basicData.description,
              location: basicData.location
            },
            personality: personalityData
          }
        })
      })

      // Save configurations
      const configResponse = await fetch(`/api/characters/${character.id}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
      values: prev.values.filter(v => v !== valueToRemove)
    }))
  }

  const tabs = [
    { id: 'basic', name: 'Basic Info' },
    { id: 'personality', name: 'Personality' },
    { id: 'llm', name: 'LLM Config' },
    { id: 'discord', name: 'Discord' },
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
          {saveStatus === 'saving' && 'Saving character...'}
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
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
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
      <div className="bg-white rounded-lg shadow p-6">
        {/* Basic Info Tab */}
        {activeTab === 'basic' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">Name</label>
                <input
                  type="text"
                  value={basicData.name}
                  onChange={(e) => setBasicData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">Occupation</label>
                <input
                  type="text"
                  value={basicData.occupation}
                  onChange={(e) => setBasicData(prev => ({ ...prev, occupation: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">Location</label>
                <input
                  type="text"
                  value={basicData.location}
                  onChange={(e) => setBasicData(prev => ({ ...prev, location: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">Character Type</label>
                <select
                  value={basicData.character_archetype}
                  onChange={(e) => setBasicData(prev => ({ ...prev, character_archetype: e.target.value as 'real-world' | 'fantasy' | 'narrative-ai' }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                >
                  <option value="real-world">Real-world</option>
                  <option value="fantasy">Fantasy</option>
                  <option value="narrative-ai">Narrative AI</option>
                </select>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">Description</label>
              <textarea
                value={basicData.description}
                onChange={(e) => setBasicData(prev => ({ ...prev, description: e.target.value }))}
                rows={4}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={basicData.allow_full_roleplay_immersion}
                onChange={(e) => setBasicData(prev => ({ ...prev, allow_full_roleplay_immersion: e.target.checked }))}
                className="mr-2"
              />
              <label className="text-sm font-medium text-gray-900">Allow full roleplay immersion</label>
            </div>
          </div>
        )}

        {/* Personality Tab */}
        {activeTab === 'personality' && (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Personality Configuration</h3>
            
            {/* Big Five Traits */}
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-4">Big Five Personality Traits</h4>
              <div className="space-y-4">
                {Object.entries(personalityData.big_five).map(([trait, value]) => (
                  <div key={trait}>
                    <label className="block text-sm font-medium text-gray-900 mb-2 capitalize">
                      {trait} ({Number(value).toFixed(1)})
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={value}
                      onChange={(e) => setPersonalityData(prev => ({
                        ...prev,
                        big_five: { ...prev.big_five, [trait]: parseFloat(e.target.value) }
                      }))}
                      className="w-full"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Core Values */}
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-4">Core Values</h4>
              
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  placeholder="Add new value..."
                  className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  onKeyPress={(e) => e.key === 'Enter' && addValue()}
                />
                <button
                  onClick={addValue}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Add
                </button>
              </div>

              <div className="flex flex-wrap gap-2">
                {personalityData.values.map((value) => (
                  <span key={value} className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded flex items-center">
                    {value}
                    <button
                      onClick={() => removeValue(value)}
                      className="ml-2 text-blue-600 hover:text-blue-800"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* LLM Config Tab */}
        {activeTab === 'llm' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">LLM Configuration</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">Provider</label>
                <select
                  value={llmConfig.llm_client_type || 'openrouter'}
                  onChange={(e) => {
                    const newProvider = e.target.value;
                    setLlmConfig(prev => ({ ...prev, llm_client_type: newProvider }));
                    
                    // Auto-populate API URL based on provider
                    const providerUrls: Record<string, string> = {
                      'openai': 'https://api.openai.com/v1',
                      'openrouter': 'https://openrouter.ai/api/v1',
                      'lmstudio': 'http://localhost:1234/v1',
                      'ollama': 'http://localhost:11434/api'
                    };
                    
                    if (providerUrls[newProvider]) {
                      setLlmConfig(prev => ({ ...prev, llm_chat_api_url: providerUrls[newProvider] }));
                    }
                  }}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                >
                  <option value="openrouter">OpenRouter</option>
                  <option value="openai">OpenAI</option>
                  <option value="lmstudio">LM Studio</option>
                  <option value="ollama">Ollama</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">Model</label>
                <input
                  type="text"
                  value={llmConfig.llm_chat_model || ''}
                  onChange={(e) => setLlmConfig(prev => ({ ...prev, llm_chat_model: e.target.value }))}
                  placeholder="e.g., gpt-4, meta-llama/llama-3.1-8b-instruct"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                />
              </div>
              
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-900 mb-2">API URL</label>
                <input
                  type="url"
                  value={llmConfig.llm_chat_api_url || ''}
                  onChange={(e) => setLlmConfig(prev => ({ ...prev, llm_chat_api_url: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                />
              </div>
              
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-900 mb-2">API Key</label>
                <input
                  type="password"
                  value={llmConfig.llm_chat_api_key || ''}
                  onChange={(e) => setLlmConfig(prev => ({ ...prev, llm_chat_api_key: e.target.value }))}
                  placeholder="Enter API key"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
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
            </div>
          </div>
        )}

        {/* Discord Config Tab */}
        {activeTab === 'discord' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Discord Configuration</h3>
            
            <div className="flex items-center mb-4">
              <input
                type="checkbox"
                checked={discordConfig.enable_discord || false}
                onChange={(e) => setDiscordConfig(prev => ({ ...prev, enable_discord: e.target.checked }))}
                className="mr-2"
              />
              <label className="text-sm font-medium text-gray-900">Enable Discord Integration</label>
            </div>

            {discordConfig.enable_discord && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-900 mb-2">Discord Bot Token</label>
                  <input
                    type="password"
                    value={discordConfig.discord_bot_token || ''}
                    onChange={(e) => setDiscordConfig(prev => ({ ...prev, discord_bot_token: e.target.value }))}
                    placeholder="Enter Discord bot token"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">Status</label>
                  <select
                    value={discordConfig.discord_status || 'online'}
                    onChange={(e) => setDiscordConfig(prev => ({ ...prev, discord_status: e.target.value as 'online' | 'idle' | 'dnd' | 'invisible' }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  >
                    <option value="online">Online</option>
                    <option value="idle">Idle</option>
                    <option value="dnd">Do Not Disturb</option>
                    <option value="invisible">Invisible</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">Activity Name</label>
                  <input
                    type="text"
                    value={discordConfig.discord_activity_name || ''}
                    onChange={(e) => setDiscordConfig(prev => ({ ...prev, discord_activity_name: e.target.value }))}
                    placeholder="conversations"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Deployment Config Tab */}
        {activeTab === 'deployment' && (
          <div className="space-y-6">
            {/* Deployment Management */}
            <DeploymentManager character={character} />
            
            {/* Advanced Deployment Configuration */}
            <div className="bg-gray-50 rounded-lg p-6">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Advanced Configuration</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">Docker Image</label>
                  <input
                    type="text"
                    value={deploymentConfig.docker_image || 'whisperengine-bot:latest'}
                    onChange={(e) => setDeploymentConfig(prev => ({ ...prev, docker_image: e.target.value }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  />
                  <p className="text-xs text-gray-500 mt-1">Container image to use for deployment</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">Memory Limit</label>
                  <input
                    type="text"
                    value={deploymentConfig.memory_limit || '2G'}
                    onChange={(e) => setDeploymentConfig(prev => ({ ...prev, memory_limit: e.target.value }))}
                    placeholder="2G"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  />
                  <p className="text-xs text-gray-500 mt-1">Memory allocation (e.g., 2G, 512M)</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">CPU Limit</label>
                  <input
                    type="text"
                    value={deploymentConfig.cpu_limit || '2.0'}
                    onChange={(e) => setDeploymentConfig(prev => ({ ...prev, cpu_limit: e.target.value }))}
                    placeholder="2.0"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  />
                  <p className="text-xs text-gray-500 mt-1">CPU cores (e.g., 2.0, 0.5)</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">Auto-Start</label>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={deploymentConfig.auto_start || false}
                      onChange={(e) => setDeploymentConfig(prev => ({ ...prev, auto_start: e.target.checked }))}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="text-sm text-gray-700">Start automatically on platform startup</span>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Enabled</label>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={deploymentConfig.enabled !== false}
                      onChange={(e) => setDeploymentConfig(prev => ({ ...prev, enabled: e.target.checked }))}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="text-sm text-gray-700">Enable deployment for this character</span>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">Port (Optional)</label>
                  <input
                    type="number"
                    value={deploymentConfig.port || ''}
                    onChange={(e) => setDeploymentConfig(prev => ({ ...prev, port: e.target.value ? parseInt(e.target.value) : undefined }))}
                    placeholder="Auto-assigned"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  />
                  <p className="text-xs text-gray-500 mt-1">Leave empty for auto-assignment</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Save Button */}
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