"""Extração por rótulos, normalização e validação dos atendimentos."""
from __future__ import annotations

from datetime import date, datetime
from difflib import SequenceMatcher
import re
import unicodedata
from typing import Any

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PROTO_RE = re.compile(r"^AT-\d{3}$")
CEP_RE = re.compile(r"^\d{5}-\d{3}$")

# Variações previsíveis produzidas pelo OCR nos rótulos do formulário.
_LABEL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("protocolo", re.compile(r"\bprotoc(?:olo|ol|ob|o)?\b", re.I)),
    ("data", re.compile(r"\bdata\b", re.I)),
    ("solicitante", re.compile(r"\bs\s*olicitante\b", re.I)),
    ("email", re.compile(r"\be\s*-?\s*m\s*ail\b|\bemail\b|\bemal\b", re.I)),
    ("categoria", re.compile(r"\bcategoria\b", re.I)),
    ("status", re.compile(r"\bstatus\b|\bstaus\b|\bsous\b", re.I)),
    (
        "cep",
        re.compile(
            r"\bcep\s*/?\s*c[ií]?\s*dade\b|\bcep\s*/?\s*cidade\b|\bcep\b",
            re.I,
        ),
    ),
    ("tempo_minutos", re.compile(r"\btem\s*po\b", re.I)),
    ("descricao", re.compile(r"\bprobl(?:ema|em|m|km)\s*a?\b", re.I)),
    ("solucao", re.compile(r"\bsolu[cç][aã]o\b|\bsolicao\b", re.I)),
    ("observacoes", re.compile(r"\bobserva(?:coes|ções|cões|cao)\b", re.I)),
]
_FIELD_ORDER = [
    "protocolo",
    "data",
    "solicitante",
    "email",
    "categoria",
    "status",
    "cep",
    "tempo_minutos",
    "descricao",
    "solucao",
    "observacoes",
]

# Aceita AT-051, AT 051, AT -@52, AT ®67 e até espaços entre os dígitos.
_PROTOCOL_LABEL_RE = re.compile(
    r"\bprotoc(?:olo|ol|ob|o)?\b"
    r"(?=\s*(?:\||:)?\s*(?:"
    r"AT\s*[-–—®]?\s*[0-9OQ@IL®]\s*[0-9OQ@IL®]\s*[0-9OQ@IL®]"
    r"|PROTOCOLO\?))",
    re.I,
)
_MISSING_MARKERS = {"", "[vazio]", "vazio", "n/a", "na", "null", "none", "-"}
_TRANSLATE_OCR_DIGITS = str.maketrans(
    {"O": "0", "Q": "0", "@": "0", "I": "1", "L": "1", "®": "0"}
)


def clean_text(text: str) -> str:
    """Remove NUL e uniformiza espaços sem modificar o texto bruto armazenado."""
    return re.sub(r"\s+", " ", str(text or "").replace("\x00", " ")).strip()


def normalize_key(value: str) -> str:
    """Gera chave comparável sem acentos e com espaços uniformes."""
    value = (
        unicodedata.normalize("NFKD", str(value or ""))
        .encode("ascii", "ignore")
        .decode()
        .lower()
        .strip()
    )
    return re.sub(r"\s+", " ", value)


def _compact_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", normalize_key(value))


def _normalize_missing(value: Any) -> str:
    text = clean_text(str(value or ""))
    key = normalize_key(text)
    if key in _MISSING_MARKERS or "[vazio]" in key:
        return ""
    return text


def split_records(page_text: str) -> list[str]:
    """Divide uma página em atendimentos, tolerando pequenas distorções do OCR."""
    clean = clean_text(page_text)
    matches = list(_PROTOCOL_LABEL_RE.finditer(clean))
    if not matches:
        return []

    records: list[str] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(clean)
        raw = clean[match.start() : end].strip()
        if raw:
            records.append(raw)
    return records


