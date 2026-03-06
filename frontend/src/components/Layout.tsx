import { Outlet, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Layout() {
  const { logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{
        padding: '1rem 2rem',
        background: '#1a1a2e',
        color: '#eee',
        display: 'flex',
        alignItems: 'center',
        gap: '2rem',
      }}>
        <Link to="/dashboard" style={{ color: '#eee', textDecoration: 'none', fontWeight: 'bold' }}>
          Fitness Gen
        </Link>
        <nav style={{ display: 'flex', gap: '1rem' }}>
          <Link to="/students" style={{ color: '#aaa', textDecoration: 'none' }}>Alunos</Link>
        </nav>
        <div style={{ marginLeft: 'auto' }}>
          <button onClick={handleLogout} style={{
            padding: '0.5rem 1rem',
            background: '#333',
            color: '#eee',
            border: '1px solid #555',
            borderRadius: 4,
            cursor: 'pointer',
          }}>Sair</button>
        </div>
      </header>
      <main style={{ flex: 1, padding: '2rem' }}>
        <Outlet />
      </main>
    </div>
  )
}
