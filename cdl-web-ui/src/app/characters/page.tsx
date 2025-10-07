import Link from 'next/link'
import { getCharacters } from '@/lib/db'
import { Character } from '@/types/cdl'

// Make this page dynamic to prevent static generation during build
export const dynamic = 'force-dynamic'

export default async function CharactersPage() {
  let characters: Character[] = []
  let error: string | null = null

  try {
    characters = await getCharacters()
  } catch (e) {
    console.error('Error loading characters:', e)
    error = e instanceof Error ? e.message : 'Failed to load characters'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-8">
            <Link href="/" className="text-xl font-bold text-blue-600">CDL Authoring Tool</Link>
            <div className="flex space-x-6">
              <Link href="/characters" className="text-blue-600 font-medium">Characters</Link>
              <Link href="/traits" className="text-gray-600 hover:text-blue-600">Traits</Link>
              <Link href="/communication" className="text-gray-600 hover:text-blue-600">Communication</Link>
              <Link href="/values" className="text-gray-600 hover:text-blue-600">Values</Link>
              <Link href="/knowledge" className="text-gray-600 hover:text-blue-600">Knowledge</Link>
              <Link href="/evolution" className="text-gray-600 hover:text-blue-600">Evolution</Link>
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Characters</h1>
          <p className="text-gray-600">Manage character definitions, personalities, and behavioral patterns.</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">Character List</h2>
            <Link href="/characters/new" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
              + New Character
            </Link>
          </div>

          {error ? (
            <div className="text-center py-12 text-red-500">
              <div className="text-4xl mb-4">⚠️</div>
              <h3 className="text-lg font-medium mb-2">Database Connection Error</h3>
              <p className="mb-2">Unable to connect to the database.</p>
              <p className="text-sm text-gray-600">Error: {error}</p>
              <p className="text-sm text-gray-600 mt-2">Please ensure PostgreSQL is running on port 5433.</p>
            </div>
          ) : characters.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <div className="text-4xl mb-4">👥</div>
              <h3 className="text-lg font-medium mb-2">No characters found</h3>
              <p>Create your first character to get started with CDL authoring.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Character
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Occupation
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Archetype
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Bot Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Updated
                    </th>
                    <th className="relative px-6 py-3">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {characters.map((character) => (
                    <tr key={character.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{character.name}</div>
                          <div className="text-sm text-gray-500">{character.location || 'No location'}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {character.occupation || 'Not specified'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          character.character_archetype === 'real-world' 
                            ? 'bg-green-100 text-green-800'
                            : character.character_archetype === 'fantasy'
                            ? 'bg-purple-100 text-purple-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}>
                          {character.character_archetype}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {character.bot_name || 'No bot assigned'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(character.updated_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <Link href={`/characters/${character.id}`} className="text-blue-600 hover:text-blue-900 mr-4">
                          Edit
                        </Link>
                        <Link href={`/characters/${character.id}/view`} className="text-gray-600 hover:text-gray-900">
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}