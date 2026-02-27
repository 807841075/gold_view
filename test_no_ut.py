import subprocess
import json

def test_no_ut_param(url):
    # Remove ut parameter
    import urllib.parse as urlparse
    parsed = urlparse.urlparse(url)
    params = urlparse.parse_qs(parsed.query)
    params.pop('ut', None)
    new_query = urlparse.urlencode(params, doseq=True)
    new_url = urlparse.urlunparse(parsed._replace(query=new_query))
    
    cmd = [
        'curl',
        '-4',
        '-s',
        '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        '-H', 'Referer: https://quote.eastmoney.com/',
        new_url
    ]
    
    print(f"Testing URL without 'ut' param: {new_url}")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    
    if result.returncode == 0 and result.stdout.strip():
        print("Success!")
        print(result.stdout[:500] + "...")
    else:
        print(f"Failed! Return code: {result.returncode}")
        print(f"Stderr: {result.stderr}")

if __name__ == "__main__":
    test_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AU9999&ut=fa5fd1943c41138ebe.0b69&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58&klt=1&fqt=1&end=20500101&lmt=120"
    test_no_ut_param(test_url)
