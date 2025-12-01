export type Source = {
  id: string
  fonte: string
  categoria: string
  pergunta: string
  resposta: string
  score?: number
}

export type Answer = {
  answer: string
  is_fallback: boolean
  sources: Source[]
  similarity_scores?: { source_id: string; score: number }[]
}
