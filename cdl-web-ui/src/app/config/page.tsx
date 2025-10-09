'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface SystemConfig {
  // LLM Configuration
  llm_client_type: string
  llm_chat_api_url: string
  llm_chat_model: string
  llm_chat_api_key: string
  
  // Discord Configuration (optional)
  discord_bot_token: string
  enable_discord: boolean
  
  // Memory Configuration
  memory_system_type: string
  enable_character_intelligence: boolean
  enable_emotional_intelligence: boolean
  
  // Database Configuration
  postgres_host: string
  postgres_port: string
  postgres_user: string
  postgres_password: string
  postgres_db: string
  
  // Vector Database Configuration
  qdrant_host: string
  qdrant_port: string
}

const defaultConfig: SystemConfig = {
  llm_client_type: 'openrouter',
  llm_chat_api_url: 'https://openrouter.ai/api/v1',
  llm_chat_model: 'anthropic/claude-3-haiku',
  llm_chat_api_key: '',
  discord_bot_token: '',
  enable_discord: false,
  memory_system_type: 'vector',
  enable_character_intelligence: true,
  enable_emotional_intelligence: true,
  postgres_host: 'postgres',
  postgres_port: '5432',
  postgres_user: 'whisperengine',
  postgres_password: 'whisperengine_password',
  postgres_db: 'whisperengine',
  qdrant_host: 'qdrant',
  qdrant_port: '6333'
}

const llmProviders = [
  { id: 'openrouter', name: 'OpenRouter', url: 'https://openrouter.ai/api/v1', models: [
    'anthropic/claude-3-haiku',
    'anthropic/claude-3-sonnet', 
    'anthropic/claude-3-opus',
    'openai/gpt-4o',
    'openai/gpt-4o-mini',
    'openai/gpt-3.5-turbo',
    'mistralai/mistral-7b-instruct',
    'mistralai/mistral-medium',
    'mistralai/mistral-large'
  ]},
  { id: 'openai', name: 'OpenAI Direct', url: 'https://api.openai.com/v1', models: [
    'gpt-4o',
    'gpt-4o-mini',
    'gpt-4-turbo',
    'gpt-3.5-turbo'
  ]},
  { id: 'lmstudio', name: 'LM Studio (Local)', url: 'http://localhost:1234/v1', models: [
    'local-model'
  ]},
  { id: 'ollama', name: 'Ollama (Local)', url: 'http://localhost:11434/v1', models: [
    'llama2',
    'mistral',
    'codellama'
  ]}
]

