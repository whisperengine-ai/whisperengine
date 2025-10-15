// Health check API endpoint for Docker container health monitoring
// Returns 200 if the application is running and database is accessible

import { NextResponse } from 'next/server'
import { Pool } from 'pg'
import { getDatabaseConfig } from '@/lib/db'

// Uses environment variables with POSTGRES_* and PG* prefix support for backward compatibility
const pool = new Pool(getDatabaseConfig())

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