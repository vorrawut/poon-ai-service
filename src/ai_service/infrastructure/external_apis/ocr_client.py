"""OCR client using Tesseract."""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
import tempfile
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class TesseractOCRClient:
    """OCR client using Tesseract."""

    def __init__(
        self, tesseract_path: str | None = None, languages: str = "eng+tha"
    ) -> None:
        """Initialize OCR client."""
        self.tesseract_path = tesseract_path or "tesseract"
        self.languages = languages
        self._available: bool | None = None

    def is_available(self) -> bool:
        """Check if Tesseract is available."""
        if self._available is None:
            self._available = shutil.which(self.tesseract_path) is not None
        return self._available

    async def extract_text(
        self, image_data: bytes | str, language: str | None = None
    ) -> dict[str, Any]:
        """Extract text from image using Tesseract OCR."""
        if not self.is_available():
            return {
                "success": False,
                "error": "Tesseract OCR not available",
                "text": "",
                "confidence": 0.0,
            }

        try:
            # Use provided language or default
            ocr_language = language or self.languages

            # Handle both bytes and file path inputs
            if isinstance(image_data, str):
                # It's a file path
                temp_image_path = image_data
                cleanup_temp = False
            else:
                # It's bytes data - create temporary file
                with tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False
                ) as temp_image:
                    temp_image.write(image_data)
                    temp_image_path = temp_image.name
                cleanup_temp = True

            try:
                # Run Tesseract OCR
                result = subprocess.run(  # nosec B603
                    [
                        self.tesseract_path,
                        temp_image_path,
                        "stdout",
                        "-l",
                        ocr_language,
                        "--oem",
                        "3",  # Use LSTM OCR Engine Mode
                        "--psm",
                        "6",  # Assume a single uniform block of text
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                extracted_text = result.stdout.strip()

                # Try to get confidence (if available)
                confidence = await self._get_confidence(temp_image_path, ocr_language)

                return {
                    "success": True,
                    "text": extracted_text,
                    "confidence": confidence,
                    "language": ocr_language,
                    "method": "tesseract",
                }

            finally:
                # Clean up temporary file only if we created it
                if cleanup_temp:
                    Path(temp_image_path).unlink(missing_ok=True)

        except subprocess.CalledProcessError as e:
            logger.error("Tesseract OCR failed", error=e.stderr)
            return {
                "success": False,
                "error": f"OCR processing failed: {e.stderr}",
                "text": "",
                "confidence": 0.0,
            }
        except Exception as e:
            logger.error("OCR error", error=str(e))
            return {"success": False, "error": str(e), "text": "", "confidence": 0.0}

    async def _get_confidence(self, image_path: str, language: str) -> float:
        """Get OCR confidence score."""
        try:
            # Run Tesseract with TSV output to get confidence
            result = subprocess.run(  # nosec B603
                [
                    self.tesseract_path,
                    image_path,
                    "stdout",
                    "-l",
                    language,
                    "--oem",
                    "3",
                    "--psm",
                    "6",
                    "-c",
                    "tessedit_create_tsv=1",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse TSV output to extract confidence values
            lines = result.stdout.strip().split("\n")
            confidences = []

            for line in lines[1:]:  # Skip header
                parts = line.split("\t")
                if len(parts) >= 11 and parts[10].strip():  # conf column
                    try:
                        conf = float(parts[10])
                        if conf > 0:  # Only include positive confidence values
                            confidences.append(conf)
                    except ValueError:
                        continue

            if confidences:
                # Return average confidence as a value between 0 and 1
                avg_confidence = sum(confidences) / len(confidences)
                return min(1.0, max(0.0, avg_confidence / 100.0))

            return 0.5  # Default confidence if we can't determine

        except Exception:
            return 0.5  # Default confidence on error
