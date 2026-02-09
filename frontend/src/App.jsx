import { Routes, Route, NavLink, Navigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'
import nokiaLogo from './nokia.jpg'

function App() {
  return (
    <div className="app">
      <nav className="nav">
        <div className="nav-brand">
          <img src={nokiaLogo} alt="Nokia" className="nav-logo" />
          <span>NYC Taxi Analytics</span>
        </div>
        <div className="nav-links">
          <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'active' : ''}>
            Dashboard
          </NavLink>
          <NavLink to="/upload" className={({ isActive }) => isActive ? 'active' : ''}>
            Upload Data
          </NavLink>
        </div>
      </nav>
      <main className="main">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
