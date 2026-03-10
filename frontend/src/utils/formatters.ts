/** Formata CPF: 000.000.000-00 */
export function formatCPF(value: string): string {
  const digits = value.replace(/\D/g, '').slice(0, 11)
  if (digits.length <= 3) return digits
  if (digits.length <= 6) return `${digits.slice(0, 3)}.${digits.slice(3)}`
  if (digits.length <= 9) return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6)}`
  return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9)}`
}

/** Retorna apenas dígitos do CPF */
export function digitsOnlyCPF(value: string): string {
  return value.replace(/\D/g, '')
}

/** Formata telefone: (11) 99999-9999 ou (11) 9999-9999 */
export function formatPhone(value: string): string {
  const digits = value.replace(/\D/g, '').slice(0, 11)
  if (digits.length <= 2) return digits ? `(${digits}` : ''
  if (digits.length <= 6) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`
}

/** Formata data para exibição BR: dd/mm/yyyy */
export function formatDateBR(dateStr: string): string {
  if (!dateStr) return ''
  const [y, m, d] = dateStr.split('-')
  if (y && m && d) return `${d.padStart(2, '0')}/${m.padStart(2, '0')}/${y}`
  return dateStr
}

/** Converte dd/mm/yyyy para yyyy-mm-dd (API) */
export function parseDateBRToISO(dateBR: string): string {
  const cleaned = dateBR.replace(/\D/g, '')
  if (cleaned.length !== 8) return ''
  const d = cleaned.slice(0, 2)
  const m = cleaned.slice(2, 4)
  const y = cleaned.slice(4, 8)
  return `${y}-${m}-${d}`
}

/** Converte input dd/mm/yyyy para valor controlado (guarda como yyyy-mm-dd internamente) */
export function formatDateInput(value: string): string {
  const digits = value.replace(/\D/g, '').slice(0, 8)
  if (digits.length <= 2) return digits
  if (digits.length <= 4) return `${digits.slice(0, 2)}/${digits.slice(2)}`
  return `${digits.slice(0, 2)}/${digits.slice(2, 4)}/${digits.slice(4)}`
}
