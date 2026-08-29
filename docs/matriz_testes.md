# Matriz de testes

## Testes automatizados

| ID | Requisito | Cenário | Resultado esperado | Arquivo | Resultado |
|---|---|---|---|---|---|
| T-001 | RF15 | `GET /health` sem chave | HTTP 200, `status=ok`, modo local | `tests/test_api.py` | Passou |
| T-002 | RF15/RF14 | `GET /health` com chave configurada | HTTP 200, modo `rag` | `tests/test_api.py` | Passou |
| T-003 | RF15 | Pergunta com 1 caractere | HTTP 422 | `tests/test_api.py` | Passou |
| T-004 | RF15 | `top_k=21` | HTTP 422 | `tests/test_api.py` | Passou |
| T-005 | RF15 | Consulta válida | HTTP 200 com resposta e fontes | `tests/test_api.py` | Passou |
| T-006 | RF15 | Falha na recuperação | HTTP 503 sem detalhe interno | `tests/test_api.py` | Passou |
| T-007 | RF16 | URL definida por variável de ambiente | URL normalizada | `tests/test_ui_client.py` | Passou |
| T-008 | RF16 | Envio do payload para `/ask` | Pergunta, `top_k` e categoria corretos | `tests/test_ui_client.py` | Passou |
| T-009 | RF16 | API indisponível | Mensagem de erro compreensível | `tests/test_ui_client.py` | Passou |
| T-010 | RF16 | Resposta JSON inesperada | Erro de formato compreensível | `tests/test_ui_client.py` | Passou |
| T-011 | RF13/RF14/RF15 | HTTP → recuperação local → fontes | HTTP 200, modo local e fonte rastreável | `tests/test_integration.py` | Passou |
| T-012 | RF05 | Chunking com limite e sobreposição | Chunks dentro do tamanho configurado | `tests/test_text_processor.py` | Passou |
| T-013 | RF05 | Remoção de stopword | Texto processado sem stopword testada | `tests/test_text_processor.py` | Passou |
| T-014 | RF04 | Registro válido | Classificação válida e categoria normalizada | `tests/test_validation.py` | Passou |
| T-015 | RF04 | E-mail inválido | Motivo `email_invalido` | `tests/test_validation.py` | Passou |

## Resultado da execução

Comando:

```bash
python -m pytest -q
```

Resultado desta revisão:

```text
15 passed
```

## Testes manuais para a integração final

| ID | Cenário | Resultado esperado |
|---|---|---|
| TM-001 | Abrir `http://127.0.0.1:8000/docs` | Swagger exibe `/health`, `/ask` e schemas |
| TM-002 | Iniciar Streamlit com a API ativa | Interface abre e consulta `/ask` |
| TM-003 | Desligar a FastAPI e tentar consultar | Interface apresenta erro de conexão compreensível |
| TM-004 | Consultar sem `OPENAI_API_KEY` | Recuperação local retorna fontes e trechos |
| TM-005 | Executar pipeline → índice → API → Streamlit | Fluxo ponta a ponta concluído sem erro |
