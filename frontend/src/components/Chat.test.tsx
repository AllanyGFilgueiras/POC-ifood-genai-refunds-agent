import { render, screen, waitFor, act } from '@testing-library/react'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'
import { vi, type MockedFunction } from 'vitest'
import Chat from './Chat'
import { askAgent } from '../services/api'

vi.mock('../services/api')

const mockedAskAgent = askAgent as MockedFunction<typeof askAgent>

describe('Chat component', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('envia pergunta e mostra resposta do agente', async () => {
    mockedAskAgent.mockResolvedValue({
      answer: 'Resposta baseada em política simulada',
      is_fallback: false,
      sources: [
        {
          id: '1',
          fonte: 'Política 3.2',
          categoria: 'reembolso',
          pergunta: 'Quando o cliente tem direito?',
          resposta: 'Sempre que falha do restaurante',
        },
      ],
    })

    render(<Chat />)
    const input = screen.getByLabelText(/pergunta/i)
    await act(async () => {
      await userEvent.type(input, 'Cliente quer reembolso')
      await userEvent.click(screen.getByRole('button', { name: /perguntar/i }))
    })

    await waitFor(() => expect(mockedAskAgent).toHaveBeenCalled())
    expect(await screen.findByText(/Resposta baseada em política simulada/)).toBeInTheDocument()
    expect(screen.getByText(/Política 3.2/)).toBeInTheDocument()
  })

  it('exibe badge de fallback quando resposta é limitada', async () => {
    mockedAskAgent.mockResolvedValue({
      answer: 'Fallback acionado',
      is_fallback: true,
      sources: [],
    })

    render(<Chat />)
    const input = screen.getByLabelText(/pergunta/i)
    await act(async () => {
      await userEvent.type(input, 'Pergunta fora do escopo')
      await userEvent.click(screen.getByRole('button', { name: /perguntar/i }))
    })

    expect(await screen.findByText(/Fallback acionado/)).toBeInTheDocument()
    expect(await screen.findByText(/Resposta limitada/)).toBeInTheDocument()
  })
})
