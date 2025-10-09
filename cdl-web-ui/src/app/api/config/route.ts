import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs/promises'
import path from 'path'

const ENV_FILE_PATH = path.join(process.cwd(), '../.env')

interface SystemConfig {
  llm_client_type: string
  llm_chat_api_url: string
  llm_chat_model: string
  llm_chat_api_key: string
  discord_bot_token: string
  enable_discord: boolean
  memory_system_type: string
  enable_character_intelligence: boolean
  enable_emotional_intelligence: boolean
  postgres_host: string
  postgres_port: string
  postgres_user: string
  postgres_password: string
  postgres_db: string
  qdrant_host: string
  qdrant_port: string
}

// Read configuration from .env file
export async function GET() {
  try {
    let envContent = ''
    try {
      envContent = await fs.readFile(ENV_FILE_PATH, 'utf-8')
    } catch (error) {
      // File doesn't exist, return defaults
      console.log('.env file not found, returning defaults')
    }

    const config: Partial<SystemConfig> = {}
    
    // Parse .env file
    const lines = envContent.split('\n')
    for (const line of lines) {
      const trimmed = line.trim()
      if (trimmed && !trimmed.startsWith('#')) {
        const [key, ...valueParts] = trimmed.split('=')
        const value = valueParts.join('=').replace(/^["']|["']$/g, '')
        
        switch (key) {
          case 'LLM_CLIENT_TYPE':
            config.llm_client_type = value
            break
          case 'LLM_CHAT_API_URL':
            config.llm_chat_api_url = value
            break
          case 'LLM_CHAT_MODEL':
            config.llm_chat_model = value
            break
          case 'LLM_CHAT_API_KEY':
            config.llm_chat_api_key = value
            break
          case 'DISCORD_BOT_TOKEN':
            config.discord_bot_token = value
            break
          case 'ENABLE_DISCORD':
            config.enable_discord = value === 'true'
            break
          case 'MEMORY_SYSTEM_TYPE':
            config.memory_system_type = value
            break
          case 'ENABLE_CHARACTER_INTELLIGENCE':
            config.enable_character_intelligence = value === 'true'
            break
          case 'ENABLE_EMOTIONAL_INTELLIGENCE':
            config.enable_emotional_intelligence = value === 'true'
            break
          case 'POSTGRES_HOST':
            config.postgres_host = value
            break
          case 'POSTGRES_PORT':
            config.postgres_port = value
            break
          case 'POSTGRES_USER':
            config.postgres_user = value
            break
          case 'POSTGRES_PASSWORD':
            config.postgres_password = value
            break
          case 'POSTGRES_DB':
            config.postgres_db = value
            break
          case 'QDRANT_HOST':
            config.qdrant_host = value
            break
          case 'QDRANT_PORT':
            config.qdrant_port = value
            break
        }
      }
    }

    return NextResponse.json(config)
  } catch (error) {
    console.error('Error reading configuration:', error)
    return NextResponse.json(
      { error: 'Failed to read configuration' },
      { status: 500 }
    )
  }
}

// Save configuration to .env file
export async function POST(request: NextRequest) {
  try {
    const config: SystemConfig = await request.json()

    // Validate required fields
    if (!config.llm_chat_api_key?.trim()) {
      return NextResponse.json(
        { error: 'LLM API key is required' },
        { status: 400 }
      )
    }

    // Read existing .env file to preserve other settings
    let existingEnv = ''
    try {
      existingEnv = await fs.readFile(ENV_FILE_PATH, 'utf-8')
    } catch (error) {
      console.log('Creating new .env file')
    }

    // Parse existing environment variables
    const existingVars: Record<string, string> = {}
    const lines = existingEnv.split('\n')
    for (const line of lines) {
      const trimmed = line.trim()
      if (trimmed && !trimmed.startsWith('#')) {
        const [key, ...valueParts] = trimmed.split('=')
        const value = valueParts.join('=')
        existingVars[key] = value
      }
    }

    // Update with new configuration
    existingVars['LLM_CLIENT_TYPE'] = config.llm_client_type
    existingVars['LLM_CHAT_API_URL'] = config.llm_chat_api_url
    existingVars['LLM_CHAT_MODEL'] = config.llm_chat_model
    existingVars['LLM_CHAT_API_KEY'] = config.llm_chat_api_key
    existingVars['DISCORD_BOT_TOKEN'] = config.discord_bot_token || ''
    existingVars['ENABLE_DISCORD'] = config.enable_discord ? 'true' : 'false'
    existingVars['MEMORY_SYSTEM_TYPE'] = config.memory_system_type
    existingVars['ENABLE_CHARACTER_INTELLIGENCE'] = config.enable_character_intelligence ? 'true' : 'false'
    existingVars['ENABLE_EMOTIONAL_INTELLIGENCE'] = config.enable_emotional_intelligence ? 'true' : 'false'
    existingVars['POSTGRES_HOST'] = config.postgres_host
    existingVars['POSTGRES_PORT'] = config.postgres_port
    existingVars['POSTGRES_USER'] = config.postgres_user
    existingVars['POSTGRES_PASSWORD'] = config.postgres_password
    existingVars['POSTGRES_DB'] = config.postgres_db
    existingVars['QDRANT_HOST'] = config.qdrant_host
    existingVars['QDRANT_PORT'] = config.qdrant_port

    // Ensure required variables exist if not set
    if (!existingVars['DISCORD_BOT_NAME']) {
      existingVars['DISCORD_BOT_NAME'] = 'assistant'
    }
    if (!existingVars['CHARACTER_NAME']) {
      existingVars['CHARACTER_NAME'] = 'assistant'
    }
    if (!existingVars['HEALTH_CHECK_PORT']) {
      existingVars['HEALTH_CHECK_PORT'] = '9090'
    }
    if (!existingVars['QDRANT_COLLECTION_NAME']) {
      existingVars['QDRANT_COLLECTION_NAME'] = 'whisperengine_memory_assistant'
    }

    // Generate .env content
    const envContent = [
      '# WhisperEngine Configuration',
      '# Generated by CDL Web UI',
      '',
      '# LLM Configuration',
      `LLM_CLIENT_TYPE=${existingVars['LLM_CLIENT_TYPE']}`,
      `LLM_CHAT_API_URL=${existingVars['LLM_CHAT_API_URL']}`,
      `LLM_CHAT_MODEL=${existingVars['LLM_CHAT_MODEL']}`,
      `LLM_CHAT_API_KEY=${existingVars['LLM_CHAT_API_KEY']}`,
      '',
      '# Discord Configuration (Optional)',
      `DISCORD_BOT_TOKEN=${existingVars['DISCORD_BOT_TOKEN']}`,
      `ENABLE_DISCORD=${existingVars['ENABLE_DISCORD']}`,
      '',
      '# Character Configuration',
      `DISCORD_BOT_NAME=${existingVars['DISCORD_BOT_NAME']}`,
      `CHARACTER_NAME=${existingVars['CHARACTER_NAME']}`,
      `HEALTH_CHECK_PORT=${existingVars['HEALTH_CHECK_PORT']}`,
      '',
      '# Memory and Intelligence',
      `MEMORY_SYSTEM_TYPE=${existingVars['MEMORY_SYSTEM_TYPE']}`,
      `ENABLE_CHARACTER_INTELLIGENCE=${existingVars['ENABLE_CHARACTER_INTELLIGENCE']}`,
      `ENABLE_EMOTIONAL_INTELLIGENCE=${existingVars['ENABLE_EMOTIONAL_INTELLIGENCE']}`,
      '',
      '# Database Configuration',
      `POSTGRES_HOST=${existingVars['POSTGRES_HOST']}`,
      `POSTGRES_PORT=${existingVars['POSTGRES_PORT']}`,
      `POSTGRES_USER=${existingVars['POSTGRES_USER']}`,
      `POSTGRES_PASSWORD=${existingVars['POSTGRES_PASSWORD']}`,
      `POSTGRES_DB=${existingVars['POSTGRES_DB']}`,
      '',
      '# Vector Database Configuration',
      `QDRANT_HOST=${existingVars['QDRANT_HOST']}`,
      `QDRANT_PORT=${existingVars['QDRANT_PORT']}`,
      `QDRANT_COLLECTION_NAME=${existingVars['QDRANT_COLLECTION_NAME']}`,
      ''
    ].join('\n')

    // Write to .env file
    await fs.writeFile(ENV_FILE_PATH, envContent, 'utf-8')

    return NextResponse.json({ 
      success: true, 
      message: 'Configuration saved successfully'
    })
  } catch (error) {
    console.error('Error saving configuration:', error)
    return NextResponse.json(
      { error: 'Failed to save configuration' },
      { status: 500 }
    )
  }
}