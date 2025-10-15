"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Character } from "@/types/cdl";
import Link from "next/link";

export default function CharactersPage() {
  const [characters, setCharacters] = useState<Character[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [importing, setImporting] = useState(false)

  useEffect(() => {
    loadCharacters()
  }, [])

  const loadCharacters = async () => {
    try {
      const response = await fetch('/api/characters')
      if (response.ok) {
        const data = await response.json()
        // Extract the characters array from the response
        const charactersArray = data.characters || data || []
        setCharacters(charactersArray)
      } else {
        setError('Failed to load characters')
      }
    } catch (e) {
      console.error('Error loading characters:', e)
      setError(e instanceof Error ? e.message : 'Failed to load characters')
    } finally {
      setLoading(false)
    }
  }

  const handleImportCharacter = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    
    setImporting(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch('/api/characters/import', {
        method: 'POST',
        body: formData
      })
      
      const result = await response.json()
      
      if (response.ok) {
        alert(`✅ ${result.message}`)
        loadCharacters() // Refresh the list
      } else {
        alert(`❌ Import failed: ${result.error}`)
      }
    } catch (error) {
      console.error('Error importing character:', error)
      alert(`❌ Import failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setImporting(false)
      // Reset the file input
      event.target.value = ''
    }
  }

  const handleExportCharacter = (characterId: number) => {
    // Create download link for YAML export
    const exportUrl = `/api/characters/${characterId}/export`
    const link = document.createElement('a')
    link.href = exportUrl
    link.download = `character_${characterId}.yaml`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-300">Loading characters...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <nav className="bg-gray-800 shadow-sm border-b border-gray-700">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-8">
            <Link href="/" className="text-xl font-bold text-blue-400">CDL Authoring Tool</Link>
            <div className="flex space-x-6">
              <Link href="/characters" className="text-blue-400 font-medium">Characters</Link>
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-100 mb-2">Characters</h1>
          <p className="text-gray-400">Manage character definitions, personalities, and behavioral patterns.</p>
        </div>

        <div className="bg-gray-800 rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">Character List</h2>
            <div className="flex space-x-3">
              {/* Import Character Button */}
              <label className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 cursor-pointer">
                {importing ? 'Importing...' : '📁 Import YAML'}
                <input
                  type="file"
                  accept=".yaml,.yml"
                  onChange={handleImportCharacter}
                  disabled={importing}
                  className="hidden"
                />
              </label>
              
              {/* New Character Button */}
              <Link href="/characters/new" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                + New Character
              </Link>
            </div>
          </div>

          {error ? (
            <div className="text-center py-12 text-red-500">
              <div className="text-4xl mb-4">⚠️</div>
              <h3 className="text-lg font-medium mb-2">Database Connection Error</h3>
              <p className="mb-2">Unable to connect to the database.</p>
              <p className="text-sm text-gray-400">Error: {error}</p>
              <p className="text-sm text-gray-400 mt-2">
                Please ensure PostgreSQL is running and configured correctly.
                Check your PGHOST and PGPORT environment variables.
              </p>
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
                <thead className="bg-gray-900">
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
                <tbody className="bg-gray-800 divide-y divide-gray-200">
                  {Array.isArray(characters) && characters.length > 0 ? (
                    characters.map((character) => (
                      <tr key={character.id} className="hover:bg-gray-900">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-100">{character.name}</div>
                            <div className="text-sm text-gray-500">{character.location || 'No location'}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">
                          {character.occupation || 'Not specified'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            character.archetype === 'real-world' 
                              ? 'bg-green-100 text-green-800'
                              : character.archetype === 'fantasy'
                              ? 'bg-purple-100 text-purple-800'
                              : 'bg-blue-100 text-blue-800'
                          }`}>
                            {character.archetype}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">
                          {character.bot_name || 'No bot assigned'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(character.updated_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex space-x-2 justify-end">
                            <Link href={`/characters/${character.id}?mode=edit`} className="text-blue-400 hover:text-blue-900">
                              Edit
                            </Link>
                            <Link href={`/characters/${character.id}?mode=view`} className="text-gray-400 hover:text-gray-100">
                              View
                            </Link>
                            <button
                              onClick={() => handleExportCharacter(character.id!)}
                              className="text-purple-600 hover:text-purple-900"
                              title="Export character as YAML"
                            >
                              📤 Export
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-500">
                        {error ? `Error: ${error}` : 'No characters available or invalid data format'}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}