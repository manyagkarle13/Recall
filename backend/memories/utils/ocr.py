"""
OCR Text Extraction Utility for Recall.
Uses RapidOCR (ONNX-based) for high-accuracy local text extraction without system binaries,
with graceful fallback to PyTesseract.
Automatically copies images to media/screenshots/ for frontend previewing.
"""

import io
import re
import os
import uuid
import base64
import logging
from typing import Tuple, Dict, Any
from PIL import Image

logger = logging.getLogger(__name__)

_rapid_ocr_engine = None

def get_rapid_ocr():
    global _rapid_ocr_engine
    if _rapid_ocr_engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _rapid_ocr_engine = RapidOCR()
        except Exception as e:
            logger.warning(f"Could not initialize RapidOCR: {e}")
            _rapid_ocr_engine = False
    return _rapid_ocr_engine if _rapid_ocr_engine is not False else None


def save_image_to_media(image: Image.Image, filename: str) -> Tuple[str, str]:
    """Saves image to media/screenshots/ and returns (disk_path, media_url)."""
    from django.conf import settings
    media_root = getattr(settings, "MEDIA_ROOT", None)
    if not media_root:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        media_root = os.path.join(base_dir, "media")

    save_dir = os.path.join(media_root, "screenshots")
    os.makedirs(save_dir, exist_ok=True)
    
    clean_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
    unique_name = f"{uuid.uuid4().hex[:6]}_{clean_name}"
    disk_path = os.path.join(save_dir, unique_name)
    image.save(disk_path)
    media_url = f"/media/screenshots/{unique_name}"
    return disk_path, media_url


def extract_text_from_image_file(file_obj, filename: str = "image.png") -> Tuple[str, Dict[str, Any]]:
    """Extracts text from uploaded image file and saves image to media."""
    try:
        if hasattr(file_obj, "read"):
            raw_bytes = file_obj.read()
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
        elif isinstance(file_obj, (bytes, bytearray)):
            raw_bytes = bytes(file_obj)
        else:
            raw_bytes = bytes(file_obj)

        image = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        return _process_image_ocr(image, filename)
    except Exception as e:
        logger.exception(f"Failed to process image file {filename}")
        return f"[Error processing image: {str(e)}]", {"error": str(e)}


def extract_text_from_screenshot(image_data: str, filename: str = "screenshot.png") -> Tuple[str, Dict[str, Any]]:
    """Extracts text from base64 screenshot data URI."""
    try:
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return _process_image_ocr(image, filename)
    except Exception as e:
        logger.exception("Failed to process screenshot image")
        return f"[Error processing screenshot: {str(e)}]", {"error": str(e)}


def _process_image_ocr(image: Image.Image, filename: str) -> Tuple[str, Dict[str, Any]]:
    width, height = image.size
    
    # Save image to media
    try:
        disk_path, media_url = save_image_to_media(image, filename)
    except Exception as save_err:
        logger.warning(f"Could not save image to media: {save_err}")
        disk_path, media_url = "", ""

    metadata = {
        "image_dimensions": f"{width}x{height}",
        "source": filename,
        "media_url": media_url,
        "disk_path": disk_path,
        "is_image": True,
    }

    # 1. Try RapidOCR
    rapid_engine = get_rapid_ocr()
    if rapid_engine:
        try:
            # Pass numpy array or PIL image
            import numpy as np
            np_img = np.array(image)
            ocr_res, elapse = rapid_engine(np_img)
            if ocr_res:
                lines = [item[1] for item in ocr_res if item and len(item) > 1]
                extracted_text = " ".join(lines).strip()
                if extracted_text:
                    metadata["ocr_engine"] = "rapidocr-onnx"
                    metadata["extracted_character_count"] = len(extracted_text)
                    return extracted_text, metadata
        except Exception as rapid_err:
            logger.warning(f"RapidOCR failed: {rapid_err}")

    # 2. Fallback to PyTesseract
    try:
        import pytesseract
        text = pytesseract.image_to_string(image, config="--psm 3")
        cleaned = re.sub(r"\s+", " ", text).strip()
        if cleaned:
            metadata["ocr_engine"] = "pytesseract"
            metadata["extracted_character_count"] = len(cleaned)
            return cleaned, metadata
    except Exception as tess_err:
        logger.warning(f"PyTesseract failed: {tess_err}")

    # If no text found in image
    no_text_msg = f"[Image capture: {filename} ({width}x{height}px) - No text detected in image]"
    metadata["ocr_engine"] = "none"
    metadata["extracted_character_count"] = 0
    return no_text_msg, metadata
