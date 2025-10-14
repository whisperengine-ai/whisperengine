import { notFound } from 'next/navigation'
import Link from 'next/link'
import { getCharacterById } from '@/lib/db'
import CharacterPageContent from '@/components/CharacterPageContent'

interface PageProps {
  params: Promise<{
    id: string
  }>
  searchParams: Promise<{
    mode?: 'view' | 'edit'
  }>
}

export default async function CharacterPage({ params, searchParams }: PageProps) {
  const resolvedParams = await params
  const resolvedSearchParams = await searchParams
  const characterId = parseInt(resolvedParams.id)
  const mode = resolvedSearchParams.mode || 'view'
  
  if (isNaN(characterId)) {
    notFound()
  }

  const character = await getCharacterById(characterId)
  
  if (!character) {
    notFound()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-8">
            <Link href="/" className="text-xl font-bold text-blue-600">
              CDL Authoring Tool
            </Link>
            <div className="flex space-x-6">
              <Link href="/characters" className="text-blue-600 font-medium">
                Characters
              </Link>
              <Link href="/traits" className="text-gray-600 hover:text-blue-600">
                Traits
              </Link>
              <Link href="/config" className="text-gray-600 hover:text-blue-600">
                Config
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  {mode === 'edit' ? 'Edit Character' : 'Character Details'}
                </h1>
                <p className="text-gray-600 mt-2">
                  {mode === 'edit' 
                    ? 'Modify character personality, traits, and behavioral patterns using enhanced JSONB CDL data.'
                    : 'View character information, configuration, and deployment status.'
                  }
                </p>
              </div>
              <div className="flex space-x-2">
                <Link 
                  href="/characters" 
                  className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600"
                >
                  ← Back to Characters
                </Link>
                {mode === 'view' ? (
                  <Link 
                    href={`/characters/${character.id}?mode=edit`}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                  >
                    Edit Character
                  </Link>
                ) : (
                  <Link 
                    href={`/characters/${character.id}`}
                    className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
                  >
                    View Character
                  </Link>
                )}
              </div>
            </div>
          </div>

          {/* Character Content */}
          <CharacterPageContent character={character} mode={mode} />
        </div>
      </div>
    </div>
  )
}
