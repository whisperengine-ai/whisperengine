import { NextRequest, NextResponse } from 'next/server'
import { Pool } from 'pg'
import { getDatabaseConfig } from '@/lib/db'

const pool = new Pool(getDatabaseConfig())

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  const resolvedParams = await params
  const characterId = parseInt(resolvedParams.id)
  
  try {
    const client = await pool.connect()
    
    const result = await client.query(`
      SELECT id, pattern_type, pattern_name, pattern_value, context, frequency, description
      FROM character_communication_patterns 
      WHERE character_id = $1
      ORDER BY pattern_type, pattern_name
    `, [characterId])
    
    client.release()
    
    return NextResponse.json(result.rows)
  } catch (error) {
    console.error('Error fetching communication patterns:', error)
    return NextResponse.json({ error: 'Failed to fetch communication patterns' }, { status: 500 })
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
    await client.query('DELETE FROM character_communication_patterns WHERE character_id = $1', [characterId])
    
    // Insert new patterns
    const insertedPatterns = []
    for (const pattern of patterns) {
      const result = await client.query(`
        INSERT INTO character_communication_patterns (character_id, pattern_type, pattern_name, pattern_value, context, frequency)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, pattern_type, pattern_name, pattern_value, context, frequency
      `, [characterId, pattern.pattern_type, pattern.pattern_name, pattern.pattern_value, pattern.context, pattern.frequency])
      
      insertedPatterns.push(result.rows[0])
    }
    
    // Commit transaction
    await client.query('COMMIT')
    client.release()
    
    return NextResponse.json(insertedPatterns)
  } catch (error) {
    console.error('Error updating communication patterns:', error)
    return NextResponse.json({ error: 'Failed to update communication patterns' }, { status: 500 })
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  // PUT requests are handled the same as POST for this endpoint
  return POST(request, { params })
}