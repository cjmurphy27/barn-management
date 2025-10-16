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
    if (this.token === 'dev_token_placeholder') {
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
    const mockResponses: Record<string, any> = {
      // Horses endpoints
      '/horses/': {
        success: true,
        data: [
          {
            id: 1,
            name: "Thunder",
            breed: "Thoroughbred",
            age_years: 8,
            color: "Bay",
            active: true,
            owner_name: "John Smith",
            notes: "Excellent jumping horse",
            created_at: "2023-01-01T00:00:00Z"
          },
          {
            id: 2,
            name: "Lightning",
            breed: "Arabian",
            age_years: 6,
            color: "Chestnut",
            active: true,
            owner_name: "Jane Doe",
            notes: "Great for trail riding",
            created_at: "2023-02-01T00:00:00Z"
          },
          {
            id: 3,
            name: "Storm",
            breed: "Quarter Horse",
            age_years: 12,
            color: "Black",
            active: true,
            owner_name: "Bob Johnson",
            notes: "Calm and reliable",
            created_at: "2023-03-01T00:00:00Z"
          }
        ]
      },
      // Calendar endpoints
      '/calendar/upcoming': {
        success: true,
        data: [
          {
            id: 1,
            title: "Vet Checkup - Thunder",
            event_type: "medical",
            start_datetime: new Date(Date.now() + 86400000).toISOString(), // Tomorrow
            horse_id: 1,
            horse_name: "Thunder",
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