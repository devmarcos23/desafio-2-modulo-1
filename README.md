# 📊 Sistema de Análise e RAG de Atendimentos

Sistema desenvolvido em Python para processamento, validação, persistência, análise e consulta semântica de dados de atendimentos de suporte técnico.

A aplicação realiza a leitura de documentos PDF, extração direta de texto e encaminhamento de páginas para OCR quando necessário, validação e classificação dos registros, tratamento de duplicidades, persistência em banco SQLite, geração de indicadores estatísticos, criação de embeddings, indexação vetorial no ChromaDB e consultas utilizando busca semântica e RAG.

## 👨‍💻 Identificação

Alunos:

- **Diego Assunção**
- **Pedro Gomes**
- **Marcos Vinicius**

Curso/Módulo: FIC_DEV — Módulo Python para IA (Aulas 11 a 17)
Instituição: SECITECI / Escola Técnica Estadual de Cuiabá
Turma: Vespertino

## 🎯 Objetivo

O objetivo do desafio é assumir tecnicamente um sistema produzido com apoio de Inteligência Artificial, realizar sua auditoria, identificar problemas, corrigir defeitos, testar seu funcionamento e transformá-lo em um MVP local auditado, corrigido, testado e documentado.

A equipe deve verificar se o sistema realmente funciona antes de considerar qualquer parte da implementação como correta.

---

## 📌 Situação-problema

Uma ferramenta de Inteligência Artificial produziu um sistema para processamento de documentos de atendimentos.

A solução possui funcionalidades para:

- processamento de documentos PDF;
- extração direta de texto;
- OCR;
- validação dos registros;
- normalização dos dados;
- identificação de duplicidades;
- persistência em banco de dados;
- geração de indicadores;
- geração de gráficos;
- criação de embeddings;
- indexação vetorial;
- busca semântica;
- RAG;
- API;
- interface Streamlit.

O sistema recebido pode apresentar erros funcionais, problemas de integração, falhas de configuração e decisões inadequadas.

A equipe assumiu a responsabilidade de analisar, executar, corrigir, testar e documentar a solução.

---
## 👥 Divisão das responsabilidades
### 👨‍💻 Marcos Vinicius — Entrada de dados + PDF + OCR

Responsável pelas funcionalidades de aplicação e interface, conforme a divisão adotada pela equipe.

Principais atividades:

- API
- endpoints
- integração da aplicação
- interface Streamlit
- testes de integração
- execução e validação da aplicação.
### 👨‍💻 Diego Assunção — Banco, Analytics, Embeddings e RAG

Responsável principalmente pela camada de persistência, análise e recuperação semântica:

src/models.py
src/database.py
src/analytics.py
src/embeddings.py
src/vector_store.py
src/rag.py

Também participou da integração dessas funcionalidades com o pipeline.

### Principais atividades
- Modelagem do banco SQLite
- Persistência dos documentos
- Persistência dos atendimentos
- Controle de unicidade dos protocolos
- Persistência dos chunks
- Registro de erros
- Criação dos indicadores
- Exportação CSV/JSON
- Geração dos gráficos
- Geração dos embeddings
- Indexação no ChromaDB
- Busca semântica
- Integração com RAG
- Testes da recuperação semântica
- Correções de integração entre banco, pipeline e analytics.
### 👨‍💻 Pedro Gomes — API + Streamlit + Integração + Teste + Documentação

Responsável pelas funcionalidades de processamento e tratamento dos documentos, conforme a divisão adotada pela equipe.

Principais atividades:

- processamento dos PDFs
- extração de texto
- OCR
- validação
- normalização
- tratamento dos registros
- identificação de dados inválidos
- apoio na integração do pipeline.

## 📌 Requisitos Funcionais
### RF01 — Processamento dos documentos

O sistema deverá processar os documentos PDF disponíveis no diretório configurado.

### RF02 — Extração de texto

O sistema deverá realizar extração direta do texto dos documentos utilizando pypdf.

Páginas sem quantidade suficiente de texto deverão ser encaminhadas para OCR.

### RF03 — Validação dos registros

O sistema deverá validar os registros extraídos, classificando-os de acordo com sua qualidade e registrando os motivos das inconsistências.

### RF04 — Tratamento e normalização

O sistema deverá realizar:

- limpeza textual
- normalização dos campos
- padronização das categorias
- conversão de datas
- tratamento de tempos
- identificação de valores inválidos
- identificação de duplicidades.
### RF05 — Persistência em banco de dados

O sistema deverá armazenar os documentos processados em banco SQLite utilizando SQLAlchemy.

Deverão ser armazenados dados como:

- nome do documento
- hash SHA-256
- quantidade de páginas
- método de processamento
- quantidade de páginas OCR
- data de processamento.
### RF06 — Persistência dos atendimentos

O sistema deverá armazenar os atendimentos extraídos contendo:

- protocolo
- data
- solicitante
- e-mail
- categoria
- descrição
- solução
- tempo
- status
- CEP
- município
- UF
- classificação
- motivos
- texto original
- texto limpo.
### RF07 — Controle de duplicidade

