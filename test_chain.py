import requests
import urllib3
import time

urllib3.disable_warnings()

def test_session_chain(url):
    print("\n--- Testing Session Chain (Referer -> API) ---")
    session = requests.Session()
    
    # 模拟真实 Chrome 的 Header 集合
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    
    try:
        # 第一步：访问行情中心主页，建立 Session
        print("Step 1: Visiting Main Quote Page...")
        session.get("https://quote.eastmoney.com/center/gridlist.html", headers=headers, timeout=10, verify=False)
        time.sleep(1) # 模拟人类停顿
        
        # 第二步：修改 Header 准备请求 API
        api_headers = headers.copy()
        api_headers.update({
            'Accept': 'application/json, text/plain, */*',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Referer': 'https://quote.eastmoney.com/',
        })
        
        # 强制禁用代理，直接连接
        session.trust_env = False
        
        print("Step 2: Fetching API...")
        resp = session.get(url, headers=api_headers, timeout=10, verify=False)
        
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200 and '"data"' in resp.text:
            print("Success with Session Chain!")
            return True
        else:
            print(f"Failed. Response: {resp.text[:200]}")
    except Exception as e:
        print(f"Session Chain Error: {e}")
    return False

if __name__ == "__main__":
    test_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AU9999&ut=fa5fd1943c41138ebe.0b69&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58&klt=1&fqt=1&end=20500101&lmt=120"
    test_session_chain(test_url)
