export interface Student {
  id: number
  cpf: string
  name: string
  birth_date: string
  age: number
  sex?: string
  email?: string
  phone?: string
  created_at: string
}

export interface Assessment {
  id: number
  student_id: number
  measurement_id?: number
  objectives?: Record<string, unknown>
  posture?: Record<string, unknown>
  injuries?: Record<string, unknown>
  restrictions?: Record<string, unknown>
  history?: Record<string, unknown>
  level?: string
  freq_per_week?: number
  session_time_min?: number
  case_notes?: string
  equipment?: Record<string, unknown>
  red_flags?: Record<string, unknown>
  readiness?: Record<string, unknown>
  periodization?: Record<string, unknown>
  status?: string
  created_at: string
}

export interface Measurement {
  id: number
  student_id: number
  measured_at: string
  height_m?: number
  weight_kg?: number
  body_fat_percent?: number
  muscle_mass_kg?: number
  bmi?: number
  source?: string
  notes?: string
  created_at: string
}

export interface PlanMeta {
  split: string
  goal: string
  periodization: Record<string, unknown>
  constraints: Record<string, unknown>
  version: number
  status: 'draft' | 'active' | 'archived'
}

export interface PlanItem {
  week: number
  day: string
  exercise_name: string
  block: string
  sets: number
  reps: string
  rest_s: number
  tempo: string
  exercise_code?: string
  rpe?: number
  load_pct_1rm?: number
  equipment?: string
  focus?: string
  cues?: string
  regression?: string
  progression?: string
  contraindications?: string[]
  notes?: string
}

export interface PlanBody {
  plan_meta: PlanMeta
  items: PlanItem[]
}

export interface Plan {
  id: number
  student_id: number
  assessment_id: number
  measurement_id?: number
  generated_plan_json?: PlanBody
  plan_json: PlanBody
  llm_call_id?: number
  edit_count: number
  created_at: string
  updated_at?: string
}

export interface PlanGenerationResponse {
  plan: PlanBody
  llm_call_id?: number
}
