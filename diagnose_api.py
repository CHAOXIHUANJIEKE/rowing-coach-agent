# AI生成
"""诊断Agnes API连接问题"""
import requests
import urllib3
import socket
urllib3.disable_warnings()

url = "https://api.agnes-ai.cn/v1/models"

# 1. DNS解析
print("=== DNS解析 ===")
try:
    ips = socket.getaddrinfo("api.agnes-ai.cn", 443)
    for ip in ips:
        print(f"  {ip[4]}")
except Exception as e:
    print(f"  DNS失败: {e}")

# 2. TCP连接测试
print("\n=== TCP连接测试 ===")
try:
    sock = socket.create_connection(("api.agnes-ai.cn", 443), timeout=10)
    print("  TCP连接成功")
    sock.close()
except Exception as e:
    print(f"  TCP连接失败: {type(e).__name__}: {e}")

# 3. HTTP请求测试
print("\n=== HTTP请求测试 ===")
try:
    r = requests.get(url, verify=False, timeout=15)
    print(f"  状态码: {r.status_code}")
    print(f"  响应: {r.text[:300]}")
except Exception as e:
    print(f"  请求失败: {type(e).__name__}: {e}")

# 4. 试HTTP (非HTTPS)
print("\n=== HTTP(非HTTPS)测试 ===")
try:
    r = requests.get("http://api.agnes-ai.cn/v1/models", timeout=10)
    print(f"  状态码: {r.status_code}")
except Exception as e:
    print(f"  HTTP请求失败: {type(e).__name__}: {e}")

print("\n=== 诊断完成 ===")