O sistema deverá identificar protocolos duplicados.

Registros repetidos pelo protocolo deverão ser classificados como duplicados e não deverão ser reinseridos como novos atendimentos.

### RF08 — Registro de erros

O sistema deverá registrar erros encontrados durante o processamento.

Os erros deverão conter informações como:

- documento
- página
- etapa
- tipo do erro
- mensagem
- data/hora.
### RF09 — Geração de indicadores

O sistema deverá calcular indicadores utilizando Pandas e NumPy.

Entre os indicadores estão:

- total de documentos
- total de páginas
- total de registros
- registros por classificação
- percentual por classificação
- registros por categoria
- registros por status
- registros por município
- registros por método de extração
- tempo médio
- tempo mediano
- desvio padrão
- categoria com maior volume
- categoria com maior tempo médio
- tempo médio por categoria
- percentual de páginas processadas por OCR
- erros por tipo
- erros por etapa.
### RF10 — Exportação dos resultados

O sistema deverá gerar arquivos de saída contendo os dados processados e os indicadores.

### Exemplo:

output/
├── atendimentos_processados.csv
├── indicadores.json
├── processamento.log
└── graficos/
### RF11 — Geração de gráficos

O sistema deverá gerar gráficos estatísticos em formato PNG.

Entre os gráficos implementados estão:

- atendimentos por categoria
- atendimentos por status
- tempo médio por categoria
- atendimentos por método de extração
- atendimentos por município
- registros por classificação.
## 🧠 Embeddings e Busca Semântica
### RF12 — Geração de embeddings

O sistema deverá gerar embeddings locais dos chunks utilizando sentence-transformers.

### RF13 — Criação dos chunks

O sistema deverá dividir os textos dos atendimentos em chunks configuráveis.

A configuração utilizada como referência é:

Tamanho do chunk: 500 caracteres
Sobreposição: 80 caracteres
### RF14 — Persistência no ChromaDB

O sistema deverá armazenar os embeddings em uma coleção persistente do ChromaDB.

Os chunks deverão possuir metadados rastreáveis, incluindo:

protocolo
documento
página
categoria
### RF15 — Busca semântica

O sistema deverá receber uma pergunta em linguagem natural, gerar seu embedding e recuperar os chunks semanticamente mais semelhantes.

Exemplo validado:

### Pergunta:
Qual atendimento apresenta problema com o depurador?

### Resultado principal:

Protocolo: AT-032
Categoria: VSCode e ferramentas
Página: 8
Similaridade: 0.4471
## 🤖 RAG
### RF16 — Recuperação de contexto

O sistema deverá recuperar os trechos mais relevantes do ChromaDB para servir como contexto da resposta.

### Fluxo:

Pergunta
↓
Embedding
↓
Busca semântica
↓
ChromaDB
↓
Chunks relevantes
↓
Contexto
### RF17 — Resposta fundamentada

Quando a OPENAI_API_KEY estiver configurada, o sistema poderá utilizar um modelo de linguagem para produzir uma síntese baseada no contexto recuperado.

### RF18 — Modo de recuperação local

Quando não houver OPENAI_API_KEY, o sistema deverá continuar funcionando, apresentando os trechos mais semelhantes e suas respectivas fontes.

Modo utilizado nos testes:

recuperacao_local
### RF19 — Apresentação das fontes

O sistema deverá informar as fontes utilizadas na recuperação, permitindo identificar:

- protocolo
- documento
- página
- categoria
- similaridade.
## 🔒 Requisitos Não Funcionais
### RNF01 — Persistência

Os dados deverão permanecer armazenados no banco SQLite após o encerramento da aplicação.

### RNF02 — Integridade

O banco deverá garantir a integridade dos registros, incluindo a unicidade dos protocolos.

### RNF03 — Rastreabilidade

Os chunks utilizados nas consultas deverão manter informações que permitam identificar sua origem.

### RNF04 — Reprodutibilidade

O banco de dados e o índice vetorial deverão poder ser reproduzidos em outro ambiente seguindo as configurações e instruções do projeto.

### RNF05 — Tolerância a falhas

Falhas durante o OCR ou processamento de um documento não deverão interromper o processamento dos demais documentos.

### RNF06 — Segurança

As chaves de API não deverão ser armazenadas diretamente no código-fonte.

As credenciais deverão ser configuradas por variáveis de ambiente.

### RNF07 — Manutenibilidade

O sistema deverá utilizar arquitetura modular, mantendo separadas as responsabilidades de:

Banco
Analytics
Embeddings
Vector Store
RAG
API
Interface
### RNF08 — Desempenho

A busca semântica deverá utilizar embeddings e índice vetorial para recuperar os conteúdos relevantes de maneira eficiente.

### RNF09 — Auditabilidade

O sistema deverá registrar erros e produzir indicadores que permitam verificar o resultado do processamento.

### RNF10 — Disponibilidade do modo local

O sistema deverá permitir consultas mesmo sem configuração da API da OpenAI, utilizando o modo de recuperação local.

## 🗄️ Banco de Dados

