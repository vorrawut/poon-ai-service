"""
OCR Service using Tesseract with optimization for receipts
Supports Thai and English languages
"""

import pytesseract
import cv2
import numpy as np
from PIL import Image
import io
import asyncio
import logging
from typing import Dict, Any, Optional
from models.spending_models import OCRResult
import time

logger = logging.getLogger(__name__)

class OCRService:
    """OCR service for processing receipt images"""
    
    def __init__(self, settings):
        self.settings = settings
        self.tesseract_config = {
            'eng+tha': r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,:-/()฿$€£¥₹₩₪₽₨₦₡₵₸₴₼₾₿กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรฤลฦวศษสหฬอฮฯะัาำิีึืฺุูเแโใไๅๆ็่้๊๋์ํ๎๏๐๑๒๓๔๕๖๗๘๙๚๛',
            'eng': r'--oem 3 --psm 6',
            'tha': r'--oem 3 --psm 6'
        }
    
    async def extract_text(self, image_bytes: bytes, language: str = "eng+tha") -> OCRResult:
        """
        Extract text from image using Tesseract OCR
        Optimized for receipt processing
        """
        start_time = time.time()
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Preprocess image for better OCR
            processed_image = await self._preprocess_image(image)
            
            # Get Tesseract config
            config = self.tesseract_config.get(language, self.tesseract_config['eng+tha'])
            
            # Run OCR in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            text, confidence, details = await loop.run_in_executor(
                None, self._run_tesseract, processed_image, language, config
            )
            
            processing_time = time.time() - start_time
            
            logger.info(f"OCR completed in {processing_time:.2f}s with confidence {confidence:.2f}")
            
            return OCRResult(
                text=text.strip(),
                confidence=confidence,
                language=language,
                processing_time=processing_time,
                bounding_boxes=details.get('bounding_boxes', []),
                metadata={
                    'image_size': image.size,
                    'preprocessing_applied': True,
                    'tesseract_config': config
                }
            )
            
        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
            raise Exception(f"OCR processing failed: {str(e)}")
    
    def _run_tesseract(self, image: Image.Image, language: str, config: str) -> tuple:
        """Run Tesseract OCR in thread"""
        try:
            # Extract text
            text = pytesseract.image_to_string(image, lang=language, config=config)
            
            # Get detailed data for confidence calculation
            data = pytesseract.image_to_data(image, lang=language, config=config, output_type=pytesseract.Output.DICT)
            
            # Calculate confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Extract bounding boxes for high-confidence text
            bounding_boxes = []
            for i, conf in enumerate(data['conf']):
                if int(conf) > 60:  # High confidence threshold
                    bounding_boxes.append({
                        'text': data['text'][i],
                        'confidence': int(conf),
                        'bbox': {
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        }
                    })
            
            return text, avg_confidence / 100.0, {'bounding_boxes': bounding_boxes}
            
        except Exception as e:
            logger.error(f"Tesseract execution failed: {str(e)}")
            return "", 0.0, {}
    
    async def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results
        Optimized for receipt images
        """
        try:
            # Convert PIL to OpenCV format
            img_array = np.array(image)
            
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Apply preprocessing steps
            # 1. Noise reduction
            denoised = cv2.medianBlur(gray, 3)
            
            # 2. Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # 3. Binarization (adaptive thresholding works better for receipts)
            binary = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # 4. Morphological operations to clean up
            kernel = np.ones((2,2), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # 5. Resize if image is too small or too large
            height, width = cleaned.shape
            if height < 300 or width < 300:
                # Upscale small images
                scale = max(300 / height, 300 / width)
                new_height, new_width = int(height * scale), int(width * scale)
                cleaned = cv2.resize(cleaned, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            elif height > 3000 or width > 3000:
                # Downscale very large images
                scale = min(3000 / height, 3000 / width)
                new_height, new_width = int(height * scale), int(width * scale)
                cleaned = cv2.resize(cleaned, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Convert back to PIL
            processed_image = Image.fromarray(cleaned)
            
            return processed_image
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed, using original: {str(e)}")
            return image
    
    async def extract_receipt_fields(self, ocr_result: OCRResult) -> Dict[str, Any]:
        """
        Extract specific fields from receipt text
        Uses pattern matching optimized for Thai receipts
        """
        text = ocr_result.text
        fields = {}
        
        # Amount patterns (Thai Baht and other currencies)
        amount_patterns = [
            r'(?:total|รวม|ยอดรวม|รวมทั้งสิ้น)[:\s]*([0-9,]+\.?[0-9]*)[:\s]*(?:บาท|฿|baht)?',
            r'([0-9,]+\.?[0-9]*)[:\s]*(?:บาท|฿|baht)',
            r'฿\s*([0-9,]+\.?[0-9]*)',
            r'([0-9,]+\.[0-9]{2})\s*$'  # Amount at end of line
        ]
        
        # Date patterns
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{2,4})',
            r'(\d{1,2}\s+(?:ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.)\s+\d{2,4})'
        ]
        
        # Merchant patterns
        merchant_patterns = [
            r'^([A-Z][A-Z\s&]+)(?:\n|\r)',  # All caps company name at start
            r'(?:ร้าน|shop|store)[:\s]*([^\n\r]+)',
            r'^([ก-๙\s]+(?:จำกัด|มหาชน|ห้างหุ้นส่วน))',  # Thai company suffixes
        ]
        
        # Payment method patterns  
        payment_patterns = [
            r'(?:credit|debit|visa|mastercard|card)[:\s]*([^\n\r]+)',
            r'(?:เงินสด|cash)',
            r'(?:โอน|transfer)',
            r'(?:พร้อมเพย์|promptpay)'
        ]
        
        # Extract fields using patterns
        import re
        
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    fields['amount'] = float(amount_str)
                    break
                except ValueError:
                    continue
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fields['date_string'] = match.group(1)
                break
        
        for pattern in merchant_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                fields['merchant'] = match.group(1).strip()
                break
        
        for pattern in payment_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fields['payment_method'] = match.group(0).strip()
                break
        
        return fields
