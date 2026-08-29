"""Entrada de linha de comando."""
from __future__ import annotations

import argparse

from .config import load_config
from .pipeline import process_all
from .indexer import build_index, semantic_query
from .rag import answer


def main():
    parser = argparse.ArgumentParser(
        description="Processa e consulta os atendimentos"
    )

    parser.add_argument(
        "--indexar",
        action="store_true",
        help="Processa os PDFs e indexa os chunks no ChromaDB",
    )

    parser.add_argument(
        "--pergunta",
        help="Executa uma consulta semântica/RAG sem reprocessar os PDFs",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Quantidade de resultados recuperados (padrão: 5)",
    )

    parser.add_argument(
        "--reprocessar",
        action="store_true",
        help="Reprocessa os PDFs mesmo que já estejam registrados",
    )

    args = parser.parse_args()
    cfg = load_config()

    # ---------------------------------------------------------
    # MODO CONSULTA
    # ---------------------------------------------------------
    # Se foi informada uma pergunta, não precisamos processar
    # novamente os PDFs. Os chunks já estão no ChromaDB.
    if args.pergunta:
        if args.top_k < 1:
            parser.error("--top-k deve ser maior ou igual a 1")

        sources = semantic_query(
            cfg,
            args.pergunta,
            args.top_k,
        )

        resultado = answer(
            args.pergunta,
            sources,
        )

        print(resultado)
        return

    # ---------------------------------------------------------
    # MODO PROCESSAMENTO
    # ---------------------------------------------------------
    df = process_all(
        cfg,
        reprocessar=args.reprocessar,
    )

    print(f"Registros encontrados: {len(df)}")

    # ---------------------------------------------------------
    # MODO INDEXAÇÃO
    # ---------------------------------------------------------
    if args.indexar:
        quantidade = build_index(cfg)
        print(f"Chunks indexados: {quantidade}")


if __name__ == "__main__":
    main()
