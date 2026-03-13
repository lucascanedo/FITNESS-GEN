import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type { Assessment, Measurement, PlanBody, Student } from '../types'
import {
  getLatestAssessment,
  getLatestMeasurement,
  getStatusMessage,
  getStatusTone,
  getStudentSetupStatus,
  isStudentReadyForPlan,
} from '../utils/studentFlow'

function formatAssessmentLabel(assessment: Assessment) {
  return `#${assessment.id} • ${assessment.level || 'nivel nao informado'} • ${assessment.freq_per_week ?? '-'}x/semana`
}

function formatMeasurementLabel(measurement: Measurement) {
  return `#${measurement.id} • ${measurement.weight_kg ?? '-'} kg • IMC ${measurement.bmi ?? '-'}`
}

function readJsonArray(value: unknown, key: string) {
  if (!value || typeof value !== 'object') return []
  const record = value as Record<string, unknown>
  const raw = record[key]
  return Array.isArray(raw) ? raw.filter((item): item is string => typeof item === 'string') : []
}

function readJsonText(value: unknown, key: string) {
  if (!value || typeof value !== 'object') return ''
  const record = value as Record<string, unknown>
  const raw = record[key]
  return typeof raw === 'string' ? raw : ''
}

export function PlanNew() {
  const { studentId } = useParams<{ studentId: string }>()
  const navigate = useNavigate()
  const [student, setStudent] = useState<Student | null>(null)
  const [assessments, setAssessments] = useState<Assessment[]>([])
  const [measurements, setMeasurements] = useState<Measurement[]>([])
  const [assessmentId, setAssessmentId] = useState<number | ''>('')
  const [measurementId, setMeasurementId] = useState<number | ''>('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [plan, setPlan] = useState<PlanBody | null>(null)
  const [llmCallId, setLlmCallId] = useState<number | undefined>()
  const [error, setError] = useState<string | null>(null)

  const id = Number(studentId)

  useEffect(() => {
    if (!id) return

    Promise.all([
      api.students.get(id),
      api.assessments.list(id),
      api.measurements.list(id),
    ])
      .then(([studentResult, assessmentsResult, measurementsResult]) => {
        const latestAssessment = getLatestAssessment(assessmentsResult)
        const latestMeasurement = getLatestMeasurement(measurementsResult)
        setStudent(studentResult)
        setAssessments(assessmentsResult)
        setMeasurements(measurementsResult)
        setAssessmentId(latestAssessment?.id ?? '')
        setMeasurementId(latestMeasurement?.id ?? '')
      })
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <p className="status-text">Carregando workspace de plano...</p>
  if (error || !student) return <p className="status-text error">Erro: {error || 'Aluno nao encontrado'}</p>

  const ready = isStudentReadyForPlan(assessments, measurements)
  const status = getStudentSetupStatus(assessments, measurements)
  const tone = getStatusTone(status)
  const selectedAssessment = assessments.find((assessment) => assessment.id === Number(assessmentId)) ?? null
  const selectedMeasurement = measurements.find((measurement) => measurement.id === Number(measurementId)) ?? null
  const preferredDays = readJsonArray(selectedAssessment?.periodization, 'preferred_days')
  const splitPreference = readJsonText(selectedAssessment?.periodization, 'split_preference')

  const handleGenerate = async () => {
    const selectedAssessmentId = Number(assessmentId)
    const selectedMeasurementId = Number(measurementId)

    if (!selectedAssessmentId || !selectedMeasurementId) {
      setError('Selecione um assessment e uma measurement validos antes de gerar o plano.')
      return
    }

    setGenerating(true)
    setError(null)

    try {
      const result = await api.llm.generatePlan(id, selectedAssessmentId, selectedMeasurementId)
      setPlan(result.plan)
      setLlmCallId(result.llm_call_id)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Falha ao gerar plano.')
    } finally {
      setGenerating(false)
    }
  }

  const handleSave = async () => {
    const selectedAssessmentId = Number(assessmentId)
    const selectedMeasurementId = Number(measurementId)

    if (!plan || !selectedAssessmentId || !selectedMeasurementId) {
      setError('Os dados do plano ou as selecoes obrigatorias nao estao completos.')
      return
    }

    setSaving(true)
    setError(null)

    try {
      const savedPlan = await api.plans.create({
        student_id: id,
        assessment_id: selectedAssessmentId,
        measurement_id: selectedMeasurementId,
        plan_meta: plan.plan_meta,
        items: plan.items,
        generated_plan_json: plan,
        llm_call_id: llmCallId,
      })
      navigate(`/plans/${savedPlan.id}/edit`)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Falha ao salvar plano.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="content-stack plan-page">
      <section className="page-heading-card compact-hero">
        <div>
          <div className="breadcrumb">
            <Link to="/dashboard">Painel</Link>
            <span>/</span>
            <Link to="/students">Alunos</Link>
            <span>/</span>
            <Link to={`/students/${student.id}`}>{student.name}</Link>
            <span>/</span>
            <strong>Geracao de plano</strong>
          </div>
          <span className="eyebrow">Geracao de plano</span>
          <h1>Plano de treino para {student.name}</h1>
          <p>{getStatusMessage(status)}</p>
        </div>

        <div className={`status-banner ${tone}`}>
          <span className="status-banner-label">Elegibilidade</span>
          <strong>{status}</strong>
          <span>{ready ? 'Dados minimos completos.' : 'Geracao bloqueada ate concluir o onboarding.'}</span>
        </div>
      </section>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="workspace-layout">
        <div className="content-stack">
          {!plan ? (
            <section className="form-card workspace-card">
              <div className="section-title-row">
                <div>
                  <span className="eyebrow">Etapa final</span>
                  <h3>Selecionar contexto para a IA</h3>
                </div>
                <span className={ready ? 'pill tone-success' : 'pill tone-warning'}>
                  {ready ? 'Pronto' : 'Pendente'}
                </span>
              </div>

              {!ready && (
                <div className="inline-notice warning">
                  <strong>Existem pendencias no cadastro.</strong>
                  <p>
                    A geracao do plano exige assessment e measurements atualizados.
                  </p>
                  <div className="section-actions">
                    {assessments.length === 0 && (
                      <Link to={`/students/${student.id}/onboarding#assessment`} className="btn-secondary">
                        Preencher assessment
                      </Link>
                    )}
                    {measurements.length === 0 && (
                      <Link to={`/students/${student.id}/onboarding#measurement`} className="btn-secondary">
                        Preencher measurements
                      </Link>
                    )}
                  </div>
                </div>
              )}

              <div className="selection-grid">
                <div className="field">
                  <label htmlFor="assessment-select">Assessment</label>
                  <select
                    id="assessment-select"
                    value={assessmentId}
                    onChange={(event) => setAssessmentId(event.target.value ? Number(event.target.value) : '')}
                    disabled={assessments.length === 0}
                  >
                    <option value="">Selecione um assessment</option>
                    {assessments.map((assessment) => (
                      <option key={assessment.id} value={assessment.id}>
                        {formatAssessmentLabel(assessment)}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="field">
                  <label htmlFor="measurement-select">Measurements</label>
                  <select
                    id="measurement-select"
                    value={measurementId}
                    onChange={(event) => setMeasurementId(event.target.value ? Number(event.target.value) : '')}
                    disabled={measurements.length === 0}
                  >
                    <option value="">Selecione uma measurement</option>
                    {measurements.map((measurement) => (
                      <option key={measurement.id} value={measurement.id}>
                        {formatMeasurementLabel(measurement)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="workspace-action-bar">
                <button
                  type="button"
                  className="btn-primary btn-lg"
                  disabled={!ready || !assessmentId || !measurementId || generating}
                  onClick={handleGenerate}
                >
                  {generating ? 'Gerando plano...' : 'Gerar plano com IA'}
                </button>
              </div>
            </section>
          ) : (
            <section className="form-card workspace-card">
              <div className="section-title-row">
                <div>
                  <span className="eyebrow">Resultado da IA</span>
                  <h3>Rascunho gerado</h3>
                </div>
                <span className="pill tone-success">Pronto para revisao</span>
              </div>

              <div className="plan-preview-meta">
                <div>
                  <span>Split</span>
                  <strong>{plan.plan_meta.split}</strong>
                </div>
                <div>
                  <span>Objetivo</span>
                  <strong>{plan.plan_meta.goal}</strong>
                </div>
                <div>
                  <span>Exercicios</span>
                  <strong>{plan.items.length}</strong>
                </div>
              </div>

              <div className="plan-preview-list">
                {plan.items.map((item, index) => (
                  <article key={`${item.day}-${item.exercise_name}-${index}`} className="plan-preview-row">
                    <div>
                      <strong>{item.exercise_name}</strong>
                      <p>{item.day} • {item.block}</p>
                    </div>
                    <span>{item.sets}x{item.reps} • {item.rest_s}s</span>
                  </article>
                ))}
              </div>

              <div className="workspace-action-bar">
                <button type="button" className="btn-primary btn-lg" disabled={saving} onClick={handleSave}>
                  {saving ? 'Salvando plano...' : 'Salvar e revisar'}
                </button>
                <button type="button" className="btn-secondary" onClick={() => setPlan(null)}>
                  Gerar novamente
                </button>
              </div>
            </section>
          )}
        </div>

        <aside className="sidebar-rail">
          <div className="content-stack relaxed">
          <section className="info-card">
            <span className="eyebrow">Resumo do aluno</span>
            <h3>{student.name}</h3>
            <p>{student.age} anos • {student.email || 'Sem email cadastrado'}</p>
            <div className="metric-list">
              <div>
                <span>Assessments</span>
                <strong>{assessments.length}</strong>
              </div>
              <div>
                <span>Measurements</span>
                <strong>{measurements.length}</strong>
              </div>
            </div>
          </section>

          <section className={`info-card status-card ${tone}`}>
            <span className="eyebrow">Status do cadastro</span>
            <h3>{status}</h3>
            <div className="indicator-list">
              <div className={assessments.length > 0 ? 'indicator-row active' : 'indicator-row'}>
                <span className="indicator-dot" />
                <span>Assessment disponivel</span>
              </div>
              <div className={measurements.length > 0 ? 'indicator-row active' : 'indicator-row'}>
                <span className="indicator-dot" />
                <span>Measurement disponivel</span>
              </div>
              <div className={ready ? 'indicator-row active' : 'indicator-row'}>
                <span className="indicator-dot" />
                <span>Pronto para gerar plano</span>
              </div>
            </div>
          </section>

          <section className="info-card">
            <span className="eyebrow">Configuracao</span>
            <h3>Contexto da geracao</h3>
            <div className="summary-block">
              <strong>Assessment</strong>
              <p>
                {selectedAssessment
                  ? `${selectedAssessment.level || 'Nivel nao informado'} • ${selectedAssessment.freq_per_week ?? '-'}x por semana • ${selectedAssessment.session_time_min ?? '-'} min`
                  : 'Nenhum assessment selecionado.'}
              </p>
            </div>
            <div className="summary-block">
              <strong>Measurement</strong>
              <p>
                {selectedMeasurement
                  ? `${selectedMeasurement.weight_kg ?? '-'} kg • ${selectedMeasurement.height_m ?? '-'} m • IMC ${selectedMeasurement.bmi ?? '-'}`
                  : 'Nenhuma measurement selecionada.'}
              </p>
            </div>
            {(preferredDays.length > 0 || splitPreference) && (
              <div className="summary-block">
                <strong>Grade semanal</strong>
                <p>
                  {splitPreference ? `${splitPreference}` : 'Estrutura automatica'}
                  {preferredDays.length > 0 ? ` • ${preferredDays.join(', ')}` : ''}
                </p>
              </div>
            )}
            {!ready && (
              <div className="content-stack compact">
                <Link to={`/students/${student.id}/onboarding#assessment`} className="btn-secondary">Ir para onboarding</Link>
              </div>
            )}
          </section>
          </div>
        </aside>
      </section>
    </div>
  )
}
