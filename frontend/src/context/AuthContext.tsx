import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { api } from '../api/client'
import type { Teacher } from '../types'

interface AuthContextType {
  teacher: Teacher | null
  isAuthenticated: boolean
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

const TOKEN_KEY = 'fitness-gen-token'
const TEACHER_KEY = 'fitness-gen-teacher'

function persistSession(token: string, teacher: Teacher) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(TEACHER_KEY, JSON.stringify(teacher))
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [teacher, setTeacher] = useState<Teacher | null>(() => {
    const raw = localStorage.getItem(TEACHER_KEY)
    return raw ? JSON.parse(raw) as Teacher : null
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) {
      setLoading(false)
      return
    }

    api.auth.me()
      .then((currentTeacher) => {
        setTeacher(currentTeacher)
        localStorage.setItem(TEACHER_KEY, JSON.stringify(currentTeacher))
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(TEACHER_KEY)
        setTeacher(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const login = async (email: string, password: string) => {
    const result = await api.auth.login({ email, password })
    persistSession(result.access_token, result.teacher)
    setTeacher(result.teacher)
  }

  const register = async (name: string, email: string, password: string) => {
    const result = await api.auth.register({ name, email, password })
    persistSession(result.access_token, result.teacher)
    setTeacher(result.teacher)
  }

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(TEACHER_KEY)
    setTeacher(null)
  }

  return (
    <AuthContext.Provider
      value={{ teacher, isAuthenticated: !!teacher, loading, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
