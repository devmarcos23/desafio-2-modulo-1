# 📊 FIC_DEV — Programador de Sistemas com IA | COD 001

## DESAFIO FINAL

### Auditoria, correção e implantação de um sistema gerado por Inteligência Artificial

**Módulo:** COD 001 — Introdução a Python para IA  
**Instituição:** SECITECI / Escola Técnica Estadual de Cuiabá  
**Turma:** Vespertino  
**Modalidade:** Equipe de 03 (três) discentes
**Versão de entrega:** `v1.0.0`

---

## 👨‍💻 Identificação

### Alunos

- **Diego Assunção**
- **Pedro Gomes**
- **Marcos Vinicius**

---

## 🎯 Objetivo

Este projeto apresenta a versão **auditada, corrigida, testada e documentada** do sistema fornecido no Desafio 02.

A aplicação processa documentos PDF de atendimentos, realiza extração direta ou OCR, valida e normaliza os registros, mantém o histórico em SQLite, produz indicadores e gráficos, gera chunks e embeddings, persiste a indexação vetorial no ChromaDB e disponibiliza consulta semântica/RAG por linha de comando, FastAPI e Streamlit.

A versão final foi validada com os quatro PDFs oficiais, totalizando **4 documentos, 27 páginas e 100 registros extraídos**, sendo **25 registros provenientes das 7 páginas processadas por OCR**. A reexecução do pipeline preserva os mesmos resultados e mantém os arquivos de saída consistentes com o histórico persistido.

---

## 📌 Situação-problema

O sistema original foi produzido com apoio de Inteligência Artificial e entregue como uma solução aparentemente completa, porém sem validação integral.

Durante a auditoria foram avaliados:

- processamento de PDFs digitais e digitalizados;
- OCR;
- extração e validação dos registros;
- normalização dos dados;
- identificação de duplicidades;
- persistência com SQLite e SQLAlchemy;
- consulta de CEP;
- indicadores e visualizações;
- processamento de linguagem natural;
- chunking e metadados;
- embeddings e busca semântica;
- ChromaDB;
- RAG;
- FastAPI;
- Streamlit;
- testes automatizados;
- documentação e reprodutibilidade da aplicação.

Os defeitos encontrados foram registrados, priorizados e tratados de acordo com o impacto no funcionamento do MVP.

---

# 👥 Divisão das responsabilidades

## 👨‍💻 Marcos Vinicius — Entrada de dados, PDF, OCR e validação

Responsável principalmente pelas funcionalidades relacionadas ao processamento inicial dos documentos e à extração dos dados.

### Principais atividades

- processamento dos PDFs;
- extração direta de texto;
- OCR com Tesseract;
- integração com Poppler/pdf2image;
- segmentação dos atendimentos;
- validação dos registros;
- normalização dos campos;
- tratamento das distorções provenientes do OCR;
- identificação de dados inválidos e incompletos;
- identificação de duplicidades;
- apoio na integração do pipeline.

---

## 👨‍💻 Diego Assunção — Banco, Analytics, Embeddings e RAG

Responsável principalmente pelas funcionalidades relacionadas à persistência, análise dos dados, embeddings, busca semântica e RAG.

### Principais arquivos

- `src/models.py`
- `src/database.py`
- `src/analytics.py`
- `src/embeddings.py`
- `src/vector_store.py`
- `src/indexer.py`
- `src/rag.py`

### Principais atividades

- modelagem do banco SQLite;
- persistência dos documentos e atendimentos;
- controle de unicidade dos protocolos;
- persistência dos chunks;
- registro de erros de processamento;
- cálculo dos indicadores;
- exportação de dados em CSV e JSON;
- geração dos gráficos;
- geração e validação dos embeddings;
- indexação persistente no ChromaDB;
- busca por similaridade;
- recuperação de contexto;
- integração com RAG;
- modo de recuperação local sem OpenAI;
- testes dos componentes de banco e recuperação semântica.

---

