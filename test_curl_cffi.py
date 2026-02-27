from curl_cffi import requests
import json

def test_curl_cffi():
    print("\n--- Testing with curl_cffi (Chrome Impersonation) ---")
    
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AU9999&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58&klt=1&fqt=1&lmt=120"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Referer': 'https://quote.eastmoney.com/',
        'Accept': '*/*',
    }
    
    try:
        # impersonate="chrome120" 会模拟 Chrome 120 的 TLS 指纹
        resp = requests.get(url, headers=headers, impersonate="chrome120", timeout=15)
        
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200 and '"data"' in resp.text:
            print("Success with curl_cffi!")
            data = resp.json()
            print(f"Verified Data: {data['data'].get('name', 'Unknown')}")
            return True
        else:
            print(f"Failed. Response: {resp.text[:200]}")
    except Exception as e:
        print(f"curl_cffi Error: {e}")
    return False

if __name__ == "__main__":
    test_curl_cffi()
