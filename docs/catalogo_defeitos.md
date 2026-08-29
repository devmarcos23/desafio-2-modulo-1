# Catálogo de defeitos

| ID | Prioridade | Comportamento observado | Resultado esperado | Correção aplicada | Status |
|---|---|---|---|---|---|
| BUG-001 | P2 | A URL da API estava fixa em `127.0.0.1:8000` no Streamlit. | Permitir execução em outra máquina/porta sem alterar código. | Adicionada `API_BASE_URL` e cliente HTTP configurável. | Corrigido |
| BUG-002 | P1 | No modo sem OpenAI, as fontes eram listadas sem mostrar o conteúdo recuperado. | Permitir que o usuário consulte os trechos que sustentam a recuperação. | O Streamlit passou a exibir o campo `conteudo` das fontes. | Corrigido |
| BUG-003 | P2 | `pytest -q` podia não localizar o pacote `src` em alguns ambientes. | Executar a suíte de forma previsível a partir da raiz do projeto. | Adicionado `pytest.ini` com `pythonpath = .`. | Corrigido |
| BUG-004 | P2 | O `/ask` expunha o tipo de exceção interna ao cliente. | Retornar erro HTTP útil sem expor detalhes internos e registrar a falha no servidor. | Adicionado logger e resposta HTTP 503 estável. | Corrigido |
| BUG-005 | P2 | A interface permitia enviar pergunta com menos de 3 caracteres, que era rejeitada depois pela API. | Evitar submissão sabidamente inválida. | Botão de consulta desabilitado enquanto a pergunta não atingir 3 caracteres. | Corrigido |
| BUG-006 | P2 | A API não tinha contratos de resposta explícitos no Swagger. | Documentar a estrutura de `/health` e `/ask` de forma clara. | Adicionados modelos Pydantic de resposta. | Corrigido |
| BUG-007 | P2 | A comunicação HTTP estava acoplada ao código visual do Streamlit. | Permitir teste isolado e separar responsabilidades. | Criado `src/ui_client.py`. | Corrigido |
| BUG-008 | P2 | A cobertura de testes da API/interface era insuficiente. | Cobrir sucesso, validação, falhas e fluxo HTTP local. | Adicionados testes de API, cliente e integração. | Corrigido |
