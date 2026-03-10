/** Valida CPF (dígitos verificadores) */
export function validateCPF(cpf: string): { valid: boolean; message?: string } {
  const digits = cpf.replace(/\D/g, '')
  if (digits.length !== 11) return { valid: false, message: 'CPF deve ter 11 dígitos' }
  if (/^(\d)\1+$/.test(digits)) return { valid: false, message: 'CPF inválido' }
  for (let i = 9; i < 11; i++) {
    let sum = 0
    for (let j = 0; j < i; j++) sum += parseInt(digits[j]) * (i + 1 - j)
    const dig = (sum * 10) % 11
    if ((dig === 10 ? 0 : dig) !== parseInt(digits[i])) return { valid: false, message: 'CPF inválido' }
  }
  return { valid: true }
}

/** Valida formato de email */
export function validateEmail(email: string): { valid: boolean; message?: string } {
  if (!email.trim()) return { valid: true }
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!re.test(email)) return { valid: false, message: 'Email inválido' }
  return { valid: true }
}
