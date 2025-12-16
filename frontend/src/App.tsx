// App.tsx
import React from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Layout from './components/Layout'
import About from './pages/About'
import Dashboard from './pages/Dashboard'
import Providers from './pages/Providers'
import Discrepancies from './pages/Discrepancies'
import Export from './pages/Export'
import Upload from './pages/Upload'

function AppRoutes() {
  const location = useLocation()

  // you no longer need currentPage for Layout, but can keep this if used elsewhere
  const path = location.pathname
  const currentPage =
    path === '/dashboard'
      ? 'dashboard'
      : path === '/providers'
      ? 'providers'
      : path === '/discrepancies'
      ? 'discrepancies'
      : path === '/export'
      ? 'export'
      : path === '/upload'
      ? 'upload'
      : 'about'

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<About />} />
        <Route path="/about" element={<About />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/providers" element={<Providers />} />
        <Route path="/discrepancies" element={<Discrepancies />} />
        <Route path="/export" element={<Export />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}
