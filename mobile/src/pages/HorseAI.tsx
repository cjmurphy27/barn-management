import { useState, useRef, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import { horseApi, apiClient } from '../services/api'

interface User {
  user_id: string
  email: string
  organizations: Array<{
    barn_id: string
    barn_name: string
    user_role: string
    permissions: string[]
  }>
}

interface Horse {
  id: string
  name: string
  barn_name?: string
  breed?: string
  color?: string
  gender?: 'mare' | 'stallion' | 'gelding'
  age_years?: number
  age_display?: string
  current_health_status?: 'Excellent' | 'Good' | 'Fair' | 'Poor' | 'Critical'
  allergies?: string
  medications?: string
  special_needs?: string
  notes?: string
  [key: string]: any
}

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  image?: string
  timestamp: Date
}

interface HorseAIProps {
  user: User
  selectedBarnId: string | null
}

export default function HorseAI({ user, selectedBarnId }: HorseAIProps) {
  const { id } = useParams<{ id: string }>()
  const [horse, setHorse] = useState<Horse | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputText, setInputText] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingHorse, setLoadingHorse] = useState(true)
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [uploadingImage, setUploadingImage] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const cameraInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (id && selectedBarnId) {
      loadHorseData()
    }
  }, [id, selectedBarnId])

  const loadHorseData = async () => {
    if (!selectedBarnId) return

    setLoadingHorse(true)
    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) return

      apiClient.setToken(accessToken)

      // Use the API service instead of direct fetch
      const response = await horseApi.getById(id!, selectedBarnId)

      if (response.success) {
        const horseData = response.data as Horse
        setHorse(horseData)

        // Add initial AI greeting with horse context
        const welcomeMessage: Message = {
          id: Date.now().toString(),
          type: 'assistant',
          content: `Hello! I'm here to help you with ${horseData.name}. I have access to all of ${horseData.name}'s profile information, documents, and health records. What would you like to know or discuss about ${horseData.name}?`,
          timestamp: new Date()
        }
        setMessages([welcomeMessage])
      } else {
        throw new Error(response.error || 'Failed to load horse data')
      }
    } catch (error) {
      console.error('Failed to load horse:', error)
    }
    setLoadingHorse(false)
  }

  const handleSendMessage = async () => {
    if ((!inputText.trim() && !selectedImage) || loading || !horse) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputText.trim(),
      image: selectedImage || undefined,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputText('')
    setSelectedImage(null)
    setLoading(true)

    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) {
        throw new Error('Not authenticated')
      }

      apiClient.setToken(accessToken)

      // Build the messages array including conversation history + current message
      const allMessages = [
        ...messages.map(msg => {
          const message: any = {
            role: msg.type === 'user' ? 'user' : 'assistant',
            content: msg.content
          }
          if (msg.image) {
            message.image = msg.image
          }
          return message
        }),
        {
          role: 'user',
          content: userMessage.content,
          ...(userMessage.image && { image: userMessage.image })
        }
      ]

      const requestBody: any = {
        messages: allMessages,
        include_barn_context: true,
        horse_id: parseInt(horse.id),
        organization_id: selectedBarnId
      }

      const apiResponse = await apiClient.post('/api/v1/ai/chat', requestBody)

      if (!apiResponse.success) {
        throw new Error(apiResponse.error || 'Failed to get AI response')
      }

      const result = apiResponse.data as { response?: string }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: result.response || 'I apologize, but I encountered an error processing your request.',
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('AI chat error:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'I apologize, but I encountered an error. Please try again.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    }

    setLoading(false)
  }

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploadingImage(true)
    const reader = new FileReader()
    reader.onload = (e) => {
      setSelectedImage(e.target?.result as string)
      setUploadingImage(false)
    }
    reader.readAsDataURL(file)
  }

  const clearImage = () => {
    setSelectedImage(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
    if (cameraInputRef.current) cameraInputRef.current.value = ''
  }

  if (loadingHorse) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading horse data...</p>
        </div>
      </div>
    )
  }

  if (!selectedBarnId) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Barn Selected</h3>
        <p className="text-gray-600 mb-4">Please select a barn to view horse information.</p>
        <Link to="/horses" className="btn-primary">Back to Horses</Link>
      </div>
    )
  }

  if (!horse) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900 mb-2">Horse Not Found</h3>
        <p className="text-gray-600 mb-4">Unable to load horse information. Horse ID: {id}, Barn ID: {selectedBarnId}</p>
        <Link to="/horses" className="btn-primary">Back to Horses</Link>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full max-h-screen md:max-w-3xl md:mx-auto lg:max-w-4xl">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 md:w-12 md:h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <span className="text-white font-semibold text-lg">🤖</span>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">AI Assistant</h1>
              <p className="text-sm text-gray-600">Helping with {horse.name}</p>
            </div>
          </div>
          <Link
            to={`/horses/${horse.id}`}
            className="text-primary-600 hover:text-primary-700 text-sm font-medium"
          >
            Back to Profile
          </Link>
        </div>
      </div>

      {/* Horse Context Banner */}
      <div className="bg-blue-50 border-b border-blue-200 p-3">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <span className="text-blue-600 font-semibold">
              {horse.gender === 'mare' ? '♀' : horse.gender === 'stallion' ? '♂' : '⚲'}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-blue-900">{horse.name}</p>
            <p className="text-xs text-blue-700">
              {horse.breed && `${horse.breed} • `}
              {horse.age_display || (horse.age_years && `${horse.age_years} years`)}
              {horse.current_health_status && ` • Health: ${horse.current_health_status}`}
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.type === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              {message.image && (
                <img
                  src={message.image}
                  alt="Uploaded"
                  className="w-full rounded-lg mb-2 max-h-48 object-cover"
                />
              )}
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              <p className={`text-xs mt-1 ${
                message.type === 'user' ? 'text-primary-100' : 'text-gray-500'
              }`}>
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2 max-w-xs">
              <div className="flex items-center space-x-2">
                <div className="animate-bounce w-2 h-2 bg-gray-400 rounded-full"></div>
                <div className="animate-bounce w-2 h-2 bg-gray-400 rounded-full" style={{ animationDelay: '0.1s' }}></div>
                <div className="animate-bounce w-2 h-2 bg-gray-400 rounded-full" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-gray-50 border-t border-gray-200 px-4 py-2">
        <div className="flex space-x-2 overflow-x-auto md:flex-wrap md:overflow-x-visible md:gap-2">
          {[
            `What should I know about ${horse.name}?`,
            `Analyze ${horse.name}'s health status`,
            `Review ${horse.name}'s feeding plan`,
            `Training recommendations for ${horse.name}`
          ].map((suggestion, index) => (
            <button
              key={index}
              onClick={() => setInputText(suggestion)}
              className="flex-shrink-0 bg-white text-gray-700 text-xs px-3 py-1 rounded-full border border-gray-300 hover:bg-gray-50"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 p-4">
        {/* Image Preview */}
        {selectedImage && (
          <div className="mb-4 relative inline-block">
            <img
              src={selectedImage}
              alt="Selected"
              className="w-16 h-16 rounded-lg object-cover"
            />
            <button
              onClick={clearImage}
              className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs"
            >
              ×
            </button>
          </div>
        )}

        <div className="flex items-end space-x-3">
          {/* Image Upload Buttons */}
          <div className="flex space-x-2">
            {/* File Upload */}
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadingImage}
              className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              className="hidden"
            />

            {/* Camera Input */}
            <button
              onClick={() => cameraInputRef.current?.click()}
              disabled={uploadingImage}
              className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
            <input
              ref={cameraInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleImageUpload}
              className="hidden"
            />
          </div>

          {/* Text Input */}
          <div className="flex-1">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSendMessage()
                }
              }}
              placeholder={`Ask me anything about ${horse.name}...`}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              rows={1}
              disabled={loading}
            />
          </div>

          {/* Send Button */}
          <button
            onClick={handleSendMessage}
            disabled={(!inputText.trim() && !selectedImage) || loading}
            className="bg-primary-600 text-white p-2 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}