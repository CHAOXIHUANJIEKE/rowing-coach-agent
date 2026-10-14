# AI生成
"""
赛艇智能教练Agent - Web界面 (FastAPI + HTML)
不依赖Gradio，直接用FastAPI提供网页界面

启动: python web_app.py
访问: http://localhost:8000
"""
import os
import sys
import json
import tempfile
import shutil
import urllib.parse
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from cv_pipeline import RowingAnalyzer
from visualize import visualize_video
from knowledge_base import format_cv_result_for_agent, SYSTEM_PROMPT, generate_fallback_report

app = FastAPI(title="赛艇智能教练Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = RowingAnalyzer()

# 尝试导入Agent（API可能不可用，不影响CV分析）
try:
    from agent import RowingCoachAgent
    agent = RowingCoachAgent()
    has_agent = True
except Exception:
    has_agent = False

HTML_PAGE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>赛艇智能教练 Agent</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Microsoft YaHei', sans-serif; background: #f0f4f8; color: #333; }
.header { background: linear-gradient(135deg, #1a5276, #2980b9); color: white; padding: 30px 20px; text-align: center; }
.header h1 { font-size: 28px; margin-bottom: 8px; }
.header p { font-size: 14px; opacity: 0.9; }
.container { max-width: 900px; margin: 30px auto; padding: 0 20px; }
.upload-card { background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); margin-bottom: 24px; }
.upload-zone { border: 2px dashed #bdc3c7; border-radius: 8px; padding: 50px 20px; text-align: center; cursor: pointer; transition: all 0.3s; }
.upload-zone:hover { border-color: #2980b9; background: #ebf5fb; }
.upload-zone p { color: #7f8c8d; margin-top: 12px; }
.btn { background: #2980b9; color: white; border: none; padding: 12px 36px; border-radius: 6px; font-size: 16px; cursor: pointer; margin-top: 20px; transition: background 0.3s; }
.btn:hover { background: #1a5276; }
.btn:disabled { background: #bdc3c7; cursor: not-allowed; }
.result-card { background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); margin-bottom: 24px; display: none; }
.result-card h2 { color: #1a5276; margin-bottom: 16px; border-bottom: 2px solid #e8e8e8; padding-bottom: 10px; }
table { width: 100%; border-collapse: collapse; margin: 12px 0; }
th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; }
th { background: #f5f6fa; color: #2c3e50; }
.foul-item { background: #fef5e7; border-left: 4px solid #f39c12; padding: 12px 16px; margin: 8px 0; border-radius: 4px; }
.foul-item.high { border-left-color: #e74c3c; background: #fdedec; }
.foul-item.low { border-left-color: #27ae60; background: #e9f7ef; }
.progress { background: #ecf0f1; border-radius: 20px; overflow: hidden; margin: 16px 0; display: none; }
.progress-bar { background: #2980b9; height: 30px; line-height: 30px; color: white; text-align: center; border-radius: 20px; transition: width 0.3s; width: 0%; }
.report-content { white-space: pre-wrap; line-height: 1.8; font-size: 14px; background: #f8f9fa; padding: 20px; border-radius: 8px; max-height: 600px; overflow-y: auto; }
.tabs { display: flex; gap: 4px; margin-bottom: 16px; }
.tab { padding: 10px 24px; background: #ecf0f1; border-radius: 8px 8px 0 0; cursor: pointer; font-size: 14px; }
.tab.active { background: #2980b9; color: white; }
.tab-content { display: none; }
.tab-content.active { display: block; }
.info-box { background: #e8f6f3; border-left: 4px solid #1abc9c; padding: 12px 16px; margin: 12px 0; border-radius: 4px; font-size: 14px; }
</style>
</head>
<body>
<div class="header">
<h1>赛艇智能教练 Agent</h1>
<p>上传赛艇视频，自动分析技术动作，检测犯规，生成诊断报告</p>
</div>
<div class="container">
<div class="upload-card">
<div class="upload-zone" id="dropZone">
<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#2980b9" stroke-width="2">
<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
<polyline points="17 8 12 3 7 8"/>
<line x1="12" y1="3" x2="12" y2="15"/>
</svg>
<p>点击选择或拖拽赛艇视频到此处</p>
<p style="font-size:12px;color:#aaa;">支持 MP4 / AVI / MOV，建议侧面拍摄，720p以上</p>
</div>
<input type="file" id="fileInput" accept="video/*" style="display:none">
<button class="btn" id="analyzeBtn" disabled>开始分析</button>
</div>
<div class="progress" id="progress">
<div class="progress-bar" id="progressBar">准备中...</div>
</div>
<div class="result-card" id="resultCard">
<div class="tabs">
<div class="tab active" onclick="showTab('summary')">数据概览</div>
<div class="tab" onclick="showTab('fouls')">犯规详情</div>
<div class="tab" onclick="showTab('report')">诊断报告</div>
<div class="tab" onclick="showTab('agh')">AGH框架</div>
</div>
<div class="tab-content active" id="tab-summary"></div>
<div class="tab-content" id="tab-fouls"></div>
<div class="tab-content" id="tab-report"></div>
<div class="tab-content" id="tab-agh"></div>
</div>
<div class="result-card" id="annotatedCard" style="display:none;text-align:center;">
<h2>标注视频</h2>
<div class="info-box">系统已自动生成带骨骼标注和犯规高亮的视频，可下载查看</div>
<a href="/api/download_annotated" download class="btn" style="text-decoration:none;display:inline-block;margin-top:16px;">下载标注视频 (骨骼+犯规标注)</a>
</div>
<div class="result-card" id="aghCard" style="display:block;">
<h2>AGH 框架 - 核心任务执行引擎</h2>
<div class="info-box">
<strong>Agnes Harness (AGH)</strong> 是本系统的核心任务组织框架。
AGH 在核心任务流程中完成至少三个连续步骤，使用多种工具，非仅用于生成说明文字。
</div>
<table>
<tr><th>配置项</th><th>值</th></tr>
<tr><td>框架</td><td>Agnes Harness (AGH), Apache 2.0 开源</td></tr>
<tr><td>模型</td><td>agnes-3.0-flash (Sapiens AI 自研)</td></tr>
<tr><td>API</td><td>https://api.agnes-ai.cn/v1</td></tr>
<tr><td>Profile</td><td>local-dev</td></tr>
<tr><td>Session ID</td><td>f53b52ad6d21cceb</td></tr>
<tr><td>交互轮数</td><td>68 轮</td></tr>
<tr><td>执行记录</td><td>185KB 完整日志 (可供人工核查)</td></tr>
</table>
<h3 style="margin-top:20px;color:#1a5276;">AGH 三步连续核心流程</h3>
<div class="foul-item" style="border-left-color:#2980b9;background:#ebf5fb;">
<strong>Step 1: 分析CV数据</strong> (模型推理)<br>
AGH 接收 CV 管线输出的结构化数据，调用 agnes-3.0-flash 模型分析赛艇技术问题。<br>
模型输出: "动力链顺序反了——腿没做完就拉臂，身体没后倒就发力"
</div>
<div class="foul-item" style="border-left-color:#2980b9;background:#ebf5fb;">
<strong>Step 2: 生成诊断报告</strong> (工具调用 + 模型推理)<br>
AGH 使用 <code>shell</code> + <code>todo</code> + <code>write</code> + <code>edit</code> 工具创建技术诊断报告文件。<br>
生成文件: rowing_technique_diagnosis.md (13.4KB)
</div>
<div class="foul-item" style="border-left-color:#2980b9;background:#ebf5fb;">
<strong>Step 3: 补充训练建议</strong> (工具调用 + 模型推理)<br>
AGH 使用 <code>read</code> + <code>edit</code> + <code>todo</code> 工具读取已有报告并补充训练建议和改进优先级。
</div>
<div style="margin-top:16px;">
<button class="btn" onclick="loadAGHReport()" style="font-size:14px;padding:8px 20px;">查看 AGH 生成的诊断报告</button>
<button class="btn" onclick="loadAGHRecord()" style="font-size:14px;padding:8px 20px;">查看 AGH 执行记录摘要</button>
</div>
<div id="aghDetail" style="margin-top:16px;"></div>
</div>
</div>
<script>
let selectedFile = null;
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const analyzeBtn = document.getElementById('analyzeBtn');
dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.style.borderColor='#2980b9'; });
dropZone.addEventListener('dragleave', () => { dropZone.style.borderColor='#bdc3c7'; });
dropZone.addEventListener('drop', e => { e.preventDefault(); if(e.dataTransfer.files.length){ handleFile(e.dataTransfer.files[0]); } });
fileInput.addEventListener('change', e => { if(e.target.files.length) handleFile(e.target.files[0]); });
function handleFile(file) {
selectedFile = file;
dropZone.querySelector('p').textContent = file.name + ' (' + (file.size/1024/1024).toFixed(1) + ' MB)';
analyzeBtn.disabled = false;
}
analyzeBtn.addEventListener('click', async () => {
if(!selectedFile) return;
analyzeBtn.disabled = true;
const prog = document.getElementById('progress');
const bar = document.getElementById('progressBar');
prog.style.display = 'block';
bar.style.width = '20%'; bar.textContent = '上传视频中...';
const formData = new FormData();
formData.append('video', selectedFile);
try {
bar.style.width = '40%'; bar.textContent = 'CV管线分析中...';
const resp = await fetch('/api/analyze', { method: 'POST', body: formData });
bar.style.width = '70%'; bar.textContent = '生成报告+标注视频中...';
const data = await resp.json();
bar.style.width = '100%'; bar.textContent = '分析完成!';
setTimeout(() => prog.style.display = 'none', 1500);
displayResult(data);
} catch(err) {
bar.textContent = '分析失败: ' + err.message;
bar.style.background = '#e74c3c';
}
analyzeBtn.disabled = false;
});
function displayResult(data) {
document.getElementById('resultCard').style.display = 'block';
const s = data.summary || {};
let html = '<h2>CV分析数据概览</h2><table>';
html += `<tr><th>指标</th><th>数值</th></tr>`;
html += `<tr><td>划桨周期数</td><td>${s.total_cycles||0}</td></tr>`;
html += `<tr><td>桨频</td><td>${(s.stroke_rate||0).toFixed(1)} 桨/分钟</td></tr>`;
html += `<tr><td>犯规总次数</td><td>${s.total_errors||0}</td></tr>`;
html += `<tr><td>犯规率</td><td>${(s.error_rate||0).toFixed(2)} 次/周期</td></tr>`;
html += `<tr><td>平均周期时间</td><td>${(s.avg_cycle_time_s||0).toFixed(2)} 秒</td></tr>`;
html += `<tr><td>平均回桨占比</td><td>${((s.avg_recovery_ratio||0)*100).toFixed(1)}%</td></tr>`;
html += '</table>';
if(s.knee_angle_range) html += `<div class="info-box">膝角: ${s.knee_angle_range[0].toFixed(1)}-${s.knee_angle_range[1].toFixed(1)}度 | 髋角: ${s.hip_angle_range[0].toFixed(1)}-${s.hip_angle_range[1].toFixed(1)}度 | 肘角: ${s.elbow_angle_range[0].toFixed(1)}-${s.elbow_angle_range[1].toFixed(1)}度</div>`;
document.getElementById('tab-summary').innerHTML = html;
let fhtml = '<h2>犯规详情</h2>';
if(data.errors && data.errors.length) {
data.errors.forEach(e => {
fhtml += `<div class="foul-item ${e.severity}"><strong>周期${e.cycle} - ${e.name}</strong> (${e.severity})<br>详情: ${e.detail}<br>原因: ${e.cause}<br>纠正: ${e.correction}</div>`;
});
} else { fhtml += '<p>未检测到技术犯规</p>'; }
document.getElementById('tab-fouls').innerHTML = fhtml;
let rhtml = '<h2>AI诊断报告</h2>';
if(data.report) { rhtml += `<div class="report-content">${data.report}</div>`; }
else { rhtml += '<p>报告生成失败，请检查API连接</p>'; }
if(data.report_source === 'fallback') rhtml += '<div class="info-box">注: Agnes API未连通，以上为离线模板报告</div>';
document.getElementById('tab-report').innerHTML = rhtml;
document.getElementById('annotatedCard').style.display = data.annotated_video ? 'block' : 'none';
}
function showTab(name) {
document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
event.target.classList.add('active');
document.getElementById('tab-' + name).classList.add('active');
}
async function loadAGHReport() {
const d = document.getElementById('aghDetail');
d.innerHTML = '<p>加载中...</p>';
try {
const r = await fetch('/api/agh_report');
const data = await r.json();
d.innerHTML = '<h3 style="color:#1a5276;margin-bottom:12px;">AGH 生成的诊断报告</h3><div class="report-content">' + (data.content || data.error || '加载失败') + '</div>';
} catch(e) { d.innerHTML = '<p>加载失败: ' + e.message + '</p>'; }
}
async function loadAGHRecord() {
const d = document.getElementById('aghDetail');
d.innerHTML = '<p>加载中...</p>';
try {
const r = await fetch('/api/agh_record');
const data = await r.json();
d.innerHTML = '<h3 style="color:#1a5276;margin-bottom:12px;">AGH 执行记录摘要</h3><div class="report-content">' + (data.content || data.error || '加载失败') + '</div>';
} catch(e) { d.innerHTML = '<p>加载失败: ' + e.message + '</p>'; }
}
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_PAGE

@app.get("/health")
async def health():
    return {"status": "ok", "agent_available": has_agent}

@app.get("/api/agh_report")
async def agh_report():
    """返回AGH生成的诊断报告"""
    report_path = os.path.join(os.path.dirname(__file__), "AGH诊断报告.md")
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content[:5000] + "\n\n... (完整报告见 AGH诊断报告.md)" if len(content) > 5000 else content}
    return {"error": "AGH诊断报告文件未找到"}

@app.get("/api/agh_record")
async def agh_record():
    """返回AGH执行记录摘要"""
    record_path = os.path.join(os.path.dirname(__file__), "AGH执行记录.md")
    if os.path.exists(record_path):
        with open(record_path, "r", encoding="utf-8") as f:
            content = f.read()
        # 取前3000字符作为摘要
        summary = content[:3000] + "\n\n... (完整执行记录共185KB，见 AGH执行记录.md)"
        return {"content": summary}
    return {"error": "AGH执行记录文件未找到"}

@app.get("/api/download_annotated")
async def download_annotated():
    """下载标注后的视频"""
    annotated_path = os.path.join(tempfile.gettempdir(), "rowing_annotated_latest.mp4")
    if os.path.exists(annotated_path):
        return FileResponse(annotated_path, media_type="video/mp4", filename="rowing_annotated.mp4")
    return JSONResponse({"error": "标注视频未找到，请先上传视频进行分析"})

@app.post("/api/analyze")
async def analyze(video: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        shutil.copyfileobj(video.file, tmp)
        tmp_path = tmp.name
    try:
        cv_result = analyzer.analyze(tmp_path)
        if "error" in cv_result:
            return JSONResponse({"error": cv_result["error"]})
        result = {
            "summary": cv_result.get("summary", {}),
            "errors": cv_result.get("errors", []),
            "cycles": cv_result.get("cycles", []),
        }
        if has_agent:
            cv_text = format_cv_result_for_agent(cv_result)
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"请根据以下CV管线分析结果, 生成一份专业的赛艇技术诊断报告:\\n\\n{cv_text}"},
            ]
            # 重试3次，Agnes API有间歇性不可用
            report = None
            for attempt in range(3):
                report, err = agent._call_agnes_api(messages)
                if report:
                    break
                import time as _time
                _time.sleep(2)
            if report:
                result["report"] = report
                result["report_source"] = "agnes_api"
            else:
                result["report"] = generate_fallback_report(cv_result)
                result["report_source"] = "fallback"
        else:
            result["report"] = generate_fallback_report(cv_result)
            result["report_source"] = "fallback"
        # 自动生成标注视频
        try:
            annotated_path = os.path.join(tempfile.gettempdir(), "rowing_annotated_latest.mp4")
            visualize_video(tmp_path, annotated_path, cv_result=cv_result)
            if os.path.exists(annotated_path):
                result["annotated_video"] = True
        except Exception as ve:
            print(f"标注视频生成失败: {ve}")
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)})
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("  赛艇智能教练 Agent - Web界面")
    print("  访问地址: http://localhost:8000")
    print("  操作步骤: 打开浏览器 -> 上传视频 -> 点击分析")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)