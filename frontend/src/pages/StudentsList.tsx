import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { Student } from '../types'

export function StudentsList() {
  const [students, setStudents] = useState<Student[]>([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.students.list()
      .then(setStudents)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const filteredStudents = students.filter((student) => {
    const term = query.trim().toLowerCase()
    if (!term) return true
    return (
      student.name.toLowerCase().includes(term) ||
      student.cpf.includes(term) ||
      (student.email || '').toLowerCase().includes(term)
    )
  })

  if (loading) return <p className="status-text">Carregando alunos...</p>
  if (error) return <p className="status-text error">Erro: {error}</p>

  return (
    <div className="content-stack">
      <section className="section-header-card">
        <div>
          <span className="eyebrow">Alunos</span>
          <h1>Base de alunos cadastrados</h1>
          <p>Entre no detalhe do aluno, visualize os dados basicos e siga para a criacao do plano.</p>
        </div>

        <div className="section-actions">
          <input
            className="search-input"
            placeholder="Buscar por nome, CPF ou email"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <Link to="/students/new" className="btn-primary">Cadastrar aluno</Link>
        </div>
      </section>

      <div className="student-grid">
        {filteredStudents.map((student) => (
          <article key={student.id} className="student-card">
            <div className="student-card-head">
              <div>
                <h3>{student.name}</h3>
                <p>{student.email || 'Sem email cadastrado'}</p>
              </div>
              <span className="pill">{student.age} anos</span>
            </div>

            <dl className="student-meta">
              <div><dt>CPF</dt><dd>{student.cpf}</dd></div>
              <div><dt>Telefone</dt><dd>{student.phone || '-'}</dd></div>
            </dl>

            <div className="student-card-actions">
              <Link to={`/students/${student.id}`} className="btn-secondary">Abrir aluno</Link>
              <Link to={`/students/${student.id}/onboarding`} className="btn-primary">Completar cadastro</Link>
            </div>
          </article>
        ))}
      </div>

      {filteredStudents.length === 0 && <p className="status-text">Nenhum aluno encontrado.</p>}
    </div>
  )
}
