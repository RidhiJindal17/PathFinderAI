import React from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import LandingPage    from './pages/LandingPage'
import AnalyzePage    from './pages/AnalyzePage'
import ReportPage     from './pages/ReportPage'
import TranslatorPage from './pages/TranslatorPage'

function Navbar() {
  const location  = useLocation()
  const isLanding = location.pathname === '/'

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      isLanding
        ? 'bg-blue-900 border-b border-blue-800'
        : 'bg-white border-b border-slate-100 shadow-sm'
    }`}>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">

        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded-lg bg-orange-500 flex items-center justify-center
                          group-hover:bg-orange-600 transition-colors duration-200">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24"
              stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round"
                d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
          </div>
          <span className={`font-display font-bold text-lg ${isLanding ? 'text-white' : 'text-blue-900'}`}>
            PathFinder <span className="text-orange-500">AI</span>
          </span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-1 sm:gap-2">
          <NavLink to="/analyze"    label="Analyze"    isLanding={isLanding} active={location.pathname === '/analyze'} />
          <NavLink to="/translator" label="Translator" isLanding={isLanding} active={location.pathname === '/translator'} />
          <Link to="/analyze" className="ml-2 btn-primary text-sm px-4 py-2 hidden sm:inline-flex">
            Get Started
          </Link>
        </div>
      </div>
    </nav>
  )
}

function NavLink({ to, label, isLanding, active }) {
  return (
    <Link
      to={to}
      className={`px-3 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${
        active
          ? 'bg-orange-100 text-orange-600'
          : isLanding
            ? 'text-blue-200 hover:text-white hover:bg-white/10'
            : 'text-slate-500 hover:text-blue-900 hover:bg-blue-50'
      }`}
    >
      {label}
    </Link>
  )
}

function Footer() {
  return (
    <footer className="bg-blue-950 text-blue-300 py-8 mt-auto">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-orange-500 flex items-center justify-center">
              <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24"
                stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round"
                  d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
            </div>
            <span className="font-display font-bold text-white text-sm">PathFinder AI</span>
          </div>
          <p className="text-xs text-blue-400 text-center">
            Built for India's freshers · Zero cost · AI-powered career navigation
          </p>
          <p className="text-xs text-blue-500">B.Tech Final Year Project · 2025</p>
        </div>
      </div>
    </footer>
  )
}

export default function App() {
  return (
    <Router>
      <div className="flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1">
          <Routes>
            <Route path="/"                 element={<LandingPage />} />
            <Route path="/analyze"          element={<AnalyzePage />} />
            <Route path="/report/:reportId" element={<ReportPage />} />
            <Route path="/translator"       element={<TranslatorPage />} />
            <Route path="*" element={
              <div className="pt-32 flex flex-col items-center justify-center min-h-screen gap-4">
                <p className="font-display text-4xl text-blue-900">404</p>
                <p className="text-slate-500">Page not found.</p>
                <Link to="/" className="btn-primary">Go Home</Link>
              </div>
            } />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  )
}