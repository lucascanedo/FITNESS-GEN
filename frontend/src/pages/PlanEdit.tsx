import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type { Plan, PlanBody, PlanItem } from '../types'

export function PlanEdit() {
  const { planId } = useParams<{ planId: string }>()
  const [plan, setPlan] = useState<Plan | null>(null)
  const [edited, setEdited] = useState<PlanBody | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const id = Number(planId)

  useEffect(() => {
    if (!id) return
    api.plans.get(id)
      .then((result) => {
        setPlan(result)
        setEdited(result.plan_json)
      })
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false))
  }, [id])

  const handleSave = () => {
    if (!edited) return
    setSaving(true)
    setError(null)
    api.plans.update(id, { plan_meta: edited.plan_meta, items: edited.items })
      .then(() => {
        setPlan((current) => current ? {
          ...current,
          plan_json: edited,
          edit_count: (current.edit_count || 0) + 1,
        } : null)
      })
      .catch((requestError) => setError(requestError.message))
      .finally(() => setSaving(false))
  }

  const updateItem = (index: number, field: keyof PlanItem, value: string | number) => {
    if (!edited) return
    const nextItems = [...edited.items]
    nextItems[index] = { ...nextItems[index], [field]: value }
    setEdited({ ...edited, items: nextItems })
  }

  if (loading) return <p className="status-text">Carregando plano...</p>
  if (error || !plan || !edited) return <p className="status-text error">Erro: {error || 'Plano nao encontrado'}</p>

  return (
    <div className="content-stack plan-page">
      <section className="page-heading-card compact-hero">
        <div>
          <div className="breadcrumb">
            <Link to="/students">Alunos</Link>
            <span>/</span>
            <Link to={`/students/${plan.student_id}`}>Aluno</Link>
            <span>/</span>
            <strong>Edicao do plano</strong>
          </div>
          <span className="eyebrow">Edicao</span>
          <h1>Plano #{plan.id}</h1>
          <p>Revise a estrutura, os dias e os exercicios antes de concluir.</p>
        </div>

        <div className="status-banner neutral">
          <span className="status-banner-label">Historico</span>
          <strong>{plan.edit_count ?? 0} edicoes</strong>
          <span>Ultima versao em modo rascunho.</span>
        </div>
      </section>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="workspace-layout">
        <section className="form-card workspace-card">
          <div className="form-row">
            <div className="field">
              <label htmlFor="split">Divisao</label>
              <input
                id="split"
                value={edited.plan_meta.split}
                onChange={(event) => setEdited({
                  ...edited,
                  plan_meta: { ...edited.plan_meta, split: event.target.value },
                })}
              />
            </div>
            <div className="field">
              <label htmlFor="goal">Objetivo</label>
              <input
                id="goal"
                value={edited.plan_meta.goal}
                onChange={(event) => setEdited({
                  ...edited,
                  plan_meta: { ...edited.plan_meta, goal: event.target.value },
                })}
              />
            </div>
          </div>

          <div className="content-stack relaxed">
            {edited.items.map((item, index) => (
              <article key={`${item.day}-${index}`} className="plan-editor-card">
                <div className="plan-editor-head">
                  <strong>{item.day}</strong>
                  <span>{item.block || 'Principal'}</span>
                </div>

                <div className="field">
                  <label htmlFor={`exercise-${index}`}>Exercicio</label>
                  <input
                    id={`exercise-${index}`}
                    value={item.exercise_name}
                    onChange={(event) => updateItem(index, 'exercise_name', event.target.value)}
                  />
                </div>

                <div className="form-row plan-editor-row">
                  <div className="field">
                    <label htmlFor={`sets-${index}`}>Series</label>
                    <input
                      id={`sets-${index}`}
                      type="number"
                      value={item.sets}
                      onChange={(event) => updateItem(index, 'sets', Number(event.target.value))}
                    />
                  </div>
                  <div className="field">
                    <label htmlFor={`reps-${index}`}>Repeticoes</label>
                    <input
                      id={`reps-${index}`}
                      value={item.reps}
                      onChange={(event) => updateItem(index, 'reps', event.target.value)}
                    />
                  </div>
                  <div className="field">
                    <label htmlFor={`rest-${index}`}>Descanso (s)</label>
                    <input
                      id={`rest-${index}`}
                      type="number"
                      value={item.rest_s}
                      onChange={(event) => updateItem(index, 'rest_s', Number(event.target.value))}
                    />
                  </div>
                </div>
              </article>
            ))}
          </div>

          <div className="workspace-action-bar">
            <button onClick={handleSave} disabled={saving} className="btn-primary btn-lg" type="button">
              {saving ? 'Salvando...' : 'Salvar alteracoes'}
            </button>
          </div>
        </section>

        <aside className="sidebar-rail">
          <div className="content-stack relaxed">
            <section className="info-card">
              <span className="eyebrow">Resumo</span>
              <h3>Estrutura atual</h3>
              <div className="metric-list">
                <div>
                  <span>Divisao</span>
                  <strong>{edited.plan_meta.split}</strong>
                </div>
                <div>
                  <span>Objetivo</span>
                  <strong>{edited.plan_meta.goal}</strong>
                </div>
                <div>
                  <span>Exercicios</span>
                  <strong>{edited.items.length}</strong>
                </div>
              </div>
            </section>
          </div>
        </aside>
      </section>
    </div>
  )
}
