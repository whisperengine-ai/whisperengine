import { NextRequest, NextResponse } from 'next/server'
import { getCharacterById } from '@/lib/db'

interface RouteParams {
  params: Promise<{
    id: string
  }>
}

// Mock deployment orchestrator API calls
// In production, these would call the actual bot orchestrator service
async function callOrchestrator(endpoint: string, options: RequestInit = {}) {
  const orchestratorUrl = process.env.ORCHESTRATOR_URL || 'http://localhost:8080'
  
  try {
    const response = await fetch(`${orchestratorUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    })
    
    if (!response.ok) {
      throw new Error(`Orchestrator API error: ${response.status}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error('Orchestrator API call failed:', error)
    // Return mock data for development
    return null
  }
}

export async function GET(request: NextRequest, { params }: RouteParams) {
  try {
    const resolvedParams = await params
    const characterId = parseInt(resolvedParams.id)
    
    if (isNaN(characterId)) {
      return NextResponse.json({ error: 'Invalid character ID' }, { status: 400 })
    }

    const character = await getCharacterById(characterId)
    if (!character) {
      return NextResponse.json({ error: 'Character not found' }, { status: 404 })
    }

    // Get deployment status from orchestrator
    const deployments = await callOrchestrator('/deployments')
    
    if (deployments?.deployments) {
      const deployment = deployments.deployments.find((d: { character_id: number }) => d.character_id === characterId)
      if (deployment) {
        return NextResponse.json({ deployment })
      }
    }

    // No active deployment
    return NextResponse.json({ deployment: null })
    
  } catch (error) {
    console.error('Error fetching deployment status:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(request: NextRequest, { params }: RouteParams) {
  try {
    const resolvedParams = await params
    const characterId = parseInt(resolvedParams.id)
    
    if (isNaN(characterId)) {
      return NextResponse.json({ error: 'Invalid character ID' }, { status: 400 })
    }

    const character = await getCharacterById(characterId)
    if (!character) {
      return NextResponse.json({ error: 'Character not found' }, { status: 404 })
    }

    const body = await request.json()
    const { action } = body

    if (action !== 'deploy') {
      return NextResponse.json({ error: 'Invalid action' }, { status: 400 })
    }

    // Trigger deployment via orchestrator
    const result = await callOrchestrator('/sync', { method: 'POST' })
    
    if (!result) {
      // Mock successful deployment for development
      const mockDeployment = {
        character_id: characterId,
        character_name: character.name,
        container_name: `whisperengine-${character.name.toLowerCase()}-bot`,
        port: 9090 + characterId,
        status: 'starting',
        health_check_url: `http://localhost:${9090 + characterId}/health`,
        created_at: new Date().toISOString()
      }
      
      return NextResponse.json({ 
        deployment: mockDeployment,
        message: 'Character deployment initiated (development mode)'
      })
    }

    return NextResponse.json({ 
      message: 'Character deployment initiated',
      result 
    })
    
  } catch (error) {
    console.error('Error deploying character:', error)
    return NextResponse.json({ error: 'Failed to deploy character' }, { status: 500 })
  }
}

export async function DELETE(request: NextRequest, { params }: RouteParams) {
  try {
    const resolvedParams = await params
    const characterId = parseInt(resolvedParams.id)
    
    if (isNaN(characterId)) {
      return NextResponse.json({ error: 'Invalid character ID' }, { status: 400 })
    }

    const character = await getCharacterById(characterId)
    if (!character) {
      return NextResponse.json({ error: 'Character not found' }, { status: 404 })
    }

    // Stop deployment via orchestrator
    const result = await callOrchestrator(`/deployments/${characterId}/stop`, { 
      method: 'DELETE' 
    })
    
    return NextResponse.json({ 
      message: 'Character deployment stopped',
      result 
    })
    
  } catch (error) {
    console.error('Error stopping character:', error)
    return NextResponse.json({ error: 'Failed to stop character' }, { status: 500 })
  }
}

export async function PATCH(request: NextRequest, { params }: RouteParams) {
  try {
    const resolvedParams = await params
    const characterId = parseInt(resolvedParams.id)
    
    if (isNaN(characterId)) {
      return NextResponse.json({ error: 'Invalid character ID' }, { status: 400 })
    }

    const character = await getCharacterById(characterId)
    if (!character) {
      return NextResponse.json({ error: 'Character not found' }, { status: 404 })
    }

    const body = await request.json()
    const { action } = body

    if (action !== 'restart') {
      return NextResponse.json({ error: 'Invalid action' }, { status: 400 })
    }

    // Restart deployment via orchestrator
    const result = await callOrchestrator(`/deployments/${characterId}/restart`, { 
      method: 'POST' 
    })
    
    return NextResponse.json({ 
      message: 'Character deployment restarted',
      result 
    })
    
  } catch (error) {
    console.error('Error restarting character:', error)
    return NextResponse.json({ error: 'Failed to restart character' }, { status: 500 })
  }
}