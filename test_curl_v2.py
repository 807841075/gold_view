import subprocess
import json

def test_curl_browser_like(url):
    # Try to match Chrome's header order and content as closely as possible
    # We use -L to follow redirects, -s for silent
    cmd = [
        'curl',
        '-v',
        '-s',
        '-H', 'Host: push2his.eastmoney.com',
        '-H', 'Connection: keep-alive',
        '-H', 'sec-ch-ua: "Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        '-H', 'sec-ch-ua-mobile: ?0',
        '-H', 'sec-ch-ua-platform: "Windows"',
        '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        '-H', 'Accept: */*',
        '-H', 'Sec-Fetch-Site: same-site',
        '-H', 'Sec-Fetch-Mode: cors',
        '-H', 'Sec-Fetch-Dest: empty',
        '-H', 'Referer: https://quote.eastmoney.com/',
        '-H', 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8',
        '--compressed',
        url
    ]
    
    print(f"Testing URL with Browser-like Curl: {url}")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    
    if result.returncode == 0 and result.stdout.strip():
        if '"data"' in result.stdout:
            print("Success!")
            print(result.stdout[:500] + "...")
        else:
            print("Output received but might be blocked/empty:")
            print(result.stdout[:500])
    else:
        print(f"Failed! Return code: {result.returncode}")
        print(f"Stderr: {result.stderr}")

if __name__ == "__main__":
    test_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AU9999&ut=fa5fd1943c41138ebe.0b69&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58&klt=1&fqt=1&end=20500101&lmt=120"
    test_curl_browser_like(test_url)
