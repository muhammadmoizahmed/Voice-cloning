"""
Script to download required AI models for VoiceForge AI
"""
import os
import urllib.request
from tqdm import tqdm


class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download_url(url, output_path):
    """Download file with progress bar"""
    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=url.split('/')[-1]) as t:
        urllib.request.urlretrieve(url, filename=output_path, reporthook=t.update_to)


def setup_models():
    """Download and setup all required models"""
    
    print("=" * 60)
    print("VoiceForge AI - Model Setup")
    print("=" * 60)
    print()
    
    models_dir = "models_cache"
    os.makedirs(models_dir, exist_ok=True)
    
    # Download face detection model (OpenCV DNN)
    face_model_files = {
        "deploy.prototxt": "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt",
        "res10_300x300_ssd_iter_140000.caffemodel": "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
    }
    
    print("[1/2] Downloading face detection models...")
    for filename, url in face_model_files.items():
        output_path = os.path.join(models_dir, filename)
        if os.path.exists(output_path):
            print(f"  ✓ {filename} already exists")
        else:
            print(f"  Downloading {filename}...")
            try:
                download_url(url, output_path)
                print(f"  ✓ Downloaded {filename}")
            except Exception as e:
                print(f"  ✗ Failed to download {filename}: {e}")
    
    # Setup TTS model
    print()
    print("[2/2] Setting up TTS model (Coqui XTTS v2)...")
    print("  This will download ~2GB of models on first run...")
    
    try:
        from TTS.api import TTS
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        print("  ✓ TTS model ready")
    except Exception as e:
        print(f"  ✗ Failed to setup TTS: {e}")
        print("  The model will be downloaded automatically on first use")
    
    print()
    print("=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print()
    print("You can now run: python main.py")


if __name__ == "__main__":
    setup_models()
