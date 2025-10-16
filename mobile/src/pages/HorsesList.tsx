import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { horseApi, apiClient } from '../services/api'

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
  profile_photo_path?: string
  current_location?: string
  stall_number?: string
  trainer_name?: string
  is_active?: boolean
  is_retired?: boolean
  is_for_sale?: boolean
  created_at: string
  updated_at: string

  // Legacy fields for compatibility
  age?: number
  status?: 'active' | 'inactive' | 'sold'
  photo_url?: string
}

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

interface HorsesListProps {
  user: User
  selectedBarnId: string | null
}

export default function HorsesList({ user, selectedBarnId }: HorsesListProps) {
  const [horses, setHorses] = useState<Horse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [horsePhotos, setHorsePhotos] = useState<Record<string, string>>({})

  useEffect(() => {
    if (user && selectedBarnId) {
      loadHorses()
    }
  }, [user, selectedBarnId])

  const loadHorses = async () => {
    if (!selectedBarnId) {
      console.log('No barn selected, skipping horse loading')
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) {
        throw new Error('Not authenticated')
      }

      // Set the authorization token for API calls
      apiClient.setToken(accessToken)

      // Use the selected barn ID directly
      const response = await horseApi.getAll(selectedBarnId)

      if (response.success) {
        const horsesData = (response.data as Horse[]) || []
        setHorses(horsesData)
        // Load photos for each horse
        loadHorsePhotos(horsesData, selectedBarnId)
      } else {
        throw new Error(response.error || 'Failed to load horses')
      }
    } catch (error) {
      console.error('Failed to load horses:', error)
      setError(error instanceof Error ? error.message : 'Failed to load horses')
      setHorses([])
    }

    setLoading(false)
  }

  const loadHorsePhotos = async (horsesData: Horse[], organizationId: string) => {
    const accessToken = localStorage.getItem('access_token')
    if (!accessToken) return

    const headers: Record<string, string> = accessToken === 'dev_token_placeholder'
      ? {}
      : { 'Authorization': `Bearer ${accessToken}` }

    const photoPromises = horsesData.map(async (horse) => {
      try {
        const photoUrl = `${import.meta.env.VITE_API_URL}/api/v1/horses/${horse.id}/photo?organization_id=${organizationId}`
        const response = await fetch(photoUrl, { headers })

        if (response.ok) {
          const blob = await response.blob()
          const photoDataUrl = URL.createObjectURL(blob)
          return { horseId: horse.id, photoUrl: photoDataUrl }
        }
      } catch (error) {
        console.error(`Failed to load photo for horse ${horse.id}:`, error)
      }
      return null
    })

    const photoResults = await Promise.all(photoPromises)
    const photoMap: Record<string, string> = {}

    photoResults.forEach((result) => {
      if (result) {
        photoMap[result.horseId] = result.photoUrl
      }
    })

    setHorsePhotos(photoMap)
  }

  const filteredHorses = horses.filter(horse =>
    horse.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    horse.breed?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    horse.color?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'inactive': return 'bg-yellow-100 text-yellow-800'
      case 'sold': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getGenderIcon = (gender?: string) => {
    switch (gender) {
      case 'mare': return '♀'
      case 'stallion': return '♂'
      case 'gelding': return '⚲'
      default: return '?'
    }
  }

  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case 'Excellent': return 'bg-green-100 text-green-800'
      case 'Good': return 'bg-blue-100 text-blue-800'
      case 'Fair': return 'bg-yellow-100 text-yellow-800'
      case 'Poor': return 'bg-orange-100 text-orange-800'
      case 'Critical': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getHealthStatusEmoji = (status: string) => {
    switch (status) {
      case 'Excellent': return '💚'
      case 'Good': return '💙'
      case 'Fair': return '💛'
      case 'Poor': return '🧡'
      case 'Critical': return '❤️'
      default: return '⚪'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading horses...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">
          <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Horses</h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={loadHorses}
          className="btn-primary"
        >
          Try Again
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">My Horses</h1>
        <Link
          to="/horses/new"
          className="bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium py-2 px-4 rounded-lg transition-colors"
        >
          + Add Horse
        </Link>
      </div>

      {/* Search */}
      <div className="relative">
        <input
          type="text"
          placeholder="Search horses..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="input-field pl-10"
        />
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <svg className="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
          </svg>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200 text-center">
          <div className="text-2xl font-bold text-gray-900">{horses.length}</div>
          <div className="text-sm text-gray-600">Total</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 text-center">
          <div className="text-2xl font-bold text-green-600">
            {horses.filter(h => h.status === 'active').length}
          </div>
          <div className="text-sm text-gray-600">Active</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 text-center">
          <div className="text-2xl font-bold text-yellow-600">
            {horses.filter(h => h.status === 'inactive').length}
          </div>
          <div className="text-sm text-gray-600">Inactive</div>
        </div>
      </div>

      {/* Horses List */}
      {filteredHorses.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {searchTerm ? 'No horses match your search' : 'No horses yet'}
          </h3>
          <p className="text-gray-600 mb-4">
            {searchTerm
              ? 'Try adjusting your search terms'
              : 'Add your first horse to get started managing your barn'
            }
          </p>
          {!searchTerm && (
            <Link to="/horses/new" className="btn-primary">
              Add Your First Horse
            </Link>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {filteredHorses.map((horse) => (
            <Link
              key={horse.id}
              to={`/horses/${horse.id}`}
              className="block bg-white p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:shadow-sm transition-all"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      {horsePhotos[horse.id] ? (
                        <img
                          src={horsePhotos[horse.id]}
                          alt={horse.name}
                          className="w-10 h-10 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                          <span className="text-primary-600 font-semibold text-lg">
                            {getGenderIcon(horse.gender)}
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <h3 className="text-lg font-medium text-gray-900 truncate">
                          {horse.name}
                        </h3>
                        {horse.barn_name && (
                          <span className="text-sm text-gray-500">({horse.barn_name})</span>
                        )}
                      </div>
                      <div className="flex items-center space-x-2 text-sm text-gray-600">
                        {horse.breed && <span>{horse.breed}</span>}
                        {(horse.age_display || horse.age) && (
                          <span>• {horse.age_display || `${horse.age} years`}</span>
                        )}
                        {horse.color && <span>• {horse.color}</span>}
                      </div>
                      {(horse.current_location || horse.stall_number || horse.trainer_name) && (
                        <div className="flex items-center space-x-2 text-xs text-gray-500">
                          {horse.current_location && <span>📍 {horse.current_location}</span>}
                          {horse.stall_number && <span>🏠 Stall {horse.stall_number}</span>}
                          {horse.trainer_name && <span>👤 {horse.trainer_name}</span>}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  {horse.current_health_status ? (
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getHealthStatusColor(horse.current_health_status)}`}>
                      {getHealthStatusEmoji(horse.current_health_status)} {horse.current_health_status}
                    </span>
                  ) : horse.status ? (
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(horse.status)}`}>
                      {horse.status}
                    </span>
                  ) : horse.is_active !== undefined ? (
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${horse.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {horse.is_active ? 'Active' : 'Inactive'}
                    </span>
                  ) : null}
                  <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}