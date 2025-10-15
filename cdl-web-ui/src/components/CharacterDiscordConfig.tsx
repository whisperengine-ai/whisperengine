'use client'

import { useState, useEffect } from 'react'
import { Character, CharacterDiscordConfig as DiscordConfigType } from '@/types/cdl'

interface CharacterDiscordConfigProps {
  character: Character
}

export default function CharacterDiscordConfig({ character }: CharacterDiscordConfigProps) {
  const [config, setConfig] = useState<Partial<DiscordConfigType>>({})
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
        setConfig(data.discord_config || {})
      }
    } catch (error) {
      console.error('Error loading Discord config:', error)
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
        body: JSON.stringify({ discord_config: config })
      })
      
      if (response.ok) {
        alert('Discord configuration saved successfully!')
        loadConfig() // Reload to get updated data
      } else {
        throw new Error('Failed to save configuration')
      }
    } catch (error) {
      console.error('Error saving Discord config:', error)
      alert('Failed to save Discord configuration')
    } finally {
      setSaving(false)
    }
  }

  const updateField = (field: string, value: any) => {
    setConfig(prev => ({ ...prev, [field]: value }))
  }

  if (loading) {
    return <div className="text-center py-8">Loading Discord configuration...</div>
  }

  return (
    <div className="space-y-6">
      {/* Discord Bot Token */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <span className="text-yellow-600">⚠️</span>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800">
              Discord Bot Setup Required
            </h3>
            <p className="mt-1 text-sm text-yellow-700">
              You'll need to create a Discord bot application and get a bot token. 
              Visit <a href="https://discord.com/developers/applications" target="_blank" rel="noopener noreferrer" className="underline">Discord Developer Portal</a> to get started.
            </p>
          </div>
        </div>
      </div>

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
              These settings are saved to the database but currently <strong>.env files are used for actual Discord configuration</strong>. 
              Database integration for runtime configuration is coming soon.
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Enable Discord */}
        <div className="lg:col-span-2">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={config.enable_discord || false}
              onChange={(e) => updateField('enable_discord', e.target.checked)}
              className="rounded border-gray-600 text-blue-400 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm font-medium text-gray-100">
              Enable Discord Integration
            </span>
          </label>
        </div>

        {/* Bot Token */}
        <div className="lg:col-span-2">
          <label className="block text-sm font-medium text-gray-100 mb-2">
            Discord Bot Token
          </label>
          <input
            type="password"
            value={config.discord_bot_token || ''}
            onChange={(e) => updateField('discord_bot_token', e.target.value)}
            className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Your Discord bot token..."
            disabled={!config.enable_discord}
          />
        </div>

        {/* Application ID */}
        <div>
          <label className="block text-sm font-medium text-gray-100 mb-2">
            Application ID (Optional)
          </label>
          <input
            type="text"
            value={config.discord_application_id || ''}
            onChange={(e) => updateField('discord_application_id', e.target.value)}
            className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="1234567890123456789"
            disabled={!config.enable_discord}
          />
        </div>

        {/* Guild ID */}
        <div>
          <label className="block text-sm font-medium text-gray-100 mb-2">
            Guild ID (Optional)
          </label>
          <input
            type="text"
            value={config.discord_guild_id || ''}
            onChange={(e) => updateField('discord_guild_id', e.target.value)}
            className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="1234567890123456789"
            disabled={!config.enable_discord}
          />
        </div>

        {/* Bot Status */}
        <div>
          <label className="block text-sm font-medium text-gray-100 mb-2">
            Bot Status
          </label>
          <select
            value={config.discord_status || 'online'}
            onChange={(e) => updateField('discord_status', e.target.value)}
            className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={!config.enable_discord}
          >
            <option value="online">Online</option>
            <option value="idle">Idle</option>
            <option value="dnd">Do Not Disturb</option>
            <option value="invisible">Invisible</option>
          </select>
        </div>

        {/* Activity Type */}
        <div>
          <label className="block text-sm font-medium text-gray-100 mb-2">
            Activity Type
          </label>
          <select
            value={config.discord_activity_type || 'playing'}
            onChange={(e) => updateField('discord_activity_type', e.target.value)}
            className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={!config.enable_discord}
          >
            <option value="playing">Playing</option>
            <option value="streaming">Streaming</option>
            <option value="listening">Listening to</option>
            <option value="watching">Watching</option>
          </select>
        </div>
      </div>

      {/* Advanced Settings */}
      <div className="border-t pt-6">
        <h3 className="text-lg font-medium text-gray-100 mb-4">Bot Behavior</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-100 mb-2">
              Max Message Length
            </label>
            <input
              type="number"
              value={config.max_message_length || 2000}
              onChange={(e) => updateField('max_message_length', parseInt(e.target.value))}
              className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              min="1"
              max="2000"
              disabled={!config.enable_discord}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-100 mb-2">
              Typing Delay (seconds)
            </label>
            <input
              type="number"
              step="0.1"
              value={config.typing_delay_seconds || 2.0}
              onChange={(e) => updateField('typing_delay_seconds', parseFloat(e.target.value))}
              className="w-full bg-gray-800 border border-gray-600 text-gray-100 placeholder-gray-400 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              min="0"
              max="10"
              disabled={!config.enable_discord}
            />
          </div>

          <div className="flex flex-col space-y-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.enable_reactions || true}
                onChange={(e) => updateField('enable_reactions', e.target.checked)}
                className="rounded border-gray-600 text-blue-400 focus:ring-blue-500"
                disabled={!config.enable_discord}
              />
              <span className="ml-2 text-sm text-gray-100">Enable Reactions</span>
            </label>
            
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.enable_typing_indicator || true}
                onChange={(e) => updateField('enable_typing_indicator', e.target.checked)}
                className="rounded border-gray-600 text-blue-400 focus:ring-blue-500"
                disabled={!config.enable_discord}
              />
              <span className="ml-2 text-sm text-gray-100">Show Typing Indicator</span>
            </label>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end pt-6 border-t">
        <button
          onClick={saveConfig}
          disabled={saving || !config.enable_discord}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Discord Configuration'}
        </button>
      </div>
    </div>
  )
}