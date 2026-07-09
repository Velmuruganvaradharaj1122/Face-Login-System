import json
import base64
import numpy as np
import cv2
from face.encoding import generate_face_encoding, serialize_encoding
from models.user import User
from config.db import db

def process_registration(employee_id, full_name, email, image_data_uri):
    """
    Process the registration of a new user.
    image_data_uri: base64 encoded image from the frontend (data:image/jpeg;base64,...)
    """
    try:
        # Extract base64 image data
        if ',' in image_data_uri:
            image_data = image_data_uri.split(',')[1]
        else:
            image_data = image_data_uri
            
        # Decode base64 string to bytes
        img_bytes = base64.b64decode(image_data)
        
        # Convert bytes to numpy array
        nparr = np.frombuffer(img_bytes, np.uint8)
        
        # Decode image (already BGR, which is what YuNet expects)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Generate encoding
        encoding = generate_face_encoding(img)
        
        if encoding is None:
            return {"success": False, "message": "No face detected in the image. Please try again."}
            
        # Serialize encoding to JSON
        encoding_list = serialize_encoding(encoding)
        encoding_json = json.dumps(encoding_list)
        
        # Create user
        new_user = User(
            employee_id=employee_id,
            full_name=full_name,
            email=email,
            face_encoding=encoding_json
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return {"success": True, "message": "User registered successfully!"}
        
    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": f"Registration failed: {str(e)}"}
