'use client'

import { useState } from 'react'
import { Character } from '@/types/cdl'
import SimpleCharacterEditForm from './SimpleCharacterEditForm'
import CharacterLLMConfig from './CharacterLLMConfig'
import CharacterDiscordConfig from './CharacterDiscordConfig'
import CharacterDeployment from './CharacterDeployment'

interface UnifiedCharacterInterfaceProps {
  character: Character
}

type TabType = 'character' | 'llm' | 'discord' | 'deployment'

export default function UnifiedCharacterInterface({ character }: UnifiedCharacterInterfaceProps) {
  const [activeTab, setActiveTab] = useState<TabType>('character')

  const tabs = [
    { id: 'character' as TabType, label: '👤 Character', description: 'Personality, traits, and behavior' },
    { id: 'llm' as TabType, label: '🤖 LLM Config', description: 'AI model and provider settings' },
    { id: 'discord' as TabType, label: '💬 Discord', description: 'Bot token and Discord settings' },
    { id: 'deployment' as TabType, label: '🚀 Deploy', description: 'Container status and deployment' }
  ]

  return (
    <div className="max-w-7xl mx-auto">
      {/* Tab Navigation */}
      <div className="bg-gray-800 rounded-lg shadow mb-6">
        <div className="border-b border-gray-700">
          <nav className="-mb-px flex space-x-8 px-6" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
                  ${activeTab === tab.id
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-300 hover:border-gray-600'
                  }
                `}
              >
                <div className="flex flex-col items-center">
                  <span className="text-lg mb-1">{tab.label}</span>
                  <span className="text-xs text-gray-400">{tab.description}</span>
                </div>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <div className="bg-gray-800 rounded-lg shadow">
        {activeTab === 'character' && (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-100 mb-6">Character Configuration</h2>
            <SimpleCharacterEditForm character={character} />
          </div>
        )}
        
        {activeTab === 'llm' && (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-100 mb-6">LLM Configuration</h2>
            <CharacterLLMConfig character={character} />
          </div>
        )}
        
        {activeTab === 'discord' && (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-100 mb-6">Discord Configuration</h2>
            <CharacterDiscordConfig character={character} />
          </div>
        )}
        
        {activeTab === 'deployment' && (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-100 mb-6">Deployment & Status</h2>
            <CharacterDeployment character={character} />
          </div>
        )}
      </div>
    </div>
  )
}