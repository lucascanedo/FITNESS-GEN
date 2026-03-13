import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { Layout } from './components/Layout'
import { Login } from './pages/Login'
import { Dashboard } from './pages/Dashboard'
import { StudentsList } from './pages/StudentsList'
import { StudentNew } from './pages/StudentNew'
import { StudentDetail } from './pages/StudentDetail'
import { StudentOnboarding } from './pages/StudentOnboarding'
import { PlanNew } from './pages/PlanNew'
import { PlanEdit } from './pages/PlanEdit'
import './index.css'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth()
  if (loading) return <div className="app-shell-loading">Carregando sessao...</div>
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="students" element={<StudentsList />} />
            <Route path="students/new" element={<StudentNew />} />
            <Route path="students/:studentId" element={<StudentDetail />} />
            <Route path="students/:studentId/onboarding" element={<StudentOnboarding />} />
            <Route path="students/:studentId/plan/new" element={<PlanNew />} />
            <Route path="plans/:planId/edit" element={<PlanEdit />} />
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
