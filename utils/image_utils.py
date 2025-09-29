"""
Image processing utilities for OCR
"""

import io
import logging
from typing import Optional, Tuple
from PIL import Image, ImageEnhance, ImageFilter
from fastapi import UploadFile

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {
    'image/jpeg',
    'image/jpg', 
    'image/png',
    'image/webp',
    'image/heic',
    'image/heif'
}

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_DIMENSIONS = (4096, 4096)

def validate_image(file: UploadFile) -> bool:
    """Validate image file type and size"""
    try:
        # Check content type
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            logger.warning(f"Invalid content type: {file.content_type}")
            return False
        
        # Check file size
        if hasattr(file, 'size') and file.size and file.size > MAX_IMAGE_SIZE:
            logger.warning(f"File too large: {file.size} bytes")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Image validation error: {str(e)}")
        return False

def preprocess_image(image_bytes: bytes) -> bytes:
    """
    Preprocess image for better OCR results
    - Resize if too large
    - Enhance contrast and sharpness
    - Convert to grayscale if needed
    """
    try:
        # Open image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert HEIC/HEIF if needed
        if image.format in ['HEIC', 'HEIF']:
            image = image.convert('RGB')
        
        # Resize if too large
        if image.size[0] > MAX_DIMENSIONS[0] or image.size[1] > MAX_DIMENSIONS[1]:
            logger.info(f"Resizing image from {image.size}")
            image.thumbnail(MAX_DIMENSIONS, Image.Resampling.LANCZOS)
        
        # Convert to RGB if not already
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Enhance for OCR
        image = enhance_for_ocr(image)
        
        # Convert back to bytes
        output = io.BytesIO()
        image.save(output, format='PNG', optimize=True)
        
        processed_bytes = output.getvalue()
        logger.info(f"Image preprocessed: {len(image_bytes)} -> {len(processed_bytes)} bytes")
        
        return processed_bytes
        
    except Exception as e:
        logger.error(f"Image preprocessing error: {str(e)}")
        # Return original bytes if preprocessing fails
        return image_bytes

def enhance_for_ocr(image: Image.Image) -> Image.Image:
    """
    Enhance image specifically for OCR
    - Increase contrast
    - Sharpen text
    - Reduce noise
    """
    try:
        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)
        
        # Sharpen for better text recognition
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.1)
        
        # Slight brightness adjustment
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.05)
        
        # Apply unsharp mask filter for text clarity
        image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=100, threshold=2))
        
        return image
        
    except Exception as e:
        logger.error(f"Image enhancement error: {str(e)}")
        return image

def extract_image_metadata(image_bytes: bytes) -> dict:
    """Extract useful metadata from image"""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        metadata = {
            'format': image.format,
            'mode': image.mode,
            'size': image.size,
            'width': image.size[0],
            'height': image.size[1],
            'has_transparency': image.mode in ('RGBA', 'LA') or 'transparency' in image.info
        }
        
        # Extract EXIF if available
        if hasattr(image, '_getexif') and image._getexif():
            exif = image._getexif()
            if exif:
                metadata['has_exif'] = True
                # Add specific EXIF tags if needed
                if 274 in exif:  # Orientation
                    metadata['orientation'] = exif[274]
        
        return metadata
        
    except Exception as e:
        logger.error(f"Metadata extraction error: {str(e)}")
        return {}

def create_thumbnail(image_bytes: bytes, size: Tuple[int, int] = (200, 200)) -> bytes:
    """Create thumbnail for preview"""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.thumbnail(size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85)
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Thumbnail creation error: {str(e)}")
        return image_bytes[:1000]  # Return first 1KB as fallback
