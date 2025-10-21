import { NextRequest, NextResponse } from 'next/server'
import { getPool, withClient, withTransaction } from '@/lib/db-pool'

const pool = getPool()

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  const resolvedParams = await params
  const characterId = parseInt(resolvedParams.id)
  
  try {
    const rows = await withClient(pool, async (client) => {
      const result = await client.query(`
        SELECT id, category, period, title, description, date_range, importance_level, created_date
        FROM character_background 
        WHERE character_id = $1
        ORDER BY importance_level DESC, created_date ASC
      `, [characterId])
      
      return result.rows
    })
    
    return NextResponse.json(rows)
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
    
    const row = await withClient(pool, async (client) => {
      const result = await client.query(`
        INSERT INTO character_background (character_id, category, period, title, description, importance_level)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, category, period, title, description, importance_level, created_date
      `, [characterId, category, period, title, description, importance_level])
      
      return result.rows[0]
    })
    
    return NextResponse.json(row)
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
    
    const insertedEntries = await withTransaction(pool, async (client) => {
      // Delete existing entries
      await client.query('DELETE FROM character_background WHERE character_id = $1', [characterId])
      
      // Insert new entries
      const results = []
      for (const entry of entries) {
        const result = await client.query(`
          INSERT INTO character_background (character_id, category, period, title, description, importance_level)
          VALUES ($1, $2, $3, $4, $5, $6)
          RETURNING id, category, period, title, description, importance_level, created_date
        `, [characterId, entry.category, entry.period, entry.title, entry.description, entry.importance_level])
        
        results.push(result.rows[0])
      }
      
      return results
    })
    
    return NextResponse.json(insertedEntries)
  } catch (error) {
    console.error('Error updating character background:', error)
    return NextResponse.json({ error: 'Failed to update background data' }, { status: 500 })
  }
}