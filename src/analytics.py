"""Indicadores, exportações e gráficos."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _series(df: pd.DataFrame, column: str) -> pd.Series:
    """Retorna uma coluna ou uma Series vazia quando ela não existe."""
    if column in df.columns:
        return df[column]
    return pd.Series(dtype="object")


def _counts(df: pd.DataFrame, column: str) -> dict:
    """Calcula quantidade de registros por valor."""
    series = _series(df, column)

    if series.empty:
        return {}

    series = series.fillna("Sem informação")

    return {
        str(key): int(value)
        for key, value in series.value_counts(dropna=False).items()
    }


def _percentages(df: pd.DataFrame, column: str) -> dict:
    """Calcula percentual de registros por valor."""
    counts = _counts(df, column)
    total = len(df)

    if total == 0:
        return {}

    return {
        key: round((value / total) * 100, 2)
        for key, value in counts.items()
    }


def _tempo_series(df: pd.DataFrame) -> pd.Series:
    """Retorna os tempos válidos em minutos."""
    if "tempo_minutos" not in df.columns:
        return pd.Series(dtype=float)

    return pd.to_numeric(
        df["tempo_minutos"],
        errors="coerce",
    ).dropna()


def build_indicators(
    df: pd.DataFrame,
    total_documentos: int | None = None,
    total_paginas: int | None = None,
    erros: pd.DataFrame | None = None,
) -> dict:
    """Calcula os indicadores exigidos pelo desafio."""

    times = _tempo_series(df)

    classificacoes = _counts(df, "classificacao")
    categorias = _counts(df, "categoria")
    status = _counts(df, "status")
    municipios = _counts(df, "municipio")
    metodos = _counts(df, "metodo")

    # Se não forem informados, fazemos uma estimativa baseada
    # nos documentos/páginas presentes no DataFrame.
    if total_documentos is None:
        if "documento" in df.columns:
            total_documentos = int(df["documento"].nunique())
        else:
            total_documentos = 0

    if total_paginas is None:
        if {"documento", "pagina"}.issubset(df.columns):
            total_paginas = int(
                df[["documento", "pagina"]]
                .drop_duplicates()
                .shape[0]
            )
        else:
            total_paginas = 0

    # Categoria com maior volume
    categoria_maior_volume = None
    if categorias:
        categoria_maior_volume = max(
            categorias,
            key=categorias.get,
        )

    # Categoria com maior tempo médio
    categoria_maior_tempo = None
    tempos_categoria = {}

    if {"categoria", "tempo_minutos"}.issubset(df.columns):
        temp_df = df.copy()
        temp_df["tempo_minutos"] = pd.to_numeric(
            temp_df["tempo_minutos"],
            errors="coerce",
        )

        tempos = (
            temp_df.dropna(subset=["tempo_minutos"])
            .groupby("categoria")["tempo_minutos"]
            .mean()
            .dropna()
        )

        tempos_categoria = {
            str(key): round(float(value), 2)
            for key, value in tempos.items()
        }

        if not tempos.empty:
            categoria_maior_tempo = str(tempos.idxmax())

    # Erros
    erros_por_tipo = {}
    erros_por_etapa = {}

    if erros is not None and not erros.empty:
        if "tipo" in erros.columns:
            erros_por_tipo = _counts(erros, "tipo")

        if "etapa" in erros.columns:
            erros_por_etapa = _counts(erros, "etapa")

    percentual_ocr = 0.0

    if len(df) and "metodo" in df.columns:
        percentual_ocr = round(
            (
                df["metodo"]
                .fillna("")
                .str.lower()
                .eq("ocr")
                .mean()
            )
            * 100,
            2,
        )

    return {
        "total_documentos": int(total_documentos),
        "total_paginas": int(total_paginas),
        "total_registros": int(len(df)),

        "por_classificacao": classificacoes,
        "percentual_por_classificacao": _percentages(
            df,
            "classificacao",
        ),

        "por_categoria": categorias,
        "por_status": status,
        "por_municipio": municipios,
        "por_metodo_extracao": metodos,

        "tempo_medio": (
            round(float(np.mean(times)), 2)
            if not times.empty
            else None
        ),

        "tempo_mediano": (
            round(float(np.median(times)), 2)
            if not times.empty
            else None
        ),

        "tempo_desvio_padrao": (
            round(float(np.std(times, ddof=1)), 2)
            if len(times) > 1
            else 0.0
        ),

        "categoria_maior_volume": categoria_maior_volume,
        "categoria_maior_tempo_medio": categoria_maior_tempo,
        "tempo_medio_por_categoria": tempos_categoria,

        "percentual_paginas_ocr": percentual_ocr,

        "erros_por_tipo": erros_por_tipo,
        "erros_por_etapa": erros_por_etapa,
    }


def export_results(
    df: pd.DataFrame,
    output_dir: str | Path,
    csv_name: str,
    json_name: str,
    total_documentos: int | None = None,
    total_paginas: int | None = None,
    erros: pd.DataFrame | None = None,
) -> dict:
    """Exporta os dados tratados e os indicadores."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    indicators = build_indicators(
        df,
        total_documentos=total_documentos,
        total_paginas=total_paginas,
        erros=erros,
    )

    df.to_csv(
        out / csv_name,
        index=False,
        encoding="utf-8",
    )

    (out / json_name).write_text(
        json.dumps(
            indicators,
            ensure_ascii=False,
            indent=2,
            default=float,
        ),
        encoding="utf-8",
    )

    return indicators


