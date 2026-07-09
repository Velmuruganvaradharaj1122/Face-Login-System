import cv2
import numpy as np
import os

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))

detector = None
recognizer = None

def get_models():
    global detector, recognizer
    if detector is None or recognizer is None:
        det_path = os.path.join(MODELS_DIR, 'face_detection_yunet_2023mar.onnx')
        rec_path = os.path.join(MODELS_DIR, 'face_recognition_sface_2021dec.onnx')
        
        if not os.path.exists(det_path) or not os.path.exists(rec_path):
            raise FileNotFoundError("OpenCV ONNX models not found. Did download_models.py run?")
            
        detector = cv2.FaceDetectorYN.create(
            det_path,
            "",
            (320, 320),
            0.9,
            0.3,
            5000
        )
        recognizer = cv2.FaceRecognizerSF.create(rec_path, "")
    return detector, recognizer

def generate_face_encoding(image_array):
    """
    Generate a face encoding from an image array using OpenCV.
    Note: image_array should be BGR format for YuNet.
    Returns the first encoding found or None if no face is detected.
    """
    det, rec = get_models()
    
    height, width, _ = image_array.shape
    det.setInputSize((width, height))
    
    # Detect faces
    _, faces = det.detect(image_array)
    
    if faces is None or len(faces) == 0:
        return None
        
    # Take the first face
    face = faces[0]
    
    # Align the face
    aligned_face = rec.alignCrop(image_array, face)
    
    # Extract features
    feature = rec.feature(aligned_face)
    return feature[0] # feature is typically shape (1, 128)

def serialize_encoding(encoding):
    """
    Convert numpy array encoding to list for JSON serialization.
    """
    if encoding is not None:
        return encoding.tolist()
    return None

def deserialize_encoding(encoding_list):
    """
    Convert list encoding back to numpy array.
    """
    if encoding_list is not None:
        return np.array(encoding_list, dtype=np.float32)
    return None

def match_faces(feature1, feature2):
    """
    Calculate match score (cosine distance).
    Returns True if faces match (closer than threshold), else False.
    """
    det, rec = get_models()
    # OpenCV SFace match: L2 or Cosine distance
    # For Cosine distance, lower distance means closer faces, but the OpenCV threshold
    # for cosine distance is typically around 0.363
    # SFace match() returns distance. The smaller the closer.
    
    # Note: cv2.FaceRecognizerSF.match uses L2 by default (0) or Cosine (1)
    # distance = rec.match(feature1, feature2, cv2.FaceRecognizerSF_FR_COSINE)
    
    # Actually, the simplest way is to manually calculate or use cv2
    distance = rec.match(feature1, feature2, cv2.FaceRecognizerSF_FR_COSINE)
    return distance
