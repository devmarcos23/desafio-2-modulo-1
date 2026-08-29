"""Indicadores, exportações e gráficos estatísticos do processamento."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _series(df: pd.DataFrame, column: str) -> pd.Series:
    return df[column] if column in df.columns else pd.Series(dtype="object")


def _counts(df: pd.DataFrame, column: str) -> dict[str, int]:
    series = _series(df, column)
    if series.empty:
        return {}
    series = series.fillna("Sem informação").replace("", "Sem informação")
    return {str(key): int(value) for key, value in series.value_counts(dropna=False).items()}


def _percentages(df: pd.DataFrame, column: str) -> dict[str, float]:
    counts = _counts(df, column)
    total = len(df)
    if total == 0:
        return {}
    return {key: round(value / total * 100, 2) for key, value in counts.items()}


def _tempo_series(df: pd.DataFrame) -> pd.Series:
    if "tempo_minutos" not in df.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(df["tempo_minutos"], errors="coerce").dropna()


def build_indicators(
    df: pd.DataFrame,
    *,
    total_documentos: int,
    total_paginas: int,
    paginas_ocr: int,
    erros: pd.DataFrame | None = None,
) -> dict:
    """Calcula todos os indicadores obrigatórios do desafio."""
    times = _tempo_series(df)
    categorias = _counts(df, "categoria")
    tempos_categoria: dict[str, float] = {}
    categoria_maior_tempo: str | None = None

    if {"categoria", "tempo_minutos"}.issubset(df.columns):
        temp_df = df.copy()
        temp_df["categoria"] = temp_df["categoria"].fillna("Sem informação").replace(
            "", "Sem informação"
        )
        temp_df["tempo_minutos"] = pd.to_numeric(temp_df["tempo_minutos"], errors="coerce")
        grouped = temp_df.dropna(subset=["tempo_minutos"]).groupby("categoria")[
            "tempo_minutos"
        ].mean()
        tempos_categoria = {
            str(key): round(float(value), 2) for key, value in grouped.items()
        }
        if not grouped.empty:
            categoria_maior_tempo = str(grouped.idxmax())

    erros_por_tipo: dict[str, int] = {}
    erros_por_etapa: dict[str, int] = {}
    if erros is not None and not erros.empty:
        erros_por_tipo = _counts(erros, "tipo")
        erros_por_etapa = _counts(erros, "etapa")

    categoria_maior_volume = max(categorias, key=categorias.get) if categorias else None
    percentual_ocr = round((paginas_ocr / total_paginas * 100), 2) if total_paginas else 0.0

    return {
        "total_documentos": int(total_documentos),
        "total_paginas": int(total_paginas),
        "total_registros": int(len(df)),
        "por_classificacao": _counts(df, "classificacao"),
        "percentual_por_classificacao": _percentages(df, "classificacao"),
        "por_categoria": categorias,
        "por_status": _counts(df, "status"),
        "por_municipio": _counts(df, "municipio"),
        "por_uf": _counts(df, "uf"),
        "por_metodo_extracao": _counts(df, "metodo"),
        "tempo_medio": round(float(np.mean(times)), 2) if not times.empty else None,
        "tempo_mediano": round(float(np.median(times)), 2) if not times.empty else None,
        "tempo_desvio_padrao": (
            round(float(np.std(times, ddof=1)), 2) if len(times) > 1 else 0.0
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
    *,
    total_documentos: int,
    total_paginas: int,
    paginas_ocr: int,
    erros: pd.DataFrame | None = None,
) -> dict:
    """Exporta CSV tratado e JSON de indicadores em UTF-8."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    indicators = build_indicators(
        df,
        total_documentos=total_documentos,
        total_paginas=total_paginas,
        paginas_ocr=paginas_ocr,
        erros=erros,
    )
    df.to_csv(output / csv_name, index=False, encoding="utf-8")
    (output / json_name).write_text(
        json.dumps(indicators, ensure_ascii=False, indent=2, default=float),
        encoding="utf-8",
    )
    return indicators


def _save_bar_chart(
    series: pd.Series,
    *,
    title: str,
    xlabel: str,
    output: Path,
    horizontal: bool = True,
) -> None:
    if series.empty:
        return
    fig, ax = plt.subplots(figsize=(10, 6))
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


def generate_charts(df: pd.DataFrame, directory: str | Path) -> None:
    """Gera gráficos PNG legíveis, incluindo os três grupos obrigatórios."""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)

    if "categoria" in df.columns:
        _save_bar_chart(
            df["categoria"].fillna("Sem informação").replace("", "Sem informação").value_counts(),
            title="Atendimentos por categoria",
            xlabel="Quantidade de atendimentos",
            output=path / "atendimentos_categoria.png",
        )

    if {"categoria", "tempo_minutos"}.issubset(df.columns):
        temp = df.copy()
        temp["tempo_minutos"] = pd.to_numeric(temp["tempo_minutos"], errors="coerce")
        temp["categoria"] = temp["categoria"].fillna("Sem informação").replace(
            "", "Sem informação"
        )
        grouped = temp.dropna(subset=["tempo_minutos"]).groupby("categoria")[
            "tempo_minutos"
        ].mean()
        _save_bar_chart(
            grouped,
            title="Tempo médio por categoria",
            xlabel="Minutos",
            output=path / "tempo_medio_categoria.png",
        )

    chart_specs = [
        ("status", "Atendimentos por status", "Quantidade", "atendimentos_status.png"),
        (
            "metodo",
            "Atendimentos por método de extração",
            "Quantidade",
            "atendimentos_metodo.png",
        ),
        ("municipio", "Atendimentos por município", "Quantidade", "atendimentos_municipio.png"),
        (
            "classificacao",
            "Registros por classificação",
            "Quantidade",
            "registros_classificacao.png",
        ),
    ]
    for column, title, xlabel, filename in chart_specs:
        if column in df.columns:
            series = (
                df[column]
                .fillna("Sem informação")
                .replace("", "Sem informação")
                .value_counts()
            )
            _save_bar_chart(
                series,
                title=title,
                xlabel=xlabel,
                output=path / filename,
            )
