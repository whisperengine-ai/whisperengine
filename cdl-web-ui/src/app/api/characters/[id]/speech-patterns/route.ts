import { NextRequest, NextResponse } from 'next/server'
import { Pool } from 'pg'

const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5433'),
  database: process.env.POSTGRES_DB || 'whisperengine',
  user: process.env.POSTGRES_USER || 'whisperengine',
  password: process.env.POSTGRES_PASSWORD || 'whisperengine_pass',
})

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  const resolvedParams = await params
  const characterId = parseInt(resolvedParams.id)
  
  try {
    const client = await pool.connect()
    
    const result = await client.query(`
      SELECT id, pattern_type, pattern_value, usage_frequency, context, priority
      FROM character_speech_patterns 
      WHERE character_id = $1
      ORDER BY priority DESC, pattern_type
    `, [characterId])
    
    client.release()
    
    return NextResponse.json(result.rows)
  } catch (error) {
    console.error('Error fetching speech patterns:', error)
    return NextResponse.json({ error: 'Failed to fetch speech patterns' }, { status: 500 })
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const resolvedParams = await params
  const characterId = parseInt(resolvedParams.id)
  
  try {
    const body = await request.json()
    const { patterns } = body
    
    const client = await pool.connect()
    
    // Start transaction
    await client.query('BEGIN')
    
    // Delete existing patterns
    await client.query('DELETE FROM character_speech_patterns WHERE character_id = $1', [characterId])
    
    // Insert new patterns
    const insertedPatterns = []
    for (const pattern of patterns) {
      const result = await client.query(`
        INSERT INTO character_speech_patterns (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, pattern_type, pattern_value, usage_frequency, context, priority
      `, [characterId, pattern.pattern_type, pattern.pattern_value, pattern.usage_frequency, pattern.context, pattern.priority])
      
      insertedPatterns.push(result.rows[0])
    }
    
    // Commit transaction
    await client.query('COMMIT')
    client.release()
    
    return NextResponse.json(insertedPatterns)
  } catch (error) {
    console.error('Error updating speech patterns:', error)
    return NextResponse.json({ error: 'Failed to update speech patterns' }, { status: 500 })
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  // PUT method does the same as POST for speech patterns (replace all)
  return POST(request, { params })
}