## 👨‍💻 Pedro Gomes — API, Streamlit, integração, testes e documentação

Responsável pelas funcionalidades relacionadas à disponibilização da aplicação, integração dos componentes, testes e documentação técnica.

### Principais atividades

- API com FastAPI;
- endpoints `GET /health` e `POST /ask`;
- validação das entradas e respostas HTTP;
- interface Streamlit;
- cliente HTTP da interface;
- integração entre pipeline, banco, ChromaDB, RAG, API e interface;
- testes da API e testes de integração;
- validação ponta a ponta;
- tratamento de erros de conexão;
- documentação de instalação e execução;
- documentação técnica e apoio visual da entrega.

---

# 🏗️ Arquitetura

O detalhamento da arquitetura está disponível em [`docs/arquitetura.md`](docs/arquitetura.md).

Fluxo principal:

```text
PDF
 ↓
Extração direta / OCR
 ↓
Segmentação dos atendimentos
 ↓
Validação e normalização
 ↓
SQLite / SQLAlchemy
 ↓
Indicadores + Chunks
 ↓
Embeddings
 ↓
ChromaDB
 ↓
RAG
 ↓
FastAPI
 ↓
Streamlit
```

---

# 📁 Estrutura do projeto

```text
desafio-2-modulo-1/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── config.json
├── pytest.ini
├── data/
│   ├── auxiliares/
│   │   ├── categorias.json
│   │   └── config_original.json
│   └── pdfs/
│       ├── atendimentos_digitais.pdf
│       ├── atendimentos_digitalizados.pdf
│       ├── atendimentos_duplicados.pdf
│       └── atendimentos_incompletos.pdf
├── database/
│   └── atendimentos.db
├── output/
│   ├── atendimentos_processados.csv
│   ├── indicadores.json
│   ├── processamento.log
│   └── graficos/
├── docs/
│   ├── arquitetura.md
│   ├── diagnostico_inicial.md
│   ├── catalogo_defeitos.md
│   ├── matriz_testes.md
│   ├── plano_melhorias.md
│   └── apoio_visual_pitch.md
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── pdf_processor.py
│   ├── ocr_processor.py
│   ├── text_processor.py
│   ├── validation.py
│   ├── cep_client.py
│   ├── analytics.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── indexer.py
│   ├── rag.py
│   ├── api.py
│   ├── ui_client.py
│   └── app_streamlit.py
└── tests/
```

---

# 🛠️ Tecnologias utilizadas

- Python;
- pypdf;
- pdf2image;
- Poppler;
- Tesseract OCR;
- Regex;
- NLTK;
- Requests;
- SQLite;
- SQLAlchemy;
- Pandas;
- NumPy;
- Matplotlib;
- sentence-transformers;
- ChromaDB;
- LangChain;
- OpenAI;
- FastAPI;
- Uvicorn;
- Streamlit;
- Pytest;
- Git / GitHub.

---

# ⚙️ Pré-requisitos

- Python **3.11+**;
- Tesseract OCR com o idioma `por` instalado;
- Poppler com `pdftoppm` e `pdfinfo` disponíveis;
- acesso à internet quando necessário para ViaCEP, download inicial do modelo de embeddings ou OpenAI.

## Windows

Instalação com `winget`:

```powershell
winget install --id tesseract-ocr.tesseract -e
winget install --id oschwartz10612.Poppler -e
```

Validação:

```powershell
tesseract --version
tesseract --list-langs
pdftoppm -h
```

O resultado de `tesseract --list-langs` deve incluir:

```text
por
```

Caso os executáveis estejam instalados mas não sejam reconhecidos pelo terminal, as respectivas pastas devem estar disponíveis no `PATH` do sistema.

## Linux — Debian/Ubuntu

```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-por poppler-utils
```

---

# 📦 Ambiente virtual e dependências

## Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

# 🔐 Variáveis de ambiente

Crie o arquivo `.env` com base em `.env.example`:

```text
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
APP_ENV=development
API_BASE_URL=http://127.0.0.1:8000
```

