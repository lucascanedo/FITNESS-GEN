import { Link } from 'react-router-dom'

export function Dashboard() {
  return (
    <div>
      <h1 style={{ marginBottom: '1rem', color: '#eee' }}>Dashboard</h1>
      <p style={{ color: '#888', marginBottom: '2rem' }}>
        Bem-vindo ao Fitness Gen. Gerencie seus alunos, anamneses, medições e planos de treino.
      </p>
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        <Link to="/students" style={{
          padding: '1rem 1.5rem',
          background: '#1a1a2e',
          borderRadius: 8,
          color: '#e94560',
          textDecoration: 'none',
          border: '1px solid #333',
        }}>Ver alunos</Link>
        <Link to="/students/new" style={{
          padding: '1rem 1.5rem',
          background: '#e94560',
          borderRadius: 8,
          color: '#fff',
          textDecoration: 'none',
        }}>Novo aluno</Link>
      </div>
    </div>
  )
}