export default function ConfigPage() {
  const [config, setConfig] = useState<SystemConfig>(defaultConfig)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)
  const [showAdvanced, setShowAdvanced] = useState(false)

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const response = await fetch('/api/config')
      if (response.ok) {
        const data = await response.json()
        setConfig({...defaultConfig, ...data})
      }
    } catch (error) {
      console.error('Failed to load config:', error)
      setMessage({type: 'error', text: 'Failed to load configuration'})
    } finally {
      setLoading(false)
    }
  }

  const saveConfig = async () => {
    setSaving(true)
    try {
      const response = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      })
      
      if (response.ok) {
        setMessage({type: 'success', text: 'Configuration saved successfully!'})
        setTimeout(() => setMessage(null), 3000)
      } else {
        const error = await response.json()
        setMessage({type: 'error', text: error.message || 'Failed to save configuration'})
      }
    } catch (error) {
      setMessage({type: 'error', text: 'Failed to save configuration'})
    } finally {
      setSaving(false)
    }
  }

  const handleProviderChange = (providerId: string) => {
    const provider = llmProviders.find(p => p.id === providerId)
    if (provider) {
      setConfig({
        ...config,
        llm_client_type: providerId,
        llm_chat_api_url: provider.url,
        llm_chat_model: provider.models[0]
      })
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading configuration...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-8">
            <Link href="/" className="text-xl font-bold text-blue-600">
              CDL Authoring Tool
            </Link>
            <div className="flex space-x-6">
              <Link href="/characters" className="text-gray-600 hover:text-blue-600">
                Characters
              </Link>
              <Link href="/config" className="text-blue-600 font-medium">
                Configuration
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">System Configuration</h1>
          <p className="text-gray-600">Configure LLM providers, Discord integration, and system settings.</p>
        </div>

        {/* Message */}
        {message && (
          <div className={`mb-6 p-4 rounded-lg ${
            message.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 
            'bg-red-50 text-red-800 border border-red-200'
          }`}>
            {message.text}
          </div>
        )}

        <div className="space-y-8">
          {/* LLM Configuration */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">🤖 LLM Provider Configuration</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  LLM Provider
                </label>
                <select
                  value={config.llm_client_type}
                  onChange={(e) => handleProviderChange(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {llmProviders.map(provider => (
                    <option key={provider.id} value={provider.id}>
                      {provider.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Endpoint
                </label>
                <input
                  type="url"
                  value={config.llm_chat_api_url}
                  onChange={(e) => setConfig({...config, llm_chat_api_url: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="https://api.openai.com/v1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Model
                </label>
                <select
                  value={config.llm_chat_model}
                  onChange={(e) => setConfig({...config, llm_chat_model: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {llmProviders.find(p => p.id === config.llm_client_type)?.models.map(model => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Key
                  <span className="text-red-500 ml-1">*</span>
                </label>
                <input
                  type="password"
                  value={config.llm_chat_api_key}
                  onChange={(e) => setConfig({...config, llm_chat_api_key: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Your API key (required)"
                />
                <p className="text-sm text-gray-600 mt-1">
                  Required for AI character functionality
                </p>
              </div>
            </div>
          </div>

          {/* Discord Configuration */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">💬 Discord Integration (Optional)</h2>
            
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="enable_discord"
                  checked={config.enable_discord}
                  onChange={(e) => setConfig({...config, enable_discord: e.target.checked})}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="enable_discord" className="text-sm font-medium text-gray-700">
                  Enable Discord Bot Integration
                </label>
              </div>

              {config.enable_discord && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Discord Bot Token
                  </label>
                  <input
                    type="password"
                    value={config.discord_bot_token}
                    onChange={(e) => setConfig({...config, discord_bot_token: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Your Discord bot token"
                  />
                  <p className="text-sm text-gray-600 mt-1">
                    Get this from the Discord Developer Portal
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Advanced Settings */}
          <div className="bg-white rounded-lg shadow p-6">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center space-x-2 text-gray-700 hover:text-gray-900 mb-4"
            >
              <span className="text-xl font-semibold">⚙️ Advanced Settings</span>
              <span className={`transform transition-transform ${showAdvanced ? 'rotate-180' : ''}`}>
                ▼
              </span>
            </button>

            {showAdvanced && (
              <div className="space-y-4 border-t pt-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Memory System Type
                    </label>
                    <select
                      value={config.memory_system_type}
                      onChange={(e) => setConfig({...config, memory_system_type: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="vector">Vector (Recommended)</option>
                      <option value="hierarchical">Hierarchical</option>
                      <option value="test_mock">Test Mock</option>
                    </select>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        id="enable_character_intelligence"
                        checked={config.enable_character_intelligence}
                        onChange={(e) => setConfig({...config, enable_character_intelligence: e.target.checked})}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <label htmlFor="enable_character_intelligence" className="text-sm font-medium text-gray-700">
                        Character Intelligence
                      </label>
                    </div>

                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        id="enable_emotional_intelligence"
                        checked={config.enable_emotional_intelligence}
                        onChange={(e) => setConfig({...config, enable_emotional_intelligence: e.target.checked})}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <label htmlFor="enable_emotional_intelligence" className="text-sm font-medium text-gray-700">
                        Emotional Intelligence
                      </label>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      PostgreSQL Host
                    </label>
                    <input
                      type="text"
                      value={config.postgres_host}
                      onChange={(e) => setConfig({...config, postgres_host: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      PostgreSQL Port
                    </label>
                    <input
                      type="text"
                      value={config.postgres_port}
                      onChange={(e) => setConfig({...config, postgres_port: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Qdrant Host
                    </label>
                    <input
                      type="text"
                      value={config.qdrant_host}
                      onChange={(e) => setConfig({...config, qdrant_host: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Qdrant Port
                    </label>
                    <input
                      type="text"
                      value={config.qdrant_port}
                      onChange={(e) => setConfig({...config, qdrant_port: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Save Button */}
          <div className="flex justify-between items-center">
            <Link 
              href="/" 
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              ← Back to Home
            </Link>
            
            <button
              onClick={saveConfig}
              disabled={saving || !config.llm_chat_api_key.trim()}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : 'Save Configuration'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}