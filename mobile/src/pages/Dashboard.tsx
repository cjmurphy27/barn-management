import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { horseApi, apiClient, buildApiUrl } from '../services/api'

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
}

interface UpcomingEvent {
  id: number
  title: string
  event_type: 'veterinary' | 'farrier' | 'dental' | 'supply_delivery' | 'training' | 'breeding' | 'health_treatment' | 'other'
  scheduled_date: string
  horse_name?: string
  description?: string
}

interface LatestMessage {
  id: number
  title: string
  content: string
  author_name: string
  created_at: string
  category: string
  comments_count: number
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

interface DashboardProps {
  user: User
  selectedBarnId: string | null
}

const EVENT_TYPE_ICONS = {
  veterinary: '🏥',
  farrier: '🔨',
  dental: '🦷',
  supply_delivery: '🚛',
  training: '⭐',
  breeding: '🐴',
  health_treatment: '💊',
  other: '📅'
}

const getHealthStatusColor = (status?: string) => {
  switch (status) {
    case 'Excellent': return 'text-green-600 bg-green-50 border-green-200'
    case 'Good': return 'text-blue-600 bg-blue-50 border-blue-200'
    case 'Fair': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    case 'Poor': return 'text-orange-600 bg-orange-50 border-orange-200'
    case 'Critical': return 'text-red-600 bg-red-50 border-red-200'
    default: return 'text-gray-600 bg-gray-50 border-gray-200'
  }
}

export default function Dashboard({ user, selectedBarnId }: DashboardProps) {
  const [horses, setHorses] = useState<Horse[]>([])
  const [upcomingEvents, setUpcomingEvents] = useState<UpcomingEvent[]>([])
  const [latestMessages, setLatestMessages] = useState<LatestMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [eventsLoading, setEventsLoading] = useState(true)
  const [messagesLoading, setMessagesLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [horsePhotos, setHorsePhotos] = useState<Record<string, string>>({})
  const [showUpcomingEvents, setShowUpcomingEvents] = useState(true)
  const [showLatestMessages, setShowLatestMessages] = useState(true)

  useEffect(() => {
    if (selectedBarnId) {
      loadHorses()
      loadUpcomingEvents()
      loadLatestMessages()
    }
  }, [selectedBarnId])

  const loadUpcomingEvents = async () => {
    if (!selectedBarnId) return

    setEventsLoading(true)
    try {
      const accessToken = localStorage.getItem('access_token')
      const headers: Record<string, string> = accessToken === 'dev_token_placeholder'
        ? {}
        : { 'Authorization': `Bearer ${accessToken}` }

      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/calendar/upcoming?organization_id=${selectedBarnId}&days_ahead=7&limit=5`,
        { headers }
      )

      if (response.ok) {
        const data = await response.json()
        setUpcomingEvents(data.upcoming_events || [])
      } else {
        console.error('Failed to load upcoming events')
      }
    } catch (error) {
      console.error('Error loading upcoming events:', error)
    }
    setEventsLoading(false)
  }

  const loadLatestMessages = async () => {
    if (!selectedBarnId) return

    setMessagesLoading(true)
    try {
      const accessToken = localStorage.getItem('access_token')
      const headers: Record<string, string> = accessToken === 'dev_token_placeholder'
        ? {}
        : { 'Authorization': `Bearer ${accessToken}` }

      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/whiteboard/posts?organization_id=${selectedBarnId}&limit=2`,
        { headers }
      )

      if (response.ok) {
        const data = await response.json()
        setLatestMessages((data.posts || []).slice(0, 2))
      } else {
        console.error('Failed to load latest messages')
      }
    } catch (error) {
      console.error('Error loading latest messages:', error)
    }
    setMessagesLoading(false)
  }

  const loadHorses = async () => {
    if (!selectedBarnId) {
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

      apiClient.setToken(accessToken)
      const response = await horseApi.getAll(selectedBarnId)

      if (response.success) {
        const horsesData = (response.data as Horse[]) || []
        setHorses(horsesData)
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
    if (!accessToken || accessToken === 'dev_token_placeholder') return

    const photoPromises = horsesData
      .map(async (horse) => {
        try {
          const photoUrl = buildApiUrl(`/api/v1/horses/${horse.id}/photo?organization_id=${organizationId}`)
          const response = await fetch(photoUrl, {
            headers: { 'Authorization': `Bearer ${accessToken}` }
          })

          if (response.ok) {
            const blob = await response.blob()
            const objectUrl = URL.createObjectURL(blob)
            return { horseId: horse.id, photoUrl: objectUrl }
          }
        } catch (error) {
          console.error(`Failed to load photo for horse ${horse.id}:`, error)
        }
        return null
      })

    const photos = await Promise.all(photoPromises)
    const photoMap: Record<string, string> = {}

    photos.forEach(photo => {
      if (photo) {
        photoMap[photo.horseId] = photo.photoUrl
      }
    })

    setHorsePhotos(photoMap)
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    })
  }

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }

