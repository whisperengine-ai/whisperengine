'use client'

import { Character, CharacterLLMConfig, CharacterDiscordConfig, CharacterDeploymentConfig } from '@/types/cdl'
import { useState, useEffect } from 'react'

interface CharacterViewProps {
  character: Character
}

export default function CharacterView({ character }: CharacterViewProps) {
  const [llmConfig, setLlmConfig] = useState<CharacterLLMConfig | null>(null)
  const [discordConfig, setDiscordConfig] = useState<CharacterDiscordConfig | null>(null)
  const [deploymentConfig, setDeploymentConfig] = useState<CharacterDeploymentConfig | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadConfigurations()
  }, [character.id])

  const loadConfigurations = async () => {
    try {
      const response = await fetch(`/api/characters/${character.id}/config`)
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setLlmConfig(data.llm_config)
          setDiscordConfig(data.discord_config)
          setDeploymentConfig(data.deployment_config)
        }
      }
    } catch (error) {
      console.error('Failed to load configurations:', error)
    } finally {
      setLoading(false)
    }
  }

  const InfoSection = ({ title, children }: { title: string; children: React.ReactNode }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">{title}</h3>
      {children}
    </div>
  )

  const InfoRow = ({ label, value }: { label: string; value: string | number | boolean | null | undefined }) => (
    <div className="flex justify-between py-2 border-b border-gray-100 last:border-b-0">
      <span className="text-sm font-medium text-gray-500">{label}</span>
      <span className="text-sm text-gray-900">
        {value === null || value === undefined ? 'Not set' : 
         typeof value === 'boolean' ? (value ? 'Yes' : 'No') : 
         String(value)}
      </span>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Character Overview */}
      <InfoSection title="Character Overview">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <InfoRow label="Name" value={character.name} />
            <InfoRow label="Occupation" value={character.occupation} />
            <InfoRow label="Location" value={character.location} />
            <InfoRow label="Archetype" value={character.character_archetype} />
            <InfoRow label="Full Roleplay" value={character.allow_full_roleplay_immersion} />
          </div>
          <div>
            <InfoRow label="Bot Name" value={character.bot_name} />
            <InfoRow label="Status" value={character.is_active ? 'Active' : 'Inactive'} />
            <InfoRow label="Created" value={new Date(character.created_at).toLocaleDateString()} />
            <InfoRow label="Updated" value={new Date(character.updated_at).toLocaleDateString()} />
          </div>
        </div>
        
        {character.description && (
          <div className="mt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Description</h4>
            <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded">{character.description}</p>
          </div>
        )}
      </InfoSection>

      {/* Personality Overview */}
      {character.cdl_data && (
        <InfoSection title="Personality">
          <div className="space-y-4">
            {/* Big Five if available */}
            {(character.cdl_data as any)?.personality?.big_five && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Big Five Traits</h4>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                  {Object.entries((character.cdl_data as any).personality.big_five).map(([trait, value]) => (
                    <div key={trait} className="text-center">
                      <div className="text-xs text-gray-500 capitalize">{trait}</div>
                      <div className="text-sm font-medium">{Number(value).toFixed(1)}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Values */}
            {(character.cdl_data as any)?.personality?.values && Array.isArray((character.cdl_data as any).personality.values) && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Core Values</h4>
                <div className="flex flex-wrap gap-2">
                  {(character.cdl_data as any).personality.values.map((value: string, index: number) => (
                    <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                      {value}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </InfoSection>
      )}

      {/* LLM Configuration */}
      {!loading && (
        <InfoSection title="LLM Configuration">
          {llmConfig ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <InfoRow label="Provider" value={llmConfig.llm_client_type} />
              <InfoRow label="Model" value={llmConfig.llm_chat_model} />
              <InfoRow label="API URL" value={llmConfig.llm_chat_api_url} />
              <InfoRow label="Temperature" value={llmConfig.llm_temperature} />
              <InfoRow label="Max Tokens" value={llmConfig.llm_max_tokens} />
              <InfoRow label="API Key" value={llmConfig.llm_chat_api_key ? '••••••••' : 'Not set'} />
            </div>
          ) : (
            <p className="text-sm text-gray-500 italic">No LLM configuration set</p>
          )}
        </InfoSection>
      )}

      {/* Discord Configuration */}
      {!loading && (
        <InfoSection title="Discord Configuration">
          {discordConfig ? (
            <div>
              <InfoRow label="Discord Enabled" value={discordConfig.enable_discord} />
              {discordConfig.enable_discord && (
                <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                  <InfoRow label="Bot Token" value={discordConfig.discord_bot_token ? '••••••••' : 'Not set'} />
                  <InfoRow label="Application ID" value={discordConfig.discord_application_id} />
                  <InfoRow label="Status" value={discordConfig.discord_status} />
                  <InfoRow label="Activity" value={`${discordConfig.discord_activity_type} ${discordConfig.discord_activity_name}`} />
                  <InfoRow label="Response Delay" value={`${discordConfig.response_delay_min}-${discordConfig.response_delay_max}ms`} />
                  <InfoRow label="Typing Indicator" value={discordConfig.typing_indicator} />
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-500 italic">No Discord configuration set</p>
          )}
        </InfoSection>
      )}

      {/* Deployment Configuration */}
      {!loading && (
        <InfoSection title="Deployment Configuration">
          {deploymentConfig ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <InfoRow label="Status" value={deploymentConfig.deployment_status} />
              <InfoRow label="Health Check Port" value={deploymentConfig.health_check_port} />
              <InfoRow label="Docker Image" value={deploymentConfig.docker_image} />
              <InfoRow label="Container Name" value={deploymentConfig.container_name} />
              <InfoRow label="Memory Limit" value={deploymentConfig.memory_limit} />
              <InfoRow label="CPU Limit" value={deploymentConfig.cpu_limit} />
              {deploymentConfig.last_deployed_at && (
                <InfoRow label="Last Deployed" value={new Date(deploymentConfig.last_deployed_at).toLocaleString()} />
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-500 italic">No deployment configuration set</p>
          )}
        </InfoSection>
      )}

      {loading && (
        <div className="text-center py-4">
          <div className="text-sm text-gray-500">Loading configurations...</div>
        </div>
      )}
    </div>
  )
}