# AI生成
"""
Agnes Harness 配置文件
赛艇智能教练Agent - 配置中心
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Agnes API 配置 (OpenAI兼容格式)
AGNES_API_URL = "https://api.agnes-ai.cn/v1/chat/completions"
AGNES_API_KEY = os.getenv("AGNES_API_KEY", "")
AGNES_MODEL = "agnes-3.0-flash"

# CV管线配置
VIDEO_FPS_TARGET = 30          # 目标帧率
SMOOTH_WINDOW = 5              # Savitzky-Golay滤波窗口大小
MIN_DETECTION_CONFIDENCE = 0.5 # MediaPipe最小检测置信度
MIN_TRACKING_CONFIDENCE = 0.5  # MediaPipe最小跟踪置信度

# 赛艇犯规检测阈值 (来自论文 Section 5.3.2)
THRESHOLDS = {
    "knee_collapse_velocity": -10.0,    # 膝关节角速度阈值 (deg/s)
    "early_arm_pull_trunk": 30.0,       # 躯干角度阈值 (deg)
    "early_arm_pull_elbow": 150.0,      # 肘关节角度阈值 (deg)
    "trunk_misalignment_optimal": 30.0, # 最优躯干后倒角 (deg)
    "trunk_misalignment_tolerance": 15.0, # 容忍区间 (deg)
    "incomplete_extension_knee": 160.0, # 膝关节伸展阈值 (deg)
    "incomplete_extension_elbow": 170.0, # 肘关节伸展阈值 (deg)
    "rushed_recovery_ratio": 0.55,      # 回桨时间占比阈值
}

# 报告输出配置
REPORT_MAX_ERRORS_DISPLAY = 50  # 报告中最多显示的犯规数
