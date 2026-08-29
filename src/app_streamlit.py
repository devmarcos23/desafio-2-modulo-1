"""Interface Streamlit para consulta dos atendimentos."""
from __future__ import annotations

import streamlit as st

from src.ui_client import ApiClientError, ask_api, get_api_base_url

st.set_page_config(
    page_title="Consulta de atendimentos",
    page_icon="🔎",
    layout="centered",
)

st.title("Consulta inteligente de atendimentos")
st.caption(
    "Faça perguntas sobre os registros processados. A resposta é acompanhada "
    "das fontes recuperadas pelo sistema."
)

with st.sidebar:
    st.subheader("Configuração")
    st.code(get_api_base_url(), language=None)
    st.caption("Altere a variável API_BASE_URL para usar outro endereço da API.")

question = st.text_area(
    "Pergunta",
    placeholder="Quais problemas de instalação do Python aparecem com maior frequência?",
    max_chars=500,
)
top_k = st.slider(
    "Quantidade de fontes",
    min_value=1,
    max_value=10,
    value=5,
)
category = st.text_input(
    "Categoria (opcional)",
    placeholder="Ex.: Instalação e ambiente",
)

can_submit = len(question.strip()) >= 3

if st.button("Consultar", type="primary", disabled=not can_submit):
    try:
        with st.spinner("Consultando os atendimentos..."):
            data = ask_api(
                question,
                top_k=top_k,
                category=category or None,
            )

        st.subheader("Resposta")
        st.write(data["resposta"])
        st.caption(f"Modo: {data.get('modo', 'não informado')}")

        if data.get("aviso"):
            st.warning(data["aviso"])

        sources = data.get("fontes", [])
        st.subheader(f"Fontes ({len(sources)})")

        if not sources:
            st.info("Nenhuma fonte foi recuperada para esta pergunta.")

        for index, source in enumerate(sources, start=1):
            protocol = source.get("protocolo") or "sem protocolo"
            document = source.get("documento") or "documento não informado"
            page = source.get("pagina") or "?"
            score = source.get("similaridade")
            score_text = f"{score:.4f}" if isinstance(score, (int, float)) else "N/A"

            with st.expander(f"Fonte {index} — {protocol}", expanded=index == 1):
                st.markdown(
                    f"**Documento:** {document}  \n"
                    f"**Página:** {page}  \n"
                    f"**Categoria:** {source.get('categoria') or 'não informada'}  \n"
                    f"**Similaridade:** {score_text}"
                )
                if source.get("conteudo"):
                    st.markdown("**Trecho recuperado:**")
                    st.write(source["conteudo"])

    except ApiClientError as exc:
        st.error(str(exc))
