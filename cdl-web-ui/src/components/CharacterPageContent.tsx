'use client'

import { Character } from '@/types/cdl'
import CharacterView from './CharacterView'
import SimpleCharacterEditForm from './SimpleCharacterEditForm'

interface CharacterPageContentProps {
  character: Character
  mode: 'view' | 'edit'
}

export default function CharacterPageContent({ character, mode }: CharacterPageContentProps) {
  if (mode === 'edit') {
    return (
      <div className="bg-white rounded-lg shadow">
        <SimpleCharacterEditForm character={character} />
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <CharacterView character={character} />
    </div>
  )
}