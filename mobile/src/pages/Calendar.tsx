import { useState, useEffect } from 'react'

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
  horse_id: string
  horse_name: string
  barn_id: string
}

interface CalendarEvent {
  id: number
  uuid: string
  event_type: 'veterinary' | 'farrier' | 'dental' | 'supply_delivery' | 'training' | 'breeding' | 'health_treatment' | 'other'
  title: string
  description?: string
  scheduled_date: string
  duration_minutes?: number
  horse_id?: number
  horse_name?: string
  horse?: Horse
}

interface CalendarProps {
  user: User
  selectedBarnId: string | null
}

const EVENT_TYPES = {
  veterinary: { label: 'Vet Visit', emoji: '🩺', color: 'bg-red-100 text-red-800' },
  farrier: { label: 'Farrier', emoji: '🔨', color: 'bg-yellow-100 text-yellow-800' },
  dental: { label: 'Dental', emoji: '🦷', color: 'bg-blue-100 text-blue-800' },
  supply_delivery: { label: 'Supply Delivery', emoji: '📦', color: 'bg-orange-100 text-orange-800' },
  training: { label: 'Training', emoji: '🏇', color: 'bg-purple-100 text-purple-800' },
  breeding: { label: 'Breeding', emoji: '🐴', color: 'bg-pink-100 text-pink-800' },
  health_treatment: { label: 'Health Treatment', emoji: '💊', color: 'bg-green-100 text-green-800' },
  other: { label: 'Other', emoji: '📝', color: 'bg-gray-100 text-gray-800' }
}

