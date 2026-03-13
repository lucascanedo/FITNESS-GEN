import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { formatCPF, formatPhone, formatDateInput, parseDateBRToISO, digitsOnlyCPF } from '../utils/formatters'
import { validateCPF, validateEmail } from '../utils/validators'

const EXAMPLE = {
  nome: 'Carlos',
  sobrenome: 'Silva Santos',
  cpf: '111.444.777-35',
  birthDate: '15/03/1990',
  sex: 'M' as const,
  email: 'carlos.silva@email.com',
  phone: '(11) 98765-4321',
}

export function StudentNew() {
  const [nome, setNome] = useState('')
  const [sobrenome, setSobrenome] = useState('')
  const [cpf, setCpf] = useState('')
  const [birthDate, setBirthDate] = useState('')
  const [sex, setSex] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const navigate = useNavigate()

  const fillExample = () => {
    setNome(EXAMPLE.nome)
    setSobrenome(EXAMPLE.sobrenome)
    setCpf(EXAMPLE.cpf)
    setBirthDate(EXAMPLE.birthDate)
    setSex(EXAMPLE.sex)
    setEmail(EXAMPLE.email)
    setPhone(EXAMPLE.phone)
    setErrors({})
    setSubmitError(null)
  }

  const validate = (): boolean => {
    const e: Record<string, string> = {}
    const nameFull = `${nome} ${sobrenome}`.trim()
    if (!nameFull) e.name = 'Nome e sobrenome sao obrigatorios'
    const cpfRes = validateCPF(cpf)
    if (!cpfRes.valid) e.cpf = cpfRes.message!
    const birthIso = parseDateBRToISO(birthDate)
    if (!birthIso || birthDate.replace(/\D/g, '').length !== 8) e.birthDate = 'Data invalida (dd/mm/aaaa)'
    const emailRes = validateEmail(email)
    if (!emailRes.valid) e.email = emailRes.message!
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitError(null)
    if (!validate()) return
    const birthIso = parseDateBRToISO(birthDate)
    const nameFull = `${nome} ${sobrenome}`.trim()
    setLoading(true)
    api.students.create({
      name: nameFull,
      cpf: digitsOnlyCPF(cpf),
      birth_date: birthIso,
      sex: sex || undefined,
      email: email.trim() || undefined,
      phone: phone.replace(/\D/g, '') || undefined,
    })
      .then((s) => navigate(`/students/${s.id}/onboarding`))
      .catch((err) => setSubmitError(err.message))
      .finally(() => setLoading(false))
  }

  return (
    <div className="content-stack narrow">
      <div className="section-header-card">
        <div>
          <span className="eyebrow">Cadastro</span>
          <h1>Novo aluno</h1>
          <p>Formulario base organizado para evoluir depois com assessment e measurement sem retrabalho.</p>
        </div>
        <button type="button" onClick={fillExample} className="btn-secondary">
          Preencher com exemplo
        </button>
      </div>

      {submitError && <div className="alert alert-error">{submitError}</div>}

      <form onSubmit={handleSubmit} className="form-card">
        <div className="form-row">
          <div className="field">
            <label htmlFor="nome">Nome *</label>
            <input
              id="nome"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              placeholder="Carlos"
              className={errors.name ? 'invalid' : ''}
            />
          </div>
          <div className="field">
            <label htmlFor="sobrenome">Sobrenome *</label>
            <input
              id="sobrenome"
              value={sobrenome}
              onChange={(e) => setSobrenome(e.target.value)}
              placeholder="Silva Santos"
              className={errors.name ? 'invalid' : ''}
            />
          </div>
          {errors.name && <span className="field-error" style={{ gridColumn: '1 / -1' }}>{errors.name}</span>}
        </div>

        <div className="field">
          <label htmlFor="cpf">CPF *</label>
          <input
            id="cpf"
            value={cpf}
            onChange={(e) => setCpf(formatCPF(e.target.value))}
            onBlur={() => {
              if (cpf) {
                const r = validateCPF(cpf)
                setErrors((p) => ({ ...p, cpf: r.valid ? '' : (r.message ?? '') }))
              }
            }}
            placeholder="000.000.000-00"
            maxLength={14}
            className={errors.cpf ? 'invalid' : ''}
          />
          {errors.cpf && <span className="field-error">{errors.cpf}</span>}
        </div>

        <div className="field">
          <label htmlFor="birthDate">Data de nascimento *</label>
          <input
            id="birthDate"
            value={birthDate}
            onChange={(e) => setBirthDate(formatDateInput(e.target.value))}
            placeholder="dd/mm/aaaa"
            maxLength={10}
            className={errors.birthDate ? 'invalid' : ''}
          />
          {errors.birthDate && <span className="field-error">{errors.birthDate}</span>}
        </div>

        <div className="field">
          <label htmlFor="sex">Sexo</label>
          <select id="sex" value={sex} onChange={(e) => setSex(e.target.value)}>
            <option value="">Selecione</option>
            <option value="M">Masculino</option>
            <option value="F">Feminino</option>
          </select>
        </div>

        <div className="field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onBlur={() => {
              if (email) {
                const r = validateEmail(email)
                setErrors((p) => ({ ...p, email: r.valid ? '' : (r.message ?? '') }))
              }
            }}
            placeholder="exemplo@email.com"
            className={errors.email ? 'invalid' : ''}
          />
          {errors.email && <span className="field-error">{errors.email}</span>}
        </div>

        <div className="field">
          <label htmlFor="phone">Telefone</label>
          <input
            id="phone"
            value={phone}
            onChange={(e) => setPhone(formatPhone(e.target.value))}
            placeholder="(00) 00000-0000"
            maxLength={15}
          />
        </div>

        <div className="form-actions">
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </form>
    </div>
  )
}
