# AI生成
"""
赛艇分析可视化工具
在视频上叠加骨骼关键点 + 犯规标注，生成标注视频

用法: python visualize.py <视频路径> [输出视频路径]
示例: python visualize.py test.mp4 annotated.mp4
"""
import cv2
import numpy as np
import mediapipe as mp
import json
import os
import sys
from cv_pipeline import RowingAnalyzer

# MediaPipe骨骼连接关系 (COCO 17关键点)
SKELETON_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),       # 头部
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),  # 上肢
    (5, 11), (6, 12), (11, 12),            # 躯干
    (11, 13), (13, 15), (12, 14), (14, 16)  # 下肢
]

# 关键点名称
KEYPOINT_NAMES = [
    "鼻", "左肩", "右肩", "左肘", "右肘", "左腕", "右腕",
    "左髋", "右髋", "左膝", "右膝", "左踝", "右踝",
    "左耳", "右耳", "左脚趾", "右脚趾"
]

# 犯规类型颜色 (BGR格式)
FOUL_COLORS = {
    "early_arm_pull": (0, 0, 255),         # 红色
    "trunk_misalignment": (0, 165, 255),   # 橙色
    "incomplete_extension": (0, 255, 255), # 黄色
    "rushed_recovery": (255, 0, 0),        # 蓝色
    "knee_collapse": (255, 0, 255),        # 紫色
}

FOUL_NAMES_CN = {
    "early_arm_pull": "提早拉臂",
    "trunk_misalignment": "躯干失稳",
    "incomplete_extension": "伸展不足",
    "rushed_recovery": "回桨仓促",
    "knee_collapse": "膝过溃缩",
}


def draw_skeleton(frame, landmarks, side="r"):
    """在帧上绘制骨骼关键点和连线"""
    h, w = frame.shape[:2]

    # MediaPipe关键点 -> COCO 17映射
    mp_to_coco = {
        0: 0,   # nose -> nose
        11: 1, 12: 2,  # shoulders
        13: 3, 14: 4,  # elbows
        15: 5, 16: 6,  # wrists
        23: 7, 24: 8,  # hips
        25: 9, 26: 10, # knees
        27: 11, 28: 12, # ankles
        29: 13, 30: 14, # feet
        31: 15, 32: 16, # foot indices
    }

    # 提取COCO关键点
    coco_kps = {}
    for mp_idx, coco_idx in mp_to_coco.items():
        if mp_idx < len(landmarks):
            lm = landmarks[mp_idx]
            coco_kps[coco_idx] = (int(lm.x * w), int(lm.y * h), lm.visibility)

    # 绘制骨骼连线
    for idx1, idx2 in SKELETON_CONNECTIONS:
        if idx1 in coco_kps and idx2 in coco_kps:
            p1 = coco_kps[idx1]
            p2 = coco_kps[idx2]
            if p1[2] > 0.3 and p2[2] > 0.3:
                cv2.line(frame, (p1[0], p1[1]), (p2[0], p2[1]), (0, 255, 0), 2)

    # 绘制关键点
    for idx, kp in coco_kps.items():
        if kp[2] > 0.3:
            color = (0, 0, 255) if idx in [3, 4] else (255, 0, 0)  # 肘关节红色
            cv2.circle(frame, (kp[0], kp[1]), 4, color, -1)

    return frame


def draw_foul_annotation(frame, foul, frame_idx):
    """在帧上绘制犯规标注"""
    foul_type = foul["type"]
    color = FOUL_COLORS.get(foul_type, (255, 255, 255))
    name_cn = FOUL_NAMES_CN.get(foul_type, foul_type)
    severity = foul.get("severity", "")
    detail = foul.get("detail", "")

    # 左上角标注框
    y_offset = 30
    text = f"[犯规] {name_cn} ({severity})"
    cv2.rectangle(frame, (5, y_offset - 20), (350, y_offset + 10), color, -1)
    cv2.putText(frame, text, (10, y_offset - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # 详细信息
    if detail:
        cv2.putText(frame, detail[:40], (10, y_offset + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    return frame


def draw_cycle_info(frame, cycle_num, total_cycles, phase=""):
    """绘制周期信息"""
    text = f"Cycle: {cycle_num}/{total_cycles}"
    if phase:
        text += f"  |  {phase}"
    cv2.rectangle(frame, (5, 5), (300, 25), (0, 0, 0), -1)
    cv2.putText(frame, text, (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    return frame


def visualize_video(video_path, output_path=None, cv_result=None):
    """主可视化函数
    Args:
        video_path: 输入视频路径
        output_path: 输出视频路径 (None则自动生成)
        cv_result: 预计算的CV分析结果 (None则重新分析)
    """
    if output_path is None:
        base = os.path.splitext(video_path)[0]
        output_path = base + "_annotated.mp4"

    print(f"输入视频: {video_path}")
    print(f"输出视频: {output_path}")

    # Step 1: CV分析 (使用预计算结果或重新分析)
    if cv_result is None:
        print("[1/3] 运行CV分析...")
        analyzer = RowingAnalyzer()
        result = analyzer.analyze(video_path)
    else:
        print("[1/3] 使用预计算CV结果")
        result = cv_result

    if "error" in result:
        print(f"分析失败: {result['error']}")
        return None

    cycles = result["cycles"]
    errors = result["errors"]
    fps = result["fps"]
    total_frames = result["total_frames"]

    print(f"  -> {len(cycles)}个周期, {len(errors)}次犯规")

    # 建立帧->犯规映射
    frame_fouls = {}
    for foul in errors:
        f = foul["frame"]
        if f not in frame_fouls:
            frame_fouls[f] = []
        frame_fouls[f].append(foul)

    # 建立帧->周期映射
    frame_cycle = {}
    for cycle in cycles:
        for f in range(cycle["catch_frame"], cycle["next_catch_frame"]):
            phase = "拉桨" if f < cycle["finish_frame"] else "回桨"
            frame_cycle[f] = (cycle["cycle_id"], phase)

    # Step 2: 逐帧标注
    print("[2/3] 生成标注视频...")

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps,
                          (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                           int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # MediaPipe姿态检测
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_result = pose.process(rgb)

        if mp_result.pose_landmarks:
            frame = draw_skeleton(frame, mp_result.pose_landmarks.landmark)

        # 绘制周期信息
        if frame_idx in frame_cycle:
            cycle_num, phase = frame_cycle[frame_idx]
            frame = draw_cycle_info(frame, cycle_num, len(cycles), phase)
        else:
            frame = draw_cycle_info(frame, 0, len(cycles))

        # 绘制犯规标注
        if frame_idx in frame_fouls:
            for foul in frame_fouls[frame_idx]:
                frame = draw_foul_annotation(frame, foul, frame_idx)

        out.write(frame)
        frame_idx += 1

        if frame_idx % 100 == 0:
            print(f"  -> 已处理 {frame_idx}/{total_frames} 帧")

    cap.release()
    out.release()
    pose.close()

    print(f"[3/3] 标注视频已保存: {output_path}")
    print(f"  -> 总帧数: {frame_idx}")
    print(f"  -> 标注犯规: {len(errors)}次")

    # 保存分析结果JSON
    json_path = output_path.replace(".mp4", "_data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  -> 分析数据: {json_path}")

    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python visualize.py <视频路径> [输出视频路径]")
        sys.exit(1)

    video_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    visualize_video(video_path, output_path)
