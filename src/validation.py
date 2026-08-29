"""Extração, normalização e validação dos registros."""

from __future__ import annotations

from datetime import datetime
import re
import unicodedata


EMAIL_RE = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

PROTO_RE = re.compile(r"^AT-\d{3}$")

CEP_RE = re.compile(r"^\d{5}-?\d{3}$")


FIELD_PATTERNS = {
    "protocolo": r"\bProtocolo\s+(AT-\d{3})\b",
    "data": r"\bData\s+(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})\b",
    "solicitante": r"\bSolicitante\s+(.+?)\s+E-mail\b",
    "email": r"\bE-mail\s+(\S+)",
    "categoria": r"\bCategoria\s+(.+?)\s+Status\b",
    "status": r"\bStatus\s+(Concluido|Pendente|Em atendimento)\b",
    "cep": r"\bCEP\s*/?\s*cidade\s+(\S+)",
    "tempo_minutos": r"\bTempo\s+(-?\d+(?:[.,]\d+)?)\s*min\b",
    "descricao": r"\bProblema\s+(.+?)\s+Solucao\b",
    "solucao": r"\bSolucao\s+(.+?)\s+Observacoes\b",
    "observacoes": r"\bObservacoes\s+(.+)$",
}


def clean_text(text: str) -> str:
    """Remove caracteres inválidos e normaliza espaços."""
    if not text:
        return ""

    text = text.replace("\x00", " ")
    text = text.replace("\r", " ")
    text = text.replace("\n", " ")

    return re.sub(r"\s+", " ", text).strip()


def extract_fields(text: str) -> dict:
    """
    Extrai os campos conhecidos do texto.

    Campos que não forem encontrados permanecem vazios.
    Isso permite preservar registros incompletos provenientes
    de OCR.
    """
    clean = clean_text(text)

    result = {
        "protocolo": "",
        "data": "",
        "solicitante": "",
        "email": "",
        "categoria": "",
        "status": "",
        "cep": "",
        "municipio": "",
        "uf": "",
        "tempo_minutos": "",
        "descricao": "",
        "solucao": "",
        "observacoes": "",
    }

    for key, pattern in FIELD_PATTERNS.items():
        match = re.search(
            pattern,
            clean,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if match:
            result[key] = match.group(1).strip()

    # ---------------------------------------------------------
    # CEP + município + UF
    # ---------------------------------------------------------
    match_cep = re.search(
        r"\bCEP\s*/?\s*cidade\s+"
        r"(\d{5}-?\d{3})"
        r"(?:\s*-\s*([A-Za-zÀ-ÿ .'-]+?)"
        r"/\s*([A-Za-z]{2}))?"
        r"(?:\s+Tempo|\s+Problema|\s+Solucao|$)",
        clean,
        flags=re.IGNORECASE,
    )

    if match_cep:
        result["cep"] = match_cep.group(1).strip()

        if match_cep.group(2):
            result["municipio"] = match_cep.group(2).strip()

        if match_cep.group(3):
            result["uf"] = match_cep.group(3).upper().strip()

    return result


def parse_date(value: str):
    """Converte uma data textual em date."""
    value = (value or "").strip()

    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass

    return None


def normalize_key(value: str) -> str:
    """Normaliza texto para comparação."""
    value = unicodedata.normalize(
        "NFKD",
        value or "",
    )

    value = (
        value.encode("ascii", "ignore")
        .decode()
        .lower()
        .strip()
    )

    return re.sub(r"\s+", " ", value)


def normalize_category(
    value: str,
    categories: dict,
) -> str | None:
    """Converte uma categoria ou variação para o nome oficial."""
    target = normalize_key(value)

    if not target:
        return None

    for item in categories.get(
        "categorias_oficiais",
        [],
    ):
        nome = normalize_key(item.get("nome", ""))

        variacoes = {
            normalize_key(valor)
            for valor in item.get("variacoes", [])
        }

        if target in {nome, *variacoes}:
            return item["nome"]

    return None


def validate_record(
    record: dict,
    categories: dict,
) -> tuple[str, list[str], dict]:
    """
    Valida um atendimento.

    Regras:

    - válido: todos os campos necessários estão corretos;
    - incompleto: há campos obrigatórios ausentes;
    - inválido: os campos existem, mas possuem valores inválidos.
    """
    r = dict(record)
    reasons: list[str] = []

    # ---------------------------------------------------------
    # Protocolo
    # ---------------------------------------------------------
    protocol = (
        r.get("protocolo", "")
        .strip()
        .upper()
    )

    r["protocolo"] = protocol

    if not protocol:
        reasons.append("protocolo_ausente")
    elif not PROTO_RE.fullmatch(protocol):
        reasons.append("protocolo_invalido")

    # ---------------------------------------------------------
    # Data
    # ---------------------------------------------------------
    r["data_obj"] = parse_date(
        r.get("data", "")
    )

    if not r["data_obj"]:
        if r.get("data", "").strip():
            reasons.append("data_invalida")
        else:
            reasons.append("data_ausente")

    # ---------------------------------------------------------
    # E-mail
    # ---------------------------------------------------------
    email = r.get("email", "").strip()

    if not email:
        reasons.append("email_ausente")
    elif not EMAIL_RE.fullmatch(email):
        reasons.append("email_invalido")

    # ---------------------------------------------------------
    # CEP
    # ---------------------------------------------------------
    cep = r.get("cep", "").strip()
    r["cep"] = cep

    if not cep:
        reasons.append("cep_ausente")
    elif not CEP_RE.fullmatch(cep):
        reasons.append("cep_invalido")

    # ---------------------------------------------------------
    # Categoria
    # ---------------------------------------------------------
    r["categoria_normalizada"] = normalize_category(
        r.get("categoria", ""),
        categories,
    )

    if not r["categoria_normalizada"]:
        if r.get("categoria", "").strip():
            reasons.append("categoria_invalida")
        else:
            reasons.append("categoria_ausente")

    # ---------------------------------------------------------
    # Tempo
    # ---------------------------------------------------------
    tempo = r.get("tempo_minutos", "").strip()

    try:
        r["tempo_obj"] = float(
            tempo.replace(",", ".")
        )

        if r["tempo_obj"] < 0:
            raise ValueError

    except (ValueError, TypeError):
        r["tempo_obj"] = None

        if tempo:
            reasons.append("tempo_invalido")
        else:
            reasons.append("tempo_ausente")

    # ---------------------------------------------------------
    # Campos obrigatórios
    # ---------------------------------------------------------
    if not r.get("solicitante", "").strip():
        reasons.append("solicitante_ausente")

    if not r.get("descricao", "").strip():
        reasons.append("descricao_ausente")

    # ---------------------------------------------------------
    # Classificação
    # ---------------------------------------------------------
    if not reasons:
        classification = "valido"

    elif any(
        reason.endswith("_ausente")
        for reason in reasons
    ):
        classification = "incompleto"

    else:
        classification = "invalido"

    return classification, reasons, r
