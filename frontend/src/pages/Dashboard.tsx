import { Link } from 'react-router-dom'
import './Dashboard.css'

const sections = [
  { to: '/wallets', label: 'Wallets' },
  { to: '/transactions', label: 'Transactions' },
  { to: '/budgets', label: 'Budgets' },
  { to: '/goals', label: 'Goals' },
  { to: '/chat', label: 'AI Chat' },
]

export function Dashboard() {
  return (
    <div className="dashboard">
      <h2>Dashboard</h2>
      <p className="dashboard-intro">Manage your finances.</p>
      <ul className="dashboard-cards">
        {sections.map(({ to, label }) => (
          <li key={to}>
            <Link to={to} className="dashboard-card">
              {label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
