"""Interface Streamlit mínima e funcional para o endpoint POST /ask."""
from pathlib import Path
import sys

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.ui_client import ApiClientError, ask_api, get_api_base_url

from src.ui_client import ApiClientError, ask_api, get_api_base_url

st.set_page_config(page_title="Consulta de atendimentos", page_icon="🔎", layout="centered")
st.title("Consulta inteligente de atendimentos")
st.caption("Pergunte sobre os registros processados e consulte as fontes recuperadas.")

with st.sidebar:
    st.subheader("Configuração")
    st.code(get_api_base_url(), language=None)
    st.caption("A URL pode ser alterada pela variável API_BASE_URL.")

question = st.text_area(
    "Pergunta",
    placeholder="Quais atendimentos relatam problemas com instalação do Python?",
    max_chars=500,
)
top_k = st.slider("Quantidade de fontes", 1, 10, 5)
category = st.text_input("Categoria (opcional)")
protocol = st.text_input("Protocolo (opcional)", placeholder="AT-032")

if st.button("Consultar", type="primary", disabled=len(question.strip()) < 3):
    try:
        with st.spinner("Consultando..."):
            data = ask_api(
                question,
                top_k=top_k,
                category=category or None,
                protocol=protocol or None,
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
            protocol_value = source.get("protocolo") or "sem protocolo"
            document = source.get("documento") or "documento não informado"
            page = source.get("pagina") if source.get("pagina") is not None else "?"
            score = source.get("similaridade")
            score_text = f"{score:.4f}" if isinstance(score, (int, float)) else "N/A"
            with st.expander(f"Fonte {index} — {protocol_value}", expanded=index == 1):
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
