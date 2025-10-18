// API service for communicating with FastAPI backend

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

// Note: Organization ID will be dynamically obtained from authenticated user

interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

// Base API client
class ApiClient {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  setToken(token: string | null) {
    this.token = token
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    // Handle development mode - return mock data
    const isDevelopment = this.token === 'dev_token_placeholder' ||
                         this.baseUrl.includes('localhost:8002') ||
                         import.meta.env.DEV

    if (isDevelopment) {
      return this.getMockData<T>(endpoint, options)
    }

    const url = `${this.baseUrl}${endpoint}`

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    }

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      })

      const data = await response.json()

      if (!response.ok) {
        return {
          success: false,
          error: data.detail || `HTTP ${response.status}: ${response.statusText}`,
        }
      }

      return {
        success: true,
        data,
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error',
      }
    }
  }

  private getMockData<T>(endpoint: string, options: RequestInit): Promise<ApiResponse<T>> {
    // Mock data for development mode
    const mockHorses = [
      {
        id: "1",
        name: "Ace",
        breed: "Paint",
        age_years: 22,
        age_display: "22 years, 3 months",
        color: "Black and White",
        gender: "gelding" as const,
        current_health_status: "Good" as const,
        active: true,
        owner_name: "John Smith",
        notes: "Excellent jumping horse",
        created_at: "2023-01-01T00:00:00Z",
        updated_at: "2023-01-01T00:00:00Z"
      },
      {
        id: "2",
        name: "Lightning",
        breed: "Arabian",
        age_years: 6,
        age_display: "6 years",
        color: "Chestnut",
        gender: "mare" as const,
        current_health_status: "Excellent" as const,
        active: true,
        owner_name: "Jane Doe",
        notes: "Great for trail riding",
        created_at: "2023-02-01T00:00:00Z",
        updated_at: "2023-02-01T00:00:00Z"
      },
      {
        id: "3",
        name: "Storm",
        breed: "Quarter Horse",
        age_years: 12,
        age_display: "12 years",
        color: "Black",
        gender: "stallion" as const,
        current_health_status: "Good" as const,
        active: true,
        owner_name: "Bob Johnson",
        notes: "Calm and reliable",
        created_at: "2023-03-01T00:00:00Z",
        updated_at: "2023-03-01T00:00:00Z"
      }
    ]

    const mockResponses: Record<string, any> = {
      // Horses endpoints
      '/horses/': {
        success: true,
        data: mockHorses
      },
      // Calendar endpoints
      '/calendar/upcoming': {
        success: true,
        data: [
          {
            id: 1,
            title: "Vet Checkup - Ace",
            event_type: "medical",
            start_datetime: new Date(Date.now() + 86400000).toISOString(), // Tomorrow
            horse_id: 1,
            horse_name: "Ace",
            description: "Annual health checkup"
          },
          {
            id: 2,
            title: "Training Session - Lightning",
            event_type: "training",
            start_datetime: new Date(Date.now() + 172800000).toISOString(), // Day after tomorrow
            horse_id: 2,
            horse_name: "Lightning",
            description: "Jumping practice"
          }
        ]
      }
    }

    // Handle individual horse lookups (e.g., /api/v1/horses/1)
    const horseIdMatch = endpoint.match(/\/horses\/(\d+)/)
    if (horseIdMatch) {
      const horseId = horseIdMatch[1]
      const horse = mockHorses.find(h => h.id === horseId)
      if (horse) {
        return Promise.resolve({
          success: true,
          data: horse as T
        })
      } else {
        return Promise.resolve({
          success: false,
          error: "Horse not found"
        })
      }
    }

    // Handle horses list lookups (e.g., /api/v1/horses/?active_only=true&...)
    if (endpoint.includes('/horses/') && (endpoint.includes('active_only') || endpoint.includes('?'))) {
      return Promise.resolve({
        success: true,
        data: mockHorses as T
      })
    }

    // Handle AI chat requests
    if (endpoint.includes('/ai/chat')) {
      const requestData = JSON.parse(options.body as string || '{}')
      const messages = requestData.messages || []
      const horseId = requestData.horse_id

      // Find the latest user message
      const latestUserMessage = messages.reverse().find((msg: any) => msg.role === 'user')?.content || 'Hello'

      // Get horse context if horse_id is provided
      let horseContext = ''
      if (horseId) {
        const horse = mockHorses.find(h => h.id === horseId.toString())
        if (horse) {
          horseContext = `Based on ${horse.name}'s profile (${horse.breed}, ${horse.age_display}, ${horse.color} ${horse.gender}), `
        }
      }

      // Generate contextual mock response
      let mockResponse = ''
      const lowerMessage = latestUserMessage.toLowerCase()

      if (lowerMessage.includes('feed') || lowerMessage.includes('eat')) {
        mockResponse = `${horseContext}I recommend a balanced diet of quality hay, grain appropriate for their activity level, and fresh water. For horses in good health, about 1.5-3% of body weight in forage daily is ideal. Make sure to feed smaller, more frequent meals rather than large ones.`
      } else if (lowerMessage.includes('health') || lowerMessage.includes('condition')) {
        mockResponse = `${horseContext}Regular health monitoring is essential. I suggest monthly weight checks, daily observation for changes in appetite or behavior, and maintaining a consistent vaccination and deworming schedule with your veterinarian.`
      } else if (lowerMessage.includes('training') || lowerMessage.includes('exercise')) {
        mockResponse = `${horseContext}A consistent training routine that matches the horse's fitness level and experience is important. Start with 20-30 minutes of work and gradually increase. Always include proper warm-up and cool-down periods.`
      } else if (lowerMessage.includes('know') || lowerMessage.includes('about')) {
        mockResponse = `${horseContext}This is a wonderful horse with good overall health status. Key things to monitor include their eating habits, social interactions with other horses, and any changes in their regular behavior patterns. Regular grooming and hoof care are also essential.`
      } else if (lowerMessage.includes('much hay') || lowerMessage.includes('should') && lowerMessage.includes('eat')) {
        mockResponse = `${horseContext}A horse should eat approximately 2-3% of their body weight in hay per day. For a 1000-pound horse, that's about 20-30 pounds of hay daily. Split this into multiple feedings throughout the day for better digestion.`
      } else {
        mockResponse = `${horseContext}Thank you for your question about "${latestUserMessage}". In development mode, I can provide general guidance on horse care, health, feeding, and training. For specific medical concerns, always consult with a qualified veterinarian.`
      }

      return Promise.resolve({
        success: true,
        response: mockResponse
      } as any)
    }

    // Find matching mock response
    for (const [pattern, response] of Object.entries(mockResponses)) {
      if (endpoint.includes(pattern)) {
        return Promise.resolve(response)
      }
    }

    // Default mock response
    return Promise.resolve({
      success: true,
      data: [] as T
    })
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' })
  }

  async post<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async put<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }
}

