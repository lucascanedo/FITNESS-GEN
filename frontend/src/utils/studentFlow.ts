import type { Assessment, Measurement } from '../types'

export type StudentSetupStatus =
  | 'Cadastro incompleto'
  | 'Assessment faltando'
  | 'Measurements faltando'
  | 'Pronto para gerar plano'

export function getLatestAssessment(assessments: Assessment[]): Assessment | null {
  if (assessments.length === 0) return null
  return [...assessments].sort((a, b) => b.created_at.localeCompare(a.created_at))[0]
}

export function getLatestMeasurement(measurements: Measurement[]): Measurement | null {
  if (measurements.length === 0) return null
  return [...measurements].sort((a, b) => {
    const aDate = new Date(a.measured_at || a.created_at).getTime()
    const bDate = new Date(b.measured_at || b.created_at).getTime()
    return bDate - aDate
  })[0]
}

export function getStudentSetupStatus(
  assessments: Assessment[],
  measurements: Measurement[],
): StudentSetupStatus {
  const hasAssessment = assessments.length > 0
  const hasMeasurement = measurements.length > 0

  if (!hasAssessment && !hasMeasurement) return 'Cadastro incompleto'
  if (!hasAssessment) return 'Assessment faltando'
  if (!hasMeasurement) return 'Measurements faltando'
  return 'Pronto para gerar plano'
}

export function isStudentReadyForPlan(
  assessments: Assessment[],
  measurements: Measurement[],
): boolean {
  return assessments.length > 0 && measurements.length > 0
}

export function getStatusTone(status: StudentSetupStatus): 'neutral' | 'warning' | 'success' {
  if (status === 'Pronto para gerar plano') return 'success'
  if (status === 'Cadastro incompleto') return 'neutral'
  return 'warning'
}

export function getStatusMessage(status: StudentSetupStatus): string {
  switch (status) {
    case 'Cadastro incompleto':
      return 'Este aluno ainda precisa de assessment e measurements para entrar no fluxo de geracao.'
    case 'Assessment faltando':
      return 'Registre o assessment mais recente para liberar a geracao do plano com contexto real.'
    case 'Measurements faltando':
      return 'Registre as measurements do aluno para evitar plano com dados corporais vazios.'
    case 'Pronto para gerar plano':
      return 'Os dados minimos existem. O professor ja pode gerar o plano com IA com seguranca.'
  }
}
