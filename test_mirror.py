import requests
import urllib3

urllib3.disable_warnings()

def test_mirror_api(symbol_id):
    print(f"\n--- Testing Mirror API for {symbol_id} ---")
    # 使用 hqdigi2 镜像域名
    url = f"https://hqdigi2.eastmoney.com/api/qt/stock/kline/get?secid={symbol_id}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58&klt=1&fqt=1&lmt=120"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Referer': 'https://quote.eastmoney.com/',
    }
    
    try:
        session = requests.Session()
        session.trust_env = False
        resp = session.get(url, headers=headers, timeout=10, verify=False)
        
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200 and '"data"' in resp.text:
            print("Success with Mirror API!")
            print(f"Data snippet: {resp.text[:100]}...")
            return True
        else:
            print(f"Failed. Response: {resp.text[:100]}")
    except Exception as e:
        print(f"Mirror API Error: {e}")
    return False

if __name__ == "__main__":
    test_mirror_api("105.AU9999")
