# AI生成
"""
赛艇智能教练Agent - Web界面 (Gradio)

功能:
  1. 上传赛艇视频, 自动分析并生成诊断报告
  2. 交互式教练问答
  3. 两段视频对比分析

启动: python app.py
访问: http://localhost:7860
"""
import gradio as gr
import json
import os
import tempfile
from agent import RowingCoachAgent
from knowledge_base import format_cv_result_for_agent


# 全局Agent实例
agent = RowingCoachAgent()
# 保存最近一次分析结果用于交互问答
last_cv_result = {"result": None}


def analyze_single_video(video_file, progress=gr.Progress()):
    """分析单个视频"""
    if video_file is None:
        return "请先上传一段赛艇视频", "", ""

    progress(0.1, desc="正在初始化分析...")
    video_path = video_file if isinstance(video_file, str) else video_file.name

    progress(0.2, desc="正在运行CV管线...")
    result = agent.analyze_video(video_path, verbose=False)

    if result.get("error") and not result.get("report"):
        return f"分析失败: {result['error']}", "", ""

    progress(0.8, desc="正在生成诊断报告...")

    # 保存CV结果用于交互问答
    last_cv_result["result"] = result.get("cv_result")

    # 格式化CV摘要
    cv_result = result.get("cv_result", {})
    summary = cv_result.get("summary", {})

    cv_summary = f"""## CV分析数据概览

| 指标 | 数值 |
|------|------|
| 划桨周期数 | {summary.get('total_cycles', 0)} |
| 桨频 | {summary.get('stroke_rate', 0)} 桨/分钟 |
| 犯规总次数 | {summary.get('total_errors', 0)} |
| 犯规率 | {summary.get('error_rate', 0)} 次/周期 |
| 平均周期时间 | {summary.get('avg_cycle_time_s', 0)} 秒 |
| 平均回桨占比 | {summary.get('avg_recovery_ratio', 0)*100:.1f}% |

### 关节活动范围
- 膝关节: {summary.get('knee_angle_range', [0,0])[0]} - {summary.get('knee_angle_range', [0,0])[1]} 度
- 髋关节: {summary.get('hip_angle_range', [0,0])[0]} - {summary.get('hip_angle_range', [0,0])[1]} 度
- 肘关节: {summary.get('elbow_angle_range', [0,0])[0]} - {summary.get('elbow_angle_range', [0,0])[1]} 度
- 躯干角: {summary.get('trunk_angle_range', [0,0])[0]} - {summary.get('trunk_angle_range', [0,0])[1]} 度
"""

    report = result.get("report", "报告生成失败")
    source_tag = ""
    if result.get("report_source") == "fallback":
        source_tag = "\n\n> *注: Agnes API未连通, 以上为离线模板报告*"
    elif result.get("report_source") == "agnes_api":
        source_tag = "\n\n> *Powered by Agnes Harness + agnes-3.0-flash*"

    progress(1.0, desc="分析完成!")
    return cv_summary, report + source_tag, "分析完成! 可以在下方提问"


def chat_with_coach(message, history):
    """交互式教练问答"""
    if last_cv_result["result"] is None:
        return "请先上传并分析一段视频, 然后再提问"

    answer = agent.interactive_coaching(last_cv_result["result"], message)
    return answer


def compare_two_videos(video1, video2, progress=gr.Progress()):
    """对比分析两段视频"""
    if video1 is None or video2 is None:
        return "请上传两段视频"

    progress(0.1, desc="正在分析视频1...")
    path1 = video1 if isinstance(video1, str) else video1.name
    path2 = video2 if isinstance(video2, str) else video2.name

    progress(0.3, desc="正在分析视频2...")
    result = agent.compare_videos(path1, path2, verbose=False)

    progress(1.0, desc="对比分析完成!")
    report = result.get("report", "对比分析失败")
    if result.get("error"):
        report += f"\n\n> *注: {result['error']}*"
    return report


# ============================================================
#  Gradio界面
# ============================================================

def create_app():
    with gr.Blocks(
        title="赛艇智能教练Agent",
        theme=gr.themes.Soft(),
    ) as app:
        gr.Markdown("# 赛艇智能教练 Agent")
        gr.Markdown("基于 Agnes Harness + MediaPipe CV管线 | "
                    "Powered by agnes-3.0-flash")

        with gr.Tabs():
            # ---- Tab1: 单视频分析 ----
            with gr.Tab("视频分析"):
                with gr.Row():
                    with gr.Column(scale=1):
                        video_input = gr.Video(
                            label="上传赛艇视频",
                            sources=["upload"],
                        )
                        analyze_btn = gr.Button(
                            "开始分析", variant="primary", size="lg")
                        status_text = gr.Textbox(
                            label="状态", interactive=False)

                    with gr.Column(scale=2):
                        cv_output = gr.Markdown(
                            label="CV分析数据", visible=True)
                        report_output = gr.Markdown(
                            label="技术诊断报告", visible=True)

                analyze_btn.click(
                    fn=analyze_single_video,
                    inputs=[video_input],
                    outputs=[cv_output, report_output, status_text],
                )

                # 交互问答
                gr.Markdown("---\n### 交互式教练问答")
                chatbot = gr.ChatInterface(
                    fn=chat_with_coach,
                    title="向教练提问",
                    description="基于上方分析结果, 向AI教练提问任何技术问题",
                )

            # ---- Tab2: 对比分析 ----
            with gr.Tab("对比分析"):
                with gr.Row():
                    video1_input = gr.Video(
                        label="视频1 (待分析)", sources=["upload"])
                    video2_input = gr.Video(
                        label="视频2 (参考标准)", sources=["upload"])

                compare_btn = gr.Button("开始对比分析", variant="primary")
                compare_output = gr.Markdown(label="对比分析报告")

                compare_btn.click(
                    fn=compare_two_videos,
                    inputs=[video1_input, video2_input],
                    outputs=[compare_output],
                )

            # ---- Tab3: 使用说明 ----
            with gr.Tab("使用说明"):
                gr.Markdown("""
## 使用说明

### 1. 视频要求
- 格式: MP4, AVI, MOV
- 内容: 赛艇划桨动作 (测功仪或水上均可)
- 拍摄角度: 侧面拍摄最佳 (能看清一侧手臂和腿部)
- 时长: 建议10秒以上, 包含至少3个完整划桨周期

### 2. 分析流程
1. 上传赛艇视频
2. 点击"开始分析"
3. 系统自动运行CV管线提取骨骼关键点
4. 计算关节角度并检测技术犯规
5. Agnes模型生成专业诊断报告
6. 可在下方与AI教练交互问答

### 3. 技术架构
```
视频 -> MediaPipe(姿态提取) -> 关节角度计算 -> 犯规检测
    -> Agnes Harness(Agent编排) -> agnes-3.0-flash(诊断报告)
    -> Web展示
```

### 4. 检测的5类技术犯规
1. **膝关节过早溃缩** - 拉桨初期膝角速度<-10deg/s
2. **提早拉臂** - 躯干<30度且肘<150度
3. **躯干姿态失稳** - 后倒角偏离30度>15度
4. **伸展不充分** - 结束时膝<160度或肘<170度
5. **回桨仓促** - 回桨时间占比<55%
""")

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch()
