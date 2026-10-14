# AI生成
赛艇智能教练 Agent - 使用说明
================================

本系统通过计算机视觉分析赛艇划桨视频，自动检测技术犯规并生成诊断报告。

【系统自包含】本压缩包包含运行所需的全部文件，不依赖任何特定平台或软件。
解压到任意目录后，只需安装 Python 和依赖包即可使用。


快速开始（3步）：
--------------------------------

1. 安装 Python
   - 访问 https://www.python.org/downloads/ 下载安装
   - 安装时务必勾选 "Add Python to PATH"

2. 安装依赖（只需一次）
   - 打开 cmd（按 Win+R 输入 cmd 回车）
   - cd 进入本文件夹
   - 输入: pip install mediapipe opencv-python numpy requests fastapi uvicorn python-dotenv
   - 等待安装完成

3. 启动系统
   - 双击 一键启动.bat
   - 浏览器打开 http://localhost:8000
   - 上传赛艇视频，点击"开始分析"


详细操作步骤请阅读: 新手使用指南.md


文件说明：
--------------------------------
一键启动.bat        - 双击启动Web界面
web_app.py          - Web界面程序
cv_pipeline.py      - CV分析核心管线
agent.py            - AI诊断Agent
config.py           - 系统配置
新手使用指南.md     - 详细使用步骤
复现指南.md         - 技术复现说明
技术方案.md         - 完整技术方案文档
测试样例.md         - 测试用例（正常/边界/失败）
成员声明.md         - 团队成员声明
AGH诊断报告.md      - AGH生成的诊断报告
AGH执行记录.md      - AGH执行记录（可供核查）


技术支持：
--------------------------------
模型: agnes-3.0-flash (Sapiens AI)
框架: Agnes Harness (AGH), Apache 2.0
CV引擎: MediaPipe Pose (Google)
视频处理: OpenCV