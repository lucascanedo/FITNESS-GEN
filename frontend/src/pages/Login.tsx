import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Login() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const { login, register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setLoading(true)

    try {
      if (mode === 'register') {
        await register(name, email, password)
        setSuccess('Conta criada com sucesso.')
      } else {
        await login(email, password)
      }
      navigate('/dashboard')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao autenticar.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <section className="auth-hero">
        <div className="hero-chip">Fitness Gen</div>
        <h1>Gerencie alunos e construa planos com ritmo de consultoria premium.</h1>
        <p>
          Workspace inicial do professor para organizar cadastro, acompanhar o contexto do aluno
          e preparar o fluxo que depois se conecta a assessments, measurements e LLM.
        </p>

        <div className="hero-metrics">
          <div>
            <strong>Cadastro</strong>
            <span>Onboarding rapido do professor e do aluno</span>
          </div>
          <div>
            <strong>Contexto</strong>
            <span>Estrutura pronta para detalhe, historico e evolucao</span>
          </div>
          <div>
            <strong>Planos</strong>
            <span>Ponto de partida para geracao e edicao posterior</span>
          </div>
        </div>
      </section>

      <section className="auth-panel">
        <div className="auth-panel-header">
          <div>
            <span className="eyebrow">Acesso do professor</span>
            <h2>{mode === 'login' ? 'Entrar na plataforma' : 'Criar conta'}</h2>
          </div>
          <div className="auth-switch">
            <button
              type="button"
              className={mode === 'login' ? 'switch-btn active' : 'switch-btn'}
              onClick={() => setMode('login')}
            >
              Login
            </button>
            <button
              type="button"
              className={mode === 'register' ? 'switch-btn active' : 'switch-btn'}
              onClick={() => setMode('register')}
            >
              Cadastro
            </button>
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          {mode === 'register' && (
            <div className="field">
              <label htmlFor="name">Nome</label>
              <input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
          )}

          <div className="field">
            <label htmlFor="email">Email</label>
            <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>

          <div className="field">
            <label htmlFor="password">Senha</label>
            <input
              id="password"
              type="password"
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn-primary btn-block" disabled={loading}>
            {loading ? 'Processando...' : mode === 'login' ? 'Entrar' : 'Criar conta'}
          </button>
        </form>
      </section>
    </div>
  )
}