A chave `OPENAI_API_KEY` é opcional. Sem ela, a aplicação permanece funcional no modo `recuperacao_local`, apresentando os chunks e as fontes recuperadas.

O arquivo `.env` é ignorado pelo Git e nenhuma chave de API é armazenada diretamente no código-fonte.

---

# ▶️ Execução

## Pipeline — reconstrução completa

```powershell
python -m src.main --reset
```

## Pipeline — execução normal

```powershell
python -m src.main
```

O diretório do banco SQLite é criado automaticamente quando necessário.

## Pipeline com indexação vetorial

```powershell
python -m src.main --indexar
```

Na primeira indexação, o `sentence-transformers` pode baixar o modelo definido em `config.json`.

## Consulta pela linha de comando

```powershell
python -m src.main --pergunta "Quais atendimentos apresentam problema com senha?"
```

## FastAPI

```powershell
python -m uvicorn src.api:app --reload
```

Endpoints:

- Health: `GET http://127.0.0.1:8000/health`
- Swagger: `http://127.0.0.1:8000/docs`
- Consulta: `POST http://127.0.0.1:8000/ask`

Exemplo de requisição:

```json
{
  "pergunta": "Quais atendimentos apresentam problema com senha?",
  "top_k": 5,
  "categoria": "Acesso e senha"
}
```

Os filtros `categoria` e `protocolo` são opcionais.

## Streamlit

Com a FastAPI em execução em outro terminal:

```powershell
streamlit run src/app_streamlit.py
```

A interface apresenta:

- pergunta em linguagem natural;
- resposta do sistema;
- protocolo;
- documento de origem;
- página;
- categoria;
- pontuação de similaridade;
- conteúdo dos trechos utilizados como fonte.

---

# 🧪 Testes e validações

Execução da suíte:

```powershell
python -m pytest -q
```

Resultado da versão de entrega:

### Testes automatizados

A versão final foi validada com a suíte completa de testes:

```text
30 passed in 34.39s
```

A suíte inclui testes para:

- configuração;
- validação e normalização;
- SQLite e SQLAlchemy;
- analytics;
- cliente de CEP;
- API;
- cliente da interface;
- indexação;
- RAG;
- integração do pipeline com os PDFs oficiais.

Com Tesseract e Poppler instalados, o teste de integração confirma:

```text
4 documentos
27 páginas
7 páginas OCR
25 registros OCR
100 registros extraídos
10 duplicados
```

A reexecução também é testada para garantir a manutenção dos resultados e a ausência de perda do histórico.

A matriz detalhada está em [`docs/matriz_testes.md`](docs/matriz_testes.md).

---

# 📋 Requisitos funcionais — RF01 a RF17

