# AI生成
"""端到端测试：分析赛艇视频"""
import sys
import os

# 重定向输出到文件
log_file = os.path.join(os.path.dirname(__file__), "test_output.txt")
log = open(log_file, "w", encoding="utf-8")

def log_print(*args):
    msg = " ".join(str(a) for a in args)
    print(msg, flush=True)
    log.write(msg + "\n")
    log.flush()

try:
    # 1. 检查视频
    video_path = r"D:\Desktop\9531f721615128052e21b29d682de3ef.mp4"
    log_print(f"视频路径: {video_path}")
    log_print(f"文件存在: {os.path.exists(video_path)}")
    log_print(f"文件大小: {os.path.getsize(video_path)} bytes")

    # 2. 检查视频信息
    import cv2
    cap = cv2.VideoCapture(video_path)
    log_print(f"视频打开: {cap.isOpened()}")
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    log_print(f"总帧数: {frame_count}")
    log_print(f"FPS: {fps}")
    if fps > 0:
        log_print(f"时长: {round(frame_count/fps, 1)}秒")
    cap.release()

    # 3. 运行CV分析
    log_print("\n--- 开始CV分析 ---")
    from cv_pipeline import RowingAnalyzer
    analyzer = RowingAnalyzer()
    cv_result = analyzer.analyze(video_path)
    log_print(f"CV分析完成!")

    # 4. 输出结果摘要
    if "error" in cv_result:
        log_print(f"CV错误: {cv_result['error']}")
    else:
        s = cv_result["summary"]
        log_print(f"划桨周期数: {s['total_cycles']}")
        log_print(f"总犯规数: {s['total_errors']}")
        for et, count in s["error_breakdown"].items():
            log_print(f"  {et}: {count}次")

    # 5. 调用Agnes模型生成报告
    log_print("\n--- 调用Agnes模型生成报告 ---")
    from knowledge_base import format_cv_result_for_agent, SYSTEM_PROMPT
    from agent import RowingCoachAgent

    agent = RowingCoachAgent()
    cv_text = format_cv_result_for_agent(cv_result)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"请根据以下CV管线分析结果, 生成一份专业的赛艇技术诊断报告:\n\n{cv_text}"},
    ]
    report, error = agent._call_agnes_api(messages)

    if report:
        log_print("模型报告生成成功!")
        log_print("\n" + "="*60)
        log_print(report)
    else:
        log_print(f"模型调用失败: {error}")
        from knowledge_base import generate_fallback_report
        fallback = generate_fallback_report(cv_result)
        log_print("使用离线模板生成报告:")
        log_print(fallback)

    # 6. 保存完整结果
    import json
    with open(os.path.join(os.path.dirname(__file__), "full_result.json"), "w", encoding="utf-8") as f:
        json.dump({"cv_result": cv_result, "report": report}, f, ensure_ascii=False, indent=2)
    log_print("\n完整结果已保存到 full_result.json")

except Exception as e:
    import traceback
    log_print(f"错误: {e}")
    log_print(traceback.format_exc())

log_print("\n=== 测试完成 ===")
log.close()