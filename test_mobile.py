import requests
import urllib3

urllib3.disable_warnings()

def test_mobile_api(symbol_id):
    print(f"\n--- Testing Mobile API for {symbol_id} ---")
    # 移动端接口域名，数据结构与原接口完全一致
    url = f"https://np-kline.eastmoney.com/api/qt/stock/kline/get?secid={symbol_id}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58&klt=1&fqt=1&lmt=120"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
        'Referer': 'https://quote.eastmoney.com/',
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10, verify=False)
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200 and '"data"' in resp.text:
            print("Success with Mobile API!")
            return True
        else:
            print(f"Failed. Response: {resp.text[:100]}")
    except Exception as e:
        print(f"Mobile API Error: {e}")
    return False

if __name__ == "__main__":
    # 测试国内金
    test_mobile_api("105.AU9999")
    # 测试国际金
    test_mobile_api("101.hf_XAU")
