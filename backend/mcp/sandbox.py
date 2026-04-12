import re
import logging

logger = logging.getLogger(__name__)

CYPHER_WRITE_KEYWORDS = ["CREATE", "MERGE", "DELETE", "DETACH DELETE", "SET", "REMOVE", "DROP", "CALL"]
SQL_WRITE_KEYWORDS = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE TABLE"]

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"you\s+are\s+now",
    r"system\s*:\s*",
    r"assistant\s*:\s*",
    r"forget\s+(everything|all)",
    r"new\s+directive",
    r"override\s+(safety|security|rules)",
    r"jailbreak",
    r"pretend\s+you\s+are",
    r"act\s+as\s+(if|a)",
]

PII_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
}


def validate_cypher(query: str) -> list[str]:
    violations = []
    upper = query.upper().strip()
    for kw in CYPHER_WRITE_KEYWORDS:
        if upper.startswith(kw) or f" {kw} " in upper:
            violations.append(f"Write operation not allowed: {kw}")
    return violations


def validate_sql(query: str) -> list[str]:
    violations = []
    upper = query.upper().strip()
    for kw in SQL_WRITE_KEYWORDS:
        if upper.startswith(kw) or f" {kw} " in upper:
            violations.append(f"Write operation not allowed: {kw}")
    return violations


def detect_prompt_injection(text: str) -> list[str]:
    violations = []
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            violations.append("Potential prompt injection detected")
            break
    return violations


def redact_pii(text: str) -> str:
    for pii_type, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", text)
    return text


def validate_inputs(tool_name: str, params: dict) -> list[str]:
    violations = []

    if tool_name == "neo4j_query":
        query = params.get("cypher_query", params.get("query", ""))
        violations.extend(validate_cypher(query))

    if tool_name == "erp_query":
        query = params.get("sql_query", params.get("query", ""))
        violations.extend(validate_sql(query))

    for key, value in params.items():
        if isinstance(value, str):
            violations.extend(detect_prompt_injection(value))

    return violations
