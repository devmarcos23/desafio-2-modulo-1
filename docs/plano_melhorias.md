# Crítica e plano de melhorias

A solução original tinha boa separação modular, mas vários componentes estavam corretos isoladamente e falhavam quando integrados. O caso mais importante foi o OCR: Tesseract/segmentação conseguiam encontrar 25 registros, mas a execução observada produzia somente 82 registros totais. Isso demonstra por que testes ponta a ponta são indispensáveis em código gerado por IA.

| Melhoria | Problema | Justificativa | Benefício | Esforço | Risco | Prioridade | Estratégia / situação |
|---|---|---|---|---|---|---|---|
| Histórico idempotente de registros | Duplicados/invalidos podiam desaparecer dos outputs ou divergir do cadastro único | Indicadores precisam considerar todos os registros oficiais | Elimina perda de dados e mantém banco × CSV coerentes | Médio | Médio | P0 | **Implementada** com `RegistroProcessado` e reconstrução dos outputs |
| Reprocessamento de documento parcial | Falha temporária de OCR podia deixar histórico incompleto | Dependências externas podem falhar | Recuperação automática na próxima execução | Médio | Baixo | P0 | **Implementada** com `Documento.concluido` |
| Integração e cache de CEP | Cliente existia sem participação no pipeline | RF07 e indicador municipal | Enriquecimento de município/UF sem interromper lote | Baixo | Baixo | P1 | **Implementada** com cache e timeout |
| Pré-processamento de imagem OCR | Alguns campos continuam com caracteres distorcidos | O registro é recuperado, mas pode ser classificado inválido | Maior qualidade em e-mail/data/categoria | Médio | Médio: correção excessiva pode inventar dados | P2 | **Futuro**: binarização/contraste/deskew e comparação de PSM, sempre preservando bruto |
| Health check de dependências | `/health` confirma API viva, não índice/modelo | Facilita operação e diagnóstico | Identifica DB/Chroma não preparados antes de `/ask` | Baixo | Baixo | P3 | **Futuro**: endpoint de readiness separado de liveness |
| Cache de modelo de embeddings no processo da API | Carregamento pode ser custoso conforme ambiente | API deve responder com menor latência | Reduz tempo de consultas repetidas | Médio | Baixo | P2 | **Parcial**: `EmbeddingService` usa cache; medir e, se necessário, inicializar em lifespan da API |