def _save_bar_chart(
    series: pd.Series,
    title: str,
    xlabel: str,
    output: Path,
    horizontal: bool = True,
) -> None:
    """Salva um gráfico de barras."""

    if series.empty:
        return

    fig, ax = plt.subplots(figsize=(9, 5))

    if horizontal:
        series.sort_values().plot.barh(ax=ax)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("")
    else:
        series.plot.bar(ax=ax)
        ax.set_ylabel(xlabel)
        ax.set_xlabel("")

    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def generate_charts(
    df: pd.DataFrame,
    directory: str | Path,
) -> None:
    """Gera os gráficos obrigatórios do desafio."""

    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)

    # 1. Atendimentos por categoria
    if "categoria" in df.columns:
        categoria = (
            df["categoria"]
            .fillna("Sem informação")
            .value_counts()
        )

        _save_bar_chart(
            categoria,
            "Atendimentos por categoria",
            "Quantidade",
            path / "atendimentos_categoria.png",
        )

    # 2. Atendimentos por status
    if "status" in df.columns:
        status = (
            df["status"]
            .fillna("Sem informação")
            .value_counts()
        )

        _save_bar_chart(
            status,
            "Atendimentos por status",
            "Quantidade",
            path / "atendimentos_status.png",
        )

    # 3. Tempo médio por categoria
    if {"categoria", "tempo_minutos"}.issubset(df.columns):
        temp_df = df.copy()

        temp_df["tempo_minutos"] = pd.to_numeric(
            temp_df["tempo_minutos"],
            errors="coerce",
        )

        tempo_categoria = (
            temp_df.dropna(subset=["tempo_minutos"])
            .groupby("categoria")["tempo_minutos"]
            .mean()
            .sort_values()
        )

        _save_bar_chart(
            tempo_categoria,
            "Tempo médio por categoria",
            "Minutos",
            path / "tempo_medio_categoria.png",
        )

    # 4. Atendimentos por método de extração
    if "metodo" in df.columns:
        metodo = (
            df["metodo"]
            .fillna("Sem informação")
            .value_counts()
        )

        _save_bar_chart(
            metodo,
            "Atendimentos por método de extração",
            "Quantidade",
            path / "atendimentos_metodo.png",
        )

    # 5. Atendimentos por município
    if "municipio" in df.columns:
        municipio = (
            df["municipio"]
            .fillna("Sem informação")
            .value_counts()
        )

        if not municipio.empty:
            _save_bar_chart(
                municipio,
                "Atendimentos por município",
                "Quantidade",
                path / "atendimentos_municipio.png",
            )

    # 6. Classificação dos registros
    if "classificacao" in df.columns:
        classificacao = (
            df["classificacao"]
            .fillna("Sem informação")
            .value_counts()
        )

        _save_bar_chart(
            classificacao,
            "Registros por classificação",
            "Quantidade",
            path / "registros_classificacao.png",
        )