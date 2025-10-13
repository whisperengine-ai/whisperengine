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
    let yamlData: any
    try {
      yamlData = yaml.load(fileContent) as any
    } catch (yamlError) {
      return NextResponse.json({
        success: false,
        error: 'Invalid YAML format',
        details: yamlError instanceof Error ? yamlError.message : 'Unknown YAML error'
      }, { status: 400 })
    }

    // Validate required fields
    if (!yamlData.name) {
      return NextResponse.json({
        success: false,
        error: 'Missing required field: name'
      }, { status: 400 })
    }

    // Convert YAML structure to database format
    const characterData = {
      name: yamlData.name,
      normalized_name: yamlData.metadata?.normalized_name || yamlData.name.toLowerCase().replace(/[^a-z0-9]/g, '_'),
      occupation: yamlData.identity?.occupation || null,
      description: yamlData.identity?.description || null,
      character_archetype: yamlData.identity?.archetype || 'real-world',
      allow_full_roleplay_immersion: yamlData.identity?.allow_full_roleplay_immersion || false,
      cdl_data: {
        identity: yamlData.identity || {},
        personality: yamlData.personality || {},
        communication: yamlData.communication || {},
        values: yamlData.values || [],
        interests: yamlData.interests || [],
        background: yamlData.background || {},
        speech_patterns: yamlData.speech_patterns || {},
        personal_knowledge: yamlData.personal_knowledge || {},
        roleplay_config: yamlData.roleplay_config || {},
        metadata: {
          ...yamlData.metadata,
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
      message: `Character "${yamlData.name}" imported successfully`,
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