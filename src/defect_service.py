import cv2
import numpy as np

def analyze_image_for_defects(image_bytes: bytes):
    """
    Receives the bytes of an image, processes them via OpenCV, and 
    returns a list of anomalies found (x, y, w, h).
    """
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
        
        # Size Filter: Ignore very small noise and the entire piece (very large)
        # Adjust these values according to the size of your test images!
        if 20 < area < 1000: 
            x, y, w, h = cv2.boundingRect(cnt)
            defects.append({
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "type": "anomalia_contraste", # Pode ser ferrugem, furo, etc.
                "area": area
            })
            
    return {
        "total_defects": len(defects),
        "defects": defects,
        "image_dimensions": {"width": img.shape[1], "height": img.shape[0]}
    }