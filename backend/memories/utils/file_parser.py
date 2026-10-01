"""
File parsing utility for extracting text and metadata from uploaded files.
Handles plain text (.txt, .md), PDFs (.pdf), and images (.png, .jpg, .jpeg, .webp, .bmp).
"""

import os
import io
import hashlib
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Media directories
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "media")
PDF_MEDIA_DIR = os.path.join(MEDIA_ROOT, "pdfs")
SCREENSHOT_MEDIA_DIR = os.path.join(MEDIA_ROOT, "screenshots")


def _safe_filename(name: str) -> str:
    """Make a safe filename by replacing special chars."""
    import re
    name = re.sub(r'[^\w\s\-.]', '_', name)
    name = re.sub(r'[\s]+', '_', name)
    return name[:80]


def extract_content_from_file(file_obj, filename: str) -> Tuple[str, str, dict]:
    """
    Extracts text content and inferred source type from uploaded file.
    Also saves file to media directory for serving.

    Returns:
        (extracted_text, inferred_source_type, metadata_dict)
    """
    ext = os.path.splitext(filename)[1].lower()
    metadata = {"filename": filename, "extension": ext}

    if ext in [".txt", ".md", ".markdown", ".csv", ".json", ".log"]:
        content_bytes = file_obj.read()
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        try:
            text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = content_bytes.decode("latin-1", errors="ignore")
        return text, "text", metadata

    elif ext == ".pdf":
        text_parts = []
        try:
            if hasattr(file_obj, "read"):
                raw_bytes = file_obj.read()
                if hasattr(file_obj, "seek"):
                    file_obj.seek(0)
            elif isinstance(file_obj, (bytes, bytearray)):
                raw_bytes = bytes(file_obj)
            else:
                raw_bytes = bytes(file_obj)

            pdf_stream = io.BytesIO(raw_bytes)

            try:
                import pypdf
                reader = pypdf.PdfReader(pdf_stream)
                metadata["num_pages"] = len(reader.pages)
                for idx, page in enumerate(reader.pages):
                    extracted = page.extract_text()
                    if extracted:
                        text_parts.append(extracted.strip())
                text = "\n\n".join(text_parts).strip()
            except ImportError:
                import PyPDF2
                reader = PyPDF2.PdfReader(pdf_stream)
                metadata["num_pages"] = len(reader.pages)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text_parts.append(extracted.strip())
                text = "\n\n".join(text_parts).strip()

            if not text:
                text = f"[PDF file: {filename} ({metadata.get('num_pages', 0)} pages) contained no parseable text or contains scanned images]"
            metadata["extracted_character_count"] = len(text)

            # Save PDF file to media/pdfs/ so it can be served/opened
            try:
                os.makedirs(PDF_MEDIA_DIR, exist_ok=True)
                prefix = hashlib.md5(raw_bytes[:256]).hexdigest()[:6]
                safe_name = _safe_filename(filename)
                disk_filename = f"{prefix}_{safe_name}"
                disk_path = os.path.join(PDF_MEDIA_DIR, disk_filename)
                with open(disk_path, "wb") as f:
                    f.write(raw_bytes)
                metadata["media_url"] = f"/media/pdfs/{disk_filename}"
                metadata["disk_path"] = disk_path
                logger.info(f"Saved PDF to {disk_path}")
            except Exception as save_err:
                logger.warning(f"Could not save PDF to media: {save_err}")

            return text, "pdf", metadata

        except Exception as e:
            logger.exception(f"Error parsing PDF {filename}: {e}")
            metadata["error"] = str(e)
            metadata["error_detail"] = repr(e)
            return f"[Error parsing PDF: {filename}: {str(e)}]", "pdf", metadata

    elif ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
        from .ocr import extract_text_from_image_file
        extracted_text, ocr_metadata = extract_text_from_image_file(file_obj, filename=filename)
        metadata.update(ocr_metadata)
        metadata["is_image"] = True
        return extracted_text, "screenshot", metadata

    else:
        try:
            content = file_obj.read().decode("utf-8", errors="ignore")
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
            return content, "text", metadata
        except Exception as e:
            return f"[Unsupported file type: {filename}]", "text", {"error": str(e)}
