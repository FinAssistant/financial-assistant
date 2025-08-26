import { Routes, Route } from 'react-router-dom'
import { PersistGate } from 'redux-persist/integration/react'
import { persistor } from './store'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import AboutPage from './pages/AboutPage'
import LoginPage from './pages/LoginPage'
import AuthGuard from './components/layout/AuthGuard'

function App() {
  return (
    <PersistGate loading={<div>Loading state...</div>} persistor={persistor}>
      <Routes>
        {/* Public routes */}
        <Route
          path="/login"
          element={
            <AuthGuard requireAuth={false}>
              <LoginPage />
            </AuthGuard>
          }
        />

        {/* Public home page */}
        <Route
          path="/"
          element={
            <Layout>
              <HomePage />
            </Layout>
          }
        />

        {/* Protected routes */}
        <Route
          path="/about"
          element={
            <AuthGuard requireAuth={true}>
              <Layout>
                <AboutPage />
              </Layout>
            </AuthGuard>
          }
        />
      </Routes>
    </PersistGate>
  )
}

export default App