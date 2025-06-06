from ultralytics.nn.tasks import DetectionModel
import cv2
import easyocr
import numpy as np
from ultralytics import YOLO
import re
import time

# Load YOLO model
model = YOLO("my_model.pt")

# EasyOCR อ่านภาษาไทยและภาษาอังกฤษ
reader = easyocr.Reader(['th', 'en'], gpu=False)

# สำหรับควบคุมเวลาการสแกน
last_scan_time = 0
SCAN_INTERVAL = 1.0  # Scan every 1 second

def preprocess_plate_image(roi):
    # ปรับขนาดภาพให้ใหญ่ขึ้นสำหรับการอ่าน OCR
    roi = cv2.resize(roi, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    # เปลี่ยนสีของภาพเป็นขาวดำ
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # ทำการลด noise ของภาพ
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    
    # ใช้ adaptive thresholding
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV, 11, 2)
    
    # ใช้ morphological operations เพื่อลบ noise ของภาพ
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    return thresh

def is_valid_thai_plate(text):
    # ลบเว้นวรรคออกจากข้อความ
    text = text.replace(" ", "")
    
    # นิยามรูปแบบทะเบียนรถไทย
    patterns = [
        r'^\d[ก-๙]{2}\d{4}$',  # 1กข1234
        r'^[ก-๙]{2}\d{4}$',    # กข1234
        r'^[ก-๙]{2}\d{3}$'     # กข123
    ]
    
    # เช็คว่าข้อความตรงกับรูปแบบทะเบียนรถไทยหรือไม่
    return any(re.match(pattern, text) for pattern in patterns)

def clean_plate_text(text):
    # Remove any non-alphanumeric characters except Thai characters
    cleaned = ''.join(c for c in text if c.isalnum() or '\u0E00' <= c <= '\u0E7F')
    return cleaned

def detect_plate_and_read(frame):
    global last_scan_time
    
    # เช็คว่าถึงเวลาสแกนหรือไม่
    current_time = time.time()
    if current_time - last_scan_time < SCAN_INTERVAL:
        return None, 0.0
    
    # อัปเดตเวลาสแกน
    last_scan_time = current_time

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

        # ข้ามถ้าภาพส่วนที่ต้องการอ่านมีขนาดน้อยกว่า 10x10
        if roi.size == 0 or roi.shape[0] < 10 or roi.shape[1] < 10:
            continue

        # ปรับภาพส่วนที่ต้องการอ่านให้อ่านง่ายขึ้น
        processed_roi = preprocess_plate_image(roi)

        # อ่านทะเบียนรถ
        ocr_results = reader.readtext(processed_roi)
        
        if ocr_results:
            # ดึงผลลัพธ์ที่มี confidence สูงสุด
            text, confidence = ocr_results[0][1], ocr_results[0][2]
            cleaned_text = clean_plate_text(text)
            
            # อัปเดตผลลัพธ์ที่มี confidence สูงสุด
            if confidence > best_confidence and is_valid_thai_plate(cleaned_text):
                best_confidence = confidence
                best_text = cleaned_text

    return best_text, best_confidence