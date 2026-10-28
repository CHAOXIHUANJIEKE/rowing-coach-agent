# 赛艇智能教练系统

[English](README.md) | 简体中文

> 基于 AI 的赛艇技术分析与智能教练系统。上传训练视频，即可获取动作诊断与改进建议。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

---

## 目录

- [项目介绍](#项目介绍)
- [视频介绍](#视频介绍)
- [架构介绍](#架构介绍)
- [集成标准](#集成标准)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [技术栈](#技术栈)
- [开源协议](#开源协议)

---

## 项目介绍

### 项目背景

赛艇是一项技术要求极高的运动，规范的划桨动作对竞技表现和伤病预防至关重要。传统教练指导依赖经验丰富的教练员现场观察，对于业余运动员或偏远地区的训练者而言，专业指导往往难以获取。本项目利用计算机视觉与深度学习技术，实现赛艇训练动作的自动化分析与诊断，让每一位赛艇运动员都能获得专业级的技术反馈。

### 核心功能

1. **视频上传与处理** — 用户通过网页界面上传赛艇训练视频，系统支持多种格式与分辨率。

2. **人体姿态估计** — 采用 YOLOv8-Pose 模型，逐帧检测人体 17 个关键点，全程跟踪运动员姿态变化。

3. **赛艇动作周期分割** — 自动将每个划桨周期分割为四个阶段：**抓水（Catch）**、**拉桨（Drive）**、**出桨（Finish）**、**回桨（Recovery）**，基于关节角信号实现，无需标注数据。

4. **多关节协同性分析** — 分析腿-背-臂的发力顺序与协调模式，检测常见错误动作（如过早打开背部、腿部驱动不足等）。

5. **基于 DTW 的技术评分** — 利用动态时间规整算法（DTW）将运动员关节角度轨迹与标准模板进行时序匹配，生成量化技术评分。

6. **可视化反馈与报告** — 生成骨架叠加标注视频、关节角度曲线图、阶段时序图，以及包含具体改进建议的文字分析报告。

### 创新亮点

- **无监督动作阶段分割算法**：利用膝关节与躯干角速度的过零检测定位动作周期边界，自适应不同桨频，无需人工标注或标定。
- **腿-背-臂发力顺序检测算法**：基于赛艇生物力学原理，通过分析各关节角速度峰值时序，验证发力顺序是否符合规范（腿→背→臂），针对赛艇技术专门设计。
- **DTW + 多维评分体系**：将时序对齐（DTW）与协调性分析、节奏稳定性相结合，实现全面的技术评估，超越简单的姿态对比。

---

## 视频介绍

| 平台 | 链接 |
|------|------|
| 哔哩哔哩 | https://b23.tv/TVcOceD |
| 抖音 | https://v.douyin.com/canFdSbdh2s/ |

**演示流程：**

1. 用户通过网页界面上传赛艇训练视频
2. 系统处理视频并实时显示分析进度
3. 生成带骨架叠加与阶段标记的标注视频
4. 展示各关节角度分析图表
5. 输出包含评分与改进建议的综合教练报告

---

## 架构介绍

### 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Web 前端 (Vue.js)                      │
│  ┌───────────┐  ┌────────────┐  ┌────────────────────┐  │
│  │  视频上传   │  │  进度追踪   │  │  结果展示           │  │
│  │  组件      │  │  器        │  │  (视频+图表+报告)   │  │
│  └───────────┘  └────────────┘  └────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │ REST API
┌────────────────────────┴────────────────────────────────┐
│                 后端服务 (FastAPI)                        │
│  ┌───────────┐  ┌────────────┐  ┌────────────────────┐  │
│  │  API       │  │  异步任务   │  │  数据库             │  │
│  │  路由      │  │  队列      │  │  (SQLite/PostgreSQL)│  │
│  └───────────┘  └────────────┘  └────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│                   分析流水线                              │
│                                                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  视频预处理  │───>│  姿态估计    │───>│  赛艇动作    │  │
│  │  (350行)    │    │  (500行)    │    │  分析(600行) │  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                │          │
│                          ┌─────────────────────┘          │
│                          v                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  可视化输出  │<──│  评估与诊断  │<──│  (中间结果)  │  │
│  │  (400行)    │    │  (550行)    │    │             │  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 核心模块

| 模块 | 功能 | 代码量（行） |
|------|------|:-----------:|
| **视频预处理模块** | 视频解码、帧提取、去噪增强、帧率标准化、视频信息提取 | ~350 |
| **人体姿态估计模块** | YOLOv8-Pose 推理、17关键点检测、多帧跟踪、卡尔曼滤波平滑 | ~500 |
| **赛艇动作分析模块** | 关节角度计算、桨频检测、四阶段分割、节奏与时长分析 | ~600 |
| **动作评估与诊断模块** | 标准模板库、DTW匹配、错误分类、建议生成、综合评分 | ~550 |
| **结果可视化模块** | 标注视频生成、角度曲线图、阶段时序图、分析报告生成 | ~400 |
| **Web前端交互模块** | 上传界面、进度显示、结果展示页、历史记录管理 | ~500 |
| **后端服务模块** | API路由、异步任务队列、文件存储、数据库操作 | ~400 |
| **合计** | | **~3,300** |

### 核心算法

#### 算法一：无监督赛艇动作阶段分割

```
输入：关节角度时序信号 θ_knee(t), θ_trunk(t)
输出：阶段边界 {抓水, 拉桨, 出桨, 回桨}

1. 计算角速度：ω(t) = dθ/dt
2. 检测 ω_knee(t) 过零点 → 划桨周期边界
3. 对每个周期：
   a. 膝关节角最小值 → 抓水阶段起点
   b. 膝关节角最大值 → 拉桨结束（出桨点）
   c. 回桨阶段为返回抓水位置的过程
4. 根据桨频自适应调整阈值
```

#### 算法二：腿-背-臂发力顺序检测

```
输入：膝关节(ω_k)、躯干(ω_t)、肘关节(ω_e)角速度峰值
输出：协调性评分与发力顺序诊断

1. 检测各关节角速度峰值时刻：t_k, t_t, t_e
2. 理想顺序：t_k < t_t < t_e（腿→背→臂）
3. 计算顺序偏差：Δ = max(0, t_t - t_k) + max(0, t_e - t_t)
4. 评分 = 1 / (1 + α·Δ)，α 为缩放因子
5. 根据违反的顺序对错误类型进行分类
```

#### 算法三：基于 DTW 的技术评分

```
输入：运动员关节角度曲线 Q，标准模板 S
输出：技术相似度评分

1. 计算 Q 与 S 之间的 DTW 对齐路径
2. 计算累积距离：D_DTW = Σ |Q[i] - S[j]|（沿对齐路径）
3. 归一化：score = exp(-D_DTW / (σ · L))，L 为曲线长度
4. 对每个关节（膝、髋、躯干、肘、肩）重复上述过程
5. 综合评分 = 各关节评分的加权平均
```

---

## 集成标准

### 接口规范

#### 上传视频

```
POST /api/v1/videos/upload
Content-Type: multipart/form-data

参数：
  - file: 视频文件 (mp4, avi, mov; 最大 500MB)
  - athlete_level: 可选 (beginner/intermediate/advanced)

响应：
{
  "task_id": "uuid",
  "status": "queued",
  "estimated_time": "60s"
}
```

#### 获取分析结果

```
GET /api/v1/analysis/{task_id}

响应：
{
  "task_id": "uuid",
  "status": "completed",
  "scores": {
    "overall": 78.5,
    "rhythm": 85.0,
    "amplitude": 72.0,
    "coordination": 75.0,
    "similarity": 82.0
  },
  "phases": [
    {"cycle": 1, "catch": 0.5, "drive": 1.2, "finish": 0.3, "recovery": 0.8}
  ],
  "errors": [
    {"type": "premature_back_opening", "severity": "moderate", "cycles": [3, 5, 7]}
  ],
  "suggestions": [
    "延迟背部打开时机，待腿部伸展至70%后再开始躯干后倾",
    "增加划桨前30%阶段的腿部驱动力度"
  ],
  "annotated_video_url": "/results/{task_id}/annotated.mp4",
  "report_url": "/results/{task_id}/report.pdf"
}
```

#### 获取历史记录

```
GET /api/v1/history?page=1&limit=10

响应：
{
  "total": 25,
  "items": [
    {"task_id": "uuid", "created_at": "2026-10-28T10:00:00Z", "overall_score": 78.5}
  ]
}
```

### 技术标准

| 标准 | 规范 |
|------|------|
| **姿态估计模型** | YOLOv8-Pose，17 个 COCO 关键点 |
| **视频格式** | MP4 (H.264), AVI, MOV |
| **API 格式** | RESTful JSON，兼容标准 HTTP 响应 |
| **身份认证** | Bearer Token（本地部署可选） |
| **异步处理** | 任务队列 + 状态轮询 |
| **数据存储** | SQLite（默认）/ PostgreSQL（生产环境） |
| **输出格式** | 标注 MP4 视频、PDF 报告、JSON 指标 |

### 集成方式

**1. Web 界面** — 通过浏览器访问 `http://localhost:8000` 使用系统。

**2. API 集成** — 通过 REST API 将分析流水线集成到现有平台：

```python
import requests

# 上传视频
resp = requests.post(
    "http://localhost:8000/api/v1/videos/upload",
    files={"file": open("training.mp4", "rb")}
)
task_id = resp.json()["task_id"]

# 轮询结果
import time
while True:
    result = requests.get(f"http://localhost:8000/api/v1/analysis/{task_id}").json()
    if result["status"] == "completed":
        break
    time.sleep(5)

print(f"综合评分: {result['scores']['overall']}")
```

**3. Python SDK** — 以 Python 包形式直接调用分析流水线：

```python
from rowing_coach import RowingAnalyzer

analyzer = RowingAnalyzer()
result = analyzer.analyze("training.mp4")
print(result.scores.overall)
print(result.suggestions)
```

---

## 快速开始

### 环境要求

- Python 3.10+
- PyTorch 2.0+
- FFmpeg（视频处理）

### 安装

```bash
git clone https://github.com/CHAOXIHUANJIEKE/rowing-coach-agent.git
cd rowing-coach-agent
pip install -r requirements.txt
```

### 启动系统

```bash
# 启动后端服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 打开浏览器访问
# http://localhost:8000
```

---

## 项目结构

```
rowing-coach-agent/
├── app/
│   ├── main.py                 # FastAPI 应用入口
│   ├── api/                    # API 路由定义
│   ├── core/                   # 核心配置
│   └── models/                 # 数据库模型
├── pipeline/
│   ├── preprocess/             # 视频预处理模块
│   ├── pose_estimation/        # 姿态估计模块
│   ├── stroke_analysis/        # 赛艇动作分析模块
│   ├── evaluation/             # 评估与诊断模块
│   └── visualization/          # 可视化模块
├── frontend/
│   ├── src/
│   │   ├── components/         # Vue 组件
│   │   ├── views/              # 页面视图
│   │   └── api/                # API 客户端
│   └── package.json
├── templates/                  # 标准技术模板库
├── tests/                      # 测试用例
├── requirements.txt
├── README.md                   # 英文文档
├── README.zh-CN.md             # 中文文档
└── LICENSE
```

---

## 技术栈

| 类别 | 技术 |
|------|------|
| **姿态估计** | YOLOv8-Pose (Ultralytics) |
| **深度学习** | PyTorch |
| **信号处理** | NumPy, SciPy（滤波、峰值检测） |
| **时序对齐** | DTW (tslearn / dtaidistance) |
| **后端** | FastAPI + Uvicorn |
| **前端** | Vue.js 3 + Element Plus |
| **数据库** | SQLite / PostgreSQL |
| **视频处理** | OpenCV, FFmpeg |
| **可视化** | Matplotlib, Plotly |

---

## 开源协议

本项目基于 MIT 协议开源 — 详见 [LICENSE](LICENSE)。

---

> U157 智科队 | 智能科学与技术 | 2026 江苏省 AI+ 科学与工程创新实践黑客松
