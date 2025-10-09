'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface Deployment {
  botName: string
  characterName: string
  envFile: string
  healthCheckPort: string
  apiEndpoint: string
  isRunning: boolean
}

export default function DeploymentsPage() {
  const [deployments, setDeployments] = useState<Deployment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDeployments()
  }, [])

  const loadDeployments = async () => {
    try {
      const response = await fetch('/api/characters/deploy')
      if (response.ok) {
        const data = await response.json()
        setDeployments(data.deployments || [])
      } else {
        setError('Failed to load deployment status')
      }
    } catch (error) {
      console.error('Error loading deployments:', error)
      setError('Failed to load deployment status')
    } finally {
      setLoading(false)
    }
  }

  const testEndpoint = async (deployment: Deployment) => {
    try {
      const response = await fetch(deployment.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: 'test_user',
          message: 'Hello!',
          context: {
            channel_type: 'web_ui',
            platform: 'test',
            metadata: {}
          }
        })
      })

      if (response.ok) {
        const data = await response.json()
        alert(`✅ ${deployment.characterName} is working!\n\nResponse: ${data.response || data.message}`)
      } else {
        alert(`❌ ${deployment.characterName} returned error: ${response.status} ${response.statusText}`)
      }
    } catch (error) {
      alert(`❌ Failed to connect to ${deployment.characterName}: ${error}`)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading deployments...</p>
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
              <Link href="/config" className="text-gray-600 hover:text-blue-600">
                Configuration
              </Link>
              <Link href="/deployments" className="text-blue-600 font-medium">
                Deployments
              </Link>
              <Link href="/chat" className="text-gray-600 hover:text-blue-600">
                Chat
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Character Deployments</h1>
          <p className="text-gray-600">View and manage deployed WhisperEngine characters.</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 text-red-800 border border-red-200 rounded-lg">
            {error}
          </div>
        )}

        <div className="bg-white rounded-lg shadow">
          {deployments.length === 0 ? (
            <div className="p-8 text-center">
              <div className="text-6xl mb-4">🤖</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No Deployed Characters</h3>
              <p className="text-gray-600 mb-6">
                Deploy characters from the Characters page to see them here.
              </p>
              <Link 
                href="/characters" 
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
              >
                Go to Characters
              </Link>
            </div>
          ) : (
            <>
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h2 className="text-xl font-semibold">Deployed Characters</h2>
                  <button
                    onClick={loadDeployments}
                    className="text-blue-600 hover:text-blue-800 font-medium"
                  >
                    🔄 Refresh
                  </button>
                </div>
              </div>

              <div className="divide-y divide-gray-200">
                {deployments.map((deployment) => (
                  <div key={deployment.botName} className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className={`w-3 h-3 rounded-full ${
                          deployment.isRunning ? 'bg-green-500' : 'bg-red-500'
                        }`}></div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">
                            {deployment.characterName}
                          </h3>
                          <p className="text-sm text-gray-600">
                            Bot Name: {deployment.botName} • Port: {deployment.healthCheckPort}
                          </p>
                          <p className="text-sm text-gray-500">
                            Environment: {deployment.envFile}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          deployment.isRunning 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {deployment.isRunning ? 'Running' : 'Stopped'}
                        </span>

                        <button
                          onClick={() => testEndpoint(deployment)}
                          className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                        >
                          Test Chat
                        </button>

                        <Link
                          href={`/chat?endpoint=${encodeURIComponent(deployment.apiEndpoint)}&character=${encodeURIComponent(deployment.characterName)}`}
                          className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                        >
                          Open Chat
                        </Link>
                      </div>
                    </div>

                    <div className="mt-4 p-3 bg-gray-50 rounded text-sm">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        <div>
                          <strong>API Endpoint:</strong> 
                          <code className="ml-2 text-blue-600">{deployment.apiEndpoint}</code>
                        </div>
                        <div>
                          <strong>Health Check:</strong> 
                          <code className="ml-2 text-blue-600">
                            http://localhost:{deployment.healthCheckPort}/health
                          </code>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">💡 Deployment Information</h3>
          <div className="text-sm text-blue-800 space-y-2">
            <p>• Characters are deployed as individual WhisperEngine bot instances</p>
            <p>• Each character gets its own environment file and API endpoint</p>
            <p>• Use the setup scripts to start/stop deployed characters</p>
            <p>• Green status = character is running and responding to requests</p>
            <p>• Red status = character environment exists but service is not running</p>
          </div>
        </div>
      </div>
    </div>
  )
}