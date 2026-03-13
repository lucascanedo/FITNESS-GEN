import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type { Assessment, Measurement, Student } from '../types'
import { formatDateBR, formatDateInput, formatPhone, parseDateBRToISO } from '../utils/formatters'
import { validateEmail } from '../utils/validators'
import {
  getLatestAssessment,
  getLatestMeasurement,
  getStatusMessage,
  getStatusTone,
  getStudentSetupStatus,
  isStudentReadyForPlan,
} from '../utils/studentFlow'

type FormState = {
  level: string
  freqPerWeek: string
  sessionTimeMin: string
  goal: string
  restrictions: string
  history: string
  caseNotes: string
  splitPreference: string
  preferredDays: string[]
}

type MeasurementFormState = {
  heightM: string
  weightKg: string
  bodyFatPercent: string
  muscleMassKg: string
  source: string
  notes: string
}

type StudentFormState = {
  name: string
  birthDate: string
  sex: string
  email: string
  phone: string
}

const weekdayOptions = ['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']

const defaultAssessmentForm: FormState = {
  level: '',
  freqPerWeek: '',
  sessionTimeMin: '',
  goal: '',
  restrictions: '',
  history: '',
  caseNotes: '',
  splitPreference: '',
  preferredDays: [],
}

const defaultMeasurementForm: MeasurementFormState = {
  heightM: '',
  weightKg: '',
  bodyFatPercent: '',
  muscleMassKg: '',
  source: 'avaliacao inicial',
  notes: '',
}

const defaultStudentForm: StudentFormState = {
  name: '',
  birthDate: '',
  sex: '',
  email: '',
  phone: '',
}

function readJsonText(value: unknown, key = 'notes') {
  if (!value || typeof value !== 'object') return ''
  const record = value as Record<string, unknown>
  const text = record[key]
  return typeof text === 'string' ? text : ''
}

function readJsonArray(value: unknown, key: string) {
  if (!value || typeof value !== 'object') return []
  const record = value as Record<string, unknown>
  const raw = record[key]
  return Array.isArray(raw) ? raw.filter((item): item is string => typeof item === 'string') : []
}

function hydrateAssessmentForm(assessment: Assessment | null): FormState {
  if (!assessment) return defaultAssessmentForm

  return {
    level: assessment.level || '',
    freqPerWeek: assessment.freq_per_week ? String(assessment.freq_per_week) : '',
    sessionTimeMin: assessment.session_time_min ? String(assessment.session_time_min) : '',
    goal: readJsonText(assessment.objectives, 'primary_goal'),
    restrictions: readJsonText(assessment.restrictions),
    history: readJsonText(assessment.history),
    caseNotes: assessment.case_notes || '',
    splitPreference: readJsonText(assessment.periodization, 'split_preference'),
    preferredDays: readJsonArray(assessment.periodization, 'preferred_days'),
  }
}

function hydrateMeasurementForm(measurement: Measurement | null): MeasurementFormState {
  if (!measurement) return defaultMeasurementForm

  return {
    heightM: measurement.height_m ? String(measurement.height_m) : '',
    weightKg: measurement.weight_kg ? String(measurement.weight_kg) : '',
    bodyFatPercent: measurement.body_fat_percent ? String(measurement.body_fat_percent) : '',
    muscleMassKg: measurement.muscle_mass_kg ? String(measurement.muscle_mass_kg) : '',
    source: measurement.source || 'avaliacao inicial',
    notes: measurement.notes || '',
  }
}

