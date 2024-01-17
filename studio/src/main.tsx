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

export const App: React.FC = () => {
  return (
    <Suspense fallback={<p>Loading...</p>}>
      {useRoutes(routes)}
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
