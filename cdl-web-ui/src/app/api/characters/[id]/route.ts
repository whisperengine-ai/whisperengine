import { NextRequest, NextResponse } from 'next/server'
import { getCharacterById, updateCharacter, deleteCharacter } from '@/lib/db'

interface RouteContext {
  params: Promise<{
    id: string
  }>
}

export async function GET(request: NextRequest, { params }: RouteContext) {
  try {
    const { id } = await params
    const characterId = parseInt(id)
    
    if (isNaN(characterId)) {
      return NextResponse.json({ error: 'Invalid character ID' }, { status: 400 })
    }

    const character = await getCharacterById(characterId)
    
    if (!character) {
      return NextResponse.json({ error: 'Character not found' }, { status: 404 })
    }

    return NextResponse.json({ character })
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    return NextResponse.json({ error: errorMessage }, { status: 500 })
  }
}

export async function PUT(request: NextRequest, { params }: RouteContext) {
  try {
    const { id } = await params
    const characterId = parseInt(id)
    
    if (isNaN(characterId)) {
      return NextResponse.json({ error: 'Invalid character ID' }, { status: 400 })
    }

    const body = await request.json()
    const { 
      name, 
      occupation, 
      location, 
      description, 
      character_archetype, 
      allow_full_roleplay_immersion,
      cdl_data 
    } = body

    const updatedCharacter = await updateCharacter(characterId, {
      name,
      occupation,
      location,
      description,
      archetype: character_archetype,
      allow_full_roleplay: allow_full_roleplay_immersion,
      cdl_data
    })

    if (!updatedCharacter) {
      return NextResponse.json({ error: 'Character not found' }, { status: 404 })
    }

    return NextResponse.json({ 
      success: true, 
      character: updatedCharacter 
    })
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    return NextResponse.json({ 
      success: false, 
      error: errorMessage 
    }, { status: 500 })
  }
}

export async function DELETE(request: NextRequest, { params }: RouteContext) {
  try {
    const { id } = await params
    const characterId = parseInt(id)
    
    if (isNaN(characterId)) {
      return NextResponse.json({ error: 'Invalid character ID' }, { status: 400 })
    }

    const deleted = await deleteCharacter(characterId)
    
    if (!deleted) {
      return NextResponse.json({ error: 'Character not found' }, { status: 404 })
    }

    return NextResponse.json({ 
      success: true, 
      message: 'Character deleted successfully' 
    })
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    return NextResponse.json({ 
      success: false, 
      error: errorMessage 
    }, { status: 500 })
  }
}