'use client'

import { useState } from 'react'
import { Character } from '@/types/cdl'

interface CharacterEditFormProps {
  character: Character
}

// Real CDL data structure that matches database
interface RealCDLData {
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
    communication_style?: {
      tone?: string
      formality?: string
      directness?: string
      empathy_level?: string
    }
  }
  communication?: {
    response_length?: string
    ai_identity_handling?: {
      approach?: string
      philosophy?: string
      allow_full_roleplay_immersion?: boolean
    }
  }
  [key: string]: unknown // Allow for additional fields
}

export default function CharacterEditForm({ character }: CharacterEditFormProps) {
  const [cdlData, setCdlData] = useState<RealCDLData>(() => {
    if (character.cdl_data) {
      try {
        // Handle the actual complex CDL structure from database
        return character.cdl_data as RealCDLData
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
    setCdlData(prev => {
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
    return current ?? defaultValue
  }

  return (
    <div className="space-y-8">
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

      {/* Basic Identity */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Basic Identity</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Name</label>
            <input
              type="text"
              value={getValue(['identity', 'name'], character.name)}
              onChange={(e) => updateCdlData(['identity', 'name'], e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Gender</label>
            <select
              value={getValue(['identity', 'gender'])}
              onChange={(e) => updateCdlData(['identity', 'gender'], e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select gender</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="non-binary">Non-binary</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Age</label>
            <input
              type="number"
              value={getValue(['identity', 'age'])}
              onChange={(e) => updateCdlData(['identity', 'age'], parseInt(e.target.value))}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
            <input
              type="text"
              value={getValue(['identity', 'location'], character.location)}
              onChange={(e) => updateCdlData(['identity', 'location'], e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
            <textarea
              value={getValue(['identity', 'description'], character.description)}
              onChange={(e) => updateCdlData(['identity', 'description'], e.target.value)}
              rows={3}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </section>

      {/* Voice & Communication */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Voice & Communication</h2>
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
              placeholder="e.g., Philosophical and poetic"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Accent</label>
            <input
              type="text"
              value={getValue(['identity', 'voice', 'accent'])}
              onChange={(e) => updateCdlData(['identity', 'voice', 'accent'], e.target.value)}
              placeholder="e.g., British, None specific"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Volume</label>
            <input
              type="text"
              value={getValue(['identity', 'voice', 'volume'])}
              onChange={(e) => updateCdlData(['identity', 'voice', 'volume'], e.target.value)}
              placeholder="e.g., Gentle but profound"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </section>

      {/* Personality Traits (Big Five) */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Personality Traits (Big Five)</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'].map((trait) => (
            <div key={trait} className="border border-gray-200 rounded-lg p-4">
              <h3 className="font-medium text-gray-900 mb-3 capitalize">{trait}</h3>
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
      </section>

      {/* Essence */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Essence</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Anchor</label>
            <textarea
              value={getValue(['identity', 'essence', 'anchor'])}
              onChange={(e) => updateCdlData(['identity', 'essence', 'anchor'], e.target.value)}
              rows={2}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Nature</label>
            <textarea
              value={getValue(['identity', 'essence', 'nature'])}
              onChange={(e) => updateCdlData(['identity', 'essence', 'nature'], e.target.value)}
              rows={2}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Core Identity</label>
            <textarea
              value={getValue(['identity', 'essence', 'core_identity'])}
              onChange={(e) => updateCdlData(['identity', 'essence', 'core_identity'], e.target.value)}
              rows={3}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </section>

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