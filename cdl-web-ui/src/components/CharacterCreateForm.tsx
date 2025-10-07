'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

// Enhanced CDL data structure for creation
interface CDLData {
  identity: {
    name: string
    occupation: string
    description: string
    location?: string
    age?: number
    voice?: {
      pace?: string
      tone?: string
      accent?: string
      volume?: string
      speech_patterns?: string[]
    }
    essence?: {
      anchor?: string
      nature?: string
      core_identity?: string
    }
  }
  personality: {
    big_five: {
      openness: number
      conscientiousness: number
      extraversion: number
      agreeableness: number
      neuroticism: number
    }
    values: string[]
    communication_style: {
      tone: string
      formality: string
      directness: string
      empathy_level: string
    }
  }
  communication: {
    response_length: string
    ai_identity_handling: {
      approach: string
      philosophy: string
      allow_full_roleplay_immersion: boolean
    }
    conversation_flow_guidance?: {
      response_style?: {
        default_mode?: string
        creative_mode?: {
          triggers?: string[]
          characteristics?: string[]
        }
        technical_mode?: {
          triggers?: string[]
          characteristics?: string[]
        }
      }
    }
  }
  personal_knowledge?: {
    relationships?: Array<{
      name: string
      relationship_type: string
      description: string
    }>
    background?: {
      education?: string
      career_history?: string
      significant_events?: string[]
    }
    interests?: string[]
    skills?: string[]
  }
}

interface FormData {
  name: string
  normalized_name: string
  bot_name: string
  character_archetype: 'real-world' | 'fantasy' | 'narrative-ai'
  allow_full_roleplay_immersion: boolean
  cdl_data: CDLData
}

