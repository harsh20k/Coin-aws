import { useState } from 'react'
import { api } from '../api/client'
import type { ChatResponse } from '../api/types'
import './Page.css'
import './Chat.css'

export function Chat() {
  const [message, setMessage] = useState('')
  const [reply, setReply] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!message.trim()) return
    setLoading(true)
    setError(null)
    setReply(null)
    try {
      const data = await api.post<ChatResponse>('/chat', { message: message.trim() })
      setReply(data.reply)
      setMessage('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to send')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <h2>AI Chat</h2>
      <p className="chat-intro">Ask questions about your budgets, goals, and transactions.</p>
      {error && <p className="page-error">{error}</p>}
      <form onSubmit={handleSubmit} className="chat-form">
        <input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Your question…"
          disabled={loading}
        />
        <button type="submit" disabled={loading}>{loading ? 'Sending…' : 'Send'}</button>
      </form>
      {reply !== null && (
        <div className="chat-reply">
          <strong>Reply:</strong>
          <p>{reply}</p>
        </div>
      )}
    </div>
  )
}
