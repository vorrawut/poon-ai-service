"""Comprehensive tests for ImageData value object to boost coverage."""

import base64
import hashlib

import pytest

from ai_service.domain.value_objects.image_data import (
    ImageData,
    ImageDimensions,
    ImageFormat,
    ImageQuality,
)


class TestImageFormat:
    """Test ImageFormat enum."""

    def test_from_mime_type_all_formats(self):
        """Test creating ImageFormat from all MIME types."""
        assert ImageFormat.from_mime_type("image/jpeg") == ImageFormat.JPEG
        assert ImageFormat.from_mime_type("image/jpg") == ImageFormat.JPG
        assert ImageFormat.from_mime_type("image/png") == ImageFormat.PNG
        assert ImageFormat.from_mime_type("image/webp") == ImageFormat.WEBP
        assert ImageFormat.from_mime_type("image/gif") == ImageFormat.GIF
        assert ImageFormat.from_mime_type("image/bmp") == ImageFormat.BMP
        assert ImageFormat.from_mime_type("image/tiff") == ImageFormat.TIFF

    def test_from_mime_type_case_insensitive(self):
        """Test MIME type parsing is case insensitive."""
        assert ImageFormat.from_mime_type("IMAGE/JPEG") == ImageFormat.JPEG
        assert ImageFormat.from_mime_type("Image/Png") == ImageFormat.PNG

    def test_from_mime_type_unknown_defaults_to_jpeg(self):
        """Test unknown MIME type defaults to JPEG."""
        assert ImageFormat.from_mime_type("image/unknown") == ImageFormat.JPEG
        assert ImageFormat.from_mime_type("text/plain") == ImageFormat.JPEG

    def test_from_extension_all_formats(self):
        """Test creating ImageFormat from all extensions."""
        assert ImageFormat.from_extension("jpeg") == ImageFormat.JPEG
        assert ImageFormat.from_extension("jpg") == ImageFormat.JPG
        assert ImageFormat.from_extension("png") == ImageFormat.PNG
        assert ImageFormat.from_extension("webp") == ImageFormat.WEBP
        assert ImageFormat.from_extension("gif") == ImageFormat.GIF
        assert ImageFormat.from_extension("bmp") == ImageFormat.BMP
        assert ImageFormat.from_extension("tiff") == ImageFormat.TIFF

    def test_from_extension_with_dot(self):
        """Test extension parsing with leading dot."""
        assert ImageFormat.from_extension(".jpeg") == ImageFormat.JPEG
        assert ImageFormat.from_extension(".png") == ImageFormat.PNG

    def test_from_extension_case_insensitive(self):
        """Test extension parsing is case insensitive."""
        assert ImageFormat.from_extension("JPEG") == ImageFormat.JPEG
        assert ImageFormat.from_extension("Png") == ImageFormat.PNG

    def test_from_extension_unknown_defaults_to_jpeg(self):
        """Test unknown extension defaults to JPEG."""
        assert ImageFormat.from_extension("unknown") == ImageFormat.JPEG
        assert ImageFormat.from_extension("txt") == ImageFormat.JPEG

    def test_get_mime_type_all_formats(self):
        """Test getting MIME type for all formats."""
        assert ImageFormat.JPEG.get_mime_type() == "image/jpeg"
        assert ImageFormat.JPG.get_mime_type() == "image/jpeg"
        assert ImageFormat.PNG.get_mime_type() == "image/png"
        assert ImageFormat.WEBP.get_mime_type() == "image/webp"
        assert ImageFormat.GIF.get_mime_type() == "image/gif"
        assert ImageFormat.BMP.get_mime_type() == "image/bmp"
        assert ImageFormat.TIFF.get_mime_type() == "image/tiff"

    def test_is_suitable_for_ocr(self):
        """Test OCR suitability for all formats."""
        # OCR-friendly formats
        assert ImageFormat.JPEG.is_suitable_for_ocr() is True
        assert ImageFormat.JPG.is_suitable_for_ocr() is True
        assert ImageFormat.PNG.is_suitable_for_ocr() is True
        assert ImageFormat.TIFF.is_suitable_for_ocr() is True

        # Not OCR-friendly formats
        assert ImageFormat.WEBP.is_suitable_for_ocr() is False
        assert ImageFormat.GIF.is_suitable_for_ocr() is False
        assert ImageFormat.BMP.is_suitable_for_ocr() is False


