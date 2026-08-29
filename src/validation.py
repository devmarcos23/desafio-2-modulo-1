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

# O PDF digital possui os rótulos corretos. O PDF escaneado, porém, gera
# pequenas variações previsíveis no OCR ("Protocol", "Tem po", "Problem a").
# As expressões abaixo normalizam somente os rótulos, nunca o conteúdo livre.
_LABEL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("protocolo", re.compile(r"\bprotoc(?:olo|ol|ob|o)?\b", re.I)),
    ("data", re.compile(r"\bdata\b", re.I)),
    ("solicitante", re.compile(r"\bs\s*olicitante\b", re.I)),
    (
        "email",
        re.compile(r"\be\s*-?\s*m\s*ail\b|\bemail\b|\bemal\b", re.I),
    ),
    ("categoria", re.compile(r"\bcategoria\b", re.I)),
    ("status", re.compile(r"\bstatus\b|\bstaus\b|\bsous\b", re.I)),
    (
        "cep",
        re.compile(r"\bcep\s*/?\s*c[ií]?\s*dade\b|\bcep\s*/?\s*cidade\b", re.I),
    ),
    ("tempo_minutos", re.compile(r"\btem\s*po\b", re.I)),
    (
        "descricao",
        re.compile(r"\bprobl(?:ema|em|m|km)\s*a?\b", re.I),
    ),
    ("solucao", re.compile(r"\bsolu[cç][aã]o\b|\bsolicao\b", re.I)),
    (
        "observacoes",
        re.compile(r"\bobserva(?:coes|ções)\b", re.I),
    ),
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

_PROTOCOL_LABEL_RE = re.compile(
    (
        r"\bprotoc(?:olo|ol|ob|o)?\b"
        r"(?=\s*(?:\||:)?\s*(?:AT\s*[-–—]?\s*[0-9OQ@IL®]{3}|PROTOCOLO\?))"
    ),
    re.I,
)
_MISSING_MARKERS = {"", "[vazio]", "vazio", "n/a", "na", "null", "none", "-"}


def clean_text(text: str) -> str:
    """Remove NUL e uniformiza espaços sem apagar o texto original armazenado."""
    text = text.replace("\x00", " ")
    return re.sub(r"\s+", " ", text).strip()


def split_records(page_text: str) -> list[str]:
    """Divide uma página em registros reconhecendo variações OCR de Protocolo.

    O rótulo só é aceito como início de registro quando é seguido por um código
    do tipo ``AT-000`` (com pequenas trocas comuns de OCR) ou por
    ``PROTOCOLO?``. Isso evita dividir o texto em frases como
    "mesmo protocolo para teste de deduplicação".
    """
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
    """Extrai valores entre rótulos respeitando a ordem do formulário.

    A busca sequencial é importante: palavras como "problema" e "categoria"
    também podem aparecer dentro dos valores e não devem ser confundidas com
    novos rótulos.
    """
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

        value = clean[match.end() : end].strip(" |:;\t\n")
        result[field] = clean_text(value)

    return result


def _normalize_missing(value: Any) -> str:
    text = clean_text(str(value or ""))
    key = normalize_key(text)
    if key in _MISSING_MARKERS or "[vazio]" in key:
        return ""
    return text


def _normalize_protocol(value: str) -> str:
    value = _normalize_missing(value).upper()
    if not value:
        return ""

    # O OCR pode trocar o zero por O/Q/@ e inserir espaços ao redor do hífen.
    match = re.search(r"\bAT\s*[-–—]?\s*([0-9OQ@IL®]{3})\b", value, re.I)
    if not match:
        return value.strip()

    digits = match.group(1).upper().translate(
        str.maketrans({"O": "0", "Q": "0", "@": "0", "I": "1", "L": "1", "®": "0"})
    )
    return f"AT-{digits}"


def _normalize_cep(value: str) -> str:
    value = _normalize_missing(value)
    if not value:
        return ""

    match = re.search(r"\b(\d{5})\s*-?\s*(\d{3})\b", value)
    if match:
        return f"{match.group(1)}-{match.group(2)}"

    # Mantém a parte candidata para que a validação informe formato inválido.
    token = value.split()[0] if value.split() else value
    return token.strip()


def _normalize_email(value: str) -> str:
    value = _normalize_missing(value)
    if not value:
        return ""

    # Espaços não são válidos em e-mails e aparecem com frequência entre
    # caracteres no OCR. Removê-los é uma correção sintática segura.
    return re.sub(r"\s+", "", value).strip("|,;:")


