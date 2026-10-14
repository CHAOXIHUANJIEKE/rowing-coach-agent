# AI生成
import sys
sys.path.insert(0, r"D:\果办\OfficeAce\workspace\20261010135443\rowing-coach-agent")
try:
    import app
    print("import app: OK")
    a = app.create_app()
    print("create_app: OK")
    print("Gradio app ready to launch!")
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()