import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { api } from '../api/client'
import type { Student, Assessment, Measurement, PlanBody, PlanItem } from '../types'

export function PlanNew() {
  const { studentId } = useParams<{ studentId: string }>()
  const [student, setStudent] = useState<Student | null>(null)
  const [assessments, setAssessments] = useState<Assessment[]>([])
  const [measurements, setMeasurements] = useState<Measurement[]>([])
  const [assessmentId, setAssessmentId] = useState<number | ''>('')
  const [measurementId, setMeasurementId] = useState<number | ''>('')
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [plan, setPlan] = useState<PlanBody | null>(null)
  const [llmCallId, setLlmCallId] = useState<number | undefined>()
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const id = Number(studentId)

  useEffect(() => {
    if (!id) return
    Promise.all([
      api.students.get(id),
      api.assessments.list(id),
      api.measurements.list(id),
    ]).then(([s, a, m]) => {
      setStudent(s)
      setAssessments(a)
      setMeasurements(m)
      if (a.length && !assessmentId) setAssessmentId(a[0].id)
      if (m.length && !measurementId) setMeasurementId(m[0].id)
    }).catch((e) => setError(e.message))
  }, [id])

  const handleGenerate = () => {
    const aid = Number(assessmentId)
    const mid = Number(measurementId)
    if (!aid || !mid) {
      setError('Selecione avaliação e medição.')
      return
    }
    setGenerating(true)
    setError(null)
    api.llm.generatePlan(id, aid, mid)
      .then((res) => {
        setPlan(res.plan)
        setLlmCallId(res.llm_call_id)
      })
      .catch((e) => setError(e.message))
      .finally(() => setGenerating(false))
  }

  const handleSave = () => {
    if (!plan) return
    const aid = Number(assessmentId)
    const mid = Number(measurementId)
    if (!aid || !mid) {
      setError('Selecione avaliação e medição.')
      return
    }
    setLoading(true)
    setError(null)
    api.plans.create({
      student_id: id,
      assessment_id: aid,
      measurement_id: mid,
      plan_meta: plan.plan_meta,
      items: plan.items,
      generated_plan_json: plan,
      llm_call_id: llmCallId,
    })
      .then((p) => navigate(`/plans/${p.id}/edit`))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  if (!student) return <p style={{ color: '#888' }}>Carregando...</p>

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <Link to={`/students/${id}`} style={{ color: '#888', textDecoration: 'none' }}>← {student.name}</Link>
        <h1 style={{ color: '#eee', marginTop: '0.5rem' }}>Novo plano</h1>
      </div>

      {error && <p style={{ color: '#e94560', marginBottom: '1rem' }}>{error}</p>}

      {!plan ? (
        <>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', color: '#aaa', marginBottom: 4 }}>Avaliação</label>
            <select
              value={assessmentId}
              onChange={(e) => setAssessmentId(e.target.value ? Number(e.target.value) : '')}
              style={{ width: 300, padding: '0.5rem', background: '#1a1a2e', border: '1px solid #333', borderRadius: 4, color: '#eee' }}
            >
              <option value="">Selecione</option>
              {assessments.map((a) => (
                <option key={a.id} value={a.id}>Avaliação #{a.id}</option>
              ))}
            </select>
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', color: '#aaa', marginBottom: 4 }}>Medição</label>
            <select
              value={measurementId}
              onChange={(e) => setMeasurementId(e.target.value ? Number(e.target.value) : '')}
              style={{ width: 300, padding: '0.5rem', background: '#1a1a2e', border: '1px solid #333', borderRadius: 4, color: '#eee' }}
            >
              <option value="">Selecione</option>
              {measurements.map((m) => (
                <option key={m.id} value={m.id}>Medição #{m.id}</option>
              ))}
            </select>
          </div>
          <button
            onClick={handleGenerate}
            disabled={generating}
            style={{ padding: '0.75rem 1.5rem', background: '#e94560', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}
          >
            {generating ? 'Gerando...' : 'Gerar plano com IA'}
          </button>
        </>
      ) : (
        <>
          <p style={{ color: '#888', marginBottom: '1rem' }}>Edite o plano e salve.</p>
          <div style={{ marginBottom: '1rem' }}>
            <span style={{ color: '#eee' }}>Split: {plan.plan_meta.split} | Objetivo: {plan.plan_meta.goal}</span>
          </div>
          <div style={{ marginBottom: '1rem', maxHeight: 400, overflow: 'auto', background: '#1a1a2e', padding: '1rem', borderRadius: 8 }}>
            {plan.items.map((it, i) => (
              <div key={i} style={{ padding: '0.5rem 0', borderBottom: '1px solid #333', color: '#aaa' }}>
                {it.exercise_name} — {it.sets}x{it.reps} @ {it.rest_s}s
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button onClick={handleSave} disabled={loading}
              style={{ padding: '0.75rem 1.5rem', background: '#e94560', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>
              {loading ? 'Salvando...' : 'Salvar plano'}
            </button>
            <button onClick={() => setPlan(null)}
              style={{ padding: '0.75rem 1.5rem', background: '#333', color: '#eee', border: 'none', borderRadius: 4, cursor: 'pointer' }}>
              Gerar outro
            </button>
          </div>
        </>
      )}
    </div>
  )
}
