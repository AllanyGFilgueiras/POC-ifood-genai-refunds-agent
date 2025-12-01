# Engineering Guidelines

## Princípios Gerais
- Escreva código legível antes de tentar ser “esperto”.
- Sempre que possível, use TDD (teste antes da implementação).
- Nenhuma funcionalidade relevante sem testes.
- Prefira funções puras e side-effects bem isolados.
- Evite acoplamento forte entre camadas (API, RAG, UI, LLM).

## Padrões de Commit (Conventional Commits)
- `feat`: nova funcionalidade.
- `fix`: correção de bug.
- `test`: adição ou ajuste de testes.
- `chore`: mudanças de infra, CI, configs.
- `refactor`: melhoria de código sem alterar comportamento.
- `docs`: mudanças em README, documentação, etc.

## TDD e Testes
- Não subir código sem pelo menos um teste básico.
- Testes devem ser simples, rápidos e focados.
- Cenários recomendados:
  - ingestão do CSV com dados mínimos e de borda.
  - retrieval retornando o documento mais relevante.
  - fallback quando não há documentos relevantes ou score baixo.
  - API respondendo corretamente para perguntas de reembolso/cancelamento/cobrança.

## Qualidade e Lint
- Backend: `black`, `isort`, `ruff`, `mypy`, `pytest`.
- Frontend: `eslint`, `prettier`, `vitest`.
- Sugestão: configure pre-commit hooks para rodar formatadores/lints antes de cada commit.

## Estilo de Código
- Python: tipagem em todas as funções públicas; nomes descritivos para funções e variáveis.
- TypeScript: evitar `any` sempre que possível; crie tipos específicos para respostas de API.
