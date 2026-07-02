"""
LLM abstraction with graceful offline fallback.

- If an Anthropic/OpenAI key is configured -> real LLM generation with grounded prompt.
- Otherwise -> deterministic EXTRACTIVE answer built from the retrieved chunks, so the
  demo always produces a cited, sensible answer even with no key and no internet.
"""
from __future__ import annotations

import re

from . import config

SYSTEM_PROMPT = (
    "You are the Expert Knowledge Copilot for an industrial plant's unified knowledge base. "
    "Answer the engineer's question ONLY using the provided document excerpts. "
    "Every factual claim must be grounded in the excerpts. Cite sources inline using the "
    "bracket tags exactly as given, e.g. [WO-2024-1187]. If the excerpts do not contain the "
    "answer, say so plainly. Be concise, technical, and practical — this is read by field "
    "technicians and engineers. When a piece of equipment has a failure history, connect the "
    "dots across the documents (work orders, near-miss, inspection) rather than listing them."
)


def _build_user_prompt(question: str, contexts: list[dict]) -> str:
    blocks = []
    for c in contexts:
        blocks.append(f"[{c['doc_id']}]  (type: {c['doc_type']})\n{c['text']}")
    joined = "\n\n---\n\n".join(blocks)
    return (
        f"DOCUMENT EXCERPTS:\n\n{joined}\n\n"
        f"QUESTION: {question}\n\n"
        "Answer with inline [DOC-ID] citations. End with a one-line 'Sources:' list of the "
        "document IDs you used."
    )


# --- circuit breaker: after a permanent failure (bad key / no quota) we stop calling
# the LLM for the rest of the session so every query falls back INSTANTLY (~10ms)
# instead of paying the API round-trip + error latency on every request. ---
_llm_disabled = False
_llm_disabled_reason = ""
_PERMANENT = ("insufficient_quota", "invalid_api_key", "authentication",
              "401", "403", "429", "permission")


def llm_status() -> dict:
    return {"disabled": _llm_disabled, "reason": _llm_disabled_reason}


def _trip_breaker(err: Exception) -> None:
    global _llm_disabled, _llm_disabled_reason
    msg = str(err).lower()
    if any(tok in msg for tok in _PERMANENT):
        _llm_disabled = True
        _llm_disabled_reason = str(err)[:200]
        print(f"[llm] circuit breaker OPEN — LLM disabled for session ({_llm_disabled_reason})")


def generate_answer(question: str, contexts: list[dict]) -> tuple[str, str]:
    """Return (answer_text, mode) where mode is 'llm' or 'offline'."""
    if not _llm_disabled:
        if config.LLM_PROVIDER == "anthropic" and config.ANTHROPIC_API_KEY:
            try:
                return _anthropic(question, contexts), "llm"
            except Exception as e:
                print(f"[llm] Anthropic call failed ({e}); falling back to offline")
                _trip_breaker(e)
        elif config.LLM_PROVIDER == "openai" and config.OPENAI_API_KEY:
            try:
                return _openai(question, contexts), "llm"
            except Exception as e:
                print(f"[llm] OpenAI call failed ({e}); falling back to offline")
                _trip_breaker(e)
    return _offline(question, contexts), "offline"


def _anthropic(question: str, contexts: list[dict]) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=900,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_prompt(question, contexts)}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


def _openai(question: str, contexts: list[dict]) -> str:  # pragma: no cover
    from openai import OpenAI
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(question, contexts)},
    ]
    # SDK 2.x / newer models prefer max_completion_tokens; fall back to max_tokens.
    try:
        resp = client.chat.completions.create(
            model=config.OPENAI_MODEL, max_completion_tokens=900, messages=messages,
        )
    except TypeError:
        resp = client.chat.completions.create(
            model=config.OPENAI_MODEL, max_tokens=900, messages=messages,
        )
    return (resp.choices[0].message.content or "").strip()


def _offline(question: str, contexts: list[dict]) -> str:
    """
    Deterministic extractive answer: pick the sentences from the retrieved chunks that
    best overlap the question keywords, grouped by source document, with inline citations.
    Not as fluent as an LLM, but grounded, cited, and 100% reliable for a live demo.
    """
    q_terms = set(t for t in re.findall(r"[a-z0-9-]+", question.lower()) if len(t) > 2)
    scored: list[tuple[float, str, str]] = []  # (score, doc_id, sentence)
    for c in contexts:
        for sent in re.split(r"(?<=[.\n])\s+", c["text"]):
            s = sent.strip()
            if len(s) < 25:
                continue
            terms = set(re.findall(r"[a-z0-9-]+", s.lower()))
            overlap = len(q_terms & terms)
            # bonus for exact tag matches (e.g. PUMP-204)
            tag_bonus = sum(2 for t in q_terms if "-" in t and t in s.lower())
            score = overlap + tag_bonus
            if score > 0:
                scored.append((score, c["doc_id"], s))
    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        return ("I couldn't find information matching that question in the current document "
                "corpus. Try naming a specific equipment tag (e.g. PUMP-204), a regulation "
                "(e.g. OISD-STD-105), or a document type.")

    # Take top sentences, keep source order stable, dedupe
    picked: list[tuple[str, str]] = []
    seen_sents = set()
    for _, doc_id, sent in scored[:8]:
        key = sent[:60]
        if key in seen_sents:
            continue
        seen_sents.add(key)
        picked.append((doc_id, sent))

    lines = ["Based on the plant knowledge base:\n"]
    for doc_id, sent in picked:
        sent = re.sub(r"\s+", " ", sent).strip()
        # strip leading ALL-CAPS section labels e.g. "WORK PERFORMED: - Isolated…"
        sent = re.sub(r"^[A-Z][A-Z0-9 /&()-]{3,}:\s*-?\s*", "", sent).rstrip(".")
        if len(sent) < 20:
            continue
        lines.append(f"- {sent}. [{doc_id}]")
    srcs = sorted({d for d, _ in picked})
    lines.append("\nSources: " + ", ".join(srcs))
    return "\n".join(lines)


# ---- optional LLM-based entity extraction (augments regex; not required) ----
def extract_entities_llm(text: str) -> list[dict]:  # pragma: no cover (optional)
    if not (config.LLM_PROVIDER == "anthropic" and config.ANTHROPIC_API_KEY):
        return []
    import anthropic, json
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    tool = {
        "name": "record_entities",
        "description": "Record industrial entities found in the text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "type": {"type": "string",
                                     "enum": ["equipment", "personnel", "regulatory",
                                              "location", "material"]},
                        },
                        "required": ["id", "type"],
                    },
                }
            },
            "required": ["entities"],
        },
    }
    msg = client.messages.create(
        model=config.ANTHROPIC_MODEL, max_tokens=800, tools=[tool],
        tool_choice={"type": "tool", "name": "record_entities"},
        messages=[{"role": "user", "content": f"Extract entities:\n{text}"}],
    )
    for b in msg.content:
        if getattr(b, "type", "") == "tool_use":
            return b.input.get("entities", [])
    return []
