interface LoginProps {
  onLogin?: () => void
}

export default function Login({ onLogin }: LoginProps) {
  const handleLogin = () => {
    const baseState = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
    const mobileState = `mobile:${baseState}`
    localStorage.setItem('oauth_state', mobileState)

    const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
    const redirectUri = isProduction
      ? window.location.origin
      : 'http://localhost:3001'

    const explicitLogout = localStorage.getItem('explicit_logout')
    localStorage.removeItem('explicit_logout')

    const params = new URLSearchParams({
      'client_id': '7808486258d0ff494a29d2dfe48b6da3',
      'redirect_uri': redirectUri,
      'response_type': 'code',
      'scope': 'openid email profile',
      'state': mobileState,
      ...(explicitLogout ? { 'prompt': 'login' } : {})
    })

    const loginUrl = `${import.meta.env.VITE_AUTH_URL}/propelauth/oauth/authorize?${params.toString()}`
    window.location.href = loginUrl
  }

  return (
    <div style={{ background: '#080808', minHeight: '100vh', color: '#fff', fontFamily: 'system-ui, sans-serif' }}>

      {/* ── Hero ── */}
      <section style={{ position: 'relative', minHeight: '100vh', display: 'flex', alignItems: 'center', overflow: 'hidden' }}>

        {/* Grid overlay */}
        <div style={{
          position: 'absolute', inset: 0, pointerEvents: 'none',
          backgroundImage: 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }} />

        {/* Amber ambient glow */}
        <div style={{
          position: 'absolute', inset: 0, pointerEvents: 'none',
          background: 'radial-gradient(ellipse 70% 60% at 20% 50%, rgba(217,119,6,0.12) 0%, transparent 65%)',
        }} />

        {/* Right-side fade mask over horse image */}
        <div style={{
          position: 'absolute', right: 0, top: 0, bottom: 0, width: '55%', pointerEvents: 'none',
          background: 'linear-gradient(to right, #080808 0%, transparent 40%, rgba(0,0,0,0.3) 100%)',
          zIndex: 1,
        }} />

        {/* Hero horse image */}
        <div style={{
          position: 'absolute', right: 0, top: 0, bottom: 0, width: '55%',
          overflow: 'hidden',
        }}>
          <img
            src="/hero-horse.jpg"
            alt=""
            style={{
              width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'center',
              opacity: 0.35,
              filter: 'grayscale(30%) brightness(0.7)',
            }}
          />
        </div>

        {/* Hero copy — left aligned */}
        <div style={{ position: 'relative', zIndex: 2, padding: '0 6% 0 6%', maxWidth: 600 }}>

          {/* Eyebrow */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 24 }}>
            <span style={{
              width: 8, height: 8, borderRadius: '50%', background: '#D97706',
              display: 'inline-block',
              animation: 'pulse-dot 2s ease-in-out infinite',
            }} />
            <span style={{ fontSize: 12, fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase', color: '#D97706' }}>
              AI-Powered Barn Management
            </span>
          </div>

          {/* Main headline */}
          <h1 style={{ margin: 0, lineHeight: 0.9, letterSpacing: '-0.02em' }}>
            <span style={{
              display: 'block',
              fontSize: 'clamp(4rem, 12vw, 8rem)',
              fontWeight: 900,
              color: '#fff',
            }}>
              STABLE
            </span>
            <span style={{
              display: 'block',
              fontSize: 'clamp(4rem, 12vw, 8rem)',
              fontWeight: 900,
              color: '#fff',
            }}>
              GENIUS
            </span>
          </h1>

          <p style={{ marginTop: 28, fontSize: 'clamp(1rem, 2vw, 1.2rem)', color: 'rgba(255,255,255,0.6)', maxWidth: 440, lineHeight: 1.6 }}>
            Everything your barn needs — horse health records, AI tools, receipt scanning, and a message board — in one smart platform.
          </p>

          <div style={{ display: 'flex', gap: 12, marginTop: 40, flexWrap: 'wrap' }}>
            <button
              onClick={handleLogin}
              style={{
                background: '#D97706', color: '#fff', border: 'none', borderRadius: 6,
                padding: '14px 32px', fontSize: 15, fontWeight: 700, cursor: 'pointer',
                letterSpacing: '0.05em', textTransform: 'uppercase',
                transition: 'opacity 0.2s',
              }}
              onMouseOver={e => (e.currentTarget.style.opacity = '0.85')}
              onMouseOut={e => (e.currentTarget.style.opacity = '1')}
            >
              Log In
            </button>
            <a
              href="https://calendly.com/chris-carril/30min"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                background: 'transparent', color: '#fff',
                border: '1px solid rgba(255,255,255,0.2)', borderRadius: 6,
                padding: '14px 32px', fontSize: 15, fontWeight: 700, cursor: 'pointer',
                letterSpacing: '0.05em', textTransform: 'uppercase',
                textDecoration: 'none', display: 'inline-flex', alignItems: 'center',
                transition: 'border-color 0.2s',
              }}
              onMouseOver={e => (e.currentTarget.style.borderColor = '#D97706')}
              onMouseOut={e => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.2)')}
            >
              Book a Demo
            </a>
          </div>
        </div>
      </section>

      {/* ── Features strip ── */}
      <section style={{ borderTop: '1px solid rgba(255,255,255,0.06)', padding: '80px 6%' }}>
        <p style={{ textAlign: 'center', fontSize: 12, fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase', color: '#D97706', marginBottom: 48 }}>
          Everything in one place
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 20, maxWidth: 1100, margin: '0 auto' }}>
          {[
            { icon: '🐴', title: 'Horse Profiles', desc: 'Health records, vet history, photos, and documents for every horse.' },
            { icon: '🤖', title: 'AI Assistant', desc: 'Ask questions about your herd. Get instant, context-aware answers.' },
            { icon: '🧾', title: 'Receipt Scanner', desc: 'Snap a receipt and watch it auto-populate your inventory.' },
            { icon: '📦', title: 'Inventory', desc: 'Track supplies, set low-stock alerts, and manage ordering.' },
            { icon: '📅', title: 'Calendar', desc: 'Vet visits, farrier schedules, and barn events in one view.' },
            { icon: '💬', title: 'Message Board', desc: 'Keep the whole team on the same page, shift to shift.' },
          ].map(f => (
            <div
              key={f.title}
              style={{
                background: '#111', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 12,
                padding: '28px 24px', transition: 'border-color 0.2s, background 0.2s',
              }}
              onMouseOver={e => {
                (e.currentTarget as HTMLDivElement).style.background = '#161616'
                ;(e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(217,119,6,0.35)'
              }}
              onMouseOut={e => {
                (e.currentTarget as HTMLDivElement).style.background = '#111'
                ;(e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(255,255,255,0.06)'
              }}
            >
              <span style={{ fontSize: 28 }}>{f.icon}</span>
              <h3 style={{ margin: '12px 0 8px', fontSize: 16, fontWeight: 700, color: '#fff' }}>{f.title}</h3>
              <p style={{ margin: 0, fontSize: 14, color: 'rgba(255,255,255,0.5)', lineHeight: 1.6 }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Pricing ── */}
      <section style={{ borderTop: '1px solid rgba(255,255,255,0.06)', padding: '80px 6%' }}>
        <p style={{ textAlign: 'center', fontSize: 12, fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase', color: '#D97706', marginBottom: 16 }}>
          Pricing
        </p>
        <h2 style={{ textAlign: 'center', fontSize: 'clamp(2rem, 5vw, 3rem)', fontWeight: 900, margin: '0 0 56px', letterSpacing: '-0.02em' }}>
          Simple, transparent plans
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 24, maxWidth: 800, margin: '0 auto' }}>

          {/* Basic */}
          <div style={{
            background: '#111', border: '1px solid rgba(217,119,6,0.4)', borderRadius: 12,
            padding: '36px 32px', display: 'flex', flexDirection: 'column',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
              <h3 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Basic</h3>
              <span style={{
                background: 'rgba(217,119,6,0.15)', color: '#D97706', borderRadius: 20,
                padding: '4px 12px', fontSize: 11, fontWeight: 700, letterSpacing: '0.05em',
              }}>
                INTRO OFFER
              </span>
            </div>
            <div style={{ marginBottom: 28 }}>
              <span style={{ fontSize: 52, fontWeight: 900, letterSpacing: '-0.03em' }}>$40</span>
              <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: 15 }}> / month</span>
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 32px', display: 'flex', flexDirection: 'column', gap: 10, flex: 1 }}>
              {[
                'AI Receipt Scanner', 'Horse Health Tracking', 'Inventory Management',
                'AI Assistant', 'Calendar & Scheduling', 'Message Board',
                'Up to 20 horses', 'Up to 5 users (+$10/additional)',
              ].map(item => (
                <li key={item} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 14, color: 'rgba(255,255,255,0.65)' }}>
                  <span style={{ color: '#D97706', fontWeight: 700 }}>✓</span>
                  {item}
                </li>
              ))}
            </ul>
            <a
              href="https://calendly.com/chris-carril/30min"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'block', textAlign: 'center', background: '#D97706', color: '#fff',
                borderRadius: 6, padding: '14px', fontWeight: 700, fontSize: 14,
                letterSpacing: '0.05em', textTransform: 'uppercase', textDecoration: 'none',
                transition: 'opacity 0.2s',
              }}
              onMouseOver={e => (e.currentTarget.style.opacity = '0.85')}
              onMouseOut={e => (e.currentTarget.style.opacity = '1')}
            >
              Book a Demo
            </a>
          </div>

          {/* Enterprise */}
          <div style={{
            background: '#111', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12,
            padding: '36px 32px', display: 'flex', flexDirection: 'column',
          }}>
            <h3 style={{ margin: '0 0 8px', fontSize: 20, fontWeight: 700 }}>Enterprise</h3>
            <div style={{ marginBottom: 28 }}>
              <span style={{ fontSize: 36, fontWeight: 900 }}>Contact Us</span>
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 32px', display: 'flex', flexDirection: 'column', gap: 10, flex: 1 }}>
              {[
                'Everything in Basic', 'Unlimited horses', 'Priority support',
                'Custom integrations', 'Multi-barn management', 'Dedicated account manager',
              ].map(item => (
                <li key={item} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 14, color: 'rgba(255,255,255,0.65)' }}>
                  <span style={{ color: '#D97706', fontWeight: 700 }}>✓</span>
                  {item}
                </li>
              ))}
            </ul>
            <a
              href="https://calendly.com/chris-carril/30min"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'block', textAlign: 'center', background: 'transparent', color: '#fff',
                border: '1px solid rgba(255,255,255,0.2)', borderRadius: 6, padding: '14px',
                fontWeight: 700, fontSize: 14, letterSpacing: '0.05em', textTransform: 'uppercase',
                textDecoration: 'none', transition: 'border-color 0.2s',
              }}
              onMouseOver={e => (e.currentTarget.style.borderColor = '#D97706')}
              onMouseOut={e => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.2)')}
            >
              Book a Demo
            </a>
          </div>

        </div>
      </section>

      {/* ── Tagline ── */}
      <section style={{ borderTop: '1px solid rgba(255,255,255,0.06)', padding: '80px 6%', textAlign: 'center' }}>
        <p style={{
          fontSize: 'clamp(1.4rem, 4vw, 2.4rem)', fontStyle: 'italic', fontWeight: 500,
          color: 'rgba(255,255,255,0.7)', maxWidth: 700, margin: '0 auto', lineHeight: 1.4,
        }}>
          "The only thing better than a great Barn Manager<br />is a{' '}
          <span style={{ color: '#D97706', fontStyle: 'normal', fontWeight: 900 }}>Stable Genius</span>."
        </p>
      </section>

      {/* ── Footer ── */}
      <footer style={{
        borderTop: '1px solid rgba(255,255,255,0.06)', padding: '24px 6%',
        textAlign: 'center', fontSize: 13, color: 'rgba(255,255,255,0.3)',
      }}>
        <p style={{ margin: 0 }}>&copy; {new Date().getFullYear()} Stable Genius. All rights reserved.</p>
      </footer>

      {/* Pulse animation for eyebrow dot */}
      <style>{`
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.4); }
        }
      `}</style>

    </div>
  )
}
