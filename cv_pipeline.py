# AI生成
"""
赛艇CV管线 - MediaPipe姿态提取 + 关节角度计算 + 犯规检测
基于论文《基于赛艇运动员骨骼点的时序动作分割及运动状态分析研究与应用》Section 5.3.2

输入: 赛艇视频文件路径
输出: 结构化JSON (关键点轨迹, 关节角度, 划桨周期, 犯规诊断)
"""
import cv2
import mediapipe as mp
import numpy as np
import json
import os
from config import (
    THRESHOLDS,
    MIN_DETECTION_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
    VIDEO_FPS_TARGET,
    SMOOTH_WINDOW,
)


# ============================================================
#  角度计算工具函数
# ============================================================

def calculate_angle(a, b, c):
    """
    计算三点形成的关节角度 (b为顶点)
    a, b, c: [x, y] 坐标
    返回: 角度(度), 0-180
    """
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    ba = a - b
    bc = c - b
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    cosine = np.clip(cosine, -1.0, 1.0)
    return np.degrees(np.arccos(cosine))


def calculate_trunk_angle(hip, shoulder):
    """
    计算躯干前倾角 (相对于垂直方向)
    hip, shoulder: [x, y] 坐标
    返回: 前倾角度(度), 正值=前倾, 负值=后倒
    """
    dx = shoulder[0] - hip[0]
    dy = hip[1] - shoulder[1]  # y轴向下为正, 所以取反
    return np.degrees(np.arctan2(dx, dy + 1e-8))


