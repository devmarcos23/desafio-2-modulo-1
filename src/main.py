"""Entrada de linha de comando para processamento, indexação e consulta."""
from __future__ import annotations

import argparse

from .config import load_config
from .indexer import build_index, semantic_query
from .pipeline import process_all
from .rag import answer


def build_parser() -> argparse.ArgumentParser:
    """Cria o parser dos argumentos da aplicação."""

    parser = argparse.ArgumentParser(
        description="Processa e consulta os atendimentos"
    )
    parser.add_argument(
        "--indexar",
        action="store_true",
        help="Cria/atualiza o índice vetorial após o processamento.",
    )
    parser.add_argument(
        "--pergunta",
        help="Executa uma consulta semântica após o processamento.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Quantidade de fontes recuperadas na consulta.",
    )
    parser.add_argument(
        "--categoria",
        help="Filtro opcional de categoria na consulta semântica.",
    )
    return parser


def main() -> None:
    """Executa o fluxo solicitado pela linha de comando."""

    args = build_parser().parse_args()
    cfg = load_config()

    dataframe = process_all(cfg)
    print(f"Registros encontrados: {len(dataframe)}")

    if args.indexar:
        print(f"Chunks indexados: {build_index(cfg)}")

    if args.pergunta:
        sources = semantic_query(
            cfg,
            args.pergunta,
            args.top_k,
            args.categoria,
        )
        print(answer(args.pergunta, sources))


if __name__ == "__main__":
    main()
