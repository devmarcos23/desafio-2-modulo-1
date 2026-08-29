# Catálogo de defeitos

Prioridades: **P0** = segurança/perda de dados/indisponibilidade crítica; **P1** = funcionamento confiável; **P2** = qualidade/desempenho/manutenção; **P3** = evolução futura/conveniência.

| id | requisito | prioridade | descricao_estado_inicial | causa | correcao | justificativa | status |
|---|---|---|---|---|---|---|---|
| BUG-001 | RF01/RF06 | P1 | Clone limpo falhava com `unable to open database file`. | Diretório pai do SQLite não era criado antes do `create_engine`. | `database.py` passou a criar o diretório do SQLite automaticamente. | A instalação deve ser reproduzível sem etapa manual escondida. | Corrigido |
| BUG-002 | RF03 | P1 | Falta de Poppler/Tesseract gerava stack traces repetidos no OCR. | Não havia verificação prévia clara das dependências externas. | `ocr_processor.py` valida executáveis e retorna mensagem orientativa. README documenta instalação. | Melhora diagnóstico e implantação em outro computador. | Corrigido |
| BUG-003 | RF03/RF04/RF09 | P0 | Com OCR funcionando, a execução observada produzia 82 registros embora os quatro PDFs contenham 100; 18 registros eram perdidos no resultado final. | O histórico/saída não preservava de forma independente todos os registros extraídos após as etapas de validação/persistência. | Criada persistência de `RegistroProcessado` para todo registro extraído; duplicados e inválidos permanecem no histórico; outputs são reconstruídos do banco. | Perda de registros compromete banco, indicadores e RAG. | Corrigido |
| BUG-004 | RF04/RF06 | P0 | Dois registros sem protocolo podiam compartilhar literalmente `PROTOCOLO?` e um ser tratado como duplicado do outro. | Valor inválido era usado como chave de unicidade. | Protocolos inválidos usam chave técnica sintética interna; o valor original continua preservado. | Evita falso positivo de duplicidade e descarte incorreto. | Corrigido |
| BUG-005 | RF04 | P1 | Marcadores como `[vazio]` podiam ser interpretados como texto válido. | Validação verificava apenas string vazia. | Normalização reconhece marcadores de ausência antes da validação. | Necessário classificar corretamente registros incompletos. | Corrigido |
| BUG-006 | RF06 | P1 | CRUD estava incompleto para atualização controlada. | Camada de banco concentrava criação/busca/exclusão. | Adicionada atualização controlada por protocolo e testes de CRUD/transação. | RF06 exige inserção, consulta, atualização e exclusão controlada. | Corrigido |
| BUG-007 | RF07/RF08 | P1 | Cliente de CEP existia, mas município/UF permaneciam sempre `None`. | `lookup_cep` não estava integrado ao pipeline. | Pipeline consulta ViaCEP com cache, timeout e fallback sem interrupção. | Sem integração não há indicador real por município/UF quando a rede está disponível. | Corrigido |
| BUG-008 | RF08 | P1 | Percentual de OCR era calculado sobre registros, não sobre páginas. | Analytics recebia apenas linhas do DataFrame. | Documento persiste `total_paginas`/`paginas_ocr` e analytics recebe os totais de páginas. | O requisito pede percentual de **páginas** OCR. | Corrigido |
| BUG-009 | RF08/RF09 | P1 | Indicadores obrigatórios estavam incompletos. | Analytics não possuía contexto de documentos/páginas/erros e faltavam agregações. | Incluídos totais, percentuais, métodos, municípios/UF, maiores categorias e erros por tipo/etapa. | Necessário para cumprir a lista obrigatória. | Corrigido |
| BUG-010 | RF01/RF06/RF09 | P0 | Na segunda execução, PDFs já processados podiam ser ignorados e CSV/JSON refletir lista vazia/parcial. | Outputs eram montados apenas com os registros processados naquele processo. | Outputs passam a ser reconstruídos de `registros_processados`; reexecução validada com 100 registros. | Risco de perda/inconsistência de arquivos de saída. | Corrigido |
| BUG-011 | RF03/RNF tolerância | P0 | Documento com falha parcial podia ficar marcado pelo hash e não ser recuperado corretamente depois. | Não havia estado explícito de conclusão para distinguir processamento íntegro de parcial. | `Documento.concluido` controla reuso; documentos incompletos são reprocessados. | Evita perda permanente após falha temporária de OCR. | Corrigido |
| BUG-012 | RF09/RNF logs | P1 | Inconsistências de validação não apareciam claramente no log textual. | Erros ficavam apenas nos motivos/estruturas internas. | Inconsistências são persistidas e registradas como `WARNING` no log. | O log deve ser útil para diagnóstico e registrar problemas. | Corrigido |
| BUG-013 | RF10 | P2 | Tamanho/sobreposição dos chunks estavam efetivamente fixos em trecho do pipeline. | Parâmetros não eram propagados da configuração até a persistência. | `_persist_record` recebe `tamanho_chunk` e `sobreposicao` de `config.json`. | O requisito pede estratégia explicada/configurável. | Corrigido |
| BUG-014 | RF12 | P1 | Consulta Chroma permitia filtro por categoria, mas não por protocolo. | Construção de `where` cobria só categoria. | Adicionado filtro por protocolo e composição `$and` categoria + protocolo. | O RF12 exige os dois tipos de filtro. | Corrigido |
| BUG-015 | RF13/RF14 | P1 | Contexto RAG não tinha limite explícito e falhas do modelo podiam produzir resposta técnica inadequada ao usuário. | Cadeia não controlava tamanho de contexto/fallback de forma centralizada. | Contexto limitado; exceção é logada internamente e o usuário recebe fallback local sem detalhes sensíveis. | Reduz risco de contexto excessivo e melhora disponibilidade. | Corrigido |
| BUG-016 | RF16/RNF configuração | P2 | URL da FastAPI estava fixa na interface. | Endpoint HTTP estava hardcoded. | `ui_client.py` usa `API_BASE_URL` e `.env.example`. | Facilita execução em outro host/porta. | Corrigido |
| BUG-017 | RF16 | P2 | Modo local mostrava metadados, mas não deixava claro o conteúdo recuperado em todas as situações. | Renderização das fontes era limitada. | Streamlit mostra fonte, similaridade e conteúdo do chunk. | O modo local precisa ser utilizável sem modelo. | Corrigido |
| BUG-018 | RNF/README | P2 | README da release misturava divisão interna da equipe, renumerava os RFs para 19 itens e apresentava resultados antigos de 64 registros/0 OCR. | Documentação foi acumulada por frentes e não reconciliada com a especificação oficial. | README reescrito conforme RF01–RF17 e resultados da auditoria final; divisão interna removida. | O professor deve conseguir reproduzir e confrontar a entrega com o enunciado oficial. | Corrigido |
| BUG-019 | RNF testes | P1 | Testes existentes não cobririam a perda dos registros oficiais nem várias integrações críticas. | Cobertura concentrada em poucos helpers/API. | Suíte ampliada para configuração, DB, validação, OCR/pipeline oficial, analytics, CEP, RAG, filtros, API e UI. | Um teste de regressão impede retorno do defeito de perda de dados. | Corrigido |
| BUG-020 | RNF manutenção | P2 | Dependências estavam apenas com mínimo aberto e havia dependência não usada. | `requirements.txt` sem faixa superior e `pdfplumber` não era usado. | Faixas de versão compatíveis foram adicionadas e dependência não utilizada removida. | Reduz variação entre instalações e manutenção desnecessária. | Corrigido |
| BUG-021 | RF03/RF04 | P2 | OCR ainda pode distorcer caracteres de e-mail/data/categoria mesmo recuperando todos os registros. | Limitação inerente à qualidade da imagem e reconhecimento óptico. | Texto bruto é preservado e campos sem sustentação são classificados como inválidos; não há correção sem evidência. | Evita inventar dados. Pré-processamento de imagem pode ser evolução futura. | Limitação conhecida |

BUG-022
Requisito: RF16 / Reprodutibilidade
Prioridade: P1

Estado inicial:
Ao executar "streamlit run src/app_streamlit.py", a interface
falhava com ModuleNotFoundError: No module named 'src'.

Causa:
A execução direta pelo Streamlit não adicionava a raiz do projeto
ao sys.path.

Correção:
A aplicação passou a resolver dinamicamente PROJECT_ROOT e incluí-lo
no caminho de importação antes de importar src.ui_client.

Validação:
A interface Streamlit iniciou em http://localhost:8501, realizou
consultas por meio da FastAPI e exibiu resposta, fontes,
similaridade e conteúdo recuperado.

Status:
Corrigido.