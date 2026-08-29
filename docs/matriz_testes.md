# Matriz de testes

## Resultado automatizado

```text
python -m pytest -q
30 passed
```

| ID | Requisito | Cenário | Esperado | Resultado obtido | Status |
|---|---|---|---|---|---|
| T-001 | RF01 | carregar `config.json` válido | configuração e raiz resolvidas | conforme esperado | Aprovado |
| T-002 | RF01/RNF | configuração incompleta | erro de configuração claro | `ConfigError` | Aprovado |
| T-003 | RF06 | SQLite em pasta inexistente | criar pasta/tabelas automaticamente | banco criado | Aprovado |
| T-004 | RF06 | buscar/atualizar/excluir protocolo | operações controladas | CRUD executado | Aprovado |
| T-005 | RF04 | registro oficial válido | `valido`, sem motivos | conforme esperado | Aprovado |
| T-006 | RF04 | e-mail inválido | `email_invalido` | conforme esperado | Aprovado |
| T-007 | RF04 | `[vazio]` em solicitante | `incompleto` | conforme esperado | Aprovado |
| T-008 | RF03/RF04 | protocolo OCR `AT -@52` | normalizar para `AT-052` | `AT-052` | Aprovado |
| T-009 | RF03 | página com 2 protocolos OCR | separar 2 registros | 2 registros | Aprovado |
| T-010 | RF04 | categoria OCR `atvidade` | categoria oficial | `Atividades e arquivos` | Aprovado |
| T-011 | RF05 | tokenização/stopwords | tokens normalizados | conforme esperado | Aprovado |
| T-012 | RF10 | chunk > limite | múltiplos chunks <= tamanho | conforme esperado | Aprovado |
| T-013 | RF08 | indicadores obrigatórios | totais, %, tempo, OCR, erros | conforme esperado | Aprovado |
| T-014 | RF07 | ViaCEP responde | preencher município/UF | dados preenchidos | Aprovado (mock) |
| T-015 | RF07 | ViaCEP indisponível | retornar `None`, sem exception | pipeline não interrompido | Aprovado (mock) |
| T-016 | RF12 | filtro categoria | `where` por categoria | conforme esperado | Aprovado |
| T-017 | RF12 | filtro protocolo | `where` por protocolo | conforme esperado | Aprovado |
| T-018 | RF12 | categoria + protocolo | `$and` dos filtros | conforme esperado | Aprovado |
| T-019 | RF13/RF14 | sem fontes | informar insuficiência | mensagem correta | Aprovado |
| T-020 | RF13 | contexto longo | respeitar limite | contexto limitado | Aprovado |
| T-021 | RF15 | `GET /health` | HTTP 200/status ok | 200 | Aprovado |
| T-022 | RF15 | pergunta muito curta | HTTP 422 | 422 | Aprovado |
| T-023 | RF15 | `/ask` com fonte | resposta + fontes + score | conforme esperado | Aprovado (mock retriever) |
| T-024 | RF15/RNF | erro interno no `/ask` | HTTP 503 sem traceback/segredo | conforme esperado | Aprovado |
| T-025 | RF16 | URL via ambiente | usar `API_BASE_URL` | conforme esperado | Aprovado |
| T-026 | RF16 | conexão API falha | mensagem compreensível | `ApiClientError` amigável | Aprovado |
| T-027 | RF01–RF09 | processamento dos 4 PDFs oficiais | 100 registros, 25 OCR, 10 duplicados | 100 / 25 / 10 | Aprovado |
| T-028* | RF01/RF06/RF09 | reexecutar após histórico existente | continuar com 100 registros | 100 registros | Aprovado |

`T-027`/`T-028` fazem parte do mesmo teste de integração automatizado; por isso há 27 funções de teste e 28 verificações principais listadas na matriz.

## Evidência do conjunto oficial

```text
Documentos: 4
Páginas: 27
Páginas OCR: 7
Registros: 100
Atendimentos únicos: 90
Duplicados: 10
```

O teste de integração real usa Tesseract/Poppler quando disponíveis e substitui apenas o ViaCEP por mock para não tornar a validação dependente de internet.

## Verificações manuais para apresentação

1. `python -m src.main --reset` e conferência do CSV/JSON/log/gráficos.
2. `python -m src.main` novamente para demonstrar idempotência.
3. `python -m src.main --indexar` para gerar/sincronizar ChromaDB.
4. `python -m uvicorn src.api:app --reload` e teste de `/health` e `/ask` em `/docs`.
5. `streamlit run src/app_streamlit.py` e consulta com exibição de fontes.
6. Retirar temporariamente `OPENAI_API_KEY` para demonstrar o modo local.


Pipeline:
4 documentos
27 páginas
7 páginas OCR
100 registros

Testes automatizados:
30 passed in 35.87s

Indexação:
90 chunks indexados

Streamlit:
Inicialização aprovada
Consulta aprovada
Exibição das fontes aprovada
Filtro por protocolo aprovado
Filtro por categoria aprovado

Modo:
recuperacao_local

### Ajustes finais da suíte

Durante a integração final, o teste HTTP/RAG foi atualizado para acompanhar
a assinatura atual de `semantic_query`, que passou a aceitar também o filtro
por protocolo.

A validação da mensagem do modo local também foi ajustada para verificar
elementos funcionais da resposta — protocolo e contexto recuperado — em vez
de depender de uma frase textual específica.

Após os ajustes, a suíte completa passou com 30 testes aprovados.