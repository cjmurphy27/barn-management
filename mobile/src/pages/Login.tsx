interface LoginProps {
  onLogin?: () => void
}

export default function Login({ onLogin }: LoginProps) {
  const handleLogin = () => {
    // Generate state parameter for security with mobile flag
    const baseState = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
    const mobileState = `mobile:${baseState}` // Prefix with mobile flag
    localStorage.setItem('oauth_state', mobileState)

    // Use environment-aware redirect URI
    const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
    const redirectUri = isProduction
      ? window.location.origin  // Use current Railway URL
      : 'http://localhost:3001' // Local development

    const params = new URLSearchParams({
      'client_id': '4a68fdae569be0db02111668f191c188', // Same as desktop version
      'redirect_uri': redirectUri,
      'response_type': 'code',
      'scope': 'openid email profile',
      'state': mobileState // Mobile flag encoded in state
    })

    // Debug environment variables
    console.log('Environment variables check:')
    console.log('VITE_AUTH_URL:', import.meta.env.VITE_AUTH_URL)
    console.log('VITE_API_URL:', import.meta.env.VITE_API_URL)
    console.log('VITE_REDIRECT_URI:', import.meta.env.VITE_REDIRECT_URI)
    console.log('isProduction:', isProduction)
    console.log('redirectUri:', redirectUri)

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
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
        <div className="inline-flex items-center bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl px-8 py-6 md:px-10 md:py-8 mb-4">
          <div className="flex flex-col">
            <span className="text-white font-black text-3xl md:text-4xl leading-tight tracking-tight">STABLE</span>
            <span className="text-blue-100 font-bold text-2xl leading-tight tracking-wide">GENIUS</span>
          </div>
        </div>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mt-4">
          Smart Barn Management
        </h1>
        <p className="text-gray-600 mt-3 max-w-md text-lg">
          AI-powered tools to manage your horses, track health records, scan receipts, and keep your barn running smoothly.
        </p>
        <button
          onClick={handleLogin}
          className="btn-primary mt-8 px-10"
        >
          Log In
        </button>
      </div>

      {/* Pricing Section */}
      <div className="px-6 pb-16 max-w-3xl mx-auto">
        <h2 className="text-xl md:text-2xl font-bold text-gray-900 text-center mb-8">
          Simple Pricing
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Basic Plan */}
          <div className="card flex flex-col">
            <h3 className="text-lg font-bold text-gray-900">Basic</h3>
            <div className="mt-2 mb-4">
              <span className="text-3xl font-bold text-gray-900">$40</span>
              <span className="text-gray-600">/month</span>
            </div>
            <ul className="text-gray-600 space-y-2 mb-6 flex-1">
              <li>AI Receipt Scanner</li>
              <li>Horse Health Tracking</li>
              <li>Inventory Management</li>
              <li>AI Assistant</li>
              <li>Calendar & Scheduling</li>
              <li>Message Board</li>
              <li>Up to 20 horses</li>
              <li>Up to 5 users (+$10/each additional)</li>
            </ul>
            <a
              href="mailto:support@stablegenius.us"
              className="btn-primary w-full"
            >
              Get Started
            </a>
          </div>

          {/* Enterprise Plan */}
          <div className="card flex flex-col">
            <h3 className="text-lg font-bold text-gray-900">Enterprise</h3>
            <div className="mt-2 mb-4">
              <span className="text-3xl font-bold text-gray-900">Contact Us</span>
            </div>
            <ul className="text-gray-600 space-y-2 mb-6 flex-1">
              <li>Everything in Basic</li>
              <li>Unlimited horses</li>
              <li>Priority support</li>
              <li>Custom integrations</li>
              <li>Multi-barn management</li>
              <li>Dedicated account manager</li>
            </ul>
            <a
              href="mailto:support@stablegenius.us"
              className="btn-primary w-full"
            >
              Contact Us
            </a>
          </div>
        </div>
      </div>

      {/* Tagline */}
      <div className="px-6 pb-16 text-center">
        <h2 className="text-2xl md:text-3xl font-bold text-gray-900">
          The only thing better than a great Barn Manager is a Stable Genius!
        </h2>
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-6 px-6 text-center text-sm text-gray-500">
        <p>&copy; {new Date().getFullYear()} Stable Genius. All rights reserved.</p>
        <p className="mt-1">Powered by PropelAuth</p>
        {/* Development mode bypass */}
        <button
          onClick={handleDevModeLogin}
          className="mt-4 px-4 py-2 border border-gray-300 rounded-md text-xs font-medium text-gray-400 bg-white hover:bg-gray-50 transition-colors"
        >
          Dev Mode
        </button>
      </footer>
    </div>
  )
}