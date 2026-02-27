import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# Custom adapter to set a more browser-like SSL context
class BrowserAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        # Chrome-like ciphers
        context.set_ciphers('ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384')
        kwargs['ssl_context'] = context
        return super(BrowserAdapter, self).init_poolmanager(*args, **kwargs)

def test_requests_browser_ssl(url):
    print(f"Testing URL with requests + Browser SSL: {url}")
    session = requests.Session()
    session.mount('https://', BrowserAdapter())
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://quote.eastmoney.com/',
        'Connection': 'keep-alive'
    }
    
    try:
        resp = session.get(url, headers=headers, timeout=10, verify=False)
        print(f"Status Code: {resp.status_code}")
        print(resp.text[:500] + "...")
    except Exception as e:
        print(f"Failed! Error: {e}")

if __name__ == "__main__":
    test_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AU9999&ut=fa5fd1943c41138ebe.0b69&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58&klt=1&fqt=1&end=20500101&lmt=120"
    test_requests_browser_ssl(test_url)
