import { ReactNode } from 'react'
import { useLocation } from 'react-router-dom'

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

interface LayoutProps {
  children: ReactNode
  user: User
  onLogout: () => void
  selectedBarnId: string | null
  onBarnChange: (barnId: string) => void
}

export default function Layout({ children, user, onLogout, selectedBarnId, onBarnChange }: LayoutProps) {
  const location = useLocation()

  const handleLogout = () => {
    onLogout()
  }

  const isActive = (path: string) => {
    return location.pathname === path ||
           (path === '/horses' && location.pathname.startsWith('/horses')) ||
           (path === '/calendar' && location.pathname.startsWith('/calendar')) ||
           (path === '/supplies' && location.pathname.startsWith('/supplies')) ||
           (path === '/menu' && (location.pathname.startsWith('/menu') ||
            location.pathname.startsWith('/messages') ||
            location.pathname.startsWith('/ai') ||
            location.pathname.startsWith('/reports') ||
            location.pathname.startsWith('/add-horse')))
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 to-blue-700 shadow-sm safe-area-top">
        <div className="px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="flex items-center bg-white bg-opacity-20 rounded-lg px-4 py-3">
                <div className="flex flex-col">
                  <span className="text-white font-black text-xl leading-tight tracking-tight">STABLE</span>
                  <span className="text-blue-100 font-bold text-lg leading-tight tracking-wide">GENIUS</span>
                </div>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="text-sm text-blue-100 hover:text-white font-medium bg-white bg-opacity-20 px-3 py-2 rounded-lg transition-colors"
            >
              Sign Out
            </button>
          </div>

          {/* Barn Selector */}
          {user.organizations && user.organizations.length > 1 && (
            <div className="mt-3">
              <select
                value={selectedBarnId || ''}
                onChange={(e) => onBarnChange(e.target.value)}
                className="w-full px-3 py-2 border border-white border-opacity-30 rounded-lg text-sm bg-white bg-opacity-90 text-gray-900 focus:outline-none focus:ring-2 focus:ring-white focus:border-white"
              >
                {user.organizations.map((org) => (
                  <option key={org.barn_id} value={org.barn_id}>
                    🏇 {org.barn_name} ({org.user_role})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Single Barn Display */}
          {user.organizations && user.organizations.length === 1 && (
            <div className="mt-3">
              <div className="px-3 py-2 bg-white bg-opacity-20 border border-white border-opacity-30 rounded-lg">
                <span className="text-sm text-white font-medium">
                  🏇 {user.organizations[0].barn_name} ({user.organizations[0].user_role})
                </span>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 px-4 py-6">
        {children}
      </main>

      {/* Bottom Navigation */}
      <nav className="bg-white border-t border-gray-200 safe-area-bottom">
        <div className="grid grid-cols-5 gap-1 px-2 py-2">
          <a
            href="/"
            className={`flex flex-col items-center py-2 px-3 rounded-lg transition-colors ${
              isActive('/')
                ? 'bg-primary-50 text-primary-600'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            <svg className="w-6 h-6 mb-1" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
            </svg>
            <span className="text-xs font-medium">Home</span>
          </a>

          <a
            href="/horses"
            className={`flex flex-col items-center py-2 px-1 rounded-lg transition-colors ${
              isActive('/horses')
                ? 'bg-primary-50 text-primary-600'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            <svg className="w-5 h-5 mb-1" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 3a2 2 0 100 4h12a2 2 0 100-4H4zM4 9a2 2 0 100 4h12a2 2 0 100-4H4zM4 15a2 2 0 100 4h12a2 2 0 100-4H4z"/>
            </svg>
            <span className="text-xs font-medium">Horses</span>
          </a>

          <a
            href="/calendar"
            className={`flex flex-col items-center py-2 px-1 rounded-lg transition-colors ${
              isActive('/calendar')
                ? 'bg-primary-50 text-primary-600'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            <svg className="w-5 h-5 mb-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
            </svg>
            <span className="text-xs font-medium">Calendar</span>
          </a>

          <a
            href="/supplies"
            className={`flex flex-col items-center py-2 px-1 rounded-lg transition-colors ${
              isActive('/supplies')
                ? 'bg-primary-50 text-primary-600'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            <svg className="w-5 h-5 mb-1" fill="currentColor" viewBox="0 0 20 20">
              <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
            </svg>
            <span className="text-xs font-medium">Supplies</span>
          </a>

          <a
            href="/menu"
            className={`flex flex-col items-center py-2 px-1 rounded-lg transition-colors ${
              isActive('/menu')
                ? 'bg-primary-50 text-primary-600'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            <svg className="w-5 h-5 mb-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
            </svg>
            <span className="text-xs font-medium">More</span>
          </a>
        </div>
      </nav>
    </div>
  )
}