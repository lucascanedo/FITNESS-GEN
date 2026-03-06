import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { api } from '../api/client'
import type { Plan, PlanBody, PlanItem } from '../types'

export function PlanEdit() {
  const { planId } = useParams<{ planId: string }>()
  const [plan, setPlan] = useState<Plan | null>(null)
  const [edited, setEdited] = useState<PlanBody | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const id = Number(planId)

  useEffect(() => {
    if (!id) return
    api.plans.get(id)
      .then((p) => {
        setPlan(p)
        setEdited(p.plan_json)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  const handleSave = () => {
    if (!edited) return
    setSaving(true)
    setError(null)
    api.plans.update(id, { plan_meta: edited.plan_meta, items: edited.items })
      .then(() => setPlan((prev) => prev ? { ...prev, plan_json: edited, edit_count: (prev.edit_count || 0) + 1 } : null))
      .catch((e) => setError(e.message))
      .finally(() => setSaving(false))
  }

  const updateItem = (index: number, field: keyof PlanItem, value: string | number) => {
    if (!edited) return
    const items = [...edited.items]
    items[index] = { ...items[index], [field]: value }
    setEdited({ ...edited, items })
  }

  if (loading) return <p style={{ color: '#888' }}>Carregando...</p>
  if (error || !plan) return <p style={{ color: '#e94560' }}>Erro: {error || 'Plano não encontrado'}</p>
  if (!edited) return null

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <Link to={`/students/${plan.student_id}`} style={{ color: '#888', textDecoration: 'none' }}>← Aluno</Link>
        <h1 style={{ color: '#eee', marginTop: '0.5rem' }}>Editar plano #{plan.id}</h1>
        <p style={{ color: '#888' }}>Edições: {plan.edit_count ?? 0}</p>
      </div>

      {error && <p style={{ color: '#e94560', marginBottom: '1rem' }}>{error}</p>}

      <div style={{ marginBottom: '1rem' }}>
        <label style={{ display: 'block', color: '#aaa', marginBottom: 4 }}>Split</label>
        <input
          value={edited.plan_meta.split}
          onChange={(e) => setEdited({ ...edited, plan_meta: { ...edited.plan_meta, split: e.target.value } })}
          style={{ width: 200, padding: '0.5rem', background: '#1a1a2e', border: '1px solid #333', borderRadius: 4, color: '#eee' }}
        />
      </div>
      <div style={{ marginBottom: '1rem' }}>
        <label style={{ display: 'block', color: '#aaa', marginBottom: 4 }}>Objetivo</label>
        <input
          value={edited.plan_meta.goal}
          onChange={(e) => setEdited({ ...edited, plan_meta: { ...edited.plan_meta, goal: e.target.value } })}
          style={{ width: '100%', maxWidth: 400, padding: '0.5rem', background: '#1a1a2e', border: '1px solid #333', borderRadius: 4, color: '#eee' }}
        />
      </div>

      <h3 style={{ color: '#eee', marginBottom: '0.5rem' }}>Exercícios</h3>
      <div style={{ marginBottom: '1.5rem' }}>
        {edited.items.map((it, i) => (
          <div key={i} style={{
            padding: '1rem',
            background: '#1a1a2e',
            borderRadius: 8,
            marginBottom: '0.5rem',
            border: '1px solid #333',
          }}>
            <input
              value={it.exercise_name}
              onChange={(e) => updateItem(i, 'exercise_name', e.target.value)}
              placeholder="Exercício"
              style={{ width: '100%', padding: '0.5rem', marginBottom: '0.5rem', background: '#0f0f23', border: '1px solid #333', borderRadius: 4, color: '#eee' }}
            />
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <input type="number" value={it.sets} onChange={(e) => updateItem(i, 'sets', Number(e.target.value))} placeholder="Séries"
                style={{ width: 60, padding: '0.5rem', background: '#0f0f23', border: '1px solid #333', borderRadius: 4, color: '#eee' }} />
              <input value={it.reps} onChange={(e) => updateItem(i, 'reps', e.target.value)} placeholder="Reps"
                style={{ width: 80, padding: '0.5rem', background: '#0f0f23', border: '1px solid #333', borderRadius: 4, color: '#eee' }} />
              <input type="number" value={it.rest_s} onChange={(e) => updateItem(i, 'rest_s', Number(e.target.value))} placeholder="Descanso (s)"
                style={{ width: 80, padding: '0.5rem', background: '#0f0f23', border: '1px solid #333', borderRadius: 4, color: '#eee' }} />
            </div>
          </div>
        ))}
      </div>

      <button onClick={handleSave} disabled={saving}
        style={{ padding: '0.75rem 1.5rem', background: '#e94560', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>
        {saving ? 'Salvando...' : 'Salvar alterações'}
      </button>
    </div>
  )
}
