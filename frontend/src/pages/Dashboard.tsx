import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Dashboard() {
  const { teacher } = useAuth()

  return (
    <div className="content-stack">
      <section className="hero-card">
        <div>
          <span className="eyebrow">Dashboard</span>
          <h1>Ola, {teacher?.name?.split(' ')[0] || 'Professor'}.</h1>
          <p>
            Painel inicial para seguir direto para os alunos ou iniciar um novo cadastro
            sem adicionar complexidade desnecessaria nesta etapa.
          </p>
        </div>

        <div className="hero-actions">
          <Link to="/students" className="btn-primary">Acessar alunos</Link>
          <Link to="/students/new" className="btn-secondary">Cadastrar aluno</Link>
        </div>
      </section>

      <section className="dashboard-grid">
        <Link to="/students" className="feature-card">
          <span className="feature-kicker">Gestao</span>
          <h3>Base de alunos</h3>
          <p>Lista responsiva com acesso ao detalhe do aluno e atalho para criacao de plano.</p>
        </Link>
        <Link to="/students/new" className="feature-card accent">
          <span className="feature-kicker">Cadastro</span>
          <h3>Novo aluno</h3>
          <p>Formulario inicial estruturado para receber depois assessment e measurement.</p>
        </Link>
      </section>
    </div>
  )
}
