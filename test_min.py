import requests
import urllib3

urllib3.disable_warnings()

def test_minimal_request(symbol_id):
    print(f"\n--- Testing Minimal Request for {symbol_id} ---")
    # 极简 URL，去掉 ut 参数，只保留核心字段
    url = f"https://push2.eastmoney.com/api/qt/stock/kline/get?secid={symbol_id}&fields1=f1,f2,f3&fields2=f51,f52,f53&klt=1&fqt=1&lmt=10"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Referer': 'https://quote.eastmoney.com/',
        'Accept': '*/*',
    }
    
    try:
        # 禁用所有代理，模拟最干净的本地环境
        session = requests.Session()
        session.trust_env = False
        resp = session.get(url, headers=headers, timeout=10, verify=False)
        
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200 and '"data"' in resp.text:
            print("Success with Minimal Request!")
            print(f"Data: {resp.text[:100]}...")
            return True
        else:
            print(f"Failed. Response: {resp.text[:200]}")
    except Exception as e:
        print(f"Minimal Request Error: {e}")
    return False

if __name__ == "__main__":
    # 测试国内金
    test_minimal_request("105.AU9999")