A persistência é realizada utilizando:

SQLite
+
SQLAlchemy

### Principais entidades:

Documento
│
└── Atendimento
│
└── Chunk

ErroProcessamento
### Principais tabelas
documentos
atendimentos
chunks
erros_processamento
## 📊 Resultado da validação do banco

Durante os testes realizados na branch feature/database-rag, foram identificados:

DOCUMENTOS:     4
ATENDIMENTOS:  64
CHUNKS:        64
ERROS:         18

Os erros registrados foram:

Duplicidade:             11
PDFInfoNotInstalledError: 7
## 📈 Resultado dos indicadores

Após a correção do pipeline, o sistema passou a reconstruir os indicadores utilizando os dados históricos do banco quando não existem novos documentos.

Resultado validado:

Documentos:       4
Páginas:         27
Registros:       64
Páginas OCR:      0
Erros:           18

Principais indicadores:

Válidos:        51
Inválidos:      13

Tempo médio:    50,00 minutos
Mediana:        47,50 minutos
Desvio padrão:  23,18 minutos

Categoria com maior volume:

Conectividade

Categoria com maior tempo médio:

VSCode e ferramentas
## 🧠 Resultado da busca semântica

### Pergunta utilizada:

Qual atendimento apresenta problema com o depurador?

### Resultado principal:

Protocolo: AT-032
Categoria: VSCode e ferramentas
Página: 8
Similaridade: 0.4471

O teste confirmou:

BUSCA OK
## 🤖 Resultado do RAG

O sistema também foi validado sem OPENAI_API_KEY.

### Resultado:

RAG OK
MODO: recuperacao_local
FONTES: 3

Nesse modo, o sistema recupera os trechos mais semelhantes e apresenta suas fontes, mantendo a aplicação funcional mesmo sem uma API externa.

## 🛠️ Tecnologias Utilizadas
Python
SQLAlchemy
SQLite
Pandas
NumPy
Matplotlib
sentence-transformers
ChromaDB
LangChain
OpenAI
FastAPI
Streamlit
Pytest
pypdf
Tesseract
Regex
Git / GitHub

---

## 📁 Estrutura do Projeto

```text
desafio-2-modulo-1/
├── data/
│   ├── auxiliares/
│   └── atendimentos/
├── database/
│   ├── atendimentos.db
│   └── chroma/
├── output/
│   ├── atendimentos_processados.csv
│   ├── indicadores.json
│   ├── processamento.log
│   └── graficos/
├── src/
│   ├── main.py
│   ├── api.py
│   ├── app_streamlit.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── pipeline.py
│   ├── analytics.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── rag.py
│   ├── pdf_processor.py
│   ├── ocr_processor.py
│   ├── text_processor.py
│   └── validation.py
├── tests/
├── .env.example
├── .gitignore
├── config.json
├── requirements.txt
└── README.md
```

---

## ▶️ Execução

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Pipeline

```powershell
python -m src.main
```

### Pipeline com indexação vetorial

```powershell
python -m src.main --indexar
```

### Consulta semântica

```powershell
python -m src.main --pergunta "Qual atendimento apresenta problema com o depurador?"
```

### API

```powershell
python -m uvicorn src.api:app --reload
```

### Streamlit

```powershell
streamlit run src/app_streamlit.py
```

### Testes

```powershell
python -m pytest
```

---

## 🔀 Controle de Versão

O projeto utiliza branches para desenvolvimento das funcionalidades.

### Branch de banco, analytics, embeddings e RAG

```text
feature/database-rag
```

### Branch principal

```text
main
```

A branch `feature/database-rag` permanece separada até a conclusão e validação das demais funcionalidades da equipe.

---

## 🤖 Uso de ferramentas de IA

Durante o desenvolvimento foi utilizada a ferramenta ChatGPT como apoio ao processo de desenvolvimento.

### Finalidades

A ferramenta foi utilizada para:

- interpretar mensagens de erro;
- auxiliar na compreensão de bibliotecas Python;
- sugerir testes;
- revisar código;
- auxiliar na implementação do banco;
- auxiliar na implementação dos indicadores;
- auxiliar na implementação do pipeline;
- auxiliar na implementação da busca semântica;
- auxiliar na documentação;
- auxiliar na organização do Git e GitHub;
- auxiliar na análise e correção de problemas.

### Participação dos discentes

As sugestões foram analisadas, executadas e validadas pelos integrantes do projeto.

Os discentes foram responsáveis por:

- implementar e modificar o código;
- executar os comandos;
- analisar os resultados;
- identificar erros;
- corrigir problemas;
- executar testes;
- validar o funcionamento do sistema;
- decidir quais sugestões seriam incorporadas;
- organizar os arquivos;
- realizar commits;
- trabalhar com branches;
- validar a execução final da aplicação.

---

## 👨‍💻 Autores

- **Diego Assunção**
- **Pedro Gomes**
- **Marcos Vinicius**

**Turma:** Vespertino — FIC_DEV Módulo Python para IA  
**Instituição:** SECITECI / Escola Técnica Estadual de Cuiabá
