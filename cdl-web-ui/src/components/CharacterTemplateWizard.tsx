'use client'

import { useState } from 'react'
import { characterTemplates, CharacterTemplate, getAllCategories } from '../data/characterTemplates'

interface CharacterWizardProps {
  onTemplateSelected?: (template: CharacterTemplate) => void
  onCustomCreate?: () => void
}

export default function CharacterTemplateWizard({ onTemplateSelected, onCustomCreate }: CharacterWizardProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [selectedTemplate, setSelectedTemplate] = useState<CharacterTemplate | null>(null)
  const [showTemplateDetails, setShowTemplateDetails] = useState(false)

  const categories = getAllCategories()
  const filteredTemplates = selectedCategory 
    ? characterTemplates.filter(t => t.category === selectedCategory)
    : characterTemplates

  const handleTemplateSelect = (template: CharacterTemplate) => {
    setSelectedTemplate(template)
    setShowTemplateDetails(true)
  }

  const handleUseTemplate = () => {
    if (selectedTemplate && onTemplateSelected) {
      onTemplateSelected(selectedTemplate)
    }
  }

  const getCategoryDisplayName = (category: string) => {
    return category.charAt(0).toUpperCase() + category.slice(1).replace('_', ' ')
  }

  const getLearningProfileColor = (level: string) => {
    switch (level) {
      case 'low': return 'bg-green-100 text-green-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'high': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  if (showTemplateDetails && selectedTemplate) {
    return (
      <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-8">
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={() => setShowTemplateDetails(false)}
            className="text-blue-600 hover:text-blue-800 flex items-center"
          >
            ← Back to Templates
          </button>
          <div className="text-4xl">{selectedTemplate.icon}</div>
        </div>

        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">{selectedTemplate.name}</h2>
          <p className="text-gray-600 text-lg mb-4">{selectedTemplate.description}</p>
          <span className="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
            {getCategoryDisplayName(selectedTemplate.category)}
          </span>
        </div>

        <div className="grid md:grid-cols-2 gap-8 mb-8">
          {/* Learning Profile */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-xl font-semibold mb-4 flex items-center">
              🧠 Learning Profile
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-700">Adaptability:</span>
                <span className={`px-2 py-1 rounded text-sm ${getLearningProfileColor(selectedTemplate.learningProfile.adaptabilityLevel)}`}>
                  {selectedTemplate.learningProfile.adaptabilityLevel}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-700">Memory Retention:</span>
                <span className={`px-2 py-1 rounded text-sm ${getLearningProfileColor(selectedTemplate.learningProfile.memoryRetention)}`}>
                  {selectedTemplate.learningProfile.memoryRetention}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-700">Attachment Risk:</span>
                <span className={`px-2 py-1 rounded text-sm ${getLearningProfileColor(selectedTemplate.learningProfile.attachmentRisk)}`}>
                  {selectedTemplate.learningProfile.attachmentRisk}
                </span>
              </div>
            </div>
            
            <div className="mt-4">
              <h4 className="font-medium text-gray-700 mb-2">Growth Areas:</h4>
              <div className="flex flex-wrap gap-2">
                {selectedTemplate.learningProfile.growthAreas.map((area, index) => (
                  <span key={index} className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-sm">
                    {area.replace('_', ' ')}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Character Preview */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-xl font-semibold mb-4 flex items-center">
              👤 Character Preview
            </h3>
            <div className="space-y-3">
              <div>
                <span className="text-gray-700 font-medium">Occupation:</span>
                <p className="text-gray-900">{selectedTemplate.cdlData.identity.occupation}</p>
              </div>
              <div>
                <span className="text-gray-700 font-medium">Communication Style:</span>
                <p className="text-gray-900 capitalize">
                  {selectedTemplate.cdlData.personality.communication_style.tone} • 
                  {selectedTemplate.cdlData.personality.communication_style.formality} • 
                  {selectedTemplate.cdlData.personality.communication_style.empathy_level} empathy
                </p>
              </div>
              <div>
                <span className="text-gray-700 font-medium">AI Identity Approach:</span>
                <p className="text-gray-900">
                  {selectedTemplate.cdlData.communication.ai_identity_handling.approach.replace('_', ' ')}
                </p>
              </div>
              <div>
                <span className="text-gray-700 font-medium">Core Values:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {selectedTemplate.cdlData.personality.values.slice(0, 3).map((value, index) => (
                    <span key={index} className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                      {value.replace('_', ' ')}
                    </span>
                  ))}
                  {selectedTemplate.cdlData.personality.values.length > 3 && (
                    <span className="text-gray-500 text-xs">+{selectedTemplate.cdlData.personality.values.length - 3} more</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-blue-50 rounded-lg p-6 mb-8">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">🎯 Perfect For:</h3>
          <p className="text-blue-800">
            This template is ideal for {selectedTemplate.category === 'educational' ? 'creating educational experiences that adapt to student learning patterns' :
            selectedTemplate.category === 'creative' ? 'inspiring creative work and artistic growth through personalized guidance' :
            selectedTemplate.category === 'professional' ? 'enhancing productivity with AI assistance that learns your work patterns' :
            selectedTemplate.category === 'entertainment' ? 'creating engaging entertainment experiences with evolving character depth' :
            'versatile character applications'}.
          </p>
        </div>

        <div className="flex gap-4 justify-center">
          <button
            onClick={handleUseTemplate}
            className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
          >
            Use This Template
          </button>
          <button
            onClick={() => setShowTemplateDetails(false)}
            className="bg-gray-300 text-gray-700 px-8 py-3 rounded-lg font-semibold hover:bg-gray-400 transition-colors"
          >
            Choose Different Template
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          🚀 Character Creation Wizard
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Choose from our professionally designed character templates with built-in learning capabilities, 
          or start from scratch to create your unique AI character.
        </p>
      </div>

      {/* Category Filter */}
      <div className="mb-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Choose a Category</h2>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => setSelectedCategory('')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              selectedCategory === '' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            All Categories
          </button>
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedCategory === category 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {getCategoryDisplayName(category)}
            </button>
          ))}
        </div>
      </div>

      {/* Template Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        {filteredTemplates.map((template) => (
          <div
            key={template.id}
            onClick={() => handleTemplateSelect(template)}
            className="bg-white rounded-lg shadow-lg hover:shadow-xl transition-shadow cursor-pointer p-6 border-2 border-transparent hover:border-blue-300"
          >
            <div className="text-center mb-4">
              <div className="text-4xl mb-2">{template.icon}</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">{template.name}</h3>
              <span className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                {getCategoryDisplayName(template.category)}
              </span>
            </div>
            
            <p className="text-gray-600 text-sm mb-4 line-clamp-3">{template.description}</p>
            
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-500">Learning:</span>
                <span className={`px-2 py-1 rounded ${getLearningProfileColor(template.learningProfile.adaptabilityLevel)}`}>
                  {template.learningProfile.adaptabilityLevel}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Attachment Risk:</span>
                <span className={`px-2 py-1 rounded ${getLearningProfileColor(template.learningProfile.attachmentRisk)}`}>
                  {template.learningProfile.attachmentRisk}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Custom Creation Option */}
      <div className="text-center">
        <div className="bg-gradient-to-r from-purple-100 to-pink-100 rounded-lg p-8 mb-6">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            🛠️ Want Complete Control?
          </h2>
          <p className="text-gray-600 mb-6">
            Start from scratch and build your character exactly how you envision them. 
            Perfect for experienced character creators who want full customization.
          </p>
          <button
            onClick={onCustomCreate}
            className="bg-purple-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-purple-700 transition-colors"
          >
            Create Custom Character
          </button>
        </div>
      </div>
    </div>
  )
}