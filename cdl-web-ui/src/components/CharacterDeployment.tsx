'use client'

import { useState, useEffect } from 'react'
import { Character, CharacterDeploymentConfig } from '@/types/cdl'

interface CharacterDeploymentProps {
  character: Character
}

interface DeploymentStatus {
  status: 'stopped' | 'running' | 'starting' | 'stopping' | 'error'
  container_name?: string
  uptime?: string
  health?: 'healthy' | 'unhealthy' | 'unknown'
  port?: number
}

export default function CharacterDeployment({ character }: CharacterDeploymentProps) {
  const [config, setConfig] = useState<Partial<CharacterDeploymentConfig>>({})
  const [deploymentStatus, setDeploymentStatus] = useState<DeploymentStatus>({ status: 'stopped' })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [deploying, setDeploying] = useState(false)

  useEffect(() => {
    loadConfig()
    loadDeploymentStatus()
    
    // Poll deployment status every 10 seconds
    const interval = setInterval(loadDeploymentStatus, 10000)
    return () => clearInterval(interval)
  }, [character.id])

  const loadConfig = async () => {
    try {
      const response = await fetch(`/api/characters/${character.id}/config`)
      if (response.ok) {
        const data = await response.json()
        setConfig(data.deployment_config || {})
      }
    } catch (error) {
      console.error('Error loading deployment config:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadDeploymentStatus = async () => {
    try {
      const response = await fetch(`/api/characters/${character.id}/deployment/status`)
      if (response.ok) {
        const data = await response.json()
        setDeploymentStatus(data)
      }
    } catch (error) {
      console.error('Error loading deployment status:', error)
    }
  }

  const saveConfig = async () => {
    setSaving(true)
    try {
      const response = await fetch(`/api/characters/${character.id}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ deployment_config: config })
      })
      
      if (response.ok) {
        alert('Deployment configuration saved successfully!')
        loadConfig()
      } else {
        throw new Error('Failed to save configuration')
      }
    } catch (error) {
      console.error('Error saving deployment config:', error)
      alert('Failed to save deployment configuration')
    } finally {
      setSaving(false)
    }
  }

  const deployCharacter = async () => {
    setDeploying(true)
    try {
      const response = await fetch(`/api/characters/${character.id}/deployment/deploy`, {
        method: 'POST'
      })
      
      if (response.ok) {
        alert('Character deployment started!')
        loadDeploymentStatus()
      } else {
        throw new Error('Failed to deploy character')
      }
    } catch (error) {
      console.error('Error deploying character:', error)
      alert('Failed to deploy character')
    } finally {
      setDeploying(false)
    }
  }

  const stopCharacter = async () => {
    setDeploying(true)
    try {
      const response = await fetch(`/api/characters/${character.id}/deployment/stop`, {
        method: 'POST'
      })
      
      if (response.ok) {
        alert('Character stopped!')
        loadDeploymentStatus()
      } else {
        throw new Error('Failed to stop character')
      }
    } catch (error) {
      console.error('Error stopping character:', error)
      alert('Failed to stop character')
    } finally {
      setDeploying(false)
    }
  }

  const updateField = (field: string, value: any) => {
    setConfig(prev => ({ ...prev, [field]: value }))
  }

  if (loading) {
    return <div className="text-center py-8">Loading deployment configuration...</div>
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'text-green-600 bg-green-100'
      case 'starting': return 'text-yellow-600 bg-yellow-100'
      case 'stopping': return 'text-orange-600 bg-orange-100'
      case 'error': return 'text-red-600 bg-red-100'
      default: return 'text-gray-400 bg-gray-100'
    }
  }

  return (
    <div className="space-y-6">
      {/* Current Status */}
      <div className="bg-gray-900 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-100 mb-4">Current Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <div className="text-sm text-gray-500">Status</div>
            <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(deploymentStatus.status)}`}>
              {deploymentStatus.status.charAt(0).toUpperCase() + deploymentStatus.status.slice(1)}
            </div>
          </div>
          
          {deploymentStatus.container_name && (
            <div>
              <div className="text-sm text-gray-500">Container</div>
              <div className="text-sm font-medium">{deploymentStatus.container_name}</div>
            </div>
          )}
          
          {deploymentStatus.uptime && (
            <div>
              <div className="text-sm text-gray-500">Uptime</div>
              <div className="text-sm font-medium">{deploymentStatus.uptime}</div>
            </div>
          )}

          {deploymentStatus.port && (
            <div>
              <div className="text-sm text-gray-500">Port</div>
              <div className="text-sm font-medium">{deploymentStatus.port}</div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="mt-4 flex space-x-3">
          {deploymentStatus.status === 'stopped' ? (
            <button
              onClick={deployCharacter}
              disabled={deploying}
              className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              {deploying ? 'Starting...' : '🚀 Deploy Character'}
            </button>
          ) : (
            <button
              onClick={stopCharacter}
              disabled={deploying}
              className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:opacity-50"
            >
              {deploying ? 'Stopping...' : '⏹️ Stop Character'}
            </button>
          )}
        </div>
      </div>

      {/* Configuration */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-100 mb-2">
            Docker Image
          </label>
          <input
            type="text"
            value={config.docker_image || 'whisperengine-bot:latest'}
            onChange={(e) => updateField('docker_image', e.target.value)}
            className="w-full border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500"
            placeholder="whisperengine-bot:latest"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-100 mb-2">
            Container Port
          </label>
          <input
            type="number"
            value={config.health_check_port || 8080}
            onChange={(e) => updateField('health_check_port', parseInt(e.target.value))}
            className="w-full border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500"
            placeholder="8080"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-100 mb-2">
            Memory Limit
          </label>
          <select
            value={config.memory_limit || '512m'}
            onChange={(e) => updateField('memory_limit', e.target.value)}
            className="w-full border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500"
          >
            <option value="256m">256 MB</option>
            <option value="512m">512 MB</option>
            <option value="1g">1 GB</option>
            <option value="2g">2 GB</option>
            <option value="4g">4 GB</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-100 mb-2">
            CPU Limit
          </label>
          <select
            value={config.cpu_limit || '0.5'}
            onChange={(e) => updateField('cpu_limit', e.target.value)}
            className="w-full border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500"
          >
            <option value="0.25">0.25 CPU</option>
            <option value="0.5">0.5 CPU</option>
            <option value="1">1 CPU</option>
            <option value="2">2 CPU</option>
          </select>
        </div>
      </div>

      {/* Auto Deploy */}
      <div>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={config.auto_start || false}
            onChange={(e) => updateField('auto_start', e.target.checked)}
            className="rounded border-gray-600 text-blue-400 focus:ring-blue-500"
          />
          <span className="ml-2 text-sm font-medium text-gray-100">
            Auto-deploy on configuration changes
          </span>
        </label>
      </div>

      {/* Save Button */}
      <div className="flex justify-end pt-6 border-t">
        <button
          onClick={saveConfig}
          disabled={saving}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Deployment Configuration'}
        </button>
      </div>
    </div>
  )
}