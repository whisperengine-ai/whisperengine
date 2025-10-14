'use client'

import Link from 'next/link'
import SimpleCharacterCreateForm from '@/components/SimpleCharacterCreateForm'

export default function NewCharacterPage() {
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
                <h1 className="text-3xl font-bold text-gray-900">Create New Character</h1>
                <p className="text-gray-600 mt-2">
                  Set up a new AI character with personality, LLM configuration, and Discord integration.
                </p>
              </div>
              <Link 
                href="/characters" 
                className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600"
              >
                ← Back to Characters
              </Link>
            </div>
          </div>

          {/* Character Creation Form */}
          <SimpleCharacterCreateForm />
        </div>
      </div>
    </div>
  )
}