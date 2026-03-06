import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { Student } from '../types'

export function StudentsList() {
  const [students, setStudents] = useState<Student[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.students.list()
      .then(setStudents)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p style={{ color: '#888' }}>Carregando...</p>
  if (error) return <p style={{ color: '#e94560' }}>Erro: {error}</p>

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ color: '#eee' }}>Alunos</h1>
        <Link to="/students/new" style={{
          padding: '0.5rem 1rem',
          background: '#e94560',
          color: '#fff',
          textDecoration: 'none',
          borderRadius: 4,
        }}>Novo aluno</Link>
      </div>
      <div style={{
        background: '#1a1a2e',
        borderRadius: 8,
        overflow: 'hidden',
        border: '1px solid #333',
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#0f0f23' }}>
              <th style={{ padding: '0.75rem', textAlign: 'left', color: '#aaa' }}>Nome</th>
              <th style={{ padding: '0.75rem', textAlign: 'left', color: '#aaa' }}>CPF</th>
              <th style={{ padding: '0.75rem', textAlign: 'left', color: '#aaa' }}>Idade</th>
              <th style={{ padding: '0.75rem', textAlign: 'left', color: '#aaa' }}>Email</th>
              <th style={{ padding: '0.75rem', color: '#aaa' }}></th>
            </tr>
          </thead>
          <tbody>
            {students.map((s) => (
              <tr key={s.id} style={{ borderTop: '1px solid #333' }}>
                <td style={{ padding: '0.75rem', color: '#eee' }}>{s.name}</td>
                <td style={{ padding: '0.75rem', color: '#aaa' }}>{s.cpf}</td>
                <td style={{ padding: '0.75rem', color: '#aaa' }}>{s.age}</td>
                <td style={{ padding: '0.75rem', color: '#aaa' }}>{s.email || '-'}</td>
                <td style={{ padding: '0.75rem' }}>
                  <Link to={`/students/${s.id}`} style={{ color: '#e94560', textDecoration: 'none' }}>Ver</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
