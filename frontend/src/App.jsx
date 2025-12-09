import React from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import UploadPage from './pages/UploadPage'
import Dashboard from './pages/Dashboard'
import ProvidersPage from './pages/ProvidersPage'
import DiscrepanciesPage from './pages/DiscrepanciesPage'
import ReportsPage from './pages/ReportsPage'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <div className="nav-container">
            <Link to="/" className="nav-logo">
              MedAtlas
            </Link>
            <div className="nav-menu">
              <Link to="/" className="nav-link">Dashboard</Link>
              <Link to="/upload" className="nav-link">Upload</Link>
              <Link to="/providers" className="nav-link">Providers</Link>
              <Link to="/discrepancies" className="nav-link">Discrepancies</Link>
              <Link to="/reports" className="nav-link">Reports</Link>
            </div>
          </div>
        </nav>
        
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/providers" element={<ProvidersPage />} />
            <Route path="/discrepancies" element={<DiscrepanciesPage />} />
            <Route path="/reports" element={<ReportsPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App

