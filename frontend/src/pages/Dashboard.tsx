import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import type { Budget, Goal, Subcategory, Transaction, Wallet, ChatResponse } from '../api/types'
import { formatCents, formatDate } from '../utils/format'
import './Dashboard.css'

export function Dashboard() {
  const [wallets, setWallets] = useState<Wallet[]>([])
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [goals, setGoals] = useState<Goal[]>([])
  const [budgets, setBudgets] = useState<Budget[]>([])
  const [subcategories, setSubcategories] = useState<Record<string, Subcategory>>({})

  const [message, setMessage] = useState('')
  const [chatHistory, setChatHistory] = useState<{ role: 'user' | 'ai'; text: string; prompt?: string }[]>([])
  const [chatLoading, setChatLoading] = useState(false)
  const [chatError, setChatError] = useState<string | null>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    Promise.all([
      api.get<Wallet[]>('/wallets'),
      api.get<Transaction[]>('/transactions'),
      api.get<Goal[]>('/goals'),
      api.get<Budget[]>('/budgets'),
      api.get<Subcategory[]>('/subcategories'),
    ])
      .then(([w, t, g, b, s]) => {
        setWallets(w)
        setTransactions(t)
        setGoals(g)
        setBudgets(b)
        const subMap: Record<string, Subcategory> = {}
        s.forEach((sc) => { subMap[sc.id] = sc })
        setSubcategories(subMap)
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory, chatLoading])

  // Wallet balances from transactions
  const walletBalances: Record<string, number> = {}
  wallets.forEach((w) => { walletBalances[w.id] = 0 })
  transactions.forEach((t) => {
    if (walletBalances[t.wallet_id] === undefined) walletBalances[t.wallet_id] = 0
    walletBalances[t.wallet_id] += t.type === 'income' ? t.amount_cents : -t.amount_cents
  })

  // Last 10 transactions sorted by date desc
  const recent10 = [...transactions]
    .sort((a, b) => b.transaction_date.localeCompare(a.transaction_date))
    .slice(0, 10)

  function goalProgress(g: Goal): number {
    const sum = transactions
      .filter(
        (t) =>
          t.type === g.goal_type &&
          t.transaction_date >= g.period_start &&
          t.transaction_date <= g.period_end,
      )
      .reduce((acc, t) => acc + t.amount_cents, 0)
    return g.target_cents > 0 ? Math.min(sum / g.target_cents, 1) : 0
  }

  function budgetProgress(b: Budget): number {
    const sum = transactions
      .filter(
        (t) =>
          t.subcategory_id === b.subcategory_id &&
          t.transaction_date >= b.period_start &&
          t.transaction_date <= b.period_end,
      )
      .reduce((acc, t) => acc + t.amount_cents, 0)
    return b.limit_cents > 0 ? Math.min(sum / b.limit_cents, 1) : 0
  }

  async function handleChat(e: React.FormEvent) {
    e.preventDefault()
    if (!message.trim() || chatLoading) return
    const userMsg = message.trim()
    setChatHistory((h) => [...h, { role: 'user', text: userMsg }])
    setMessage('')
    setChatLoading(true)
    setChatError(null)
    try {
      const data = await api.post<ChatResponse>('/chat', { message: userMsg })
      setChatHistory((h) => [...h, { role: 'ai', text: data.reply, prompt: data.prompt }])
    } catch (err) {
      setChatError(err instanceof Error ? err.message : 'Failed to send')
    } finally {
      setChatLoading(false)
    }
  }

  return (
    <div className="dashboard">
      {/* Left column: wallets, goals, budgets */}
      <div className="db-left">
        <section className="db-panel">
          <h3 className="db-panel-title">Wallets</h3>
          {wallets.length === 0 ? (
            <p className="db-empty">No wallets yet</p>
          ) : (
            <ul className="db-wallet-list">
              {wallets.map((w) => {
                const bal = walletBalances[w.id] ?? 0
                return (
                  <li key={w.id}>
                    <span className="db-wallet-name">{w.name}</span>
                    <span className={`db-wallet-bal ${bal >= 0 ? 'pos' : 'neg'}`}>
                      {bal < 0 ? '−' : ''}{formatCents(Math.abs(bal))}
                    </span>
                  </li>
                )
              })}
            </ul>
          )}
        </section>

        <section className="db-panel">
          <h3 className="db-panel-title">Goals</h3>
          {goals.length === 0 ? (
            <p className="db-empty">No goals yet</p>
          ) : (
            <ul className="db-progress-list">
              {goals.map((g) => {
                const pct = Math.round(goalProgress(g) * 100)
                return (
                  <li key={g.id}>
                    <div className="db-progress-header">
                      <span>{g.title}</span>
                      <span>{pct}%</span>
                    </div>
                    <div className="db-bar-track">
                      <div className="db-bar-fill goal" style={{ width: `${pct}%` }} />
                    </div>
                  </li>
                )
              })}
            </ul>
          )}
        </section>

        <section className="db-panel">
          <h3 className="db-panel-title">Budgets</h3>
          {budgets.length === 0 ? (
            <p className="db-empty">No budgets yet</p>
          ) : (
            <ul className="db-progress-list">
              {budgets.map((b) => {
                const pct = Math.round(budgetProgress(b) * 100)
                const over = pct >= 100
                return (
                  <li key={b.id}>
                    <div className="db-progress-header">
                      <span>{subcategories[b.subcategory_id]?.name ?? 'Budget'}</span>
                      <span className={over ? 'db-over' : ''}>{pct}%</span>
                    </div>
                    <div className="db-bar-track">
                      <div
                        className={`db-bar-fill budget ${over ? 'over' : ''}`}
                        style={{ width: `${Math.min(pct, 100)}%` }}
                      />
                    </div>
                  </li>
                )
              })}
            </ul>
          )}
        </section>
      </div>

      {/* Center: chat */}
      <div className="db-center">
        <section className="db-panel db-chat-panel">
          <h3 className="db-panel-title">👶 Penny</h3>
          <div className="db-chat-messages">
            {chatHistory.length === 0 && (
              <p className="db-chat-hint">Ask Penny about your finances!</p>
            )}
            {chatHistory.map((msg, i) => (
              <div key={i} className={`db-chat-msg db-chat-msg-${msg.role}`}>
                <div className="db-chat-bubble">{msg.text}</div>
                {msg.prompt && (
                  <details className="db-prompt-details">
                    <summary>Prompt sent to Claude ↓</summary>
                    <pre>{msg.prompt}</pre>
                  </details>
                )}
              </div>
            ))}
            {chatLoading && (
              <div className="db-chat-msg db-chat-msg-ai">
                <div className="db-chat-bubble db-chat-thinking">…</div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>
          {chatError && <p className="db-chat-error">{chatError}</p>}
          <form onSubmit={handleChat} className="db-chat-form">
            <input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask Penny…"
              disabled={chatLoading}
            />
            <button type="submit" disabled={chatLoading || !message.trim()}>
              Send
            </button>
          </form>
        </section>
      </div>

      {/* Right: recent transactions */}
      <div className="db-right">
        <section className="db-panel">
          <h3 className="db-panel-title">Recent Transactions</h3>
          {recent10.length === 0 ? (
            <p className="db-empty">No transactions yet</p>
          ) : (
            <ul className="db-txn-list">
              {recent10.map((t) => {
                const isIncome = t.type === 'income'
                return (
                  <li key={t.id} className={`db-txn-item ${isIncome ? 'income' : 'outflow'}`}>
                    <span className="db-txn-sign">{isIncome ? '+' : '−'}</span>
                    <span className="db-txn-amount">{formatCents(t.amount_cents)}</span>
                    <span className="db-txn-cat">
                      {subcategories[t.subcategory_id]?.name ?? t.type}
                    </span>
                    <span className="db-txn-date">{formatDate(t.transaction_date)}</span>
                  </li>
                )
              })}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}
