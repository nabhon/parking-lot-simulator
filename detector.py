import cv2
import easyocr
from ultralytics import YOLO

# Load YOLO model (your custom trained one)
model = YOLO("best.pt")

# EasyOCR reader with Thai language support
reader = easyocr.Reader(['th', 'en'], gpu=False)

def detect_plate_and_read(frame):
    results = model(frame)
    if not results:
        return None, 0.0

    result = results[0]
    if result.boxes is None:
        return None, 0.0

    for box in result.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        roi = frame[y1:y2, x1:x2]

        # Use EasyOCR to read the region
        ocr_result = reader.readtext(roi)
        if ocr_result:
            text, confidence = ocr_result[0][1], ocr_result[0][2]
            return text.strip(), confidence

    return None, 0.0
