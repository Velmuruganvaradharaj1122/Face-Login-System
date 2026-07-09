import json
import base64
import numpy as np
import cv2
import os
from face.encoding import generate_face_encoding, deserialize_encoding, match_faces
from models.user import User

def process_login(image_data_uri):
    """
    Process face login attempt.
    """
    try:
        # SFace cosine SIMILARITY threshold: higher score = more similar faces.
        # OpenCV docs recommend 0.363 as the minimum score to consider a match.
        threshold = float(os.getenv('FACE_MATCH_THRESHOLD', 0.363))
        
        # Extract base64 image data
        if ',' in image_data_uri:
            image_data = image_data_uri.split(',')[1]
        else:
            image_data = image_data_uri
            
        # Decode base64 string
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR) # BGR
        
        # Generate encoding for current face
        current_encoding = generate_face_encoding(img)
        
        if current_encoding is None:
            return {"success": False, "message": "No face detected in the image."}
            
        # Fetch all users
        users = User.query.all()
        
        if not users:
            return {"success": False, "message": "No users registered in the system."}
            
        best_match = None
        max_score = -1.0  # Track highest similarity score
        
        for user in users:
            if not user.face_encoding:
                continue
                
            # Parse stored encoding
            stored_encoding_list = json.loads(user.face_encoding)
            stored_encoding = deserialize_encoding(stored_encoding_list)
            
            # match_faces returns a cosine SIMILARITY score (higher = more similar)
            score = match_faces(stored_encoding, current_encoding)
            
            if score > max_score:
                max_score = score
                if score > threshold:  # Score must be ABOVE threshold to be a match
                    best_match = user
                    
        if best_match:
            return {
                "success": True, 
                "message": "Login successful!", 
                "user": {
                    "id": best_match.id,
                    "employee_id": best_match.employee_id,
                    "full_name": best_match.full_name,
                    "email": best_match.email
                }
            }
        else:
            return {"success": False, "message": "Face not recognized or unauthorized."}
            
    except Exception as e:
        return {"success": False, "message": f"Login process error: {str(e)}"}
