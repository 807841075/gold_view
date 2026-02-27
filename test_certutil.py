import subprocess
import os
import json

def test_certutil_fetch(url):
    print(f"\n--- Testing CertUtil Fetch ---")
    output_file = "kline_temp.json"
    if os.path.exists(output_file):
        os.remove(output_file)
        
    # certutil -urlcache -split -f "URL" output_file
    # -f 强制刷新缓存
    # -split 分块下载
    cmd = [
        "certutil",
        "-urlcache",
        "-split",
        "-f",
        url,
        output_file
    ]
    
    try:
        # certutil 会弹出一个短暂的进度窗口，我们可以通过设置来隐藏它
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='gbk', timeout=15)
        
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # certutil 下载的内容开头可能有一些十六进制标记，我们提取 JSON 部分
                start = content.find('{')
                if start != -1:
                    json_str = content[start:]
                    data = json.loads(json_str)
                    if "data" in data:
                        print("Success with CertUtil!")
                        return True
        print(f"CertUtil failed. Stderr: {result.stderr}")
    except Exception as e:
        print(f"CertUtil Error: {e}")
    finally:
        if os.path.exists(output_file):
            os.remove(output_file)
            # 清理 certutil 的缓存索引
            subprocess.run(["certutil", "-urlcache", url, "delete"], capture_output=True)
    return False

if __name__ == "__main__":
    test_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AU9999&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58&klt=1&fqt=1&lmt=120"
    test_certutil_fetch(test_url)
