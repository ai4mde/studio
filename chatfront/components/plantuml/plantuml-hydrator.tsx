'use client'

import { useEffect } from 'react'
import PlantUML from './plantuml'
import { createRoot } from 'react-dom/client'

export default function PlantUMLHydrator() {
  useEffect(() => {
    const diagrams = document.querySelectorAll('.plantuml-diagram')
    diagrams.forEach(diagram => {
      const diagramCode = diagram.getAttribute('data-diagram')
      if (diagramCode) {
        const root = createRoot(diagram)
        root.render(<PlantUML value={diagramCode} />)
      }
    })
  }, [])

  return null
} 