def smooth_signal(signal, window=5):
    """滑动平均平滑信号"""
    if len(signal) < window:
        return signal
    kernel = np.ones(window) / window
    padded = np.pad(signal, window // 2, mode='edge')
    return np.convolve(padded, kernel, mode='valid')[:len(signal)]


def calculate_angular_velocity(angles, fps):
    """
    中心差分法计算角速度
    返回: 角速度数组 (deg/s)
    """
    dt = 1.0 / fps
    velocity = np.zeros(len(angles))
    for i in range(1, len(angles) - 1):
        velocity[i] = (angles[i + 1] - angles[i - 1]) / (2 * dt)
    if len(angles) > 1:
        velocity[0] = (angles[1] - angles[0]) / dt
        velocity[-1] = (angles[-1] - angles[-2]) / dt
    return velocity


# ============================================================
#  划桨周期检测
# ============================================================

def detect_rowing_cycles(knee_angles, fps, min_cycle_frames=15):
    """
    通过膝角极小值检测划桨周期
    膝角最小 = Catch相位 (腿部最压缩)
    膝角最大 = Finish相位 (腿部最伸展)

    返回: cycles列表, 每个元素 = {catch_frame, finish_frame, next_catch_frame, ...}
    """
    smoothed = smooth_signal(knee_angles, window=7)
    cycles = []

    # 寻找局部极小值 (Catch点)
    minima = []
    window_size = max(int(fps * 0.3), 5)  # 至少0.3秒间隔

    for i in range(window_size, len(smoothed) - window_size):
        is_min = True
        for j in range(1, window_size + 1):
            if smoothed[i] > smoothed[i - j] or smoothed[i] > smoothed[i + j]:
                is_min = False
                break
        if is_min:
            if not minima or (i - minima[-1]) >= min_cycle_frames:
                minima.append(i)

    # 寻找每个周期内的极大值 (Finish点)
    for idx in range(len(minima) - 1):
        catch = minima[idx]
        next_catch = minima[idx + 1]
        segment = smoothed[catch:next_catch]
        if len(segment) == 0:
            continue
        finish = catch + np.argmax(segment)

        # 计算时间占比
        drive_frames = finish - catch
        recovery_frames = next_catch - finish
        total_frames = next_catch - catch
        recovery_ratio = recovery_frames / total_frames if total_frames > 0 else 0

        cycles.append({
            "cycle_id": len(cycles) + 1,
            "catch_frame": int(catch),
            "finish_frame": int(finish),
            "next_catch_frame": int(next_catch),
            "drive_frames": int(drive_frames),
            "recovery_frames": int(recovery_frames),
            "total_frames": int(total_frames),
            "recovery_ratio": round(recovery_ratio, 3),
            "drive_time_s": round(drive_frames / fps, 2),
            "recovery_time_s": round(recovery_frames / fps, 2),
            "total_time_s": round(total_frames / fps, 2),
        })

    return cycles


# ============================================================
#  五类技术犯规检测 (论文 Section 5.3.2)
# ============================================================

def detect_errors(cycles, knee_angles, hip_angles, elbow_angles,
                  trunk_angles, knee_velocities, fps):
    """
    检测五类技术犯规
    返回: errors列表
    """
    errors = []
    t = THRESHOLDS

    for cycle in cycles:
        catch = cycle["catch_frame"]
        finish = cycle["finish_frame"]
        next_catch = cycle["next_catch_frame"]

        # 定义相位窗口
        drive_start = catch
        drive_end = finish
        early_drive_end = catch + int((finish - catch) * 0.3)  # 拉桨前30%

        # ---- 犯规1: 膝关节过早溃缩 ----
        # 拉桨初期, 膝角速度 < -10 deg/s
        for i in range(drive_start, min(early_drive_end, len(knee_velocities))):
            if knee_velocities[i] < t["knee_collapse_velocity"]:
                errors.append({
                    "cycle": cycle["cycle_id"],
                    "type": "knee_collapse",
                    "name": "膝关节过早溃缩",
                    "frame": int(i),
                    "severity": "high",
                    "detail": f"第{i}帧膝角速度={knee_velocities[i]:.1f}deg/s "
                              f"(阈值<{t['knee_collapse_velocity']}deg/s)",
                    "cause": "拉桨初期腿部未能保持张力, 膝关节过早弯曲",
                    "correction": "强化蹬腿发力意识, 保持腿部推力直到桨叶完全入水",
                })
                break  # 每周期只报一次

        # ---- 犯规2: 提早拉臂 ----
        # 躯干<30度 且 肘关节<150度 (在拉桨阶段)
        for i in range(drive_start, min(drive_end, len(trunk_angles))):
            if (trunk_angles[i] < t["early_arm_pull_trunk"] and
                    elbow_angles[i] < t["early_arm_pull_elbow"]):
                errors.append({
                    "cycle": cycle["cycle_id"],
                    "type": "early_arm_pull",
                    "name": "提早拉臂",
                    "frame": int(i),
                    "severity": "medium",
                    "detail": f"第{i}帧躯干角={trunk_angles[i]:.1f}deg, "
                              f"肘角={elbow_angles[i]:.1f}deg",
                    "cause": "上肢过早参与拉桨, 破坏了蹬腿->开体->拉臂的动力链顺序",
                    "correction": "先完成蹬腿和躯干打开, 最后再屈臂拉桨, 遵循动力链顺序",
                })
                break

        # ---- 犯规3: 躯干姿态失稳 ----
        # 结束相位, 后倒角偏离最优30度超过15度
        finish_window_start = finish - int((finish - catch) * 0.1)
        for i in range(max(finish_window_start, 0), min(finish + 1, len(trunk_angles))):
            deviation = abs(trunk_angles[i] - t["trunk_misalignment_optimal"])
            if deviation > t["trunk_misalignment_tolerance"]:
                direction = "过度后倒" if trunk_angles[i] > t["trunk_misalignment_optimal"] else "后倒不足"
                errors.append({
                    "cycle": cycle["cycle_id"],
                    "type": "trunk_misalignment",
                    "name": f"躯干姿态失稳({direction})",
                    "frame": int(i),
                    "severity": "medium",
                    "detail": f"第{i}帧躯干角={trunk_angles[i]:.1f}deg, "
                              f"偏离最优{t['trunk_misalignment_optimal']}deg达{deviation:.1f}deg",
                    "cause": f"核心力量不足或发力习惯问题导致{direction}",
                    "correction": "加强核心训练, 结束相位控制躯干后倒在25-35度区间",
                })
                break

        # ---- 犯规4: 伸展不充分 ----
        # 结束时膝<160度 或 肘<170度
        if finish < len(knee_angles) and finish < len(elbow_angles):
            knee_ext = knee_angles[finish]
            elbow_ext = elbow_angles[finish]
            issues = []
            if knee_ext < t["incomplete_extension_knee"]:
                issues.append(f"膝角={knee_ext:.1f}deg(应>{t['incomplete_extension_knee']})")
            if elbow_ext < t["incomplete_extension_elbow"]:
                issues.append(f"肘角={elbow_ext:.1f}deg(应>{t['incomplete_extension_elbow']})")
            if issues:
                errors.append({
                    "cycle": cycle["cycle_id"],
                    "type": "incomplete_extension",
                    "name": "伸展不充分",
                    "frame": int(finish),
                    "severity": "medium",
                    "detail": "结束相位 " + ", ".join(issues),
                    "cause": "蹬腿或拉臂幅度不够, 桨柄行程不完整",
                    "correction": "加大蹬腿力度和拉臂幅度, 确保结束相位充分伸展",
                })

        # ---- 犯规5: 回桨仓促 ----
        # 回桨时间占比 < 55%
        if cycle["recovery_ratio"] < t["rushed_recovery_ratio"]:
            errors.append({
                "cycle": cycle["cycle_id"],
                "type": "rushed_recovery",
                "name": "回桨仓促",
                "frame": int(finish),
                "severity": "low",
                "detail": f"回桨占比={cycle['recovery_ratio']*100:.1f}% "
                          f"(阈值>{t['rushed_recovery_ratio']*100:.0f}%), "
                          f"回桨{cycle['recovery_time_s']}s vs 拉桨{cycle['drive_time_s']}s",
                "cause": "回桨过快, 缺乏控制, 影响下一个周期的准备质量",
                "correction": "放慢回桨节奏, 利用回桨时间充分恢复和准备下一次抓水",
            })

    return errors


# ============================================================
#  主分析类
# ============================================================

class RowingAnalyzer:
    """赛艇视频分析器"""

    # MediaPipe关键点索引
    LANDMARKS = {
        "nose": 0,
        "l_shoulder": 11, "r_shoulder": 12,
        "l_elbow": 13, "r_elbow": 14,
        "l_wrist": 15, "r_wrist": 16,
        "l_hip": 23, "r_hip": 24,
        "l_knee": 25, "r_knee": 26,
        "l_ankle": 27, "r_ankle": 28,
    }

    def __init__(self):
        self.pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose

    def _select_side(self, landmarks):
        """选择可见度更高的一侧 (左/右)"""
        l_score = (landmarks[self.LANDMARKS["l_shoulder"]].visibility +
                   landmarks[self.LANDMARKS["l_hip"]].visibility +
                   landmarks[self.LANDMARKS["l_knee"]].visibility) / 3
        r_score = (landmarks[self.LANDMARKS["r_shoulder"]].visibility +
                   landmarks[self.LANDMARKS["r_hip"]].visibility +
                   landmarks[self.LANDMARKS["r_knee"]].visibility) / 3
        return "l" if l_score >= r_score else "r"

    def _extract_side_landmarks(self, landmarks, side):
        """提取一侧的关键点坐标"""
        prefix = side
        return {
            "shoulder": [landmarks[self.LANDMARKS[f"{prefix}_shoulder"]].x,
                         landmarks[self.LANDMARKS[f"{prefix}_shoulder"]].y],
            "elbow": [landmarks[self.LANDMARKS[f"{prefix}_elbow"]].x,
                      landmarks[self.LANDMARKS[f"{prefix}_elbow"]].y],
            "wrist": [landmarks[self.LANDMARKS[f"{prefix}_wrist"]].x,
                      landmarks[self.LANDMARKS[f"{prefix}_wrist"]].y],
            "hip": [landmarks[self.LANDMARKS[f"{prefix}_hip"]].x,
                    landmarks[self.LANDMARKS[f"{prefix}_hip"]].y],
            "knee": [landmarks[self.LANDMARKS[f"{prefix}_knee"]].x,
                     landmarks[self.LANDMARKS[f"{prefix}_knee"]].y],
            "ankle": [landmarks[self.LANDMARKS[f"{prefix}_ankle"]].x,
                      landmarks[self.LANDMARKS[f"{prefix}_ankle"]].y],
        }

    def analyze(self, video_path, save_annotated=False, output_path=None):
        """
        主分析函数: 视频 -> 结构化分析结果

        参数:
            video_path: 视频文件路径
            save_annotated: 是否保存标注视频
            output_path: 标注视频保存路径

        返回: dict (分析结果)
        """
        # 每次分析前重新创建Pose对象（避免上次close后状态残留）
        self.pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
        )

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"无法打开视频: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = VIDEO_FPS_TARGET
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # 逐帧提取姿态
        all_landmarks = []
        frames_data = []
        frame_idx = 0
        selected_side = None

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb)

            if results.pose_landmarks:
                lms = results.pose_landmarks.landmark
                if selected_side is None:
                    selected_side = self._select_side(lms)
                side_lms = self._extract_side_landmarks(lms, selected_side)

                # 计算关节角度
                knee_angle = calculate_angle(
                    side_lms["hip"], side_lms["knee"], side_lms["ankle"])
                hip_angle = calculate_angle(
                    side_lms["shoulder"], side_lms["hip"], side_lms["knee"])
                elbow_angle = calculate_angle(
                    side_lms["shoulder"], side_lms["elbow"], side_lms["wrist"])
                trunk_angle = calculate_trunk_angle(
                    side_lms["hip"], side_lms["shoulder"])

                frames_data.append({
                    "frame": frame_idx,
                    "knee_angle": round(knee_angle, 2),
                    "hip_angle": round(hip_angle, 2),
                    "elbow_angle": round(elbow_angle, 2),
                    "trunk_angle": round(trunk_angle, 2),
                    "landmarks": side_lms,
                })
            else:
                # 未检测到人, 用前一帧数据填充
                if frames_data:
                    prev = frames_data[-1].copy()
                    prev["frame"] = frame_idx
                    frames_data.append(prev)

            frame_idx += 1

        cap.release()
        self.pose.close()

        if not frames_data:
            return {"error": "未检测到任何人体姿态, 请检查视频内容"}

        # 提取角度序列
        knee_angles = np.array([f["knee_angle"] for f in frames_data])
        hip_angles = np.array([f["hip_angle"] for f in frames_data])
        elbow_angles = np.array([f["elbow_angle"] for f in frames_data])
        trunk_angles = np.array([f["trunk_angle"] for f in frames_data])

        # 平滑
        knee_angles_s = smooth_signal(knee_angles, SMOOTH_WINDOW)
        hip_angles_s = smooth_signal(hip_angles, SMOOTH_WINDOW)
        elbow_angles_s = smooth_signal(elbow_angles, SMOOTH_WINDOW)
        trunk_angles_s = smooth_signal(trunk_angles, SMOOTH_WINDOW)

        # 角速度
        knee_velocities = calculate_angular_velocity(knee_angles_s, fps)

        # 划桨周期检测
        cycles = detect_rowing_cycles(knee_angles_s, fps)

        # 犯规检测
        errors = detect_errors(
            cycles, knee_angles_s, hip_angles_s, elbow_angles_s,
            trunk_angles_s, knee_velocities, fps)

        # 统计摘要
        summary = self._generate_summary(
            cycles, errors, knee_angles_s, hip_angles_s,
            elbow_angles_s, trunk_angles_s, fps, total_frames)

        result = {
            "video_path": video_path,
            "fps": round(fps, 2),
            "total_frames": total_frames,
            "analyzed_frames": len(frames_data),
            "detected_side": selected_side,
            "cycles": cycles,
            "errors": errors,
            "summary": summary,
            "angle_series": {
                "knee": [round(v, 2) for v in knee_angles_s],
                "hip": [round(v, 2) for v in hip_angles_s],
                "elbow": [round(v, 2) for v in elbow_angles_s],
                "trunk": [round(v, 2) for v in trunk_angles_s],
            },
        }

        return result

    def _generate_summary(self, cycles, errors, knee, hip, elbow,
                          trunk, fps, total_frames):
        """生成统计摘要"""
        error_counts = {}
        for e in errors:
            error_counts[e["type"]] = error_counts.get(e["type"], 0) + 1

        return {
            "total_cycles": len(cycles),
            "total_errors": len(errors),
            "error_rate": round(len(errors) / max(len(cycles), 1), 2),
            "error_breakdown": error_counts,
            "avg_cycle_time_s": round(
                np.mean([c["total_time_s"] for c in cycles]), 2) if cycles else 0,
            "avg_recovery_ratio": round(
                np.mean([c["recovery_ratio"] for c in cycles]), 3) if cycles else 0,
            "knee_angle_range": [round(float(np.min(knee)), 1),
                                 round(float(np.max(knee)), 1)],
            "hip_angle_range": [round(float(np.min(hip)), 1),
                                round(float(np.max(hip)), 1)],
            "elbow_angle_range": [round(float(np.min(elbow)), 1),
                                  round(float(np.max(elbow)), 1)],
            "trunk_angle_range": [round(float(np.min(trunk)), 1),
                                  round(float(np.max(trunk)), 1)],
            "stroke_rate": round(len(cycles) / (total_frames / fps) * 60, 1)
                if total_frames > 0 and cycles else 0,
        }

    def analyze_to_json(self, video_path, output_json_path=None):
        """分析并输出JSON文件"""
        result = self.analyze(video_path)
        if output_json_path:
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        return result


# ============================================================
#  命令行入口
# ============================================================

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python cv_pipeline.py <视频路径> [输出JSON路径]")
        sys.exit(1)

    video_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "analysis_result.json"

    analyzer = RowingAnalyzer()
    result = analyzer.analyze_to_json(video_path, output_path)

    print(f"\n{'='*60}")
    print(f"分析完成!")
    print(f"{'='*60}")
    print(f"视频: {video_path}")
    print(f"帧率: {result.get('fps', 'N/A')} fps")
    print(f"分析帧数: {result.get('analyzed_frames', 0)}")
    print(f"检测到划桨周期: {result['summary']['total_cycles']} 个")
    print(f"检测到犯规: {result['summary']['total_errors']} 次")
    print(f"犯规率: {result['summary']['error_rate']} 次/周期")
    print(f"桨频: {result['summary']['stroke_rate']} 桨/分钟")
    print(f"\n犯规明细:")
    for e in result["errors"]:
        print(f"  [周期{e['cycle']}] {e['name']} - {e['detail']}")
    print(f"\n结果已保存到: {output_path}")
