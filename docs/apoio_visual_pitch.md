# Apoio visual — pitch técnico (5 minutos)

## Tela 1 — Problema e estado inicial

**Sistema gerado por IA entregue como aparentemente pronto.**

- primeira execução podia falhar por diretório SQLite inexistente;
- sem Poppler: 0 páginas OCR e 75 registros;
- com OCR funcionando: 7 páginas OCR, mas execução observada com 82/100 registros;
- documentação possuía resultados antigos.

## Tela 2 — Arquitetura auditada

`PDF → pypdf/Tesseract → validação → SQLite → analytics/chunks → embeddings/Chroma → RAG → FastAPI → Streamlit`

Ponto central da correção: separar **100 registros extraídos** de **90 atendimentos únicos**, preservando os 10 duplicados para auditoria/indicadores sem violar a unicidade do protocolo.

## Tela 3 — Principal defeito e correção

**P0 — perda de dados.**

O debug do OCR mostrou 25 registros digitalizados (`4+4+4+4+4+4+1`), mas a execução não entregava todos. Após a correção:

```text
4 documentos
27 páginas
7 páginas OCR
100 registros
90 atendimentos únicos
10 duplicados
```

Reexecutar o pipeline continua retornando 100 registros.

## Tela 4 — Testes e requisitos

- 30 testes automatizados aprovados;
- teste real dos quatro PDFs oficiais;
- CRUD/SQLite, validação, indicadores, ViaCEP tolerante a falha;
- filtros categoria/protocolo;
- FastAPI `/health` e `/ask`;
- Streamlit e modo local sem OpenAI.

## Tela 5 — Demonstração

1. `python -m src.main --reset`
2. mostrar `output/indicadores.json` e gráficos;
3. `python -m src.main --indexar`
4. abrir FastAPI `/docs` e testar `/ask`;
5. abrir Streamlit, fazer pergunta e mostrar fontes;
6. concluir com limitação: OCR pode distorcer caracteres, portanto campos sem evidência são marcados como inválidos em vez de serem inventados.
