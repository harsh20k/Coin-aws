import { useState } from 'react'
import { api } from '../api/client'
import type { ChatResponse, DemoLoadResponse, DemoProfile } from '../api/types'
import './Page.css'
import './Chat.css'

const DEMO_PROFILES: { value: DemoProfile; label: string; description: string }[] = [
  {
    value: 'frequent_shopper',
    label: 'Frequent Shopper',
    description: 'Heavy on shopping & dining, regular salary income, modest savings.',
  },
  {
    value: 'savvy_investor',
    label: 'Savvy Investor',
    description: 'High income, aggressive investing in stocks & savings, minimal expenses.',
  },
  {
    value: 'budget_conscious',
    label: 'Budget-Conscious Saver',
    description: 'Modest income, tightly controlled spending, consistent small investments.',
  },
]

export function Chat() {
  const [message, setMessage] = useState('')
  const [reply, setReply] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [demoProfile, setDemoProfile] = useState<DemoProfile>('frequent_shopper')
  const [demoLoading, setDemoLoading] = useState(false)
  const [demoResult, setDemoResult] = useState<DemoLoadResponse | null>(null)
  const [demoError, setDemoError] = useState<string | null>(null)

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
      // #region agent log
      fetch('http://127.0.0.1:7244/ingest/ca6e21a8-b6aa-467e-976e-d9f77506770e',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'ef78fc'},body:JSON.stringify({sessionId:'ef78fc',location:'Chat.tsx:handleSubmit:catch',message:'Chat request exception',data:{error_message:e instanceof Error ? e.message : String(e),error_type:typeof e,error_name:e instanceof Error ? e.name : 'unknown'},timestamp:Date.now(),hypothesisId:'H-I'})}).catch(()=>{});
      // #endregion
      setError(e instanceof Error ? e.message : 'Failed to send')
    } finally {
      setLoading(false)
    }
  }

  async function handleLoadDemo(e: React.FormEvent) {
    e.preventDefault()
    setDemoLoading(true)
    setDemoError(null)
    setDemoResult(null)
    try {
      const data = await api.post<DemoLoadResponse>('/demo', { profile: demoProfile })
      setDemoResult(data)
    } catch (e) {
      setDemoError(e instanceof Error ? e.message : 'Failed to load demo data')
    } finally {
      setDemoLoading(false)
    }
  }

  const selectedProfile = DEMO_PROFILES.find((p) => p.value === demoProfile)

  return (
    <div className="page">
      <h2>AI Chat</h2>
      <p className="chat-intro">Ask questions about your budgets, goals, and transactions.</p>

      <div className="demo-panel">
        <div className="demo-panel-header">
          <span className="demo-badge">Demo</span>
          <h3>Load Sample Data</h3>
        </div>
        <p className="demo-panel-desc">
          Populate your account with realistic transactions to test the AI assistant.
        </p>
        <form onSubmit={handleLoadDemo} className="demo-form">
          <select
            value={demoProfile}
            onChange={(e) => {
              setDemoProfile(e.target.value as DemoProfile)
              setDemoResult(null)
              setDemoError(null)
            }}
            disabled={demoLoading}
          >
            {DEMO_PROFILES.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
          <button type="submit" disabled={demoLoading} className="demo-load-btn">
            {demoLoading ? 'Loading…' : 'Load Profile'}
          </button>
        </form>
        {selectedProfile && (
          <p className="demo-profile-desc">{selectedProfile.description}</p>
        )}
        {demoError && <p className="demo-error">{demoError}</p>}
        {demoResult && (
          <p className="demo-success">
            ✓ Loaded <strong>{demoResult.label}</strong> — {demoResult.transactions_loaded} transactions added to "Demo Wallet".
          </p>
        )}
      </div>

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
