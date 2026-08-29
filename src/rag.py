"""Resposta RAG com recuperação local e síntese opcional."""

from __future__ import annotations

import os
import re
import unicodedata


def _normalizar(texto: str) -> str:
    """Remove acentos e normaliza o texto para comparação."""
    texto = unicodedata.normalize("NFKD", texto)

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    return texto.lower()


def _palavras_chave(pergunta: str) -> list[str]:
    """Extrai palavras relevantes da pergunta."""

    texto = _normalizar(pergunta)

    stopwords = {
        "qual",
        "quais",
        "que",
        "quem",
        "onde",
        "quando",
        "como",
        "apresenta",
        "apresentam",
        "apresentar",
        "problema",
        "problemas",
        "atendimento",
        "atendimentos",
        "relacionado",
        "relacionados",
        "relacionada",
        "relacionadas",
        "com",
        "do",
        "da",
        "de",
        "dos",
        "das",
        "um",
        "uma",
        "uns",
        "umas",
        "os",
        "as",
        "o",
        "a",
        "e",
        "em",
        "no",
        "na",
        "nos",
        "nas",
        "para",
        "por",
        "ao",
        "aos",
        "à",
        "às",
        "esta",
        "este",
        "está",
        "estao",
        "estão",
        "tem",
        "têm",
        "sobre",
    }

    palavras = re.findall(
        r"\b[\w-]+\b",
        texto,
    )

    return [
        palavra
        for palavra in palavras
        if len(palavra) >= 3
        and palavra not in stopwords
    ]


