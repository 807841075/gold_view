import urllib.request
import ssl

def test_bare_urllib(url):
    print(f"\n--- Testing Bare Urllib for {url[:50]}... ---")
    # 使用最基础的上下文，不进行任何指纹模拟
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    # 只带一个最通用的 UA
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=context, timeout=10) as response:
            data = response.read().decode('utf-8')
            if '"data"' in data:
                print("Success with Bare Urllib!")
                return True
            else:
                print(f"Failed. Response: {data[:100]}")
    except Exception as e:
        print(f"Bare Urllib Error: {e}")
    return False

if __name__ == "__main__":
    test_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AU9999&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58&klt=1&fqt=1&lmt=120"
    test_bare_urllib(test_url)
