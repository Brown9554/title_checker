import json
import os
import re
from typing import Any, Dict

from anthropic import Anthropic


class EntityExtractorError(Exception):
    """Raised when entity extraction cannot be completed."""


TAXONOMY_PATH = os.path.join(os.path.dirname(__file__), "properties", "taxonomy.json")
try:
    with open(TAXONOMY_PATH, "r", encoding="utf-8") as taxonomy_file:
        TAXONOMY = json.load(taxonomy_file)
except Exception as exc:
    raise RuntimeError(f"Unable to load taxonomy from {TAXONOMY_PATH}: {exc}") from exc


def _get_cache_path(filename: str) -> str:
    base_path = os.path.splitext(filename)[0]
    return f"{base_path}_entities.json"


def _load_cache(filename: str) -> str | None:
    cache_path = _get_cache_path(filename)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as cache_file:
                return cache_file.read()
        except Exception:
            return None
    return None


def _save_cache(filename: str, content: str) -> None:
    cache_path = _get_cache_path(filename)
    try:
        with open(cache_path, "w", encoding="utf-8") as cache_file:
            cache_file.write(content)
    except Exception:
        pass


def _build_system_prompt() -> str:
    taxonomy_text = json.dumps(TAXONOMY, indent=2)
    return (
        "You are an expert at analyzing Massachusetts registry of deeds documents.\n"
        "Extract structured information from the provided document text and return\n"
        "ONLY a valid JSON object with no preamble or markdown formatting.\n\n"
        "Use this taxonomy as your source of truth for document types, states, \n"
        "party roles, and risk flags:\n"
        f"{taxonomy_text}\n\n"
        "Return a JSON object with these fields:\n"
        "document_type, subtype, date (YYYY-MM-DD), book, page, parties \n"
        "(grantor, grantee, lender, borrower as lists), consideration (numeric),\n"
        "references (list of {book, page, type} objects for any prior documents \n"
        "referenced), state, risk_flags, notes"
    )


def _call_anthropic(raw_text: str, api_key: str) -> str:
    client = Anthropic(api_key=api_key)
    system_prompt = _build_system_prompt()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": raw_text,
                    }
                ],
            }
        ],
    )

    if not response.content:
        return ""

    first_chunk = response.content[0]
    if hasattr(first_chunk, "text"):
        return first_chunk.text or ""
    if isinstance(first_chunk, dict):
        return first_chunk.get("text", "") or ""
    return ""


def _clean_response_text(response_text: str) -> str:
    cleaned = re.sub(r"```json\s*", "", response_text, flags=re.IGNORECASE)
    cleaned = re.sub(r"```\s*", "", cleaned)
    return cleaned.strip()


def extract_entities(raw_text: str, filename: str) -> Dict[str, Any]:
    cached = _load_cache(filename)
    if cached is not None:
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            pass

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EntityExtractorError("ANTHROPIC_API_KEY environment variable is not set")

    response_text = _call_anthropic(raw_text, api_key)
    cleaned_response = _clean_response_text(response_text)
    try:
        result = json.loads(cleaned_response)
    except json.JSONDecodeError:
        result = {
            "document_type": "requires_review",
            "notes": response_text,
        }

    _save_cache(filename, json.dumps(result, indent=2))
    return result
