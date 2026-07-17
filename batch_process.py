import argparse
import re
from pathlib import Path

from document_reader import read_document
from entity_extractor import extract_entities

PDF_PATTERN = re.compile(r"^book(\d+)_p\d+_.*\.pdf$", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch process property PDFs to extract text and structured entities."
    )
    parser.add_argument(
        "property_folder",
        help="Property folder path, e.g. properties/3-Hawthorne",
    )
    return parser.parse_args()


def get_pdf_files(documents_dir: Path) -> list[Path]:
    pdf_files = [path for path in documents_dir.glob("*.pdf") if path.is_file()]
    sorted_files = sorted(
        pdf_files,
        key=lambda path: int(PDF_PATTERN.match(path.name).group(1))
        if PDF_PATTERN.match(path.name)
        else float("inf"),
    )
    return sorted_files


def main() -> None:
    args = parse_args()
    property_path = Path(args.property_folder)
    documents_dir = property_path / "documents"

    if not documents_dir.exists() or not documents_dir.is_dir():
        raise SystemExit(f"Documents directory not found: {documents_dir}")

    pdf_files = get_pdf_files(documents_dir)
    total_files = len(pdf_files)

    if total_files == 0:
        print(f"No PDF files found in {documents_dir}")
        return

    processed = 0
    skipped = 0
    failed = 0

    for index, pdf_path in enumerate(pdf_files, start=1):
        filename = pdf_path.name
        entities_cache_path = pdf_path.with_name(f"{pdf_path.stem}_entities.json")

        if entities_cache_path.exists():
            print(f"Skipping (cached): {filename}")
            skipped += 1
            continue

        print(f"Processing {index}/{total_files}: {filename}...", end=" ")
        try:
            raw_text = read_document(str(pdf_path))
            extract_entities(raw_text, str(pdf_path))
            print("done")
            processed += 1
        except Exception as exc:
            print("failed")
            print(f"Error processing {filename}: {exc}")
            failed += 1

    print("\nSummary:")
    print(f"  Processed: {processed}")
    print(f"  Skipped:   {skipped}")
    print(f"  Failed:    {failed}")


if __name__ == "__main__":
    main()
