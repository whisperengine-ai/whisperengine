import { NextRequest, NextResponse } from 'next/server'
import { 
  getCharacterLLMConfig, 
  createOrUpdateCharacterLLMConfig,
  getCharacterDiscordConfig,
  createOrUpdateCharacterDiscordConfig,
  getCharacterDeploymentConfig,
  createOrUpdateCharacterDeploymentConfig
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
    
    return NextResponse.json({
      success: false,
      error: errorMessage
    }, { status: 500 })
  }
}