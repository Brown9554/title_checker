import base64
import io
import os
from typing import List

import pdfplumber
from anthropic import Anthropic


class DocumentReaderError(Exception):
    """Raised when a document cannot be processed."""


def _pdf_to_page_images(pdf_path: str) -> List[bytes]:
    """Render each page of a PDF to an image and return the image bytes."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    images: List[bytes] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            try:
                page_image = page.to_image(resolution=300).original
                if isinstance(page_image, bytes):
                    image_bytes = page_image
                else:
                    buffer = io.BytesIO()
                    page_image.save(buffer, format="PNG")
                    image_bytes = buffer.getvalue()
                images.append(image_bytes)
            except Exception as exc:
                raise DocumentReaderError(f"Unable to render page {len(images) + 1}: {exc}") from exc
    return images


def _get_cache_path(pdf_path: str) -> str:
    """Get the cache file path for a given PDF."""
    base_path = os.path.splitext(pdf_path)[0]
    return f"{base_path}.txt"


def _load_cache(pdf_path: str) -> str | None:
    """Load cached extracted text if it exists."""
    cache_path = _get_cache_path(pdf_path)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None
    return None


def _save_cache(pdf_path: str, content: str) -> None:
    """Save extracted text to cache file."""
    cache_path = _get_cache_path(pdf_path)
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        pass  # Silently skip cache save on error


def _image_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def _extract_text_from_image(image_bytes: bytes, api_key: str) -> str:
    client = Anthropic(api_key=api_key)

    encoded_image = _image_to_base64(image_bytes)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system="You are an expert at reading Massachusetts registry of deeds documents. Extract all text and information you can see in this document image, including handwritten notes, stamps, marginalia, and typed text. Preserve the structure and layout as much as possible.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": encoded_image,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Please extract all visible text and details from this page.",
                    },
                ],
            }
        ],
    )

    return response.content[0].text if response.content and hasattr(response.content[0], "text") else ""


def read_document(pdf_path: str) -> str:
    """Read a PDF document page by page, extract text using Claude Vision, and return the concatenated text."""
    # Check cache first
    cached_content = _load_cache(pdf_path)
    if cached_content is not None:
        return cached_content

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise DocumentReaderError("ANTHROPIC_API_KEY environment variable is not set")

    try:
        page_images = _pdf_to_page_images(pdf_path)
    except Exception as exc:
        raise DocumentReaderError(f"Failed to read PDF: {exc}") from exc

    extracted_pages: List[str] = []
    for index, image_bytes in enumerate(page_images, start=1):
        try:
            page_text = _extract_text_from_image(image_bytes, api_key)
            extracted_pages.append(page_text.strip())
        except Exception as exc:
            extracted_pages.append(f"[Error reading page {index}: {exc}]")

    result = "\n\n".join(part for part in extracted_pages if part)
    _save_cache(pdf_path, result)
    return result
