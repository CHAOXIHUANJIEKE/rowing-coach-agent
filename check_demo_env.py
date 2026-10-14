# AI生成
import sys
print(f"Python: {sys.version}")
try:
    import mediapipe
    print("mediapipe: OK")
except ImportError as e:
    print(f"mediapipe: MISSING - {e}")
try:
    import cv2
    print(f"opencv: OK ({cv2.__version__})")
except ImportError as e:
    print(f"opencv: MISSING - {e}")
try:
    import requests
    print("requests: OK")
except ImportError as e:
    print(f"requests: MISSING - {e}")
try:
    import numpy
    print(f"numpy: OK ({numpy.__version__})")
except ImportError as e:
    print(f"numpy: MISSING - {e}")
import os
video = r"D:\Desktop\9531f721615128052e21b29d682de3ef.mp4"
print(f"test_video: {'OK' if os.path.exists(video) else 'MISSING'}")
annotated = r"D:\Desktop\rowing_annotated.mp4"
print(f"annotated_video: {'OK' if os.path.exists(annotated) else 'MISSING'}")