| Requisito | Implementação da versão final |
|---|---|
| **RF01 — Inicialização e configuração** | CLI por `python -m src.main`, ambiente virtual, `requirements.txt`, `config.json`, `.env.example` e segredos fora do Git |
| **RF02 — Detecção e extração de PDFs** | Detecção com `pathlib`, extração por `pypdf`, decisão de extração por página e registro do método utilizado |
| **RF03 — OCR** | Rasterização com Poppler/pdf2image, OCR com Tesseract, texto bruto e limpo, tratamento e registro de falhas |
| **RF04 — Extração, validação e classificação** | Regex, validação de protocolo/data/e-mail/CEP/tempo, normalização e classificação em válido, incompleto, inválido ou duplicado |
| **RF05 — Processamento de linguagem natural** | Normalização, tokenização, remoção de stopwords e stemming em português como processo equivalente à lematização |
| **RF06 — Persistência com SQLite e SQLAlchemy** | Modelos, sessões, transações, CRUD controlado, unicidade de protocolo e recriação/reuso previsível do banco |
| **RF07 — Consumo de API HTTP** | Integração ViaCEP com `requests`, timeout, tratamento de códigos HTTP e continuidade em falhas de rede |
| **RF08 — Análise de dados** | Pandas + NumPy, agregações e todos os indicadores obrigatórios |
| **RF09 — Visualização e exportação** | CSV, JSON, log e gráficos PNG com títulos, eixos e dimensões adequadas |
| **RF10 — Chunking e metadados** | Tamanho e sobreposição configuráveis, IDs únicos e metadados de documento, página, protocolo e categoria |
| **RF11 — Embeddings e busca semântica** | `sentence-transformers`, similaridade de cosseno e retorno top-k com fontes e pontuações |
| **RF12 — ChromaDB** | Coleção persistente, sincronização sem duplicidade e filtros por categoria e protocolo |
| **RF13 — RAG** | Recuperação de chunks, contexto limitado, resposta baseada nas fontes e indicação de insuficiência documental |
| **RF14 — OpenAI API e LangChain** | Chave por variável de ambiente, cadeia de resposta, tratamento de falha e modo local sem chamada ao modelo |
| **RF15 — FastAPI** | `GET /health`, `POST /ask`, validação, códigos HTTP adequados e documentação `/docs` |
| **RF16 — Streamlit** | Campo de pergunta, consumo de `/ask`, resposta, fontes e tratamento compreensível de erros de conexão |
| **RF17 — Controle de versão com Git** | `.gitignore`, commits organizados, branches de desenvolvimento, integração da versão final e versão de entrega `v1.0.0` |

---

# 🔒 Requisitos não funcionais

A versão final atende aos requisitos não funcionais do desafio por meio das seguintes decisões:

- arquitetura organizada em módulos com responsabilidades definidas;
- type hints e docstrings em funções relevantes;
- erros de registros ou páginas isolados sem interromper todo o pipeline;
- mensagens e logs úteis para diagnóstico;
- arquivos textuais gerados em UTF-8;
- código organizado conforme convenções Python/PEP 8;
- ausência de segredos no código e no repositório;
- ausência de caminhos absolutos dependentes do computador dos integrantes;
- banco e índice vetorial reproduzíveis;
- README com instruções completas para reprodução da aplicação em outro ambiente.

---

# 🧩 Decisões de processamento

## Extração e OCR

Páginas com texto selecionável suficiente são processadas diretamente com `pypdf`. Páginas sem texto suficiente são convertidas em imagem por `pdf2image`/Poppler e submetidas ao Tesseract.

O texto bruto do OCR é preservado, enquanto uma versão normalizada é utilizada para extração e recuperação.

## Validação e normalização

São tratados e validados:

- protocolo;
- data;
- solicitante;
- e-mail;
- categoria;
- descrição;
- tempo;
- status;
- CEP.

Marcadores como `[vazio]` são tratados como ausência. Pequenas distorções do OCR em protocolos são normalizadas sem substituir o texto original.

Classificações possíveis:

```text
valido
incompleto
invalido
duplicado
```

Os motivos de classificação permanecem disponíveis no banco, no CSV e nos registros de processamento.

## Deduplicação

`Atendimento.protocolo` possui unicidade. Protocolos repetidos são classificados como `duplicado` e não geram um novo atendimento persistido.

O histórico de extração mantém os registros duplicados para que os indicadores representem corretamente os **100 registros oficiais**.

Registros sem protocolo válido recebem identificadores técnicos internos na persistência, evitando falso reconhecimento de duplicidade entre registros diferentes.

## CEP

CEPs válidos podem ser enriquecidos pelo ViaCEP. A chamada utiliza timeout e tratamento de falhas. Se a API estiver indisponível, o pipeline continua normalmente.

## NLP

O texto utilizado na recuperação passa por:

```text
normalização
→ tokenização
→ remoção de stopwords
→ stemming em português
```

O texto original permanece preservado.

## Chunking

Parâmetros configurados em `config.json`:

- **Tamanho:** 500 caracteres;
- **Sobreposição:** 80 caracteres.

Cada chunk mantém em seus metadados:

- protocolo;
- documento;
- página;
- categoria.

## Embeddings e ChromaDB

Modelo utilizado:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