def _extrair_problema(conteudo: str) -> str:
    """Extrai somente o campo Problema do atendimento."""

    match = re.search(
        r"\bproblema\s+(.*?)(?=\s+solucao\s+|\s+observacoes\s+|$)",
        conteudo,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return ""

    return match.group(1).strip()


def _extrair_status(conteudo: str) -> str:
    """Extrai o status do atendimento."""

    match = re.search(
        r"\bstatus\s+(.*?)(?=\s+cep|\s+tempo|\s+problema|$)",
        conteudo,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return ""

    return match.group(1).strip()


def _correspondencia_problema(
    pergunta: str,
    resultado: dict,
) -> tuple[int, float]:
    """
    Mede a correspondência lexical entre a pergunta
    e o campo Problema.

    Retorna:
        (quantidade_de_termos, percentual)
    """

    palavras = _palavras_chave(pergunta)

    if not palavras:
        return 0, 0.0

    problema = _normalizar(
        _extrair_problema(
            resultado.get("conteudo", "")
        )
    )

    if not problema:
        return 0, 0.0

    encontrados = sum(
        1
        for palavra in palavras
        if palavra in problema
    )

    percentual = encontrados / len(palavras)

    return encontrados, percentual


def _pontuar_relevancia(
    pergunta: str,
    resultado: dict,
) -> float:
    """
    Combina similaridade semântica com correspondência
    lexical.

    Correspondências no campo Problema recebem peso
    maior do que correspondências no restante do texto.
    """

    conteudo = _normalizar(
        resultado.get("conteudo", "")
    )

    categoria = _normalizar(
        resultado.get("categoria", "")
    )

    palavras = _palavras_chave(pergunta)

    if not palavras:
        return float(
            resultado.get("similaridade", 0.0)
        )

    problema = _normalizar(
        _extrair_problema(
            resultado.get("conteudo", "")
        )
    )

    pontos = 0.0

    for palavra in palavras:

        if palavra in problema:
            pontos += 0.35

        elif palavra in conteudo:
            pontos += 0.08

        elif palavra in categoria:
            pontos += 0.04

    similaridade = float(
        resultado.get("similaridade", 0.0)
    )

    return (
        similaridade * 0.35
        + pontos
    )


def _eh_consulta_por_problema(
    pergunta: str,
) -> bool:
    """
    Detecta perguntas que procuram especificamente
    um problema de atendimento.
    """

    texto = _normalizar(pergunta)

    indicadores = (
        "problema",
        "erro",
        "falha",
        "dificuldade",
        "nao funciona",
        "não funciona",
        "apresenta",
        "apresentam",
    )

    return any(
        indicador in texto
        for indicador in indicadores
    )


def _filtrar_correspondencias_exatas(
    pergunta: str,
    fontes: list[dict],
) -> list[dict]:
    """
    Quando a pergunta procura um problema específico,
    mantém somente os atendimentos cujo campo Problema
    possui correspondência lexical forte.
    """

    candidatos = []

    for fonte in fontes:
        encontrados, percentual = (
            _correspondencia_problema(
                pergunta,
                fonte,
            )
        )

        item = {
            **fonte,
            "_termos_problema": encontrados,
            "_percentual_problema": percentual,
        }

        candidatos.append(item)

    if not candidatos:
        return []

    # Maior correspondência primeiro.
    candidatos.sort(
        key=lambda item: (
            item["_percentual_problema"],
            item["_termos_problema"],
            float(
                item.get("similaridade", 0.0)
            ),
        ),
        reverse=True,
    )

    # Se houver correspondência textual forte,
    # descartamos resultados apenas semanticamente parecidos.
    fortes = [
        item
        for item in candidatos
        if item["_percentual_problema"] >= 0.50
    ]

    if fortes:
        return fortes

    return candidatos


def _reranquear(
    pergunta: str,
    fontes: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """Reranqueia os resultados recuperados pelo Chroma."""

    if not fontes:
        return []

    # ---------------------------------------------------------
    # CONSULTAS POR PROBLEMA
    # ---------------------------------------------------------

    if _eh_consulta_por_problema(pergunta):

        candidatos = _filtrar_correspondencias_exatas(
            pergunta,
            fontes,
        )

        avaliados = []

        for fonte in candidatos:
            score = _pontuar_relevancia(
                pergunta,
                fonte,
            )

            item = {
                **fonte,
                "_relevancia": score,
            }

            avaliados.append(item)

    # ---------------------------------------------------------
    # CONSULTA SEMÂNTICA NORMAL
    # ---------------------------------------------------------

    else:

        avaliados = []

        for fonte in fontes:
            score = _pontuar_relevancia(
                pergunta,
                fonte,
            )

            item = {
                **fonte,
                "_relevancia": score,
            }

            avaliados.append(item)

    avaliados.sort(
        key=lambda item: item["_relevancia"],
        reverse=True,
    )

    resultados = []

    for item in avaliados[:top_k]:

        item = dict(item)

        item.pop("_relevancia", None)
        item.pop("_termos_problema", None)
        item.pop("_percentual_problema", None)

        resultados.append(item)

    return resultados


def _formatar_resposta(
    pergunta: str,
    fontes: list[dict],
) -> str:
    """Gera uma resposta legível sem depender de API externa."""

    if not fontes:
        return (
            "Não foram encontrados atendimentos relevantes "
            "para a pergunta."
        )

    resposta = [
        f"Pergunta: {pergunta}",
        "",
        f"Foram encontrados {len(fontes)} "
        "atendimentos relacionados:",
        "",
    ]

    for indice, fonte in enumerate(
        fontes,
        start=1,
    ):

        protocolo = fonte.get(
            "protocolo",
            "não informado",
        )

        categoria = fonte.get(
            "categoria",
            "não informada",
        )

        documento = fonte.get(
            "documento",
            "não informado",
        )

        pagina = fonte.get(
            "pagina",
            "não informada",
        )

        classificacao = fonte.get(
            "classificacao",
            "não informada",
        )

        municipio = fonte.get(
            "municipio",
            "não informado",
        )

        uf = fonte.get(
            "uf",
            "",
        )

        similaridade = fonte.get(
            "similaridade",
            0.0,
        )

        conteudo = fonte.get(
            "conteudo",
            "",
        )

        status = _extrair_status(
            conteudo
        )

        problema = _extrair_problema(
            conteudo
        )

        localidade = municipio

        if uf:
            localidade = f"{municipio}/{uf}"

        resposta.extend(
            [
                f"{indice}. {protocolo}",
                f"   Categoria: {categoria}",
                f"   Status: {status or 'não informado'}",
                f"   Classificação: {classificacao}",
                f"   Município: {localidade}",
                f"   Documento: {documento}",
                f"   Página: {pagina}",
                f"   Problema: "
                f"{problema or 'não informado'}",
                f"   Similaridade: {similaridade}",
                "",
            ]
        )

    return "\n".join(resposta)


def _responder_openai(
    pergunta: str,
    fontes: list[dict],
) -> str | None:
    """
    Tenta gerar uma síntese usando OpenAI.

    Se não houver chave ou ocorrer erro,
    retorna None.
    """

    api_key = os.getenv(
        "OPENAI_API_KEY"
    )

    if not api_key:
        return None

    try:

        from openai import OpenAI

        client = OpenAI(
            api_key=api_key
        )

        contexto = "\n\n".join(
            fonte.get(
                "conteudo",
                "",
            )
            for fonte in fontes
        )

        prompt = f"""
Responda à pergunta usando somente os atendimentos abaixo.

Pergunta:
{pergunta}

Atendimentos:
{contexto}

Regras:
- Não invente informações.
- Se houver vários atendimentos com o mesmo problema,
  liste todos os protocolos relevantes.
- Dê preferência aos atendimentos cujo campo Problema
  corresponde diretamente à pergunta.
- Não trate apenas similaridade semântica como
  correspondência exata.
"""

        response = client.responses.create(
            model=os.getenv(
                "OPENAI_MODEL",
                "gpt-4.1-mini",
            ),
            input=prompt,
        )

        return response.output_text

    except Exception:
        return None


def answer(
    question: str,
    sources: list[dict],
) -> dict:
    """
    Produz a resposta final do RAG.

    Primeiro reranqueia os resultados.
    Depois tenta síntese via OpenAI.
    Sem chave, utiliza resposta local.
    """

    fontes = _reranquear(
        question,
        sources,
        top_k=len(sources),
    )

    resposta_openai = _responder_openai(
        question,
        fontes,
    )

    if resposta_openai:
        return {
            "resposta": resposta_openai,
            "modo": "openai",
            "pergunta": question,
            "fontes": fontes,
        }

    resposta_local = _formatar_resposta(
        question,
        fontes,
    )

    return {
        "resposta": resposta_local,
        "modo": "recuperacao_local",
        "pergunta": question,
        "fontes": fontes,
    }