import { Routes, Route } from 'react-router-dom'
import { PersistGate } from 'redux-persist/integration/react'
import { persistor } from './store'
import Layout from './components/layout/Layout'
import HomePage from './pages/HomePage'
import AboutPage from './pages/AboutPage'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import NotImplementedPage from './pages/NotImplementedPage'
import AuthGuard from './components/layout/AuthGuard'
import { useSelector } from 'react-redux'
import { selectIsAuthenticated } from './store/slices/authSlice'

function App() {
  const isAuthenticated = useSelector(selectIsAuthenticated)

  return (
    <PersistGate loading={<div>Loading state...</div>} persistor={persistor}>
      <Routes>
        {/* Public routes */}
        <Route
          path="/login"
          element={<LoginPage />}
        />

        {/* Public home page */}
        <Route
          path="/"
          element={
            isAuthenticated ? (
              <Layout>
                <DashboardPage />
              </Layout>
            ) : (
              <HomePage />
            )
          }
        />

        {/* Protected routes */}
        <Route
          path="/about"
          element={
            <Layout>
              <AboutPage />
            </Layout>
          }
        />

        {/* Financial Management Routes */}
        <Route
          path="/accounts"
          element={
            <AuthGuard requireAuth={true}>
              <Layout>
                <NotImplementedPage />
              </Layout>
            </AuthGuard>
          }
        />
        
        <Route
          path="/transactions"
          element={
            <AuthGuard requireAuth={true}>
              <Layout>
                <NotImplementedPage />
              </Layout>
            </AuthGuard>
          }
        />
        
        <Route
          path="/investments"
          element={
            <AuthGuard requireAuth={true}>
              <Layout>
                <NotImplementedPage />
              </Layout>
            </AuthGuard>
          }
        />
        
        <Route
          path="/budgets"
          element={
            <AuthGuard requireAuth={true}>
              <Layout>
                <NotImplementedPage />
              </Layout>
            </AuthGuard>
          }
        />

        {/* Analytics Routes */}
        <Route
          path="/reports"
          element={
            <AuthGuard requireAuth={true}>
              <Layout>
                <NotImplementedPage />
              </Layout>
            </AuthGuard>
          }
        />
        
        <Route
          path="/analytics"
          element={
            <AuthGuard requireAuth={true}>
              <Layout>
                <NotImplementedPage />
              </Layout>
            </AuthGuard>
          }
        />

        {/* Account Routes */}
        <Route
          path="/profile"
          element={
            <AuthGuard requireAuth={true}>
              <Layout>
                <NotImplementedPage />
              </Layout>
            </AuthGuard>
          }
        />
        
        <Route
          path="/settings"
          element={
            <AuthGuard requireAuth={true}>
              <Layout>
                <NotImplementedPage />
              </Layout>
            </AuthGuard>
          }
        />

        {/* Catch-all route for unmatched paths */}
        <Route
          path="*"
          element={
            <Layout>
              <NotImplementedPage 
                title="Page Not Found"
                message="The page you're looking for doesn't exist or may have been moved."
                features={[]}
              />
            </Layout>
          }
        />
      </Routes >
    </PersistGate >
  )
}

export default App