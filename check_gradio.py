# AI生成
import sys
print(f"Python: {sys.version}")
try:
    import gradio
    print(f"gradio: OK ({gradio.__version__})")
except ImportError:
    print("gradio: NOT INSTALLED")
try:
    import mediapipe
    print("mediapipe: OK")
except ImportError:
    print("mediapipe: NOT INSTALLED")
try:
    import cv2
    print("opencv: OK")
except ImportError:
    print("opencv: NOT INSTALLED")
try:
    import requests
    print("requests: OK")
except ImportError:
    print("requests: NOT INSTALLED")