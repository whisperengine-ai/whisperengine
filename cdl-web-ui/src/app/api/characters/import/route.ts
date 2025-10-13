import { NextRequest, NextResponse } from 'next/server'
import { createCharacter } from '@/lib/db'
import * as yaml from 'js-yaml'

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
  character_archetype: getArchetype(getString(identity, 'archetype')),
      allow_full_roleplay_immersion: getBoolean(identity, 'allow_full_roleplay_immersion') ?? false,
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

    // Create character in database
    const character = await createCharacter(characterData)
    
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