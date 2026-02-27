import httpx
import ssl

def test_httpx_http2():
    print("\n--- Testing HTTP/2 with httpx ---")
    
    url = "https://push2.eastmoney.com/api/qt/stock/kline/get?secid=105.AU9999&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58&klt=1&fqt=1&lmt=120"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Referer': 'https://quote.eastmoney.com/',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    try:
        # Create a custom SSL context that is more permissive
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        # Force HTTP/2
        ssl_context.set_alpn_protocols(["h2"])

        with httpx.Client(http2=True, verify=False, headers=headers, timeout=20.0) as client:
            print("Sending request...")
            resp = client.get(url)
            print(f"Status Code: {resp.status_code}")
            print(f"Protocol: {resp.http_version}")
            if resp.status_code == 200 and '"data"' in resp.text:
                print("Success with httpx HTTP/2!")
                print(f"Response snippet: {resp.text[:200]}")
                return True
            else:
                print(f"Failed. Response: {resp.text[:200]}")
    except Exception as e:
        print(f"httpx Error: {e}")
    return False

if __name__ == "__main__":
    test_httpx_http2()
