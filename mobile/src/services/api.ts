// API service for communicating with FastAPI backend

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '') // Remove trailing slash

// Helper function to build API URLs with proper slash handling
export const buildApiUrl = (path: string): string => {
  const baseUrl = API_BASE_URL
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  // Don't replace double slashes in the protocol (https://)
  const fullUrl = `${baseUrl}${cleanPath}`
  return fullUrl.replace(/([^:]\/)\/+/g, '$1').replace(/\/$/, '')
}

// Note: Organization ID will be dynamically obtained from authenticated user

interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

// Base API client
// Mock data for development mode - defined at module level to persist across requests
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

const mockSupplies = [
  {
    id: 1,
    uuid: "supply-1",
    name: "Premium Horse Feed",
    description: "High-quality grain feed for adult horses",
    category: "feed_nutrition",
    brand: "Purina",
    unit_type: "bags",
    package_size: 50,
    package_unit: "lbs",
    current_stock: 12,
    min_stock_level: 5,
    reorder_point: 3,
    last_cost_per_unit: 18.99,
    storage_location: "Feed Room",
    is_low_stock: false,
    is_out_of_stock: false
  },
  {
    id: 2,
    uuid: "supply-2",
    name: "Pine Shavings",
    description: "Natural bedding material",
    category: "bedding",
    brand: "Tractor Supply",
    unit_type: "bales",
    current_stock: 2,
    min_stock_level: 8,
    reorder_point: 4,
    last_cost_per_unit: 7.50,
    storage_location: "Barn Storage",
    is_low_stock: true,
    is_out_of_stock: false
  },
  {
    id: 3,
    uuid: "supply-3",
    name: "Fly Spray",
    description: "Insect repellent for horses",
    category: "health_medical",
    brand: "Farnam",
    unit_type: "bottles",
    current_stock: 0,
    min_stock_level: 3,
    reorder_point: 2,
    last_cost_per_unit: 12.95,
    storage_location: "Tack Room",
    is_low_stock: false,
    is_out_of_stock: true
  }
]

