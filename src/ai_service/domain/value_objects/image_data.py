"""Image data value object for receipt and photo processing."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from enum import Enum
import hashlib
from typing import Any


class ImageFormat(str, Enum):
    """Supported image formats."""

    JPEG = "jpeg"
    JPG = "jpg"
    PNG = "png"
    WEBP = "webp"
    GIF = "gif"
    BMP = "bmp"
    TIFF = "tiff"

    @classmethod
    def from_mime_type(cls, mime_type: str) -> ImageFormat:
        """Create ImageFormat from MIME type."""
        mime_mapping = {
            "image/jpeg": cls.JPEG,
            "image/jpg": cls.JPG,
            "image/png": cls.PNG,
            "image/webp": cls.WEBP,
            "image/gif": cls.GIF,
            "image/bmp": cls.BMP,
            "image/tiff": cls.TIFF,
        }
        return mime_mapping.get(mime_type.lower(), cls.JPEG)

    @classmethod
    def from_extension(cls, extension: str) -> ImageFormat:
        """Create ImageFormat from file extension."""
        ext = extension.lower().lstrip('.')
        try:
            return cls(ext)
        except ValueError:
            return cls.JPEG  # Default fallback

    def get_mime_type(self) -> str:
        """Get MIME type for the format."""
        mime_types = {
            self.JPEG: "image/jpeg",
            self.JPG: "image/jpeg",
            self.PNG: "image/png",
            self.WEBP: "image/webp",
            self.GIF: "image/gif",
            self.BMP: "image/bmp",
            self.TIFF: "image/tiff",
        }
        return mime_types.get(self, "image/jpeg")

    def is_suitable_for_ocr(self) -> bool:
        """Check if format is suitable for OCR processing."""
        ocr_friendly = {self.JPEG, self.JPG, self.PNG, self.TIFF}
        return self in ocr_friendly


class ImageQuality(str, Enum):
    """Image quality levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXCELLENT = "excellent"

    @classmethod
    def from_size_and_dimensions(cls, size_bytes: int, width: int, height: int) -> ImageQuality:
        """Determine quality from size and dimensions."""
        total_pixels = width * height
        bytes_per_pixel = size_bytes / total_pixels if total_pixels > 0 else 0

        if bytes_per_pixel > 3 and total_pixels > 2_000_000:
            return cls.EXCELLENT
        elif bytes_per_pixel > 2 and total_pixels > 1_000_000:
            return cls.HIGH
        elif bytes_per_pixel > 1 and total_pixels > 500_000:
            return cls.MEDIUM
        else:
            return cls.LOW


@dataclass(frozen=True)
class ImageDimensions:
    """Image dimensions value object."""

    width: int
    height: int

    def __post_init__(self) -> None:
        """Validate dimensions."""
        if self.width <= 0 or self.height <= 0:
            msg = f"Invalid dimensions: {self.width}x{self.height}"
            raise ValueError(msg)

    def get_aspect_ratio(self) -> float:
        """Get aspect ratio (width/height)."""
        return self.width / self.height

    def get_total_pixels(self) -> int:
        """Get total pixel count."""
        return self.width * self.height

    def is_portrait(self) -> bool:
        """Check if image is portrait orientation."""
        return self.height > self.width

    def is_landscape(self) -> bool:
        """Check if image is landscape orientation."""
        return self.width > self.height

    def is_square(self) -> bool:
        """Check if image is square."""
        return self.width == self.height

    def is_high_resolution(self) -> bool:
        """Check if image is high resolution (>= 1920x1080)."""
        return self.width >= 1920 and self.height >= 1080

    def __str__(self) -> str:
        """String representation."""
        return f"{self.width}x{self.height}"


