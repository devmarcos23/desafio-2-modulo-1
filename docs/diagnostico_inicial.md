# Diagnóstico inicial

Este registro documenta o estado encontrado antes das correções na camada de API, interface e integração.

## Arquivos inspecionados

- `src/api.py`
- `src/app_streamlit.py`
- `src/main.py`
- `tests/test_api.py`
- `README.md`
- `.env.example`
- `.gitignore`

## Estado inicial

### FastAPI

O projeto já possuía `GET /health`, `POST /ask`, validação básica com Pydantic e conversão de falhas do `/ask` para HTTP 503.

Foram encontrados os seguintes pontos:

- não havia modelos explícitos para as respostas da API;
- o `/ask` devolvia o nome da exceção interna ao cliente;
- a falha não era registrada por logger;
- os testes cobriam apenas `/health` e rejeição de uma pergunta curta.

### Streamlit

A interface já enviava perguntas para `POST /ask` e mostrava resposta e fontes.

Foram encontrados:

- endereço `http://127.0.0.1:8000/ask` fixo no código;
- o conteúdo dos trechos recuperados não era exibido;
- a interface permitia enviar perguntas menores que o limite aceito pela API;
- mensagens de erro exibiam diretamente detalhes de `requests`;
- comunicação HTTP e interface estavam no mesmo módulo, dificultando testes isolados.

### Testes

Antes das alterações, a suíte possuía 6 testes e a execução abaixo foi bem-sucedida:

```bash
python -m pytest -q
```

Resultado registrado:

```text
6 passed
```

Também foi observado que a execução direta com `pytest -q` podia falhar na coleta em ambientes onde a raiz do projeto não era adicionada ao caminho de importação.

## Resultado após as correções desta revisão

Foram adicionados modelos de resposta, logging seguro, configuração por variável de ambiente, cliente HTTP separado, exibição dos trechos recuperados e novos testes.

A suíte final desta revisão apresentou:

```text
15 passed
```
