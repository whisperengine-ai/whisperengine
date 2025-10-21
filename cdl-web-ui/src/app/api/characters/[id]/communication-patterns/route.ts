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
        SELECT id, pattern_type, pattern_name, pattern_value, context, frequency, description
        FROM character_communication_patterns 
        WHERE character_id = $1
        ORDER BY pattern_type, pattern_name
      `, [characterId])
      
      return result.rows
    })
    
    return NextResponse.json(rows)
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
    
    const insertedPatterns = await withTransaction(pool, async (client) => {
      // Delete existing patterns
      await client.query('DELETE FROM character_communication_patterns WHERE character_id = $1', [characterId])
      
      // Insert new patterns
      const results = []
      for (const pattern of patterns) {
        const result = await client.query(`
          INSERT INTO character_communication_patterns (character_id, pattern_type, pattern_name, pattern_value, context, frequency)
          VALUES ($1, $2, $3, $4, $5, $6)
          RETURNING id, pattern_type, pattern_name, pattern_value, context, frequency
        `, [characterId, pattern.pattern_type, pattern.pattern_name, pattern.pattern_value, pattern.context, pattern.frequency])
        
        results.push(result.rows[0])
      }
      
      return results
    })
    
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