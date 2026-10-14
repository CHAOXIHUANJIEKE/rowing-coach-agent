# AI生成
"""
环境检查脚本 - 验证依赖安装和API连通性
运行: python check_env.py
"""
import sys


def check_python():
    print(f"[1] Python版本: {sys.version}")
    if sys.version_info < (3, 8):
        print("    [FAIL] 需要Python 3.8+")
        return False
    print("    [OK]")
    return True


def check_dependencies():
    print("[2] 检查Python依赖...")
    deps = {
        "cv2": "opencv-python",
        "mediapipe": "mediapipe",
        "numpy": "numpy",
        "requests": "requests",
        "gradio": "gradio",
        "dotenv": "python-dotenv",
    }
    all_ok = True
    for module, package in deps.items():
        try:
            __import__(module)
            print(f"    [OK] {package}")
        except ImportError:
            print(f"    [FAIL] {package} 未安装, 运行: pip install {package}")
            all_ok = False
    return all_ok


def check_api():
    print("[3] 检查Agnes API连通性...")
    try:
        from config import AGNES_API_URL, AGNES_API_KEY, AGNES_MODEL
        import requests

        if not AGNES_API_KEY:
            print("    [FAIL] AGNES_API_KEY未设置, 请检查.env文件")
            return False

        print(f"    API地址: {AGNES_API_URL}")
        print(f"    模型: {AGNES_MODEL}")
        print(f"    Key: {AGNES_API_KEY[:10]}...{AGNES_API_KEY[-4:]}")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {AGNES_API_KEY}",
        }
        payload = {
            "model": AGNES_MODEL,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 10,
        }
        resp = requests.post(AGNES_API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        print("    [OK] Agnes API连通!")
        return True
    except Exception as e:
        print(f"    [FAIL] {str(e)}")
        return False


def check_cv():
    print("[4] 检查CV管线...")
    try:
        from cv_pipeline import RowingAnalyzer
        print("    [OK] CV管线模块可导入")
        return True
    except Exception as e:
        print(f"    [FAIL] {str(e)}")
        return False


def check_agent():
    print("[5] 检查Agent模块...")
    try:
        from agent import RowingCoachAgent
        print("    [OK] Agent模块可导入")
        return True
    except Exception as e:
        print(f"    [FAIL] {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("赛艇智能教练Agent - 环境检查")
    print("=" * 50 + "\n")

    results = []
    results.append(("Python版本", check_python()))
    print()
    results.append(("Python依赖", check_dependencies()))
    print()
    results.append(("Agnes API", check_api()))
    print()
    results.append(("CV管线", check_cv()))
    print()
    results.append(("Agent模块", check_agent()))

    print("\n" + "=" * 50)
    print("检查结果汇总")
    print("=" * 50)
    for name, ok in results:
        status = "[OK]  " if ok else "[FAIL]"
        print(f"  {status} {name}")

    all_ok = all(ok for _, ok in results)
    print()
    if all_ok:
        print("所有检查通过! 运行 python app.py 启动系统")
    else:
        print("部分检查未通过, 请修复后重试")
