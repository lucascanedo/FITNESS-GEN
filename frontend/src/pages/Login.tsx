import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    login(email, password)
    navigate('/dashboard')
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
    }}>
      <form onSubmit={handleSubmit} style={{
        padding: '2rem',
        background: '#0f0f23',
        borderRadius: 8,
        boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
        width: 320,
      }}>
        <h1 style={{ color: '#eee', marginBottom: '1.5rem', textAlign: 'center' }}>Fitness Gen</h1>
        <p style={{ color: '#888', marginBottom: '1.5rem', fontSize: 14, textAlign: 'center' }}>
          Login do treinador (demo: qualquer email)
        </p>
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', color: '#aaa', marginBottom: 4, fontSize: 14 }}>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{
              width: '100%',
              padding: '0.75rem',
              background: '#1a1a2e',
              border: '1px solid #333',
              borderRadius: 4,
              color: '#eee',
            }}
          />
        </div>
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', color: '#aaa', marginBottom: 4, fontSize: 14 }}>Senha</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{
              width: '100%',
              padding: '0.75rem',
              background: '#1a1a2e',
              border: '1px solid #333',
              borderRadius: 4,
              color: '#eee',
            }}
          />
        </div>
        <button type="submit" style={{
          width: '100%',
          padding: '0.75rem',
          background: '#e94560',
          color: '#fff',
          border: 'none',
          borderRadius: 4,
          cursor: 'pointer',
          fontWeight: 'bold',
        }}>Entrar</button>
      </form>
    </div>
  )
}
