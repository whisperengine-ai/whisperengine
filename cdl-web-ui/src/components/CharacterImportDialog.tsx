'use client'
/* eslint-disable @typescript-eslint/no-explicit-any */

import { useState, useRef } from 'react'

interface CharacterImportDialogProps {
  isOpen: boolean
  onClose: () => void
  onImport: (characterData: any) => void
}

interface ImportedData {
  data: any
  format: 'json' | 'yaml' | 'template' | 'unknown'
  isValid: boolean
  errors: string[]
  warnings: string[]
  type: 'character' | 'template' | 'unknown'
}

export default function CharacterImportDialog({ isOpen, onClose, onImport }: CharacterImportDialogProps) {
  const [importMethod, setImportMethod] = useState<'file' | 'paste'>('file')
  const [pastedData, setPastedData] = useState('')
  const [importedData, setImportedData] = useState<ImportedData | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  if (!isOpen) return null

  const validateCharacterData = (data: any): { isValid: boolean; errors: string[]; warnings: string[] } => {
    const errors: string[] = []
    const warnings: string[] = []

    // Check required fields
    if (!data.name) errors.push('Missing required field: name')
    if (!data.cdl_data) errors.push('Missing required field: cdl_data')
    
    if (data.cdl_data) {
      if (!data.cdl_data.identity) errors.push('Missing required field: cdl_data.identity')
      if (!data.cdl_data.personality) errors.push('Missing required field: cdl_data.personality')
      if (!data.cdl_data.communication) errors.push('Missing required field: cdl_data.communication')
      
      // Check identity fields
      if (data.cdl_data.identity) {
        if (!data.cdl_data.identity.name) errors.push('Missing required field: identity.name')
        if (!data.cdl_data.identity.occupation) errors.push('Missing required field: identity.occupation')
        if (!data.cdl_data.identity.description) warnings.push('Missing recommended field: identity.description')
      }
      
      // Check personality fields
      if (data.cdl_data.personality) {
        if (!data.cdl_data.personality.big_five) errors.push('Missing required field: personality.big_five')
        if (!data.cdl_data.personality.values) warnings.push('Missing recommended field: personality.values')
        if (!data.cdl_data.personality.communication_style) errors.push('Missing required field: personality.communication_style')
      }
      
      // Check communication fields
      if (data.cdl_data.communication) {
        if (!data.cdl_data.communication.ai_identity_handling) errors.push('Missing required field: communication.ai_identity_handling')
      }
    }

    // Check for deprecated fields
    if (data.bot_id) warnings.push('Deprecated field found: bot_id (will be auto-generated)')
    if (data.created_at) warnings.push('Timestamp field found: created_at (will be updated on import)')

    return { isValid: errors.length === 0, errors, warnings }
  }

  const detectFormat = (content: string): 'json' | 'yaml' | 'unknown' => {
    try {
      JSON.parse(content)
      return 'json'
    } catch {
      // Check for YAML patterns
      if (content.includes('\n') && content.includes(':') && !content.includes('{')) {
        return 'yaml'
      }
      return 'unknown'
    }
  }

  const parseContent = (content: string): any => {
    const format = detectFormat(content)
    
    if (format === 'json') {
      return JSON.parse(content)
    } else if (format === 'yaml') {
      // Simple YAML parsing for basic structures
      // Note: In a real implementation, you'd use a proper YAML parser like js-yaml
      throw new Error('YAML parsing not implemented. Please use JSON format or convert to JSON.')
    } else {
      throw new Error('Unrecognized format. Please use JSON or YAML.')
    }
  }

  const processImportData = (content: string) => {
    setIsProcessing(true)
    
    try {
      const data = parseContent(content)
      const format = detectFormat(content)
      
      // Determine if it's a character or template
      const isTemplate = data.hasOwnProperty('learningProfile') || data.hasOwnProperty('category') || data.hasOwnProperty('cdlData')
      const type = isTemplate ? 'template' : 'character'
      
      // Validate the data
      const validation = validateCharacterData(isTemplate ? data.cdlData || data : data)
      
      setImportedData({
        data,
        format: format === 'unknown' ? 'json' : format,
        isValid: validation.isValid,
        errors: validation.errors,
        warnings: validation.warnings,
        type
      })
      
    } catch (error) {
      setImportedData({
        data: null,
        format: 'unknown',
        isValid: false,
        errors: [error instanceof Error ? error.message : 'Failed to parse import data'],
        warnings: [],
        type: 'unknown'
      })
    } finally {
      setIsProcessing(false)
    }
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      const content = e.target?.result as string
      processImportData(content)
    }
    reader.readAsText(file)
  }

  const handlePasteProcess = () => {
    if (!pastedData.trim()) return
    processImportData(pastedData)
  }

  const handleImport = () => {
    if (!importedData?.isValid || !importedData.data) return

    let characterData = importedData.data

    // Convert template to character format if needed
    if (importedData.type === 'template') {
      characterData = {
        name: characterData.name,
        normalized_name: characterData.name?.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '') || '',
        bot_name: characterData.name?.toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 20) || '',
        character_archetype: characterData.cdlData?.communication?.ai_identity_handling?.allow_full_roleplay_immersion ? 'fantasy' : 'real-world',
        allow_full_roleplay_immersion: characterData.cdlData?.communication?.ai_identity_handling?.allow_full_roleplay_immersion || false,
        cdl_data: characterData.cdlData || characterData,
        // Add import metadata
        imported_at: new Date().toISOString(),
        imported_from: 'template',
        original_template: {
          id: characterData.id,
          category: characterData.category,
          learningProfile: characterData.learningProfile
        }
      }
    } else {
      // Clean up character data
      characterData = {
        ...characterData,
        // Update metadata
        imported_at: new Date().toISOString(),
        imported_from: 'character'
      }
      
      // Generate missing fields if needed
      if (!characterData.normalized_name && characterData.name) {
        characterData.normalized_name = characterData.name.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '')
      }
      if (!characterData.bot_name && characterData.name) {
        characterData.bot_name = characterData.name.toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 20)
      }
    }

    onImport(characterData)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-100">
            Import Character or Template
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-400 text-2xl"
          >
            ×
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {/* Import Method Selection */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-4">Import Method</h3>
            <div className="flex space-x-4">
              <button
                onClick={() => setImportMethod('file')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  importMethod === 'file'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-300 hover:bg-gray-300'
                }`}
              >
                📁 Upload File
              </button>
              <button
                onClick={() => setImportMethod('paste')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  importMethod === 'paste'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-300 hover:bg-gray-300'
                }`}
              >
                📋 Paste Data
              </button>
            </div>
          </div>

          {/* File Upload */}
          {importMethod === 'file' && (
            <div className="mb-6">
              <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".json,.yaml,.yml"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <div className="text-4xl mb-4">📄</div>
                <p className="text-gray-400 mb-4">
                  Click to select a JSON or YAML file containing character data
                </p>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700"
                >
                  Choose File
                </button>
                <p className="text-gray-500 text-sm mt-2">
                  Supports: .json, .yaml, .yml files
                </p>
              </div>
            </div>
          )}

          {/* Paste Data */}
          {importMethod === 'paste' && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Paste Character Data (JSON or YAML)
              </label>
              <textarea
                value={pastedData}
                onChange={(e) => setPastedData(e.target.value)}
                placeholder="Paste your character data here..."
                className="w-full h-32 p-3 border border-gray-600 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              />
              <div className="mt-2 flex justify-end">
                <button
                  onClick={handlePasteProcess}
                  disabled={!pastedData.trim() || isProcessing}
                  className="bg-blue-600 text-white px-4 py-2 rounded font-medium hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {isProcessing ? 'Processing...' : 'Process Data'}
                </button>
              </div>
            </div>
          )}

          {/* Import Results */}
          {importedData && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-4">Import Analysis</h3>
              
              <div className="space-y-4">
                {/* Status Summary */}
                <div className={`p-4 rounded-lg ${
                  importedData.isValid 
                    ? 'bg-green-50 border border-green-200' 
                    : 'bg-red-50 border border-red-200'
                }`}>
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-2xl">
                      {importedData.isValid ? '✅' : '❌'}
                    </span>
                    <span className={`font-semibold ${
                      importedData.isValid ? 'text-green-800' : 'text-red-800'
                    }`}>
                      {importedData.isValid ? 'Valid Data' : 'Invalid Data'}
                    </span>
                  </div>
                  <div className="text-sm space-y-1">
                    <p><strong>Format:</strong> {importedData.format.toUpperCase()}</p>
                    <p><strong>Type:</strong> {importedData.type.charAt(0).toUpperCase() + importedData.type.slice(1)}</p>
                    {importedData.data?.name && (
                      <p><strong>Name:</strong> {importedData.data.name}</p>
                    )}
                  </div>
                </div>

                {/* Errors */}
                {importedData.errors.length > 0 && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <h4 className="font-semibold text-red-800 mb-2">❌ Errors (Must Fix):</h4>
                    <ul className="text-red-700 text-sm space-y-1">
                      {importedData.errors.map((error, index) => (
                        <li key={index}>• {error}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Warnings */}
                {importedData.warnings.length > 0 && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <h4 className="font-semibold text-yellow-800 mb-2">⚠️ Warnings (Recommended to Fix):</h4>
                    <ul className="text-yellow-700 text-sm space-y-1">
                      {importedData.warnings.map((warning, index) => (
                        <li key={index}>• {warning}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Template Conversion Notice */}
                {importedData.type === 'template' && importedData.isValid && (
                  <div className="bg-gray-800 border border-blue-200 rounded-lg p-4">
                    <h4 className="font-semibold text-blue-800 mb-2">🔄 Template Conversion:</h4>
                    <p className="text-blue-700 text-sm">
                      This template will be converted to a character format for editing. 
                      Learning profile data will be preserved in metadata.
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Data Preview */}
          {importedData?.data && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2">Data Preview</h3>
              <pre className="bg-gray-100 p-4 rounded-lg text-sm overflow-auto max-h-48 border">
                <code>{JSON.stringify(importedData.data, null, 2)}</code>
              </pre>
            </div>
          )}
        </div>

        <div className="flex justify-between items-center p-6 border-t bg-gray-900">
          <div className="text-sm text-gray-400">
            💡 Tip: You can import characters from other CDL systems or templates from the Character Wizard
          </div>
          <div className="flex space-x-4">
            <button
              onClick={onClose}
              className="px-6 py-2 text-gray-400 hover:text-gray-100 font-medium"
            >
              Cancel
            </button>
            <button
              onClick={handleImport}
              disabled={!importedData?.isValid}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              Import Character
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}