import socket
import requests
import urllib3

urllib3.disable_warnings()

def test_http_ip_bypass(domain, url_path):
    print(f"\n--- Testing HTTP IP Bypass for {domain} ---")
    try:
        # 1. 解析域名 IP
        ip = socket.gethostbyname(domain)
        print(f"Resolved IP: {ip}")
        
        # 2. 构建 HTTP URL (注意是 http 而不是 https)
        bypass_url = f"http://{ip}{url_path}"
        
        # 3. 手动设置 Host 头，这是绕过 IP 访问限制的关键
        headers = {
            'Host': domain,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Referer': f'https://{domain}/',
        }
        
        print(f"Requesting: {bypass_url}")
        session = requests.Session()
        session.trust_env = False
        resp = session.get(bypass_url, headers=headers, timeout=10)
        
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200 and '"data"' in resp.text:
            print("Success with HTTP IP Bypass!")
            return True
        else:
            print(f"Failed. Response: {resp.text[:100]}")
            
    except Exception as e:
        print(f"IP Bypass Error: {e}")
    return False

if __name__ == "__main__":
    domain = "push2his.eastmoney.com"
    # K线请求的路径部分
    path = "/api/qt/stock/kline/get?secid=105.AU9999&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58&klt=1&fqt=1&lmt=120"
    test_http_ip_bypass(domain, path)
