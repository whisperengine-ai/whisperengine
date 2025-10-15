import { NextRequest, NextResponse } from 'next/server'
import { Pool } from 'pg'
import { getDatabaseConfig } from '@/lib/db'

export async function POST(request: NextRequest) {
  try {
    const { sourceCharacterId, newName } = await request.json()
    
    if (!sourceCharacterId || !newName) {
      return NextResponse.json(
        { success: false, message: 'Source character ID and new name are required' },
        { status: 400 }
      )
    }

    const pool = new Pool(getDatabaseConfig())

    const client = await pool.connect()
    
    try {
      await client.query('BEGIN')

      // Get the source character
      const sourceCharacterResult = await client.query(
        'SELECT * FROM characters WHERE id = $1',
        [sourceCharacterId]
      )

      if (sourceCharacterResult.rows.length === 0) {
        await client.query('ROLLBACK')
        return NextResponse.json(
          { success: false, message: 'Source character not found' },
          { status: 404 }
        )
      }

      const sourceCharacter = sourceCharacterResult.rows[0]
      const normalizedName = newName.toLowerCase().replace(/[^a-z0-9]/g, '_')

      // Create the new character
      const newCharacterResult = await client.query(
        `INSERT INTO characters (name, normalized_name, occupation, description, archetype, allow_full_roleplay, is_active, created_at, updated_at) 
         VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) 
         RETURNING id, name, normalized_name, occupation, description, archetype, allow_full_roleplay, is_active, created_at, updated_at`,
        [
          newName.trim(),
          normalizedName,
          sourceCharacter.occupation,
          sourceCharacter.description,
          sourceCharacter.archetype,
          sourceCharacter.allow_full_roleplay,
          true
        ]
      )

      const newCharacterId = newCharacterResult.rows[0].id

      // Clone personality traits
      const personalityTraits = await client.query(
        'SELECT trait_name, trait_value, intensity, description FROM personality_traits WHERE character_id = $1',
        [sourceCharacterId]
      )

      for (const trait of personalityTraits.rows) {
        await client.query(
          'INSERT INTO personality_traits (character_id, trait_name, trait_value, intensity, description) VALUES ($1, $2, $3, $4, $5)',
          [newCharacterId, trait.trait_name, trait.trait_value, trait.intensity, trait.description]
        )
      }

      // Clone communication styles
      const commStyles = await client.query(
        'SELECT engagement_level, formality, emotional_expression, response_length, conversation_flow_guidance, ai_identity_handling FROM communication_styles WHERE character_id = $1',
        [sourceCharacterId]
      )

      for (const style of commStyles.rows) {
        await client.query(
          'INSERT INTO communication_styles (character_id, engagement_level, formality, emotional_expression, response_length, conversation_flow_guidance, ai_identity_handling) VALUES ($1, $2, $3, $4, $5, $6, $7)',
          [newCharacterId, style.engagement_level, style.formality, style.emotional_expression, style.response_length, style.conversation_flow_guidance, style.ai_identity_handling]
        )
      }

      // Clone character values
      const characterValues = await client.query(
        'SELECT value_key, value_description, importance_level, category FROM character_values WHERE character_id = $1',
        [sourceCharacterId]
      )

      for (const value of characterValues.rows) {
        await client.query(
          'INSERT INTO character_values (character_id, value_key, value_description, importance_level, category) VALUES ($1, $2, $3, $4, $5)',
          [newCharacterId, value.value_key, value.value_description, value.importance_level, value.category]
        )
      }

      await client.query('COMMIT')

      const newCharacter = {
        id: newCharacterId,
        ...newCharacterResult.rows[0],
        bot_name: normalizedName
      }

      return NextResponse.json({
        success: true,
        message: `Character "${newName}" cloned successfully`,
        character: newCharacter
      })

    } finally {
      client.release()
      await pool.end()
    }

  } catch (error) {
    console.error('Error cloning character:', error)
    return NextResponse.json(
      { success: false, message: 'Failed to clone character' },
      { status: 500 }
    )
  }
}