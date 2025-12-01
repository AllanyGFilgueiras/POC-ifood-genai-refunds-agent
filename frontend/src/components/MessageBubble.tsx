import React from 'react'

interface Props {
  from: 'user' | 'agent'
  content: string
  isFallback?: boolean
}

const MessageBubble: React.FC<Props> = ({ from, content, isFallback }) => {
  return (
    <div className={`message ${from}`}>
      <div className="meta">
        {from === 'user' ? 'Você' : 'Agente iFood'}
        {isFallback && <span className="fallback">Resposta limitada</span>}
      </div>
      <div>{content}</div>
    </div>
  )
}

export default MessageBubble