@dataclass(frozen=True)
class ImageData:
    """Immutable image data value object for OCR processing."""

    data: bytes
    format: ImageFormat
    dimensions: ImageDimensions | None = None
    filename: str | None = None

    def __post_init__(self) -> None:
        """Validate image data."""
        if not isinstance(self.data, bytes):
            msg = f"Image data must be bytes, got {type(self.data)}"
            raise TypeError(msg)

        if len(self.data) == 0:
            msg = "Image data cannot be empty"
            raise ValueError(msg)

        # Size limits (10MB max)
        max_size = 10 * 1024 * 1024
        if len(self.data) > max_size:
            msg = f"Image too large: {len(self.data)} bytes (max {max_size})"
            raise ValueError(msg)

        # Basic format validation
        if not self._validate_format():
            msg = f"Invalid image format: {self.format}"
            raise ValueError(msg)

    def _validate_format(self) -> bool:
        """Validate image format matches data."""
        if len(self.data) < 4:
            return False

        # Check magic bytes for common formats
        magic_bytes = self.data[:4]

        format_signatures = {
            ImageFormat.JPEG: [b'\xff\xd8\xff'],
            ImageFormat.JPG: [b'\xff\xd8\xff'],
            ImageFormat.PNG: [b'\x89PNG'],
            ImageFormat.GIF: [b'GIF8'],
            ImageFormat.BMP: [b'BM'],
            ImageFormat.WEBP: [b'RIFF'],  # Simplified check
        }

        signatures = format_signatures.get(self.format, [])
        return any(magic_bytes.startswith(sig) for sig in signatures)

    @classmethod
    def from_base64(
        cls,
        base64_data: str,
        format: ImageFormat,
        filename: str | None = None
    ) -> ImageData:
        """Create ImageData from base64 encoded string."""
        try:
            # Remove data URL prefix if present
            if base64_data.startswith('data:'):
                base64_data = base64_data.split(',', 1)[1]

            data = base64.b64decode(base64_data)
            return cls(data=data, format=format, filename=filename)
        except Exception as e:
            msg = f"Failed to decode base64 image data: {e}"
            raise ValueError(msg) from e

    def to_base64(self) -> str:
        """Convert image data to base64 string."""
        return base64.b64encode(self.data).decode('utf-8')

    def get_data_url(self) -> str:
        """Get data URL for the image."""
        mime_type = self.format.get_mime_type()
        base64_data = self.to_base64()
        return f"data:{mime_type};base64,{base64_data}"

    def get_size_bytes(self) -> int:
        """Get image size in bytes."""
        return len(self.data)

    def get_size_kb(self) -> float:
        """Get image size in kilobytes."""
        return len(self.data) / 1024

    def get_size_mb(self) -> float:
        """Get image size in megabytes."""
        return len(self.data) / (1024 * 1024)

    def get_hash(self) -> str:
        """Get SHA-256 hash of image data."""
        return hashlib.sha256(self.data).hexdigest()

    def get_quality(self) -> ImageQuality:
        """Get estimated image quality."""
        if self.dimensions:
            return ImageQuality.from_size_and_dimensions(
                self.get_size_bytes(),
                self.dimensions.width,
                self.dimensions.height
            )
        else:
            # Quality based on size alone
            size_mb = self.get_size_mb()
            if size_mb > 5:
                return ImageQuality.EXCELLENT
            elif size_mb > 2:
                return ImageQuality.HIGH
            elif size_mb > 0.5:
                return ImageQuality.MEDIUM
            else:
                return ImageQuality.LOW

    def is_suitable_for_ocr(self) -> bool:
        """Check if image is suitable for OCR processing."""
        # Format check
        if not self.format.is_suitable_for_ocr():
            return False

        # Size check (not too small, not too large)
        size_kb = self.get_size_kb()
        if size_kb < 10 or size_kb > 5000:  # 10KB to 5MB range
            return False

        # Quality check
        quality = self.get_quality()
        return quality in {ImageQuality.MEDIUM, ImageQuality.HIGH, ImageQuality.EXCELLENT}

    def get_estimated_ocr_confidence(self) -> float:
        """Get estimated OCR confidence based on image characteristics."""
        base_confidence = 0.5

        # Format bonus
        if self.format in {ImageFormat.PNG, ImageFormat.TIFF}:
            base_confidence += 0.2
        elif self.format in {ImageFormat.JPEG, ImageFormat.JPG}:
            base_confidence += 0.1

        # Quality bonus
        quality = self.get_quality()
        quality_bonus = {
            ImageQuality.EXCELLENT: 0.3,
            ImageQuality.HIGH: 0.2,
            ImageQuality.MEDIUM: 0.1,
            ImageQuality.LOW: 0.0,
        }
        base_confidence += quality_bonus[quality]

        # Size penalty for very large or very small images
        size_mb = self.get_size_mb()
        if size_mb > 8 or size_mb < 0.05:
            base_confidence -= 0.1

        return min(1.0, max(0.1, base_confidence))

    def get_processing_recommendations(self) -> list[str]:
        """Get recommendations for optimal processing."""
        recommendations = []

        if not self.is_suitable_for_ocr():
            recommendations.append("Image may not be suitable for OCR processing")

        quality = self.get_quality()
        if quality == ImageQuality.LOW:
            recommendations.append("Consider using a higher quality image")

        size_mb = self.get_size_mb()
        if size_mb > 5:
            recommendations.append("Consider compressing image to reduce processing time")
        elif size_mb < 0.1:
            recommendations.append("Image may be too small for accurate text recognition")

        if self.dimensions:
            if self.dimensions.width < 300 or self.dimensions.height < 300:
                recommendations.append("Image resolution may be too low for OCR")

        return recommendations

    def __str__(self) -> str:
        """String representation."""
        size_info = f"{self.get_size_kb():.1f}KB"
        dim_info = str(self.dimensions) if self.dimensions else "unknown"
        filename_info = f" ({self.filename})" if self.filename else ""

        return f"ImageData({self.format.value}, {size_info}, {dim_info}{filename_info})"

    def __eq__(self, other: Any) -> bool:
        """Check equality based on data hash."""
        if not isinstance(other, ImageData):
            return False
        return self.get_hash() == other.get_hash()

    def __len__(self) -> int:
        """Get data length."""
        return len(self.data)
