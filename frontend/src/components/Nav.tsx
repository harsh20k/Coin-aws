import { Link, useLocation } from 'react-router-dom'
import { signOut } from 'aws-amplify/auth'
import './Nav.css'

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/wallets', label: 'Wallets' },
  { to: '/transactions', label: 'Transactions' },
  { to: '/budgets', label: 'Budgets' },
  { to: '/goals', label: 'Goals' },
  { to: '/chat', label: 'Chat' },
]

export function Nav() {
  const location = useLocation()

  async function handleSignOut() {
    await signOut()
    window.location.href = '/'
  }

  return (
    <nav className="nav">
      <ul className="nav-list">
        {links.map(({ to, label }) => (
          <li key={to}>
            <Link
              to={to}
              className={location.pathname === to ? 'nav-link active' : 'nav-link'}
            >
              {label}
            </Link>
          </li>
        ))}
      </ul>
      <button type="button" className="nav-logout" onClick={handleSignOut}>
        Sign out
      </button>
    </nav>
  )
}
