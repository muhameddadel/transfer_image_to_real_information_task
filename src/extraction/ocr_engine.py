import cv2
import pytesseract
import numpy as np
from pathlib import Path
from PIL import Image
from loguru import logger
from src.config import Config


class OCREngine:
    def __init__(self):
        self.language = Config.OCR_LANGUAGE
        self.confidence_threshold = Config.OCR_CONFIDENCE_THRESHOLD
        
    def extract_text(self, image_path: str) -> str:
        """Extract text from image using OCR"""
        logger.info(f"OCR processing: {image_path}")
        
        image = self._load_image(image_path)
        processed = self._preprocess_image(image)
        
        try:
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(
                processed, 
                lang=self.language,
                config=custom_config
            )
            
            confidence = self._get_confidence(processed)
            logger.debug(f"OCR confidence: {confidence}%")
            
            if confidence < self.confidence_threshold:
                logger.warning(f"OCR confidence {confidence}% below threshold {self.confidence_threshold}%")
                alternative = self._preprocess_alternative(image)
                alt_text = pytesseract.image_to_string(alternative, lang=self.language)
                if len(alt_text) > len(text):
                    text = alt_text
                    logger.info("Alternative preprocessing yielded better results")
            
            logger.success(f"OCR extracted {len(text)} characters")
            return text
            
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            raise
    
    def _load_image(self, image_path: str) -> np.ndarray:
        """Load image from path"""
        if Path(image_path).suffix.lower() == '.pdf':
            from pdf2image import convert_from_path
            images = convert_from_path(image_path)
            image = np.array(images[0])
        else:
            image = cv2.imread(image_path)
        
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        return image
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        coords = np.column_stack(np.where(thresh > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        if angle != 0:
            (h, w) = thresh.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            thresh = cv2.warpAffine(thresh, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        thresh = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        
        scale = 1.5
        thresh = cv2.resize(thresh, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        return thresh
    
    def _preprocess_alternative(self, image: np.ndarray) -> np.ndarray:
        """Alternative preprocessing for difficult images"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        thresh = cv2.filter2D(thresh, -1, kernel)
        return thresh
    
    def _get_confidence(self, image: np.ndarray) -> float:
        """Get OCR confidence score"""
        try:
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            confidences = [int(c) for c in data['conf'] if c != '-1']
            if confidences:
                return sum(confidences) / len(confidences)
        except:
            pass
        return 0.0