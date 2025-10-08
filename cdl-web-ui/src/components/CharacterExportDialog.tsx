'use client'

import { useState } from 'react'
import { CharacterTemplate } from '@/data/characterTemplates'

interface CharacterExportDialogProps {
  character: any // eslint-disable-line @typescript-eslint/no-explicit-any
  isOpen: boolean
  onClose: () => void
}

export default function CharacterExportDialog({ character, isOpen, onClose }: CharacterExportDialogProps) {
  const [exportFormat, setExportFormat] = useState<'json' | 'yaml' | 'template'>('json')
  const [includePersonalData, setIncludePersonalData] = useState(false)
  const [includeSystemPrompts, setIncludeSystemPrompts] = useState(true)
  const [copySuccess, setCopySuccess] = useState(false)

  if (!isOpen) return null

  const generateTemplate = (): CharacterTemplate => {
    return {
      id: `custom_${character.normalized_name || 'character'}`,
      name: character.name || 'Custom Character',
      category: 'professional', // Default category
      description: character.cdl_data?.identity?.description || 'A custom character created with CDL Authoring Tool',
      icon: '🤖',
      learningProfile: {
        adaptabilityLevel: 'medium',
        growthAreas: ['conversation_skills', 'domain_expertise'],
        memoryRetention: 'medium',
        attachmentRisk: 'low'
      },
      cdlData: {
        identity: {
          name: character.cdl_data?.identity?.name || character.name,
          occupation: character.cdl_data?.identity?.occupation || 'Professional',
          description: character.cdl_data?.identity?.description || '',
          location: character.cdl_data?.identity?.location,
          age: character.cdl_data?.identity?.age
        },
        personality: {
          big_five: character.cdl_data?.personality?.big_five || {
            openness: 0.7,
            conscientiousness: 0.6,
            extraversion: 0.5,
            agreeableness: 0.7,
            neuroticism: 0.3
          },
          values: character.cdl_data?.personality?.values || ['helpfulness', 'honesty', 'growth'],
          communication_style: character.cdl_data?.personality?.communication_style || {
            tone: 'friendly',
            formality: 'casual',
            directness: 'moderate',
            empathy_level: 'high'
          }
        },
        communication: {
          response_length: character.cdl_data?.communication?.response_length || 'moderate',
          ai_identity_handling: {
            approach: character.cdl_data?.communication?.ai_identity_handling?.approach || '3-tier',
            philosophy: character.cdl_data?.communication?.ai_identity_handling?.philosophy || 'honest_with_alternatives',
            allow_full_roleplay_immersion: character.allow_full_roleplay_immersion || false
          }
        }
      }
    }
  }

  const generateExportData = () => {
    const exportData: any = { // eslint-disable-line @typescript-eslint/no-explicit-any
      ...character,
      exported_at: new Date().toISOString(),
      export_version: '1.0',
      created_with: 'CDL Authoring Tool'
    }

    // Remove personal data if not included
    if (!includePersonalData && exportData.cdl_data?.personal_knowledge) {
      delete exportData.cdl_data.personal_knowledge
    }

    // Add system prompts if included
    if (includeSystemPrompts) {
      exportData.system_integration = {
        prompt_templates: {
          system_prompt: `You are ${character.name}, ${character.cdl_data?.identity?.occupation || 'an AI character'}. ${character.cdl_data?.identity?.description || ''}`,
          personality_prompt: `Your personality reflects ${character.cdl_data?.personality?.values?.join(', ') || 'core values'} with a ${character.cdl_data?.personality?.communication_style?.tone || 'friendly'} communication style.`,
          behavior_prompt: `You respond with ${character.cdl_data?.communication?.response_length || 'moderate'} length responses and maintain ${character.cdl_data?.personality?.communication_style?.empathy_level || 'high'} empathy.`
        }
      }
    }

    if (exportFormat === 'template') {
      return generateTemplate()
    }

    return exportData
  }

  const formatExportData = () => {
    const data = generateExportData()
    
    switch (exportFormat) {
      case 'yaml':
        return `# CDL Character Export
# Generated on ${new Date().toISOString()}
# Character: ${character.name}

name: "${data.name}"
normalized_name: "${data.normalized_name}"
character_archetype: "${data.character_archetype}"
allow_full_roleplay_immersion: ${data.allow_full_roleplay_immersion}

cdl_data:
  identity:
    name: "${data.cdl_data.identity.name}"
    occupation: "${data.cdl_data.identity.occupation}"
    description: "${data.cdl_data.identity.description}"
    ${data.cdl_data.identity.location ? `location: "${data.cdl_data.identity.location}"` : ''}
    ${data.cdl_data.identity.age ? `age: ${data.cdl_data.identity.age}` : ''}
  
  personality:
    big_five:
      openness: ${data.cdl_data.personality.big_five.openness}
      conscientiousness: ${data.cdl_data.personality.big_five.conscientiousness}
      extraversion: ${data.cdl_data.personality.big_five.extraversion}
      agreeableness: ${data.cdl_data.personality.big_five.agreeableness}
      neuroticism: ${data.cdl_data.personality.big_five.neuroticism}
    values:
${data.cdl_data.personality.values.map((v: string) => `      - "${v}"`).join('\n')}
    communication_style:
      tone: "${data.cdl_data.personality.communication_style.tone}"
      formality: "${data.cdl_data.personality.communication_style.formality}"
      directness: "${data.cdl_data.personality.communication_style.directness}"
      empathy_level: "${data.cdl_data.personality.communication_style.empathy_level}"
  
  communication:
    response_length: "${data.cdl_data.communication.response_length}"
    ai_identity_handling:
      approach: "${data.cdl_data.communication.ai_identity_handling.approach}"
      philosophy: "${data.cdl_data.communication.ai_identity_handling.philosophy}"
      allow_full_roleplay_immersion: ${data.cdl_data.communication.ai_identity_handling.allow_full_roleplay_immersion}

${includeSystemPrompts ? `
system_integration:
  prompt_templates:
    system_prompt: "${data.system_integration.prompt_templates.system_prompt}"
    personality_prompt: "${data.system_integration.prompt_templates.personality_prompt}"
    behavior_prompt: "${data.system_integration.prompt_templates.behavior_prompt}"
` : ''}`

      case 'template':
        return JSON.stringify(data, null, 2)

      case 'json':
      default:
        return JSON.stringify(data, null, 2)
    }
  }

  const handleCopyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(formatExportData())
      setCopySuccess(true)
      setTimeout(() => setCopySuccess(false), 2000)
    } catch (err) {
      console.error('Failed to copy to clipboard:', err)
    }
  }

  const handleDownload = () => {
    const data = formatExportData()
    const extension = exportFormat === 'yaml' ? 'yml' : 'json'
    const filename = `${character.normalized_name || 'character'}.${extension}`
    
    const blob = new Blob([data], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">
            Export Character: {character.name}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {/* Export Options */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-4">Export Options</h3>
            
            <div className="grid md:grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Export Format
                </label>
                <select
                  value={exportFormat}
                  onChange={(e) => setExportFormat(e.target.value as 'json' | 'yaml' | 'template')}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="json">JSON (Complete)</option>
                  <option value="yaml">YAML (Human Readable)</option>
                  <option value="template">Character Template</option>
                </select>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="includePersonalData"
                  checked={includePersonalData}
                  onChange={(e) => setIncludePersonalData(e.target.checked)}
                  className="mr-2"
                />
                <label htmlFor="includePersonalData" className="text-sm text-gray-700">
                  Include Personal Knowledge
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="includeSystemPrompts"
                  checked={includeSystemPrompts}
                  onChange={(e) => setIncludeSystemPrompts(e.target.checked)}
                  className="mr-2"
                />
                <label htmlFor="includeSystemPrompts" className="text-sm text-gray-700">
                  Include System Prompts
                </label>
              </div>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg mb-4">
              <h4 className="font-medium text-blue-900 mb-2">Format Information:</h4>
              <div className="text-blue-800 text-sm space-y-1">
                {exportFormat === 'json' && (
                  <p>• Complete character data in JSON format for technical integration</p>
                )}
                {exportFormat === 'yaml' && (
                  <p>• Human-readable YAML format for documentation and version control</p>
                )}
                {exportFormat === 'template' && (
                  <p>• Reusable character template for the Character Creation Wizard</p>
                )}
              </div>
            </div>
          </div>

          {/* Preview */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-semibold">Export Preview</h3>
              <div className="space-x-2">
                <button
                  onClick={handleCopyToClipboard}
                  className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                    copySuccess 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-blue-100 text-blue-800 hover:bg-blue-200'
                  }`}
                >
                  {copySuccess ? '✓ Copied!' : 'Copy to Clipboard'}
                </button>
                <button
                  onClick={handleDownload}
                  className="px-4 py-2 bg-purple-100 text-purple-800 rounded text-sm font-medium hover:bg-purple-200"
                >
                  Download File
                </button>
              </div>
            </div>
            
            <pre className="bg-gray-100 p-4 rounded-lg text-sm overflow-auto max-h-96 border">
              <code>{formatExportData()}</code>
            </pre>
          </div>

          {/* Usage Instructions */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Usage Instructions:</h4>
            <div className="text-gray-700 text-sm space-y-1">
              <p>• <strong>JSON Format:</strong> Import into WhisperEngine or other CDL-compatible systems</p>
              <p>• <strong>YAML Format:</strong> Human-readable format for documentation or Git repositories</p>
              <p>• <strong>Character Template:</strong> Add to characterTemplates.ts for reuse in the Character Wizard</p>
              <p>• <strong>Sharing:</strong> Share exported files with other character creators or development teams</p>
            </div>
          </div>
        </div>

        <div className="flex justify-end space-x-4 p-6 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-6 py-2 text-gray-600 hover:text-gray-800 font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}