// Create API client instance
export const apiClient = new ApiClient(API_BASE_URL)

// Horse API functions
export const horseApi = {
  getAll: (organizationId: string) => apiClient.get(`/api/v1/horses/?active_only=true&sort_by=age_years&sort_order=asc&limit=100&organization_id=${organizationId}`),
  getById: (id: string, organizationId: string) => apiClient.get(`/api/v1/horses/${id}?organization_id=${organizationId}`),
  create: (data: any, organizationId: string) => apiClient.post('/api/v1/horses', { ...data, organization_id: organizationId }),
  update: (id: string, data: any, organizationId: string) => apiClient.put(`/api/v1/horses/${id}`, { ...data, organization_id: organizationId }),
  delete: (id: string, organizationId: string) => apiClient.delete(`/api/v1/horses/${id}?organization_id=${organizationId}`),
}

// Medical records API
export const medicalApi = {
  getByHorseId: (horseId: string) => apiClient.get(`/horses/${horseId}/medical`),
  create: (data: any) => apiClient.post('/medical', data),
  update: (id: string, data: any) => apiClient.put(`/medical/${id}`, data),
  delete: (id: string) => apiClient.delete(`/medical/${id}`),
}

// Feed records API
export const feedApi = {
  getByHorseId: (horseId: string) => apiClient.get(`/horses/${horseId}/feed`),
  create: (data: any) => apiClient.post('/feed', data),
  update: (id: string, data: any) => apiClient.put(`/feed/${id}`, data),
  delete: (id: string) => apiClient.delete(`/feed/${id}`),
}

// Training sessions API
export const trainingApi = {
  getByHorseId: (horseId: string) => apiClient.get(`/horses/${horseId}/training`),
  create: (data: any) => apiClient.post('/training', data),
  update: (id: string, data: any) => apiClient.put(`/training/${id}`, data),
  delete: (id: string) => apiClient.delete(`/training/${id}`),
}

export default apiClient