import { NextRequest, NextResponse } from 'next/server'
import { createCharacter, getDatabaseConfig } from '@/lib/db'
import * as yaml from 'js-yaml'
import { Pool } from 'pg'

const pool = new Pool(getDatabaseConfig())

// Helper function to create character within existing transaction
async function createCharacterWithinTransaction(client: any, characterData: any) {
  // Generate a unique normalized name
  let baseNormalizedName = characterData.name?.toLowerCase().replace(/[^a-z0-9]/g, '_') || '';
  let normalizedName = characterData.normalized_name || baseNormalizedName;
  let counter = 1;
  
  // Check for existing normalized names and add a counter if needed
  while (true) {
    const existingResult = await client.query(
      'SELECT id FROM characters WHERE normalized_name = $1',
      [normalizedName]
    );
    
    if (existingResult.rows.length === 0) {
      break; // Name is unique
    }
    
    normalizedName = `${baseNormalizedName}_${counter}`;
    counter++;
  }
  
  // Insert main character record
  const characterResult = await client.query(
    `INSERT INTO characters (name, normalized_name, occupation, description, archetype, allow_full_roleplay, is_active, created_at, updated_at) 
     VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) 
     RETURNING id, name, normalized_name, occupation, description, archetype, allow_full_roleplay, is_active, created_at, updated_at`,
    [
      characterData.name,
      normalizedName,
      characterData.occupation || null,
      characterData.description || null,
      characterData.archetype || 'real-world',
      characterData.allow_full_roleplay || false,
      true
    ]
  );

  const characterId = parseInt(characterResult.rows[0].id);
  const row = characterResult.rows[0];

  return {
    id: characterId,
    name: row.name,
    normalized_name: row.normalized_name,
    occupation: row.occupation,
    description: row.description,
    archetype: row.archetype,
    allow_full_roleplay: row.allow_full_roleplay,
    is_active: row.is_active,
    created_at: row.created_at,
    updated_at: row.updated_at
  };
}

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File
    
    if (!file) {
      return NextResponse.json({
        success: false,
        error: 'No file provided'
      }, { status: 400 })
    }

    // Read file content
    const fileContent = await file.text()
    
    // Parse YAML
    let yamlDataUnknown: unknown
    try {
      yamlDataUnknown = yaml.load(fileContent)
    } catch (yamlError) {
      return NextResponse.json({
        success: false,
        error: 'Invalid YAML format',
        details: yamlError instanceof Error ? yamlError.message : 'Unknown YAML error'
      }, { status: 400 })
    }

    // Basic shape validation
    if (typeof yamlDataUnknown !== 'object' || yamlDataUnknown === null) {
      return NextResponse.json({
        success: false,
        error: 'Invalid YAML structure'
      }, { status: 400 })
    }

    const yamlData = yamlDataUnknown as Record<string, unknown>

    // Validate required fields
    const nameVal = yamlData.name
    if (typeof nameVal !== 'string' || !nameVal) {
      return NextResponse.json({
        success: false,
        error: 'Missing required field: name'
      }, { status: 400 })
    }

    const metadata = (yamlData.metadata && typeof yamlData.metadata === 'object')
      ? (yamlData.metadata as Record<string, unknown>)
      : undefined
    const identity = (yamlData.identity && typeof yamlData.identity === 'object')
      ? (yamlData.identity as Record<string, unknown>)
      : undefined

    const getString = (obj: Record<string, unknown> | undefined, key: string): string | undefined => {
      const v = obj?.[key]
      return typeof v === 'string' ? v : undefined
    }
    const getBoolean = (obj: Record<string, unknown> | undefined, key: string): boolean | undefined => {
      const v = obj?.[key]
      return typeof v === 'boolean' ? v : undefined
    }
    const getObject = (v: unknown): Record<string, unknown> => (typeof v === 'object' && v !== null ? (v as Record<string, unknown>) : {})
    const getArray = (v: unknown): unknown[] => (Array.isArray(v) ? v : [])

    type Archetype = 'real-world' | 'fantasy' | 'narrative-ai'
    const getArchetype = (val: unknown): Archetype => {
      if (val === 'fantasy' || val === 'narrative-ai' || val === 'real-world') return val
      return 'real-world'
    }

    // Convert YAML structure to database format
    const characterData = {
      name: nameVal,
      normalized_name: getString(metadata, 'normalized_name') || nameVal.toLowerCase().replace(/[^a-z0-9]/g, '_'),
      occupation: getString(identity, 'occupation') || null,
      description: getString(identity, 'description') || null,
  archetype: getArchetype(getString(identity, 'archetype')),
      allow_full_roleplay: getBoolean(identity, 'allow_full_roleplay_immersion') ?? false,
      cdl_data: {
        identity: identity || {},
        personality: getObject(yamlData.personality),
        communication: getObject(yamlData.communication),
        values: getArray(yamlData.values),
        interests: getArray(yamlData.interests),
        background: getObject(yamlData.background),
        speech_patterns: getObject(yamlData.speech_patterns),
        personal_knowledge: getObject(yamlData.personal_knowledge),
        roleplay_config: getObject(yamlData.roleplay_config),
        metadata: {
          ...(metadata || {}),
          import_date: new Date().toISOString(),
          import_source: 'yaml_file',
          original_filename: file.name
        }
      }
    }

    // Start a single transaction for entire import operation
    const client = await pool.connect()
    let character: any = null
    
    try {
      await client.query('BEGIN')
      
      // Create character in database within the transaction
      character = await createCharacterWithinTransaction(client, characterData)
      
      // Import background entries
      const backgroundData = yamlData.background as Record<string, unknown> | undefined
      if (backgroundData && Array.isArray(backgroundData.entries)) {
        for (const entry of backgroundData.entries) {
          if (typeof entry === 'object' && entry !== null) {
            const bgEntry = entry as Record<string, unknown>
            await client.query(`
              INSERT INTO character_background (character_id, category, period, title, description, importance_level)
              VALUES ($1, $2, $3, $4, $5, $6)
            `, [
              character.id,
              getString(bgEntry, 'category') || 'General',
              getString(bgEntry, 'period') || getString(bgEntry, 'timeframe') || null,
              getString(bgEntry, 'title') || null,
              getString(bgEntry, 'description') || getString(bgEntry, 'content') || null,
              typeof bgEntry.importance_level === 'number' ? bgEntry.importance_level : 5
            ])
          }
        }
      }
      
      // Import interests
      const interestsData = yamlData.interests as Record<string, unknown> | undefined
      if (interestsData && Array.isArray(interestsData.entries)) {
        for (const entry of interestsData.entries) {
          if (typeof entry === 'object' && entry !== null) {
            const interestEntry = entry as Record<string, unknown>
            await client.query(`
              INSERT INTO character_interests (character_id, category, interest_text, proficiency_level, importance, display_order)
              VALUES ($1, $2, $3, $4, $5, $6)
            `, [
              character.id,
              getString(interestEntry, 'category') || 'General',
              getString(interestEntry, 'interest_text') || null,
              typeof interestEntry.proficiency_level === 'number' ? interestEntry.proficiency_level : 5,
              getString(interestEntry, 'importance') || 'Medium',
              typeof interestEntry.display_order === 'number' ? interestEntry.display_order : 1
            ])
          }
        }
      }
      
      // Import speech patterns
      const speechData = yamlData.speech_patterns as Record<string, unknown> | undefined
      if (speechData && Array.isArray(speechData.patterns)) {
        for (const pattern of speechData.patterns) {
          if (typeof pattern === 'object' && pattern !== null) {
            const speechPattern = pattern as Record<string, unknown>
            await client.query(`
              INSERT INTO character_speech_patterns (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
              VALUES ($1, $2, $3, $4, $5, $6)
            `, [
              character.id,
              getString(speechPattern, 'pattern_type') || 'General',
              getString(speechPattern, 'pattern_value') || getString(speechPattern, 'pattern') || null,
              getString(speechPattern, 'usage_frequency') || getString(speechPattern, 'frequency') || 'Medium',
              getString(speechPattern, 'context') || null,
              typeof speechPattern.priority === 'number' ? speechPattern.priority : 5
            ])
          }
        }
      }
      
      await client.query('COMMIT')
      
      return NextResponse.json({
        success: true,
        message: `Character "${nameVal}" imported successfully`,
        character: {
          id: character.id,
          name: character.name,
          normalized_name: character.normalized_name,
          occupation: character.occupation,
          description: character.description
        }
      }, { status: 201 })

    } catch (importError) {
      await client.query('ROLLBACK')
      console.error('Error during complete import operation:', importError)
      
      return NextResponse.json({
        success: false,
        error: `Import failed: ${importError instanceof Error ? importError.message : 'Unknown error'}`
      }, { status: 500 })
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