export default function Calendar({ user, selectedBarnId }: CalendarProps) {
  const [activeTab, setActiveTab] = useState<'upcoming' | 'calendar' | 'add'>('upcoming')
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [horses, setHorses] = useState<Horse[]>([])
  const [loading, setLoading] = useState(false)
  const [currentDate, setCurrentDate] = useState(new Date())
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null)
  const [showEventModal, setShowEventModal] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)

  // Form state for add/edit event
  const [formData, setFormData] = useState({
    event_type: 'veterinary' as keyof typeof EVENT_TYPES,
    title: '',
    description: '',
    scheduled_date: '',
    scheduled_time: '',
    duration_minutes: '',
    horse_id: ''
  })

  useEffect(() => {
    if (selectedBarnId) {
      fetchEvents()
      fetchHorses()
    }
  }, [selectedBarnId])

  const fetchEvents = async () => {
    if (!selectedBarnId) return

    setLoading(true)
    try {
      const accessToken = localStorage.getItem('access_token')
      const headers: Record<string, string> = accessToken === 'dev_token_placeholder'
        ? {}
        : { 'Authorization': `Bearer ${accessToken}` }

      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/calendar/events?organization_id=${selectedBarnId}`,
        { headers }
      )

      if (response.ok) {
        const data = await response.json()
        setEvents(data || [])
      }
    } catch (error) {
      console.error('Error fetching events:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchHorses = async () => {
    if (!selectedBarnId) return

    try {
      const accessToken = localStorage.getItem('access_token')
      const headers: Record<string, string> = accessToken === 'dev_token_placeholder'
        ? {}
        : { 'Authorization': `Bearer ${accessToken}` }

      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/horses?organization_id=${selectedBarnId}`,
        { headers }
      )

      if (response.ok) {
        const data = await response.json()
        setHorses(data.horses || [])
      }
    } catch (error) {
      console.error('Error fetching horses:', error)
    }
  }

  const handleAddEvent = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedBarnId) return

    try {
      const accessToken = localStorage.getItem('access_token')
      const headers: Record<string, string> = accessToken === 'dev_token_placeholder'
        ? { 'Content-Type': 'application/json' }
        : {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }

      // Combine date and time into scheduled_date
      const dateTimeString = formData.scheduled_time
        ? `${formData.scheduled_date}T${formData.scheduled_time}:00`
        : `${formData.scheduled_date}T09:00:00`

      const eventData = {
        title: formData.title,
        description: formData.description,
        event_type: formData.event_type,
        scheduled_date: dateTimeString,
        duration_minutes: formData.duration_minutes ? parseInt(formData.duration_minutes) : 60,
        horse_id: formData.horse_id ? parseInt(formData.horse_id) : null
      }

      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/calendar/events?organization_id=${selectedBarnId}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(eventData)
      })

      if (response.ok) {
        await fetchEvents()
        setShowAddForm(false)
        setFormData({
          event_type: 'veterinary',
          title: '',
          description: '',
          scheduled_date: '',
          scheduled_time: '',
          duration_minutes: '',
          horse_id: ''
        })
        setActiveTab('upcoming')
      }
    } catch (error) {
      console.error('Error adding event:', error)
    }
  }

  const handleDeleteEvent = async (eventId: number) => {
    try {
      const accessToken = localStorage.getItem('access_token')
      const headers: Record<string, string> = accessToken === 'dev_token_placeholder'
        ? {}
        : { 'Authorization': `Bearer ${accessToken}` }

      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/calendar/events/${eventId}`, {
        method: 'DELETE',
        headers
      })

      if (response.ok) {
        await fetchEvents()
        setShowEventModal(false)
        setSelectedEvent(null)
      }
    } catch (error) {
      console.error('Error deleting event:', error)
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    })
  }

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }


  const getUpcomingEvents = () => {
    const now = new Date()
    return events
      .filter(event => new Date(event.scheduled_date) >= now)
      .sort((a, b) => new Date(a.scheduled_date).getTime() - new Date(b.scheduled_date).getTime())
      .slice(0, 10)
  }

  const getCalendarDays = () => {
    const year = currentDate.getFullYear()
    const month = currentDate.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const startDate = new Date(firstDay)
    startDate.setDate(startDate.getDate() - firstDay.getDay())

    const days = []
    const current = new Date(startDate)

    for (let i = 0; i < 42; i++) {
      const dayEvents = events.filter(event => {
        const eventDate = new Date(event.scheduled_date)
        return eventDate.toDateString() === current.toDateString()
      })

      days.push({
        date: new Date(current),
        isCurrentMonth: current.getMonth() === month,
        isToday: current.toDateString() === new Date().toDateString(),
        events: dayEvents
      })

      current.setDate(current.getDate() + 1)
    }

    return days
  }

  const navigateMonth = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate)
    newDate.setMonth(newDate.getMonth() + (direction === 'next' ? 1 : -1))
    setCurrentDate(newDate)
  }

  const renderUpcomingTab = () => (
    <div className="space-y-4">
      {loading ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading events...</p>
        </div>
      ) : getUpcomingEvents().length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">📅</div>
          <p className="font-medium">No upcoming events</p>
          <p className="text-sm mt-1">Schedule veterinary visits, training sessions, and more</p>
          <button
            onClick={() => setActiveTab('add')}
            className="btn-primary mt-4"
          >
            Add Your First Event
          </button>
        </div>
      ) : (
        getUpcomingEvents().map((event) => (
          <div
            key={event.id}
            className="bg-white rounded-lg border border-gray-200 p-4 cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => {
              setSelectedEvent(event)
              setShowEventModal(true)
            }}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${EVENT_TYPES[event.event_type].color}`}>
                    {EVENT_TYPES[event.event_type].emoji} {EVENT_TYPES[event.event_type].label}
                  </span>
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">{event.title}</h3>
                {event.description && (
                  <p className="text-sm text-gray-600 mb-2">{event.description}</p>
                )}
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span>📅 {formatDate(event.scheduled_date)}</span>
                  {event.scheduled_date && <span>🕐 {formatTime(event.scheduled_date)}</span>}
                  {event.horse && <span>🐴 {event.horse.horse_name}</span>}
                </div>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  )

  const renderCalendarTab = () => (
    <div className="space-y-4">
      {/* Calendar Header */}
      <div className="flex items-center justify-between bg-white rounded-lg border border-gray-200 p-4">
        <button
          onClick={() => navigateMonth('prev')}
          className="p-2 hover:bg-gray-100 rounded-lg"
        >
          <span className="text-lg">←</span>
        </button>
        <h2 className="text-lg font-semibold">
          {currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
        </h2>
        <button
          onClick={() => navigateMonth('next')}
          className="p-2 hover:bg-gray-100 rounded-lg"
        >
          <span className="text-lg">→</span>
        </button>
      </div>

      {/* Calendar Grid */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {/* Day Headers */}
        <div className="grid grid-cols-7 bg-gray-50">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
            <div key={day} className="p-2 text-center text-sm font-medium text-gray-700">
              {day}
            </div>
          ))}
        </div>

        {/* Calendar Days */}
        <div className="grid grid-cols-7">
          {getCalendarDays().map((day, index) => (
            <div
              key={index}
              className={`min-h-[60px] p-1 border-t border-gray-200 ${
                !day.isCurrentMonth ? 'bg-gray-50' : ''
              } ${day.isToday ? 'bg-blue-50' : ''}`}
            >
              <div className={`text-sm font-medium mb-1 ${
                !day.isCurrentMonth ? 'text-gray-400' : day.isToday ? 'text-blue-600' : 'text-gray-900'
              }`}>
                {day.date.getDate()}
              </div>
              <div className="space-y-1">
                {day.events.slice(0, 2).map((event) => (
                  <div
                    key={event.id}
                    className={`text-xs px-1 py-0.5 rounded cursor-pointer ${EVENT_TYPES[event.event_type].color}`}
                    onClick={() => {
                      setSelectedEvent(event)
                      setShowEventModal(true)
                    }}
                  >
                    {EVENT_TYPES[event.event_type].emoji} {event.title.length > 8 ? event.title.substring(0, 8) + '...' : event.title}
                  </div>
                ))}
                {day.events.length > 2 && (
                  <div className="text-xs text-gray-500">
                    +{day.events.length - 2} more
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  const renderAddTab = () => (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Add New Event</h2>
      <form onSubmit={handleAddEvent} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Event Type
          </label>
          <select
            value={formData.event_type}
            onChange={(e) => setFormData({ ...formData, event_type: e.target.value as keyof typeof EVENT_TYPES })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            required
          >
            {Object.entries(EVENT_TYPES).map(([key, type]) => (
              <option key={key} value={key}>
                {type.emoji} {type.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Title
          </label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            rows={3}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Date
          </label>
          <input
            type="date"
            value={formData.scheduled_date}
            onChange={(e) => setFormData({ ...formData, scheduled_date: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Time (Optional)
          </label>
          <input
            type="time"
            value={formData.scheduled_time}
            onChange={(e) => setFormData({ ...formData, scheduled_time: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Duration (minutes)
          </label>
          <input
            type="number"
            value={formData.duration_minutes}
            onChange={(e) => setFormData({ ...formData, duration_minutes: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            min="1"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Horse (Optional)
          </label>
          <select
            value={formData.horse_id}
            onChange={(e) => setFormData({ ...formData, horse_id: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">Select a horse...</option>
            {horses.map((horse) => (
              <option key={horse.horse_id} value={horse.horse_id}>
                🐴 {horse.horse_name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex space-x-3 pt-4">
          <button
            type="submit"
            className="flex-1 btn-primary"
          >
            Add Event
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('upcoming')}
            className="flex-1 btn-secondary"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <h1 className="text-xl font-bold text-gray-900">Calendar</h1>
        <p className="text-sm text-gray-600">Schedule and track events for your horses</p>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white border-b border-gray-200">
        <div className="flex">
          <button
            onClick={() => setActiveTab('upcoming')}
            className={`flex-1 py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'upcoming'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            📅 Upcoming
          </button>
          <button
            onClick={() => setActiveTab('calendar')}
            className={`flex-1 py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'calendar'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            🗓️ Calendar
          </button>
          <button
            onClick={() => setActiveTab('add')}
            className={`flex-1 py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'add'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            ➕ Add Event
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'upcoming' && renderUpcomingTab()}
        {activeTab === 'calendar' && renderCalendarTab()}
        {activeTab === 'add' && renderAddTab()}
      </div>

      {/* Event Detail Modal */}
      {showEventModal && selectedEvent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Event Details</h3>
              <button
                onClick={() => setShowEventModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${EVENT_TYPES[selectedEvent.event_type].color}`}>
                  {EVENT_TYPES[selectedEvent.event_type].emoji} {EVENT_TYPES[selectedEvent.event_type].label}
                </span>
              </div>

              <h4 className="font-semibold text-gray-900">{selectedEvent.title}</h4>

              {selectedEvent.description && (
                <p className="text-gray-600">{selectedEvent.description}</p>
              )}

              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex items-center space-x-2">
                  <span>📅</span>
                  <span>{formatDate(selectedEvent.scheduled_date)}</span>
                </div>
                {selectedEvent.scheduled_date && (
                  <div className="flex items-center space-x-2">
                    <span>🕐</span>
                    <span>{formatTime(selectedEvent.scheduled_date)}</span>
                  </div>
                )}
                {selectedEvent.duration_minutes && (
                  <div className="flex items-center space-x-2">
                    <span>⏱️</span>
                    <span>{selectedEvent.duration_minutes} minutes</span>
                  </div>
                )}
                {selectedEvent.horse && (
                  <div className="flex items-center space-x-2">
                    <span>🐴</span>
                    <span>{selectedEvent.horse.horse_name}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => handleDeleteEvent(selectedEvent.id)}
                className="flex-1 bg-red-600 text-white py-2 rounded-lg hover:bg-red-700 transition-colors"
              >
                Delete Event
              </button>
              <button
                onClick={() => setShowEventModal(false)}
                className="flex-1 btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}