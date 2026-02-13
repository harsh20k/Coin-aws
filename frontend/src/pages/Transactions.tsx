import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Transaction, Wallet, Subcategory, TransactionCreate } from '../api/types'
import { formatCents, formatDate } from '../utils/format'
import './Page.css'
import './Transactions.css'

export function Transactions() {
  const [list, setList] = useState<Transaction[]>([])
  const [wallets, setWallets] = useState<Wallet[]>([])
  const [subcategories, setSubcategories] = useState<Subcategory[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [walletId, setWalletId] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [form, setForm] = useState<TransactionCreate>({
    wallet_id: '',
    type: 'expense',
    subcategory_id: '',
    amount_cents: 0,
    description: '',
    transaction_date: new Date().toISOString().slice(0, 10),
  })

  async function loadWallets() {
    const data = await api.get<Wallet[]>('/wallets')
    setWallets(data)
  }

  async function loadSubcategories(t?: string) {
    const path = t ? `/subcategories?type=${t}` : '/subcategories'
    const data = await api.get<Subcategory[]>(path)
    setSubcategories(data)
  }

  async function loadTransactions() {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (walletId) params.set('wallet_id', walletId)
      if (typeFilter) params.set('type', typeFilter)
      if (dateFrom) params.set('date_from', dateFrom)
      if (dateTo) params.set('date_to', dateTo)
      const path = params.toString() ? `/transactions?${params}` : '/transactions'
      const data = await api.get<Transaction[]>(path)
      setList(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadWallets().catch(() => {})
  }, [])

  useEffect(() => {
    loadSubcategories(form.type).catch(() => {})
  }, [form.type])

  useEffect(() => {
    loadTransactions()
  }, [walletId, typeFilter, dateFrom, dateTo])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!form.wallet_id || !form.subcategory_id || form.amount_cents <= 0) return
    try {
      await api.post('/transactions', {
        ...form,
        amount_cents: Math.round(form.amount_cents),
        tags: form.tags ?? [],
      })
      setForm((f) => ({ ...f, amount_cents: 0, description: '' }))
      loadTransactions()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Create failed')
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Delete this transaction?')) return
    try {
      await api.delete(`/transactions/${id}`)
      loadTransactions()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed')
    }
  }

  const subsForType = subcategories.filter((s) => s.transaction_type === form.type)

  return (
    <div className="page">
      <h2>Transactions</h2>
      {error && <p className="page-error">{error} <button type="button" onClick={() => loadTransactions()}>Retry</button></p>}
      <div className="transactions-filters">
        <select value={walletId} onChange={(e) => setWalletId(e.target.value)}>
          <option value="">All wallets</option>
          {wallets.map((w) => (
            <option key={w.id} value={w.id}>{w.name}</option>
          ))}
        </select>
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="">All types</option>
          <option value="income">Income</option>
          <option value="expense">Expense</option>
          <option value="investment">Investment</option>
          <option value="donation">Donation</option>
        </select>
        <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} placeholder="From" />
        <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} placeholder="To" />
      </div>
      <form onSubmit={handleCreate} className="page-form transactions-form">
        <select
          value={form.wallet_id}
          onChange={(e) => setForm((f) => ({ ...f, wallet_id: e.target.value }))}
          required
        >
          <option value="">Wallet</option>
          {wallets.map((w) => (
            <option key={w.id} value={w.id}>{w.name}</option>
          ))}
        </select>
        <select
          value={form.type}
          onChange={(e) => setForm((f) => ({ ...f, type: e.target.value as Transaction['type'], subcategory_id: '' }))}
        >
          <option value="income">Income</option>
          <option value="expense">Expense</option>
          <option value="investment">Investment</option>
          <option value="donation">Donation</option>
        </select>
        <select
          value={form.subcategory_id}
          onChange={(e) => setForm((f) => ({ ...f, subcategory_id: e.target.value }))}
          required
        >
          <option value="">Subcategory</option>
          {subsForType.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
        <input
          type="number"
          step="0.01"
          placeholder="Amount"
          value={form.amount_cents ? form.amount_cents / 100 : ''}
          onChange={(e) => setForm((f) => ({ ...f, amount_cents: Math.round(parseFloat(e.target.value || '0') * 100) }))}
        />
        <input
          type="date"
          value={form.transaction_date}
          onChange={(e) => setForm((f) => ({ ...f, transaction_date: e.target.value }))}
        />
        <input
          placeholder="Description"
          value={form.description ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, description: e.target.value || undefined }))}
        />
        <button type="submit">Add</button>
      </form>
      {loading && list.length === 0 ? (
        <p className="page-loading">Loading…</p>
      ) : (
        <ul className="page-list">
          {list.map((t) => (
            <li key={t.id} className="page-list-item">
              <span>{formatDate(t.transaction_date)}</span>
              <span>{t.type}</span>
              <span>{formatCents(t.amount_cents)}</span>
              <span>{t.description || '—'}</span>
              <button type="button" onClick={() => handleDelete(t.id)}>Delete</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
