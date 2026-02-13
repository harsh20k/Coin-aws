import { Outlet } from 'react-router-dom'
import { Nav } from './Nav'
import './Layout.css'

export function Layout() {
  return (
    <div className="layout">
      <header className="layout-header">
        <h1 className="layout-title">Dalla</h1>
        <Nav />
      </header>
      <main className="layout-main">
        <Outlet />
      </main>
    </div>
  )
}
