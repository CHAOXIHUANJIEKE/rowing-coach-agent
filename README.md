# Rowing Intelligent Coach System

English | [简体中文](README.zh-CN.md)

> AI-powered rowing technique analysis and coaching system. Upload a training video, get instant feedback.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

---

## Table of Contents

- [Project Overview](#project-overview)
- [Demo Video](#demo-video)
- [Architecture](#architecture)
- [Integration Standards](#integration-standards)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [License](#license)

---

## Project Overview

### Background

Rowing is a highly technical sport where proper form is critical for both performance and injury prevention. Traditional coaching relies on the physical presence of an experienced coach, which is not always available for amateur or remote athletes. This project leverages computer vision and deep learning to provide automated, real-time rowing technique analysis, making professional-level coaching accessible to every rower.

### Core Features

1. **Video Upload & Processing** — Users upload rowing training videos via a web interface. The system handles various formats and resolutions.

2. **Human Pose Estimation** — Using YOLOv8-Pose, the system detects 17 body keypoints per frame, tracking the athlete's posture throughout the rowing cycle.

3. **Stroke Cycle Segmentation** — Automatically segments each stroke into four phases: **Catch**, **Drive**, **Finish**, and **Recovery**, using joint angle signals without requiring labeled data.

4. **Multi-Joint Coordination Analysis** — Analyzes the force application sequence of legs, back, and arms to evaluate coordination. Detects common errors such as premature back opening or insufficient leg drive.

5. **DTW-Based Technique Scoring** — Compares the athlete's joint angle trajectories against standard templates using Dynamic Time Warping, producing a quantitative technique score.

6. **Visual Feedback & Report** — Generates an annotated video with skeleton overlay, joint angle curves, phase timeline, and a text report with specific improvement suggestions.

### Innovation Highlights

- **Unsupervised Stroke Phase Segmentation**: A novel algorithm that uses knee and trunk angular velocity zero-crossings to detect stroke boundaries, adapting to varying stroke rates without manual calibration.
- **Leg-Back-Arm Sequencing Detection**: A biomechanics-inspired algorithm that analyzes joint angular velocity peak timing to verify the correct force application order (legs → back → arms), specific to rowing technique.
- **DTW + Multi-Dimensional Scoring**: Combines temporal alignment (DTW) with coordination analysis and rhythm stability for comprehensive technique evaluation, going beyond simple pose comparison.

---

## Demo Video

| Platform | Link |
|----------|------|
| Bilibili | https://b23.tv/TVcOceD |
| Douyin | https://v.douyin.com/canFdSbdh2s/ |

**Demo Workflow:**

1. User uploads a rowing training video via the web interface
2. System processes the video and displays a progress indicator
3. Annotated video with skeleton overlay and phase markers is generated
4. Joint angle analysis charts are displayed
5. A comprehensive coaching report with scores and improvement suggestions is produced

---

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Web Frontend (Vue.js)                  │
│  ┌───────────┐  ┌────────────┐  ┌────────────────────┐  │
│  │  Upload    │  │  Progress   │  │  Results Display   │  │
│  │  Component │  │  Tracker    │  │  (Video + Charts)  │  │
│  └───────────┘  └────────────┘  └────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │ REST API
┌────────────────────────┴────────────────────────────────┐
│                 Backend Service (FastAPI)                 │
│  ┌───────────┐  ┌────────────┐  ┌────────────────────┐  │
│  │  API       │  │  Task Queue │  │  Database          │  │
│  │  Routes    │  │  (Async)    │  │  (SQLite/PostgreSQL)│  │
│  └───────────┘  └────────────┘  └────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│                   Analysis Pipeline                       │
│                                                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  Video       │───>│  Pose        │───>│  Stroke     │  │
│  │  Preprocess  │    │  Estimation  │    │  Analysis   │  │
│  │  (350 lines) │    │  (500 lines) │    │  (600 lines) │  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                │          │
│                          ┌─────────────────────┘          │
│                          v                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  Visualization│<──│  Evaluation  │<──│  (Output)   │  │
│  │  (400 lines) │    │  & Diagnosis │    │             │  │
│  └─────────────┘    │  (550 lines) │    └─────────────┘  │
│                      └─────────────┘                      │
└─────────────────────────────────────────────────────────┘
```

### Core Modules

| Module | Function | Lines of Code |
|--------|----------|:-------------:|
| **Video Preprocessing** | Video decoding, frame extraction, denoising, frame rate standardization | ~350 |
| **Pose Estimation** | YOLOv8-Pose inference, 17-keypoint detection, multi-frame tracking, Kalman smoothing | ~500 |
| **Stroke Analysis** | Joint angle calculation, stroke cycle detection, 4-phase segmentation, rhythm analysis | ~600 |
| **Evaluation & Diagnosis** | Standard template library, DTW matching, error classification, suggestion generation, scoring | ~550 |
| **Visualization** | Annotated video generation, angle curves, phase timeline, report generation | ~400 |
| **Web Frontend** | Upload UI, progress display, results page, history management | ~500 |
| **Backend Service** | API routes, async task queue, file storage, database operations | ~400 |
| **Total** | | **~3,300** |

### Key Algorithms

#### Algorithm 1: Unsupervised Stroke Phase Segmentation

```
Input:  Joint angle time series θ_knee(t), θ_trunk(t)
Output: Phase boundaries {catch, drive, finish, recovery}

1. Compute angular velocity: ω(t) = dθ/dt
2. Detect zero-crossings of ω_knee(t) → stroke cycle boundaries
3. For each cycle:
   a. Find knee angle minimum → Catch phase start
   b. Find knee angle maximum → Drive phase end (Finish)
   c. Segment Recovery as the return to catch position
4. Adaptively adjust thresholds based on stroke rate
```

#### Algorithm 2: Leg-Back-Arm Coordination Detection

```
Input:  Angular velocity peaks for knee (ω_k), trunk (ω_t), elbow (ω_e)
Output: Coordination score and force sequence diagnosis

1. Detect peak angular velocity timestamps: t_k, t_t, t_e
2. Ideal sequence: t_k < t_t < t_e (legs → back → arms)
3. Compute sequence deviation: Δ = max(0, t_t - t_k) + max(0, t_e - t_t)
4. Score = 1 / (1 + α·Δ), where α is a scaling factor
5. Classify error type based on which sequence is violated
```

#### Algorithm 3: DTW-Based Technique Scoring

```
Input:  Athlete joint angle curve Q, standard template S
Output: Technique similarity score

1. Compute DTW alignment path between Q and S
2. Calculate cumulative distance: D_DTW = Σ |Q[i] - S[j]| along path
3. Normalize: score = exp(-D_DTW / (σ · L)), where L = curve length
4. Repeat for each joint (knee, hip, trunk, elbow, shoulder)
5. Overall score = weighted average across all joints
```

---

## Integration Standards

### API Specification

#### Upload Video

```
POST /api/v1/videos/upload
Content-Type: multipart/form-data

Parameters:
  - file: Video file (mp4, avi, mov; max 500MB)
  - athlete_level: Optional (beginner/intermediate/advanced)

Response:
{
  "task_id": "uuid",
  "status": "queued",
  "estimated_time": "60s"
}
```

#### Get Analysis Result

```
GET /api/v1/analysis/{task_id}

Response:
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
    "Delay back opening until legs are 70% extended",
    "Increase leg drive power in the first 30% of the stroke"
  ],
  "annotated_video_url": "/results/{task_id}/annotated.mp4",
  "report_url": "/results/{task_id}/report.pdf"
}
```

#### Get Analysis History

```
GET /api/v1/history?page=1&limit=10

Response:
{
  "total": 25,
  "items": [
    {"task_id": "uuid", "created_at": "2026-10-28T10:00:00Z", "overall_score": 78.5}
  ]
}
```

### Technical Standards

| Standard | Specification |
|----------|--------------|
| **Pose Model** | YOLOv8-Pose, 17 COCO keypoints |
| **Video Format** | MP4 (H.264), AVI, MOV |
| **API Format** | RESTful JSON, OpenAI-compatible response structure |
| **Authentication** | Bearer Token (optional for local deployment) |
| **Async Processing** | Task queue with status polling |
| **Data Storage** | SQLite (default) / PostgreSQL (production) |
| **Output Formats** | Annotated MP4, PDF report, JSON metrics |

### Integration Methods

**1. Web Interface** — Access the system through the built-in web UI at `http://localhost:8000`.

**2. API Integration** — Integrate the analysis pipeline into existing platforms via REST API:

```python
import requests

# Upload video
resp = requests.post(
    "http://localhost:8000/api/v1/videos/upload",
    files={"file": open("training.mp4", "rb")}
)
task_id = resp.json()["task_id"]

# Poll for result
import time
while True:
    result = requests.get(f"http://localhost:8000/api/v1/analysis/{task_id}").json()
    if result["status"] == "completed":
        break
    time.sleep(5)

print(f"Overall Score: {result['scores']['overall']}")
```

**3. Python SDK** — Use the analysis pipeline directly as a Python package:

```python
from rowing_coach import RowingAnalyzer

analyzer = RowingAnalyzer()
result = analyzer.analyze("training.mp4")
print(result.scores.overall)
print(result.suggestions)
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- PyTorch 2.0+
- FFmpeg (for video processing)

### Installation

```bash
git clone https://github.com/CHAOXIHUANJIEKE/rowing-coach-agent.git
cd rowing-coach-agent
pip install -r requirements.txt
```

### Run the System

```bash
# Start the backend server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Open the web interface
# Navigate to http://localhost:8000
```

---

## Project Structure

```
rowing-coach-agent/
├── app/
│   ├── main.py                 # FastAPI application entry
│   ├── api/                    # API route definitions
│   ├── core/                   # Core configuration
│   └── models/                 # Database models
├── pipeline/
│   ├── preprocess/             # Video preprocessing module
│   ├── pose_estimation/        # Pose estimation module
│   ├── stroke_analysis/        # Stroke analysis module
│   ├── evaluation/             # Evaluation & diagnosis module
│   └── visualization/          # Visualization module
├── frontend/
│   ├── src/
│   │   ├── components/         # Vue components
│   │   ├── views/              # Page views
│   │   └── api/                # API client
│   └── package.json
├── templates/                  # Standard technique templates
├── tests/                      # Test cases
├── requirements.txt
├── README.md                   # English documentation
├── README.zh-CN.md             # Chinese documentation
└── LICENSE
```

---

## Tech Stack

| Category | Technology |
|----------|-----------|
| **Pose Estimation** | YOLOv8-Pose (Ultralytics) |
| **Deep Learning** | PyTorch |
| **Signal Processing** | NumPy, SciPy (filtering, peak detection) |
| **Temporal Alignment** | DTW (tslearn / dtaidistance) |
| **Backend** | FastAPI + Uvicorn |
| **Frontend** | Vue.js 3 + Element Plus |
| **Database** | SQLite / PostgreSQL |
| **Video Processing** | OpenCV, FFmpeg |
| **Visualization** | Matplotlib, Plotly |

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

> Team U157 | Intelligent Science and Technology | 2026 Jiangsu AI+ Science and Engineering Innovation Practice Hackathon
