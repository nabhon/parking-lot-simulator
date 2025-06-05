from ultralytics.nn.tasks import DetectionModel
import cv2
import easyocr
import numpy as np
from ultralytics import YOLO

# Load YOLO model (your custom trained one)
model = YOLO("my_model.pt")

# EasyOCR reader with Thai language support and optimized settings
reader = easyocr.Reader(['th', 'en'], gpu=False)

def preprocess_plate_image(roi):
    # Resize the image to a larger size for better OCR
    roi = cv2.resize(roi, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    # Convert to grayscale
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Apply bilateral filter to remove noise while preserving edges
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    
    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV, 11, 2)
    
    # Apply morphological operations to clean up the image
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    return thresh

def clean_plate_text(text):
    # Remove any non-alphanumeric characters except Thai characters
    cleaned = ''.join(c for c in text if c.isalnum() or '\u0E00' <= c <= '\u0E7F')
    return cleaned

def detect_plate_and_read(frame):
    results = model(frame)
    if not results:
        return None, 0.0

    result = results[0]
    if result.boxes is None:
        return None, 0.0

    best_confidence = 0.0
    best_text = None

    for box in result.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        roi = frame[y1:y2, x1:x2]

        # Skip if ROI is too small
        if roi.size == 0 or roi.shape[0] < 10 or roi.shape[1] < 10:
            continue

        # Preprocess the ROI
        processed_roi = preprocess_plate_image(roi)

        # Try to read the plate with different preprocessing
        ocr_results = reader.readtext(processed_roi)
        
        if ocr_results:
            # Get the result with highest confidence
            text, confidence = ocr_results[0][1], ocr_results[0][2]
            cleaned_text = clean_plate_text(text)
            
            # Update best result if confidence is higher
            if confidence > best_confidence and len(cleaned_text) >= 3:
                best_confidence = confidence
                best_text = cleaned_text

    return best_text, best_confidence