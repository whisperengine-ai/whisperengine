import { NextResponse } from 'next/server'
import { Pool } from 'pg'

export async function POST(request: Request) {
  try {
    const { character_id, character_name } = await request.json()
    
    if (!character_id || !character_name) {
      return NextResponse.json(
        { error: 'character_id and character_name are required' },
        { status: 400 }
      )
    }
    
    // Sanitize character name for container/environment usage
    const sanitizedName = character_name.toLowerCase().replace(/[^a-z0-9-]/g, '-')
    const containerName = `${sanitizedName}-bot`
    const portNumber = await getNextAvailablePort()
    const collectionName = `whisperengine_memory_${sanitizedName}`
    
    // Check if character exists in database
    const pool = new Pool({
      host: process.env.PGHOST || 'localhost',
      port: parseInt(process.env.PGPORT || '5432'),
      database: process.env.PGDATABASE || 'whisperengine',
      user: process.env.PGUSER || 'whisperengine',
      password: process.env.PGPASSWORD || 'whisperengine_password',
    })
    
    const characterQuery = 'SELECT * FROM characters WHERE id = $1'
    const characterResult = await pool.query(characterQuery, [character_id])
    
    if (characterResult.rows.length === 0) {
      return NextResponse.json(
        { error: 'Character not found' },
        { status: 404 }
      )
    }
    
    // Create deployment configuration
    const deploymentConfig = {
      container_name: containerName,
      image: 'whisperengine/whisperengine:latest',
      port: portNumber,
      environment: {
        // Database connection
        POSTGRES_HOST: "postgres",
        POSTGRES_PORT: "5432", 
        POSTGRES_USER: "whisperengine",
        POSTGRES_PASSWORD: "whisperengine_password",
        POSTGRES_DB: "whisperengine",
        
        // Vector database
        QDRANT_HOST: "qdrant",
        QDRANT_PORT: "6333",
        QDRANT_COLLECTION_NAME: collectionName,
        
        // Character configuration
        DISCORD_BOT_NAME: sanitizedName,
        CHARACTER_NAME: sanitizedName,
        HEALTH_CHECK_PORT: portNumber.toString(),
        CHARACTER_ID: character_id.toString(),
        
        // LLM configuration
        LLM_CLIENT_TYPE: "openrouter",
        LLM_CHAT_API_URL: "https://openrouter.ai/api/v1",
        LLM_CHAT_MODEL: "anthropic/claude-3-haiku",
        LLM_CHAT_API_KEY: "",
        
        // Memory and intelligence
        MEMORY_SYSTEM_TYPE: "vector",
        ENABLE_CHARACTER_INTELLIGENCE: "true",
        ENABLE_EMOTIONAL_INTELLIGENCE: "true",
        
        // Discord (optional)
        DISCORD_BOT_TOKEN: "",
        ENABLE_DISCORD: "false"
      }
    }
    
    // Generate deployment commands and configurations
    const dockerCommand = generateDockerRunCommand(deploymentConfig)
    const dockerComposeConfig = generateDockerComposeConfig(deploymentConfig)
    const envFileContent = generateEnvFile(deploymentConfig)
    
    // Record deployment in database (status: generated)
    const deploymentResult = await pool.query(
      `INSERT INTO bot_deployments 
       (character_id, container_name, port, status, config) 
       VALUES ($1, $2, $3, $4, $5) 
       RETURNING id`,
      [character_id, containerName, portNumber, 'generated', JSON.stringify(deploymentConfig)]
    )
    
    await pool.end()
    
    return NextResponse.json({
      success: true,
      message: `Deployment configuration generated for ${character_name}`,
      deployment: {
        id: deploymentResult.rows[0].id,
        character_name,
        container_name: containerName,
        port: portNumber,
        status: 'generated'
      },
      instructions: {
        overview: `This will deploy ${character_name} as a WhisperEngine bot on port ${portNumber}`,
        methods: [
          {
            name: "Docker Command (Quick)",
            description: "Run this single command to start the bot",
            command: dockerCommand
          },
          {
            name: "Docker Compose (Recommended)", 
            description: "Save as docker-compose.yml and run with docker-compose",
            config: dockerComposeConfig,
            commands: [
              "Save the above config as docker-compose.yml",
              "Run: docker-compose up -d"
            ]
          },
          {
            name: "Environment File",
            description: "Create .env file for manual configuration",
            content: envFileContent
          }
        ],
        verification: [
          `Wait 30-60 seconds for startup`,
          `Check health: curl http://localhost:${portNumber}/health`,
          `View logs: docker logs ${containerName}`
        ]
      }
    })
    
  } catch (error: any) {
    console.error('Deployment generation failed:', error)
    return NextResponse.json(
      { error: 'Failed to generate deployment', details: error.message },
      { status: 500 }
    )
  }
}

function generateDockerRunCommand(config: any): string {
  const envVars = Object.entries(config.environment)
    .map(([key, value]) => `-e ${key}="${value}"`)
    .join(' ')
    
  return `docker run -d \\
  --name ${config.container_name} \\
  --network whisperengine_whisperengine-network \\
  -p ${config.port}:9090 \\
  ${envVars} \\
  ${config.image}`
}

function generateDockerComposeConfig(config: any): object {
  return {
    version: '3.8',
    services: {
      [config.container_name]: {
        image: config.image,
        container_name: config.container_name,
        ports: [`${config.port}:9090`],
        environment: config.environment,
        networks: ['whisperengine_whisperengine-network'],
        depends_on: ['postgres', 'qdrant'],
        restart: 'unless-stopped'
      }
    },
    networks: {
      'whisperengine_whisperengine-network': {
        external: true
      }
    }
  }
}

function generateEnvFile(config: any): string {
  const envLines = Object.entries(config.environment)
    .map(([key, value]) => `${key}=${value}`)
    .join('\n')
    
  return `# ${config.container_name} Environment Configuration
# Generated by WhisperEngine CDL Web UI

${envLines}

# To use this file:
# 1. Save as .env.${config.container_name}
# 2. Run: docker run --env-file .env.${config.container_name} -d --name ${config.container_name} -p ${config.port}:9090 ${config.image}`
}

async function getNextAvailablePort(): Promise<number> {
  // Start from 9090 and find the next available port
  let port = 9090
  const maxPort = 9200
  
  while (port <= maxPort) {
    try {
      // Check if port is in use by querying existing deployments
      const pool = new Pool({
        host: process.env.PGHOST || 'localhost',
        port: parseInt(process.env.PGPORT || '5432'),
        database: process.env.PGDATABASE || 'whisperengine',
        user: process.env.PGUSER || 'whisperengine',
        password: process.env.PGPASSWORD || 'whisperengine_password',
      })
      
      const result = await pool.query('SELECT COUNT(*) FROM bot_deployments WHERE port = $1 AND status IN ($2, $3, $4)', [port, 'running', 'deploying', 'generated'])
      await pool.end()
      
      if (parseInt(result.rows[0].count) === 0) {
        return port
      }
      
      port++
    } catch (error) {
      console.error('Error checking port availability:', error)
      port++
    }
  }
  
  throw new Error('No available ports found')
}