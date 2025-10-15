'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface DeployedBot {
  name: string
  container_name: string
  image: string
  status: string
  ports: string
  health: 'healthy' | 'unhealthy' | 'unknown'
  uptime: string
}

interface DeploymentInfo {
  deployed_bots: DeployedBot[]
  total_deployed: number
  infrastructure_status: string
}

export default function DeploymentsPage() {
  const [deploymentInfo, setDeploymentInfo] = useState<DeploymentInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [testingBot, setTestingBot] = useState<string | null>(null)

  useEffect(() => {
    loadDeployments()
    const interval = setInterval(loadDeployments, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadDeployments = async () => {
    try {
      const response = await fetch('/api/deployments')
      if (response.ok) {
        const data = await response.json()
        setDeploymentInfo(data)
        setError(null)
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

  const testBotHealth = async (botName: string) => {
    setTestingBot(botName)
    try {
      const response = await fetch('/api/deployments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ bot_name: botName })
      })
      
      if (response.ok) {
        const result = await response.json()
        alert(`Bot Health Check:\nContainer: ${result.container_status}\nHealth: ${result.health_check}`)
      } else {
        alert('Failed to check bot health')
      }
    } catch (error) {
      console.error('Error testing bot health:', error)
      alert('Error testing bot health')
    } finally {
      setTestingBot(null)
    }
  }

  const getHealthIcon = (health: string) => {
    switch (health) {
      case 'healthy': return '🟢'
      case 'unhealthy': return '🔴'
      default: return '🟡'
    }
  }

  const getStatusColor = (health: string) => {
    switch (health) {
      case 'healthy': return 'bg-green-100 text-green-800'
      case 'unhealthy': return 'bg-red-100 text-red-800'
      default: return 'bg-yellow-100 text-yellow-800'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-400">Loading deployments...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <nav className="bg-gray-800 shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-8">
            <Link href="/" className="text-xl font-bold text-blue-400">
              CDL Authoring Tool
            </Link>
            <div className="flex space-x-6">
              <Link href="/characters" className="text-gray-400 hover:text-blue-400">
                Characters
              </Link>
              <Link href="/config" className="text-gray-400 hover:text-blue-400">
                Configuration
              </Link>
              <Link href="/deployments" className="text-blue-400 font-medium">
                Deployments
              </Link>
              <Link href="/chat" className="text-gray-400 hover:text-blue-400">
                Chat
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-100 mb-2">Bot Deployments</h1>
          <p className="text-gray-400">View currently deployed WhisperEngine bots and their status.</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 text-red-800 border border-red-200 rounded-lg">
            {error}
          </div>
        )}

        {deploymentInfo && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-gray-800 p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-400">Deployed Bots</p>
                  <p className="text-2xl font-bold text-gray-100">{deploymentInfo.total_deployed}</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-400">Infrastructure</p>
                  <p className="text-2xl font-bold text-gray-100 capitalize">{deploymentInfo.infrastructure_status}</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012 2v2M7 7h10" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-400">Deployment Type</p>
                  <p className="text-2xl font-bold text-gray-100">Quickstart</p>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="bg-gray-800 rounded-lg shadow">
          {!deploymentInfo || deploymentInfo.deployed_bots.length === 0 ? (
            <div className="p-8 text-center">
              <div className="text-6xl mb-4">🤖</div>
              <h3 className="text-xl font-semibold text-gray-100 mb-2">No Deployed Bots</h3>
              <p className="text-gray-400 mb-6">
                Start WhisperEngine to see deployed bots here. Run <code className="bg-gray-100 px-2 py-1 rounded">docker compose up</code> to start the system.
              </p>
              <div className="flex justify-center space-x-4">
                <button
                  onClick={loadDeployments}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
                >
                  🔄 Check Again
                </button>
                <Link 
                  href="/characters" 
                  className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700"
                >
                  Manage Characters
                </Link>
              </div>
            </div>
          ) : (
            <>
              <div className="px-6 py-4 border-b border-gray-700">
                <div className="flex justify-between items-center">
                  <h2 className="text-xl font-semibold">Currently Deployed Bots</h2>
                  <button
                    onClick={loadDeployments}
                    className="text-blue-400 hover:text-blue-800 font-medium"
                  >
                    🔄 Refresh
                  </button>
                </div>
              </div>

              <div className="divide-y divide-gray-200">
                {deploymentInfo.deployed_bots.map((bot) => (
                  <div key={bot.container_name} className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="text-2xl">
                          {getHealthIcon(bot.health)}
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-100">
                            {bot.name.charAt(0).toUpperCase() + bot.name.slice(1)} Bot
                          </h3>
                          <p className="text-sm text-gray-400">
                            Container: {bot.container_name}
                          </p>
                          <p className="text-sm text-gray-500">
                            Image: {bot.image}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(bot.health)}`}>
                          {bot.health}
                        </span>

                        <button
                          onClick={() => testBotHealth(bot.name)}
                          disabled={testingBot === bot.name}
                          className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                        >
                          {testingBot === bot.name ? 'Testing...' : 'Health Check'}
                        </button>

                        {bot.health === 'healthy' && (
                          <Link
                            href={`/chat`}
                            className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                            title="Chat with this bot"
                          >
                            Chat
                          </Link>
                        )}
                      </div>
                    </div>

                    <div className="mt-4 p-3 bg-gray-900 rounded text-sm">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        <div>
                          <strong>Status:</strong> 
                          <span className="ml-2">{bot.status}</span>
                        </div>
                        <div>
                          <strong>Ports:</strong> 
                          <code className="ml-2 text-blue-400">{bot.ports}</code>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        <div className="mt-8 bg-gray-800 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">QuickStart Deployment</h3>
          <p className="text-blue-800 mb-4">
            WhisperEngine is running in quickstart mode with a single bot. This is perfect for getting started and testing characters.
          </p>
          <div className="bg-gray-800 rounded p-4 font-mono text-sm">
            <div className="text-gray-400 mb-2"># Start WhisperEngine</div>
            <div className="text-blue-400">docker compose up -d</div>
            <div className="text-gray-400 mt-2 mb-2"># View logs</div>
            <div className="text-blue-400">docker logs whisperengine-assistant</div>
          </div>
        </div>
      </div>
    </div>
  )
}
