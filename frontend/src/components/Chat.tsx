import React, { useState } from 'react'
import MessageBubble from './MessageBubble'
import SourcesPanel from './SourcesPanel'
import { askAgent } from '../services/api'
import { Answer, Source } from '../types'

interface Message {
  from: 'user' | 'agent'
  content: string
  isFallback?: boolean
  sources?: Source[]
}

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const lastAnswerSources = messages.filter((m) => m.from === 'agent').at(-1)?.sources || []

  const handleSubmit = async () => {
    if (!question.trim()) return
    setError(null)
    const q = question.trim()
    setMessages((prev) => [...prev, { from: 'user', content: q }])
    setLoading(true)
    setQuestion('')
    try {
      const response: Answer = await askAgent(q)
      setMessages((prev) => [
        ...prev,
        { from: 'agent', content: response.answer, isFallback: response.is_fallback, sources: response.sources },
      ])
    } catch (err) {
      setError('Não foi possível obter resposta. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="layout">
      <div className="card chat-window" aria-label="Janela do chat">
        <div className="messages">
          {messages.map((msg, idx) => (
            <MessageBubble key={idx} from={msg.from} content={msg.content} isFallback={msg.isFallback} />
          ))}
          {loading && <div className="loading">Consultando políticas…</div>}
          {error && <div className="error" role="alert">{error}</div>}
        </div>
        <div className="input-area">
          <label className="sr-only" htmlFor="question-input">Pergunta</label>
          <input
            id="question-input"
            placeholder="Digite a pergunta do cliente"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            aria-label="Pergunta"
          />
          <button onClick={handleSubmit} disabled={loading}>Perguntar</button>
        </div>
      </div>

      <div className="card" aria-label="Fontes usadas">
        <h3>Fontes aplicadas</h3>
        {messages.length === 0 && <p className="loading">Envie uma pergunta para ver as políticas usadas.</p>}
        {messages.length > 0 && <SourcesPanel sources={lastAnswerSources} />}
      </div>
    </div>
  )
}

export default Chat
