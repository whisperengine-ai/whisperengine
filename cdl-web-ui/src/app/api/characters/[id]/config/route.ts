import { NextRequest, NextResponse } from 'next/server'
import { 
  getCharacterLLMConfig, 
  createOrUpdateCharacterLLMConfig,
  deleteCharacterLLMConfig,
  getCharacterDiscordConfig,
  createOrUpdateCharacterDiscordConfig,
  deleteCharacterDiscordConfig,
  getCharacterDeploymentConfig,
  createOrUpdateCharacterDeploymentConfig,
  deleteCharacterDeploymentConfig
} from '@/lib/db'
import { CharacterLLMConfig, CharacterDiscordConfig, CharacterDeploymentConfig } from '@/types/cdl'

interface RouteParams {
  params: Promise<{ id: string }>
}

export async function GET(request: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params
    const characterId = parseInt(id)
    
    if (isNaN(characterId)) {
      return NextResponse.json({
        success: false,
        error: 'Invalid character ID'
      }, { status: 400 })
    }

    const [llmConfig, discordConfig, deploymentConfig] = await Promise.all([
      getCharacterLLMConfig(characterId),
      getCharacterDiscordConfig(characterId),
      getCharacterDeploymentConfig(characterId)
    ])

    return NextResponse.json({
      success: true,
      llm_config: llmConfig,
      discord_config: discordConfig,
      deployment_config: deploymentConfig
    })
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    
    return NextResponse.json({
      success: false,
      error: errorMessage
    }, { status: 500 })
  }
}

export async function POST(request: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params
    const characterId = parseInt(id)
    
    if (isNaN(characterId)) {
      return NextResponse.json({
        success: false,
        error: 'Invalid character ID'
      }, { status: 400 })
    }

    const data = await request.json()
    
    console.log('Received config POST data:', data)
    
    const results: {
      llm_config?: CharacterLLMConfig
      discord_config?: CharacterDiscordConfig
      deployment_config?: CharacterDeploymentConfig
    } = {}

    // Update LLM config if provided
    if (data.llm_config) {
      results.llm_config = await createOrUpdateCharacterLLMConfig(characterId, data.llm_config)
    }

    // Update Discord config if provided
    if (data.discord_config) {
      results.discord_config = await createOrUpdateCharacterDiscordConfig(characterId, data.discord_config)
    }

    // Update Deployment config if provided
    if (data.deployment_config) {
      results.deployment_config = await createOrUpdateCharacterDeploymentConfig(characterId, data.deployment_config)
    }

    return NextResponse.json({
      success: true,
      ...results
    })
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    const errorStack = error instanceof Error ? error.stack : 'No stack trace'
    
    console.error('Config POST error:', {
      message: errorMessage,
      stack: errorStack,
      error
    })
    
    return NextResponse.json({
      success: false,
      error: errorMessage
    }, { status: 500 })
  }
}

export async function DELETE(request: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params
    const characterId = parseInt(id)
    
    if (isNaN(characterId)) {
      return NextResponse.json({
        success: false,
        error: 'Invalid character ID'
      }, { status: 400 })
    }

    // Get query parameters to determine which config type to delete
    const url = new URL(request.url)
    const configType = url.searchParams.get('type')

    if (!configType) {
      return NextResponse.json({
        success: false,
        error: 'Config type parameter required (llm, discord, or deployment)'
      }, { status: 400 })
    }

    let deleted = false
    let message = ''

    switch (configType) {
      case 'llm':
        deleted = await deleteCharacterLLMConfig(characterId)
        message = 'LLM configuration deleted successfully'
        break
      case 'discord':
        deleted = await deleteCharacterDiscordConfig(characterId)
        message = 'Discord configuration deleted successfully'
        break
      case 'deployment':
        deleted = await deleteCharacterDeploymentConfig(characterId)
        message = 'Deployment configuration deleted successfully'
        break
      default:
        return NextResponse.json({
          success: false,
          error: 'Invalid config type. Must be llm, discord, or deployment'
        }, { status: 400 })
    }

    if (!deleted) {
      return NextResponse.json({
        success: false,
        error: 'Configuration not found or already deleted'
      }, { status: 404 })
    }

    return NextResponse.json({
      success: true,
      message
    })
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    
    return NextResponse.json({
      success: false,
      error: errorMessage
    }, { status: 500 })
  }
}