# AI生成
import json
r = json.load(open(r"D:\果办\OfficeAce\workspace\20261010135443\rowing-coach-agent\full_result.json", "r", encoding="utf-8"))
s = r["cv_result"]["summary"]
with open(r"D:\果办\OfficeAce\workspace\20261010135443\rowing-coach-agent\summary_check.txt", "w", encoding="utf-8") as f:
    f.write(json.dumps(s, ensure_ascii=False, indent=2))
    f.write("\n\n--- All keys in cv_result ---\n")
    f.write(json.dumps(list(r["cv_result"].keys()), ensure_ascii=False, indent=2))