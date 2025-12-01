import React from 'react'
import Chat from './components/Chat'

const App: React.FC = () => {
  return (
    <div className="app-shell">
      <div className="header">
        <div className="title-block">
          <h1>iFood GenAI Refunds Agent</h1>
          <p>Agente interno com RAG para reembolsos, cancelamentos e cobrança.</p>
          <div className="meta-cards">
            <div className="meta-chip"><span className="meta-dot dot-green" />Anti-alucinação</div>
            <div className="meta-chip"><span className="meta-dot dot-orange" />Fallback seguro</div>
            <div className="meta-chip"><span className="meta-dot dot-pink" />Transparência de fontes</div>
          </div>
        </div>
        <span className="badge">POC educativa · anti-alucinação</span>
      </div>
      <Chat />
    </div>
  )
}

export default App
