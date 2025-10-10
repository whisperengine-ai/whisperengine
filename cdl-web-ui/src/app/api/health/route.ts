// Health check API endpoint for Docker container health monitoring
// Returns 200 if the application is running and database is accessible

import { NextResponse } from 'next/server'
import { Pool } from 'pg'

const pool = new Pool({
  host: process.env.PGHOST || 'localhost',
  port: parseInt(process.env.PGPORT || '5432'),
  database: process.env.PGDATABASE || 'whisperengine',
  user: process.env.PGUSER || 'whisperengine',
  password: process.env.PGPASSWORD || 'whisperengine_password',
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