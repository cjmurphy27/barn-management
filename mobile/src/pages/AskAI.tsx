import { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { apiClient } from '../services/api'

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

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  image?: string
  timestamp: Date
}

interface AskAIProps {
  user: User
  selectedBarnId: string | null
}

export default function AskAI({ user, selectedBarnId }: AskAIProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputText, setInputText] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [uploadingImage, setUploadingImage] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const cameraInputRef = useRef<HTMLInputElement>(null)

  const handleSendMessage = async () => {
    if ((!inputText.trim() && !selectedImage) || loading) return

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
        include_barn_context: true
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
              <h1 className="text-lg font-semibold text-gray-900">Ask AI</h1>
              <p className="text-sm text-gray-600">Your intelligent stable assistant</p>
            </div>
          </div>
          <Link
            to="/horses"
            className="text-primary-600 hover:text-primary-700 text-sm font-medium"
          >
            Back to Horses
          </Link>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-white text-2xl">🤖</span>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Welcome to AI Assistant!
            </h3>
            <p className="text-gray-600 mb-4 max-w-md mx-auto">
              I can help you with questions about your horses, analyze photos, review documents, and provide insights about horse care and management.
            </p>
            <div className="bg-blue-50 rounded-lg p-4 max-w-sm mx-auto">
              <p className="text-sm text-blue-800 font-medium mb-2">Try asking:</p>
              <ul className="text-xs text-blue-700 space-y-1 text-left">
                <li>• "What should I know about this horse?"</li>
                <li>• "Analyze this photo of my horse"</li>
                <li>• "Review health documents"</li>
                <li>• "Feeding recommendations"</li>
              </ul>
            </div>
          </div>
        ) : (
          messages.map((message) => (
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
          ))
        )}

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
              placeholder="Ask me anything about your horses..."
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