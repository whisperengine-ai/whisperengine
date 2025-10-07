import { NextRequest, NextResponse } from 'next/server'
import { getCharacters, createCharacter } from '@/lib/db'

export async function GET() {
  try {
    const characters = await getCharacters()
    
    // Return both raw data and debug info
    return NextResponse.json({
      success: true,
      count: characters.length,
      characters: characters,
      debug: {
        first_character: characters[0] || null,
        bot_names: characters.map(c => ({ name: c.name, bot_name: c.bot_name, character_archetype: c.character_archetype }))
      }
    })
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    const errorStack = error instanceof Error ? error.stack : undefined
    
    return NextResponse.json({
      success: false,
      error: errorMessage,
      stack: errorStack
    }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const data = await request.json()
    
    // Validate required fields
    if (!data.name || !data.cdl_data?.identity?.occupation) {
      return NextResponse.json({
        success: false,
        error: 'Missing required fields: name and occupation'
      }, { status: 400 })
    }
    
    const character = await createCharacter(data)
    
    return NextResponse.json({
      success: true,
      character
    }, { status: 201 })
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    const errorStack = error instanceof Error ? error.stack : undefined
    
    console.error('Character creation error:', error)
    
    return NextResponse.json({
      success: false,
      error: errorMessage,
      stack: errorStack
    }, { status: 500 })
  }
}