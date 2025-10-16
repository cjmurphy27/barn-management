interface LoginProps {
  onLogin?: () => void
}

export default function Login({ onLogin }: LoginProps) {
  const handleLogin = () => {
    // Generate state parameter for security with mobile flag
    const baseState = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
    const mobileState = `mobile:${baseState}` // Prefix with mobile flag
    localStorage.setItem('oauth_state', mobileState)

    // Use exact desktop redirect URI (without mobile parameter)
    const params = new URLSearchParams({
      'client_id': '4a68fdae569be0db02111668f191c188', // Same as desktop version
      'redirect_uri': 'http://localhost:3001', // Mobile app port
      'response_type': 'code',
      'scope': 'openid email profile',
      'state': mobileState // Mobile flag encoded in state
    })

    const loginUrl = `${import.meta.env.VITE_AUTH_URL}/propelauth/oauth/authorize?${params.toString()}`

    console.log('Redirecting to PropelAuth OAuth (matching desktop):', loginUrl)

    // Redirect to PropelAuth OAuth
    window.location.href = loginUrl
  }

  const handleDevModeLogin = () => {
    console.log('Development mode login - using test token')

    // For development, create a test token and trigger login callback
    localStorage.setItem('access_token', 'dev_token_placeholder')

    if (onLogin) {
      onLogin()
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <div className="inline-flex items-center bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl px-8 py-6 mb-4">
            <div className="flex flex-col">
              <span className="text-white font-black text-3xl leading-tight tracking-tight">STABLE</span>
              <span className="text-blue-100 font-bold text-2xl leading-tight tracking-wide">GENIUS</span>
            </div>
          </div>
          <p className="text-gray-600">
            Smart Barn Management
          </p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-6">
        <div className="bg-white py-8 px-6 shadow rounded-lg sm:px-10">
          <div className="text-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">
              Sign in to your account
            </h2>

            <button
              onClick={handleLogin}
              className="btn-primary w-full"
            >
              Sign In with PropelAuth
            </button>

            {/* Development mode bypass */}
            <button
              onClick={handleDevModeLogin}
              className="mt-4 w-full px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
            >
              🚧 Development Mode (Skip Auth)
            </button>

            <p className="mt-6 text-sm text-gray-500">
              Secure authentication powered by PropelAuth
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}