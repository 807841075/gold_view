import subprocess
import json
import sys

def test_powershell_fetch(url):
    host = "push2his.eastmoney.com"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    
    headers_dict = f"""
    $headers = @{{
        'Accept' = '*/*'
        'Accept-Language' = 'zh-CN,zh;q=0.9,en;q=0.8'
        'Cache-Control' = 'no-cache'
        'Connection' = 'keep-alive'
        'Pragma' = 'no-cache'
        'Referer' = 'https://quote.eastmoney.com/'
        'Host' = '{host}'
        'Sec-Fetch-Dest' = 'empty'
        'Sec-Fetch-Mode' = 'cors'
        'Sec-Fetch-Site' = 'same-site'
    }}
    """
    
    ps_script = f"""
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    {headers_dict}
    try {{
        $resp = Invoke-RestMethod -Uri '{url}' -Headers $headers -UserAgent '{user_agent}' -Method Get
        $resp | ConvertTo-Json -Depth 10
    }} catch {{
        Write-Error $_.Exception.Message
        exit 1
    }}
    """
    
    cmd = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script]
    print(f"Testing URL: {url}")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    
    if result.returncode == 0:
        print("Success!")
        print(result.stdout[:200] + "...")
    else:
        print("Failed!")
        print(f"Error: {result.stderr}")

if __name__ == "__main__":
    # Test with the SGE_AU9999 K-line URL (similar to what's in main.py)
    test_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AU9999&ut=fa5fd1943c41138ebe.0b69&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58&klt=1&fqt=1&end=20500101&lmt=120"
    test_powershell_fetch(test_url)
