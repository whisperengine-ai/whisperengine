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
      SELECT id, category, period, title, description, date_range, importance_level, created_date
      FROM character_background 
      WHERE character_id = $1
      ORDER BY importance_level DESC, created_date ASC
    `, [characterId])
    
    client.release()
    
    return NextResponse.json(result.rows)
  } catch (error) {
    console.error('Error fetching character background:', error)
    return NextResponse.json({ error: 'Failed to fetch background data' }, { status: 500 })
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
    const { category, period, title, description, importance_level } = body
    
    const client = await pool.connect()
    
    const result = await client.query(`
      INSERT INTO character_background (character_id, category, period, title, description, importance_level)
      VALUES ($1, $2, $3, $4, $5, $6)
      RETURNING id, category, period, title, description, importance_level, created_date
    `, [characterId, category, period, title, description, importance_level])
    
    client.release()
    
    return NextResponse.json(result.rows[0])
  } catch (error) {
    console.error('Error creating character background:', error)
    return NextResponse.json({ error: 'Failed to create background entry' }, { status: 500 })
  }
}

export async function PUT(
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
    await client.query('DELETE FROM character_background WHERE character_id = $1', [characterId])
    
    // Insert new entries
    const insertedEntries = []
    for (const entry of entries) {
      const result = await client.query(`
        INSERT INTO character_background (character_id, category, period, title, description, importance_level)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, category, period, title, description, importance_level, created_date
      `, [characterId, entry.category, entry.period, entry.title, entry.description, entry.importance_level])
      
      insertedEntries.push(result.rows[0])
    }
    
    // Commit transaction
    await client.query('COMMIT')
    client.release()
    
    return NextResponse.json(insertedEntries)
  } catch (error) {
    console.error('Error updating character background:', error)
    return NextResponse.json({ error: 'Failed to update background data' }, { status: 500 })
  }
}