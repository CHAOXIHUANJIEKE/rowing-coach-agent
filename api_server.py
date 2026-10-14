# AI生成
"""
赛艇分析 - CV管线HTTP API服务
在Windows上运行，提供HTTP接口供AGH调用

启动: python api_server.py
端口: 8000
"""
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import tempfile
import shutil
from cv_pipeline import RowingAnalyzer
from knowledge_base import format_cv_result_for_agent

app = FastAPI(title="赛艇CV分析API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = RowingAnalyzer()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "rowing-cv-api"}


@app.post("/analyze")
async def analyze_video(video: UploadFile = File(...)):
    """
    分析赛艇视频，返回结构化JSON结果
    """
    # 保存上传的视频到临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        shutil.copyfileobj(video.file, tmp)
        tmp_path = tmp.name

    try:
        # 运行CV分析
        result = analyzer.analyze(tmp_path)
        return result
    except Exception as e:
        return {"error": str(e)}
    finally:
        os.unlink(tmp_path)


@app.post("/analyze_path")
async def analyze_by_path(video_path: str):
    """
    通过文件路径分析视频（不需要上传）
    """
    try:
        result = analyzer.analyze(video_path)
        return result
    except Exception as e:
        return {"error": str(e)}


@app.post("/format_for_agent")
async def format_for_agent(video: UploadFile = File(...)):
    """
    分析视频并格式化为Agent可读的文本
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        shutil.copyfileobj(video.file, tmp)
        tmp_path = tmp.name

    try:
        result = analyzer.analyze(tmp_path)
        if "error" in result:
            return {"error": result["error"]}
        formatted = format_cv_result_for_agent(result)
        return {"formatted_text": formatted, "raw_result": result}
    except Exception as e:
        return {"error": str(e)}
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    import uvicorn
    print("赛艇CV分析API服务启动中...")
    print("API地址: http://localhost:8000")
    print("接口:")
    print("  GET  /health          - 健康检查")
    print("  POST /analyze         - 上传视频分析")
    print("  POST /analyze_path    - 按路径分析")
    print("  POST /format_for_agent - 分析并格式化")
    uvicorn.run(app, host="0.0.0.0", port=8000)
