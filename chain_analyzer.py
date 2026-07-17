import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

from anthropic import Anthropic

ENTITY_PATTERN = re.compile(r"^book(\d+)_p\d+_.*_entities\.json$", re.IGNORECASE)


class ChainAnalyzerError(Exception):
    pass


def _load_taxonomy() -> Any:
    project_root = Path(__file__).resolve().parent
    taxonomy_path = project_root / "taxonomy.json"
    if not taxonomy_path.exists():
        raise ChainAnalyzerError(f"taxonomy.json not found at {taxonomy_path}")
    with open(taxonomy_path, "r", encoding="utf-8") as taxonomy_file:
        return json.load(taxonomy_file)


def _get_entity_files(documents_dir: Path) -> list[Path]:
    entity_files = [path for path in documents_dir.glob("*_entities.json") if path.is_file()]
    return sorted(
        entity_files,
        key=lambda path: int(ENTITY_PATTERN.match(path.name).group(1))
        if ENTITY_PATTERN.match(path.name)
        else float("inf"),
    )


def _load_entities(entity_file: Path) -> Any:
    with open(entity_file, "r", encoding="utf-8") as file:
        return json.load(file)


def _build_system_prompt(taxonomy: Any) -> str:
    taxonomy_text = json.dumps(taxonomy, indent=2)
    return (
        "You are an expert Massachusetts real estate title examiner with decades of experience.\n"
        "You will be given a chronologically ordered set of structured entities extracted from \n"
        "recorded registry of deeds documents for a single property.\n\n"
        "Analyze the complete chain of title and:\n"
        "1. Reconstruct the ownership history from first to current owner\n"
        "2. Identify all mortgages and determine whether each has been discharged, assigned, or remains open\n"
        "3. Flag any gaps in the chain of title where grantor/grantee continuity breaks\n"
        "4. Identify any unresolved notices, liens, or encumbrances\n"
        "5. Note any other title defects or items requiring attention\n\n"
        "Use this taxonomy as your reference:\n"
        f"{taxonomy_text}\n\n"
        "Return a JSON object with this structure:\n"
        "{\n"
        "  'ownership_history': list of {grantor, grantee, date, book, page, consideration},\n"
        "  'mortgage_status': list of {book, page, lender, borrower, date, status, discharged_by},\n"
        "  'open_encumbrances': list of any unresolved liens, notices, or encumbrances,\n"
        "  'risk_flags': list of {flag, severity, description, action},\n"
        "  'summary': plain English paragraph summarizing the title condition,\n"
        "  'title_condition': one of [clear, clouded, requires_review]\n"
        "}"
    )


def _call_anthropic(entities: list[Any], taxonomy: Any, api_key: str) -> str:
    client = Anthropic(api_key=api_key)
    system_prompt = _build_system_prompt(taxonomy)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(entities, indent=2),
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


def analyze_chain(property_folder: str) -> dict[str, Any]:
    property_path = Path(property_folder)
    documents_dir = property_path / "documents"
    if not documents_dir.exists() or not documents_dir.is_dir():
        raise ChainAnalyzerError(f"Documents directory not found: {documents_dir}")

    entity_files = _get_entity_files(documents_dir)
    if not entity_files:
        raise ChainAnalyzerError(f"No entity cache files found in {documents_dir}")

    entities = [_load_entities(entity_file) for entity_file in entity_files]
    taxonomy = _load_taxonomy()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ChainAnalyzerError("ANTHROPIC_API_KEY environment variable is not set")

    response_text = _call_anthropic(entities, taxonomy, api_key)
    cleaned_text = re.sub(r"```json\s*", "", response_text, flags=re.IGNORECASE)
    cleaned_text = re.sub(r"```\s*", "", cleaned_text)
    cleaned_text = cleaned_text.strip()

    try:
        analysis = json.loads(cleaned_text)
    except json.JSONDecodeError as exc:
        raise ChainAnalyzerError(f"Unable to parse Anthropic response as JSON: {exc}\nResponse was:\n{cleaned_text}") from exc

    output_path = property_path / "chain_analysis.json"
    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(analysis, output_file, indent=2)

    return analysis


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze the chain of title for a property using cached entity JSONs."
    )
    parser.add_argument("property_folder", help="Property folder path, e.g. properties/3-Hawthorne")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = analyze_chain(args.property_folder)
    print(json.dumps(result, indent=2))
