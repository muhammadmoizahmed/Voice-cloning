"""
Face Detection API Router
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
import cv2
import numpy as np
from PIL import Image
import io

router = APIRouter(prefix="/api/face-detection", tags=["Face Detection"])


@router.post("/validate")
async def validate_face_detection(file: UploadFile = File(...)):
    """Validate that uploaded image contains a face"""
    try:
        # Read image file
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Convert to OpenCV format
        image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Load face cascade classifier
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        face_detected = len(faces) > 0
        face_count = len(faces)
        
        # Get face details
        face_details = []
        if face_detected:
            for (x, y, w, h) in faces:
                face_area_ratio = (w * h) / (image_cv.shape[0] * image_cv.shape[1])
                face_details.append({
                    "x": int(x),
                    "y": int(y),
                    "width": int(w),
                    "height": int(h),
                    "area_ratio": round(face_area_ratio, 4)
                })
        
        return {
            "face_detected": face_detected,
            "face_count": face_count,
            "faces": face_details,
            "message": "Face detected successfully" if face_detected else "No face detected in the image"
        }
        
    except Exception as e:
        return {
            "face_detected": False,
            "face_count": 0,
            "faces": [],
            "message": f"Face detection failed: {str(e)}"
        }
