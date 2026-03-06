import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

export function StudentNew() {
  const [name, setName] = useState('')
  const [cpf, setCpf] = useState('')
  const [birthDate, setBirthDate] = useState('')
  const [sex, setSex] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    api.students.create({ name, cpf, birth_date: birthDate, sex: sex || undefined, email: email || undefined, phone: phone || undefined })
      .then((s) => navigate(`/students/${s.id}`))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem', color: '#eee' }}>Novo aluno</h1>
      {error && <p style={{ color: '#e94560', marginBottom: '1rem' }}>{error}</p>}
      <form onSubmit={handleSubmit} style={{ maxWidth: 480 }}>
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', color: '#aaa', marginBottom: 4 }}>Nome *</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required
            style={{ width: '100%', padding: '0.75rem', background: '#1a1a2e', border: '1px solid #333', borderRadius: 4, color: '#eee' }} />
        </div>
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', color: '#aaa', marginBottom: 4 }}>CPF *</label>
          <input value={cpf} onChange={(e) => setCpf(e.target.value)} required
            placeholder="000.000.000-00"
            style={{ width: '100%', padding: '0.75rem', background: '#1a1a2e', border: '1px solid #333', borderRadius: 4, color: '#eee' }} />
        </div>
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', color: '#aaa', marginBottom: 4 }}>Data de nascimento *</label>
          <input type="date" value={birthDate} onChange={(e) => setBirthDate(e.target.value)} required
            style={{ width: '100%', padding: '0.75rem', background: '#1a1a2e', border: '1px solid #333', borderRadius: 4, color: '#eee' }} />
        </div>
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', color: '#aaa', marginBottom: 4 }}>Sexo</label>
          <select value={sex} onChange={(e) => setSex(e.target.value)}
            style={{ width: '100%', padding: '0.75rem', background: '#1a1a2e', border: '1px solid #333', borderRadius: 4, color: '#eee' }}>
            <option value="">Selecione</option>
            <option value="M">Masculino</option>
            <option value="F">Feminino</option>
          </select>
        </div>
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', color: '#aaa', marginBottom: 4 }}>Email</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
            style={{ width: '100%', padding: '0.75rem', background: '#1a1a2e', border: '1px solid #333', borderRadius: 4, color: '#eee' }} />
        </div>
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', color: '#aaa', marginBottom: 4 }}>Telefone</label>
          <input value={phone} onChange={(e) => setPhone(e.target.value)}
            style={{ width: '100%', padding: '0.75rem', background: '#1a1a2e', border: '1px solid #333', borderRadius: 4, color: '#eee' }} />
        </div>
        <button type="submit" disabled={loading}
          style={{ padding: '0.75rem 1.5rem', background: '#e94560', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>
          {loading ? 'Salvando...' : 'Salvar'}
        </button>
      </form>
    </div>
  )
}
