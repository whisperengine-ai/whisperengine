import { NextResponse } from 'next/server'
import { exec } from 'child_process'
import { promisify } from 'util'
import { Pool } from 'pg'
import { getDatabaseConfig } from '@/lib/db'

const execAsync = promisify(exec)

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
    const pool = new Pool(getDatabaseConfig())
    
    const characterQuery = 'SELECT * FROM characters WHERE id = $1'
    const characterResult = await pool.query(characterQuery, [character_id])
    
    if (characterResult.rows.length === 0) {
      return NextResponse.json(
        { error: 'Character not found' },
        { status: 404 }
      )
    }
    
    const character = characterResult.rows[0]
    
    // Create deployment configuration
    const deploymentConfig = {
      container_name: containerName,
      image: 'whisperengine/whisperengine:latest',
      port: portNumber,
      environment: {
        // Core infrastructure
        POSTGRES_HOST: 'postgres',
        POSTGRES_PORT: '5432',
        POSTGRES_USER: 'whisperengine',
        POSTGRES_PASSWORD: 'whisperengine_password',
        POSTGRES_DB: 'whisperengine',
        QDRANT_HOST: 'qdrant',
        QDRANT_PORT: '6333',
        QDRANT_COLLECTION_NAME: collectionName,
        
        // Bot configuration
        DISCORD_BOT_NAME: sanitizedName,
        CHARACTER_NAME: sanitizedName,
        HEALTH_CHECK_PORT: portNumber.toString(),
        
        // Character-specific data
        CHARACTER_ID: character_id.toString(),
        
        // LLM Configuration (inherit from environment or character config)
        LLM_CLIENT_TYPE: process.env.LLM_CLIENT_TYPE || 'openrouter',
        LLM_CHAT_API_URL: process.env.LLM_CHAT_API_URL || 'https://openrouter.ai/api/v1',
        LLM_CHAT_MODEL: process.env.LLM_CHAT_MODEL || 'anthropic/claude-3-haiku',
        LLM_CHAT_API_KEY: process.env.LLM_CHAT_API_KEY || '',
        
        // Memory and intelligence
        MEMORY_SYSTEM_TYPE: 'vector',
        ENABLE_CHARACTER_INTELLIGENCE: 'true',
        ENABLE_EMOTIONAL_INTELLIGENCE: 'true',
        
        // Optional Discord configuration
        DISCORD_BOT_TOKEN: '', // Would need to be configured per bot
        ENABLE_DISCORD: 'false'
      }
    }
    
    // Store deployment record in database
    const deploymentQuery = `
      INSERT INTO bot_deployments (character_id, container_name, port, status, config, created_at)
      VALUES ($1, $2, $3, $4, $5, NOW())
      RETURNING *
    `
    
    const deploymentResult = await pool.query(deploymentQuery, [
      character_id,
      containerName,
      portNumber,
      'deploying',
      JSON.stringify(deploymentConfig)
    ])
    
    // Generate Docker run command (for now - later this would use Docker API)
    const dockerCommand = generateDockerRunCommand(deploymentConfig)
    
    try {
      // Execute Docker command to start the container
      const { stdout, stderr } = await execAsync(dockerCommand)
      
      // Update deployment status to running
      await pool.query(
        'UPDATE bot_deployments SET status = $1, deployed_at = NOW() WHERE id = $2',
        ['running', deploymentResult.rows[0].id]
      )
      
      await pool.end()
      
      return NextResponse.json({
        success: true,
        deployment: {
          id: deploymentResult.rows[0].id,
          character_id,
          character_name,
          container_name: containerName,
          port: portNumber,
          endpoint: `http://localhost:${portNumber}`,
          status: 'running',
          health_check_url: `http://localhost:${portNumber}/health`
        },
        docker_output: stdout
      })
      
    } catch (dockerError: any) {
      // Update deployment status to failed
      await pool.query(
        'UPDATE bot_deployments SET status = $1, error_message = $2 WHERE id = $3',
        ['failed', dockerError.message || 'Unknown error', deploymentResult.rows[0].id]
      )
      
      await pool.end()
      
      return NextResponse.json(
        { 
          error: 'Failed to start container',
          deployment_id: deploymentResult.rows[0].id,
          docker_error: dockerError.message || 'Unknown error'
        },
        { status: 500 }
      )
    }
    
  } catch (error: any) {
    console.error('Error deploying bot:', error)
    return NextResponse.json(
      { error: 'Failed to deploy bot', details: error.message || 'Unknown error' },
      { status: 500 }
    )
  }
}

async function getNextAvailablePort(): Promise<number> {
  // Start from 9090 and find the next available port
  let port = 9090
  const maxPort = 9200
  
  while (port <= maxPort) {
    try {
      // Check if port is in use by querying existing deployments
      const pool = new Pool(getDatabaseConfig())
      
      const result = await pool.query('SELECT COUNT(*) FROM bot_deployments WHERE port = $1 AND status IN ($2, $3)', [port, 'running', 'deploying'])
      await pool.end()
      
      if (parseInt(result.rows[0].count) === 0) {
        return port
      }
      
      port++
    } catch (error) {
      port++
    }
  }
  
  throw new Error('No available ports found')
}

function generateDockerRunCommand(config: any): string {
  const { container_name, image, port, environment } = config
  
  let envString = ''
  for (const [key, value] of Object.entries(environment)) {
    envString += ` -e ${key}="${value}"`
  }
  
  return `docker run -d --name ${container_name} --network whisperengine_whisperengine-network -p ${port}:${port}${envString} ${image}`
}

// GET endpoint to list all deployments
export async function GET() {
  try {
    const pool = new Pool(getDatabaseConfig())
    
    const query = `
      SELECT bd.*, c.name as character_name, c.occupation, c.description
      FROM bot_deployments bd
      JOIN characters c ON bd.character_id = c.id
      ORDER BY bd.created_at DESC
    `
    
    const result = await pool.query(query)
    await pool.end()
    
    return NextResponse.json({
      deployments: result.rows.map((row: any) => ({
        id: row.id,
        character_id: row.character_id,
        character_name: row.character_name,
        character_occupation: row.occupation,
        character_description: row.description,
        container_name: row.container_name,
        port: row.port,
        status: row.status,
        endpoint: `http://localhost:${row.port}`,
        health_check_url: `http://localhost:${row.port}/health`,
        created_at: row.created_at,
        deployed_at: row.deployed_at,
        error_message: row.error_message
      }))
    })
    
  } catch (error) {
    console.error('Error getting deployments:', error)
    return NextResponse.json(
      { error: 'Failed to get deployments' },
      { status: 500 }
    )
  }
}