  const formatRelativeTime = (dateStr: string) => {
    const now = new Date()
    const date = new Date(dateStr)
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffMinutes = Math.floor(diffMs / (1000 * 60))

    if (diffDays > 0) {
      return `${diffDays}d ago`
    } else if (diffHours > 0) {
      return `${diffHours}h ago`
    } else if (diffMinutes > 0) {
      return `${diffMinutes}m ago`
    } else {
      return 'Just now'
    }
  }

  const filteredHorses = horses.filter(horse =>
    horse.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    horse.breed?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    horse.color?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const displayedHorses = searchTerm ? filteredHorses : filteredHorses.slice(0, 5)
  const hasMoreHorses = !searchTerm && filteredHorses.length > 5

  const totalHorses = horses.length
  const activeHorses = horses.filter(horse => horse.is_active !== false).length
  const retiredHorses = horses.filter(horse => horse.is_retired === true).length
  const forSaleHorses = horses.filter(horse => horse.is_for_sale === true).length

  if (!selectedBarnId) {
    return (
      <div className="flex items-center justify-center min-h-[200px]">
        <div className="text-center">
          <div className="text-gray-400 mb-2">
            <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-1">No Barn Selected</h3>
          <p className="text-gray-600">Please select a barn to view your dashboard</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Upcoming Events Section */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">📅 Upcoming Events</h2>
          <button
            onClick={() => setShowUpcomingEvents(!showUpcomingEvents)}
            className="text-primary-600 text-sm font-medium"
          >
            {showUpcomingEvents ? 'Hide' : 'Show'}
          </button>
        </div>

        {showUpcomingEvents && (
          <div>
            {eventsLoading ? (
              <div className="text-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mx-auto"></div>
              </div>
            ) : upcomingEvents.length > 0 ? (
              <div className="space-y-3">
                {upcomingEvents.map((event) => (
                  <div key={event.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <span className="text-lg">{EVENT_TYPE_ICONS[event.event_type]}</span>
                      <div>
                        <p className="font-medium text-gray-900">{event.title}</p>
                        {event.horse_name && (
                          <p className="text-sm text-gray-600">🐴 {event.horse_name}</p>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">{formatDate(event.scheduled_date)}</p>
                      <p className="text-xs text-gray-600">{formatTime(event.scheduled_date)}</p>
                    </div>
                  </div>
                ))}
                <Link
                  to="/calendar"
                  className="block text-center text-primary-600 text-sm font-medium py-2 hover:text-primary-700"
                >
                  View Full Calendar →
                </Link>
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500">
                <p>No upcoming events in the next 7 days</p>
                <Link to="/calendar" className="text-primary-600 text-sm font-medium hover:text-primary-700">
                  Add an event →
                </Link>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Latest Messages Section */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">💬 Latest Messages</h2>
          <button
            onClick={() => setShowLatestMessages(!showLatestMessages)}
            className="text-primary-600 text-sm font-medium"
          >
            {showLatestMessages ? 'Hide' : 'Show'}
          </button>
        </div>

        {showLatestMessages && (
          <div>
            {messagesLoading ? (
              <div className="text-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mx-auto"></div>
              </div>
            ) : latestMessages.length > 0 ? (
              <div className="space-y-3">
                {latestMessages.map((message) => (
                  <Link
                    key={message.id}
                    to={`/messages/${message.id}`}
                    className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">{message.title}</p>
                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                          {message.content.substring(0, 100)}...
                        </p>
                        <div className="flex items-center space-x-3 mt-2 text-xs text-gray-500">
                          <span>👤 {message.author_name}</span>
                          {message.category && <span>📂 {message.category}</span>}
                          {message.comments_count > 0 && (
                            <span>💬 {message.comments_count} comments</span>
                          )}
                        </div>
                      </div>
                      <div className="text-right ml-3">
                        <p className="text-xs text-gray-500">{formatRelativeTime(message.created_at)}</p>
                      </div>
                    </div>
                  </Link>
                ))}
                <Link
                  to="/messages"
                  className="block text-center text-primary-600 text-sm font-medium py-2 hover:text-primary-700"
                >
                  View All Messages →
                </Link>
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500">
                <p>No messages yet</p>
                <Link to="/messages" className="text-primary-600 text-sm font-medium hover:text-primary-700">
                  Start a conversation →
                </Link>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Horse Statistics */}
      <div className="grid grid-cols-2 gap-4">
        <div className="card text-center">
          <div className="text-2xl font-bold text-primary-600">{totalHorses}</div>
          <div className="text-sm text-gray-600">Total Horses</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-green-600">{activeHorses}</div>
          <div className="text-sm text-gray-600">Active</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-orange-600">{retiredHorses}</div>
          <div className="text-sm text-gray-600">Retired</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-blue-600">{forSaleHorses}</div>
          <div className="text-sm text-gray-600">For Sale</div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">🐴 Horse Directory</h2>
          <Link to="/add-horse" className="text-primary-600 text-sm font-medium">
            Add Horse +
          </Link>
        </div>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            placeholder="Search horses by name, breed, or color..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>

      {/* Horses List */}
      {loading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      ) : error ? (
        <div className="card text-center py-8">
          <div className="text-red-600 mb-2">⚠️</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Horses</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button onClick={loadHorses} className="btn-primary">
            Try Again
          </button>
        </div>
      ) : displayedHorses.length === 0 ? (
        <div className="card text-center py-8">
          {horses.length === 0 ? (
            <>
              <div className="text-gray-400 mb-4">🐴</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Horses Found</h3>
              <p className="text-gray-600 mb-4">Get started by adding your first horse to the barn.</p>
              <Link to="/add-horse" className="btn-primary">
                Add First Horse
              </Link>
            </>
          ) : (
            <>
              <div className="text-gray-400 mb-4">🔍</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Results Found</h3>
              <p className="text-gray-600">Try adjusting your search terms.</p>
            </>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {displayedHorses.map((horse) => (
            <div key={horse.id} className="card">
              <div className="flex items-start space-x-4">
                {/* Horse Photo */}
                <div className="flex-shrink-0">
                  {horsePhotos[horse.id] ? (
                    <img
                      src={horsePhotos[horse.id]}
                      alt={horse.name}
                      className="w-16 h-16 rounded-lg object-cover"
                    />
                  ) : (
                    <div className="w-16 h-16 bg-gray-200 rounded-lg flex items-center justify-center">
                      <span className="text-gray-400 text-2xl">🐴</span>
                    </div>
                  )}
                </div>

                {/* Horse Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 truncate">
                        {horse.name}
                      </h3>
                      <div className="mt-1 space-y-1">
                        {horse.breed && (
                          <p className="text-sm text-gray-600">{horse.breed}</p>
                        )}
                        <div className="flex items-center space-x-3 text-sm text-gray-500">
                          {horse.age_display && <span>🎂 {horse.age_display}</span>}
                          {horse.color && <span>🎨 {horse.color}</span>}
                          {horse.gender && <span>⚥ {horse.gender}</span>}
                        </div>
                        {(horse.current_location || horse.stall_number) && (
                          <p className="text-sm text-gray-500">
                            📍 {horse.current_location || 'Stall'} {horse.stall_number}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Health Status */}
                    {horse.current_health_status && (
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getHealthStatusColor(horse.current_health_status)}`}>
                        {horse.current_health_status}
                      </span>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="mt-3 flex space-x-2">
                    <Link
                      to={`/horses/${horse.id}`}
                      className="btn-primary text-sm py-1 px-3"
                    >
                      View Details
                    </Link>
                    <Link
                      to={`/horses/${horse.id}/ai`}
                      className="btn-secondary text-sm py-1 px-3"
                    >
                      🤖 Ask AI
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          ))}
          {hasMoreHorses && (
            <div className="text-center pt-4">
              <Link
                to="/horses"
                className="text-primary-600 text-sm font-medium hover:text-primary-700"
              >
                View All {filteredHorses.length} Horses →
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  )
}