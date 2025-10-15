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
      SELECT id, category, interest_text, proficiency_level, importance, frequency, display_order, created_at
      FROM character_interests 
      WHERE character_id = $1
      ORDER BY display_order ASC, created_at ASC
    `, [characterId])
    
    client.release()
    
    return NextResponse.json(result.rows)
  } catch (error) {
    console.error('Error fetching character interests:', error)
    return NextResponse.json({ error: 'Failed to fetch interests data' }, { status: 500 })
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
    const { entries } = body
    
    const client = await pool.connect()
    
    // Start transaction
    await client.query('BEGIN')
    
    // Delete existing entries
    await client.query('DELETE FROM character_interests WHERE character_id = $1', [characterId])
    
    // Insert new entries
    const insertedEntries = []
    for (let i = 0; i < entries.length; i++) {
      const entry = entries[i]
      const result = await client.query(`
        INSERT INTO character_interests (character_id, category, interest_text, proficiency_level, importance, display_order)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, category, interest_text, proficiency_level, importance, display_order, created_at
      `, [characterId, entry.category, entry.interest_text, entry.proficiency_level, entry.importance, i + 1])
      
      insertedEntries.push(result.rows[0])
    }
    
    // Commit transaction
    await client.query('COMMIT')
    client.release()
    
    return NextResponse.json(insertedEntries)
  } catch (error) {
    console.error('Error updating character interests:', error)
    return NextResponse.json({ error: 'Failed to update interests data' }, { status: 500 })
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  // PUT requests are handled the same as POST for this endpoint
  return POST(request, { params })
}