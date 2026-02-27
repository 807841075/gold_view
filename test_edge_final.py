import subprocess
import json
import os
import re

def test_edge_old_headless(url):
    print(f"\n--- Testing Edge Old Headless ---")
    # 尝试寻找 msedge.exe 的标准路径
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "msedge.exe"
    ]
    
    edge_exe = None
    for path in edge_paths:
        if os.path.exists(path) or path == "msedge.exe":
            edge_exe = path
            break
            
    if not edge_exe:
        print("Edge not found.")
        return False

    # --headless=old 是关键，它比新的 --headless 更难被 WAF 识别
    cmd = [
        edge_exe,
        "--headless=old",
        "--disable-gpu",
        "--dump-dom",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        url
    ]
    
    try:
        # 增加超时时间，因为启动浏览器需要一点时间
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=20)
        
        # 浏览器返回的是 HTML 包装的内容，我们需要从中提取 JSON
        # 东方财富返回的 JSON 通常在 <pre> 标签中或者直接作为文本
        output = result.stdout
        if '"data"' in output:
            print("Success with Edge Old Headless!")
            # 提取 JSON (寻找 { "rc": ... } 结构)
            match = re.search(r'\{.*"data":.*\}', output, re.DOTALL)
            if match:
                json_str = match.group(0)
                data = json.loads(json_str)
                print(f"Verified JSON data for: {data['data'].get('name', 'Unknown')}")
                return True
        else:
            print(f"Failed. Output snippet: {output[:200]}")
    except Exception as e:
        print(f"Edge Error: {e}")
    return False

if __name__ == "__main__":
    test_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AU9999&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58&klt=1&fqt=1&lmt=120"
    test_edge_old_headless(test_url)