def _normalize_time(value: str) -> str:
    value = _normalize_missing(value)
    if not value:
        return ""
    match = re.search(r"-?\d+(?:[.,]\d+)?", value)
    return match.group(0).replace(",", ".") if match else value


def extract_fields(text: str) -> dict[str, str]:
    """Extrai campos de registros digitais e de texto proveniente de OCR."""
    result = _extract_ordered_fields(text)
    result["protocolo"] = _normalize_protocol(result["protocolo"])
    result["email"] = _normalize_email(result["email"])
    result["cep"] = _normalize_cep(result["cep"])
    result["tempo_minutos"] = _normalize_time(result["tempo_minutos"])

    text_fields = (
        "data",
        "solicitante",
        "categoria",
        "status",
        "descricao",
        "solucao",
        "observacoes",
    )
    for field in text_fields:
        result[field] = _normalize_missing(result[field])
    return result


def parse_date(value: str) -> date | None:
    """Converte datas ISO, brasileiras e pequenas perdas de separador do OCR."""
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


def normalize_key(value: str) -> str:
    """Gera chave comparável sem acentos e com espaços uniformes."""
    value = (
        unicodedata.normalize("NFKD", str(value))
        .encode("ascii", "ignore")
        .decode()
        .lower()
        .strip()
    )
    return re.sub(r"\s+", " ", value)


def _compact_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", normalize_key(value))


def _best_fuzzy_match(
    target: str, candidates: list[tuple[str, str]], cutoff: float
) -> str | None:
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
    """Mapeia categoria oficial, variação declarada ou pequena distorção de OCR."""
    target = normalize_key(value)
    if not target:
        return None

    candidates: list[tuple[str, str]] = []
    for item in categories.get("categorias_oficiais", []):
        canonical = item["nome"]
        names = [canonical, *item.get("variacoes", [])]
        for name in names:
            if (
                target == normalize_key(name)
                or _compact_key(target) == _compact_key(name)
            ):
                return canonical
            candidates.append((_compact_key(name), canonical))

    # Corrige somente variações curtas de OCR; categorias realmente diferentes
    # (ex.: "categoria desconhecida") ficam inválidas.
    return _best_fuzzy_match(value, candidates, cutoff=0.66)


def normalize_status(value: str, categories: dict[str, Any]) -> str | None:
    """Padroniza o status usando a lista oficial do arquivo de categorias."""
    target = normalize_key(value)
    if not target:
        return None

    valid_statuses = [str(item) for item in categories.get("status_validos", [])]
    for status in valid_statuses:
        if (
            target == normalize_key(status)
            or _compact_key(target) == _compact_key(status)
        ):
            return status

    candidates = [(_compact_key(status), status) for status in valid_statuses]
    return _best_fuzzy_match(value, candidates, cutoff=0.70)


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
    """Retorna ``True`` quando o protocolo já está no formato oficial."""
    return bool(PROTO_RE.fullmatch(_normalize_protocol(value)))

def validate_record(
    record: dict[str, Any], categories: dict[str, Any]
) -> tuple[str, list[str], dict[str, Any]]:
    """Valida e classifica um registro como válido, incompleto ou inválido.

    Regra de classificação:
    - ``incompleto``: existe ao menos um campo obrigatório ausente;
    - ``invalido``: campos estão presentes, mas um ou mais possuem formato ou
      domínio inválido;
    - ``valido``: nenhuma inconsistência foi identificada.

    A classificação ``duplicado`` depende do histórico persistido e, portanto,
    é aplicada posteriormente pelo pipeline/banco.
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
    normalized["data_obj"] = parse_date(raw_date)
    _add_missing_or_invalid(
        reasons,
        "data_ausente",
        "data_invalida",
        raw_date,
        normalized["data_obj"] is not None,
    )

    email = _normalize_email(str(record.get("email", "")))
    normalized["email"] = email
    _add_missing_or_invalid(
        reasons,
        "email_ausente",
        "email_invalido",
        email,
        bool(EMAIL_RE.fullmatch(email)),
    )

    cep = _normalize_cep(str(record.get("cep", "")))
    normalized["cep"] = cep
    _add_missing_or_invalid(
        reasons,
        "cep_ausente",
        "cep_invalido",
        cep,
        bool(CEP_RE.fullmatch(cep)),
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

    if any(reason.endswith("_ausente") for reason in reasons):
        classification = "incompleto"
    elif reasons:
        classification = "invalido"
    else:
        classification = "valido"

    return classification, reasons, normalized
