import React, { Suspense } from 'react'
import ReactDOM from 'react-dom/client'
import '@fontsource/ibm-plex-mono'
import '@fontsource/inter'
import './index.css'
import {
  BrowserRouter as Router,
  useRoutes,
} from 'react-router-dom'
import routes from '~react-pages'
import { useAuthStore } from '$lib/features/auth/state/auth'
import LoginScreen from '$lib/features/auth/components/LoginScreen'

export const App: React.FC = () => {
  const { isAuthenticated } = useAuthStore()
  const _routes = useRoutes(routes)

  if (!isAuthenticated) {
    return (
      <LoginScreen/>
    )
  }

  return (
    <Suspense fallback={<p>Loading...</p>}>
      {_routes}
    </Suspense>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Router>
      <App />
    </Router>
  </React.StrictMode>,
)
