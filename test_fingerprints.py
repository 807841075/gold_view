from curl_cffi import requests
import time

def test_variant(name, impersonate_target):
    print(f"\n>>> 正在测试指纹: {name} ({impersonate_target})")
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AU9999&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58&klt=1&fqt=1&lmt=10"
    
    # 模拟更完整的浏览器 Header
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Referer': 'https://quote.eastmoney.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }

    try:
        resp = requests.get(url, headers=headers, impersonate=impersonate_target, timeout=10)
        print(f"状态码: {resp.status_code}")
        if resp.status_code == 200 and '"data"' in resp.text:
            print(f"✅ 成功！{name} 指纹有效。")
            return True
        else:
            print(f"❌ 失败。返回内容长度: {len(resp.text)}")
    except Exception as e:
        print(f"💥 异常: {e}")
    return False

if __name__ == "__main__":
    # 尝试不同的指纹，避开之前可能被封的 chrome
    targets = [
        ("Safari 17", "safari17"),
        ("Edge 101", "edge101"),
        ("Chrome 110", "chrome110"),
        ("iPhone (Mobile)", "safari_ios_16_0")
    ]
    
    for name, target in targets:
        if test_variant(name, target):
            break
        time.sleep(1)
