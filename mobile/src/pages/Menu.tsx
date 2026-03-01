import { Link } from 'react-router-dom'

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

interface MenuProps {
  user: User
  onLogout: () => void
}

export default function Menu({ user, onLogout }: MenuProps) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
          More Options
        </h1>
        <p className="text-gray-600">
          Additional features and settings
        </p>
      </div>

      <div className="space-y-6 md:grid md:grid-cols-2 md:gap-6 md:space-y-0">
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          🐎 Horse Management
        </h2>
        <div className="space-y-3">
          <Link to="/add-horse" className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
            <div className="flex items-center">
              <span className="text-2xl mr-3">➕</span>
              <span className="font-medium">Add New Horse</span>
            </div>
            <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
          </Link>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          💬 Communication
        </h2>
        <div className="space-y-3">
          <Link to="/messages" className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
            <div className="flex items-center">
              <span className="text-2xl mr-3">💬</span>
              <span className="font-medium">Message Board</span>
            </div>
            <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
          </Link>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          🤖 AI & Reports
        </h2>
        <div className="space-y-3">
          <Link to="/ai" className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
            <div className="flex items-center">
              <span className="text-2xl mr-3">🤖</span>
              <span className="font-medium">AI Assistant</span>
            </div>
            <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
          </Link>

          <Link to="/reports" className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
            <div className="flex items-center">
              <span className="text-2xl mr-3">📊</span>
              <span className="font-medium">Reports</span>
            </div>
            <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
          </Link>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          ⚙️ Account
        </h2>
        <div className="space-y-3">
          <button
            onClick={() => window.open(`${import.meta.env.VITE_AUTH_URL}/account`, '_blank')}
            className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors w-full text-left"
          >
            <div className="flex items-center">
              <span className="text-2xl mr-3">👤</span>
              <span className="font-medium">Profile Settings</span>
            </div>
            <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
          </button>

          <button
            onClick={onLogout}
            className="flex items-center justify-between p-3 rounded-lg bg-red-50 hover:bg-red-100 transition-colors w-full text-left text-red-600"
          >
            <div className="flex items-center">
              <span className="text-2xl mr-3">🚪</span>
              <span className="font-medium">Sign Out</span>
            </div>
            <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
      </div>
    </div>
  )
}