# AI生成
"""
CV管线命令行工具
用法: python cv_cli.py <视频路径> [输出JSON路径]

示例:
  python cv_cli.py test_video.mp4
  python cv_cli.py test_video.mp4 result.json
"""
import sys
import json
from cv_pipeline import RowingAnalyzer
from knowledge_base import format_cv_result_for_agent


def main():
    if len(sys.argv) < 2:
        print("用法: python cv_cli.py <视频路径> [输出JSON路径]")
        print("")
        print("示例:")
        print("  python cv_cli.py test_video.mp4")
        print("  python cv_cli.py test_video.mp4 result.json")
        sys.exit(1)

    video_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "cv_result.json"

    print(f"正在分析视频: {video_path}")
    print("-" * 40)

    analyzer = RowingAnalyzer()
    result = analyzer.analyze(video_path)

    # 保存JSON结果
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"分析结果已保存到: {output_path}")

    # 打印格式化摘要
    print("-" * 40)
    formatted = format_cv_result_for_agent(result)
    print(formatted)

    # 同时保存格式化文本
    text_path = output_path.replace(".json", "_text.txt")
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(formatted)
    print(f"格式化报告已保存到: {text_path}")


if __name__ == "__main__":
    main()
