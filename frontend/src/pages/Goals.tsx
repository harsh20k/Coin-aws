import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Goal, GoalCreate } from '../api/types'
import { formatCents, formatDate } from '../utils/format'
import './Page.css'

export function Goals() {
  const [list, setList] = useState<Goal[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState<GoalCreate>({
    title: '',
    target_cents: 0,
    goal_type: 'investment',
    period_start: '',
    period_end: '',
  })

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const data = await api.get<Goal[]>('/goals')
      setList(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!form.title.trim() || form.target_cents <= 0 || !form.period_start || !form.period_end) return
    try {
      await api.post('/goals', {
        ...form,
        target_cents: Math.round(form.target_cents),
      })
      setForm({ title: '', target_cents: 0, goal_type: 'investment', period_start: '', period_end: '' })
      load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Create failed')
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Delete this goal?')) return
    try {
      await api.delete(`/goals/${id}`)
      load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed')
    }
  }

  if (loading && list.length === 0) return <p className="page-loading">Loading…</p>
  return (
    <div className="page">
      <h2>Goals</h2>
      {error && <p className="page-error">{error} <button type="button" onClick={load}>Retry</button></p>}
      <form onSubmit={handleCreate} className="page-form">
        <input
          value={form.title}
          onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
          placeholder="Title"
          required
        />
        <input
          type="number"
          step="0.01"
          placeholder="Target ($)"
          value={form.target_cents ? form.target_cents / 100 : ''}
          onChange={(e) => setForm((f) => ({ ...f, target_cents: Math.round(parseFloat(e.target.value || '0') * 100) }))}
        />
        <select
          value={form.goal_type}
          onChange={(e) => setForm((f) => ({ ...f, goal_type: e.target.value as Goal['goal_type'] }))}
        >
          <option value="income">Income</option>
          <option value="expense">Expense</option>
          <option value="investment">Investment</option>
          <option value="donation">Donation</option>
        </select>
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
        <button type="submit">Add goal</button>
      </form>
      <ul className="page-list">
        {list.map((g) => (
          <li key={g.id} className="page-list-item">
            <span>{g.title}</span>
            <span>{formatCents(g.target_cents)}</span>
            <span>{g.goal_type}</span>
            <span>{formatDate(g.period_start)} – {formatDate(g.period_end)}</span>
            <button type="button" onClick={() => handleDelete(g.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  )
}
