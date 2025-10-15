import { NextRequest, NextResponse } from 'next/server'
import { getCharacterById } from '@/lib/db'
import { Pool } from 'pg'
import * as yaml from 'js-yaml'

const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5433'),
  database: process.env.POSTGRES_DB || 'whisperengine',
  user: process.env.POSTGRES_USER || 'whisperengine',
  password: process.env.POSTGRES_PASSWORD || 'whisperengine_pass',
})

interface PageProps {
  params: Promise<{
    id: string
  }>
}

export async function GET(request: NextRequest, { params }: PageProps) {
  try {
    const resolvedParams = await params
    const characterId = parseInt(resolvedParams.id)
    
    if (isNaN(characterId)) {
      return NextResponse.json({
        success: false,
        error: 'Invalid character ID'
      }, { status: 400 })
    }

    const character = await getCharacterById(characterId)
    
    if (!character) {
      return NextResponse.json({
        success: false,
        error: 'Character not found'
      }, { status: 404 })
    }

    const client = await pool.connect()

    try {
      // Fetch all related data from different tables
      const [
        backgroundRows,
        interestsRows,
        communicationRows,
        speechRows,
        responseStyleRows,
        personalityRows,
        valuesRows
      ] = await Promise.all([
        // Background data
        client.query(`
          SELECT id, category, period, title, description, date_range, importance_level
          FROM character_background 
          WHERE character_id = $1
          ORDER BY importance_level DESC
        `, [characterId]),
        
        // Interests data  
        client.query(`
          SELECT id, category, interest_text, proficiency_level, importance, created_at
          FROM character_interests
          WHERE character_id = $1
          ORDER BY created_at ASC
        `, [characterId]),
        
        // Communication patterns
        client.query(`
          SELECT id, pattern_type, pattern_name, pattern_value, context, frequency
          FROM character_communication_patterns
          WHERE character_id = $1
        `, [characterId]),
        
        // Speech patterns
        client.query(`
          SELECT id, pattern_type, pattern_value, usage_frequency, context, priority
          FROM character_speech_patterns
          WHERE character_id = $1
          ORDER BY priority DESC
        `, [characterId]),
        
        // Response style guidelines
        client.query(`
          SELECT crg.id, crg.guideline_type as item_type, crg.guideline_content as item_text, 
                 crg.priority as sort_order
          FROM character_response_guidelines crg
          WHERE crg.character_id = $1
          ORDER BY crg.priority DESC
        `, [characterId]),
        
        // Personality traits (for Big Five)
        client.query(`
          SELECT trait_name, trait_value, intensity, description
          FROM personality_traits 
          WHERE character_id = $1
        `, [characterId]),
        
        // Character values
        client.query(`
          SELECT value_key, value_description, importance_level, category
          FROM character_values 
          WHERE character_id = $1
          ORDER BY importance_level DESC
        `, [characterId])
      ])

      // Build comprehensive YAML structure matching form fields
      const yamlStructure: any = {
        name: character.name,
        identity: {
          name: character.name,
          occupation: character.occupation,
          description: character.description,
          archetype: character.archetype || 'real-world',
          allow_full_roleplay_immersion: character.allow_full_roleplay || false
        },
        metadata: {
          database_id: character.id,
          normalized_name: character.normalized_name,
          export_date: new Date().toISOString(),
          created_at: character.created_at,
          updated_at: character.updated_at,
          is_active: character.is_active,
          schema_version: '2.0',
          source: 'whisperengine_cdl_web_ui_comprehensive'
        }
      }

      // Add personality data (Big Five + values)
      if (personalityRows.rows.length > 0 || valuesRows.rows.length > 0) {
        yamlStructure.personality = {}
        
        // Big Five traits
        const bigFive: any = {}
        const bigFiveNames = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        
        personalityRows.rows.forEach(row => {
          if (bigFiveNames.includes(row.trait_name.toLowerCase())) {
            bigFive[row.trait_name.toLowerCase()] = row.trait_value || 0.5
          }
        })
        
        if (Object.keys(bigFive).length > 0) {
          yamlStructure.personality.big_five = bigFive
        }
        
        // Values
        if (valuesRows.rows.length > 0) {
          yamlStructure.personality.values = valuesRows.rows.map(row => 
            row.value_description || row.value_key
          )
        }
      }

      // Add background entries
      if (backgroundRows.rows.length > 0) {
        yamlStructure.background = {
          entries: backgroundRows.rows.map(row => ({
            id: row.id,
            category: row.category,
            title: row.title,
            description: row.description,
            period: row.period,
            importance_level: row.importance_level
          }))
        }
      }

      // Add interests
      if (interestsRows.rows.length > 0) {
        yamlStructure.interests = {
          entries: interestsRows.rows.map(row => ({
            id: row.id,
            category: row.category,
            interest_text: row.interest_text,
            proficiency_level: row.proficiency_level,
            importance: row.importance
          }))
        }
      }

      // Add communication patterns
      if (communicationRows.rows.length > 0) {
        yamlStructure.communication_patterns = {
          patterns: communicationRows.rows.map(row => ({
            id: row.id,
            pattern_type: row.pattern_type,
            pattern_name: row.pattern_name,
            pattern_value: row.pattern_value,
            context: row.context,
            frequency: row.frequency
          }))
        }
      }

      // Add speech patterns
      if (speechRows.rows.length > 0) {
        yamlStructure.speech_patterns = {
          patterns: speechRows.rows.map(row => ({
            id: row.id,
            pattern_type: row.pattern_type,
            pattern_value: row.pattern_value,
            usage_frequency: row.usage_frequency,
            context: row.context,
            priority: row.priority
          }))
        }
      }

      // Add response style
      if (responseStyleRows.rows.length > 0) {
        yamlStructure.response_style = {
          items: responseStyleRows.rows.map(row => ({
            id: row.id,
            item_type: row.item_type,
            item_text: row.item_text,
            sort_order: row.sort_order
          }))
        }
      }

      // Add any existing CDL data for backward compatibility
      if (character.cdl_data) {
        yamlStructure.legacy_cdl_data = character.cdl_data
      }

      // Remove null/undefined values
      const cleanStructure = JSON.parse(JSON.stringify(yamlStructure, (key, value) => 
        value === null || value === undefined ? undefined : value
      ))

      // Convert to YAML
      const yamlContent = yaml.dump(cleanStructure, {
        indent: 2,
        lineWidth: 120,
        noRefs: true,
        sortKeys: false
      })

      // Return YAML file as download
      const filename = `${character.normalized_name || character.name.toLowerCase().replace(/[^a-z0-9]/g, '_')}_complete.yaml`
      
      return new NextResponse(yamlContent, {
        status: 200,
        headers: {
          'Content-Type': 'application/x-yaml',
          'Content-Disposition': `attachment; filename="${filename}"`,
          'Cache-Control': 'no-cache'
        }
      })

    } finally {
      client.release()
    }

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    const errorStack = error instanceof Error ? error.stack : undefined
    
    console.error('Character YAML export error:', error)
    
    return NextResponse.json({
      success: false,
      error: errorMessage,
      stack: errorStack
    }, { status: 500 })
  }
}