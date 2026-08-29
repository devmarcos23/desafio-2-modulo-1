"""CLI para pipeline, indexação e consulta semântica."""
from __future__ import annotations

import argparse

from .config import load_config
from .indexer import build_index, semantic_query
from .pipeline import process_all
from .rag import answer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Processa e consulta atendimentos")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Recria banco e índice antes do pipeline",
    )
    parser.add_argument("--indexar", action="store_true", help="Cria/atualiza o índice ChromaDB")
    parser.add_argument("--pergunta", help="Executa consulta após o processamento")
    parser.add_argument("--top-k", type=int, default=5, help="Quantidade de fontes")
    parser.add_argument("--categoria", help="Filtro opcional por categoria")
    parser.add_argument("--protocolo", help="Filtro opcional por protocolo")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    cfg = load_config()
    dataframe = process_all(cfg, reset=args.reset)
    print(f"Registros encontrados: {len(dataframe)}")
    if args.indexar:
        print(f"Chunks indexados: {build_index(cfg)}")
    if args.pergunta:
        sources = semantic_query(
            cfg,
            args.pergunta,
            args.top_k,
            args.categoria,
            args.protocolo,
        )
        print(answer(args.pergunta, sources))


if __name__ == "__main__":
    main()
