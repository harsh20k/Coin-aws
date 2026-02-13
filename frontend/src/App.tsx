import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthGuard } from './auth/AuthGuard'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Wallets } from './pages/Wallets'
import { Transactions } from './pages/Transactions'
import { Budgets } from './pages/Budgets'
import { Goals } from './pages/Goals'
import { Chat } from './pages/Chat'

function App() {
  return (
    <BrowserRouter>
      <AuthGuard>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="wallets" element={<Wallets />} />
            <Route path="transactions" element={<Transactions />} />
            <Route path="budgets" element={<Budgets />} />
            <Route path="goals" element={<Goals />} />
            <Route path="chat" element={<Chat />} />
          </Route>
        </Routes>
      </AuthGuard>
    </BrowserRouter>
  )
}

export default App