def _extract_ordered_fields(text: str) -> dict[str, str]:
    """Extrai valores entre rótulos respeitando a ordem do formulário."""
    clean = clean_text(text)
    positions: dict[str, re.Match[str]] = {}
    cursor = 0
    for field, pattern in _LABEL_PATTERNS:
        match = pattern.search(clean, cursor)
        if match is None:
            continue
        positions[field] = match
        cursor = match.end()

    result = {field: "" for field in _FIELD_ORDER}
    for index, field in enumerate(_FIELD_ORDER):
        match = positions.get(field)
        if match is None:
            continue
        end = len(clean)
        for next_field in _FIELD_ORDER[index + 1 :]:
            next_match = positions.get(next_field)
            if next_match is not None and next_match.start() >= match.end():
                end = next_match.start()
                break
        result[field] = clean_text(clean[match.end() : end].strip(" |:;\t\n"))
    return result


def _normalize_protocol(value: str) -> str:
    value = _normalize_missing(value).upper()
    if not value:
        return ""
    match = re.search(
        r"\bAT\s*[-–—®]?\s*([0-9OQ@IL®])\s*([0-9OQ@IL®])\s*([0-9OQ@IL®])\b",
        value,
        re.I,
    )
    if not match:
        return value.strip()
    digits = "".join(match.groups()).upper().translate(_TRANSLATE_OCR_DIGITS)
    return f"AT-{digits}"


def _normalize_cep(value: str) -> str:
    value = _normalize_missing(value)
    if not value:
        return ""
    match = re.search(r"\b(\d{5})\s*-?\s*(\d{3})\b", value)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    token = value.split()[0] if value.split() else value
    return token.strip("|,;:")


def _normalize_email(value: str) -> str:
    value = _normalize_missing(value)
    if not value:
        return ""
    # O OCR insere espaços dentro de e-mails; removê-los é uma correção sintática.
    return re.sub(r"\s+", "", value).strip("|,;:")


def _normalize_time(value: str) -> str:
    value = _normalize_missing(value)
    if not value:
        return ""
    match = re.search(r"-?\d+(?:[.,]\d+)?", value)
    return match.group(0).replace(",", ".") if match else value


def extract_fields(text: str) -> dict[str, str]:
    """Extrai e faz normalizações sintáticas seguras dos campos."""
    result = _extract_ordered_fields(text)
    result["protocolo"] = _normalize_protocol(result["protocolo"])
    result["email"] = _normalize_email(result["email"])
    result["cep"] = _normalize_cep(result["cep"])
    result["tempo_minutos"] = _normalize_time(result["tempo_minutos"])
    for field in (
        "data",
        "solicitante",
        "categoria",
        "status",
        "descricao",
        "solucao",
        "observacoes",
    ):
        result[field] = _normalize_missing(result[field])
    return result


def parse_date(value: str) -> date | None:
    """Converte datas ISO/BR e datas com separadores perdidos pelo OCR."""
    value = _normalize_missing(value)
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass

    digits = re.sub(r"\D", "", value)
    if len(digits) == 8:
        formats = ("%Y%m%d", "%d%m%Y") if digits.startswith("20") else ("%d%m%Y",)
        for fmt in formats:
            try:
                return datetime.strptime(digits, fmt).date()
            except ValueError:
                pass
    return None


def _best_fuzzy_match(target: str, candidates: list[tuple[str, str]], cutoff: float) -> str | None:
    compact_target = _compact_key(target)
    if not compact_target:
        return None
    best_name: str | None = None
    best_score = 0.0
    for candidate_key, canonical_name in candidates:
        score = SequenceMatcher(None, compact_target, candidate_key).ratio()
        if score > best_score:
            best_score = score
            best_name = canonical_name
    return best_name if best_score >= cutoff else None


def normalize_category(value: str, categories: dict[str, Any]) -> str | None:
    """Mapeia categoria oficial/variação e pequenas distorções do OCR."""
    target = normalize_key(value)
    if not target:
        return None
    candidates: list[tuple[str, str]] = []
    for item in categories.get("categorias_oficiais", []):
        canonical = str(item["nome"])
        for name in [canonical, *item.get("variacoes", [])]:
            if target == normalize_key(name) or _compact_key(target) == _compact_key(name):
                return canonical
            candidates.append((_compact_key(name), canonical))
    return _best_fuzzy_match(value, candidates, cutoff=0.66)