Os vetores são normalizados e a recuperação utiliza similaridade de cosseno. A coleção do ChromaDB é persistente e evita indexações duplicadas.

São suportados filtros por:

- categoria;
- protocolo.

## RAG e recuperação local

Com `OPENAI_API_KEY` configurada, o LangChain utiliza os trechos recuperados para produzir uma resposta fundamentada no contexto.

Sem a chave, o sistema utiliza o modo:

```text
recuperacao_local
```

Nesse modo, os chunks semanticamente mais relevantes e suas fontes continuam sendo apresentados ao usuário.

Quando os documentos não sustentam uma resposta, a aplicação informa que não há informação suficiente.

---

# 📊 Resultados com os dados oficiais

A validação final utilizou os quatro PDFs disponibilizados no desafio.

| Indicador | Resultado |
|---|---:|
| Documentos processados | **4** |
| Páginas processadas | **27** |
| Páginas processadas por OCR | **7** |
| Registros extraídos | **100** |
| Registros provenientes do OCR | **25** |
| Atendimentos únicos persistidos | **90** |
| Duplicados | **10** |
| Chunks persistidos no SQLite | **90** |
| Registros válidos | **53** |
| Registros inválidos | **32** |
| Registros incompletos | **5** |
| Percentual de páginas processadas por OCR | **25,93%** |

Distribuição do PDF digitalizado:

```text
Página 1: 4 registros
Página 2: 4 registros
Página 3: 4 registros
Página 4: 4 registros
Página 5: 4 registros
Página 6: 4 registros
Página 7: 1 registro
----------------------
Total:   25 registros
```

As distorções naturais do OCR podem tornar campos específicos inválidos mesmo quando o atendimento foi recuperado corretamente. Esses registros não são descartados: permanecem armazenados com a respectiva classificação e os motivos identificados.

Para manter a medição principal reproduzível e independente de disponibilidade externa, o enriquecimento de município/UF pelo ViaCEP é tratado separadamente. A integração HTTP é coberta por testes e falhas do serviço não interrompem o pipeline.

---

# 📈 Arquivos de saída

O processamento gera:

```text
output/
├── atendimentos_processados.csv
├── indicadores.json
├── processamento.log
└── graficos/
```

Entre os indicadores produzidos estão:

- total de documentos e páginas;
- quantidade e percentual por classificação;
- quantidade por categoria;
- quantidade por status;
- quantidade por município/UF;
- quantidade por método de extração;
- média, mediana e desvio-padrão do tempo;
- categoria com maior volume;
- categoria com maior tempo médio;
- percentual de páginas processadas por OCR;
- erros por tipo;
- erros por etapa.

Os gráficos incluem, entre outros:

- atendimentos por categoria;
- tempo médio por categoria;
- atendimentos por status;
- registros por classificação;
- atendimentos por método de extração;
- atendimentos por município, quando houver enriquecimento disponível.

---

# 📝 Documentação técnica e auditoria

Os documentos de apoio da versão final estão em `docs/`:

- [`docs/arquitetura.md`](docs/arquitetura.md) — arquitetura e fluxo da aplicação;
- [`docs/diagnostico_inicial.md`](docs/diagnostico_inicial.md) — estado encontrado antes das correções;
- [`docs/catalogo_defeitos.md`](docs/catalogo_defeitos.md) — defeitos, causas, prioridades e correções;
- [`docs/matriz_testes.md`](docs/matriz_testes.md) — estratégia e resultados dos testes;
- [`docs/plano_melhorias.md`](docs/plano_melhorias.md) — crítica técnica e melhorias priorizadas;
- [`docs/apoio_visual_pitch.md`](docs/apoio_visual_pitch.md) — apoio visual para apresentação técnica.

---

# ⚠️ Limitações conhecidas