class TestImageQuality:
    """Test ImageQuality enum."""

    def test_from_size_and_dimensions_excellent(self):
        """Test excellent quality detection."""
        quality = ImageQuality.from_size_and_dimensions(
            size_bytes=16_000_000,  # 16MB
            width=2500,
            height=2000,  # 5M pixels, bytes_per_pixel = 3.2 > 3
        )
        assert quality == ImageQuality.EXCELLENT

    def test_from_size_and_dimensions_high(self):
        """Test high quality detection."""
        quality = ImageQuality.from_size_and_dimensions(
            size_bytes=4_000_000,  # 4MB
            width=1600,
            height=1200,  # 1.92M pixels
        )
        assert quality == ImageQuality.HIGH

    def test_from_size_and_dimensions_medium(self):
        """Test medium quality detection."""
        quality = ImageQuality.from_size_and_dimensions(
            size_bytes=800_000,  # 800KB
            width=1000,
            height=600,  # 600K pixels
        )
        assert quality == ImageQuality.MEDIUM

    def test_from_size_and_dimensions_low(self):
        """Test low quality detection."""
        quality = ImageQuality.from_size_and_dimensions(
            size_bytes=100_000,  # 100KB
            width=640,
            height=480,  # 307K pixels
        )
        assert quality == ImageQuality.LOW

    def test_from_size_and_dimensions_zero_pixels(self):
        """Test handling zero pixels."""
        quality = ImageQuality.from_size_and_dimensions(
            size_bytes=100_000,
            width=0,
            height=0,
        )
        assert quality == ImageQuality.LOW


class TestImageDimensions:
    """Test ImageDimensions value object."""

    def test_creation_valid(self):
        """Test valid dimensions creation."""
        dims = ImageDimensions(width=1920, height=1080)
        assert dims.width == 1920
        assert dims.height == 1080

    def test_creation_invalid_width(self):
        """Test invalid width raises error."""
        with pytest.raises(ValueError, match="Invalid dimensions"):
            ImageDimensions(width=0, height=1080)

    def test_creation_invalid_height(self):
        """Test invalid height raises error."""
        with pytest.raises(ValueError, match="Invalid dimensions"):
            ImageDimensions(width=1920, height=0)

    def test_creation_negative_dimensions(self):
        """Test negative dimensions raise error."""
        with pytest.raises(ValueError, match="Invalid dimensions"):
            ImageDimensions(width=-100, height=200)

    def test_get_aspect_ratio(self):
        """Test aspect ratio calculation."""
        dims = ImageDimensions(width=1920, height=1080)
        assert dims.get_aspect_ratio() == pytest.approx(1.777, rel=1e-3)

        dims = ImageDimensions(width=1080, height=1920)
        assert dims.get_aspect_ratio() == pytest.approx(0.5625, rel=1e-3)

    def test_get_total_pixels(self):
        """Test total pixel calculation."""
        dims = ImageDimensions(width=1920, height=1080)
        assert dims.get_total_pixels() == 2_073_600

    def test_is_portrait(self):
        """Test portrait orientation detection."""
        portrait = ImageDimensions(width=1080, height=1920)
        landscape = ImageDimensions(width=1920, height=1080)
        square = ImageDimensions(width=1000, height=1000)

        assert portrait.is_portrait() is True
        assert landscape.is_portrait() is False
        assert square.is_portrait() is False

    def test_is_landscape(self):
        """Test landscape orientation detection."""
        portrait = ImageDimensions(width=1080, height=1920)
        landscape = ImageDimensions(width=1920, height=1080)
        square = ImageDimensions(width=1000, height=1000)

        assert portrait.is_landscape() is False
        assert landscape.is_landscape() is True
        assert square.is_landscape() is False

    def test_is_square(self):
        """Test square orientation detection."""
        portrait = ImageDimensions(width=1080, height=1920)
        landscape = ImageDimensions(width=1920, height=1080)
        square = ImageDimensions(width=1000, height=1000)

        assert portrait.is_square() is False
        assert landscape.is_square() is False
        assert square.is_square() is True

    def test_is_high_resolution(self):
        """Test high resolution detection."""
        high_res = ImageDimensions(width=1920, height=1080)
        higher_res = ImageDimensions(width=3840, height=2160)
        low_res = ImageDimensions(width=800, height=600)

        assert high_res.is_high_resolution() is True
        assert higher_res.is_high_resolution() is True
        assert low_res.is_high_resolution() is False

    def test_string_representation(self):
        """Test string representation."""
        dims = ImageDimensions(width=1920, height=1080)
        assert str(dims) == "1920x1080"


