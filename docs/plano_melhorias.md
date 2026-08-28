# Crítica e plano de melhorias

As melhorias foram priorizadas conforme impacto, esforço e risco.

| ID | Prioridade | Problema | Justificativa/benefício | Esforço | Risco | Estratégia | Status |
|---|---|---|---|---|---|---|---|
| MEL-001 | P1 | O modo local não mostrava o conteúdo recuperado na interface. | Sem chave da OpenAI, o usuário precisa visualizar os trechos que sustentam a recuperação. | Baixo | Baixo | Exibir `conteudo` de cada fonte no Streamlit. | Implementada |
| MEL-002 | P2 | URL da API estava fixa no código. | A configuração por ambiente melhora reprodutibilidade e implantação local. | Baixo | Baixo | Usar `API_BASE_URL` com fallback local. | Implementada |
| MEL-003 | P2 | Comunicação HTTP estava misturada à camada visual. | Separar responsabilidades facilita manutenção e testes. | Baixo | Baixo | Criar `src/ui_client.py`. | Implementada |
| MEL-004 | P2 | Cobertura de testes da API/interface era pequena. | Maior cobertura reduz regressões no merge e na demonstração. | Médio | Baixo | Cobrir validação, sucesso, 503, cliente HTTP e integração local. | Implementada |
| MEL-005 | P2 | O contrato de saída da API não estava explicitado. | Schemas tornam `/docs` mais claro e previsível. | Baixo | Baixo | Criar modelos Pydantic para health, consulta e fontes. | Implementada |
| MEL-006 | P3 | `/health` verifica apenas disponibilidade HTTP e modo. | Uma verificação opcional mais profunda poderia detectar banco/índice indisponíveis antes de `/ask`. | Médio | Médio | Criar endpoint separado de readiness, sem tornar o health básico pesado. | Futuro |
