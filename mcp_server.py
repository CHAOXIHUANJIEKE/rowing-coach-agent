# AI生成
"""
MCP Server - 赛艇CV分析工具
为AGH提供MCP协议接口，支持stdio传输

安装依赖: pip install mcp
启动: python mcp_server.py

AGH添加命令(在容器内):
  node packages/cli/dist/local/agnes.mjs mcp add \
    --name rowing-cv \
    --transport stdio \
    --command "python" \
    --args "/mnt/rowing-coach-agent/mcp_server.py"
"""
import json
import sys
import os
from mcp.server import Server
from mcp.types import Tool, TextContent

# 导入CV管线
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cv_pipeline import RowingAnalyzer
from knowledge_base import format_cv_result_for_agent

server = Server("rowing-cv")
analyzer = RowingAnalyzer()


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="analyze_rowing_video",
            description="分析赛艇视频，检测划桨技术问题。返回结构化分析结果，包含划桨周期、5类犯规检测、关节角度数据等。",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_path": {
                        "type": "string",
                        "description": "赛艇视频文件的完整路径"
                    }
                },
                "required": ["video_path"]
            }
        ),
        Tool(
            name="format_analysis_for_report",
            description="分析赛艇视频并格式化为教练可读的文本报告，适合直接传给LLM生成诊断报告。",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_path": {
                        "type": "string",
                        "description": "赛艇视频文件的完整路径"
                    }
                },
                "required": ["video_path"]
            }
        ),
        Tool(
            name="get_foul_rules",
            description="获取赛艇5类犯规检测规则和阈值参数说明。",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "analyze_rowing_video":
        video_path = arguments.get("video_path")
        result = analyzer.analyze(video_path)
        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]

    elif name == "format_analysis_for_report":
        video_path = arguments.get("video_path")
        result = analyzer.analyze(video_path)
        formatted = format_cv_result_for_agent(result)
        return [TextContent(type="text", text=formatted)]

    elif name == "get_foul_rules":
        rules = """赛艇5类犯规检测规则 (基于论文§5.3.2):

1. 膝关节过早溃缩
   - 检测: 膝关节角速度 < -10度/秒
   - 影响: 蹬腿力量不足，动力链断裂

2. 提早拉臂
   - 检测: 躯干前倾角 < 30度 且 肘关节角 < 150度
   - 影响: 手臂过早参与拉桨，躯干力量浪费

3. 躯干姿态失稳
   - 检测: 躯干偏离垂直方向 > 30度 且 持续 > 15度
   - 影响: 核心稳定性差，力量传递效率低

4. 伸展不充分
   - 检测: 膝关节最大角 < 160度 或 肘关节最大角 < 170度
   - 影响: 活动范围不足，做功距离短

5. 回桨仓促
   - 检测: 回桨时间占比 < 55%
   - 影响: 恢复不充分，节奏紊乱
   - 正常比例: 拉桨:回桨 = 4:6"""
        return [TextContent(type="text", text=rules)]

    return [TextContent(type="text", text=f"未知工具: {name}")]


if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    asyncio.run(main())
