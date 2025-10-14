'use client'

import { useState, useEffect } from 'react'
import { Character } from '@/types/cdl'

interface DeploymentManagerProps {
  character: Character
}

interface DeploymentStatus {
  character_id: number
  character_name: string
  container_name: string
  port: number
  status: string
  health_check_url: string
  created_at: string
}

export default function DeploymentManager({ character }: DeploymentManagerProps) {
  const [deploymentStatus, setDeploymentStatus] = useState<DeploymentStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDeploymentStatus()
  }, [character.id])

  const loadDeploymentStatus = async () => {
    try {
      const response = await fetch(`/api/characters/${character.id}/deployment`)
      if (response.ok) {
        const data = await response.json()
        setDeploymentStatus(data.deployment)
      }
    } catch (err) {
      console.error('Failed to load deployment status:', err)
    }
  }

  const deployCharacter = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`/api/characters/${character.id}/deployment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'deploy'
        })
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to deploy character')
      }
      
      const data = await response.json()
      setDeploymentStatus(data.deployment)
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const stopCharacter = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`/api/characters/${character.id}/deployment`, {
        method: 'DELETE'
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to stop character')
      }
      
      setDeploymentStatus(null)
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const restartCharacter = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`/api/characters/${character.id}/deployment`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'restart'
        })
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to restart character')
      }
      
      await loadDeploymentStatus()
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'text-green-600 bg-green-100'
      case 'starting': return 'text-yellow-600 bg-yellow-100'
      case 'stopping': return 'text-orange-600 bg-orange-100'
      case 'stopped': return 'text-gray-600 bg-gray-100'
      case 'error': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return '🟢'
      case 'starting': return '🟡'
      case 'stopping': return '🟠'
      case 'stopped': return '⚫'
      case 'error': return '🔴'
      default: return '⚪'
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        🚀 Deployment Status
      </h3>

      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {deploymentStatus ? (
        <div className="space-y-4">
          {/* Status Overview */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">{getStatusIcon(deploymentStatus.status)}</span>
              <div>
                <p className="font-medium text-gray-900">{character.name}</p>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(deploymentStatus.status)}`}>
                    {deploymentStatus.status.toUpperCase()}
                  </span>
                  <span className="text-sm text-gray-500">
                    Port: {deploymentStatus.port}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="flex space-x-2">
              <button
                onClick={restartCharacter}
                disabled={loading}
                className="px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                🔄 Restart
              </button>
              <button
                onClick={stopCharacter}
                disabled={loading}
                className="px-3 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
              >
                ⏹️ Stop
              </button>
            </div>
          </div>

          {/* Deployment Details */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Container Name</label>
              <p className="mt-1 text-sm text-gray-900 font-mono">{deploymentStatus.container_name}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Health Check</label>
              <a 
                href={deploymentStatus.health_check_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-1 text-sm text-blue-600 hover:text-blue-800 underline"
              >
                {deploymentStatus.health_check_url}
              </a>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Deployed At</label>
              <p className="mt-1 text-sm text-gray-900">
                {new Date(deploymentStatus.created_at).toLocaleString()}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Chat Endpoint</label>
              <p className="mt-1 text-sm text-gray-900 font-mono">
                http://localhost:{deploymentStatus.port}/api/chat
              </p>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="border-t pt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Quick Actions</h4>
            <div className="flex space-x-2">
              <button
                onClick={() => window.open(deploymentStatus.health_check_url, '_blank')}
                className="px-3 py-1 text-xs bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                📊 Health Check
              </button>
              <button
                onClick={() => window.open(`http://localhost:${deploymentStatus.port}/api/chat`, '_blank')}
                className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
              >
                💬 Test Chat API
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-8">
          <div className="text-gray-400 text-6xl mb-4">🚀</div>
          <h4 className="text-lg font-medium text-gray-900 mb-2">Character Not Deployed</h4>
          <p className="text-gray-600 mb-4">
            Deploy this character to start chatting with {character.name}
          </p>
          <button
            onClick={deployCharacter}
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? '🔄 Deploying...' : '🚀 Deploy Character'}
          </button>
        </div>
      )}

      {/* Help Section */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h4 className="text-sm font-medium text-blue-900 mb-2">💡 How Deployment Works</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Character configurations are loaded from the database</li>
          <li>• Each character gets its own Docker container and port</li>
          <li>• LLM and Discord settings are automatically applied</li>
          <li>• Health monitoring and auto-restart are enabled</li>
        </ul>
      </div>
    </div>
  )
}