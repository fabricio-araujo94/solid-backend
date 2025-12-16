from abc import ABC, abstractmethod
import cv2
import numpy as np

class DefectDetectorStrategy(ABC):
    @abstractmethod
    def detect(self, image_bytes: bytes) -> dict:
        """
        Abstract method to detect defects in an image.
        Returns a dictionary with detection results.
        """
        pass

class OpenCVContrastDefectDetector(DefectDetectorStrategy):
    def detect(self, image_bytes: bytes) -> dict:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Não foi possível decodificar a imagem.")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        defects = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Size Filter
            if 20 < area < 1000: 
                x, y, w, h = cv2.boundingRect(cnt)
                defects.append({
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h,
                    "type": "anomalia_contraste",
                    "area": area
                })
                
        return {
            "total_defects": len(defects),
            "defects": defects,
            "image_dimensions": {"width": img.shape[1], "height": img.shape[0]}
        }

class DefectService:
    def __init__(self, strategy: DefectDetectorStrategy):
        self.strategy = strategy

    def analyze(self, image_bytes: bytes) -> dict:
        return self.strategy.detect(image_bytes)

def analyze_image_for_defects(image_bytes: bytes) -> dict:
    service = DefectService(OpenCVContrastDefectDetector())
    return service.analyze(image_bytes)