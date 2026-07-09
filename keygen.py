import hmac
import hashlib
from datetime import datetime

def generate_key(machine_id, year=None):
    if not year:
        year = str(datetime.utcnow().year)
        
    SECRET_KEY = "FACE_AUTH_ENTERPRISE_SECRET"
    
    # Generate HMAC-SHA256 hash of machine_id + year
    expected_hash = hmac.new(SECRET_KEY.encode(), (machine_id + str(year)).encode(), hashlib.sha256).hexdigest()[:16].upper()
    
    # Format into groups of 4: XXXX-XXXX-XXXX-XXXX
    key = f"{expected_hash[:4]}-{expected_hash[4:8]}-{expected_hash[8:12]}-{expected_hash[12:16]}"
    return key

if __name__ == "__main__":
    print("=== FaceAuth License Generator ===")
    m_id = input("Enter client's Machine ID: ")
    yr = input("Enter expiry year (leave blank for current year): ")
    
    key = generate_key(m_id, yr if yr else None)
    
    print("\nGenerated Product Key:")
    print("-------------------------")
    print(key)
    print("-------------------------")
    print("Send this key to the client.")