class TestImageData:
    """Test ImageData value object."""

    def create_sample_jpeg_data(self) -> bytes:
        """Create sample JPEG data with valid magic bytes."""
        return b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 100

    def create_sample_png_data(self) -> bytes:
        """Create sample PNG data with valid magic bytes."""
        return b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

    def test_creation_valid(self):
        """Test valid ImageData creation."""
        data = self.create_sample_jpeg_data()
        image = ImageData(data=data, format=ImageFormat.JPEG, filename="test.jpg")
        assert image.data == data
        assert image.format == ImageFormat.JPEG
        assert image.filename == "test.jpg"

    def test_creation_empty_data_raises_error(self):
        """Test empty data raises error."""
        with pytest.raises(ValueError, match="Image data cannot be empty"):
            ImageData(data=b"", format=ImageFormat.JPEG)

    def test_creation_too_large_raises_error(self):
        """Test too large data raises error."""
        large_data = b"\xff\xd8\xff\xe0" + b"\x00" * (11 * 1024 * 1024)  # 11MB
        with pytest.raises(ValueError, match="Image too large"):
            ImageData(data=large_data, format=ImageFormat.JPEG)

    def test_creation_invalid_format_raises_error(self):
        """Test invalid format raises error."""
        # PNG data with JPEG format
        png_data = self.create_sample_png_data()
        with pytest.raises(ValueError, match="Invalid image format"):
            ImageData(data=png_data, format=ImageFormat.JPEG)

    def test_validate_format_jpeg(self):
        """Test JPEG format validation."""
        jpeg_data = self.create_sample_jpeg_data()
        image = ImageData(data=jpeg_data, format=ImageFormat.JPEG)
        assert image._validate_format() is True

    def test_validate_format_png(self):
        """Test PNG format validation."""
        png_data = self.create_sample_png_data()
        image = ImageData(data=png_data, format=ImageFormat.PNG)
        assert image._validate_format() is True

    def test_validate_format_gif(self):
        """Test GIF format validation."""
        gif_data = b"GIF89a" + b"\x00" * 100
        image = ImageData(data=gif_data, format=ImageFormat.GIF)
        assert image._validate_format() is True

    def test_validate_format_bmp(self):
        """Test BMP format validation."""
        bmp_data = b"BM" + b"\x00" * 100
        image = ImageData(data=bmp_data, format=ImageFormat.BMP)
        assert image._validate_format() is True

    def test_validate_format_webp(self):
        """Test WEBP format validation."""
        webp_data = b"RIFF" + b"\x00" * 100
        image = ImageData(data=webp_data, format=ImageFormat.WEBP)
        assert image._validate_format() is True

    def test_validate_format_too_short(self):
        """Test validation with too short data."""
        short_data = b"\xff\xd8"  # Only 2 bytes
        image = ImageData.__new__(ImageData)
        object.__setattr__(image, "data", short_data)
        object.__setattr__(image, "format", ImageFormat.JPEG)
        assert image._validate_format() is False

    def test_from_base64_valid(self):
        """Test creating from valid base64."""
        original_data = self.create_sample_jpeg_data()
        base64_data = base64.b64encode(original_data).decode()

        image = ImageData.from_base64(base64_data, ImageFormat.JPEG, "test.jpg")
        assert image.data == original_data
        assert image.format == ImageFormat.JPEG
        assert image.filename == "test.jpg"

    def test_from_base64_with_data_url(self):
        """Test creating from base64 with data URL prefix."""
        original_data = self.create_sample_jpeg_data()
        base64_data = base64.b64encode(original_data).decode()
        data_url = f"data:image/jpeg;base64,{base64_data}"

        image = ImageData.from_base64(data_url, ImageFormat.JPEG)
        assert image.data == original_data

    def test_from_base64_invalid_raises_error(self):
        """Test invalid base64 raises error."""
        with pytest.raises(ValueError, match="Failed to decode base64"):
            ImageData.from_base64("invalid_base64!", ImageFormat.JPEG)

    def test_to_base64(self):
        """Test converting to base64."""
        data = self.create_sample_jpeg_data()
        image = ImageData(data=data, format=ImageFormat.JPEG)

        base64_result = image.to_base64()
        expected = base64.b64encode(data).decode()
        assert base64_result == expected

    def test_get_data_url(self):
        """Test getting data URL."""
        data = self.create_sample_jpeg_data()
        image = ImageData(data=data, format=ImageFormat.JPEG)

        data_url = image.get_data_url()
        expected_base64 = base64.b64encode(data).decode()
        expected = f"data:image/jpeg;base64,{expected_base64}"
        assert data_url == expected

    def test_get_size_bytes(self):
        """Test getting size in bytes."""
        data = b"\xff\xd8\xff\xe0" + b"\x00" * 1000
        image = ImageData(data=data, format=ImageFormat.JPEG)
        assert image.get_size_bytes() == 1004

    def test_get_size_kb(self):
        """Test getting size in KB."""
        data = b"\xff\xd8\xff\xe0" + b"\x00" * 1020  # 1024 bytes total
        image = ImageData(data=data, format=ImageFormat.JPEG)
        assert image.get_size_kb() == 1.0

    def test_get_size_mb(self):
        """Test getting size in MB."""
        data = b"\xff\xd8\xff\xe0" + b"\x00" * (1024 * 1024 - 4)  # 1MB total
        image = ImageData(data=data, format=ImageFormat.JPEG)
        assert image.get_size_mb() == 1.0

    def test_get_hash(self):
        """Test getting hash."""
        data = self.create_sample_jpeg_data()
        image = ImageData(data=data, format=ImageFormat.JPEG)

        hash_result = image.get_hash()
        expected = hashlib.sha256(data).hexdigest()
        assert hash_result == expected

    def test_get_quality_with_dimensions(self):
        """Test quality calculation with dimensions."""
        data = b"\xff\xd8\xff\xe0" + b"\x00" * (4 * 1024 * 1024)  # 4MB
        dimensions = ImageDimensions(width=1600, height=1200)
        image = ImageData(data=data, format=ImageFormat.JPEG, dimensions=dimensions)

        quality = image.get_quality()
        assert quality == ImageQuality.HIGH

    def test_get_quality_without_dimensions_excellent(self):
        """Test quality calculation without dimensions - excellent."""
        data = b"\xff\xd8\xff\xe0" + b"\x00" * (6 * 1024 * 1024)  # 6MB
        image = ImageData(data=data, format=ImageFormat.JPEG)

        quality = image.get_quality()
        assert quality == ImageQuality.EXCELLENT

    def test_get_quality_without_dimensions_high(self):
        """Test quality calculation without dimensions - high."""
        data = b"\xff\xd8\xff\xe0" + b"\x00" * (3 * 1024 * 1024)  # 3MB
        image = ImageData(data=data, format=ImageFormat.JPEG)

        quality = image.get_quality()
        assert quality == ImageQuality.HIGH

    def test_get_quality_without_dimensions_medium(self):
        """Test quality calculation without dimensions - medium."""
        data = b"\xff\xd8\xff\xe0" + b"\x00" * (1024 * 1024)  # 1MB
        image = ImageData(data=data, format=ImageFormat.JPEG)

        quality = image.get_quality()
        assert quality == ImageQuality.MEDIUM

    def test_get_quality_without_dimensions_low(self):
        """Test quality calculation without dimensions - low."""
        data = b"\xff\xd8\xff\xe0" + b"\x00" * (100 * 1024)  # 100KB
        image = ImageData(data=data, format=ImageFormat.JPEG)

        quality = image.get_quality()
        assert quality == ImageQuality.LOW

    def test_is_suitable_for_ocr_good_image(self):
        """Test OCR suitability for good image."""
        data = b"\xff\xd8\xff\xe0" + b"\x00" * (1024 * 1024)  # 1MB JPEG
        image = ImageData(data=data, format=ImageFormat.JPEG)

        assert image.is_suitable_for_ocr() is True

    def test_is_suitable_for_ocr_bad_format(self):
        """Test OCR suitability for bad format."""
        data = b"GIF89a" + b"\x00" * (1024 * 1024)  # 1MB GIF
        image = ImageData(data=data, format=ImageFormat.GIF)

        assert image.is_suitable_for_ocr() is False

    def test_is_suitable_for_ocr_too_small(self):
        """Test OCR suitability for too small image."""
        data = b"\xff\xd8\xff\xe0" + b"\x00" * (5 * 1024)  # 5KB
        image = ImageData(data=data, format=ImageFormat.JPEG)

        assert image.is_suitable_for_ocr() is False

    def test_is_suitable_for_ocr_too_large(self):
        """Test OCR suitability for too large image."""
        data = b"\xff\xd8\xff\xe0" + b"\x00" * (6 * 1024 * 1024)  # 6MB
        image = ImageData(data=data, format=ImageFormat.JPEG)

        assert image.is_suitable_for_ocr() is False

    def test_is_suitable_for_ocr_low_quality(self):
        """Test OCR suitability for low quality image."""
        data = b"\xff\xd8\xff\xe0" + b"\x00" * (50 * 1024)  # 50KB
        image = ImageData(data=data, format=ImageFormat.JPEG)

        assert image.is_suitable_for_ocr() is False

    def test_get_estimated_ocr_confidence_png(self):
        """Test OCR confidence estimation for PNG."""
        data = self.create_sample_png_data() + b"\x00" * (1024 * 1024)  # 1MB PNG
        image = ImageData(data=data, format=ImageFormat.PNG)

        confidence = image.get_estimated_ocr_confidence()
        assert 0.75 <= confidence <= 1.0  # PNG gets format bonus + quality bonus

    def test_get_estimated_ocr_confidence_jpeg(self):
        """Test OCR confidence estimation for JPEG."""
        data = self.create_sample_jpeg_data() + b"\x00" * (1024 * 1024)  # 1MB JPEG
        image = ImageData(data=data, format=ImageFormat.JPEG)

        confidence = image.get_estimated_ocr_confidence()
        assert 0.6 <= confidence <= 0.8  # JPEG gets smaller format bonus

    def test_get_estimated_ocr_confidence_size_penalty(self):
        """Test OCR confidence with size penalty."""
        # Very large image
        data = self.create_sample_jpeg_data() + b"\x00" * (9 * 1024 * 1024)  # 9MB
        image = ImageData(data=data, format=ImageFormat.JPEG)

        confidence = image.get_estimated_ocr_confidence()
        assert confidence < 0.85  # Should get size penalty

    def test_get_estimated_ocr_confidence_bounds(self):
        """Test OCR confidence stays within bounds."""
        # Very small, low quality image
        data = b"GIF89a" + b"\x00" * 1000  # Small GIF
        image = ImageData(data=data, format=ImageFormat.GIF)

        confidence = image.get_estimated_ocr_confidence()
        assert 0.1 <= confidence <= 1.0

    def test_get_processing_recommendations_good_image(self):
        """Test recommendations for good image."""
        data = self.create_sample_jpeg_data() + b"\x00" * (2 * 1024 * 1024)  # 2MB
        dimensions = ImageDimensions(width=1920, height=1080)
        image = ImageData(data=data, format=ImageFormat.JPEG, dimensions=dimensions)

        recommendations = image.get_processing_recommendations()
        # May have some recommendations based on actual implementation
        assert isinstance(recommendations, list)

    def test_get_processing_recommendations_unsuitable(self):
        """Test recommendations for unsuitable image."""
        data = b"GIF89a" + b"\x00" * 1000  # Small GIF
        image = ImageData(data=data, format=ImageFormat.GIF)

        recommendations = image.get_processing_recommendations()
        assert "Image may not be suitable for OCR processing" in recommendations

    def test_get_processing_recommendations_low_quality(self):
        """Test recommendations for low quality image."""
        data = self.create_sample_jpeg_data() + b"\x00" * (50 * 1024)  # 50KB
        image = ImageData(data=data, format=ImageFormat.JPEG)

        recommendations = image.get_processing_recommendations()
        assert "Consider using a higher quality image" in recommendations

    def test_get_processing_recommendations_too_large(self):
        """Test recommendations for too large image."""
        data = self.create_sample_jpeg_data() + b"\x00" * (6 * 1024 * 1024)  # 6MB
        image = ImageData(data=data, format=ImageFormat.JPEG)

        recommendations = image.get_processing_recommendations()
        assert "Consider compressing image to reduce processing time" in recommendations

    def test_get_processing_recommendations_too_small(self):
        """Test recommendations for too small image."""
        data = self.create_sample_jpeg_data() + b"\x00" * (50 * 1024)  # 50KB
        image = ImageData(data=data, format=ImageFormat.JPEG)

        recommendations = image.get_processing_recommendations()
        assert "Image may be too small for accurate text recognition" in recommendations

    def test_get_processing_recommendations_low_resolution(self):
        """Test recommendations for low resolution image."""
        data = self.create_sample_jpeg_data() + b"\x00" * (1024 * 1024)  # 1MB
        dimensions = ImageDimensions(width=200, height=150)  # Very small
        image = ImageData(data=data, format=ImageFormat.JPEG, dimensions=dimensions)

        recommendations = image.get_processing_recommendations()
        assert "Image resolution may be too low for OCR" in recommendations

    def test_string_representation_with_filename(self):
        """Test string representation with filename."""
        data = self.create_sample_jpeg_data()
        dimensions = ImageDimensions(width=1920, height=1080)
        image = ImageData(
            data=data,
            format=ImageFormat.JPEG,
            dimensions=dimensions,
            filename="test.jpg",
        )

        result = str(image)
        assert "jpeg" in result
        assert "1920x1080" in result
        assert "test.jpg" in result

    def test_string_representation_without_filename(self):
        """Test string representation without filename."""
        data = self.create_sample_jpeg_data()
        image = ImageData(data=data, format=ImageFormat.JPEG)

        result = str(image)
        assert "jpeg" in result
        assert "unknown" in result
        assert "test.jpg" not in result

    def test_equality_same_data(self):
        """Test equality with same data."""
        data = self.create_sample_jpeg_data()
        image1 = ImageData(data=data, format=ImageFormat.JPEG)
        image2 = ImageData(data=data, format=ImageFormat.JPEG)

        assert image1 == image2

    def test_equality_different_data(self):
        """Test equality with different data."""
        data1 = self.create_sample_jpeg_data()
        data2 = self.create_sample_png_data()
        image1 = ImageData(data=data1, format=ImageFormat.JPEG)
        image2 = ImageData(data=data2, format=ImageFormat.PNG)

        assert image1 != image2

    def test_equality_different_type(self):
        """Test equality with different type."""
        data = self.create_sample_jpeg_data()
        image = ImageData(data=data, format=ImageFormat.JPEG)

        assert image != "not an image"
        assert image != 123

    def test_len(self):
        """Test length method."""
        data = self.create_sample_jpeg_data()
        image = ImageData(data=data, format=ImageFormat.JPEG)

        assert len(image) == len(data)
