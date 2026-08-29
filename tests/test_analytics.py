import pandas as pd

from src.analytics import build_indicators


def test_mandatory_indicators_are_calculated():
    df = pd.DataFrame(
        [
            {"classificacao": "valido", "categoria": "A", "status": "Concluido", "municipio": "Cuiaba", "uf": "MT", "metodo": "extracao_direta", "tempo_minutos": 10},
            {"classificacao": "invalido", "categoria": "B", "status": "Pendente", "municipio": "Cuiaba", "uf": "MT", "metodo": "ocr", "tempo_minutos": 30},
        ]
    )
    errors = pd.DataFrame([{"tipo": "X", "etapa": "validacao"}])
    result = build_indicators(df, total_documentos=2, total_paginas=4, paginas_ocr=1, erros=errors)
    assert result["total_documentos"] == 2
    assert result["total_paginas"] == 4
    assert result["total_registros"] == 2
    assert result["percentual_paginas_ocr"] == 25.0
    assert result["percentual_por_classificacao"]["valido"] == 50.0
    assert result["tempo_medio"] == 20.0
    assert result["erros_por_tipo"] == {"X": 1}
