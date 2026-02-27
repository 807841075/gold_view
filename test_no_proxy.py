import requests
import urllib3

urllib3.disable_warnings()

def test_requests_no_proxy(url):
    print(f"Testing URL with requests (trust_env=False): {url}")
    session = requests.Session()
    session.trust_env = False # Ignore system proxies
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Referer': 'https://quote.eastmoney.com/'
    }
    
    try:
        resp = session.get(url, headers=headers, timeout=10, verify=False)
        print(f"Status Code: {resp.status_code}")
        print(resp.text[:500] + "...")
    except Exception as e:
        print(f"Failed! Error: {e}")

if __name__ == "__main__":
    test_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AU9999&ut=fa5fd1943c41138ebe.0b69&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58&klt=1&fqt=1&end=20500101&lmt=120"
    test_requests_no_proxy(test_url)