def normalize_status(value: str, categories: dict[str, Any]) -> str | None:
    """Padroniza status contra a lista oficial."""
    target = normalize_key(value)
    if not target:
        return None
    statuses = [str(item) for item in categories.get("status_validos", [])]
    for status in statuses:
        if target == normalize_key(status) or _compact_key(target) == _compact_key(status):
            return status
    return _best_fuzzy_match(
        value, [(_compact_key(status), status) for status in statuses], cutoff=0.70
    )


def _add_missing_or_invalid(
    reasons: list[str],
    missing_reason: str,
    invalid_reason: str,
    raw_value: str,
    is_valid: bool,
) -> None:
    if not _normalize_missing(raw_value):
        reasons.append(missing_reason)
    elif not is_valid:
        reasons.append(invalid_reason)


def is_valid_protocol(value: str) -> bool:
    """Indica se um protocolo pode ser usado como chave de negócio."""
    return bool(PROTO_RE.fullmatch(_normalize_protocol(value)))


def validate_record(
    record: dict[str, Any], categories: dict[str, Any]
) -> tuple[str, list[str], dict[str, Any]]:
    """Classifica o registro em ``valido``, ``incompleto`` ou ``invalido``.

    ``duplicado`` é aplicado posteriormente, pois depende do banco/histórico.
    """
    normalized = dict(record)
    reasons: list[str] = []

    protocol = _normalize_protocol(str(record.get("protocolo", "")))
    normalized["protocolo"] = protocol
    _add_missing_or_invalid(
        reasons,
        "protocolo_ausente",
        "protocolo_invalido",
        protocol,
        bool(PROTO_RE.fullmatch(protocol)),
    )

    raw_date = _normalize_missing(record.get("data", ""))
    normalized["data_texto"] = raw_date
    normalized["data_obj"] = parse_date(raw_date)
    _add_missing_or_invalid(
        reasons, "data_ausente", "data_invalida", raw_date, normalized["data_obj"] is not None
    )

    email = _normalize_email(str(record.get("email", "")))
    normalized["email"] = email
    _add_missing_or_invalid(
        reasons, "email_ausente", "email_invalido", email, bool(EMAIL_RE.fullmatch(email))
    )

    cep = _normalize_cep(str(record.get("cep", "")))
    normalized["cep"] = cep
    _add_missing_or_invalid(
        reasons, "cep_ausente", "cep_invalido", cep, bool(CEP_RE.fullmatch(cep))
    )

    raw_category = _normalize_missing(record.get("categoria", ""))
    normalized["categoria_normalizada"] = normalize_category(raw_category, categories)
    _add_missing_or_invalid(
        reasons,
        "categoria_ausente",
        "categoria_invalida",
        raw_category,
        normalized["categoria_normalizada"] is not None,
    )

    raw_status = _normalize_missing(record.get("status", ""))
    normalized["status_normalizado"] = normalize_status(raw_status, categories)
    _add_missing_or_invalid(
        reasons,
        "status_ausente",
        "status_invalido",
        raw_status,
        normalized["status_normalizado"] is not None,
    )

    raw_time = _normalize_time(str(record.get("tempo_minutos", "")))
    normalized["tempo_obj"] = None
    if not raw_time:
        reasons.append("tempo_ausente")
    else:
        try:
            time_value = float(raw_time)
            if time_value < 0:
                raise ValueError
            normalized["tempo_obj"] = time_value
        except (ValueError, TypeError):
            reasons.append("tempo_invalido")

    for required in ("solicitante", "descricao"):
        value = _normalize_missing(record.get(required, ""))
        normalized[required] = value
        if not value:
            reasons.append(f"{required}_ausente")

    normalized["solucao"] = _normalize_missing(record.get("solucao", ""))
    normalized["observacoes"] = _normalize_missing(record.get("observacoes", ""))

    if any(reason.endswith("_ausente") for reason in reasons):
        classification = "incompleto"
    elif reasons:
        classification = "invalido"
    else:
        classification = "valido"
    return classification, reasons, normalized
