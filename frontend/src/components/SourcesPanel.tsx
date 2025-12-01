import React from 'react'
import { Source } from '../types'

interface Props {
  sources: Source[]
}

const SourcesPanel: React.FC<Props> = ({ sources }) => {
  if (!sources.length) {
    return <p className="loading">Nenhuma fonte aplicada.</p>
  }

  return (
    <div className="sources">
      {sources.map((source) => (
        <div key={source.id} className="source-card">
          <div className="source-meta">
            <strong>{source.fonte}</strong>
            <span>· {source.categoria}</span>
            {source.score !== undefined && <span>· score {source.score.toFixed(2)}</span>}
          </div>
          <div><strong>Cenário:</strong> {source.pergunta}</div>
          <div><strong>Ação:</strong> {source.resposta}</div>
        </div>
      ))}
    </div>
  )
}

export default SourcesPanel
