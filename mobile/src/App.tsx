import { useState, useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import HorsesList from './pages/HorsesList'
import HorseProfile from './pages/HorseProfile'
import AddHorse from './pages/AddHorse'
import Calendar from './pages/Calendar'
import Supplies from './pages/Supplies'
import Menu from './pages/Menu'
import Login from './pages/Login'
import AskAI from './pages/AskAI'
import HorseAI from './pages/HorseAI'
import Messages from './pages/Messages'

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

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedBarnId, setSelectedBarnId] = useState<string | null>(null)

  useEffect(() => {
    checkAuthentication()
  }, [])

  const checkAuthentication = async () => {
    try {
      // Check if we have an OAuth code in the URL (returning from PropelAuth)
      const urlParams = new URLSearchParams(window.location.search)
      const code = urlParams.get('code')

      if (code) {
        console.log('OAuth code detected, exchanging for token...')
        await handleOAuthCallback(code)
        return
      }

      // Check if we have a stored access token
      const accessToken = localStorage.getItem('access_token')
      if (accessToken) {
        console.log('Stored token found, validating...')
        await validateStoredToken(accessToken)
        return
      }

      // No authentication found
      setLoading(false)
    } catch (error) {
      console.error('Authentication check failed:', error)
      setError('Authentication failed')
      setLoading(false)
    }
  }

  const handleOAuthCallback = async (code: string) => {
    try {
      // Use environment-aware redirect URI (must match Login component)
      const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
      const redirectUri = isProduction
        ? window.location.origin  // Use current Railway URL
        : 'http://localhost:3001' // Local development

      // First, try to exchange code with backend (normal flow)
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/auth/exchange-code`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code,
          redirect_uri: redirectUri // Must match the redirect_uri used in Login
        })
      })

      // Check if the response indicates the endpoint doesn't exist
      if (response.status === 404) {
        throw new Error('Endpoint not found (404)')
      }

      const result = await response.json()

      if (result.success) {
        // Store access token
        localStorage.setItem('access_token', result.access_token)

        // Handle data structure transformation: barns -> organizations
        const userData = result.user
        if (userData.barns && !userData.organizations) {
          userData.organizations = userData.barns
          delete userData.barns
        }

        setUser(userData)
        // Set default barn (first organization)
        if (userData.organizations && userData.organizations.length > 0) {
          setSelectedBarnId(userData.organizations[0].barn_id)
        }
        // Cache user data for persistence across navigation
        localStorage.setItem('user_data', JSON.stringify(userData))

        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname)

        console.log('Authentication successful:', userData)
      } else {
        throw new Error(result.error || 'Token exchange failed')
      }
    } catch (error) {
      console.error('OAuth callback failed:', error)

      // Only fall back to development mode if backend is completely unavailable
      // (network error, 404, etc.) and we're on localhost
      const errorMessage = error instanceof Error ? error.message : String(error)
      const isNetworkError = error instanceof TypeError && errorMessage.includes('fetch')
      const isNotFound = errorMessage.includes('404') || errorMessage.includes('Not Found')
      const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'

      if ((isNetworkError || isNotFound) && isLocalhost) {
        console.log('Backend unavailable - falling back to development mode')

        // Use development mode authentication as fallback
        const userData = {
          user_id: "dev-user-123",
          email: "dev@example.com",
          organizations: [
            {
              barn_id: "dev-barn-123",
              barn_name: "Development Barn",
              user_role: "Owner",
              permissions: ["all"]
            }
          ]
        }

        // Store development token
        localStorage.setItem('access_token', 'dev_token_placeholder')
        setUser(userData)
        setSelectedBarnId(userData.organizations[0].barn_id)
        localStorage.setItem('user_data', JSON.stringify(userData))

        // Set the development token in API client
        const { apiClient } = await import('./services/api')
        apiClient.setToken('dev_token_placeholder')

        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname)

        console.log('Development mode authentication successful:', userData)
        setLoading(false)
        return
      }

      setError('Login failed')
    } finally {
      setLoading(false)
    }
  }

  const validateStoredToken = async (accessToken: string) => {
    try {
      // Check if we already have user data in localStorage to avoid unnecessary API calls
      const storedUserData = localStorage.getItem('user_data')

      if (storedUserData) {
        try {
          const userData = JSON.parse(storedUserData)
          if (userData.organizations && userData.organizations.length > 0) {
            setUser(userData)
            // Set default barn (first organization)
            if (userData.organizations && userData.organizations.length > 0) {
              setSelectedBarnId(userData.organizations[0].barn_id)
            }

            // Set the development token in API client for cached dev users
            if (accessToken === 'dev_token_placeholder') {
              const { apiClient } = await import('./services/api')
              apiClient.setToken('dev_token_placeholder')
            }

            console.log('Using cached user data:', userData)
            setLoading(false)
            return
          }
        } catch (e) {
          console.error('Failed to parse cached user data:', e)
          // Invalid cached data, fetch fresh
          localStorage.removeItem('user_data')
        }
      }

      // Handle development mode directly without backend call
      if (accessToken === 'dev_token_placeholder') {
        const userData = {
          user_id: "dev-user-123",
          email: "dev@example.com",
          organizations: [
            {
              barn_id: "dev-barn-123",
              barn_name: "Development Barn",
              user_role: "Owner",
              permissions: ["all"]
            }
          ]
        }

        setUser(userData)
        setSelectedBarnId(userData.organizations[0].barn_id)
        localStorage.setItem('user_data', JSON.stringify(userData))

        // Set the development token in API client
        const { apiClient } = await import('./services/api')
        apiClient.setToken('dev_token_placeholder')

        console.log('Development mode authentication successful:', userData)
        setLoading(false)
        return
      }

      // Use regular endpoint for real authentication
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/auth/user`, {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      })

      if (response.ok) {
        const userData = await response.json()

        // Handle data structure transformation: barns -> organizations
        if (userData.barns && !userData.organizations) {
          userData.organizations = userData.barns
          delete userData.barns
        }

        setUser(userData)
        // Set default barn (first organization)
        if (userData.organizations && userData.organizations.length > 0) {
          setSelectedBarnId(userData.organizations[0].barn_id)
        }
        // Cache user data for persistence across navigation
        localStorage.setItem('user_data', JSON.stringify(userData))
        console.log('Token validation successful:', userData)
      } else {
        // Token is invalid, remove it
        localStorage.removeItem('access_token')
        localStorage.removeItem('user_data')
        console.log('Stored token is invalid')
      }
    } catch (error) {
      console.error('Token validation failed:', error)
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_data')
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_data')
    setUser(null)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-red-600 mb-4">
            <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Authentication Error</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => {
              setError(null)
              setLoading(true)
              checkAuthentication()
            }}
            className="btn-primary"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  if (!user) {
    return <Login onLogin={checkAuthentication} />
  }

  return (
    <Layout
      user={user}
      onLogout={logout}
      selectedBarnId={selectedBarnId}
      onBarnChange={setSelectedBarnId}
    >
      <Routes>
        <Route path="/" element={<Dashboard user={user} selectedBarnId={selectedBarnId} />} />
        <Route path="/horses" element={<HorsesList user={user} selectedBarnId={selectedBarnId} />} />
        <Route path="/horses/new" element={<AddHorse user={user} selectedBarnId={selectedBarnId} />} />
        <Route path="/horses/:id" element={<HorseProfile user={user} selectedBarnId={selectedBarnId} />} />
        <Route path="/horses/:id/ai" element={<HorseAI user={user} selectedBarnId={selectedBarnId} />} />
        <Route path="/calendar" element={<Calendar user={user} selectedBarnId={selectedBarnId} />} />
        <Route path="/supplies" element={<Supplies user={user} selectedBarnId={selectedBarnId} />} />
        <Route path="/menu" element={<Menu user={user} onLogout={logout} />} />
        <Route path="/add-horse" element={<div className="text-center py-12">Add New Horse (Coming Soon)</div>} />
        <Route path="/messages" element={<Messages user={user} selectedBarnId={selectedBarnId} />} />
        <Route path="/messages/:postId" element={<Messages user={user} selectedBarnId={selectedBarnId} />} />
        <Route path="/ai" element={<AskAI user={user} selectedBarnId={selectedBarnId} />} />
        <Route path="/reports" element={<div className="text-center py-12">Reports (Coming Soon)</div>} />
        <Route path="*" element={<Dashboard user={user} selectedBarnId={selectedBarnId} />} />
      </Routes>
    </Layout>
  )
}

export default App