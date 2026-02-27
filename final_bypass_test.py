import subprocess
import json
import os

def test_system_curl(url):
    print("\n--- Testing System32 curl.exe ---")
    # 显式使用 System32 下的 curl.exe，避开 PowerShell 别名
    curl_path = r"C:\Windows\System32\curl.exe"
    if not os.path.exists(curl_path):
        curl_path = "curl" # fallback
        
    cmd = [
        curl_path,
        "-k", # 忽略证书校验（有时能避开某些指纹检测）
        "--http1.1", # 强制使用 HTTP/1.1，避开 H2 指纹
        "-s",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "-H", "Referer: https://quote.eastmoney.com/",
        "-H", "Accept: */*",
        url
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if result.returncode == 0 and '"data"' in result.stdout:
            print("Success with System32 curl!")
            return True
        else:
            print(f"Failed. Code: {result.returncode}, Output: {result.stdout[:100]}")
    except Exception as e:
        print(f"Error: {e}")
    return False

def test_msedge_headless(url):
    print("\n--- Testing MS Edge Headless ---")
    # Edge 的 headless 模式会返回页面内容，对于 JSON API，它会直接显示内容
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(edge_path):
        print("Edge path not found.")
        return False
        
    cmd = [
        edge_path,
        "--headless",
        "--disable-gpu",
        "--dump-dom", # 获取渲染后的内容
        url
    ]
    try:
        # Edge 会在输出中带有一些日志，我们需要提取其中的 JSON
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=20)
        if '"data"' in result.stdout:
            print("Success with Edge Headless!")
            # 提取 JSON 部分
            start = result.stdout.find('{')
            end = result.stdout.rfind('}') + 1
            if start != -1 and end != -1:
                print(f"Data snippet: {result.stdout[start:start+100]}...")
            return True
        else:
            print(f"Failed. Output: {result.stdout[:200]}")
    except Exception as e:
        print(f"Error: {e}")
    return False

if __name__ == "__main__":
    test_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AU9999&ut=fa5fd1943c41138ebe.0b69&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58&klt=1&fqt=1&end=20500101&lmt=120"
    
    if not test_system_curl(test_url):
        test_msedge_headless(test_url)
