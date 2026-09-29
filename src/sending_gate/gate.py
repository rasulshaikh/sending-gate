from __future__ import annotations

import re
from typing import Any

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ROLE_LOCALS = {"info", "hello", "support", "admin", "sales", "contact", "team"}
PLACEHOLDER_MARKERS = ("{{", "}}", "TBD", "TODO", "[insert", "xxx@")
AI_SMELL = ("leverage", "synergy")


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _email_domain(email: str) -> str:
    if "@" not in email:
        return ""
    return email.split("@", 1)[1].lower()


def _derive_first_name(row: dict[str, Any]) -> str:
    first = _norm(row.get("first_name"))
    if first:
        return first
    full = _norm(row.get("full_name"))
    if full:
        return full.split()[0]
    return ""


def validate_row(
    row: dict[str, Any],
    *,
    reject_role_accounts: bool = True,
    seen_emails: set[str] | None = None,
) -> list[str]:
    """Return hard failure reasons (empty means validation passed)."""
    reasons: list[str] = []
    email = _norm(row.get("email")).lower()
    subject = _norm(row.get("subject"))
    body = _norm(row.get("body"))
    company = _norm(row.get("company_name"))
    first = _derive_first_name(row)

    if not email or not EMAIL_RE.match(email):
        reasons.append("invalid_or_missing_email")
    else:
        local = email.split("@", 1)[0]
        if reject_role_accounts and local in ROLE_LOCALS:
            reasons.append("role_account_email")
        if seen_emails is not None:
            if email in seen_emails:
                reasons.append("duplicate_email")
            else:
                seen_emails.add(email)

    if not first:
        reasons.append("missing_first_name")
    if not company:
        reasons.append("missing_company_name")
    if not subject:
        reasons.append("missing_subject")
    if not body:
        reasons.append("missing_body")

    blob = f"{subject}\n{body}"
    for marker in PLACEHOLDER_MARKERS:
        if marker.lower() in blob.lower() or marker in blob:
            reasons.append(f"placeholder:{marker}")
            break

    return reasons


def soft_flags(row: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    email = _norm(row.get("email")).lower()
    domain = _norm(row.get("company_domain")).lower().removeprefix("www.")
    if email and domain:
        ed = _email_domain(email)
        if ed and domain not in ed and ed not in domain:
            flags.append("email_domain_mismatch")
    if not domain:
        flags.append("missing_company_domain")

    body = _norm(row.get("body")).lower()
    for term in AI_SMELL:
        if term in body:
            flags.append(f"ai_smell:{term}")
    return flags


def score_row(row: dict[str, Any], flags: list[str]) -> int:
    score = 100
    body = _norm(row.get("body"))
    subject = _norm(row.get("subject"))
    words = len(body.split()) if body else 0

    if "missing_company_domain" in flags:
        score -= 5
    if "email_domain_mismatch" in flags:
        score -= 15
    if words and (words < 30 or words > 180):
        score -= 10
    if subject and (len(subject) < 8 or len(subject) > 80):
        score -= 5

    icp = row.get("icp_score")
    try:
        if icp is not None and float(icp) < 50:
            score -= 20
    except (TypeError, ValueError):
        pass

    email = _norm(row.get("email")).lower()
    if email and EMAIL_RE.match(email):
        local = email.split("@", 1)[0]
        if local in ROLE_LOCALS:
            score -= 25

    smell_hits = sum(1 for f in flags if f.startswith("ai_smell:"))
    score -= min(10, smell_hits * 5)

    return max(0, min(100, score))


def verdict_for(hard: list[str], score: int, flags: list[str]) -> str:
    if hard:
        return "FAIL"
    if score >= 80 and not flags:
        return "PASS"
    if score >= 60:
        return "FLAG"
    return "FAIL"


def evaluate_row(
    row: dict[str, Any],
    *,
    reject_role_accounts: bool = True,
    seen_emails: set[str] | None = None,
) -> dict[str, Any]:
    hard = validate_row(
        row, reject_role_accounts=reject_role_accounts, seen_emails=seen_emails
    )
    flags = soft_flags(row) if not hard else soft_flags(row)
    # If role account already hard-failed, still compute score for debugging
    sc = score_row(row, flags)
    ver = verdict_for(hard, sc, flags)
    return {
        "email": _norm(row.get("email")).lower(),
        "verdict": ver,
        "score": sc,
        "hard_failures": hard,
        "flags": flags,
    }


def evaluate_batch(
    rows: list[dict[str, Any]],
    *,
    reject_role_accounts: bool = True,
) -> dict[str, Any]:
    seen: set[str] = set()
    results = [
        evaluate_row(r, reject_role_accounts=reject_role_accounts, seen_emails=seen)
        for r in rows
    ]
    counts = {"PASS": 0, "FLAG": 0, "FAIL": 0}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    return {"counts": counts, "results": results}
