'use client'

import { useState } from 'react'
import Link from 'next/link'
import CharacterCreateForm from '@/components/CharacterCreateForm'
import CharacterTemplateWizard from '@/components/CharacterTemplateWizard'
import { CharacterTemplate } from '@/data/characterTemplates'

export default function NewCharacterPage() {
  const [mode, setMode] = useState<'wizard' | 'custom' | 'form'>('wizard')
  const [selectedTemplate, setSelectedTemplate] = useState<CharacterTemplate | null>(null)

  const handleTemplateSelected = (template: CharacterTemplate) => {
    setSelectedTemplate(template)
    setMode('form')
  }

  const handleCustomCreate = () => {
    setSelectedTemplate(null)
    setMode('form')
  }

  const handleBackToWizard = () => {
    setMode('wizard')
    setSelectedTemplate(null)
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
              <Link href="/communication" className="text-gray-600 hover:text-blue-600">
                Communication
              </Link>
              <Link href="/values" className="text-gray-600 hover:text-blue-600">
                Values
              </Link>
              <Link href="/knowledge" className="text-gray-600 hover:text-blue-600">
                Knowledge
              </Link>
              <Link href="/evolution" className="text-gray-600 hover:text-blue-600">
                Evolution
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        {mode === 'wizard' && (
          <CharacterTemplateWizard
            onTemplateSelected={handleTemplateSelected}
            onCustomCreate={handleCustomCreate}
          />
        )}

        {mode === 'form' && (
          <>
            <div className="mb-8">
              <div className="flex items-center space-x-4 mb-4">
                <Link 
                  href="/characters" 
                  className="text-blue-600 hover:text-blue-800 font-medium"
                >
                  ← Back to Characters
                </Link>
                <span className="text-gray-300">|</span>
                <button
                  onClick={handleBackToWizard}
                  className="text-blue-600 hover:text-blue-800 font-medium"
                >
                  ← Back to Template Wizard
                </button>
              </div>
              <div className="flex items-center space-x-4 mb-4">
                <h1 className="text-3xl font-bold text-gray-900">
                  {selectedTemplate ? `Create ${selectedTemplate.name}` : 'Create Custom Character'}
                </h1>
                {selectedTemplate && (
                  <span className="text-2xl">{selectedTemplate.icon}</span>
                )}
              </div>
              <p className="text-gray-600">
                {selectedTemplate 
                  ? `Using the ${selectedTemplate.name} template with pre-configured learning capabilities. Customize as needed.`
                  : 'Define a new AI character with comprehensive personality, communication style, and behavioral patterns.'
                }
              </p>
              {selectedTemplate && (
                <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                  <h3 className="font-semibold text-blue-900 mb-2">Template Benefits:</h3>
                  <ul className="text-blue-800 text-sm space-y-1">
                    <li>• Pre-configured learning profile with {selectedTemplate.learningProfile.adaptabilityLevel} adaptability</li>
                    <li>• Optimized for {selectedTemplate.category.replace('_', ' ')} use cases</li>
                    <li>• Built-in attachment monitoring and ethical boundaries</li>
                    <li>• {selectedTemplate.learningProfile.growthAreas.length} growth areas configured</li>
                  </ul>
                </div>
              )}
            </div>

            <CharacterCreateForm initialTemplate={selectedTemplate} />
          </>
        )}
      </div>
    </div>
  )
}