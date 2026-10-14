# 赛艇智能教练 Agent

基于 Agnes Harness 的赛艇技术动作分析与诊断系统。

## 架构

```
赛艇视频 -> MediaPipe(姿态提取) -> 关节角度计算 -> 犯规检测(5类)
        -> Agnes Harness(Agent编排) -> agnes-2.0-flash(诊断报告生成)
        -> Gradio Web界面
```

## 快速开始

### 1. 安装Python依赖

```bash
cd rowing-coach-agent
pip install -r requirements.txt
```

### 2. 配置API Key

编辑 `.env` 文件，填入你的 Agnes API Key：

```
AGNES_API_KEY=你的key
```

### 3. 启动Web界面

```bash
python app.py
```

浏览器打开 http://localhost:7860 ，上传赛艇视频即可分析。

### 4. 命令行使用

```bash
# 分析单个视频
python agent.py video.mp4

# 对比两个视频
python agent.py video1.mp4 video2.mp4

# 交互问答模式
python agent.py video.mp4 --chat

# 仅运行CV管线
python cv_pipeline.py video.mp4 result.json
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `config.py` | 配置中心：API地址、模型名、犯规阈值 |
| `.env` | 环境变量：API Key |
| `cv_pipeline.py` | CV管线：MediaPipe姿态提取 + 角度计算 + 犯规检测 |
| `knowledge_base.py` | 知识库：赛艇生物力学 + 系统提示词 |
| `agent.py` | Agent核心：调用Agnes API生成诊断报告 |
| `app.py` | Web界面：Gradio |

## 检测的5类技术犯规

| 犯规 | 检测条件 | 来源 |
|------|---------|------|
| 膝关节过早溃缩 | 拉桨初期膝角速度 < -10deg/s | 论文§5.3.2 |
| 提早拉臂 | 躯干<30度 且 肘<150度 | 论文§5.3.2 |
| 躯干姿态失稳 | 后倒角偏离30度 > 15度 | 论文§5.3.2 |
| 伸展不充分 | 结束时膝<160度 或 肘<170度 | 论文§5.3.2 |
| 回桨仓促 | 回桨时间占比 < 55% | 论文§5.3.2 |

## Agnes Harness 集成

本项目使用 Agnes Harness 架构：Agent = Model + Harness

- **Model**: agnes-2.0-flash (Agnes AI平台提供)
- **Harness**: 工具编排(CV管线) + 上下文管理(会话历史) + 任务规划(分析->诊断->报告)
- **API**: https://apihub.agnes-ai.cn/v1/chat/completions (OpenAI兼容格式)

AGH开源仓库: https://github.com/AgnesAI-Labs/agnes-harness

## 注意事项

- 无GPU环境可用，MediaPipe支持CPU推理
- 侧面拍摄的视频效果最佳
- 如果Agnes API不可用，系统会自动降级为离线模板报告