export function StudentOnboarding() {
  const { studentId } = useParams<{ studentId: string }>()
  const navigate = useNavigate()
  const [student, setStudent] = useState<Student | null>(null)
  const [assessments, setAssessments] = useState<Assessment[]>([])
  const [measurements, setMeasurements] = useState<Measurement[]>([])
  const [studentForm, setStudentForm] = useState<StudentFormState>(defaultStudentForm)
  const [assessmentForm, setAssessmentForm] = useState<FormState>(defaultAssessmentForm)
  const [measurementForm, setMeasurementForm] = useState<MeasurementFormState>(defaultMeasurementForm)
  const [assessmentDraftId, setAssessmentDraftId] = useState<number | 'new'>('new')
  const [measurementDraftId, setMeasurementDraftId] = useState<number | 'new'>('new')
  const [loading, setLoading] = useState(true)
  const [savingAssessment, setSavingAssessment] = useState(false)
  const [savingMeasurement, setSavingMeasurement] = useState(false)
  const [savingStudent, setSavingStudent] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [studentErrors, setStudentErrors] = useState<Record<string, string>>({})
  const [assessmentErrors, setAssessmentErrors] = useState<Record<string, string>>({})
  const [measurementErrors, setMeasurementErrors] = useState<Record<string, string>>({})

  const id = Number(studentId)

  const syncForms = (nextAssessments: Assessment[], nextMeasurements: Measurement[]) => {
    const latestAssessment = getLatestAssessment(nextAssessments)
    const latestMeasurement = getLatestMeasurement(nextMeasurements)
    setAssessmentDraftId(latestAssessment?.id ?? 'new')
    setMeasurementDraftId(latestMeasurement?.id ?? 'new')
    setAssessmentForm(hydrateAssessmentForm(latestAssessment))
    setMeasurementForm(hydrateMeasurementForm(latestMeasurement))
  }

  useEffect(() => {
    if (!id) return

    Promise.all([
      api.students.get(id),
      api.assessments.list(id),
      api.measurements.list(id),
    ])
      .then(([studentResult, assessmentsResult, measurementsResult]) => {
        setStudent(studentResult)
        setStudentForm({
          name: studentResult.name,
          birthDate: formatDateBR(studentResult.birth_date),
          sex: studentResult.sex || '',
          email: studentResult.email || '',
          phone: formatPhone(studentResult.phone || ''),
        })
        setAssessments(assessmentsResult)
        setMeasurements(measurementsResult)
        syncForms(assessmentsResult, measurementsResult)
      })
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false))
  }, [id])

  const reloadData = async () => {
    const [assessmentsResult, measurementsResult] = await Promise.all([
      api.assessments.list(id),
      api.measurements.list(id),
    ])
    setAssessments(assessmentsResult)
    setMeasurements(measurementsResult)
    syncForms(assessmentsResult, measurementsResult)
  }

  const validateAssessment = () => {
    const nextErrors: Record<string, string> = {}
    if (!assessmentForm.level) nextErrors.level = 'Selecione o nivel do aluno.'
    if (!assessmentForm.freqPerWeek) nextErrors.freqPerWeek = 'Informe a frequencia semanal.'
    if (!assessmentForm.sessionTimeMin) nextErrors.sessionTimeMin = 'Informe o tempo por sessao.'
    if (!assessmentForm.goal.trim()) nextErrors.goal = 'Informe o objetivo principal.'
    if (assessmentForm.preferredDays.length === 0) nextErrors.preferredDays = 'Selecione os dias disponiveis para treino.'
    setAssessmentErrors(nextErrors)
    return Object.keys(nextErrors).length === 0
  }

  const validateStudent = () => {
    const nextErrors: Record<string, string> = {}
    if (!studentForm.name.trim()) nextErrors.name = 'Informe o nome completo.'
    const birthIso = parseDateBRToISO(studentForm.birthDate)
    if (!birthIso || studentForm.birthDate.replace(/\D/g, '').length !== 8) {
      nextErrors.birthDate = 'Informe uma data de nascimento valida.'
    }
    const emailResult = validateEmail(studentForm.email)
    if (!emailResult.valid) nextErrors.email = emailResult.message || 'Email invalido.'
    setStudentErrors(nextErrors)
    return Object.keys(nextErrors).length === 0
  }

  const validateMeasurement = () => {
    const nextErrors: Record<string, string> = {}
    if (!measurementForm.heightM) nextErrors.heightM = 'Informe a altura.'
    if (!measurementForm.weightKg) nextErrors.weightKg = 'Informe o peso.'
    setMeasurementErrors(nextErrors)
    return Object.keys(nextErrors).length === 0
  }

  const handleAssessmentRecordChange = (value: string) => {
    if (value === 'new') {
      setAssessmentDraftId('new')
      setAssessmentForm(defaultAssessmentForm)
      setAssessmentErrors({})
      return
    }

    const selected = assessments.find((assessment) => assessment.id === Number(value)) ?? null
    setAssessmentDraftId(selected?.id ?? 'new')
    setAssessmentForm(hydrateAssessmentForm(selected))
    setAssessmentErrors({})
  }

  const handleMeasurementRecordChange = (value: string) => {
    if (value === 'new') {
      setMeasurementDraftId('new')
      setMeasurementForm(defaultMeasurementForm)
      setMeasurementErrors({})
      return
    }

    const selected = measurements.find((measurement) => measurement.id === Number(value)) ?? null
    setMeasurementDraftId(selected?.id ?? 'new')
    setMeasurementForm(hydrateMeasurementForm(selected))
    setMeasurementErrors({})
  }

  const handleAssessmentSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    setSuccess(null)
    if (!validateAssessment()) return
    setSavingAssessment(true)

    const payload = {
      student_id: id,
      level: assessmentForm.level,
      freq_per_week: Number(assessmentForm.freqPerWeek),
      session_time_min: Number(assessmentForm.sessionTimeMin),
      objectives: { primary_goal: assessmentForm.goal.trim() },
      restrictions: assessmentForm.restrictions ? { notes: assessmentForm.restrictions.trim() } : undefined,
      history: assessmentForm.history ? { notes: assessmentForm.history.trim() } : undefined,
      case_notes: assessmentForm.caseNotes.trim() || undefined,
      periodization: {
        preferred_days: assessmentForm.preferredDays,
        split_preference: assessmentForm.splitPreference || 'auto',
      },
      status: 'completed',
    }

    try {
      if (assessmentDraftId === 'new') {
        await api.assessments.create(payload)
        setSuccess('Assessment registrado com sucesso.')
      } else {
        await api.assessments.update(assessmentDraftId, payload)
        setSuccess('Assessment atualizado com sucesso.')
      }
      await reloadData()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Nao foi possivel salvar o assessment.')
    } finally {
      setSavingAssessment(false)
    }
  }

  const handleMeasurementSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    setSuccess(null)
    if (!validateMeasurement()) return
    setSavingMeasurement(true)

    const payload = {
      student_id: id,
      height_m: Number(measurementForm.heightM),
      weight_kg: Number(measurementForm.weightKg),
      body_fat_percent: measurementForm.bodyFatPercent ? Number(measurementForm.bodyFatPercent) : undefined,
      muscle_mass_kg: measurementForm.muscleMassKg ? Number(measurementForm.muscleMassKg) : undefined,
      source: measurementForm.source.trim() || undefined,
      notes: measurementForm.notes.trim() || undefined,
    }

    try {
      if (measurementDraftId === 'new') {
        await api.measurements.create(payload)
        setSuccess('Measurements registradas com sucesso.')
      } else {
        await api.measurements.update(measurementDraftId, payload)
        setSuccess('Measurements atualizadas com sucesso.')
      }
      await reloadData()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Nao foi possivel salvar as measurements.')
    } finally {
      setSavingMeasurement(false)
    }
  }

  const handleStudentSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    setSuccess(null)
    if (!validateStudent()) return
    setSavingStudent(true)

    try {
      const birthIso = parseDateBRToISO(studentForm.birthDate)
      const updatedStudent = await api.students.update(id, {
        name: studentForm.name.trim(),
        birth_date: birthIso,
        sex: studentForm.sex || undefined,
        email: studentForm.email.trim() || undefined,
        phone: studentForm.phone.replace(/\D/g, '') || undefined,
      })
      setStudent(updatedStudent)
      setStudentForm({
        name: updatedStudent.name,
        birthDate: formatDateBR(updatedStudent.birth_date),
        sex: updatedStudent.sex || '',
        email: updatedStudent.email || '',
        phone: formatPhone(updatedStudent.phone || ''),
      })
      setSuccess('Dados do aluno atualizados com sucesso.')
      setStudentErrors({})
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Nao foi possivel atualizar os dados do aluno.')
    } finally {
      setSavingStudent(false)
    }
  }

  if (loading) return <p className="status-text">Carregando cadastro do aluno...</p>
  if (error || !student) return <p className="status-text error">Erro: {error || 'Aluno nao encontrado'}</p>

  const latestAssessment = getLatestAssessment(assessments)
  const latestMeasurement = getLatestMeasurement(measurements)
  const status = getStudentSetupStatus(assessments, measurements)
  const ready = isStudentReadyForPlan(assessments, measurements)
  const tone = getStatusTone(status)

  return (
    <div className="content-stack onboarding-page">
      <section className="page-heading-card compact-hero">
        <div>
          <div className="breadcrumb">
            <Link to="/dashboard">Painel</Link>
            <span>/</span>
            <Link to="/students">Alunos</Link>
            <span>/</span>
            <Link to={`/students/${student.id}`}>{student.name}</Link>
            <span>/</span>
            <strong>Cadastro complementar</strong>
          </div>
          <span className="eyebrow">Cadastro complementar</span>
          <h1>{student.name}</h1>
          <p>{getStatusMessage(status)}</p>
        </div>

        <div className={`status-banner ${tone}`}>
          <span className="status-banner-label">Status atual</span>
          <strong>{status}</strong>
          <button
            type="button"
            className="btn-primary"
            disabled={!ready}
            onClick={() => navigate(`/students/${student.id}/plan/new`)}
          >
            {ready ? 'Prosseguir para o plano' : 'Plano indisponivel'}
          </button>
        </div>
      </section>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <section className="onboarding-layout">
        <div className="content-stack relaxed">
          <section id="basic" className="form-card">
            <div className="section-title-row">
              <div>
                <span className="eyebrow">Dados do aluno</span>
                <h3>Informacoes basicas</h3>
              </div>
            </div>

            <form onSubmit={handleStudentSubmit}>
              <div className="form-row">
                <div className="field">
                  <label htmlFor="student-name">Nome completo</label>
                  <input
                    id="student-name"
                    value={studentForm.name}
                    onChange={(event) => {
                      setStudentForm((current) => ({ ...current, name: event.target.value }))
                      setStudentErrors((current) => ({ ...current, name: '' }))
                    }}
                    className={studentErrors.name ? 'invalid' : ''}
                  />
                  {studentErrors.name && <span className="field-error">{studentErrors.name}</span>}
                </div>
                <div className="field">
                  <label htmlFor="student-birth-date">Data de nascimento</label>
                  <input
                    id="student-birth-date"
                    value={studentForm.birthDate}
                    onChange={(event) => {
                      setStudentForm((current) => ({ ...current, birthDate: formatDateInput(event.target.value) }))
                      setStudentErrors((current) => ({ ...current, birthDate: '' }))
                    }}
                    placeholder="dd/mm/aaaa"
                    className={studentErrors.birthDate ? 'invalid' : ''}
                  />
                  {studentErrors.birthDate && <span className="field-error">{studentErrors.birthDate}</span>}
                </div>
              </div>

              <div className="form-row">
                <div className="field">
                  <label htmlFor="student-email">Email</label>
                  <input
                    id="student-email"
                    type="email"
                    value={studentForm.email}
                    onChange={(event) => {
                      setStudentForm((current) => ({ ...current, email: event.target.value }))
                      setStudentErrors((current) => ({ ...current, email: '' }))
                    }}
                    className={studentErrors.email ? 'invalid' : ''}
                  />
                  {studentErrors.email && <span className="field-error">{studentErrors.email}</span>}
                </div>
                <div className="field">
                  <label htmlFor="student-phone">Telefone</label>
                  <input
                    id="student-phone"
                    value={studentForm.phone}
                    onChange={(event) => setStudentForm((current) => ({ ...current, phone: formatPhone(event.target.value) }))}
                    placeholder="(00) 00000-0000"
                  />
                </div>
              </div>

              <div className="field">
                <label htmlFor="student-sex">Sexo</label>
                <select
                  id="student-sex"
                  value={studentForm.sex}
                  onChange={(event) => setStudentForm((current) => ({ ...current, sex: event.target.value }))}
                >
                  <option value="">Selecione</option>
                  <option value="M">Masculino</option>
                  <option value="F">Feminino</option>
                </select>
              </div>

              <div className="form-actions">
                <button type="submit" className="btn-primary" disabled={savingStudent}>
                  {savingStudent ? 'Salvando...' : 'Salvar dados do aluno'}
                </button>
              </div>
            </form>
          </section>

          <section id="assessment" className="form-card">
            <div className="section-title-row">
              <div>
                <span className="eyebrow">Assessment</span>
                <h3>Avaliacao de treino</h3>
              </div>
              <div className="section-actions">
                <select
                  value={assessmentDraftId}
                  onChange={(event) => handleAssessmentRecordChange(event.target.value)}
                  className="compact-select"
                >
                  {assessments.map((assessment) => (
                    <option key={assessment.id} value={assessment.id}>
                      Assessment #{assessment.id} {assessment.id === latestAssessment?.id ? '• atual' : ''}
                    </option>
                  ))}
                  <option value="new">Novo assessment</option>
                </select>
                <button type="button" className="btn-secondary" onClick={() => handleAssessmentRecordChange('new')}>
                  Novo registro
                </button>
              </div>
            </div>

            <form onSubmit={handleAssessmentSubmit}>
              <div className="form-row">
                <div className="field">
                  <label htmlFor="level">Nivel</label>
                  <select
                    id="level"
                    value={assessmentForm.level}
                    onChange={(event) => {
                      setAssessmentForm((current) => ({ ...current, level: event.target.value }))
                      setAssessmentErrors((current) => ({ ...current, level: '' }))
                    }}
                    className={assessmentErrors.level ? 'invalid' : ''}
                  >
                    <option value="">Selecione</option>
                    <option value="iniciante">Iniciante</option>
                    <option value="intermediario">Intermediario</option>
                    <option value="avancado">Avancado</option>
                  </select>
                  {assessmentErrors.level && <span className="field-error">{assessmentErrors.level}</span>}
                </div>

                <div className="field">
                  <label htmlFor="goal">Objetivo principal</label>
                  <input
                    id="goal"
                    value={assessmentForm.goal}
                    onChange={(event) => {
                      setAssessmentForm((current) => ({ ...current, goal: event.target.value }))
                      setAssessmentErrors((current) => ({ ...current, goal: '' }))
                    }}
                    placeholder="Ex.: hipertrofia, recomposicao corporal ou condicionamento."
                    className={assessmentErrors.goal ? 'invalid' : ''}
                  />
                  {assessmentErrors.goal && <span className="field-error">{assessmentErrors.goal}</span>}
                </div>
              </div>

              <div className="form-row">
                <div className="field">
                  <label htmlFor="freq">Frequencia semanal</label>
                  <input
                    id="freq"
                    type="number"
                    min="1"
                    max="7"
                    value={assessmentForm.freqPerWeek}
                    onChange={(event) => {
                      setAssessmentForm((current) => ({ ...current, freqPerWeek: event.target.value }))
                      setAssessmentErrors((current) => ({ ...current, freqPerWeek: '' }))
                    }}
                    placeholder="3"
                    className={assessmentErrors.freqPerWeek ? 'invalid' : ''}
                  />
                  {assessmentErrors.freqPerWeek && <span className="field-error">{assessmentErrors.freqPerWeek}</span>}
                </div>

                <div className="field">
                  <label htmlFor="session">Duracao por sessao (min)</label>
                  <input
                    id="session"
                    type="number"
                    min="20"
                    max="180"
                    value={assessmentForm.sessionTimeMin}
                    onChange={(event) => {
                      setAssessmentForm((current) => ({ ...current, sessionTimeMin: event.target.value }))
                      setAssessmentErrors((current) => ({ ...current, sessionTimeMin: '' }))
                    }}
                    placeholder="60"
                    className={assessmentErrors.sessionTimeMin ? 'invalid' : ''}
                  />
                  {assessmentErrors.sessionTimeMin && <span className="field-error">{assessmentErrors.sessionTimeMin}</span>}
                </div>
              </div>

              <div className="form-row">
                <div className="field">
                  <label htmlFor="split-preference">Estrutura preferencial</label>
                  <select
                    id="split-preference"
                    value={assessmentForm.splitPreference}
                    onChange={(event) => setAssessmentForm((current) => ({ ...current, splitPreference: event.target.value }))}
                  >
                    <option value="">Definir automaticamente</option>
                    <option value="3 treinos">3 treinos</option>
                    <option value="ABC">ABC</option>
                    <option value="PPL">PPL</option>
                    <option value="Upper/Lower">Upper/Lower</option>
                    <option value="Full Body">Full Body</option>
                  </select>
                </div>
                <div className="field">
                  <label>Dias disponiveis para treino</label>
                  <div className="day-chip-group">
                    {weekdayOptions.map((day) => {
                      const active = assessmentForm.preferredDays.includes(day)
                      return (
                        <button
                          key={day}
                          type="button"
                          className={active ? 'day-chip active' : 'day-chip'}
                          onClick={() => {
                            setAssessmentForm((current) => ({
                              ...current,
                              preferredDays: active
                                ? current.preferredDays.filter((item) => item !== day)
                                : [...current.preferredDays, day],
                            }))
                            setAssessmentErrors((current) => ({ ...current, preferredDays: '' }))
                          }}
                        >
                          {day}
                        </button>
                      )
                    })}
                  </div>
                  {assessmentErrors.preferredDays && <span className="field-error">{assessmentErrors.preferredDays}</span>}
                </div>
              </div>

              <div className="field">
                <label htmlFor="restrictions">Restricoes relevantes</label>
                <textarea
                  id="restrictions"
                  value={assessmentForm.restrictions}
                  onChange={(event) => setAssessmentForm((current) => ({ ...current, restrictions: event.target.value }))}
                  placeholder="Informe limitacoes, desconfortos ou cuidados importantes."
                  rows={3}
                />
              </div>

              <div className="field">
                <label htmlFor="history">Historico e contexto</label>
                <textarea
                  id="history"
                  value={assessmentForm.history}
                  onChange={(event) => setAssessmentForm((current) => ({ ...current, history: event.target.value }))}
                  placeholder="Descreva experiencia anterior, rotina e aderencia."
                  rows={3}
                />
              </div>

              <div className="field">
                <label htmlFor="case-notes">Observacoes do professor</label>
                <textarea
                  id="case-notes"
                  value={assessmentForm.caseNotes}
                  onChange={(event) => setAssessmentForm((current) => ({ ...current, caseNotes: event.target.value }))}
                  placeholder="Registre informacoes relevantes para a geracao do plano."
                  rows={3}
                />
              </div>

              <div className="form-actions">
                <button type="submit" className="btn-primary" disabled={savingAssessment}>
                  {savingAssessment
                    ? 'Salvando...'
                    : assessmentDraftId === 'new'
                      ? 'Salvar assessment'
                      : 'Atualizar assessment'}
                </button>
              </div>
            </form>
          </section>

          <section id="measurement" className="form-card">
            <div className="section-title-row">
              <div>
                <span className="eyebrow">Measurements</span>
                <h3>Medidas corporais</h3>
              </div>
              <div className="section-actions">
                <select
                  value={measurementDraftId}
                  onChange={(event) => handleMeasurementRecordChange(event.target.value)}
                  className="compact-select"
                >
                  {measurements.map((measurement) => (
                    <option key={measurement.id} value={measurement.id}>
                      Measurement #{measurement.id} {measurement.id === latestMeasurement?.id ? '• atual' : ''}
                    </option>
                  ))}
                  <option value="new">Nova measurement</option>
                </select>
                <button type="button" className="btn-secondary" onClick={() => handleMeasurementRecordChange('new')}>
                  Novo registro
                </button>
              </div>
            </div>

            <form onSubmit={handleMeasurementSubmit}>
              <div className="form-row">
                <div className="field">
                  <label htmlFor="height">Altura (m)</label>
                  <input
                    id="height"
                    type="number"
                    step="0.01"
                    min="1"
                    value={measurementForm.heightM}
                    onChange={(event) => {
                      setMeasurementForm((current) => ({ ...current, heightM: event.target.value }))
                      setMeasurementErrors((current) => ({ ...current, heightM: '' }))
                    }}
                    placeholder="1.75"
                    className={measurementErrors.heightM ? 'invalid' : ''}
                  />
                  {measurementErrors.heightM && <span className="field-error">{measurementErrors.heightM}</span>}
                </div>

                <div className="field">
                  <label htmlFor="weight">Peso (kg)</label>
                  <input
                    id="weight"
                    type="number"
                    step="0.1"
                    min="1"
                    value={measurementForm.weightKg}
                    onChange={(event) => {
                      setMeasurementForm((current) => ({ ...current, weightKg: event.target.value }))
                      setMeasurementErrors((current) => ({ ...current, weightKg: '' }))
                    }}
                    placeholder="82.4"
                    className={measurementErrors.weightKg ? 'invalid' : ''}
                  />
                  {measurementErrors.weightKg && <span className="field-error">{measurementErrors.weightKg}</span>}
                </div>
              </div>

              <div className="form-row">
                <div className="field">
                  <label htmlFor="fat">Gordura corporal (%)</label>
                  <input
                    id="fat"
                    type="number"
                    step="0.1"
                    min="0"
                    value={measurementForm.bodyFatPercent}
                    onChange={(event) => setMeasurementForm((current) => ({ ...current, bodyFatPercent: event.target.value }))}
                    placeholder="18.2"
                  />
                </div>

                <div className="field">
                  <label htmlFor="muscle">Massa muscular (kg)</label>
                  <input
                    id="muscle"
                    type="number"
                    step="0.1"
                    min="0"
                    value={measurementForm.muscleMassKg}
                    onChange={(event) => setMeasurementForm((current) => ({ ...current, muscleMassKg: event.target.value }))}
                    placeholder="36.5"
                  />
                </div>
              </div>

              <div className="field">
                <label htmlFor="source">Origem da medicao</label>
                <input
                  id="source"
                  value={measurementForm.source}
                  onChange={(event) => setMeasurementForm((current) => ({ ...current, source: event.target.value }))}
                  placeholder="Ex.: avaliacao inicial, bioimpedancia ou balanca."
                />
              </div>

              <div className="field">
                <label htmlFor="measurement-notes">Observacoes</label>
                <textarea
                  id="measurement-notes"
                  value={measurementForm.notes}
                  onChange={(event) => setMeasurementForm((current) => ({ ...current, notes: event.target.value }))}
                  placeholder="Inclua somente observacoes relevantes."
                  rows={3}
                />
              </div>

              <div className="form-actions">
                <button type="submit" className="btn-primary" disabled={savingMeasurement}>
                  {savingMeasurement
                    ? 'Salvando...'
                    : measurementDraftId === 'new'
                      ? 'Salvar measurements'
                      : 'Atualizar measurements'}
                </button>
              </div>
            </form>
          </section>
        </div>

        <aside className="sidebar-rail">
          <div className="content-stack relaxed">
            <section className="info-card">
              <span className="eyebrow">Resumo do aluno</span>
              <h3>{student.name}</h3>
              <p>{student.age} anos • {student.email || 'Email nao informado'}</p>
              <div className="metric-list">
                <div>
                  <span>Assessment</span>
                  <strong>{latestAssessment ? 'Atualizado' : 'Pendente'}</strong>
                </div>
                <div>
                  <span>Measurements</span>
                  <strong>{latestMeasurement ? 'Atualizadas' : 'Pendentes'}</strong>
                </div>
              </div>
            </section>

            <section className={`info-card status-card ${tone}`}>
              <span className="eyebrow">Status do cadastro</span>
              <h3>{status}</h3>
              <p>{getStatusMessage(status)}</p>
            </section>
          </div>
        </aside>
      </section>
    </div>
  )
}
