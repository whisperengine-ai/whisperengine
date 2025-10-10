'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import CharacterEvolutionTimeline from '@/components/CharacterEvolutionTimeline'

interface DeployedCharacter {
  id: string
  name: string
  occupation: string
  apiEndpoint: string
  health_status: 'healthy' | 'unhealthy'
  last_deployment: string
}

export default function EvolutionPage() {
  const [deployedCharacters, setDeployedCharacters] = useState<DeployedCharacter[]>([])
  const [selectedCharacter, setSelectedCharacter] = useState<DeployedCharacter | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load deployed characters
  const loadDeployedCharacters = async () => {
    try {
      const response = await fetch('/api/characters/deploy', {
        method: 'GET'
      })

      if (!response.ok) {
        throw new Error('Failed to fetch deployed characters')
      }

      const data = await response.json()
      const characters = data.deployedCharacters || []
      
      // Filter to only healthy characters for evolution viewing
      const healthyCharacters = characters.filter((char: DeployedCharacter) => char.health_status === 'healthy')
      
      setDeployedCharacters(healthyCharacters)
      
      // Auto-select first healthy character
      if (healthyCharacters.length > 0) {
        setSelectedCharacter(healthyCharacters[0])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load characters')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDeployedCharacters()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading character evolution data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg border border-red-200 p-8 max-w-md mx-auto">
          <div className="text-center">
            <div className="text-red-600 text-4xl mb-4">⚠️</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Failed to Load Characters</h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <button 
              onClick={loadDeployedCharacters}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (deployedCharacters.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg border border-gray-200 p-8 max-w-md mx-auto text-center">
          <div className="text-gray-400 text-4xl mb-4">🤖</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Characters Available</h2>
          <p className="text-gray-600 mb-4">
            No deployed characters found for evolution viewing. Deploy some characters first to see their learning progression.
          </p>
          <Link 
            href="/characters/deploy"
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 inline-block"
          >
            Deploy Characters
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-4">
            <Link href="/" className="text-gray-500 hover:text-gray-700">
              ← Back to Home
            </Link>
            <div className="border-l border-gray-300 h-6"></div>
            <h1 className="text-xl font-semibold text-gray-900">Character Evolution</h1>
          </div>            {/* Character Selector */}
            <div className="flex items-center space-x-4">
              <label className="text-sm font-medium text-gray-700">Character:</label>
              <select 
                value={selectedCharacter?.id || ''} 
                onChange={(e) => {
                  const character = deployedCharacters.find(c => c.id === e.target.value)
                  setSelectedCharacter(character || null)
                }}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {deployedCharacters.map((character) => (
                  <option key={character.id} value={character.id}>
                    {character.name} ({character.occupation})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {selectedCharacter ? (
          <div className="space-y-6">
            {/* Character Summary */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{selectedCharacter.name}</h2>
                  <p className="text-gray-600">{selectedCharacter.occupation}</p>
                </div>
                <div className="text-right">
                  <div className="flex items-center space-x-2">
                    <span className="inline-block w-2 h-2 bg-green-500 rounded-full"></span>
                    <span className="text-sm text-gray-600">Active</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Last deployed: {new Date(selectedCharacter.last_deployment).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>

            {/* Evolution Timeline */}
            <CharacterEvolutionTimeline 
              characterName={selectedCharacter.name}
              apiEndpoint={selectedCharacter.apiEndpoint}
              maxMilestones={50}
              showPhases={true}
              showMetrics={true}
            />
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
            <p className="text-gray-600">Select a character to view their evolution timeline.</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              WhisperEngine Character Evolution • Real-time learning insights
            </p>
            <div className="flex items-center space-x-4">
              <Link href="/chat" className="text-sm text-indigo-600 hover:text-indigo-700">
                Chat Interface
              </Link>
              <Link href="/characters" className="text-sm text-indigo-600 hover:text-indigo-700">
                Manage Characters
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}