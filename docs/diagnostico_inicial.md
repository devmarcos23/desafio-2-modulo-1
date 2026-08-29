# Diagnóstico Inicial do Sistema

## 1. Objetivo do diagnóstico
Breve descrição da auditoria realizada antes das correções.

## 2. Estado inicial encontrado

### 2.1 Ambiente e dependências
- ausência/inconsistência de dependências externas;
- necessidade de Tesseract;
- necessidade de Poppler;
- problemas de reprodutibilidade identificados.

### 2.2 Pipeline
- processamento parcial;
- perda de registros;
- inconsistências em reexecuções;
- problemas de criação do banco/diretórios.

### 2.3 OCR
- inicialmente, sem Poppler:
  - 27 páginas;
  - 0 páginas OCR;
  - 75 registros.

- após instalação das dependências, mas antes das correções:
  - 27 páginas;
  - 7 páginas OCR;
  - 82 registros;
  - somente parte dos registros digitalizados chegava ao resultado final.

### 2.4 Validação e persistência
- valores `[vazio]` não tratados adequadamente;
- falsos duplicados com `PROTOCOLO?`;
- inconsistências em protocolos vindos do OCR;
- registros inválidos/incompletos precisavam permanecer rastreáveis.

### 2.5 Indicadores e outputs
- percentual de OCR calculado de forma inadequada;
- risco de sobrescrita/reconstrução incorreta dos outputs;
- indicadores obrigatórios incompletos.

### 2.6 API e interface
- API implementada;
- Streamlit apresentava erro de importação na execução real:
  `ModuleNotFoundError: No module named 'src'`.

## 3. Principais riscos encontrados

- perda de dados;
- inconsistência entre banco e arquivos de saída;
- dificuldade de reprodução em outro computador;
- dependência de serviços externos;
- falhas de integração entre módulos.

## 4. Resultado após as correções

Após a auditoria e implementação das correções:

- documentos processados: 4;
- páginas processadas: 27;
- páginas por OCR: 7;
- registros extraídos: 100;
- atendimentos únicos: 90;
- duplicados identificados: 10;
- chunks indexados: 90;
- testes automatizados: 30 aprovados;
- FastAPI: operacional;
- Streamlit: operacional;
- busca semântica: operacional;
- modo de recuperação local: operacional.

## 5. Evolução observada

| Etapa | Registros | Páginas OCR |
|---|---:|---:|
| Execução sem Poppler | 75 | 0 |
| OCR funcionando antes das correções | 82 | 7 |
| Versão auditada e corrigida | 100 | 7 |

## 6. Conclusão do diagnóstico

O diagnóstico confirmou que o sistema possuía funcionalidades implementadas,
porém apresentava falhas de integração, configuração, processamento e
reprodutibilidade. As correções realizadas eliminaram as perdas de registros
identificadas e permitiram executar o fluxo completo de processamento,
persistência, análise, indexação, consulta via API e interface Streamlit.