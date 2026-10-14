# AI生成
#!/bin/bash
# 赛艇智能教练 - AGH集成分析脚本
# 用法: bash run_with_agh.sh <视频路径>
#
# 流程:
#   1. Python CV管线分析视频 -> JSON
#   2. AGH调Agnes模型生成诊断报告
#   3. 输出完整报告

VIDEO_PATH=$1
AGH_CMD="node /app/packages/cli/dist/local/agnes.mjs"
PROJECT_DIR="D:/果办/OfficeAce/workspace/20261010135443/rowing-coach-agent"

if [ -z "$VIDEO_PATH" ]; then
    echo "用法: bash run_with_agh.sh <视频路径>"
    exit 1
fi

echo "========================================"
echo "赛艇智能教练 - AGH集成分析"
echo "========================================"
echo ""

# Step 1: CV管线分析
echo "[1/2] 运行CV管线分析视频..."
python "$PROJECT_DIR/cv_pipeline.py" "$VIDEO_PATH" "$PROJECT_DIR/cv_result.json"

if [ ! -f "$PROJECT_DIR/cv_result.json" ]; then
    echo "CV分析失败!"
    exit 1
fi

echo "CV分析完成!"
echo ""

# Step 2: AGH生成诊断报告
echo "[2/2] AGH调用Agnes模型生成诊断报告..."

CV_RESULT=$(cat "$PROJECT_DIR/cv_result.json")

$AGH_CMD -p "你是一位专业赛艇教练。根据以下CV管线分析结果(JSON格式)，生成一份专业的赛艇技术诊断报告。报告需包含: 总体评价、数据概览、问题分析、训练建议、改进优先级。

分析数据:
$CV_RESULT

请用中文输出完整诊断报告。" --profile local-dev --cwd /app

echo ""
echo "========================================"
echo "分析完成!"
echo "========================================"
