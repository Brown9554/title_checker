import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import streamlit as st
except ImportError:  # pragma: no cover - exercised when streamlit is unavailable in tests
    st = None


def discover_properties(properties_dir: Path) -> list[str]:
    if not properties_dir.exists() or not properties_dir.is_dir():
        return []

    return sorted(
        [path.name for path in properties_dir.iterdir() if path.is_dir() and not path.name.startswith(".")]
    )


def sort_risk_flags(flags: list[dict[str, Any]]) -> list[dict[str, Any]]:
    severity_order = {"high": 0, "medium": 1, "low": 2}

    def severity_rank(flag: dict[str, Any]) -> int:
        severity = str(flag.get("severity", "")).strip().lower()
        return severity_order.get(severity, 99)

    return sorted(flags, key=lambda flag: (severity_rank(flag), str(flag.get("flag", "")).lower()))


def _load_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _run_analysis(property_name: str, project_root: Path) -> tuple[bool, str]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return False, "ANTHROPIC_API_KEY environment variable is not set."

    property_dir = project_root / "properties" / property_name
    batch_command = [sys.executable, str(project_root / "batch_process.py"), str(property_dir)]
    chain_command = [sys.executable, str(project_root / "chain_analyzer.py"), str(property_dir)]

    batch_result = subprocess.run(
        batch_command,
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if batch_result.returncode != 0:
        stderr = batch_result.stderr.strip() or batch_result.stdout.strip()
        return False, f"Batch processing failed:\n{stderr}"

    chain_result = subprocess.run(
        chain_command,
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if chain_result.returncode != 0:
        stderr = chain_result.stderr.strip() or chain_result.stdout.strip()
        return False, f"Chain analysis failed:\n{stderr}"

    return True, "Analysis completed successfully."


def _render_documents_tab(property_dir: Path) -> None:
    documents_dir = property_dir / "documents"
    pdf_files = sorted([path for path in documents_dir.glob("*.pdf") if path.is_file()])

    if not pdf_files:
        st.info("No PDFs found in this property's documents folder.")
        return

    for pdf_path in pdf_files:
        entity_path = pdf_path.with_name(f"{pdf_path.stem}_entities.json")
        with st.expander(pdf_path.name, expanded=False):
            if entity_path.exists():
                entity_data = _load_json(entity_path)
                st.code(json.dumps(entity_data, indent=2), language="json")
            else:
                st.write("No entity cache JSON was found for this document.")


def _render_chain_analysis_tab(property_dir: Path) -> None:
    chain_analysis_path = property_dir / "chain_analysis.json"
    chain_analysis = _load_json(chain_analysis_path)

    if chain_analysis is None:
        st.info("No chain_analysis.json found yet for this property.")
        return

    st.json(chain_analysis)


def _render_risk_flags_tab(property_dir: Path) -> None:
    chain_analysis_path = property_dir / "chain_analysis.json"
    chain_analysis = _load_json(chain_analysis_path)

    if chain_analysis is None:
        st.info("No chain_analysis.json found yet for this property.")
        return

    risk_flags = chain_analysis.get("risk_flags") or []
    if not risk_flags:
        st.success("No risk flags were reported.")
        return

    for flag in sort_risk_flags(list(risk_flags)):
        severity = str(flag.get("severity", "low")).strip().lower()
        title = flag.get("flag") or "Unnamed flag"
        description = flag.get("description") or ""
        action = flag.get("action") or ""

        if severity == "high":
            st.error(f"**{title}**\n\n{description}\n\nAction: {action}")
        elif severity == "medium":
            st.warning(f"**{title}**\n\n{description}\n\nAction: {action}")
        else:
            st.info(f"**{title}**\n\n{description}\n\nAction: {action}")


def main() -> None:
    if st is None:
        raise SystemExit("Streamlit is required. Install it with 'pip install streamlit'.")

    st.set_page_config(page_title="Title Checker", layout="wide")
    st.title("Title Checker")

    project_root = Path(__file__).resolve().parent
    properties_dir = project_root / "properties"
    properties = discover_properties(properties_dir)

    if not properties:
        st.error("No property folders were found under the properties directory.")
        st.stop()

    with st.sidebar:
        st.header("Property")
        selected_property = st.selectbox("Choose a property", properties)

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            st.success("Anthropic API key detected from the environment.")
        else:
            st.warning("ANTHROPIC_API_KEY is not set.")

        if st.button("Run Analysis", type="primary"):
            with st.spinner("Running batch processing and chain analysis..."):
                success, message = _run_analysis(selected_property, project_root)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    property_dir = properties_dir / selected_property
    documents_tab, chain_tab, risk_tab = st.tabs(["Documents", "Chain Analysis", "Risk Flags"])

    with documents_tab:
        _render_documents_tab(property_dir)

    with chain_tab:
        _render_chain_analysis_tab(property_dir)

    with risk_tab:
        _render_risk_flags_tab(property_dir)


if __name__ == "__main__":
    main()
