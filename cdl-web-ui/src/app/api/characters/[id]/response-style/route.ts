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
    
    // UPDATED CODE - Using correct tables (guidelines and modes)
    // Get response guidelines
    const guidelinesResult = await client.query(`
      SELECT id, guideline_type, guideline_name, guideline_content, priority, context, is_critical, created_date
      FROM character_response_guidelines 
      WHERE character_id = $1
      ORDER BY priority ASC, guideline_type, guideline_name
    `, [characterId])
    
    // Get response modes
    const modesResult = await client.query(`
      SELECT id, mode_name, mode_description, response_style, length_guideline, tone_adjustment, conflict_resolution_priority, examples
      FROM character_response_modes
      WHERE character_id = $1
      ORDER BY conflict_resolution_priority ASC, mode_name
    `, [characterId])
    
    const responseStyle = {
      guidelines: guidelinesResult.rows,
      modes: modesResult.rows,
      // Legacy format for component compatibility
      items: guidelinesResult.rows.map((guideline, index) => ({
        id: guideline.id,
        item_type: guideline.guideline_type,
        item_text: guideline.guideline_content,
        sort_order: guideline.priority || index + 1
      }))
    }
    
    client.release()
    
    return NextResponse.json(responseStyle)
  } catch (error) {
    console.error('Error fetching response style:', error)
    return NextResponse.json({ error: 'Failed to fetch response style' }, { status: 500 })
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
    const { guidelines, modes } = body
    
    const client = await pool.connect()
    
    // Start transaction
    await client.query('BEGIN')
    
    // Update guidelines if provided
    if (guidelines) {
      // Delete existing guidelines
      await client.query('DELETE FROM character_response_guidelines WHERE character_id = $1', [characterId])
      
      // Insert new guidelines
      for (const guideline of guidelines) {
        await client.query(`
          INSERT INTO character_response_guidelines 
          (character_id, guideline_type, guideline_name, guideline_content, priority, context, is_critical)
          VALUES ($1, $2, $3, $4, $5, $6, $7)
        `, [
          characterId,
          guideline.guideline_type || 'general',
          guideline.guideline_name,
          guideline.guideline_content,
          guideline.priority || 1,
          guideline.context,
          guideline.is_critical || false
        ])
      }
    }
    
    // Update modes if provided  
    if (modes) {
      // Delete existing modes
      await client.query('DELETE FROM character_response_modes WHERE character_id = $1', [characterId])
      
      // Insert new modes
      for (const mode of modes) {
        await client.query(`
          INSERT INTO character_response_modes
          (character_id, mode_name, mode_description, response_style, length_guideline, tone_adjustment, conflict_resolution_priority, examples)
          VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        `, [
          characterId,
          mode.mode_name,
          mode.mode_description,
          mode.response_style,
          mode.length_guideline,
          mode.tone_adjustment,
          mode.conflict_resolution_priority || 1,
          mode.examples
        ])
      }
    }
    
    // Commit transaction
    await client.query('COMMIT')
    client.release()
    
    return NextResponse.json({ message: 'Response style updated successfully' })
  } catch (error) {
    console.error('Error updating response style:', error)
    return NextResponse.json({ error: 'Failed to update response style' }, { status: 500 })
  }
}