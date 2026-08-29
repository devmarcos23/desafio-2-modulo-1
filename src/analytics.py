"""Indicadores, exportações e gráficos."""

from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def _serie(df: pd.DataFrame, coluna: str) -> pd.Series:
    """Retorna uma série segura mesmo quando a coluna não existe."""
    if coluna in df.columns:
        return df[coluna]

    return pd.Series(dtype="object")


def _contagem(df: pd.DataFrame, coluna: str) -> dict:
    """Gera contagem por coluna, tratando valores ausentes."""
    serie = _serie(df, coluna)

    if serie.empty:
        return {}

    serie = serie.fillna("Sem informação").astype(str)

    return {
        str(chave): int(valor)
        for chave, valor in serie.value_counts(dropna=False).items()
    }


def _total_documentos(df: pd.DataFrame) -> int:
    """Calcula a quantidade de documentos distintos."""
    serie = _serie(df, "documento")

    if serie.empty:
        return 0

    return int(serie.dropna().nunique())


def _total_paginas(df: pd.DataFrame) -> int:
    """
    Calcula a quantidade de páginas distintas.

    A mesma página pode conter vários atendimentos, portanto
    não devemos simplesmente usar len(df).
    """
    if "documento" not in df.columns or "pagina" not in df.columns:
        return 0

    paginas = (
        df[["documento", "pagina"]]
        .dropna()
        .drop_duplicates()
    )

    return int(len(paginas))


def _tempos(df: pd.DataFrame) -> np.ndarray:
    """Retorna tempos numéricos válidos."""
    if "tempo_minutos" not in df.columns:
        return np.array([], dtype=float)

    serie = pd.to_numeric(
        df["tempo_minutos"],
        errors="coerce",
    ).dropna()

    return serie.to_numpy(dtype=float)


def build_indicators(df: pd.DataFrame) -> dict:
    """
    Constrói os indicadores obrigatórios do projeto.

    Indicadores:
    - total de documentos;
    - total de páginas;
    - registros por classificação;
    - registros por categoria;
    - registros por status;
    - registros por município;
    - registros por método de extração;
    - média, mediana e desvio padrão do tempo;
    - percentual de OCR.
    """
    times = _tempos(df)

    quantidade_ocr = int(
        (_serie(df, "metodo").fillna("") == "ocr").sum()
    )

    total_registros = int(len(df))

    percentual_ocr = (
        float(quantidade_ocr / total_registros * 100)
        if total_registros
        else 0.0
    )

    return {
        "total_documentos": _total_documentos(df),
        "total_paginas": _total_paginas(df),
        "total_registros": total_registros,

        "registros_validos": int(
            (_serie(df, "classificacao") == "valido").sum()
        ),
        "registros_incompletos": int(
            (_serie(df, "classificacao") == "incompleto").sum()
        ),
        "registros_invalidos": int(
            (_serie(df, "classificacao") == "invalido").sum()
        ),
        "registros_duplicados": int(
            (_serie(df, "classificacao") == "duplicado").sum()
        ),

        "por_classificacao": _contagem(
            df,
            "classificacao",
        ),
        "por_categoria": _contagem(
            df,
            "categoria",
        ),
        "por_status": _contagem(
            df,
            "status",
        ),
        "por_municipio": _contagem(
            df,
            "municipio",
        ),
        "por_metodo_extracao": _contagem(
            df,
            "metodo",
        ),

        "tempo_medio": (
            float(np.mean(times))
            if times.size
            else None
        ),
        "tempo_mediano": (
            float(np.median(times))
            if times.size
            else None
        ),
        "tempo_desvio_padrao": (
            float(np.std(times))
            if times.size
            else None
        ),

        "total_com_tempo": int(times.size),
        "percentual_ocr": percentual_ocr,
        "total_ocr": quantidade_ocr,
    }


def export_results(
    df: pd.DataFrame,
    output_dir: str | Path,
    csv_name: str,
    json_name: str,
) -> dict:
    """Exporta os registros para CSV e os indicadores para JSON."""
    output = Path(output_dir)
    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    indicators = build_indicators(df)

    csv_path = output / csv_name
    json_path = output / json_name

    df.to_csv(
        csv_path,
        index=False,
        encoding="utf-8",
    )

    json_path.write_text(
        json.dumps(
            indicators,
            ensure_ascii=False,
            indent=2,
            default=float,
        ),
        encoding="utf-8",
    )

    return indicators


def generate_charts(
    df: pd.DataFrame,
    directory: str | Path,
) -> None:
    """Gera os gráficos principais dos atendimentos."""
    path = Path(directory)
    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    if df.empty:
        return

    # ---------------------------------------------------------
    # Gráfico por categoria
    # ---------------------------------------------------------
    if "categoria" in df.columns:
        dados = (
            df["categoria"]
            .fillna("Sem informação")
            .astype(str)
            .value_counts()
            .sort_values()
        )

        if not dados.empty:
            ax = dados.plot.barh(
                figsize=(9, 5),
            )

            ax.set_title(
                "Atendimentos por categoria"
            )
            ax.set_xlabel("Quantidade")
            ax.set_ylabel("")

            plt.tight_layout()
            plt.savefig(
                path / "atendimentos_categoria.png",
                dpi=160,
            )
            plt.close()

    # ---------------------------------------------------------
    # Gráfico por status
    # ---------------------------------------------------------
    if "status" in df.columns:
        dados = (
            df["status"]
            .fillna("Sem informação")
            .astype(str)
            .value_counts()
            .sort_values()
        )

        if not dados.empty:
            ax = dados.plot.barh(
                figsize=(9, 5),
            )

            ax.set_title(
                "Atendimentos por status"
            )
            ax.set_xlabel("Quantidade")
            ax.set_ylabel("")

            plt.tight_layout()
            plt.savefig(
                path / "atendimentos_status.png",
                dpi=160,
            )
            plt.close()

    # ---------------------------------------------------------
    # Tempo médio por categoria
    # ---------------------------------------------------------
    if (
        "categoria" in df.columns
        and "tempo_minutos" in df.columns
    ):
        dados = df.copy()

        dados["tempo"] = pd.to_numeric(
            dados["tempo_minutos"],
            errors="coerce",
        )

        tempo_categoria = (
            dados
            .dropna(subset=["tempo"])
            .groupby("categoria")["tempo"]
            .mean()
            .dropna()
            .sort_values()
        )

        if not tempo_categoria.empty:
            ax = tempo_categoria.plot.barh(
                figsize=(9, 5),
            )

            ax.set_title(
                "Tempo médio por categoria"
            )
            ax.set_xlabel("Minutos")
            ax.set_ylabel("")

            plt.tight_layout()
            plt.savefig(
                path / "tempo_medio_categoria.png",
                dpi=160,
            )
            plt.close()

    # ---------------------------------------------------------
    # Gráfico por método de extração
    # ---------------------------------------------------------
    if "metodo" in df.columns:
        dados = (
            df["metodo"]
            .fillna("Sem informação")
            .astype(str)
            .value_counts()
            .sort_values()
        )

        if not dados.empty:
            ax = dados.plot.barh(
                figsize=(9, 5),
            )

            ax.set_title(
                "Atendimentos por método de extração"
            )
            ax.set_xlabel("Quantidade")
            ax.set_ylabel("")

            plt.tight_layout()
            plt.savefig(
                path / "atendimentos_metodo.png",
                dpi=160,
            )
            plt.close()
