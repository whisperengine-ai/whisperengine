'use client'

import { useState } from 'react'
import { Character } from '@/types/cdl'

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

  const handleSave = async () => {
    setIsLoading(true)
    setSaveStatus('saving')
    
    try {
      const response = await fetch(`/api/characters/${character.id}`, {
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

      if (response.ok) {
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
    { id: 'knowledge', name: 'Knowledge' }
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