import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Wallet } from '../api/types'
import './Page.css'

export function Wallets() {
  const [list, setList] = useState<Wallet[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const data = await api.get<Wallet[]>('/wallets')
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
    if (!name.trim()) return
    try {
      await api.post('/wallets', { name: name.trim() })
      setName('')
      load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Create failed')
    }
  }

  async function handleUpdate(id: string) {
    if (!editName.trim()) return
    try {
      await api.put(`/wallets/${id}`, { name: editName.trim() })
      setEditingId(null)
      load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Update failed')
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Delete this wallet?')) return
    try {
      await api.delete(`/wallets/${id}`)
      load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed')
    }
  }

  if (loading && list.length === 0) return <p className="page-loading">Loading…</p>
  return (
    <div className="page">
      <h2>Wallets</h2>
      {error && <p className="page-error">{error} <button type="button" onClick={load}>Retry</button></p>}
      <form onSubmit={handleCreate} className="page-form">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Wallet name"
          required
        />
        <button type="submit">Add wallet</button>
      </form>
      <ul className="page-list">
        {list.map((w) => (
          <li key={w.id} className="page-list-item">
            {editingId === w.id ? (
              <>
                <input
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  autoFocus
                />
                <button type="button" onClick={() => handleUpdate(w.id)}>Save</button>
                <button type="button" onClick={() => setEditingId(null)}>Cancel</button>
              </>
            ) : (
              <>
                <span>{w.name}</span>
                <button type="button" onClick={() => { setEditingId(w.id); setEditName(w.name) }}>Edit</button>
                <button type="button" onClick={() => handleDelete(w.id)}>Delete</button>
              </>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
