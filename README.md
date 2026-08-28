# Sistema Inteligente de Processamento e Consulta de Atendimentos

Projeto do **Desafio 02 — Introdução a Python para IA (FIC_DEV)**. A aplicação processa documentos de atendimentos, persiste os dados, gera indicadores, cria um índice vetorial e disponibiliza consulta semântica por linha de comando, FastAPI e Streamlit.

## Equipe

- Pedro Gomes
- Marcos Vinicius
- Diego Leite


## Arquitetura

Fluxo principal:

```text
PDFs
  ↓
Extração direta / OCR
  ↓
Limpeza, validação e classificação
  ↓
SQLite / SQLAlchemy
  ├──→ Analytics / CSV / JSON / PNG
  ↓
Chunking / Embeddings
  ↓
ChromaDB
  ↓
RAG / recuperação local
  ↓
FastAPI
  ↓
Streamlit
```

O diagrama técnico está em [`docs/diagramas/arquitetura_sistema.svg`](docs/diagramas/arquitetura_sistema.svg).

## Estrutura

```text
desafio_final_python_ia/
├── README.md
├── requirements.txt
├── pytest.ini
├── .env.example
├── .gitignore
├── config.json
├── data/
├── database/
├── output/
├── docs/
│   ├── diagnostico_inicial.md
│   ├── catalogo_defeitos.md
│   ├── matriz_testes.md
│   ├── plano_melhorias.md
│   └── diagramas/
├── src/
└── tests/
```

## Pré-requisitos

- Python compatível com as dependências de `requirements.txt`;
- `venv`;
- Poppler;
- Tesseract OCR com suporte ao idioma português;
- acesso à internet quando forem usados serviços externos, download inicial de modelos ou OpenAI.

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install poppler-utils tesseract-ocr tesseract-ocr-por
```

## Ambiente virtual

### Linux

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

## Variáveis de ambiente

Exemplo de `.env`:

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
APP_ENV=development
API_BASE_URL=http://127.0.0.1:8000
```

- `OPENAI_API_KEY`: opcional. Sem chave, a aplicação utiliza recuperação local.
- `OPENAI_MODEL`: modelo usado no RAG quando houver chave.
- `API_BASE_URL`: endereço da FastAPI consumido pelo Streamlit.

O arquivo `.env` está no `.gitignore` e não deve ser versionado.

## Execução do pipeline

Processar os documentos:

```bash
python -m src.main
```

Processar e criar/atualizar o índice vetorial:

```bash
python -m src.main --indexar
```

Consulta por linha de comando:

```bash
python -m src.main --pergunta "Quais problemas mencionam instalação do Python?" --top-k 5
```

Filtro opcional por categoria:

```bash
python -m src.main --pergunta "Quais atendimentos tratam de senha?" --top-k 5 --categoria "Acesso e senha"
```

## FastAPI

Iniciar:

```bash
uvicorn src.api:app --reload
```

Endpoints:

```text
GET  /health
POST /ask
```

Documentação interativa:

```text
http://127.0.0.1:8000/docs
```

Exemplo de requisição:

```json
{
  "pergunta": "Quais problemas mencionam instalação do Python?",
  "top_k": 5,
  "categoria": null
}
```

A resposta contém a resposta gerada/recuperada e as fontes com protocolo, documento, página, categoria, conteúdo e similaridade quando disponíveis.

Entradas inválidas são rejeitadas pela validação do FastAPI. Falhas internas da recuperação retornam HTTP `503` sem expor detalhes internos da aplicação.

## Streamlit

Com a FastAPI em execução em outro terminal:

```bash
streamlit run src/app_streamlit.py
```

A interface:

- recebe a pergunta;
- permite configurar a quantidade de fontes;
- permite filtro opcional de categoria;
- consome `POST /ask`;
- apresenta resposta e fontes;
- mostra o trecho recuperado de cada fonte;
- apresenta mensagem compreensível quando a API não estiver disponível.

Para executar a API em outro endereço, altere `API_BASE_URL` no `.env`.

## Decisões de validação, limpeza, chunking e deduplicação

O código-base mantém o texto original e utiliza versões normalizadas para processamento e recuperação. A validação usa funções e expressões regulares para campos estruturados. O protocolo é utilizado como referência de deduplicação. O chunking preserva metadados de rastreabilidade, como documento, página, protocolo e categoria, e os parâmetros de tamanho/sobreposição são configuráveis em `config.json`.

Essas decisões devem permanecer consistentes.

## Modo sem chave da OpenAI

A chave da OpenAI não é obrigatória para iniciar a aplicação. Sem `OPENAI_API_KEY`, o sistema recupera os trechos semanticamente mais próximos e apresenta as fontes. Com a chave configurada, a camada RAG pode gerar uma síntese baseada no contexto recuperado.

## Testes

Executar:

```bash
python -m pytest -q
```

ou:

```bash
pytest -q
```

A matriz e os resultados desta revisão estão em [`docs/matriz_testes.md`](docs/matriz_testes.md).

## Documentação da auditoria

- Diagnóstico inicial: [`docs/diagnostico_inicial.md`](docs/diagnostico_inicial.md)
- Catálogo de defeitos: [`docs/catalogo_defeitos.md`](docs/catalogo_defeitos.md)
- Matriz de testes: [`docs/matriz_testes.md`](docs/matriz_testes.md)
- Plano de melhorias: [`docs/plano_melhorias.md`](docs/plano_melhorias.md)
- Diagrama técnico: [`docs/diagramas/arquitetura_sistema.svg`](docs/diagramas/arquitetura_sistema.svg)

## Limitações conhecidas nesta revisão

- o endpoint `/health` verifica a disponibilidade do serviço HTTP e o modo de operação, não faz uma verificação pesada de banco/modelo/ChromaDB;
- os testes automatizados da API e da interface utilizam mocks para evitar dependência de rede, modelos externos e chave da OpenAI;
- o fluxo ponta a ponta deve ser novamente executado após o merge de todas as alterações da equipe e a regeneração do banco, índice vetorial e arquivos de saída.

## Uso de ferramentas de Inteligência Artificial

Foi utilizado **ChatGPT** como apoio à auditoria dos requisitos, revisão da camada HTTP/interface, elaboração de casos de teste e organização da documentação.

### Finalidades

- comparar o código recebido com os requisitos do desafio;
- identificar falhas de configuração, tratamento de erros e testabilidade;
- propor casos de teste para `GET /health`, `POST /ask` e integração Streamlit → FastAPI;
- revisar a documentação de instalação e execução.

### Solicitações relevantes

- análise dos documentos do desafio e do código-base;
- revisão de `src/api.py`, `src/app_streamlit.py`, `src/main.py` e testes;
- sugestões de tratamento de erros e configuração da URL da API;
- criação/revisão de testes automatizados.

### Sugestões aceitas

- tornar o endereço da API configurável por `API_BASE_URL`;
- separar a comunicação HTTP em `src/ui_client.py`;
- exibir o conteúdo das fontes recuperadas no Streamlit;
- definir modelos de resposta Pydantic;
- ampliar a cobertura de testes da API, cliente HTTP e integração local;
- adicionar `pytest.ini` para execução previsível dos testes.

### Sugestões rejeitadas

- executar chamadas reais da OpenAI nos testes automatizados, para não depender de segredo, rede, custo ou comportamento externo;
- transformar `/health` em uma chamada pesada que carregasse banco, embeddings e modelo a cada requisição.

### Limitações observadas e revisão

Sugestões de IA não foram consideradas corretas sem verificação. As alterações foram revisadas no código, compiladas e validadas por testes automatizados pela equipe.
