import axios from 'axios'
import { Answer } from '../types'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
})

export async function askAgent(question: string): Promise<Answer> {
  const { data } = await client.post<Answer>('/chat', { question })
  return data
}
