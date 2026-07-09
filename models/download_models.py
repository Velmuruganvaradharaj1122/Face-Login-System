import os
import urllib.request

MODELS_DIR = os.path.dirname(os.path.abspath(__file__))

MODELS = {
    "face_detection_yunet_2023mar.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "face_recognition_sface_2021dec.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"
}

def download_models():
    for filename, url in MODELS.items():
        filepath = os.path.join(MODELS_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Downloading {filename}...")
            try:
                urllib.request.urlretrieve(url, filepath)
                print(f"Successfully downloaded {filename}")
            except Exception as e:
                print(f"Error downloading {filename}: {e}")
        else:
            print(f"{filename} already exists.")

if __name__ == "__main__":
    download_models()
