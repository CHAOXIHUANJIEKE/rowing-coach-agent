# AI生成
import requests
import urllib3
urllib3.disable_warnings()

url = "https://api.agnes-ai.cn/v1/chat/completions"
headers = {
    "Authorization": "Bearer sk-j1Ks9Zb1j8lmAJkk2SdLZZmM4l2kP7QPEJTru8aYuxakfB4r",
    "Content-Type": "application/json"
}
payload = {
    "model": "agnes-3.0-flash",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 50
}

print("Testing Agnes API...")
try:
    resp = requests.post(url, json=payload, headers=headers, timeout=30, verify=False)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Response: {data['choices'][0]['message']['content'][:100]}")
        print("API: OK")
    else:
        print(f"Response body: {resp.text[:200]}")
except requests.exceptions.Timeout:
    print("API: TIMEOUT (30s)")
except requests.exceptions.ConnectionError as e:
    print(f"API: CONNECTION FAILED - {e}")
except Exception as e:
    print(f"API: ERROR - {e}")