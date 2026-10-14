# AI生成
"""
Agnes Harness Agent - 赛艇智能教练
通过Agnes API (OpenAI兼容格式) 调用agnes-2.0-flash模型生成诊断报告

架构: Agent = Model(Agnes-2.0-flash) + Harness(工具编排+会话管理)

工作流程:
  1. 调用CV管线分析视频 -> 结构化JSON
  2. 将CV结果格式化为文本, 喂给Agnes模型
  3. 模型基于赛艇生物力学知识生成专业诊断报告
  4. 返回完整分析结果
"""
import requests
import json
import time
import os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from config import AGNES_API_URL, AGNES_API_KEY, AGNES_MODEL
from cv_pipeline import RowingAnalyzer
from knowledge_base import SYSTEM_PROMPT, format_cv_result_for_agent, generate_fallback_report


class RowingCoachAgent:
    """赛艇智能教练Agent"""

    def __init__(self):
        self.api_url = AGNES_API_URL
        self.api_key = AGNES_API_KEY
        self.model = AGNES_MODEL
        self.cv_analyzer = RowingAnalyzer()
        self.conversation_history = []

    def _call_agnes_api(self, messages, temperature=0.7, max_tokens=4096):
        """
        调用Agnes API (OpenAI兼容格式)
        POST https://apihub.agnes-ai.cn/v1/chat/completions
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            response = requests.post(
                self.api_url, headers=headers, json=payload, timeout=120, verify=False)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"], None
        except requests.exceptions.Timeout:
            return None, "Agnes API请求超时(120s), 请稍后重试"
        except requests.exceptions.ConnectionError:
            return None, "无法连接Agnes API, 请检查网络"
        except requests.exceptions.HTTPError as e:
            return None, f"Agnes API返回错误: {e.response.status_code} - {e.response.text[:200]}"
        except (KeyError, IndexError) as e:
            return None, f"Agnes API响应格式异常: {str(e)}"
        except Exception as e:
            return None, f"未知错误: {str(e)}"

    def analyze_video(self, video_path, verbose=True):
        """
        完整分析流程: 视频 -> CV分析 -> Agent诊断 -> 报告

        参数:
            video_path: 视频文件路径
            verbose: 是否打印进度

        返回: dict {
            "cv_result": CV分析结果,
            "report": 诊断报告文本,
            "report_source": "agnes_api" 或 "fallback",
            "error": 错误信息(如有)
        }
        """
        result = {
            "cv_result": None,
            "report": None,
            "report_source": None,
            "error": None,
        }

        # ---- Step 1: CV管线分析 ----
        if verbose:
            print("[1/3] 正在运行CV管线分析视频...")

        try:
            cv_result = self.cv_analyzer.analyze(video_path)
            result["cv_result"] = cv_result
        except Exception as e:
            result["error"] = f"CV分析失败: {str(e)}"
            return result

        if "error" in cv_result:
            result["error"] = cv_result["error"]
            return result

        if verbose:
            s = cv_result["summary"]
            print(f"  -> 检测到{s['total_cycles']}个划桨周期, "
                  f"{s['total_errors']}次犯规")

        # ---- Step 2: 格式化CV结果 ----
        if verbose:
            print("[2/3] 正在格式化分析数据...")

        cv_text = format_cv_result_for_agent(cv_result)

        # ---- Step 3: 调用Agnes模型生成报告 ----
        if verbose:
            print(f"[3/3] 正在调用Agnes模型({self.model})生成诊断报告...")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"请根据以下CV管线分析结果, "
             f"生成一份专业的赛艇技术诊断报告:\n\n{cv_text}"},
        ]

        report, error = self._call_agnes_api(messages)

        if report:
            result["report"] = report
            result["report_source"] = "agnes_api"
            if verbose:
                print("  -> 诊断报告生成完成 (Agnes API)")
        else:
            # Fallback: 使用模板生成基础报告
            if verbose:
                print(f"  -> Agnes API调用失败: {error}")
                print("  -> 使用离线模板生成基础报告...")
            result["report"] = generate_fallback_report(cv_result)
            result["report_source"] = "fallback"
            result["error"] = error

        return result

    def interactive_coaching(self, cv_result, user_question):
        """
        交互式教练问答: 用户基于分析结果提问, Agent回答

        参数:
            cv_result: 之前的CV分析结果
            user_question: 用户的问题

        返回: Agent的回答文本
        """
        cv_text = format_cv_result_for_agent(cv_result)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"以下是运动员的CV分析结果:\n\n{cv_text}\n\n"
             f"基于以上数据, 回答运动员的问题: {user_question}"},
        ]

        answer, error = self._call_agnes_api(messages, temperature=0.8)
        return answer if answer else f"抱歉, 无法获取回答: {error}"

    def compare_videos(self, video_path_1, video_path_2, verbose=True):
        """
        对比分析两个视频 (如: 运动员 vs 教练示范)
        """
        if verbose:
            print("正在分析视频1...")
        result1 = self.cv_analyzer.analyze(video_path_1)
        if verbose:
            print("正在分析视频2...")
        result2 = self.cv_analyzer.analyze(video_path_2)

        cv_text_1 = format_cv_result_for_agent(result1)
        cv_text_2 = format_cv_result_for_agent(result2)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"请对比分析以下两段赛艇视频的技术差异, "
             f"指出视频1相对于视频2的改进方向:\n\n"
             f"=== 视频1 (待分析) ===\n{cv_text_1}\n\n"
             f"=== 视频2 (参考标准) ===\n{cv_text_2}"},
        ]

        report, error = self._call_agnes_api(messages, max_tokens=6144)
        return {
            "cv_result_1": result1,
            "cv_result_2": result2,
            "report": report if report else generate_fallback_report(result1),
            "error": error,
        }


# ============================================================
#  命令行入口
# ============================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("赛艇智能教练Agent - 使用方法:")
        print("  分析视频:     python agent.py <视频路径>")
        print("  对比分析:     python agent.py <视频1> <视频2>")
        print("  交互问答:     python agent.py <视频路径> --chat")
        sys.exit(1)

    video_path = sys.argv[1]
    agent = RowingCoachAgent()

    if len(sys.argv) >= 3 and not sys.argv[2].startswith("--"):
        # 对比模式
        video_path_2 = sys.argv[2]
        print(f"\n对比分析: {video_path} vs {video_path_2}\n")
        result = agent.compare_videos(video_path, video_path_2)
        print("\n" + "=" * 60)
        print(result["report"])
    else:
        # 单视频分析
        print(f"\n分析视频: {video_path}\n")
        result = agent.analyze_video(video_path)

        print("\n" + "=" * 60)
        print("赛艇技术诊断报告")
        print("=" * 60)
        print(result["report"])

        if result["report_source"] == "fallback":
            print(f"\n[注意] {result.get('error', '使用离线模板')}")

        # 交互问答模式
        if "--chat" in sys.argv:
            print("\n" + "=" * 60)
            print("进入交互问答模式 (输入quit退出)")
            print("=" * 60)
            while True:
                question = input("\n你的问题: ").strip()
                if question.lower() in ("quit", "exit", "q"):
                    break
                answer = agent.interactive_coaching(
                    result["cv_result"], question)
                print(f"\n教练: {answer}")
