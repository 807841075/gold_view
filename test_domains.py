import requests
import json

def test_push2_requests():
    print("\n--- Testing push2.eastmoney.com with requests ---")
    
    # Try different domains
    domains = [
        "push2his.eastmoney.com",
        "push2.eastmoney.com",
        "push2ex.eastmoney.com",
        "101.226.30.221" # Direct IP for push2his
    ]
    
    symbol_id = "105.AU9999"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Referer': 'https://quote.eastmoney.com/',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive'
    }

    for domain in domains:
        print(f"\nTrying domain: {domain}")
        if domain.startswith("101"):
            url = f"https://{domain}/api/qt/stock/kline/get?secid={symbol_id}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58&klt=1&fqt=1&lmt=120"
            # Need to set Host header for IP access
            current_headers = headers.copy()
            current_headers['Host'] = "push2his.eastmoney.com"
        else:
            url = f"https://{domain}/api/qt/stock/kline/get?secid={symbol_id}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58&klt=1&fqt=1&lmt=120"
            current_headers = headers

        try:
            session = requests.Session()
            session.trust_env = False  # Disable proxies
            resp = session.get(url, headers=current_headers, timeout=10, verify=False)
            print(f"Status Code: {resp.status_code}")
            if resp.status_code == 200 and '"data"' in resp.text:
                print(f"Success with {domain}!")
                return True
            else:
                print(f"Failed {domain}. Response snippet: {resp.text[:100]}")
        except Exception as e:
            print(f"Error with {domain}: {e}")
            
    return False

if __name__ == "__main__":
    test_push2_requests()
