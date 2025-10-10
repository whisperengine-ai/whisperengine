// Health check API endpoint for Docker container health monitoring
// Returns 200 if the application is running and database is accessible

import { NextResponse } from 'next/server'
import { Pool } from 'pg'

// Uses same environment variables as main WhisperEngine app (no PG* prefix)
const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  database: process.env.POSTGRES_DB || 'whisperengine',
  user: process.env.POSTGRES_USER || 'whisperengine',
  password: process.env.POSTGRES_PASSWORD || 'whisperengine_password',
})

export async function GET() {
  try {
    // Test database connection
    const client = await pool.connect()
    await client.query('SELECT 1')
    client.release()
    
    return NextResponse.json({ 
      status: 'healthy',
      timestamp: new Date().toISOString(),
      database: 'connected'
    })
  } catch (error) {
    return NextResponse.json(
      { 
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        database: 'disconnected',
        error: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}