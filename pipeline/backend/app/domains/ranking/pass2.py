"""Step 5, pass 2 — the critic. DESIGN.md: "The LLM reasoner over the
complaint and the photo, given no signals... Pass 2 is an error detector,
not a voter — its ranking is never merged into Pass 1's."

llama-3.1-8b-instant is text-only, so "the photo" here means the complaint
text plus station/material metadata only — never fingerprint.axes (pass
1's structured answers) and never fingerprint.signals. That's what makes
this a genuinely different view rather than pass 1 re-read: if a vision-
capable model is swapped in later, the image bytes are the only thing to
add here, not the axis answers.
"""

import json
import re

from app.domains.causes.vocabulary import load_causes
from app.domains.llm import client as llm_client


def critic_pass(
    complaint_text: str | None, dispenser_class: str, material_family: str
) -> list[dict] | None:
    """Returns [{cause_id, likelihood_pct}, ...] or None if unavailable."""
    if not llm_client.is_configured():
        return None

    causes = load_causes()
    cause_list = "\n".join(f"- {c['id']}: {c['label']}" for c in causes)
    reply = llm_client.chat(
        [
            {
                "role": "system",
                "content": (
                    "You are a dispensing-defect triage assistant. Given only an "
                    "operator's complaint and basic machine context (no measurements), "
                    "rank how likely each candidate cause is. Reply with strict JSON: "
                    '[{"cause_id": "...", "likelihood_pct": 0-100}, ...] for every '
                    "candidate cause listed, nothing else."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Dispenser class: {dispenser_class}\nMaterial family: {material_family}\n"
                    f"Complaint: {complaint_text or '(not given)'}\n\nCandidate causes:\n{cause_list}"
                ),
            },
        ],
        max_tokens=700,
    )
    if reply is None:
        return None

    match = re.search(r"\[.*\]", reply, re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group())
    except json.JSONDecodeError:
        return None

    valid_ids = {c["id"] for c in causes}
    out = [
        {"cause_id": item["cause_id"], "likelihood_pct": float(item["likelihood_pct"])}
        for item in parsed
        if isinstance(item, dict) and item.get("cause_id") in valid_ids
    ]
    return out or None