- O OCR pode produzir caracteres incorretos em campos específicos. O sistema prioriza registrar a inconsistência em vez de inferir ou inventar um valor.
- Município e UF dependem do acesso ao ViaCEP. Em indisponibilidade de rede, o processamento continua sem enriquecimento.
- O primeiro uso de `sentence-transformers` pode exigir download do modelo configurado.
- `GET /health` verifica a disponibilidade da API. A disponibilidade prática do índice vetorial é validada durante a consulta em `POST /ask`.

---

# 🔀 Controle de versão

O projeto utilizou branches separadas para o desenvolvimento e integração das funcionalidades.

### OCR e validação

```text
feature/ocr-validation
```

### Banco, analytics, embeddings e RAG

```text
feature/database-rag
```

### API e Streamlit

```text
feature/api-streamlit
```

### Integração

```text
release
```

### Branch principal

```text
main
```

### Versão da entrega

```text
v1.0.0
```

O histórico de commits, branches, merges e tag é mantido no repositório Git. A pasta `.git` não faz parte do conteúdo do ZIP da aplicação.

---

# 🤖 Uso de ferramentas de IA

Durante a auditoria e desenvolvimento foi utilizado **ChatGPT** como ferramenta de apoio.

## Finalidades

A ferramenta foi utilizada para:

- interpretação dos requisitos do desafio;
- análise de mensagens de erro e stack traces;
- apoio à auditoria do código;
- investigação de falhas no OCR e pipeline;
- revisão de SQLite/SQLAlchemy;
- revisão de FastAPI e Streamlit;
- sugestões de testes de regressão;
- análise dos requisitos funcionais e não funcionais;
- revisão da documentação técnica.

## Solicitações relevantes

Entre as solicitações realizadas estiveram:

- analisar os documentos oficiais e o projeto arquivo por arquivo;
- investigar a diferença entre registros reconhecidos pelo OCR e registros mantidos pelo pipeline;
- comparar a implementação com RF01–RF17;
- revisar a integração dos componentes;
- revisar o README e os documentos de entrega;
- propor testes capazes de reproduzir e impedir regressões dos defeitos encontrados.

## Sugestões incorporadas após validação

Entre as sugestões incorporadas após análise e teste estão:

- criação automática do diretório do SQLite;
- manutenção do histórico de todos os registros extraídos;
- reprocessamento previsível de documentos;
- preservação dos outputs em reexecuções;
- integração tolerante a falhas do ViaCEP;
- cálculo do percentual de OCR por página;
- diferenciação correta entre protocolo ausente e protocolo duplicado;
- filtro do ChromaDB por protocolo;
- limite de contexto no RAG;
- URL configurável para a API;
- mensagens de erro compreensíveis na interface;
- ampliação da suíte de testes.

## Sugestões rejeitadas ou adaptadas

Não foram aplicadas correções que inferissem valores ilegíveis sem evidência no documento original. Por exemplo, quando o OCR não permite determinar de maneira confiável uma categoria ou outro campo, o sistema registra a inconsistência em vez de criar uma informação artificial.

As sugestões recebidas foram adaptadas às regras e aos dados oficiais antes de serem incorporadas ao código.

## Revisão e validação

As alterações incorporadas foram verificadas por leitura do código, execução dos módulos e testes automatizados. A versão final foi validada com os quatro PDFs oficiais e recuperou os **100 registros previstos**, além de passar pela suíte de **30 testes**.

---

# 📦 Entregáveis

A entrega do Desafio 02 é composta por:

1. código corrigido e configurável;
2. arquivos de saída gerados com os dados oficiais;
3. banco SQLite e índice vetorial reproduzíveis;
4. documentação técnica da aplicação;
5. catálogo de defeitos;
6. crítica e plano de melhorias;
7. apoio visual do pitch técnico;
8. vídeo de aproximadamente 5 minutos com demonstração ponta a ponta.

---

# 👨‍💻 Autores

- **Diego Assunção**
- **Pedro Gomes**
- **Marcos Vinicius**

**Turma:** Vespertino — FIC_DEV | COD 001 — Introdução a Python para IA
**Instituição:** SECITECI / Escola Técnica Estadual de Cuiabá
