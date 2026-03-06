import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type { Student, Assessment, Measurement, Plan } from '../types'

type Tab = 'overview' | 'anamnesis' | 'assessments' | 'measurements' | 'plans'

export function StudentDetail() {
  const { studentId } = useParams<{ studentId: string }>()
  const [student, setStudent] = useState<Student | null>(null)
  const [assessments, setAssessments] = useState<Assessment[]>([])
  const [measurements, setMeasurements] = useState<Measurement[]>([])
  const [plans, setPlans] = useState<Plan[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const id = Number(studentId)

  useEffect(() => {
    if (!id) return
    Promise.all([
      api.students.get(id),
      api.assessments.list(id),
      api.measurements.list(id),
      api.plans.list(id),
    ])
      .then(([s, a, m, p]) => {
        setStudent(s)
        setAssessments(a)
        setMeasurements(m)
        setPlans(p)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <p style={{ color: '#888' }}>Carregando...</p>
  if (error || !student) return <p style={{ color: '#e94560' }}>Erro: {error || 'Aluno não encontrado'}</p>

  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const tabs: { key: Tab; label: string }[] = [
    { key: 'overview', label: 'Visão geral' },
    { key: 'anamnesis', label: 'Anamnese' },
    { key: 'assessments', label: 'Avaliações' },
    { key: 'measurements', label: 'Medições' },
    { key: 'plans', label: 'Planos' },
  ]

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <Link to="/students" style={{ color: '#888', textDecoration: 'none', fontSize: 14 }}>← Alunos</Link>
        <h1 style={{ color: '#eee', marginTop: '0.5rem' }}>{student.name}</h1>
        <p style={{ color: '#888' }}>CPF: {student.cpf} | Idade: {student.age} | {student.email || '-'}</p>
      </div>

      <nav style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '1px solid #333' }}>
        {tabs.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            onClick={() => setActiveTab(key)}
            style={{
              padding: '0.75rem 1rem',
              background: 'none',
              border: 'none',
              color: activeTab === key ? '#e94560' : '#888',
              cursor: 'pointer',
              borderBottom: activeTab === key ? '2px solid #e94560' : '2px solid transparent',
              marginBottom: -1,
            }}
          >
            {label}
          </button>
        ))}
      </nav>

      <TabContent
        tab={activeTab}
        student={student}
        assessments={assessments}
        measurements={measurements}
        plans={plans}
      />
    </div>
  )
}

function TabContent({ tab, student, assessments, measurements, plans }: {
  tab: Tab
  student: Student
  assessments: Assessment[]
  measurements: Measurement[]
  plans: Plan[]
}) {
  switch (tab) {
    case 'overview':
      return (
        <div style={{ color: '#aaa' }}>
          <p><strong style={{ color: '#eee' }}>Nome:</strong> {student.name}</p>
          <p><strong style={{ color: '#eee' }}>CPF:</strong> {student.cpf}</p>
          <p><strong style={{ color: '#eee' }}>Idade:</strong> {student.age}</p>
          <p><strong style={{ color: '#eee' }}>Email:</strong> {student.email || '-'}</p>
          <p><strong style={{ color: '#eee' }}>Telefone:</strong> {student.phone || '-'}</p>
          <p><strong style={{ color: '#eee' }}>Avaliações:</strong> {assessments.length}</p>
          <p><strong style={{ color: '#eee' }}>Medições:</strong> {measurements.length}</p>
          <p><strong style={{ color: '#eee' }}>Planos:</strong> {plans.length}</p>
        </div>
      )
    case 'assessments':
      return (
        <div>
          <p style={{ color: '#888' }}>Total: {assessments.length} avaliação(ões)</p>
          {assessments.length === 0 && <p style={{ color: '#888' }}>Nenhuma avaliação.</p>}
          {assessments.map((a) => (
            <div key={a.id} style={{ padding: '1rem', background: '#1a1a2e', borderRadius: 8, marginBottom: '0.5rem', border: '1px solid #333' }}>
              <p style={{ color: '#eee' }}>ID {a.id} | Nível: {a.level || '-'} | Freq/sem: {a.freq_per_week ?? '-'}</p>
            </div>
          ))}
        </div>
      )
    case 'measurements':
      return (
        <div>
          <p style={{ color: '#888' }}>Total: {measurements.length} medição(ões)</p>
          {measurements.length === 0 && <p style={{ color: '#888' }}>Nenhuma medição.</p>}
          {measurements.map((m) => (
            <div key={m.id} style={{ padding: '1rem', background: '#1a1a2e', borderRadius: 8, marginBottom: '0.5rem', border: '1px solid #333' }}>
              <p style={{ color: '#eee' }}>ID {m.id} | Peso: {m.weight_kg ?? '-'} kg | Altura: {m.height_m ?? '-'} m | IMC: {m.bmi ?? '-'}</p>
            </div>
          ))}
        </div>
      )
    case 'plans':
      return (
        <div>
          <Link to={`/students/${student.id}/plan/new`} style={{
            display: 'inline-block',
            marginBottom: '1rem',
            padding: '0.5rem 1rem',
            background: '#e94560',
            color: '#fff',
            textDecoration: 'none',
            borderRadius: 4,
          }}>Gerar novo plano</Link>
          {plans.length === 0 && <p style={{ color: '#888' }}>Nenhum plano.</p>}
          {plans.map((p) => (
            <div key={p.id} style={{ padding: '1rem', background: '#1a1a2e', borderRadius: 8, marginBottom: '0.5rem', border: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#eee' }}>Plano #{p.id} | Split: {p.plan_json?.plan_meta?.split || '-'}</span>
              <Link to={`/plans/${p.id}/edit`} style={{ color: '#e94560', textDecoration: 'none' }}>Editar</Link>
            </div>
          ))}
        </div>
      )
    case 'anamnesis':
      return <p style={{ color: '#888' }}>Anamnese integrada às avaliações.</p>
    default:
      return null
  }
}
