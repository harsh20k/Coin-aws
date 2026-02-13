import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Budget, Subcategory, BudgetCreate } from '../api/types'
import { formatCents, formatDate } from '../utils/format'
import './Page.css'

export function Budgets() {
  const [list, setList] = useState<Budget[]>([])
  const [subcategories, setSubcategories] = useState<Subcategory[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState<BudgetCreate>({
    subcategory_id: '',
    limit_cents: 0,
    period_start: '',
    period_end: '',
  })

  async function loadSubcategories() {
    const data = await api.get<Subcategory[]>('/subcategories?type=expense')
    setSubcategories(data)
  }

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const data = await api.get<Budget[]>('/budgets')
      setList(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSubcategories().catch(() => {})
    load()
  }, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!form.subcategory_id || form.limit_cents <= 0 || !form.period_start || !form.period_end) return
    try {
      await api.post('/budgets', {
        ...form,
        limit_cents: Math.round(form.limit_cents),
      })
      setForm({ subcategory_id: '', limit_cents: 0, period_start: '', period_end: '' })
      load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Create failed')
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Delete this budget?')) return
    try {
      await api.delete(`/budgets/${id}`)
      load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed')
    }
  }

  const subByName: Record<string, string> = {}
  subcategories.forEach((s) => { subByName[s.id] = s.name })

  if (loading && list.length === 0) return <p className="page-loading">Loading…</p>
  return (
    <div className="page">
      <h2>Budgets</h2>
      {error && <p className="page-error">{error} <button type="button" onClick={load}>Retry</button></p>}
      <form onSubmit={handleCreate} className="page-form">
        <select
          value={form.subcategory_id}
          onChange={(e) => setForm((f) => ({ ...f, subcategory_id: e.target.value }))}
          required
        >
          <option value="">Subcategory</option>
          {subcategories.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
        <input
          type="number"
          step="0.01"
          placeholder="Limit ($)"
          value={form.limit_cents ? form.limit_cents / 100 : ''}
          onChange={(e) => setForm((f) => ({ ...f, limit_cents: Math.round(parseFloat(e.target.value || '0') * 100) }))}
        />
        <input
          type="date"
          value={form.period_start}
          onChange={(e) => setForm((f) => ({ ...f, period_start: e.target.value }))}
          required
        />
        <input
          type="date"
          value={form.period_end}
          onChange={(e) => setForm((f) => ({ ...f, period_end: e.target.value }))}
          required
        />
        <button type="submit">Add budget</button>
      </form>
      <ul className="page-list">
        {list.map((b) => (
          <li key={b.id} className="page-list-item">
            <span>{subByName[b.subcategory_id] ?? b.subcategory_id}</span>
            <span>{formatCents(b.limit_cents)}</span>
            <span>{formatDate(b.period_start)} – {formatDate(b.period_end)}</span>
            <button type="button" onClick={() => handleDelete(b.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  )
}
