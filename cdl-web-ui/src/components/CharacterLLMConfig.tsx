'use client'

import { useState, useEffect } from 'react'
import { Character, CharacterLLMConfig as LLMConfigType } from '@/types/cdl'

interface CharacterLLMConfigProps {
  character: Character
}

const llmProviders = [
  { id: 'openrouter', name: 'OpenRouter', url: 'https://openrouter.ai/api/v1' },
  { id: 'openai', name: 'OpenAI', url: 'https://api.openai.com/v1' },
  { id: 'anthropic', name: 'Anthropic', url: 'https://api.anthropic.com' },
  { id: 'ollama', name: 'Ollama (Local)', url: 'http://localhost:11434' }
]

const commonModels = {
  openrouter: [
    'anthropic/claude-3-haiku',
    'anthropic/claude-3-sonnet',
    'anthropic/claude-3-opus',
    'openai/gpt-4o',
    'openai/gpt-4o-mini'
  ],
  openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'],
  anthropic: ['claude-3-haiku-20240307', 'claude-3-sonnet-20240229', 'claude-3-opus-20240229'],
  ollama: ['llama3.1', 'mistral', 'codellama']
}

export default function CharacterLLMConfig({ character }: CharacterLLMConfigProps) {
  const [config, setConfig] = useState<Partial<LLMConfigType>>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadConfig()
  }, [character.id])

  const loadConfig = async () => {
    try {
      const response = await fetch(`/api/characters/${character.id}/config`)
      if (response.ok) {
        const data = await response.json()
        setConfig(data.llm_config || {})
      }
    } catch (error) {
      console.error('Error loading LLM config:', error)
    } finally {
      setLoading(false)
    }
  }

  const saveConfig = async () => {
    setSaving(true)
    try {
      const response = await fetch(`/api/characters/${character.id}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ llm_config: config })
      })
      
      if (response.ok) {
        alert('LLM configuration saved successfully!')
        loadConfig() // Reload to get updated data
      } else {
        throw new Error('Failed to save configuration')
      }
    } catch (error) {
      console.error('Error saving LLM config:', error)
      alert('Failed to save LLM configuration')
    } finally {
      setSaving(false)
    }
  }

  const updateField = (field: string, value: any) => {
    setConfig(prev => ({ ...prev, [field]: value }))
  }

  if (loading) {
    return <div className="text-center py-8">Loading LLM configuration...</div>
  }

  return (
    <div className="space-y-6">
      {/* Configuration Note */}
      <div className="bg-gray-800 border border-blue-200 rounded-md p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Configuration Note</h3>
            <div className="mt-1 text-sm text-blue-700">
              These settings are saved to the database but currently <strong>.env files are used for actual LLM configuration</strong>. 
              Database integration for runtime configuration is coming soon.
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Provider Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-100 mb-2">
            LLM Provider
          </label>
          <select
            value={config.llm_client_type || 'openrouter'}
            onChange={(e) => {
              const provider = e.target.value
              updateField('llm_client_type', provider)
              updateField('llm_chat_api_url', llmProviders.find(p => p.id === provider)?.url || '')
            }}
            className="w-full bg-gray-800 border border-gray-600 text-gray-100 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {llmProviders.map(provider => (
              <option key={provider.id} value={provider.id}>
                {provider.name}
              </option>
            ))}
          </select>
        </div>

        {/* API URL */}
        <div>
          <label className="block text-sm font-medium text-gray-100 mb-2">
            API URL
          </label>
          <input
            type="url"
            value={config.llm_chat_api_url || ''}
            onChange={(e) => updateField('llm_chat_api_url', e.target.value)}
            className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="https://api.provider.com/v1"
          />
        </div>

        {/* Model Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-100 mb-2">
            Model
          </label>
          <select
            value={config.llm_chat_model || ''}
            onChange={(e) => updateField('llm_chat_model', e.target.value)}
            className="w-full bg-gray-800 border border-gray-600 text-gray-100 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select a model...</option>
            {(commonModels[config.llm_client_type as keyof typeof commonModels] || []).map(model => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </div>

        {/* API Key */}
        <div>
          <label className="block text-sm font-medium text-gray-100 mb-2">
            API Key
          </label>
          <input
            type="password"
            value={config.llm_chat_api_key || ''}
            onChange={(e) => updateField('llm_chat_api_key', e.target.value)}
            className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="sk-..."
          />
        </div>
      </div>

      {/* Advanced Settings */}
      <div className="border-t pt-6">
        <h3 className="text-lg font-medium text-gray-100 mb-4">Advanced Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-100 mb-2">
              Temperature ({config.llm_temperature || 0.7})
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={config.llm_temperature || 0.7}
              onChange={(e) => updateField('llm_temperature', parseFloat(e.target.value))}
              className="w-full"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-100 mb-2">
              Max Tokens
            </label>
            <input
              type="number"
              value={config.llm_max_tokens || 4000}
              onChange={(e) => updateField('llm_max_tokens', parseInt(e.target.value))}
              className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-100 mb-2">
              Top P
            </label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={config.llm_top_p || 0.9}
              onChange={(e) => updateField('llm_top_p', parseFloat(e.target.value))}
              className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end pt-6 border-t">
        <button
          onClick={saveConfig}
          disabled={saving}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save LLM Configuration'}
        </button>
      </div>
    </div>
  )
}