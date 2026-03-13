const BASE = '/api'

function getToken() {
  return localStorage.getItem('fitness-gen-token')
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken()
  let res: Response
  try {
    res = await fetch(`${BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options?.headers,
      },
    })
  } catch {
    throw new Error('Nao foi possivel conectar ao servidor. Confira se o backend esta ativo.')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || res.statusText)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  auth: {
    register: (data: { name: string; email: string; password: string }) =>
      request<import('../types').AuthResponse>('/auth/register', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    login: (data: { email: string; password: string }) =>
      request<import('../types').AuthResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    me: () => request<import('../types').Teacher>('/auth/me'),
  },
  students: {
    list: () => request<import('../types').Student[]>('/students'),
    get: (id: number) => request<import('../types').Student>(`/students/${id}`),
    create: (data: Omit<import('../types').Student, 'id' | 'age' | 'created_at'>) =>
      request<import('../types').Student>('/students', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Partial<import('../types').Student>) =>
      request<import('../types').Student>(`/students/update?id=${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  },
  assessments: {
    list: (studentId: number) => request<import('../types').Assessment[]>(`/assessments/student/${studentId}`),
    get: (id: number) => request<import('../types').Assessment>(`/assessments/${id}`),
    create: (data: import('../types').AssessmentInput) =>
      request<import('../types').Assessment>('/assessments', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Partial<import('../types').Assessment>) =>
      request<import('../types').Assessment>(`/assessments/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  },
  measurements: {
    list: (studentId: number) => request<import('../types').Measurement[]>(`/measurements/student/${studentId}`),
    get: (id: number) => request<import('../types').Measurement>(`/measurements/${id}`),
    create: (data: import('../types').MeasurementInput) =>
      request<import('../types').Measurement>('/measurements', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Partial<import('../types').Measurement>) =>
      request<import('../types').Measurement>(`/measurements/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  },
  plans: {
    list: (studentId: number) => request<import('../types').Plan[]>(`/plans/student/${studentId}`),
    get: (id: number) => request<import('../types').Plan>(`/plans/${id}`),
    create: (data: {
      student_id: number
      assessment_id: number
      measurement_id: number
      plan_meta: import('../types').PlanMeta
      items: import('../types').PlanItem[]
      generated_plan_json?: import('../types').PlanBody
      llm_call_id?: number
    }) => request<import('../types').Plan>('/plans', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: { plan_meta?: import('../types').PlanMeta; items?: import('../types').PlanItem[] }) =>
      request<import('../types').Plan>(`/plans/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  },
  llm: {
    generatePlan: (
      studentId: number,
      assessmentId: number,
      measurementId: number
    ) =>
      request<import('../types').PlanGenerationResponse>(
        `/llm/generate-plan/student/${studentId}/assessment/${assessmentId}/measurement/${measurementId}`,
        { method: 'POST' }
      ),
  },
}
