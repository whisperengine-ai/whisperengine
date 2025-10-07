import { NextRequest, NextResponse } from 'next/server'
import { getCharacterById, updateCharacter } from '@/lib/db'

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
    const { name, occupation, location, description, cdl_data } = body

    const updatedCharacter = await updateCharacter(characterId, {
      name,
      occupation,
      location,
      description,
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