const mockEvents = [
  {
    id: 1,
    uuid: "event-1",
    event_type: "veterinary",
    title: "Vet Checkup - Ace",
    description: "Annual health checkup",
    scheduled_date: new Date(Date.now() + 86400000).toISOString(), // Tomorrow
    duration_minutes: 60,
    horse_id: 1,
    horse_name: "Ace",
    horse: { horse_id: "1", horse_name: "Ace", barn_id: "1" }
  },
  {
    id: 2,
    uuid: "event-2",
    event_type: "training",
    title: "Training Session - Lightning",
    description: "Jumping practice",
    scheduled_date: new Date(Date.now() + 172800000).toISOString(), // Day after tomorrow
    duration_minutes: 90,
    horse_id: 2,
    horse_name: "Lightning",
    horse: { horse_id: "2", horse_name: "Lightning", barn_id: "1" }
  },
  {
    id: 3,
    uuid: "event-3",
    event_type: "farrier",
    title: "Horseshoeing - Storm",
    description: "Regular horseshoeing appointment",
    scheduled_date: new Date(Date.now() + 259200000).toISOString(), // 3 days from now
    duration_minutes: 45,
    horse_id: 3,
    horse_name: "Storm",
    horse: { horse_id: "3", horse_name: "Storm", barn_id: "1" }
  },
  {
    id: 4,
    uuid: "event-4",
    event_type: "dental",
    title: "Dental Check - All Horses",
    description: "Annual dental examination",
    scheduled_date: new Date(Date.now() + 604800000).toISOString(), // 1 week from now
    duration_minutes: 120
  },
  {
    id: 5,
    uuid: "event-5",
    event_type: "supply_delivery",
    title: "Feed Delivery",
    description: "Monthly feed delivery",
    scheduled_date: new Date(Date.now() + 1209600000).toISOString(), // 2 weeks from now
    duration_minutes: 30
  }
]

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

    const url = buildApiUrl(endpoint)

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

    const mockResponses: Record<string, any> = {
      // Horses endpoints
      '/horses/': {
        success: true,
        data: mockHorses
      },
      '/horses?': {
        success: true,
        data: { horses: mockHorses }
      },
      // Calendar endpoints
      '/calendar/events': {
        success: true,
        data: mockEvents
      },
      '/calendar/upcoming': {
        success: true,
        data: mockEvents.slice(0, 3)
      },
      '/api/v1/calendar/events': {
        success: true,
        data: mockEvents
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

    // Handle POST requests (creating events)
    if (options.method === 'POST' && endpoint.includes('/api/v1/calendar/events')) {
      const newEventData = JSON.parse(options.body as string || '{}')
      const newEvent = {
        id: mockEvents.length + 1,
        uuid: `event-${mockEvents.length + 1}`,
        ...newEventData,
        horse: newEventData.horse_id ?
          mockHorses.find(h => h.id === newEventData.horse_id.toString()) :
          undefined
      }
      mockEvents.push(newEvent)
      return Promise.resolve({
        success: true,
        data: newEvent as T
      })
    }

    // Handle POST requests (creating supplies)
    if (options.method === 'POST' && endpoint.includes('/api/v1/supplies')) {
      const newSupplyData = JSON.parse(options.body as string || '{}')
      const newSupply = {
        id: mockSupplies.length + 1,
        uuid: `supply-${mockSupplies.length + 1}`,
        is_low_stock: (newSupplyData.current_stock || 0) <= (newSupplyData.reorder_point || 0),
        is_out_of_stock: (newSupplyData.current_stock || 0) === 0,
        ...newSupplyData
      }
      mockSupplies.push(newSupply)
      return Promise.resolve({
        success: true,
        data: newSupply as T
      })
    }

    // Handle GET requests for supplies
    if (options.method === 'GET' && endpoint.includes('/api/v1/supplies/')) {
      return Promise.resolve({
        success: true,
        data: mockSupplies as T
      })
    }

    // Handle GET requests for supplies dashboard
    if (endpoint.includes('/api/v1/supplies/dashboard')) {
      const dashboardData = {
        total_supplies: mockSupplies.length,
        low_stock_count: mockSupplies.filter(s => s.is_low_stock).length,
        out_of_stock_count: mockSupplies.filter(s => s.is_out_of_stock).length,
        total_inventory_value: mockSupplies.reduce((total, s) => total + (s.current_stock * (s.last_cost_per_unit || 0)), 0),
        monthly_spending: 1234.56,
        top_categories: [
          { category: "feed_nutrition", amount: 850.00 },
          { category: "bedding", amount: 245.50 }
        ],
        recent_transactions: [],
        low_stock_items: mockSupplies.filter(s => s.is_low_stock)
      }
      return Promise.resolve({
        success: true,
        data: dashboardData as T
      })
    }

    // Handle receipt processing (mock)
    if (endpoint.includes('/api/v1/supplies/transactions/process-receipt')) {
      // Return mock receipt processing result
      const mockReceiptResult = {
        vendor_name: "Chipaway Stables, Inc.",
        purchase_date: new Date().toISOString().split('T')[0],
        total_amount: 2899.76,
        line_items: [
          {
            description: "Corn 1st cut",
            quantity: "25",
            unit: "bags",
            unit_price: 18.50,
            category: "feed_nutrition"
          }
        ]
      }
      return Promise.resolve({
        success: true,
        data: mockReceiptResult as T
      })
    }

    // Handle DELETE requests (deleting events)
    if (options.method === 'DELETE' && endpoint.includes('/api/v1/calendar/events/')) {
      const eventIdMatch = endpoint.match(/\/api\/v1\/calendar\/events\/(\d+)/)
      if (eventIdMatch) {
        const eventId = parseInt(eventIdMatch[1])
        const index = mockEvents.findIndex(e => e.id === eventId)
        if (index !== -1) {
          mockEvents.splice(index, 1)
          return Promise.resolve({
            success: true,
            message: 'Event deleted successfully' as T
          } as any)
        }
      }
      return Promise.resolve({
        success: false,
        error: 'Event not found' as T
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

  async postFormData<T>(endpoint: string, formData: FormData): Promise<ApiResponse<T>> {
    const headers: Record<string, string> = {}
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }
    // Don't set Content-Type for FormData - let browser set it

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers,
        body: formData
      })

      const result = await response.json()

      if (response.ok) {
        return { success: true, data: result }
      } else {
        return { success: false, error: result.message || 'Upload failed' }
      }
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Upload failed' }
    }
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

// Calendar events API
export const calendarApi = {
  getEvents: (organizationId: string) => apiClient.get(`/api/v1/calendar/events?organization_id=${organizationId}`),
  getUpcoming: (organizationId: string) => apiClient.get(`/api/v1/calendar/upcoming?organization_id=${organizationId}`),
  create: (data: any, organizationId: string) => apiClient.post(`/api/v1/calendar/events?organization_id=${organizationId}`, data),
  update: (id: number, data: any, organizationId: string) => apiClient.put(`/api/v1/calendar/events/${id}?organization_id=${organizationId}`, data),
  delete: (id: number, organizationId: string) => apiClient.delete(`/api/v1/calendar/events/${id}?organization_id=${organizationId}`),
}

// Supplies API functions
export const suppliesApi = {
  getAll: (organizationId: string) => apiClient.get(`/api/v1/supplies/?organization_id=${organizationId}&active_only=false`),
  getDashboard: (organizationId: string) => apiClient.get(`/api/v1/supplies/dashboard?organization_id=${organizationId}`),
  create: (data: any, organizationId: string) => apiClient.post(`/api/v1/supplies/`, { ...data, organization_id: organizationId }),
  update: (id: string, data: any, organizationId: string) => apiClient.put(`/api/v1/supplies/${id}`, { ...data, organization_id: organizationId }),
  delete: (id: string, organizationId: string) => apiClient.delete(`/api/v1/supplies/${id}?organization_id=${organizationId}`),
  processReceipt: (formData: FormData, organizationId: string) => {
    return apiClient.postFormData(`/api/v1/supplies/transactions/process-receipt`, formData)
  }
}

export default apiClient