'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'

interface Character {
  id: number
  name: string
  is_active: boolean
}

export default function GettingStarted() {
  const [characters, setCharacters] = useState<Character[]>([])
  const [hasCharacters, setHasCharacters] = useState(false)

  useEffect(() => {
    loadCharacters()
  }, [])

  const loadCharacters = async () => {
    try {
      const response = await fetch('/api/characters')
      if (response.ok) {
        const data = await response.json()
        setCharacters(data.characters || [])
        setHasCharacters((data.characters || []).length > 0)
      }
    } catch (error) {
      console.error('Failed to load characters:', error)
    }
  }

  if (hasCharacters) {
    return (
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 mb-8">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                🎉 Welcome to WhisperEngine!
              </h2>
              <p className="text-gray-600 mb-4">
                You have {characters.length} character{characters.length !== 1 ? 's' : ''} ready. 
                Manage configurations and deployments all from this Web UI.
              </p>
              <div className="flex space-x-4">
                <Link 
                  href="/characters"
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                  View Characters
                </Link>
                <Link 
                  href="/characters/new"
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                >
                  Create New Character
                </Link>
              </div>
            </div>
            <div className="text-6xl">🎭</div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-8 mb-8">
      <div className="max-w-4xl mx-auto text-center">
        <div className="text-6xl mb-4">🎭</div>
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Welcome to WhisperEngine!
        </h2>
        <p className="text-xl text-gray-600 mb-6">
          Zero-Configuration AI Character Platform
        </p>
        
        <div className="bg-white rounded-lg p-6 mb-6 text-left max-w-2xl mx-auto">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            ✨ Quick Start Guide
          </h3>
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">1</span>
              <div>
                <p className="font-medium text-gray-900">Create Your First Character</p>
                <p className="text-sm text-gray-600">Use our simple wizard to create an AI character with personality</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">2</span>
              <div>
                <p className="font-medium text-gray-900">Configure LLM Provider</p>
                <p className="text-sm text-gray-600">Add your OpenAI, Anthropic, or other LLM API key in character settings</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">3</span>
              <div>
                <p className="font-medium text-gray-900">Deploy & Chat</p>
                <p className="text-sm text-gray-600">One-click deployment - your character will be ready to chat!</p>
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-center space-x-4">
          <Link 
            href="/characters/new"
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 font-medium"
          >
            🚀 Create Your First Character
          </Link>
          <a 
            href="https://github.com/whisperengine-ai/whisperengine/blob/main/docs/guides/README.quickstart.md"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 font-medium"
          >
            📚 View Documentation
          </a>
        </div>

        <div className="mt-8 pt-6 border-t border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="bg-white rounded-lg p-4">
              <div className="text-2xl mb-2">🔧</div>
              <h4 className="font-medium text-gray-900 mb-1">Zero Configuration</h4>
              <p className="text-gray-600">No .env editing required - everything via Web UI</p>
            </div>
            <div className="bg-white rounded-lg p-4">
              <div className="text-2xl mb-2">🐳</div>
              <h4 className="font-medium text-gray-900 mb-1">Docker Only</h4>
              <p className="text-gray-600">Simple Docker commands for platform management</p>
            </div>
            <div className="bg-white rounded-lg p-4">
              <div className="text-2xl mb-2">🎭</div>
              <h4 className="font-medium text-gray-900 mb-1">Multi-Character</h4>
              <p className="text-gray-600">Create unlimited AI characters with unique personalities</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}