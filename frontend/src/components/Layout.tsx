import { Outlet, Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Layout() {
  const { logout, teacher } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <Link to="/dashboard" className="brand-link">
            Fitness Gen
          </Link>
          <span className="brand-tag">Professor workspace</span>
        </div>

        <nav className="topbar-nav">
          <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            Dashboard
          </NavLink>
          <NavLink to="/students" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            Alunos
          </NavLink>
          <NavLink to="/students/new" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            Cadastrar aluno
          </NavLink>
        </nav>

        <div className="topbar-actions">
          <div className="teacher-badge">
            <span>{teacher?.name}</span>
            <small>{teacher?.email}</small>
          </div>
          <button onClick={handleLogout} className="btn-secondary" type="button">
            Sair
          </button>
        </div>
      </header>

      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