export default function CharacterCreateForm() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<'identity' | 'personality' | 'communication' | 'knowledge'>('identity')
  const [isLoading, setIsLoading] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')

  const [formData, setFormData] = useState<FormData>({
    name: '',
    normalized_name: '',
    bot_name: '',
    character_archetype: 'real-world',
    allow_full_roleplay_immersion: false,
    cdl_data: {
      identity: {
        name: '',
        occupation: '',
        description: '',
        location: '',
        age: undefined,
        voice: {
          pace: 'moderate',
          tone: 'warm',
          accent: 'neutral',
          volume: 'normal',
          speech_patterns: []
        },
        essence: {
          anchor: '',
          nature: '',
          core_identity: ''
        }
      },
      personality: {
        big_five: {
          openness: 0.5,
          conscientiousness: 0.5,
          extraversion: 0.5,
          agreeableness: 0.5,
          neuroticism: 0.5
        },
        values: [],
        communication_style: {
          tone: 'friendly',
          formality: 'casual',
          directness: 'moderate',
          empathy_level: 'high'
        }
      },
      communication: {
        response_length: 'moderate',
        ai_identity_handling: {
          approach: '3-tier',
          philosophy: 'honest_with_alternatives',
          allow_full_roleplay_immersion: false
        },
        conversation_flow_guidance: {
          response_style: {
            default_mode: 'conversational',
            creative_mode: {
              triggers: ['creative', 'artistic', 'imaginative'],
              characteristics: ['metaphorical', 'expressive', 'colorful']
            },
            technical_mode: {
              triggers: ['technical', 'debug', 'code', 'precise'],
              characteristics: ['clear', 'structured', 'factual']
            }
          }
        }
      },
      personal_knowledge: {
        relationships: [],
        background: {
          education: '',
          career_history: '',
          significant_events: []
        },
        interests: [],
        skills: []
      }
    }
  })

  // Update normalized name when name changes
  const handleNameChange = (name: string) => {
    const normalized = name.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '')
    const botName = name.toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 20)
    
    setFormData(prev => ({
      ...prev,
      name,
      normalized_name: normalized,
      bot_name: botName,
      cdl_data: {
        ...prev.cdl_data,
        identity: {
          ...prev.cdl_data.identity,
          name
        }
      }
    }))
  }

  const handleSave = async () => {
    if (!formData.name || !formData.cdl_data.identity.occupation) {
      alert('Please fill in required fields: Name and Occupation')
      return
    }

    setIsLoading(true)
    setSaveStatus('saving')
    
    try {
      const response = await fetch('/api/characters', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        const result = await response.json()
        setSaveStatus('saved')
        setTimeout(() => {
          router.push(`/characters/${result.character.id}`)
        }, 1000)
      } else {
        const error = await response.json()
        console.error('Save error:', error)
        setSaveStatus('error')
      }
    } catch (error) {
      console.error('Save error:', error)
      setSaveStatus('error')
    } finally {
      setIsLoading(false)
    }
  }

  const addArrayItem = (path: string, value: string) => {
    if (!value.trim()) return
    
    setFormData(prev => {
      const newData = { ...prev }
      const pathParts = path.split('.')
      let target: any = newData
      
      for (let i = 0; i < pathParts.length - 1; i++) {
        target = target[pathParts[i]]
      }
      
      const arrayKey = pathParts[pathParts.length - 1]
      if (!Array.isArray(target[arrayKey])) {
        target[arrayKey] = []
      }
      
      target[arrayKey] = [...target[arrayKey], value]
      return newData
    })
  }

  const removeArrayItem = (path: string, index: number) => {
    setFormData(prev => {
      const newData = { ...prev }
      const pathParts = path.split('.')
      let target: any = newData
      
      for (let i = 0; i < pathParts.length - 1; i++) {
        target = target[pathParts[i]]
      }
      
      const arrayKey = pathParts[pathParts.length - 1]
      target[arrayKey] = target[arrayKey].filter((_: any, i: number) => i !== index)
      return newData
    })
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6 py-4">
          {[
            { id: 'identity', label: 'Identity', icon: '👤' },
            { id: 'personality', label: 'Personality', icon: '🧠' },
            { id: 'communication', label: 'Communication', icon: '💬' },
            { id: 'knowledge', label: 'Knowledge', icon: '📚' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg font-medium ${
                activeTab === tab.id
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {activeTab === 'identity' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900">Character Identity</h3>
            
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Character Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleNameChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter character name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Occupation *
                </label>
                <input
                  type="text"
                  value={formData.cdl_data.identity.occupation}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    cdl_data: {
                      ...prev.cdl_data,
                      identity: {
                        ...prev.cdl_data.identity,
                        occupation: e.target.value
                      }
                    }
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Marine Biologist, AI Researcher"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Location
                </label>
                <input
                  type="text"
                  value={formData.cdl_data.identity.location || ''}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    cdl_data: {
                      ...prev.cdl_data,
                      identity: {
                        ...prev.cdl_data.identity,
                        location: e.target.value
                      }
                    }
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., San Francisco, Remote"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Age
                </label>
                <input
                  type="number"
                  value={formData.cdl_data.identity.age || ''}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    cdl_data: {
                      ...prev.cdl_data,
                      identity: {
                        ...prev.cdl_data.identity,
                        age: e.target.value ? parseInt(e.target.value) : undefined
                      }
                    }
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Age"
                />
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Character Description
              </label>
              <textarea
                value={formData.cdl_data.identity.description}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  cdl_data: {
                    ...prev.cdl_data,
                    identity: {
                      ...prev.cdl_data.identity,
                      description: e.target.value
                    }
                  }
                }))}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Describe the character's background, role, and key characteristics..."
              />
            </div>

            {/* Character Archetype */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Character Archetype
              </label>
              <select
                value={formData.character_archetype}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  character_archetype: e.target.value as any
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="real-world">Real-world (Human-like professional)</option>
                <option value="fantasy">Fantasy/Mythical (Fictional entity)</option>
                <option value="narrative-ai">Narrative AI (AI character with story)</option>
              </select>
            </div>

            {/* Voice Characteristics */}
            <div>
              <h4 className="text-md font-medium text-gray-800 mb-3">Voice Characteristics</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Pace</label>
                  <select
                    value={formData.cdl_data.identity.voice?.pace || 'moderate'}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        identity: {
                          ...prev.cdl_data.identity,
                          voice: {
                            ...prev.cdl_data.identity.voice,
                            pace: e.target.value
                          }
                        }
                      }
                    }))}
                    className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                  >
                    <option value="slow">Slow</option>
                    <option value="moderate">Moderate</option>
                    <option value="fast">Fast</option>
                    <option value="variable">Variable</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tone</label>
                  <select
                    value={formData.cdl_data.identity.voice?.tone || 'warm'}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        identity: {
                          ...prev.cdl_data.identity,
                          voice: {
                            ...prev.cdl_data.identity.voice,
                            tone: e.target.value
                          }
                        }
                      }
                    }))}
                    className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                  >
                    <option value="warm">Warm</option>
                    <option value="professional">Professional</option>
                    <option value="friendly">Friendly</option>
                    <option value="authoritative">Authoritative</option>
                    <option value="gentle">Gentle</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Accent</label>
                  <input
                    type="text"
                    value={formData.cdl_data.identity.voice?.accent || ''}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        identity: {
                          ...prev.cdl_data.identity,
                          voice: {
                            ...prev.cdl_data.identity.voice,
                            accent: e.target.value
                          }
                        }
                      }
                    }))}
                    className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                    placeholder="e.g., British, Southern"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Volume</label>
                  <select
                    value={formData.cdl_data.identity.voice?.volume || 'normal'}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        identity: {
                          ...prev.cdl_data.identity,
                          voice: {
                            ...prev.cdl_data.identity.voice,
                            volume: e.target.value
                          }
                        }
                      }
                    }))}
                    className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                  >
                    <option value="quiet">Quiet</option>
                    <option value="normal">Normal</option>
                    <option value="loud">Loud</option>
                    <option value="varies">Varies</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'personality' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900">Personality Traits</h3>
            
            {/* Big Five Personality */}
            <div>
              <h4 className="text-md font-medium text-gray-800 mb-3">Big Five Personality Traits</h4>
              <div className="space-y-4">
                {Object.entries(formData.cdl_data.personality.big_five).map(([trait, value]) => (
                  <div key={trait}>
                    <label className="block text-sm font-medium text-gray-700 mb-2 capitalize">
                      {trait} ({Math.round(value * 100)}%)
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.01"
                      value={value}
                      onChange={(e) => setFormData(prev => ({
                        ...prev,
                        cdl_data: {
                          ...prev.cdl_data,
                          personality: {
                            ...prev.cdl_data.personality,
                            big_five: {
                              ...prev.cdl_data.personality.big_five,
                              [trait]: parseFloat(e.target.value)
                            }
                          }
                        }
                      }))}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>Low</span>
                      <span>High</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Values */}
            <div>
              <h4 className="text-md font-medium text-gray-800 mb-3">Core Values</h4>
              <div className="space-y-2">
                {formData.cdl_data.personality.values.map((value, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <span className="flex-1 px-3 py-2 bg-gray-100 rounded">{value}</span>
                    <button
                      onClick={() => removeArrayItem('cdl_data.personality.values', index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <div className="flex space-x-2">
                  <input
                    type="text"
                    placeholder="Add a core value"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        addArrayItem('cdl_data.personality.values', (e.target as HTMLInputElement).value);
                        (e.target as HTMLInputElement).value = ''
                      }
                    }}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded"
                  />
                </div>
              </div>
            </div>

            {/* Communication Style */}
            <div>
              <h4 className="text-md font-medium text-gray-800 mb-3">Communication Style</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tone</label>
                  <select
                    value={formData.cdl_data.personality.communication_style.tone}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        personality: {
                          ...prev.cdl_data.personality,
                          communication_style: {
                            ...prev.cdl_data.personality.communication_style,
                            tone: e.target.value
                          }
                        }
                      }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded"
                  >
                    <option value="friendly">Friendly</option>
                    <option value="professional">Professional</option>
                    <option value="casual">Casual</option>
                    <option value="formal">Formal</option>
                    <option value="enthusiastic">Enthusiastic</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Formality</label>
                  <select
                    value={formData.cdl_data.personality.communication_style.formality}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        personality: {
                          ...prev.cdl_data.personality,
                          communication_style: {
                            ...prev.cdl_data.personality.communication_style,
                            formality: e.target.value
                          }
                        }
                      }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded"
                  >
                    <option value="casual">Casual</option>
                    <option value="semi-formal">Semi-formal</option>
                    <option value="formal">Formal</option>
                    <option value="academic">Academic</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Directness</label>
                  <select
                    value={formData.cdl_data.personality.communication_style.directness}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        personality: {
                          ...prev.cdl_data.personality,
                          communication_style: {
                            ...prev.cdl_data.personality.communication_style,
                            directness: e.target.value
                          }
                        }
                      }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded"
                  >
                    <option value="indirect">Indirect</option>
                    <option value="moderate">Moderate</option>
                    <option value="direct">Direct</option>
                    <option value="blunt">Blunt</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Empathy Level</label>
                  <select
                    value={formData.cdl_data.personality.communication_style.empathy_level}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        personality: {
                          ...prev.cdl_data.personality,
                          communication_style: {
                            ...prev.cdl_data.personality.communication_style,
                            empathy_level: e.target.value
                          }
                        }
                      }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded"
                  >
                    <option value="low">Low</option>
                    <option value="moderate">Moderate</option>
                    <option value="high">High</option>
                    <option value="very_high">Very High</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'communication' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900">Communication Settings</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Response Length
                </label>
                <select
                  value={formData.cdl_data.communication.response_length}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    cdl_data: {
                      ...prev.cdl_data,
                      communication: {
                        ...prev.cdl_data.communication,
                        response_length: e.target.value
                      }
                    }
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                >
                  <option value="brief">Brief (1-2 sentences)</option>
                  <option value="moderate">Moderate (2-4 sentences)</option>
                  <option value="detailed">Detailed (4+ sentences)</option>
                  <option value="variable">Variable (context-dependent)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  AI Identity Approach
                </label>
                <select
                  value={formData.cdl_data.communication.ai_identity_handling.approach}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    cdl_data: {
                      ...prev.cdl_data,
                      communication: {
                        ...prev.cdl_data.communication,
                        ai_identity_handling: {
                          ...prev.cdl_data.communication.ai_identity_handling,
                          approach: e.target.value
                        }
                      }
                    }
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                >
                  <option value="3-tier">3-Tier (Enthusiasm → Clarification → Alternatives)</option>
                  <option value="direct_honest">Direct Honest</option>
                  <option value="roleplay_immersion">Full Roleplay Immersion</option>
                  <option value="narrative_ai">Narrative AI Character</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                AI Identity Philosophy
              </label>
              <textarea
                value={formData.cdl_data.communication.ai_identity_handling.philosophy}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  cdl_data: {
                    ...prev.cdl_data,
                    communication: {
                      ...prev.cdl_data.communication,
                      ai_identity_handling: {
                        ...prev.cdl_data.communication.ai_identity_handling,
                        philosophy: e.target.value
                      }
                    }
                  }
                }))}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded"
                placeholder="Describe how this character should handle questions about AI identity..."
              />
            </div>

            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="roleplay_immersion"
                checked={formData.cdl_data.communication.ai_identity_handling.allow_full_roleplay_immersion}
                onChange={(e) => {
                  const allow = e.target.checked
                  setFormData(prev => ({
                    ...prev,
                    allow_full_roleplay_immersion: allow,
                    cdl_data: {
                      ...prev.cdl_data,
                      communication: {
                        ...prev.cdl_data.communication,
                        ai_identity_handling: {
                          ...prev.cdl_data.communication.ai_identity_handling,
                          allow_full_roleplay_immersion: allow
                        }
                      }
                    }
                  }))
                }}
                className="h-4 w-4 text-blue-600"
              />
              <label htmlFor="roleplay_immersion" className="text-sm font-medium text-gray-700">
                Allow Full Roleplay Immersion (character never breaks character)
              </label>
            </div>
          </div>
        )}

        {activeTab === 'knowledge' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900">Personal Knowledge</h3>
            
            {/* Interests */}
            <div>
              <h4 className="text-md font-medium text-gray-800 mb-3">Interests & Hobbies</h4>
              <div className="space-y-2">
                {formData.cdl_data.personal_knowledge?.interests?.map((interest, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <span className="flex-1 px-3 py-2 bg-blue-50 rounded">{interest}</span>
                    <button
                      onClick={() => removeArrayItem('cdl_data.personal_knowledge.interests', index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <div className="flex space-x-2">
                  <input
                    type="text"
                    placeholder="Add an interest or hobby"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        addArrayItem('cdl_data.personal_knowledge.interests', (e.target as HTMLInputElement).value);
                        (e.target as HTMLInputElement).value = ''
                      }
                    }}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded"
                  />
                </div>
              </div>
            </div>

            {/* Skills */}
            <div>
              <h4 className="text-md font-medium text-gray-800 mb-3">Skills & Expertise</h4>
              <div className="space-y-2">
                {formData.cdl_data.personal_knowledge?.skills?.map((skill, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <span className="flex-1 px-3 py-2 bg-green-50 rounded">{skill}</span>
                    <button
                      onClick={() => removeArrayItem('cdl_data.personal_knowledge.skills', index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <div className="flex space-x-2">
                  <input
                    type="text"
                    placeholder="Add a skill or area of expertise"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        addArrayItem('cdl_data.personal_knowledge.skills', (e.target as HTMLInputElement).value);
                        (e.target as HTMLInputElement).value = ''
                      }
                    }}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded"
                  />
                </div>
              </div>
            </div>

            {/* Background */}
            <div>
              <h4 className="text-md font-medium text-gray-800 mb-3">Background Information</h4>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Education</label>
                  <textarea
                    value={formData.cdl_data.personal_knowledge?.background?.education || ''}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        personal_knowledge: {
                          ...prev.cdl_data.personal_knowledge,
                          background: {
                            ...prev.cdl_data.personal_knowledge?.background,
                            education: e.target.value
                          }
                        }
                      }
                    }))}
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded"
                    placeholder="Educational background, degrees, certifications..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Career History</label>
                  <textarea
                    value={formData.cdl_data.personal_knowledge?.background?.career_history || ''}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        personal_knowledge: {
                          ...prev.cdl_data.personal_knowledge,
                          background: {
                            ...prev.cdl_data.personal_knowledge?.background,
                            career_history: e.target.value
                          }
                        }
                      }
                    }))}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded"
                    placeholder="Work experience, career progression, notable achievements..."
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="border-t border-gray-200 px-6 py-4">
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-500">
            {saveStatus === 'saving' && 'Saving character...'}
            {saveStatus === 'saved' && '✅ Character saved successfully!'}
            {saveStatus === 'error' && '❌ Error saving character'}
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={() => router.push('/characters')}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isLoading || !formData.name || !formData.cdl_data.identity.occupation}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
            >
              {isLoading ? 'Creating...' : 'Create Character'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}