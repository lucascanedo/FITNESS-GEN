import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type { Assessment, Measurement, Plan, Student } from '../types'
import {
  getLatestAssessment,
  getLatestMeasurement,
  getStatusMessage,
  getStatusTone,
  getStudentSetupStatus,
  isStudentReadyForPlan,
} from '../utils/studentFlow'

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
      .then(([studentResult, assessmentsResult, measurementsResult, plansResult]) => {
        setStudent(studentResult)
        setAssessments(assessmentsResult)
        setMeasurements(measurementsResult)
        setPlans(plansResult)
      })
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <p className="status-text">Carregando aluno...</p>
  if (error || !student) return <p className="status-text error">Erro: {error || 'Aluno nao encontrado'}</p>

  const latestAssessment = getLatestAssessment(assessments)
  const latestMeasurement = getLatestMeasurement(measurements)
  const status = getStudentSetupStatus(assessments, measurements)
  const tone = getStatusTone(status)
  const ready = isStudentReadyForPlan(assessments, measurements)

  return (
    <div className="content-stack student-page">
      <section className="page-heading-card compact-hero">
        <div>
          <div className="breadcrumb">
            <Link to="/dashboard">Painel</Link>
            <span>/</span>
            <Link to="/students">Alunos</Link>
            <span>/</span>
            <strong>{student.name}</strong>
          </div>
          <span className="eyebrow">Aluno</span>
          <h1>{student.name}</h1>
          <p>{getStatusMessage(status)}</p>
        </div>

        <div className="section-actions">
          <Link to={`/students/${student.id}/onboarding`} className="btn-secondary">Completar cadastro</Link>
          <Link
            to={`/students/${student.id}/plan/new`}
            className="btn-primary"
            aria-disabled={!ready}
          >
            {ready ? 'Gerar plano com IA' : 'Revisar pendencias'}
          </Link>
        </div>
      </section>

      <section className="student-overview-layout">
        <div className="content-stack">
          <section className="detail-grid">
            <article className="info-card">
              <span className="eyebrow">Dados basicos</span>
              <h3>Identificacao</h3>
              <p><strong>CPF:</strong> {student.cpf}</p>
              <p><strong>Idade:</strong> {student.age} anos</p>
              <p><strong>Email:</strong> {student.email || '-'}</p>
              <p><strong>Telefone:</strong> {student.phone || '-'}</p>
            </article>

            <article className={`info-card status-card ${tone}`}>
              <span className="eyebrow">Status do cadastro</span>
              <h3>{status}</h3>
              <p>{getStatusMessage(status)}</p>
              <div className="indicator-list">
                <div className={assessments.length > 0 ? 'indicator-row active' : 'indicator-row'}>
                  <span className="indicator-dot" />
                  <span>Assessment disponivel</span>
                </div>
                <div className={measurements.length > 0 ? 'indicator-row active' : 'indicator-row'}>
                  <span className="indicator-dot" />
                  <span>Measurements disponiveis</span>
                </div>
                <div className={ready ? 'indicator-row active' : 'indicator-row'}>
                  <span className="indicator-dot" />
                  <span>Pronto para gerar plano</span>
                </div>
              </div>
            </article>
          </section>

          <section className="detail-grid">
            <article className="info-card">
              <div className="section-title-row">
              <div>
                <span className="eyebrow">Assessment mais recente</span>
                  <h3>Contexto de treino</h3>
                </div>
                <Link to={`/students/${student.id}/onboarding#assessment`} className="btn-secondary">
                  {latestAssessment ? 'Atualizar assessment' : 'Preencher assessment'}
                </Link>
              </div>
              {latestAssessment ? (
                <>
                  <p><strong>Nivel:</strong> {latestAssessment.level || '-'}</p>
                  <p><strong>Frequencia semanal:</strong> {latestAssessment.freq_per_week ?? '-'}x</p>
                  <p><strong>Tempo por sessao:</strong> {latestAssessment.session_time_min ?? '-'} min</p>
                  <p><strong>Observacoes:</strong> {latestAssessment.case_notes || 'Sem observacoes registradas.'}</p>
                </>
              ) : (
                <p>Nenhum assessment cadastrado ainda. Complete esta etapa antes de gerar o plano.</p>
              )}
            </article>

            <article className="info-card">
              <div className="section-title-row">
              <div>
                <span className="eyebrow">Measurements mais recentes</span>
                  <h3>Dados corporais</h3>
                </div>
                <Link to={`/students/${student.id}/onboarding#measurement`} className="btn-secondary">
                  {latestMeasurement ? 'Atualizar measurements' : 'Preencher measurements'}
                </Link>
              </div>
              {latestMeasurement ? (
                <>
                  <p><strong>Peso:</strong> {latestMeasurement.weight_kg ?? '-'} kg</p>
                  <p><strong>Altura:</strong> {latestMeasurement.height_m ?? '-'} m</p>
                  <p><strong>Gordura corporal:</strong> {latestMeasurement.body_fat_percent ?? '-'}%</p>
                  <p><strong>IMC:</strong> {latestMeasurement.bmi ?? '-'}</p>
                </>
              ) : (
                <p>Nenhuma measurement cadastrada ainda. Sem isso o professor nao deve gerar plano.</p>
              )}
            </article>
          </section>
        </div>

        <aside className="sidebar-rail">
          <div className="content-stack">
          <article className="info-card">
            <span className="eyebrow">Resumo geral</span>
            <h3>Progresso do aluno</h3>
            <div className="metric-list">
              <div>
                <span>Assessments</span>
                <strong>{assessments.length}</strong>
              </div>
              <div>
                <span>Measurements</span>
                <strong>{measurements.length}</strong>
              </div>
              <div>
                <span>Planos</span>
                <strong>{plans.length}</strong>
              </div>
            </div>
          </article>

          <article className="info-card">
            <span className="eyebrow">Proximo passo</span>
            <h3>{ready ? 'Gerar plano com IA' : 'Completar cadastro'}</h3>
            <p>
              {ready
                ? 'Assessment e measurements ja existem. O workspace de geracao vai abrir com os ultimos dados selecionados.'
                : 'Use o fluxo de onboarding para preencher os dados faltantes e liberar a geracao do plano.'}
            </p>
            <div className="content-stack compact">
              <Link to={`/students/${student.id}/onboarding`} className="btn-secondary">Abrir onboarding</Link>
              <Link to={`/students/${student.id}/plan/new`} className="btn-primary">
                {ready ? 'Abrir geracao de plano' : 'Ver pendencias'}
              </Link>
            </div>
          </article>
          </div>
        </aside>
      </section>
    </div>
  )
}
