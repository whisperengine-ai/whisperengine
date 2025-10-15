import { NextRequest, NextResponse } from 'next/server'
import { Pool } from 'pg'
import * as yaml from 'js-yaml'

const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5433'),
  database: process.env.POSTGRES_DB || 'whisperengine',
  user: process.env.POSTGRES_USER || 'whisperengine',
  password: process.env.POSTGRES_PASSWORD || 'whisperengine_pass',
})

interface YAMLCharacterData {
  name: string
  identity: {
    name: string
    occupation?: string
    description?: string
    archetype?: string
    allow_full_roleplay_immersion?: boolean
  }
  personality?: {
    big_five?: {
      openness?: number
      conscientiousness?: number
      extraversion?: number
      agreeableness?: number
      neuroticism?: number
    }
    values?: string[]
  }
  background?: {
    entries?: Array<{
      category: string
      title: string
      description: string
      period?: string
      importance_level: number
    }>
  }
  interests?: {
    entries?: Array<{
      category: string
      interest_text: string
      proficiency_level: number
      importance: string
    }>
  }
  communication_patterns?: {
    patterns?: Array<{
      pattern_type: string
      pattern_name: string
      pattern_value: string
      context?: string
      frequency: string
    }>
  }
  speech_patterns?: {
    patterns?: Array<{
      pattern_type: string
      pattern_value: string
      usage_frequency: string
      context?: string
      priority: number
    }>
  }
  response_style?: {
    items?: Array<{
      item_type: string
      item_text: string
      sort_order: number
    }>
  }
  metadata?: {
    normalized_name?: string
    [key: string]: any
  }
}

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const yamlFile = formData.get('yamlFile') as File
    const overwrite = formData.get('overwrite') === 'true'

    if (!yamlFile) {
      return NextResponse.json({
        success: false,
        error: 'No YAML file provided'
      }, { status: 400 })
    }

    // Read and parse YAML
    const yamlContent = await yamlFile.text()
    let yamlData: YAMLCharacterData
    
    try {
      yamlData = yaml.load(yamlContent) as YAMLCharacterData
    } catch (error) {
      return NextResponse.json({
        success: false,
        error: 'Invalid YAML format: ' + (error instanceof Error ? error.message : 'Unknown error')
      }, { status: 400 })
    }

    if (!yamlData || !yamlData.identity?.name) {
      return NextResponse.json({
        success: false,
        error: 'Invalid YAML structure: missing identity.name'
      }, { status: 400 })
    }

    const client = await pool.connect()

    try {
      await client.query('BEGIN')

      const characterName = yamlData.identity.name
      const normalizedName = yamlData.metadata?.normalized_name || 
        characterName.toLowerCase().replace(/[^a-z0-9]/g, '_')

      // Check if character exists
      const existingResult = await client.query(
        'SELECT id FROM characters WHERE LOWER(normalized_name) = LOWER($1)',
        [normalizedName]
      )

      let characterId: number

      if (existingResult.rows.length > 0) {
        if (!overwrite) {
          await client.query('ROLLBACK')
          return NextResponse.json({
            success: false,
            error: `Character '${characterName}' already exists. Set overwrite=true to replace.`
          }, { status: 409 })
        }

        characterId = existingResult.rows[0].id
        
        // Update existing character
        await client.query(`
          UPDATE characters 
          SET name = $1, occupation = $2, description = $3, archetype = $4, 
              allow_full_roleplay = $5, updated_at = NOW()
          WHERE id = $6
        `, [
          characterName,
          yamlData.identity.occupation,
          yamlData.identity.description,
          yamlData.identity.archetype || 'real-world',
          yamlData.identity.allow_full_roleplay_immersion || false,
          characterId
        ])

        // Clear existing related data
        await Promise.all([
          client.query('DELETE FROM character_background WHERE character_id = $1', [characterId]),
          client.query('DELETE FROM character_interest_topics WHERE character_id = $1', [characterId]),
          client.query('DELETE FROM character_communication_patterns WHERE character_id = $1', [characterId]),
          client.query('DELETE FROM character_speech_patterns WHERE character_id = $1', [characterId]),
          client.query('DELETE FROM character_response_guidelines WHERE character_id = $1', [characterId]),
          client.query('DELETE FROM personality_traits WHERE character_id = $1', [characterId]),
          client.query('DELETE FROM character_values WHERE character_id = $1', [characterId])
        ])

      } else {
        // Create new character
        const insertResult = await client.query(`
          INSERT INTO characters (name, normalized_name, occupation, description, archetype, allow_full_roleplay, is_active)
          VALUES ($1, $2, $3, $4, $5, $6, true)
          RETURNING id
        `, [
          characterName,
          normalizedName,
          yamlData.identity.occupation,
          yamlData.identity.description,
          yamlData.identity.archetype || 'real-world',
          yamlData.identity.allow_full_roleplay_immersion || false
        ])

        characterId = insertResult.rows[0].id
      }

      // Import personality data (Big Five)
      if (yamlData.personality?.big_five) {
        const bigFive = yamlData.personality.big_five
        for (const [traitName, value] of Object.entries(bigFive)) {
          if (typeof value === 'number') {
            await client.query(`
              INSERT INTO personality_traits (character_id, trait_name, trait_value, intensity)
              VALUES ($1, $2, $3, $4)
            `, [characterId, traitName, value, 'medium'])
          }
        }
      }

      // Import values
      if (yamlData.personality?.values) {
        for (let i = 0; i < yamlData.personality.values.length; i++) {
          const value = yamlData.personality.values[i]
          await client.query(`
            INSERT INTO character_values (character_id, value_key, value_description, importance_level)
            VALUES ($1, $2, $3, $4)
          `, [characterId, `value_${i + 1}`, value, 5])
        }
      }

      // Import background entries
      if (yamlData.background?.entries) {
        for (const entry of yamlData.background.entries) {
          await client.query(`
            INSERT INTO character_background (character_id, category, period, title, description, importance_level)
            VALUES ($1, $2, $3, $4, $5, $6)
          `, [
            characterId,
            entry.category,
            entry.period,
            entry.title,
            entry.description,
            entry.importance_level
          ])
        }
      }

      // Import interests
      if (yamlData.interests?.entries) {
        for (const entry of yamlData.interests.entries) {
          await client.query(`
            INSERT INTO character_interest_topics (character_id, category, interest_text, proficiency_level, importance)
            VALUES ($1, $2, $3, $4, $5)
          `, [
            characterId,
            entry.category,
            entry.interest_text,
            entry.proficiency_level,
            entry.importance
          ])
        }
      }

      // Import communication patterns
      if (yamlData.communication_patterns?.patterns) {
        for (const pattern of yamlData.communication_patterns.patterns) {
          await client.query(`
            INSERT INTO character_communication_patterns (character_id, pattern_type, pattern_name, pattern_value, context, frequency)
            VALUES ($1, $2, $3, $4, $5, $6)
          `, [
            characterId,
            pattern.pattern_type,
            pattern.pattern_name,
            pattern.pattern_value,
            pattern.context,
            pattern.frequency
          ])
        }
      }

      // Import speech patterns
      if (yamlData.speech_patterns?.patterns) {
        for (const pattern of yamlData.speech_patterns.patterns) {
          await client.query(`
            INSERT INTO character_speech_patterns (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
            VALUES ($1, $2, $3, $4, $5, $6)
          `, [
            characterId,
            pattern.pattern_type,
            pattern.pattern_value,
            pattern.usage_frequency,
            pattern.context,
            pattern.priority
          ])
        }
      }

      // Import response style items
      if (yamlData.response_style?.items) {
        for (const item of yamlData.response_style.items) {
          await client.query(`
            INSERT INTO character_response_guidelines (character_id, guideline_type, guideline_content, priority)
            VALUES ($1, $2, $3, $4)
          `, [
            characterId,
            item.item_type,
            item.item_text,
            item.sort_order
          ])
        }
      }

      await client.query('COMMIT')

      return NextResponse.json({
        success: true,
        message: `Character '${characterName}' imported successfully`,
        characterId,
        action: existingResult.rows.length > 0 ? 'updated' : 'created'
      })

    } catch (error) {
      await client.query('ROLLBACK')
      throw error
    } finally {
      client.release()
    }

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    const errorStack = error instanceof Error ? error.stack : undefined
    
    console.error('Character YAML import error:', error)
    
    return NextResponse.json({
      success: false,
      error: errorMessage,
      stack: errorStack
    }, { status: 500 })
  }
}